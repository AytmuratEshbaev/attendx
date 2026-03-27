"""Input validation and sanitization utilities."""

import html
import re


class InputSanitizer:
    """Sanitize and validate all user inputs to prevent injection attacks."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 500) -> str:
        """Remove HTML tags, null bytes, limit length, and strip whitespace."""
        if not value:
            return value
        # Strip HTML tags with a simple regex (avoids bleach dependency issues)
        cleaned = re.sub(r"<[^>]+>", "", value)
        # Decode HTML entities (e.g. &amp; → &)
        cleaned = html.unescape(cleaned)
        # Remove null bytes
        cleaned = cleaned.replace("\x00", "")
        # Limit length and strip surrounding whitespace
        return cleaned[:max_length].strip()

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IPv4 address format."""
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, ip):
            return False
        parts = ip.split(".")
        return all(0 <= int(p) <= 255 for p in parts)

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number (Uzbekistan / general)."""
        digits = re.sub(r"\D", "", phone)
        return 9 <= len(digits) <= 13

    @staticmethod
    def validate_employee_no(emp_no: str) -> bool:
        """Validate employee number format (alphanumeric, dash, underscore)."""
        return bool(re.match(r"^[A-Za-z0-9\-_]{1,50}$", emp_no))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize uploaded filename — remove dangerous chars and path traversal."""
        cleaned = re.sub(r"[^\w\-_\.]", "_", filename)
        cleaned = cleaned.replace("..", "_")
        return cleaned[:200]

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate webhook URL (http/https only)."""
        pattern = r"^https?://[a-zA-Z0-9\-\.]+(:[0-9]+)?(/.*)?$"
        return bool(re.match(pattern, url))
