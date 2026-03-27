"""Tests for DataMasker."""

import pytest

from app.core.data_masking import DataMasker


class TestMaskDict:
    def test_masks_password(self):
        data = {"username": "alice", "password": "secret123"}
        result = DataMasker.mask_dict(data)
        assert result["username"] == "alice"
        assert "secret" not in result["password"]
        assert "***" in result["password"]

    def test_masks_token(self):
        data = {"access_token": "eyJhbGciOiJIUzI1NiJ9.payload.sig"}
        result = DataMasker.mask_dict(data)
        assert "***" in result["access_token"]

    def test_passes_through_non_sensitive(self):
        data = {"name": "Ali", "class": "5-A"}
        assert DataMasker.mask_dict(data) == data

    def test_recursive_masking(self):
        data = {"user": {"password": "topsecret", "name": "Bob"}}
        result = DataMasker.mask_dict(data)
        assert "***" in result["user"]["password"]
        assert result["user"]["name"] == "Bob"

    def test_list_values(self):
        data = {"items": [{"password": "abc123", "id": 1}]}
        result = DataMasker.mask_dict(data)
        assert "***" in result["items"][0]["password"]
        assert result["items"][0]["id"] == 1

    def test_short_secret_replaced_with_stars(self):
        data = {"password": "ab"}
        result = DataMasker.mask_dict(data)
        assert result["password"] == "***"

    def test_case_insensitive_key(self):
        data = {"Authorization": "Bearer token123"}
        result = DataMasker.mask_dict(data)
        assert "***" in result["Authorization"]


class TestMaskPhone:
    def test_masks_middle(self):
        result = DataMasker.mask_phone("+998901234567")
        assert result.startswith("+99890")
        assert "***" in result
        assert result.endswith("67")

    def test_short_phone_returns_stars(self):
        assert DataMasker.mask_phone("12345") == "***"

    def test_empty_returns_stars(self):
        assert DataMasker.mask_phone("") == "***"


class TestMaskEmail:
    def test_masks_local_part(self):
        result = DataMasker.mask_email("alice@example.com")
        assert result.startswith("a***")
        assert "@example.com" in result

    def test_no_at_sign_returns_stars(self):
        assert DataMasker.mask_email("notanemail") == "***"

    def test_empty_returns_stars(self):
        assert DataMasker.mask_email("") == "***"
