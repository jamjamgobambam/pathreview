"""Tests for portfolio_url validation in profile schemas."""

import pytest
from pydantic import ValidationError

from api.schemas.profile import ProfileCreate, ProfileUpdate


@pytest.mark.unit
class TestPortfolioUrlValidation:
    """Test suite for portfolio_url validation on profile schemas."""

    @pytest.mark.parametrize("model", [ProfileCreate, ProfileUpdate])
    def test_accepts_valid_https_url(self, model: type) -> None:
        """Test that a valid https URL is accepted."""
        profile = model(portfolio_url="https://jane.dev")
        assert profile.portfolio_url == "https://jane.dev"

    @pytest.mark.parametrize("model", [ProfileCreate, ProfileUpdate])
    def test_accepts_valid_http_url(self, model: type) -> None:
        """Test that a valid http URL is accepted."""
        profile = model(portfolio_url="http://jane.dev")
        assert profile.portfolio_url == "http://jane.dev"

    @pytest.mark.parametrize("model", [ProfileCreate, ProfileUpdate])
    def test_accepts_none(self, model: type) -> None:
        """Test that omitting the portfolio URL is allowed."""
        profile = model()
        assert profile.portfolio_url is None

    @pytest.mark.parametrize("model", [ProfileCreate, ProfileUpdate])
    def test_rejects_url_without_scheme(self, model: type) -> None:
        """Test that a URL missing http(s):// is rejected."""
        with pytest.raises(ValidationError):
            model(portfolio_url="jane.dev")

    @pytest.mark.parametrize("model", [ProfileCreate, ProfileUpdate])
    def test_rejects_non_http_scheme(self, model: type) -> None:
        """Test that a non-http(s) scheme is rejected."""
        with pytest.raises(ValidationError):
            model(portfolio_url="ftp://jane.dev")
