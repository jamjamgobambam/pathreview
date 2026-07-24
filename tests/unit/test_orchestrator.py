"""Reproduction tests for issue C-03 (#43): agent session state between reviews.

The issue claims:
    "session_store.py caches agent state by user ID. When a user requests a
    second review after updating their portfolio, the orchestrator uses stale
    tool results from the previous session instead of re-running the tools."

Tracing the code shows the mechanism is misattributed:
  * Orchestrator.run() always re-runs every tool in the plan; it never consults
    session_store to decide whether to skip a tool. The only cache checked is
    the in-memory ContextManager (per-instance, keyed by hash of tool input).
  * session_store state is loaded, merged via session_state.update(results),
    and re-saved -- but run() returns the freshly computed `results`, so stale
    session data is never served.

These two tests make that concrete:
  * test_second_review_reflects_updated_portfolio -- the issue AS WRITTEN does
    NOT reproduce. Even with stale data sitting in the session store, a second
    review returns fresh results because the tools re-run.
  * test_market_analyzer_serves_stale_result_on_reused_orchestrator -- the REAL
    staleness. It only appears when a single Orchestrator instance (hence its
    ContextManager) is reused AND the tool's input hash does not change with the
    portfolio -- which is exactly market_analyzer, whose input is the constant
    {"detected_skills": {}} placeholder at orchestrator.py:130.
"""

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class RecordingTool(BaseTool):
    """Fake tool that records every call so tests can assert re-runs.

    `output_builder(input_data, call_number)` builds the result data, letting a
    test tell "this is the Nth execution" apart from a cached replay.
    """

    def __init__(self, name: str, output_builder):
        self.name = name
        self.description = f"fake {name}"
        self.calls: list[dict] = []
        self._output_builder = output_builder

    def execute(self, input_data: dict) -> ToolResult:
        self.calls.append(input_data)
        return ToolResult(
            success=True,
            data=self._output_builder(input_data, len(self.calls)),
        )


class FakeSessionStore:
    """In-memory stand-in for the Redis-backed SessionStore.

    Mirrors the get/set/delete surface Orchestrator uses so we can observe what
    ends up persisted per profile_id.
    """

    def __init__(self):
        self.store: dict[str, dict] = {}

    def get(self, session_id: str):
        return self.store.get(session_id)

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        self.store[session_id] = dict(data)

    def delete(self, session_id: str) -> None:
        self.store.pop(session_id, None)


@pytest.mark.unit
class TestOrchestratorSessionReset:
    """Reproduction suite for C-03."""

    @pytest.fixture
    def tools(self):
        """Fake tech_detector + market_analyzer that record their calls.

        tech_detector echoes the files it saw (input changes with the portfolio,
        so its memo key changes). market_analyzer echoes the input it was handed
        by the orchestrator (constant {} placeholder, so its memo key never
        changes) plus the execution number.
        """
        tech = RecordingTool(
            "tech_detector",
            lambda inp, n: {"files_seen": inp["files"], "run": n},
        )
        market = RecordingTool(
            "market_analyzer",
            lambda inp, n: {"input_skills": inp.get("detected_skills"), "run": n},
        )
        return {"tech_detector": tech, "market_analyzer": market}

    @pytest.fixture
    def session_store(self):
        return FakeSessionStore()

    def _portfolio(self, files):
        return {"files": list(files)}

    def test_second_review_reflects_updated_portfolio(self, tools, session_store):
        """Issue AS WRITTEN does not reproduce: a fresh review re-runs the tools.

        Two reviews for the same profile_id, each with its own Orchestrator
        instance (the realistic per-request case, since nothing wires the
        orchestrator as a singleton). The portfolio changes between them. Even
        though the session store still holds review 1's state, review 2 returns
        fresh results -- so the "uses stale tool results instead of re-running"
        mechanism does not hold here.
        """
        profile_id = "user-123"

        # Review 1 with portfolio v1.
        orch1 = Orchestrator(tools, session_store=session_store)
        result1 = orch1.run(profile_id, self._portfolio(["a.py", "b.py"]))
        assert result1["tool_results"]["tech_detector"]["files_seen"] == ["a.py", "b.py"]

        # Stale review-1 state is now sitting in the session store...
        assert session_store.get(profile_id)["tech_detector"]["files_seen"] == ["a.py", "b.py"]

        # Review 2 with an UPDATED portfolio (same user, new Orchestrator).
        orch2 = Orchestrator(tools, session_store=session_store)
        result2 = orch2.run(profile_id, self._portfolio(["c.rs", "d.rs"]))

        # ...yet the result reflects the NEW portfolio, and the tool re-ran.
        assert result2["tool_results"]["tech_detector"]["files_seen"] == ["c.rs", "d.rs"]
        assert tools["tech_detector"].calls[-1] == {"files": ["c.rs", "d.rs"]}
        assert len(tools["tech_detector"].calls) == 2, "tech_detector should re-run each review"

    def test_market_analyzer_serves_stale_result_on_reused_orchestrator(self, tools, session_store):
        """A reused orchestrator should not replay its previous profile run.

        With ONE Orchestrator instance reused across both reviews, the
        ContextManager must be scoped to the individual run rather than the
        lifetime of the orchestrator object. tech_detector's input changes with
        the portfolio, so it re-runs naturally. market_analyzer should also
        re-execute for the second review, even though its input placeholder is
        the same, because that memoization must not bleed across profile runs.
        """
        profile_id = "user-456"
        orch = Orchestrator(tools, session_store=session_store)

        # Review 1.
        result1 = orch.run(profile_id, self._portfolio(["a.py"]))
        assert result1["tool_results"]["market_analyzer"]["run"] == 1
        assert result1["tool_results"]["tech_detector"]["run"] == 1

        # Review 2 on the SAME orchestrator, updated portfolio.
        result2 = orch.run(profile_id, self._portfolio(["b.rs"]))

        # tech_detector re-ran (input hash changed): fresh.
        assert result2["tool_results"]["tech_detector"]["files_seen"] == ["b.rs"]
        assert len(tools["tech_detector"].calls) == 2

        # market_analyzer must also re-run for the second review rather than
        # serving the stale review-1 result from the reused orchestrator.
        assert len(tools["market_analyzer"].calls) == 2
        assert result2["tool_results"]["market_analyzer"]["run"] == 2
