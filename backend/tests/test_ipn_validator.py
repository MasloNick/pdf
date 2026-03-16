"""Tests for Ukrainian IPN validator."""

import pytest
from app.services.ipn_validator import validate_ipn, extract_birth_date_from_ipn


def test_valid_ipn():
    # Well-known test IPN with valid checksum
    is_valid, error = validate_ipn("3184710691")
    assert is_valid, f"Expected valid but got: {error}"


def test_empty_ipn():
    is_valid, error = validate_ipn("")
    assert not is_valid
    assert "empty" in error.lower()


def test_short_ipn():
    is_valid, error = validate_ipn("12345")
    assert not is_valid
    assert "10 digits" in error


def test_non_digit_ipn():
    is_valid, error = validate_ipn("123456789A")
    assert not is_valid
    assert "digits" in error.lower()


def test_invalid_checksum():
    is_valid, error = validate_ipn("1234567890")
    assert not is_valid
    assert "checksum" in error.lower()


def test_extract_birth_date():
    result = extract_birth_date_from_ipn("3184710691")
    assert result is not None
    # IPN 31847 => 31847 days after 31.12.1899
