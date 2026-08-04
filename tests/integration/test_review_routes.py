"""Integration tests for the POST /reviews route.

Covers the route-level guard clause in api/routes/reviews.py that rejects
review creation for a profile with no ingested documents, verifying both
the 400 response and the accompanying warning log.
"""

from uuid import uuid4

import pytest
from unittest.mock import Mock


@pytest.mark.integration
class TestReviewRoutes:
    """Test suite for the /reviews route."""

    @pytest.fixture
    def profile_with_no_documents(self, mock_db_session):
        """Configure the mock DB session to simulate a profile with no ingested documents."""
        profile_id = uuid4()
        mock_db_session.execute.return_value.scalars.return_value.first.return_value = None
        return profile_id

    def test_post_reviews_no_documents(self, client, profile_with_no_documents, caplog):
        """POST /reviews with no ingested documents returns 400 and logs a warning."""
        caplog.at_level("WARNING")

        response = client.post(
            "/reviews", json={"profile_id": str(profile_with_no_documents)}
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Profile has no ingested documents"
        assert "review_creation_no_ingested_documents" in caplog.text
