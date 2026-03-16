"""Court fee calculator for Ukrainian judicial system.

Based on the Law of Ukraine "On Court Fees" (Закон України "Про судовий збір").
Fee rates are calculated relative to the "prozhytkovyy minimum" (прожитковий мінімум)
for able-bodied persons as of January 1 of the current year.

NOTE: These rates are for informational purposes only and may change.
Always verify with the current legislation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# Прожитковий мінімум для працездатних осіб (станом на 01.01.2025)
LIVING_WAGE = 3028.0  # грн

# Мінімальна заробітна плата (станом на 01.01.2025)
MIN_WAGE = 8000.0  # грн


@dataclass
class FeeResult:
    """Result of fee calculation."""

    amount: float
    description: str
    basis: str
    category: str
    notes: List[str]

    @property
    def formatted_amount(self) -> str:
        return f"{self.amount:,.2f} грн"


# Court fee rates by category
# Format: (description, rate_type, rate_value, min_value, max_value)
# rate_type: "percent" = % of claim amount, "living_wage" = multiplier of living wage,
#            "min_wage" = multiplier of min wage, "fixed" = fixed amount

FEE_RATES: Dict[str, List[Tuple[str, str, float, float, float]]] = {
    "civil": [
        ("Позов майнового характеру (фіз. особа)", "percent", 1.0, LIVING_WAGE * 0.4, None),
        ("Позов майнового характеру (юр. особа)", "percent", 1.5, LIVING_WAGE, None),
        ("Позов немайнового характеру (фіз. особа)", "living_wage", 0.4, 0, None),
        ("Позов немайнового характеру (юр. особа)", "living_wage", 1.0, 0, None),
        ("Заява про видачу судового наказу", "percent", 0.5, LIVING_WAGE * 0.2, None),
        ("Заява про забезпечення позову", "living_wage", 0.5, 0, None),
        ("Апеляційна скарга на рішення (фіз. особа)", "percent", 1.5, LIVING_WAGE * 0.6, None),
        ("Апеляційна скарга на рішення (юр. особа)", "percent", 2.25, LIVING_WAGE * 1.5, None),
        ("Касаційна скарга на рішення (фіз. особа)", "percent", 2.0, LIVING_WAGE * 0.8, None),
        ("Касаційна скарга на рішення (юр. особа)", "percent", 3.0, LIVING_WAGE * 2.0, None),
        ("Заява про розлучення", "living_wage", 0.4, 0, None),
        ("Заява про зміну імені", "living_wage", 0.3, 0, None),
    ],
    "commercial": [
        ("Позов майнового характеру", "percent", 1.5, LIVING_WAGE, None),
        ("Позов немайнового характеру", "living_wage", 1.0, 0, None),
        ("Заява про забезпечення позову", "living_wage", 1.0, 0, None),
        ("Заява про визнання банкрутом", "living_wage", 8.0, 0, None),
        ("Апеляційна скарга", "percent", 2.25, LIVING_WAGE * 1.5, None),
        ("Касаційна скарга", "percent", 3.0, LIVING_WAGE * 2.0, None),
    ],
    "admin": [
        ("Позов фіз. особи", "living_wage", 0.4, 0, None),
        ("Позов юр. особи", "living_wage", 1.0, 0, None),
        ("Позов суб'єкта владних повноважень", "living_wage", 1.5, 0, None),
        ("Апеляційна скарга (фіз. особа)", "living_wage", 0.6, 0, None),
        ("Апеляційна скарга (юр. особа)", "living_wage", 1.5, 0, None),
        ("Касаційна скарга (фіз. особа)", "living_wage", 0.8, 0, None),
        ("Касаційна скарга (юр. особа)", "living_wage", 2.0, 0, None),
    ],
}

FEE_CATEGORIES = {
    "civil": "Цивільне судочинство",
    "commercial": "Господарське судочинство",
    "admin": "Адміністративне судочинство",
}


def calculate_fee(
    category: str,
    fee_index: int,
    claim_amount: float = 0.0,
) -> FeeResult:
    """Calculate court fee for a given category and fee type.

    Args:
        category: One of 'civil', 'commercial', 'admin'.
        fee_index: Index into the fee rate list for the category.
        claim_amount: Amount of the claim (for percentage-based fees).

    Returns:
        FeeResult with the calculated amount and description.
    """
    rates = FEE_RATES.get(category, [])
    if fee_index < 0 or fee_index >= len(rates):
        return FeeResult(
            amount=0,
            description="Невідомий тип збору",
            basis="",
            category=category,
            notes=["Помилка: невідомий індекс типу збору"],
        )

    desc, rate_type, rate_value, min_val, max_val = rates[fee_index]
    notes = []
    amount = 0.0
    basis = ""

    if rate_type == "percent":
        if claim_amount <= 0:
            notes.append("Необхідно вказати суму позову для розрахунку")
            amount = min_val or 0
            basis = f"{rate_value}% від суми позову"
        else:
            amount = claim_amount * rate_value / 100.0
            basis = f"{rate_value}% від {claim_amount:,.2f} грн"
            if min_val and amount < min_val:
                notes.append(f"Мінімальний збір: {min_val:,.2f} грн")
                amount = min_val
    elif rate_type == "living_wage":
        amount = LIVING_WAGE * rate_value
        basis = f"{rate_value} × прожитковий мінімум ({LIVING_WAGE:,.2f} грн)"
    elif rate_type == "min_wage":
        amount = MIN_WAGE * rate_value
        basis = f"{rate_value} × мінімальна зарплата ({MIN_WAGE:,.2f} грн)"
    elif rate_type == "fixed":
        amount = rate_value
        basis = "Фіксована ставка"

    if max_val and amount > max_val:
        notes.append(f"Максимальний збір: {max_val:,.2f} грн")
        amount = max_val

    amount = round(amount, 2)

    notes.append("Ставки наведено відповідно до ЗУ «Про судовий збір»")
    notes.append(f"Прожитковий мінімум: {LIVING_WAGE:,.2f} грн")

    return FeeResult(
        amount=amount,
        description=desc,
        basis=basis,
        category=FEE_CATEGORIES.get(category, category),
        notes=notes,
    )


def get_fee_options(category: str) -> List[Dict[str, str]]:
    """Return available fee types for a category."""
    rates = FEE_RATES.get(category, [])
    return [
        {"index": i, "description": desc, "rate_type": rt}
        for i, (desc, rt, *_) in enumerate(rates)
    ]


# Standard procedural deadlines (in calendar days unless noted)
PROCEDURAL_DEADLINES = {
    "civil": [
        {"name": "Подання позовної заяви", "days": None, "note": "Строк позовної давності — 3 роки (загальний)"},
        {"name": "Відкриття провадження", "days": 5, "note": "Робочих днів з дня надходження"},
        {"name": "Відповідь на відзив", "days": 15, "note": "Від дня отримання копії відзиву"},
        {"name": "Підготовче засідання", "days": 60, "note": "Від дня відкриття провадження"},
        {"name": "Розгляд справи", "days": 30, "note": "Від закінчення підготовки"},
        {"name": "Апеляційна скарга", "days": 30, "note": "Від дня проголошення рішення"},
        {"name": "Касаційна скарга", "days": 30, "note": "Від дня складення повного рішення апеляційного суду"},
        {"name": "Заява про перегляд за нововиявленими обставинами", "days": 30, "note": "Від дня встановлення обставин"},
    ],
    "commercial": [
        {"name": "Відкриття провадження", "days": 5, "note": "Робочих днів"},
        {"name": "Відзив на позов", "days": 15, "note": "Від дня вручення ухвали"},
        {"name": "Підготовче провадження", "days": 60, "note": "Від відкриття провадження"},
        {"name": "Розгляд справи по суті", "days": 30, "note": "Від закінчення підготовки"},
        {"name": "Апеляційна скарга", "days": 20, "note": "Від дня складення повного рішення"},
        {"name": "Касаційна скарга", "days": 20, "note": "Від дня складення повного постанови"},
    ],
    "admin": [
        {"name": "Відкриття провадження", "days": 5, "note": "Робочих днів"},
        {"name": "Відзив на позов", "days": 15, "note": "Від дня вручення ухвали"},
        {"name": "Підготовче провадження", "days": 60, "note": "Від відкриття провадження"},
        {"name": "Апеляційна скарга", "days": 30, "note": "Від дня складення повного рішення"},
        {"name": "Касаційна скарга", "days": 30, "note": "Від дня складення повного постанови"},
    ],
}
