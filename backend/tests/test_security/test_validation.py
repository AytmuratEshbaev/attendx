"""Tests for input sanitization and validation utilities."""

import pytest

from app.core.validation import InputSanitizer


class TestSanitizeString:
    def test_strips_html_tags(self):
        assert InputSanitizer.sanitize_string("<b>hello</b>") == "hello"

    def test_strips_nested_html(self):
        result = InputSanitizer.sanitize_string("<script>alert('xss')</script>text")
        assert "<script>" not in result
        assert "text" in result

    def test_removes_null_bytes(self):
        assert "\x00" not in InputSanitizer.sanitize_string("hello\x00world")

    def test_respects_max_length(self):
        assert len(InputSanitizer.sanitize_string("a" * 1000, max_length=50)) == 50

    def test_strips_whitespace(self):
        assert InputSanitizer.sanitize_string("  hello  ") == "hello"

    def test_empty_string_returned_as_is(self):
        assert InputSanitizer.sanitize_string("") == ""

    def test_decodes_html_entities(self):
        result = InputSanitizer.sanitize_string("&amp;hello&lt;world&gt;")
        assert "&amp;" not in result
        assert "&" in result


class TestValidateIpAddress:
    def test_valid_ipv4(self):
        assert InputSanitizer.validate_ip_address("192.168.1.100") is True
        assert InputSanitizer.validate_ip_address("0.0.0.0") is True
        assert InputSanitizer.validate_ip_address("255.255.255.255") is True

    def test_invalid_ipv4(self):
        assert InputSanitizer.validate_ip_address("256.0.0.1") is False
        assert InputSanitizer.validate_ip_address("abc.def.ghi.jkl") is False
        assert InputSanitizer.validate_ip_address("192.168.1") is False
        assert InputSanitizer.validate_ip_address("") is False

    def test_hostname_rejected(self):
        assert InputSanitizer.validate_ip_address("example.com") is False


class TestValidatePhone:
    def test_valid_phones(self):
        assert InputSanitizer.validate_phone("+998901234567") is True
        assert InputSanitizer.validate_phone("998901234567") is True
        assert InputSanitizer.validate_phone("901234567") is True

    def test_too_short_rejected(self):
        assert InputSanitizer.validate_phone("12345") is False

    def test_too_long_rejected(self):
        assert InputSanitizer.validate_phone("1" * 14) is False


class TestSanitizeFilename:
    def test_removes_path_separators(self):
        result = InputSanitizer.sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_removes_dangerous_chars(self):
        result = InputSanitizer.sanitize_filename("file<>name.txt")
        assert "<" not in result
        assert ">" not in result

    def test_keeps_valid_chars(self):
        result = InputSanitizer.sanitize_filename("my-file_name.xlsx")
        assert result == "my-file_name.xlsx"

    def test_max_length(self):
        assert len(InputSanitizer.sanitize_filename("a" * 300)) <= 200


class TestValidateUrl:
    def test_valid_https(self):
        assert InputSanitizer.validate_url("https://example.com/webhook") is True

    def test_valid_http(self):
        assert InputSanitizer.validate_url("http://localhost:8080/hook") is True

    def test_invalid_scheme(self):
        assert InputSanitizer.validate_url("ftp://example.com") is False
        assert InputSanitizer.validate_url("javascript:alert(1)") is False

    def test_empty_rejected(self):
        assert InputSanitizer.validate_url("") is False
