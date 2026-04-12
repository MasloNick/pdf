"""Історія цін та ринкова аналітика NPL-портфелів.

Модуль для запису продажів, аналізу ринкових трендів та імпорту
історичних даних із CSV.  Працює з таблицею ``price_history`` в SQLite.

Усі текстові мітки — українською.
"""

from __future__ import annotations

import csv
import io
import sqlite3
import statistics
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Внутрішні допоміжні функції
# ---------------------------------------------------------------------------

def _float(val: Any) -> float:
    """Безпечне перетворення на float."""
    if val is None or val == "":
        return 0.0
    try:
        if isinstance(val, str):
            val = (
                val.replace("\xa0", "")
                .replace(" ", "")
                .replace(",", ".")
                .replace("грн", "")
                .strip()
            )
        return float(val)
    except (ValueError, TypeError):
        return 0.0


_EXTRA_COLUMNS: List[Tuple[str, str]] = [
    ("total_debt", "REAL"),
    ("portfolio_type", "TEXT"),
    ("seller", "TEXT"),
    ("seller_type", "TEXT"),
    ("buyer", "TEXT"),
    ("notes", "TEXT"),
    ("sale_date", "TEXT"),
]


def _ensure_columns(conn: sqlite3.Connection) -> None:
    """Додає відсутні колонки до price_history (ідемпотентно).

    Таблиця вже створена в ``models.init_db`` із базовими полями.  Цей
    модуль розширює її, щоб зберігати повну інформацію про кожний продаж.
    """
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(price_history)").fetchall()
    }
    for col_name, col_type in _EXTRA_COLUMNS:
        if col_name not in existing:
            conn.execute(
                f"ALTER TABLE price_history ADD COLUMN {col_name} {col_type}"
            )
    conn.commit()


def _normalize_seller_type(seller: str) -> str:
    """Визначає тип продавця за назвою (евристика)."""
    s = seller.lower()
    if any(kw in s for kw in ("банк", "bank")):
        return "банк"
    if any(kw in s for kw in ("мфо", "mfo", "мікрофінанс")):
        return "МФО"
    if any(kw in s for kw in ("фк", "fc", "фінансова компанія", "факторинг")):
        return "ФК"
    if any(kw in s for kw in ("фгвфо", "dgf", "фонд гарантування")):
        return "ФГВФО"
    return "інше"


def _parse_date(raw: str) -> str:
    """Спроба розпізнати дату у різних форматах -> ISO (YYYY-MM-DD)."""
    raw = raw.strip()
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Якщо нічого не підійшло — повертаємо як є
    return raw


# ---------------------------------------------------------------------------
# 1. Запис продажу
# ---------------------------------------------------------------------------

def record_sale(
    conn: sqlite3.Connection,
    auction_id: int,
    sale_price: float,
    total_debt: float,
    portfolio_type: str,
    seller: str,
    buyer: str = "",
    notes: str = "",
) -> int:
    """Записати продаж портфеля в ``price_history``.

    Parameters
    ----------
    conn : sqlite3.Connection
        З'єднання з базою даних.
    auction_id : int
        Ідентифікатор аукціону (FK → auctions.id).  Може бути 0/None,
        якщо продаж імпортовано без прив'язки до конкретного аукціону.
    sale_price : float
        Ціна продажу (грн).
    total_debt : float
        Загальна сума боргу портфеля (грн).
    portfolio_type : str
        Тип портфеля: ``physical`` / ``legal`` / ``mixed``.
    seller : str
        Назва продавця.
    buyer : str
        Назва покупця (необов'язково).
    notes : str
        Додаткові примітки.

    Returns
    -------
    int
        ``id`` вставленого рядка.
    """
    _ensure_columns(conn)

    price_per_debt = round(sale_price / total_debt, 6) if total_debt > 0 else 0.0
    seller_type = _normalize_seller_type(seller)
    now = time.time()
    today_iso = datetime.utcnow().strftime("%Y-%m-%d")

    cur = conn.execute(
        """
        INSERT INTO price_history
            (auction_id, price, price_per_debt, total_debt,
             portfolio_type, seller, seller_type, buyer, notes,
             sale_date, recorded_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            auction_id or None,
            sale_price,
            price_per_debt,
            total_debt,
            portfolio_type,
            seller,
            seller_type,
            buyer,
            notes,
            today_iso,
            now,
        ),
    )
    conn.commit()
    return cur.lastrowid or 0


# ---------------------------------------------------------------------------
# 2. Ринкова статистика
# ---------------------------------------------------------------------------

def get_market_stats(
    conn: sqlite3.Connection,
    portfolio_type: str = "",
    period_months: int = 12,
) -> Dict[str, Any]:
    """Отримати агреговану ринкову статистику за заданий період.

    Parameters
    ----------
    conn : sqlite3.Connection
        З'єднання з базою даних.
    portfolio_type : str
        Фільтр за типом портфеля (порожній рядок = усі типи).
    period_months : int
        Кількість місяців від поточної дати для вибірки.

    Returns
    -------
    dict
        Структура з ринковою аналітикою (див. опис нижче).
    """
    _ensure_columns(conn)

    cutoff_ts = time.time() - period_months * 30.44 * 86400  # приблизно

    base_sql = """
        SELECT id, auction_id, price, price_per_debt, total_debt,
               portfolio_type, seller, seller_type, buyer, notes,
               sale_date, recorded_at
        FROM price_history
        WHERE recorded_at >= ?
    """
    params: list = [cutoff_ts]

    if portfolio_type:
        base_sql += " AND portfolio_type = ?"
        params.append(portfolio_type)

    base_sql += " ORDER BY recorded_at DESC"

    rows = conn.execute(base_sql, params).fetchall()

    # Порожній результат
    if not rows:
        return {
            "період_місяців": period_months,
            "фільтр_тип": portfolio_type or "всі",
            "всього_продажів": 0,
            "середня_ціна_відсоток": 0.0,
            "мін_ціна_відсоток": 0.0,
            "макс_ціна_відсоток": 0.0,
            "медіана_ціна_відсоток": 0.0,
            "за_типом_портфеля": {},
            "за_типом_продавця": {},
            "останні_продажі": [],
        }

    # Збір відсотків ціна/борг
    pcts: List[float] = []
    by_type: Dict[str, List[float]] = {}
    by_seller: Dict[str, List[float]] = {}

    for r in rows:
        pct = (r[3] or 0.0) * 100  # price_per_debt → %
        pcts.append(pct)

        pt = r[5] or "невизначено"
        by_type.setdefault(pt, []).append(pct)

        st = r[7] or "невизначено"
        by_seller.setdefault(st, []).append(pct)

    # Агрегація за типом портфеля
    type_stats: Dict[str, Dict[str, Any]] = {}
    for t, vals in sorted(by_type.items()):
        type_stats[t] = {
            "кількість": len(vals),
            "середній_відсоток": round(statistics.mean(vals), 2),
        }

    # Агрегація за типом продавця
    seller_stats: Dict[str, Dict[str, Any]] = {}
    for s, vals in sorted(by_seller.items()):
        seller_stats[s] = {
            "кількість": len(vals),
            "середній_відсоток": round(statistics.mean(vals), 2),
        }

    # Останні 20 продажів
    recent: List[Dict[str, Any]] = []
    for r in rows[:20]:
        recent.append({
            "дата": r[10] or "",
            "тип_портфеля": r[5] or "",
            "продавець": r[6] or "",
            "ціна": r[2] or 0.0,
            "борг": r[4] or 0.0,
            "відсоток": round((r[3] or 0.0) * 100, 2),
        })

    return {
        "період_місяців": period_months,
        "фільтр_тип": portfolio_type or "всі",
        "всього_продажів": len(pcts),
        "середня_ціна_відсоток": round(statistics.mean(pcts), 2),
        "мін_ціна_відсоток": round(min(pcts), 2),
        "макс_ціна_відсоток": round(max(pcts), 2),
        "медіана_ціна_відсоток": round(statistics.median(pcts), 2),
        "за_типом_портфеля": type_stats,
        "за_типом_продавця": seller_stats,
        "останні_продажі": recent,
    }


# ---------------------------------------------------------------------------
# 3. Імпорт історичних продажів із CSV
# ---------------------------------------------------------------------------

# Маппінг колонок (укр. / англ. → внутрішнє ім'я)
_CSV_COLUMN_MAP: Dict[str, List[str]] = {
    "date": ["дата", "date", "дата продажу", "sale_date"],
    "seller": ["продавець", "seller", "банк", "продавец"],
    "buyer": ["покупець", "buyer", "покупатель"],
    "portfolio_type": ["тип", "type", "тип портфеля", "portfolio_type"],
    "total_debt": ["борг", "debt", "total_debt", "загальний борг", "сума боргу"],
    "price": ["ціна", "price", "ціна продажу", "sale_price"],
    "notes": ["примітки", "notes", "коментар", "нотатки"],
}


def import_historical_sales_csv(
    conn: sqlite3.Connection,
    csv_text: str,
) -> Dict[str, Any]:
    """Імпортувати історичні продажі з CSV-тексту.

    Очікувані колонки (допускаються українські та англійські назви):
    ``дата``, ``продавець``, ``покупець``, ``тип``, ``борг``, ``ціна``,
    ``примітки``.

    Parameters
    ----------
    conn : sqlite3.Connection
        З'єднання з базою даних.
    csv_text : str
        Вміст CSV-файлу як рядок.

    Returns
    -------
    dict
        ``{"imported": N, "warnings": [...]}``
    """
    _ensure_columns(conn)

    warnings: List[str] = []
    reader = csv.DictReader(io.StringIO(csv_text))

    if not reader.fieldnames:
        return {"imported": 0, "warnings": ["CSV порожній або не має заголовків."]}

    # Побудова маппінгу: оригінальна колонка CSV → внутрішнє ім'я
    header_map: Dict[str, str] = {}
    lower_fields = {f.strip().lower(): f for f in reader.fieldnames}
    for internal_name, aliases in _CSV_COLUMN_MAP.items():
        for alias in aliases:
            if alias.lower() in lower_fields:
                header_map[lower_fields[alias.lower()]] = internal_name
                break

    # Перевірка обов'язкових колонок
    mapped_internal = set(header_map.values())
    if "price" not in mapped_internal:
        warnings.append("Не знайдено колонку з ціною продажу (ціна/price).")
        return {"imported": 0, "warnings": warnings}
    if "total_debt" not in mapped_internal:
        warnings.append(
            "Не знайдено колонку з сумою боргу (борг/debt). "
            "Відсоток ціна/борг не буде розраховано."
        )

    imported = 0

    for row_num, row in enumerate(reader, start=2):
        # Зчитування полів через маппінг
        raw: Dict[str, str] = {}
        for csv_col, internal in header_map.items():
            raw[internal] = (row.get(csv_col) or "").strip()

        price = _float(raw.get("price", ""))
        debt = _float(raw.get("total_debt", ""))
        seller = raw.get("seller", "")
        buyer = raw.get("buyer", "")
        ptype = raw.get("portfolio_type", "")
        notes = raw.get("notes", "")
        date_raw = raw.get("date", "")

        # Валідація
        if price <= 0:
            warnings.append(
                f"Рядок {row_num}: пропущено — ціна <= 0 або відсутня."
            )
            continue

        if debt <= 0 and "total_debt" in mapped_internal:
            warnings.append(
                f"Рядок {row_num}: борг <= 0, відсоток не розраховано."
            )

        price_per_debt = round(price / debt, 6) if debt > 0 else 0.0
        seller_type = _normalize_seller_type(seller)
        sale_date = _parse_date(date_raw)

        # Визначаємо recorded_at: якщо є дата — конвертуємо, інакше now
        if sale_date:
            try:
                recorded_at = datetime.strptime(sale_date, "%Y-%m-%d").timestamp()
            except ValueError:
                recorded_at = time.time()
        else:
            recorded_at = time.time()

        conn.execute(
            """
            INSERT INTO price_history
                (auction_id, price, price_per_debt, total_debt,
                 portfolio_type, seller, seller_type, buyer, notes,
                 sale_date, recorded_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                None,  # auction_id — історичні дані без прив'язки
                price,
                price_per_debt,
                debt,
                ptype,
                seller,
                seller_type,
                buyer,
                notes,
                sale_date,
                recorded_at,
            ),
        )
        imported += 1

    conn.commit()

    if imported == 0 and not warnings:
        warnings.append("CSV не містить жодного валідного рядка з продажем.")

    return {"imported": imported, "warnings": warnings}
