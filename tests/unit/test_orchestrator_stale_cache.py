"""Regression tests for issue #43: stale session cache.

When a user requests a second review after updating their portfolio, the
orchestrator must re-run its tools instead of serving stale results cached
from the previous session.

These tests are EXPECTED TO FAIL until the caching bug is fixed. They act as
a regression guard: once the fix lands, they should pass.
"""

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class CountingTool(BaseTool):
    """A tool that records how many times it actually executed."""

    def __init__(self, name: str):
        self.name = name
        self.description = f"counting {name}"
        self.calls = 0
        self.last_input = None

    def execute(self, input_data: dict) -> ToolResult:
        self.calls += 1
        self.last_input = input_data
        return ToolResult(success=True, data={"ran_at_call": self.calls})


@pytest.mark.unit
class TestOrchestratorStaleCache:
    """Second review after a portfolio update must re-run tools (issue #43)."""

    @pytest.fixture
    def tools(self):
        return {
            "github_tool": CountingTool("github_tool"),
            "market_analyzer": CountingTool("market_analyzer"),
        }

    def test_second_review_reruns_tools_after_portfolio_update(self, tools):
        """A reused orchestrator must not serve stale results on the 2nd review.

        The github repo name is unchanged between reviews, but the underlying
        project content changed. The tools must still re-execute.
        """
        # One long-lived orchestrator, reused across requests (service singleton).
        orch = Orchestrator(tools=tools, session_store=None)
        profile_id = "user-123"

        profile_v1 = {
            "github_username": "alice",
            "projects": [{"github_repo": "portfolio", "description": "old bio"}],
        }
        orch.run(profile_id, profile_v1)

        # User updates portfolio content, then requests a second review.
        profile_v2 = {
            "github_username": "alice",
            "projects": [{"github_repo": "portfolio", "description": "new bio + new commits"}],
        }
        orch.run(profile_id, profile_v2)

        assert tools["github_tool"].calls == 2, (
            "github_tool served a stale cached result instead of re-running " "on the second review"
        )
        assert tools["market_analyzer"].calls == 2, (
            "market_analyzer served a stale cached result instead of re-running "
            "on the second review"
        )

    def test_stale_results_not_accumulated_in_session_state(self):
        """Dropping a tool from the plan must not keep its old result around.

        First review runs github_tool; the second review has no projects, so
        github_tool should not be in the plan. Its old result must not linger
        in the persisted session state (issue #43, accumulation variant).
        """
        github = CountingTool("github_tool")
        readme = CountingTool("readme_scorer")
        market = CountingTool("market_analyzer")
        tools = {
            "github_tool": github,
            "readme_scorer": readme,
            "market_analyzer": market,
        }

        # In-memory fake of the SessionStore interface (no Redis needed).
        class FakeSessionStore:
            def __init__(self):
                self.store = {}

            def get(self, session_id):
                return self.store.get(session_id)

            def set(self, session_id, data, ttl_seconds=3600):
                self.store[session_id] = data

            def delete(self, session_id):
                self.store.pop(session_id, None)

        session_store = FakeSessionStore()
        profile_id = "user-123"

        orch1 = Orchestrator(tools=tools, session_store=session_store)
        orch1.run(
            profile_id,
            {
                "github_username": "alice",
                "projects": [{"github_repo": "portfolio"}],
            },
        )

        # Fresh orchestrator (fresh in-memory cache), same persisted session.
        orch2 = Orchestrator(tools=tools, session_store=session_store)
        orch2.run(
            profile_id,
            {"readme_content": "# My Project"},  # no projects -> no github_tool
        )

        persisted = session_store.get(profile_id)
        assert "github_tool" not in persisted, (
            "stale github_tool result from the first review accumulated in the "
            "persisted session state even though the second review dropped it "
            f"from the plan (persisted keys: {sorted(persisted)})"
        )
