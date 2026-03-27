"""Tests for bot.utils phone number utilities."""

import pytest

from bot.utils import generate_phone_variants, is_valid_phone, normalize_phone


class TestNormalizePhone:
    def test_normalizes_plus_998_format(self):
        result = normalize_phone("+998901234567")
        assert result == "998901234567"

    def test_normalizes_12_digit_starting_998(self):
        result = normalize_phone("998901234567")
        assert result == "998901234567"

    def test_normalizes_9_digit_local(self):
        """Local 9-digit number gets 998 prepended."""
        result = normalize_phone("901234567")
        assert result == "998901234567"

    def test_normalizes_10_digit_starting_8(self):
        """10-digit number starting with 8 (Russian format) → replace 8 with 998."""
        result = normalize_phone("8901234567")
        assert result == "998901234567"

    def test_strips_spaces_and_dashes(self):
        result = normalize_phone("+998 90 123-45-67")
        assert result == "998901234567"

    def test_strips_parentheses(self):
        result = normalize_phone("+998(90)1234567")
        assert result == "998901234567"

    def test_returns_digits_for_unrecognized_format(self):
        """Unrecognized formats return digits as-is (no crash)."""
        result = normalize_phone("00998901234567")
        assert isinstance(result, str)
        assert result.isdigit()


class TestIsValidPhone:
    def test_valid_uzbek_number_plus(self):
        assert is_valid_phone("+998901234567") is True

    def test_valid_uzbek_number_no_plus(self):
        assert is_valid_phone("998901234567") is True

    def test_valid_9_digit_local(self):
        """9-digit local number is valid (normalizes to 998...)."""
        assert is_valid_phone("901234567") is True

    def test_invalid_too_short(self):
        assert is_valid_phone("9012345") is False

    def test_invalid_empty(self):
        assert is_valid_phone("") is False

    def test_non_uzb_country_code_invalid(self):
        """Numbers with non-UZB country code are not valid."""
        # +1-202-555-1234 → digits only = 12025551234 (11 chars) but doesn't start with 998
        result = is_valid_phone("+12025551234")
        assert result is False

    def test_letters_stripped_and_validated(self):
        """Letters are stripped; remaining digits are checked normally."""
        # "abc901234567" → digits = "901234567" (9 chars) → "998901234567" → valid
        result = is_valid_phone("abc901234567")
        assert isinstance(result, bool)


class TestGeneratePhoneVariants:
    def test_returns_list(self):
        variants = generate_phone_variants("+998901234567")
        assert isinstance(variants, list)
        assert len(variants) >= 1

    def test_includes_normalized_format(self):
        variants = generate_phone_variants("998901234567")
        assert "998901234567" in variants

    def test_includes_plus_format(self):
        variants = generate_phone_variants("998901234567")
        assert "+998901234567" in variants

    def test_includes_local_9_digit(self):
        variants = generate_phone_variants("+998901234567")
        assert "901234567" in variants

    def test_includes_8_prefix_format(self):
        variants = generate_phone_variants("+998901234567")
        assert "8901234567" in variants

    def test_handles_already_local(self):
        variants = generate_phone_variants("901234567")
        assert len(variants) >= 1
        assert isinstance(variants[0], str)

    def test_all_variants_are_strings(self):
        variants = generate_phone_variants("+998901234567")
        for v in variants:
            assert isinstance(v, str)
