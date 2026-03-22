"""Tests for security.py"""

import pytest
from datetime import timedelta
from unittest.mock import patch

from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


@pytest.mark.unit
class TestSecurity:
    """Test suite for security.py functions."""

    def test_hash_password_returns_bcrypt_hash(self):
        """Test hash_password returns a bcrypt hash (not plain text)."""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0
        # Bcrypt hashes start with $2a$, $2b$, or $2y$
        assert hashed.startswith("$2")

    def test_verify_password_correct(self):
        """Test verify_password returns True for correct password."""
        password = "my_secure_password"
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_verify_password_incorrect(self):
        """Test verify_password returns False for wrong password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        result = verify_password(wrong_password, hashed)

        assert result is False

    def test_verify_password_case_sensitive(self):
        """Test verify_password is case sensitive."""
        password = "MyPassword123"
        hashed = hash_password(password)

        result = verify_password("mypassword123", hashed)

        assert result is False

    def test_hash_same_password_different_hash(self):
        """Test that hashing same password produces different hashes (salt)."""
        password = "test_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_create_access_token_returns_string(self):
        """Test create_access_token returns a string token."""
        data = {"user_id": "123", "username": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_is_jwt(self):
        """Test created token is JWT format (has 3 parts separated by dots)."""
        data = {"user_id": "123"}
        token = create_access_token(data)

        parts = token.split(".")
        assert len(parts) == 3  # JWT has 3 parts: header.payload.signature

    def test_decode_access_token_valid(self):
        """Test decode_access_token works with valid token."""
        data = {"user_id": "123", "username": "john"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert isinstance(decoded, dict)
        assert decoded["user_id"] == "123"
        assert decoded["username"] == "john"

    def test_decode_access_token_invalid_token(self):
        """Test decode_access_token returns None for invalid token."""
        invalid_token = "invalid.token.here"

        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_decode_access_token_malformed(self):
        """Test decode_access_token handles malformed token."""
        malformed = "not_a_jwt_token"

        decoded = decode_access_token(malformed)

        assert decoded is None

    def test_decode_access_token_empty_string(self):
        """Test decode_access_token handles empty string."""
        decoded = decode_access_token("")

        assert decoded is None

    def test_roundtrip_token_with_data(self):
        """Test complete roundtrip: create and decode token."""
        original_data = {
            "user_id": "user_456",
            "username": "alice",
            "email": "alice@example.com"
        }

        token = create_access_token(original_data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["user_id"] == original_data["user_id"]
        assert decoded["username"] == original_data["username"]
        assert decoded["email"] == original_data["email"]

    def test_create_access_token_with_custom_expiry(self):
        """Test create_access_token with custom expiration."""
        data = {"user_id": "123"}
        custom_expiry = timedelta(hours=2)

        token = create_access_token(data, expires_delta=custom_expiry)

        assert isinstance(token, str)
        # Token should be valid and decodable
        decoded = decode_access_token(token)
        assert decoded is not None

    def test_access_token_includes_expiration(self):
        """Test that access token includes expiration claim."""
        data = {"user_id": "123"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert "exp" in decoded  # Expiration claim should exist

    def test_password_hash_different_for_different_passwords(self):
        """Test different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")

        assert hash1 != hash2
        assert verify_password("password1", hash1) is True
        assert verify_password("password1", hash2) is False

    def test_verify_password_with_empty_strings(self):
        """Test verify_password handles empty strings."""
        hashed = hash_password("")

        result = verify_password("", hashed)

        assert result is True

    def test_verify_password_with_special_characters(self):
        """Test verify_password with special characters."""
        password = "P@ssw0rd!#$%"
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_token_with_empty_data(self):
        """Test creating token with empty data dict."""
        token = create_access_token({})

        decoded = decode_access_token(token)

        assert decoded is not None
        assert "exp" in decoded

    def test_token_with_special_characters_in_data(self):
        """Test token with special characters in claims."""
        data = {
            "username": "user@example.com",
            "description": "User with special chars: !@#$%"
        }

        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert "@" in decoded["username"]

    def test_token_with_unicode_data(self):
        """Test token with unicode characters."""
        data = {"username": "用户", "name": "José"}

        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["username"] == "用户"
        assert decoded["name"] == "José"

    def test_hash_password_long_input(self):
        """Test hash_password with very long input."""
        long_password = "p" * 1000

        hashed = hash_password(long_password)

        assert isinstance(hashed, str)
        assert verify_password(long_password, hashed) is True

    def test_verify_with_wrong_hash_format(self):
        """Test verify_password with non-bcrypt hash."""
        wrong_hash = "not_a_valid_bcrypt_hash"

        # Should handle gracefully, return False
        result = verify_password("password", wrong_hash)

        assert result is False

    def test_token_tampering_detection(self):
        """Test that tampered token is rejected."""
        data = {"user_id": "123"}
        token = create_access_token(data)

        # Tamper with token
        parts = token.split(".")
        tampered_token = parts[0] + ".tampered_payload." + parts[2]

        decoded = decode_access_token(tampered_token)

        assert decoded is None

    def test_create_token_consistency(self):
        """Test token creation for same data produces valid but different tokens."""
        data = {"user_id": "123"}

        token1 = create_access_token(data)
        token2 = create_access_token(data)

        # Tokens may be different due to timestamp
        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)

        assert decoded1 is not None
        assert decoded2 is not None
        assert decoded1["user_id"] == decoded2["user_id"]

    def test_password_with_whitespace(self):
        """Test password with leading/trailing whitespace."""
        password = "  password with spaces  "
        hashed = hash_password(password)

        # Exact match including whitespace
        result = verify_password(password, hashed)

        assert result is True

        # Without whitespace should fail
        result_wrong = verify_password("password with spaces", hashed)

        assert result_wrong is False
