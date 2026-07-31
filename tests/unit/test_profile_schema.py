"""Tests for api/schemas/profile.py"""

import pytest
from pydantic import ValidationError

from api.schemas.profile import ProfileCreate, ProfileUpdate


@pytest.mark.unit
class TestProfilePortfolioUrlValidation:
    """Test suite for portfolio_url validation on ProfileCreate/ProfileUpdate."""

    @pytest.mark.parametrize("schema_cls", [ProfileCreate, ProfileUpdate])
    def test_accepts_valid_http_url(self, schema_cls):
        """Test that a well-formed http:// URL is accepted."""
        profile = schema_cls(portfolio_url="http://example.com")
        assert profile.portfolio_url == "http://example.com"

    @pytest.mark.parametrize("schema_cls", [ProfileCreate, ProfileUpdate])
    def test_accepts_valid_https_url(self, schema_cls):
        """Test that a well-formed https:// URL is accepted."""
        profile = schema_cls(portfolio_url="https://example.com/portfolio")
        assert profile.portfolio_url == "https://example.com/portfolio"

    @pytest.mark.parametrize("schema_cls", [ProfileCreate, ProfileUpdate])
    def test_accepts_none(self, schema_cls):
        """Test that an absent portfolio_url is still allowed (optional field)."""
        profile = schema_cls(portfolio_url=None)
        assert profile.portfolio_url is None

    @pytest.mark.parametrize("schema_cls", [ProfileCreate, ProfileUpdate])
    def test_rejects_url_without_scheme(self, schema_cls):
        """Test that a malformed URL missing http(s):// is rejected."""
        with pytest.raises(ValidationError):
            schema_cls(portfolio_url="example.com")

    @pytest.mark.parametrize("schema_cls", [ProfileCreate, ProfileUpdate])
    def test_rejects_non_http_scheme(self, schema_cls):
        """Test that a non-http(s) scheme (e.g. javascript:) is rejected."""
        with pytest.raises(ValidationError):
            schema_cls(portfolio_url="javascript:alert(1)")
