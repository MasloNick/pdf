"""Tests for rule-based court decision parser."""

from decimal import Decimal

from app.parsers.decision_parser import RuleBasedParser


def test_satisfied_decision():
    text = """
    Розглянувши справу, суд
    ВИРІШИВ:
    Позовні вимоги задовольнити.
    Стягнути з відповідача на користь позивача 150 000,50 грн.
    Судовий збір у сумі 2 270,00 грн стягнути з відповідача.
    """
    parser = RuleBasedParser()
    result = parser.parse(text)
    assert result.result == "satisfied"
    assert result.confidence >= 0.65
    assert result.awarded_total == Decimal("150000.50")
    assert result.awarded_court_fee == Decimal("2270.00")


def test_denied_decision():
    text = """
    Розглянувши справу, суд
    ВИРІШИВ:
    У задоволенні позову відмовити.
    """
    parser = RuleBasedParser()
    result = parser.parse(text)
    assert result.result == "denied"
    assert result.confidence >= 0.65


def test_partially_satisfied():
    text = """
    УХВАЛИВ:
    Позов задоволити частково.
    Стягнути з відповідача 75 000,00 грн основного боргу.
    """
    parser = RuleBasedParser()
    result = parser.parse(text)
    assert result.result == "partially_satisfied"
    assert result.awarded_total == Decimal("75000.00")


def test_missing_decision():
    text = "Просто якийсь текст без рішення суду."
    parser = RuleBasedParser()
    result = parser.parse(text)
    assert result.result == "MISSING_IN_DECISION"
    assert result.needs_review is True
    assert result.confidence == 0.0
