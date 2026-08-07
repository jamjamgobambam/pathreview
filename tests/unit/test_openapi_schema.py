"""Regression tests for the generated OpenAPI schema (what Swagger UI renders)."""

import pytest

from api.main import app


@pytest.mark.unit
class TestOpenAPISchema:
    """Test suite ensuring documented endpoints keep exposing their fields."""

    def _get_request_body_properties(
        self, schema: dict, path: str, method: str
    ) -> dict:
        operation = schema["paths"][path][method]
        media = operation["requestBody"]["content"]["multipart/form-data"]
        ref = media["schema"]["$ref"].split("/")[-1]
        return schema["components"]["schemas"][ref]["properties"]

    def test_create_profile_request_body_exposes_documented_fields(self) -> None:
        """POST /profiles schema should still expose the fields documented in docs/API.md."""
        schema = app.openapi()

        properties = self._get_request_body_properties(schema, "/profiles", "post")

        assert set(properties.keys()) == {
            "github_username",
            "portfolio_url",
            "resume_file",
        }
