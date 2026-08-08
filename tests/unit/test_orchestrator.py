"""Tests for orchestrator.py."""

from unittest.mock import MagicMock, patch

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.readme_scorer import ReadmeScorer
from agent.tools.tech_detector import TechDetector


@pytest.mark.unit
class TestOrchestrator:
    """Test suite for Orchestrator agent."""

    def test_second_review_does_not_retain_previous_tool_results(self) -> None:
        """Test that a new review does not retain obsolete tool results."""

        # Simulate Redis storage shared across separate review sessions.
        stored_sessions = {}

        redis_client = MagicMock()

        # Store serialized session data using the same key behavior as Redis.
        def setex(key: str, ttl_seconds: int, value: str) -> None:
            stored_sessions[key] = value

        # Return previously stored session data for the requested Redis key.
        def get(key: str) -> str | None:
            return stored_sessions.get(key)

        redis_client.setex.side_effect = setex
        redis_client.get.side_effect = get

        session_store = SessionStore(redis_client)

        # Use real tools so each review produces a genuine tool result.
        tools = {
            "readme_scorer": ReadmeScorer(),
            "tech_detector": TechDetector(),
        }

        # Run the first review and persist its README scoring result.
        first_orchestrator = Orchestrator(
            tools=tools,
            session_store=session_store,
        )

        with patch.object(
            first_orchestrator,
            "_build_plan",
            return_value=[
                (
                    "readme_scorer",
                    {"readme_content": "# Portfolio\nOriginal README."},
                ),
            ],
        ):
            first_orchestrator.run(
                "profile-123",
                {"readme_content": "# Portfolio\nOriginal README."},
            )

        first_session = session_store.get("profile-123")

        # Confirm the first review stored only its own tool result.
        assert first_session is not None
        assert set(first_session) == {"readme_scorer"}

        # Simulate a later review for the same profile using a new orchestrator.
        second_orchestrator = Orchestrator(
            tools=tools,
            session_store=session_store,
        )

        with patch.object(
            second_orchestrator,
            "_build_plan",
            return_value=[
                (
                    "tech_detector",
                    {
                        "files": [
                            "src/main.py",
                            "requirements.txt",
                            "Dockerfile",
                        ],
                    },
                ),
            ],
        ):
            second_orchestrator.run(
                "profile-123",
                {
                    "files": [
                        "src/main.py",
                        "requirements.txt",
                        "Dockerfile",
                    ],
                },
            )

        second_session = session_store.get("profile-123")

        # The new review must replace, not merge with, the previous review state.
        assert second_session is not None
        assert set(second_session) == {"tech_detector"}
