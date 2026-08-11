"""Guard docs/API.md against drifting from the actual POST request models."""

import inspect
from pathlib import Path

import pytest

from api.routes.profiles import create_profile_endpoint
from api.schemas.review import ReviewCreate

pytestmark = pytest.mark.unit

API_DOC = Path(__file__).parents[2] / "docs" / "API.md"


def test_api_doc_documents_all_profile_request_fields() -> None:
    """Every form field POST /profiles accepts must appear in docs/API.md."""
    doc = API_DOC.read_text(encoding="utf-8")
    params = inspect.signature(create_profile_endpoint).parameters

    for field in ("github_username", "portfolio_url", "resume_file"):
        assert field in params, f"{field} is no longer a handler parameter"
        assert field in doc, f"{field} is undocumented in docs/API.md"


def test_api_doc_documents_all_review_request_fields() -> None:
    """Every field ReviewCreate declares must appear in docs/API.md."""
    doc = API_DOC.read_text(encoding="utf-8")

    for field in ReviewCreate.model_fields:
        assert field in doc, f"{field} is undocumented in docs/API.md"
