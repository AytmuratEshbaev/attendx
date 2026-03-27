"""Phone number utilities for Uzbekistan numbers."""

import re


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to consistent 12-digit format (no + prefix).

    Input variants: +998901234567, 998901234567, 8901234567, 901234567
    Output: 998901234567
    """
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 12 and digits.startswith("998"):
        return digits
    elif len(digits) == 9:
        return f"998{digits}"
    elif len(digits) == 10 and digits.startswith("8"):
        return f"998{digits[1:]}"
    elif len(digits) == 13 and digits.startswith("8998"):
        return digits[1:]

    return digits


def generate_phone_variants(phone: str) -> list[str]:
    """
    Generate all possible phone format variants for DB search.

    Handles cases where parent_phone was entered in different formats.
    """
    normalized = normalize_phone(phone)

    if len(normalized) == 12 and normalized.startswith("998"):
        short = normalized[3:]  # 901234567
        return [
            normalized,  # 998901234567
            f"+{normalized}",  # +998901234567
            short,  # 901234567
            f"8{short}",  # 8901234567
            f"+998{short}",  # +998901234567
            f"+998 {short[:2]} {short[2:5]} {short[5:]}",  # +998 90 123 4567
        ]

    return [phone, normalized]


def is_valid_phone(phone: str) -> bool:
    """Validate Uzbekistan phone number format."""
    normalized = normalize_phone(phone)
    return len(normalized) == 12 and normalized.startswith("998")
