"""Tests for orchestrator.py"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator


class FakeRedis:
    """Fake Redis client for unit testing."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.ttls: dict[str, int] = {}

    def get(self, key: str) -> Any:
        return self.data.get(key)

    def setex(self, key: str, ttl: int, value: Any) -> None:
        self.data[key] = value
        self.ttls[key] = ttl

    def delete(self, key: str) -> None:
        self.data.pop(key, None)
        self.ttls.pop(key, None)


@pytest.mark.unit
class TestOrchestrator:
    """Test suite for Orchestrator."""

    @pytest.fixture
    def session_store(self) -> SessionStore:
        """Create a SessionStore backed by FakeRedis."""
        fake_redis = FakeRedis()
        return SessionStore(fake_redis)  # type: ignore[arg-type]

    @pytest.fixture
    def orchestrator(self, session_store: SessionStore) -> Orchestrator:
        """Create an Orchestrator with mock tools and session store."""
        mock_github_tool = MagicMock()
        mock_github_tool.execute.return_value = MagicMock(data={"repo": "repo-A", "stars": 10})

        mock_skill_tool = MagicMock()
        mock_skill_tool.execute.return_value = MagicMock(data={"skills": ["Python"]})

        mock_market_tool = MagicMock()
        mock_market_tool.execute.return_value = MagicMock(data={"market_demand": "High"})

        tools = {
            "github_tool": mock_github_tool,
            "skill_extractor": mock_skill_tool,
            "market_analyzer": mock_market_tool,
        }
        return Orchestrator(tools=tools, session_store=session_store)

    def test_session_state_not_cleared_between_reviews(
        self, orchestrator: Orchestrator, session_store: SessionStore
    ) -> None:
        """Test agent session state is not cleared between reviews (reproduces #43)."""
        profile_id = "user_profile_123"

        # First review: profile contains a GitHub repo
        profile_data_1 = {
            "github_username": "alice",
            "projects": [{"github_repo": "repo-A"}],
        }
        result_1 = orchestrator.run(profile_id, profile_data_1)
        assert "github_tool" in result_1["tool_results"]

        # Verify state was saved to session store
        stored_state_after_run1 = session_store.get(profile_id)
        assert stored_state_after_run1 is not None
        assert "github_tool" in stored_state_after_run1

        # Second review: same user profile_id submits a new review with only resume text
        profile_data_2 = {"resume_text": "Software Engineer with 5 years experience"}
        result_2 = orchestrator.run(profile_id, profile_data_2)
        assert "skill_extractor" in result_2["tool_results"]

        # Session state after second run
        stored_state_after_run2 = session_store.get(profile_id)
        assert stored_state_after_run2 is not None

        # Bug assertion: Each review should start with clean session state
        assert "github_tool" not in stored_state_after_run2, (
            "REPRODUCED BUG #43 / C-03: Stale 'github_tool' result from previous review "
            "was retained in session state for profile_id."
        )

    def test_persisted_state_matches_current_run_results_only(
        self, orchestrator: Orchestrator, session_store: SessionStore
    ) -> None:
        """Persisted session state should mirror only the current run's tool_results."""
        profile_id = "user_profile_456"

        profile_data = {"resume_text": "Backend engineer"}
        result = orchestrator.run(profile_id, profile_data)

        stored_state = session_store.get(profile_id)
        assert stored_state == result["tool_results"]

    def test_ttl_preserved_on_persist(
        self, orchestrator: Orchestrator, session_store: SessionStore
    ) -> None:
        """Session state should still be persisted with the default TTL."""
        profile_id = "user_profile_789"

        orchestrator.run(profile_id, {"resume_text": "Data engineer"})

        assert session_store.redis.ttls[f"session:{profile_id}"] == 3600  # type: ignore[attr-defined]

    def test_run_without_session_store_does_not_raise(self) -> None:
        """Orchestrator should work when session_store is not configured (backward compat)."""
        mock_skill_tool = MagicMock()
        mock_skill_tool.execute.return_value = MagicMock(data={"skills": ["Python"]})

        orchestrator = Orchestrator(tools={"skill_extractor": mock_skill_tool}, session_store=None)

        result = orchestrator.run("user_profile_no_store", {"resume_text": "Full stack engineer"})

        assert result["tool_results"]["skill_extractor"] == {"skills": ["Python"]}

    def test_failed_tool_does_not_corrupt_next_clean_run(
        self, orchestrator: Orchestrator, session_store: SessionStore
    ) -> None:
        """A tool failure in one run should not leak an error result into a later clean run."""
        profile_id = "user_profile_failure"

        orchestrator.tools["github_tool"].execute.side_effect = RuntimeError("GitHub API down")
        profile_data_1 = {
            "github_username": "bob",
            "projects": [{"github_repo": "repo-B"}],
        }
        result_1 = orchestrator.run(profile_id, profile_data_1)
        assert result_1["tool_results"]["github_tool"]["success"] is False

        # Second, unrelated review for the same profile should start clean
        orchestrator.tools["github_tool"].execute.side_effect = None
        orchestrator.tools["github_tool"].execute.return_value = MagicMock(
            data={"repo": "repo-A", "stars": 10}
        )
        result_2 = orchestrator.run(profile_id, {"resume_text": "QA engineer"})

        assert "github_tool" not in result_2["tool_results"]
        stored_state = session_store.get(profile_id) or {}
        assert "github_tool" not in stored_state

    def test_build_plan_skips_unconfigured_market_analyzer(self) -> None:
        """_build_plan should not schedule market_analyzer if it is not in self.tools."""
        mock_skill_tool = MagicMock()
        mock_skill_tool.execute.return_value = MagicMock(data={"skills": ["Python"]})

        orchestrator = Orchestrator(tools={"skill_extractor": mock_skill_tool})
        plan = orchestrator._build_plan({"resume_text": "Python developer"})

        tool_names = [tool_name for tool_name, _ in plan]
        assert "market_analyzer" not in tool_names
        assert tool_names == ["skill_extractor"]
