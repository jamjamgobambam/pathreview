"""Reproduction test for issue #89.

https://github.com/ascherj/pathreview/issues/89

The API reference (``docs/API.md``) lists ``POST /profiles`` and ``POST /reviews``
as one-line endpoint summaries but never documents their request bodies. A reader
cannot tell which fields are accepted, which are required, or what content type to
send without reading the FastAPI routes and Pydantic schemas.

These tests assert that ``docs/API.md`` documents the request-body fields that are
actually accepted by the routes. They FAILED on the documentation as it stood when
issue #89 was filed, which is the reproduction of the gap; the documentation fix
turns them green. They now stand as regression guards against the reference drifting
back out of sync with the routes.

Sources of truth for the expected field names:
- ``api/routes/profiles.py`` / ``api/schemas/profile.py`` -> github_username,
  portfolio_url, resume_file (multipart/form-data).
- ``api/routes/reviews.py`` / ``api/schemas/review.py`` -> profile_id
  (application/json).
"""

import re
from pathlib import Path

import pytest

API_DOC = Path(__file__).resolve().parents[2] / "docs" / "API.md"


def _sections(text: str) -> dict[str, str]:
    """Split the reference into a mapping of heading -> section body.

    Args:
        text: The full Markdown source of ``docs/API.md``.

    Returns:
        A dict keyed by ``##``/``###`` heading text, whose values are the body
        of each section. Used to scope assertions to a single endpoint group so
        that a term documented elsewhere in the file cannot satisfy them.
    """
    parts = re.split(r"^#{2,3} (.+)$", text, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


@pytest.mark.unit
class TestApiDocRequestSchemas:
    """Reproduce issue #89: missing request-body documentation."""

    @pytest.fixture
    def api_doc_text(self) -> str:
        return API_DOC.read_text(encoding="utf-8")

    @pytest.fixture
    def profiles_section(self, api_doc_text: str) -> str:
        """The body of the ``### Profiles`` section."""
        return _sections(api_doc_text)["Profiles"]

    @pytest.fixture
    def reviews_section(self, api_doc_text: str) -> str:
        """The body of the ``### Reviews`` section."""
        return _sections(api_doc_text)["Reviews"]

    def test_post_profiles_documents_request_fields(self, api_doc_text: str) -> None:
        """POST /profiles accepts multipart form fields that must be documented."""
        expected_fields = ["github_username", "portfolio_url", "resume_file"]
        missing = [f for f in expected_fields if f not in api_doc_text]
        assert not missing, (
            "docs/API.md does not document the POST /profiles request body "
            f"fields: {missing}. See api/routes/profiles.py (issue #89)."
        )

    def test_post_profiles_documents_content_type(self, api_doc_text: str) -> None:
        """POST /profiles is a multipart upload; the content type must be stated."""
        assert "multipart/form-data" in api_doc_text, (
            "docs/API.md does not state that POST /profiles uses "
            "multipart/form-data. See api/routes/profiles.py (issue #89)."
        )

    def test_post_reviews_documents_json_request_body(self, api_doc_text: str) -> None:
        """POST /reviews takes an application/json body with a required profile_id.

        ``profile_id`` already appears in docs as a *path* parameter for the
        profile endpoints, so its bare presence proves nothing. The gap is that
        the JSON request body and its content type are never documented, so this
        asserts the content type is stated.
        """
        assert "application/json" in api_doc_text, (
            "docs/API.md does not document the POST /reviews JSON request body "
            "(no application/json content type stated). See api/routes/reviews.py "
            "and api/schemas/review.py (issue #89)."
        )

    def test_post_profiles_documents_accepted_resume_types(self, profiles_section: str) -> None:
        """The route accepts exactly three resume MIME types; all must be listed.

        ``api/routes/profiles.py`` rejects anything outside this set with a 422,
        so omitting one from the reference would send readers down a failing path.
        """
        accepted = ["application/pdf", "text/markdown", "text/plain"]
        missing = [mime for mime in accepted if mime not in profiles_section]
        assert not missing, (
            "The Profiles section of docs/API.md does not document these accepted "
            f"resume types: {missing}. See the MIME allow-list in "
            "api/routes/profiles.py."
        )

    def test_post_profiles_documents_field_length_limits(self, profiles_section: str) -> None:
        """``ProfileCreate`` caps github_username at 255 and portfolio_url at 500."""
        for limit in ("255", "500"):
            assert limit in profiles_section, (
                f"The Profiles section of docs/API.md does not document the {limit} "
                "character limit declared in api/schemas/profile.py."
            )

    def test_post_reviews_documents_profile_id_in_its_own_section(
        self, reviews_section: str
    ) -> None:
        """``profile_id`` must be documented as the JSON body field for reviews.

        Scoped to the Reviews section because ``profile_id`` also appears as a
        path parameter under Profiles, where its presence proves nothing about
        the ``POST /reviews`` request body.
        """
        assert "profile_id" in reviews_section, (
            "The Reviews section of docs/API.md does not document the required "
            "profile_id body field. See ReviewCreate in api/schemas/review.py."
        )
        assert "application/json" in reviews_section, (
            "The Reviews section of docs/API.md does not state the "
            "application/json content type for POST /reviews."
        )

    def test_write_endpoints_document_bearer_authentication(self, api_doc_text: str) -> None:
        """Both write endpoints depend on ``get_current_user`` and need a token."""
        assert "Bearer" in api_doc_text, (
            "docs/API.md does not document the bearer token required by the "
            "profile and review endpoints. See get_current_user in "
            "api/middleware/auth.py."
        )

    def test_write_endpoints_include_example_requests(
        self, profiles_section: str, reviews_section: str
    ) -> None:
        """Issue #89 asks for example requests, not just field lists."""
        assert (
            "curl" in profiles_section
        ), "The Profiles section of docs/API.md has no example request (issue #89)."
        assert (
            "curl" in reviews_section
        ), "The Reviews section of docs/API.md has no example request (issue #89)."
