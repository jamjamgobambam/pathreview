"""Tests for the review ingestion path."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.review_service import _run_ingestion_pipeline


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_ingestion_pipeline_uses_existing_ingested_source_fields() -> None:
    """Ingestion should build IngestedSource rows with existing model fields only."""
    mock_db_session = AsyncMock()
    mock_db_session.add = Mock()
    mock_db_session.commit = AsyncMock()

    profile = SimpleNamespace(
        id=uuid4(),
        github_username="octocat",
        portfolio_url="https://example.com",
        resume_text="Resume text",
        resume_filename="resume.md",
    )

    with patch("core.services.review_service.IngestedSource") as mock_ingested_source:
        mock_ingested_source.return_value = Mock()

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

    assert len(sources) == 3
    assert mock_ingested_source.call_count == 3
    for call in mock_ingested_source.call_args_list:
        assert "raw_data" not in call.kwargs
        assert call.kwargs["source_type"] in {"github", "portfolio", "resume"}
        assert call.kwargs["chunk_count"] == 0
