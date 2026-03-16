"""Tests for the rule-based court decision parser."""

from decimal import Decimal

from app.ai_parser.pipeline import rule_based_parse


def test_satisfied_outcome():
    text = "Суд вирішив: позов задовольнити повністю. Стягнути основну суму 15000,00 грн."
    result = rule_based_parse(text)
    assert result.outcome == "satisfied"
    assert result.confidence >= 0.65


def test_partial_outcome():
    text = "Суд постановив позов задовольнити частково."
    result = rule_based_parse(text)
    assert result.outcome == "partial"


def test_rejected_outcome():
    text = "У задоволенні позову відмовити повністю."
    result = rule_based_parse(text)
    assert result.outcome == "rejected"


def test_amount_extraction():
    text = (
        "Позов задовольнити. Стягнути основну суму боргу 50 000,50 грн "
        "та судовий збір 2 500,00 грн."
    )
    result = rule_based_parse(text)
    assert result.awarded_principal == Decimal("50000.50")
    assert result.awarded_court_fee == Decimal("2500.00")
    assert result.awarded_total == Decimal("52500.50")


def test_needs_review_when_no_outcome():
    text = "Якийсь текст без маркерів рішення."
    result = rule_based_parse(text)
    assert result.needs_review is True
    assert result.confidence < 0.65
