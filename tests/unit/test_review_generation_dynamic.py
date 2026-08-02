"""Tests that review generation changes with uploaded document content."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from core.services.review_service import (
    _run_agent_orchestration,
    _run_rag_retrieval_generation,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_agent_orchestration_changes_when_resume_text_changes() -> None:
    """Different uploaded resumes should produce different agent analysis."""
    profile = SimpleNamespace(
        id=uuid4(),
        github_username="octocat",
        portfolio_url="https://example.com",
        resume_text="",
        resume_filename="resume.md",
    )

    python_resume = "Python FastAPI PostgreSQL Docker"
    frontend_resume = "React TypeScript Next.js Tailwind"

    python_ingestion = [
        {
            "source_type": "resume",
            "filename": "resume.md",
            "data": python_resume,
        },
    ]
    frontend_ingestion = [
        {
            "source_type": "resume",
            "filename": "resume.md",
            "data": frontend_resume,
        },
    ]

    python_output = await _run_agent_orchestration(profile, python_ingestion)
    frontend_output = await _run_agent_orchestration(profile, frontend_ingestion)

    assert python_output != frontend_output
    assert python_output["overall_score"] != frontend_output["overall_score"]
    assert python_output["sections"][0]["content"] != frontend_output["sections"][0]["content"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rag_generation_changes_with_uploaded_resume_text() -> None:
    """RAG output should reflect the latest upload instead of repeating stale text."""
    profile = SimpleNamespace(
        id=uuid4(),
        github_username="octocat",
        portfolio_url="https://example.com",
        resume_text="",
        resume_filename="resume.md",
    )

    python_resume = "Python FastAPI PostgreSQL Docker"
    frontend_resume = "React TypeScript Next.js Tailwind"

    python_ingestion = [
        {
            "source_type": "resume",
            "filename": "resume.md",
            "data": python_resume,
        },
    ]
    frontend_ingestion = [
        {
            "source_type": "resume",
            "filename": "resume.md",
            "data": frontend_resume,
        },
    ]

    python_agent_output = await _run_agent_orchestration(profile, python_ingestion)
    frontend_agent_output = await _run_agent_orchestration(profile, frontend_ingestion)

    python_rag = await _run_rag_retrieval_generation(profile, python_ingestion, python_agent_output)
    frontend_rag = await _run_rag_retrieval_generation(
        profile, frontend_ingestion, frontend_agent_output
    )

    assert python_rag != frontend_rag
    assert python_rag["sections"][0]["content"] != frontend_rag["sections"][0]["content"]
