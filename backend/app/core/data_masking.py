"""Sensitive data masking for logs, audit trails, and error reports."""


class DataMasker:
    """Mask sensitive fields in dicts, phone numbers, and email addresses."""

    SENSITIVE_FIELDS = {
        "password",
        "password_hash",
        "password_enc",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "fernet_key",
        "jwt_secret",
        "authorization",
        "x-api-key",
        "cookie",
        "key_hash",
    }

    @classmethod
    def mask_dict(cls, data: dict, depth: int = 0) -> dict:
        """Recursively mask sensitive fields in a dictionary."""
        if depth > 10:
            return data

        masked: dict = {}
        for key, value in data.items():
            if key.lower() in cls.SENSITIVE_FIELDS:
                if isinstance(value, str) and len(value) > 4:
                    masked[key] = value[:2] + "***" + value[-2:]
                else:
                    masked[key] = "***"
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value, depth + 1)
            elif isinstance(value, list):
                masked[key] = [
                    cls.mask_dict(item, depth + 1) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        return masked

    @classmethod
    def mask_phone(cls, phone: str) -> str:
        """Mask phone: +998 90 *** ** 67 → show first 6 and last 2 digits."""
        if not phone or len(phone) < 6:
            return "***"
        return phone[:6] + "***" + phone[-2:]

    @classmethod
    def mask_email(cls, email: str) -> str:
        """Mask email: alice@example.com → a***@example.com"""
        if not email or "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        return local[0] + "***@" + domain
