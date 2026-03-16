"""Ukrainian IPN (РНОКПП) validator with checksum."""


def validate_ipn(ipn: str) -> tuple[bool, str]:
    """
    Validate Ukrainian IPN (individual tax number).
    Returns (is_valid, error_message).
    """
    if not ipn:
        return False, "IPN is empty"

    ipn = ipn.strip()

    if len(ipn) != 10:
        return False, f"IPN must be 10 digits, got {len(ipn)}"

    if not ipn.isdigit():
        return False, "IPN must contain only digits"

    # Checksum validation
    weights = [-1, 5, 7, 9, 4, 6, 10, 5, 7]
    checksum = sum(int(ipn[i]) * weights[i] for i in range(9)) % 11 % 10

    if checksum != int(ipn[9]):
        return False, "IPN checksum validation failed"

    return True, ""


def extract_birth_date_from_ipn(ipn: str) -> str | None:
    """
    Extract approximate birth date from IPN.
    First 5 digits = days since 01.01.1900.
    """
    if not ipn or len(ipn) != 10 or not ipn.isdigit():
        return None

    from datetime import date, timedelta

    days = int(ipn[:5])
    try:
        birth = date(1899, 12, 31) + timedelta(days=days)
        return birth.isoformat()
    except (ValueError, OverflowError):
        return None
