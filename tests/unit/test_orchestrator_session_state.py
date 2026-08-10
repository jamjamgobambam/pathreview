"""Tests for issue #43: agent session state must be cleared between reviews.

See JOURNAL.md (Week 8) for the reproduction narrative and PLAN.md for the
fix design.
"""

import pytest

from agent.orchestrator import Orchestrator


class _FakeToolResult:
    def __init__(self, data):
        self.data = data


class _FakeGithubTool:
    """Simulates github_tool: same input (repo name), but the underlying
    GitHub data changes between calls, as it would after a user updates
    their portfolio and requests a fresh review."""

    name = "github_tool"

    def __init__(self):
        self.call_count = 0

    def execute(self, tool_input):
        self.call_count += 1
        return _FakeToolResult({"stars": 10 * self.call_count, "call_count": self.call_count})


class _FakeSessionStore:
    """In-memory stand-in for SessionStore, to verify delete/get/set calls
    without requiring a real Redis connection."""

    def __init__(self):
        self._data = {}
        self.deleted_ids = []

    def get(self, session_id):
        return self._data.get(session_id)

    def set(self, session_id, data, ttl_seconds=3600):
        self._data[session_id] = data

    def delete(self, session_id):
        self.deleted_ids.append(session_id)
        self._data.pop(session_id, None)


@pytest.mark.unit
class TestOrchestratorSessionState:
    """Verifies issue #43 is fixed: cached tool results and session state
    no longer leak across separate review requests for the same profile."""

    def _make_profile(self):
        return {
            "github_username": "octocat",
            "projects": [{"github_repo": "octocat/hello-world"}],
        }

    def test_second_review_executes_tool_fresh_instead_of_reusing_cache(self):
        github_tool = _FakeGithubTool()
        orchestrator = Orchestrator(tools={"github_tool": github_tool})
        profile_id = "user-123"
        profile_data = self._make_profile()

        # Review #1: initial portfolio review.
        orchestrator.run(profile_id, profile_data)
        assert github_tool.call_count == 1

        # Review #2: user requests another review of the same profile with
        # the same tool input. The tool must execute again to produce fresh
        # results, not reuse the cached result from review #1.
        result = orchestrator.run(profile_id, profile_data)

        assert github_tool.call_count == 2
        assert result["tool_results"]["github_tool"]["call_count"] == 2

    def test_run_clears_prior_session_state_for_the_same_profile(self):
        github_tool = _FakeGithubTool()
        session_store = _FakeSessionStore()
        orchestrator = Orchestrator(tools={"github_tool": github_tool}, session_store=session_store)
        profile_id = "user-123"
        profile_data = self._make_profile()

        orchestrator.run(profile_id, profile_data)
        orchestrator.run(profile_id, profile_data)

        # delete() must be called for this profile at the start of each run.
        assert session_store.deleted_ids == [profile_id, profile_id]

        # The persisted state should reflect only the latest run's results,
        # not a merge of both runs.
        stored = session_store.get(profile_id)
        assert stored["github_tool"] == {"stars": 20, "call_count": 2}
        assert "market_analyzer" not in stored or stored["market_analyzer"]["success"] is False

    def test_repeated_tool_call_within_a_single_run_is_still_memoized(self):
        """The fix must only stop caching *across* separate run() calls;
        in-request memoization within a single run() call is preserved."""
        github_tool = _FakeGithubTool()
        orchestrator = Orchestrator(tools={"github_tool": github_tool})

        # Directly exercise the memoized _execute_tool path twice with the
        # same input inside what would be a single run.
        tool_input = {
            "github_username": "octocat",
            "repo_name": "octocat/hello-world",
        }
        first = orchestrator._execute_tool("github_tool", tool_input)
        second = orchestrator._execute_tool("github_tool", tool_input)

        assert github_tool.call_count == 1
        assert first.data == second.data
