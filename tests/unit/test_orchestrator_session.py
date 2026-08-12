"""Tests for agent session state clearing between reviews (issue #43).

Covers agent/orchestrator.py + agent/memory/session_store.py: after a
portfolio is updated, a re-review should not reuse stale tool results
from the previous run.
"""

from unittest.mock import Mock

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class FakeReadmeScorer(BaseTool):
    """Tool whose output changes based on input, so we can detect staleness."""

    name = "readme_scorer"
    description = "Fake readme scorer for tests"

    def execute(self, input_data: dict) -> ToolResult:
        return ToolResult(
            success=True,
            data={"readme_content": input_data["readme_content"]},
        )


class FakeSkillExtractor(BaseTool):
    """Tool that only runs when resume_text is present in the profile."""

    name = "skill_extractor"
    description = "Fake skill extractor for tests"

    def execute(self, input_data: dict) -> ToolResult:
        return ToolResult(
            success=True,
            data={"resume_text": input_data["resume_text"]},
        )


@pytest.mark.unit
class TestOrchestratorSessionClearing:
    """Test suite for session state handling across repeated reviews."""

    @pytest.fixture
    def mock_redis(self) -> Mock:
        """Create a mock Redis client backed by an in-memory dict."""
        store: dict[str, str] = {}
        redis = Mock()
        redis.get = Mock(side_effect=lambda key: store.get(key))
        redis.setex = Mock(side_effect=lambda key, ttl, value: store.__setitem__(key, value))
        redis.delete = Mock(side_effect=lambda key: store.pop(key, None))
        return redis

    @pytest.fixture
    def session_store(self, mock_redis: Mock) -> SessionStore:
        """Create a SessionStore backed by the mock Redis client."""
        return SessionStore(mock_redis)

    @pytest.fixture
    def orchestrator(self, session_store: SessionStore) -> Orchestrator:
        """Create an Orchestrator wired with fake tools and a real SessionStore."""
        tools = {
            "readme_scorer": FakeReadmeScorer(),
            "skill_extractor": FakeSkillExtractor(),
        }
        return Orchestrator(tools=tools, session_store=session_store)

    def test_second_review_reflects_updated_profile_data(self, orchestrator: Orchestrator) -> None:
        """After the profile changes, re-running should return the new data, not stale data."""
        profile_id = "profile-123"

        profile_v1 = {"readme_content": "original readme"}
        profile_v2 = {"readme_content": "updated readme"}

        result_v1 = orchestrator.run(profile_id, profile_v1)
        result_v2 = orchestrator.run(profile_id, profile_v2)

        assert result_v1["tool_results"]["readme_scorer"]["readme_content"] == "original readme"
        # This is expected to currently FAIL until issue #43 is fixed:
        # stale session state causes the second run's results to be
        # merged with / overridden by the first run's cached data.
        assert result_v2["tool_results"]["readme_scorer"]["readme_content"] == "updated readme"

    def test_removed_tool_output_does_not_linger_in_session(
        self, orchestrator: Orchestrator, session_store: SessionStore
    ) -> None:
        """If a user removes content (e.g. deletes their resume), the stale
        tool output for that removed input should not persist in the
        session forever.

        Reproduces issue #43: orchestrator.run() merges new results into
        session_state via `session_state.update(results)` but nothing ever
        clears stale keys or calls session_store.delete(), so a tool result
        computed against old profile data can outlive the data it came from.
        """
        profile_id = "profile-456"

        # First review: profile has both a readme and a resume.
        orchestrator.run(
            profile_id,
            {"readme_content": "v1 readme", "resume_text": "v1 resume"},
        )

        # User deletes their resume and re-requests a review.
        orchestrator.run(profile_id, {"readme_content": "v2 readme"})

        session_state = session_store.get(profile_id)

        assert session_state is not None
        # skill_extractor's output from the first run must not survive: the
        # resume that produced it no longer exists.
        assert "skill_extractor" not in session_state
        # ...while the tool that did run is present, with current data.
        assert session_state["readme_scorer"]["readme_content"] == "v2 readme"

    def test_session_reflects_only_current_run_results(
        self, orchestrator: Orchestrator, session_store: SessionStore
    ) -> None:
        """The persisted session is a replacement, not an accumulation."""
        profile_id = "profile-789"

        orchestrator.run(profile_id, {"resume_text": "only a resume"})
        assert set(session_store.get(profile_id) or {}) == {"skill_extractor", "market_analyzer"}

        orchestrator.run(profile_id, {"readme_content": "only a readme"})
        assert set(session_store.get(profile_id) or {}) == {"readme_scorer", "market_analyzer"}

    def test_profile_with_no_tool_triggering_data_clears_session(
        self, orchestrator: Orchestrator, session_store: SessionStore
    ) -> None:
        """Removing all reviewable content leaves no stale session behind."""
        profile_id = "profile-empty"

        orchestrator.run(profile_id, {"readme_content": "v1 readme"})
        assert session_store.get(profile_id) is not None

        # Every tool-triggering field is now gone, so the plan is empty.
        orchestrator.run(profile_id, {})

        assert session_store.get(profile_id) is None

    def test_first_review_with_no_prior_session_succeeds(
        self, orchestrator: Orchestrator, session_store: SessionStore
    ) -> None:
        """A profile Redis has never seen (or whose TTL expired) is not an error."""
        profile_id = "profile-brand-new"

        result = orchestrator.run(profile_id, {"readme_content": "first ever readme"})

        assert result["tool_results"]["readme_scorer"]["readme_content"] == "first ever readme"
        assert (session_store.get(profile_id) or {})["readme_scorer"][
            "readme_content"
        ] == "first ever readme"

    def test_failed_tool_result_replaces_previous_success(
        self, session_store: SessionStore
    ) -> None:
        """An erroring tool must not leave the prior run's success in the session.

        Otherwise a later review would appear to have working data for a
        tool that in fact failed.
        """
        profile_id = "profile-failing"

        class ExplodingReadmeScorer(BaseTool):
            name = "readme_scorer"
            description = "Readme scorer that fails on demand"

            def __init__(self) -> None:
                self.should_fail = False

            def execute(self, input_data: dict) -> ToolResult:
                if self.should_fail:
                    raise RuntimeError("scoring backend unavailable")
                return ToolResult(success=True, data={"score": 90})

        scorer = ExplodingReadmeScorer()
        orchestrator = Orchestrator(tools={"readme_scorer": scorer}, session_store=session_store)

        orchestrator.run(profile_id, {"readme_content": "good readme"})
        assert (session_store.get(profile_id) or {})["readme_scorer"] == {"score": 90}

        # Same profile re-reviewed, but the tool now fails. Note the readme
        # text differs so the in-run memoization cache does not mask this.
        scorer.should_fail = True
        orchestrator.run(profile_id, {"readme_content": "different readme"})

        persisted = (session_store.get(profile_id) or {})["readme_scorer"]
        assert persisted["success"] is False
        assert "score" not in persisted
