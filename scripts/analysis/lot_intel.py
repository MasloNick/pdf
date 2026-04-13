"""Lot intelligence — automatic analysis of what exactly is being sold.

Parses lot title/description and produces a structured understanding:
- What type of asset
- What exactly you buy
- Who is the debtor
- What are the risks
- What is the collection strategy
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


def analyze_lot(lot: Dict[str, Any]) -> Dict[str, Any]:
    """Produce intelligence card for a lot.

    Takes a lot dict (from lots_data or scraper) and returns
    enriched dict with human-readable analysis.
    """
    text = " ".join([
        str(lot.get("what", "")),
        str(lot.get("title", "")),
        str(lot.get("seller", "")),
    ]).lower()

    asset_type = lot.get("asset_type", _detect_type(text))
    info = _build_info(asset_type, lot, text)

    return {
        **lot,
        "asset_type": asset_type,
        "asset_label": info["label"],
        "what_you_buy": info["what_you_buy"],
        "debtor_info": info["debtor_info"],
        "risks": info["risks"],
        "collection_strategy": info["strategy"],
        "recommendation_short": info["recommendation"],
    }


def _detect_type(text: str) -> str:
    if "пул актив" in text or ("кредит" in text and "дебіторськ" in text and "основн" in text):
        return "asset_pool"
    if "телеком" in text:
        return "mixed"
    if "дебіторськ" in text or "дебіторка" in text:
        if any(w in text for w in ("банк", "фгв", "приватбанк", "ощадбанк")):
            return "npl_credit_mixed"
        return "receivable"
    if "кредитн" in text or "позичальник" in text:
        if "юр" in text:
            return "npl_credit_corporate"
        if "іпотек" in text or "забезпечен" in text or "авто" in text:
            return "npl_credit_secured"
        if "беззастав" in text or "картков" in text or "споживч" in text:
            return "npl_credit_unsecured"
        return "npl_credit_mixed"
    if "відступлення" in text or "факторинг" in text:
        return "assignment"
    if "право вимоги" in text or "зобов'язання" in text:
        return "receivable"
    return "unknown"


def _build_info(asset_type: str, lot: Dict[str, Any], text: str) -> Dict[str, str]:
    seller = lot.get("seller", "")
    total = lot.get("total_debt")
    contracts = lot.get("num_contracts")

    # Detect debtor from title/what
    debtor = _extract_debtor(lot)

    TEMPLATES = {
        "npl_credit_unsecured": {
            "label": "NPL: Беззаставні кредити фіз.осіб",
            "what_you_buy": f"Права кредитора за {contracts or '?'} беззаставними кредитними договорами. "
                            "Ви стаєте новим кредитором і маєте право вимагати повернення боргу.",
            "debtor_info": f"Боржники: фізичні особи. {f'Загальний борг: {total:,.0f} грн.' if total else ''}",
            "risks": "Без забезпечення — стягнення тільки з доходів/майна боржника. "
                     "Перевірити: строк позовної давності (3 роки), наявність доходу, виконавчих проваджень.",
            "strategy": "1) Досудове врегулювання (дзвінки, листи) → 2) Позов до суду → "
                        "3) Виконавчий лист → 4) Виконавча служба (стягнення з зарплати/рахунків).",
            "recommendation": "Великі портфелі (1000+ договорів) — працюють на масовості. "
                              "Окремі дрібні борги (<10K) — витрати на стягнення можуть перевищити борг.",
        },
        "npl_credit_secured": {
            "label": "NPL: Забезпечені кредити (іпотека/авто)",
            "what_you_buy": "Права кредитора за кредитами із заставою (нерухомість або транспорт). "
                            "Крім права вимоги боргу — отримуєте право на предмет застави.",
            "debtor_info": f"Боржники з заставним майном. {f'Загальний борг: {total:,.0f} грн.' if total else ''}",
            "risks": "Перевірити: стан застави (не знищена/не продана), обтяження в реєстрі, "
                     "чи не в іпотеці третіх осіб, чи зареєстроване право застави.",
            "strategy": "1) Звернення стягнення на предмет застави (через суд або позасудово) → "
                        "2) Реалізація заставного майна → 3) Задоволення вимог з виручки.",
            "recommendation": "Найвищий recovery rate (15-60%). Ключове — перевірити стан застави ДО покупки.",
        },
        "npl_credit_corporate": {
            "label": "NPL: Кредити юридичних осіб",
            "what_you_buy": f"Права кредитора за кредитами до юр.осіб. {f'Продавець: {seller}.' if seller else ''}",
            "debtor_info": f"{debtor}. ОБОВ'ЯЗКОВО перевірити статус в ЄДР: діюча, в ліквідації, банкрут.",
            "risks": "Головний ризик: юр.особа може бути припинена або в банкрутстві — тоді стягнення неможливе. "
                     "Перевірити через /check-company (ЄДРПОУ).",
            "strategy": "1) Перевірка статусу боржника → 2) Якщо діючий: досудовий → позов → виконавча → "
                        "3) Якщо банкрут: заявити кредиторські вимоги ліквідатору.",
            "recommendation": "Перевіряти КОЖНОГО боржника через ЄДРПОУ. Якщо компанія припинена — ціна = 0.",
        },
        "receivable": {
            "label": "Дебіторська заборгованість",
            "what_you_buy": f"Право вимоги до {debtor or 'контрагента'} за договором поставки/послуг. "
                            "Це НЕ кредит — це борг за товари/послуги.",
            "debtor_info": f"{debtor}. Продавець (банкрут): {seller}.",
            "risks": "Перевірити: наявність первинних документів (акти, накладні), "
                     "визнання боргу боржником, строк давності, платоспроможність боржника.",
            "strategy": "1) Отримати від ліквідатора всі документи → 2) Направити претензію боржнику → "
                        "3) Позов до суду з доказами (акти, договори) → 4) Виконавче провадження.",
            "recommendation": "Якщо борг підтверджений документами і боржник діючий — recovery 10-30%. "
                              "Без документів — ризик програти суд.",
        },
        "asset_pool": {
            "label": "Пул активів (змішаний)",
            "what_you_buy": "Комплексний пул: кредитні права вимоги + дебіторка + можливо основні засоби/транспорт. "
                            "Купуєте все разом одним лотом.",
            "debtor_info": f"{f'{contracts} договорів/активів.' if contracts else ''} {f'Продавець: {seller}.' if seller else ''}",
            "risks": "Змішаний склад — частина активів може бути безнадійною. "
                     "Потрібно аналізувати паспорт торгів детально: які кредити, яка дебіторка, чи є ОЗ.",
            "strategy": "1) Отримати паспорт торгів → 2) Проаналізувати кожну складову окремо → "
                        "3) Оцінити recovery по кожному типу → 4) Порахувати загальну ціну.",
            "recommendation": "Пули від ФГВ — великі обсяги, потребують серйозної аналітики. "
                              "Ціна зазвичай 2-8% від номіналу.",
        },
        "mixed": {
            "label": "Змішаний портфель (кредити + телеком + інше)",
            "what_you_buy": f"Пул різнорідних прав вимоги: кредитні + телекомунікаційні договори. "
                            f"{f'{contracts} договорів.' if contracts else ''}",
            "debtor_info": "Фіз. та юр. особи. Різні типи боргів в одному лоті.",
            "risks": "Телеком-борги зазвичай дрібні і важко стягуються. "
                     "Кредитні — залежить від забезпечення.",
            "strategy": "Масове стягнення: автоматичні претензії → судові накази → виконавчі.",
            "recommendation": "Ефективно тільки при великих обсягах (10K+ договорів). "
                              "Потрібна автоматизація процесів.",
        },
        "assignment": {
            "label": "Відступлення права вимоги",
            "what_you_buy": "Банк/ФК відступає своє право вимоги за кредитним договором. "
                            "Ви стаєте новим кредитором замість банку.",
            "debtor_info": f"{debtor}. {f'Продавець: {seller}.' if seller else ''}",
            "risks": "Перевірити: чи повідомлений боржник про відступлення, "
                     "чи не оспорюється договір відступлення.",
            "strategy": "1) Повідомити боржника → 2) Досудове → 3) Суд → 4) Виконання.",
            "recommendation": "Стандартна процедура. Ключове — якість документації від продавця.",
        },
    }

    template = TEMPLATES.get(asset_type, {
        "label": "Не класифіковано",
        "what_you_buy": "Потрібно вивчити документацію лота.",
        "debtor_info": debtor or "Невідомо",
        "risks": "Потрібен детальний аналіз.",
        "strategy": "Залежить від типу активу.",
        "recommendation": "Перевірити на сайті торгів.",
    })

    return template


def _extract_debtor(lot: Dict[str, Any]) -> str:
    """Try to extract debtor name from lot data."""
    what = lot.get("what", "")

    # "до Макаренко В.С." pattern
    match = re.search(r"до\s+(.+?)(?:\s*[—\-]\s*\d|\s*$)", what)
    if match:
        return match.group(1).strip()

    # "ТОВ «...»" pattern
    match = re.search(r'(ТОВ|ПрАТ|АТ|ФОП|ФГ)\s*[«"]?([^»"]+)', what)
    if match:
        return f"{match.group(1)} {match.group(2).strip()}"

    return ""
