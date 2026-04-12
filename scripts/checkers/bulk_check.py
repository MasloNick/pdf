"""Масова перевірка юридичних осіб за даними CSV або портфеля.

Використовує CompanyChecker для паралельної перевірки компаній
за кодом ЄДРПОУ з відкритих джерел даних.
"""

from __future__ import annotations

import csv
import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

from scripts.checkers.company import CompanyChecker

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Маппінг колонок CSV для пошуку ЄДРПОУ та назви
# ---------------------------------------------------------------------------

EDRPOU_ALIASES = ["єдрпоу", "edrpou", "код", "код єдрпоу"]
NAME_ALIASES = ["назва", "name", "найменування", "компанія", "боржник", "піб", "пiб"]

# ---------------------------------------------------------------------------
# Статуси українською
# ---------------------------------------------------------------------------

STATUS_LABELS: Dict[str, str] = {
    "active": "Діюча",
    "in_liquidation": "В процесі ліквідації",
    "bankrupt": "Банкрут",
    "terminated": "Припинена",
    "unknown": "Невідомо",
}

RISK_LABELS: Dict[str, str] = {
    "low": "Низький",
    "medium": "Середній",
    "high": "Високий",
}


def _find_column(fieldnames: List[str], aliases: List[str]) -> str | None:
    """Знайти колонку у заголовках CSV за списком можливих назв."""
    lower_map = {f.strip().lower(): f for f in fieldnames}
    for alias in aliases:
        if alias.lower() in lower_map:
            return lower_map[alias.lower()]
    return None


def _check_single_company(
    checker: CompanyChecker,
    edrpou: str,
    name: str,
) -> Dict[str, Any]:
    """Перевірити одну компанію, обгорнувши помилки."""
    try:
        status = checker.check_company(edrpou, name)
        return {
            "edrpou": status.edrpou,
            "name": status.name or name,
            "status": STATUS_LABELS.get(status.status, status.status),
            "risk_level": RISK_LABELS.get(status.risk_level, status.risk_level),
            "is_problematic": status.is_problematic,
            "court_cases_count": len(status.court_cases),
            "enforcement_count": len(status.enforcement_proceedings),
            "warnings": "; ".join(status.warnings) if status.warnings else "",
        }
    except Exception as exc:
        LOGGER.error("Помилка перевірки ЄДРПОУ %s: %s", edrpou, exc)
        return {
            "edrpou": edrpou,
            "name": name,
            "status": "Помилка перевірки",
            "risk_level": "Невідомо",
            "is_problematic": False,
            "court_cases_count": 0,
            "enforcement_count": 0,
            "warnings": f"Помилка: {exc}",
        }


# ---------------------------------------------------------------------------
# Основні функції
# ---------------------------------------------------------------------------


def check_companies_from_csv(csv_text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Масова перевірка компаній з CSV-тексту.

    Шукає колонки ЄДРПОУ та назви компанії, для кожного рядка з
    валідним ЄДРПОУ запускає перевірку через CompanyChecker.

    Parameters
    ----------
    csv_text:
        Текстовий вміст CSV-файлу (UTF-8).

    Returns
    -------
    tuple
        (results, warnings) — список результатів перевірки та
        список попереджень щодо імпорту.
    """
    warnings: List[str] = []

    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        return [], ["CSV файл порожній або не має заголовків."]

    edrpou_col = _find_column(list(reader.fieldnames), EDRPOU_ALIASES)
    name_col = _find_column(list(reader.fieldnames), NAME_ALIASES)

    if not edrpou_col:
        return [], ["Не знайдено колонку з кодом ЄДРПОУ. "
                     "Очікується одна з: " + ", ".join(EDRPOU_ALIASES)]

    if not name_col:
        warnings.append("Не знайдено колонку з назвою компанії. "
                        "Буде використано лише ЄДРПОУ.")

    # Зібрати компанії для перевірки
    companies: List[Tuple[str, str]] = []
    for row_num, row in enumerate(reader, start=2):
        edrpou = (row.get(edrpou_col) or "").strip()
        name = (row.get(name_col) or "").strip() if name_col else ""
        if not edrpou:
            warnings.append(f"Рядок {row_num}: порожній ЄДРПОУ, пропущено.")
            continue
        companies.append((edrpou, name))

    if not companies:
        return [], warnings + ["Не знайдено жодного рядка з ЄДРПОУ."]

    warnings.append(f"Знайдено {len(companies)} компаній для перевірки.")

    # Паралельна перевірка
    checker = CompanyChecker(timeout=15, max_retries=2)
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_idx = {
            executor.submit(_check_single_company, checker, edrpou, name): idx
            for idx, (edrpou, name) in enumerate(companies)
        }
        # Збираємо результати зберігаючи порядок
        indexed_results: List[Tuple[int, Dict[str, Any]]] = []
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result = future.result()
            except Exception as exc:
                edrpou, name = companies[idx]
                LOGGER.error("Неочікувана помилка для ЄДРПОУ %s: %s", edrpou, exc)
                result = {
                    "edrpou": edrpou,
                    "name": name,
                    "status": "Помилка перевірки",
                    "risk_level": "Невідомо",
                    "is_problematic": False,
                    "court_cases_count": 0,
                    "enforcement_count": 0,
                    "warnings": f"Помилка: {exc}",
                }
            indexed_results.append((idx, result))

        # Сортуємо за оригінальним порядком рядків
        indexed_results.sort(key=lambda x: x[0])
        results = [r for _, r in indexed_results]

    return results, warnings


def check_companies_from_portfolio(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Перевірка юридичних осіб із записів портфеля.

    Фільтрує лише юридичних осіб (debtor_type містить 'юр' або 'legal'),
    витягує ЄДРПОУ та запускає перевірку.

    Parameters
    ----------
    records:
        Список записів боржників, отриманих з import_portfolio_csv.

    Returns
    -------
    list
        Список результатів перевірки (dict).
    """
    # Фільтруємо юридичних осіб
    companies: List[Tuple[str, str]] = []
    for rec in records:
        debtor_type = (rec.get("debtor_type") or "").lower()
        if "юр" not in debtor_type and "legal" not in debtor_type:
            continue
        edrpou = (rec.get("edrpou") or "").strip()
        if not edrpou:
            continue
        name = (rec.get("name") or "").strip()
        companies.append((edrpou, name))

    if not companies:
        return []

    # Паралельна перевірка
    checker = CompanyChecker(timeout=15, max_retries=2)
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_idx = {
            executor.submit(_check_single_company, checker, edrpou, name): idx
            for idx, (edrpou, name) in enumerate(companies)
        }
        indexed_results: List[Tuple[int, Dict[str, Any]]] = []
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result = future.result()
            except Exception as exc:
                edrpou, name = companies[idx]
                LOGGER.error("Неочікувана помилка для ЄДРПОУ %s: %s", edrpou, exc)
                result = {
                    "edrpou": edrpou,
                    "name": name,
                    "status": "Помилка перевірки",
                    "risk_level": "Невідомо",
                    "is_problematic": False,
                    "court_cases_count": 0,
                    "enforcement_count": 0,
                    "warnings": f"Помилка: {exc}",
                }
            indexed_results.append((idx, result))

        indexed_results.sort(key=lambda x: x[0])
        results = [r for _, r in indexed_results]

    return results


def export_check_results_csv(results: List[Dict[str, Any]]) -> str:
    """Експорт результатів перевірки у CSV-рядок.

    Parameters
    ----------
    results:
        Список результатів перевірки (як повертає check_companies_from_csv
        або check_companies_from_portfolio).

    Returns
    -------
    str
        CSV-текст з результатами перевірки (UTF-8).
    """
    output = io.StringIO()
    fieldnames = [
        "ЄДРПОУ",
        "Назва",
        "Статус",
        "Ризик",
        "Проблемна",
        "Суд.справ",
        "Викон.проваджень",
        "Попередження",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for r in results:
        writer.writerow({
            "ЄДРПОУ": r.get("edrpou", ""),
            "Назва": r.get("name", ""),
            "Статус": r.get("status", ""),
            "Ризик": r.get("risk_level", ""),
            "Проблемна": "Так" if r.get("is_problematic") else "Ні",
            "Суд.справ": r.get("court_cases_count", 0),
            "Викон.проваджень": r.get("enforcement_count", 0),
            "Попередження": r.get("warnings", ""),
        })

    return output.getvalue()
