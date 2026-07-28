"""Reproduction + fix-target tests for issue C-03 (#43): agent session state.

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

The genuine staleness only appears when BOTH hold:
  1. a single Orchestrator instance is reused across reviews (its ContextManager
     persists), and
  2. a tool's input hash does not change with the portfolio -- exactly
     market_analyzer, whose input is the constant {"detected_skills": {}}
     placeholder at orchestrator.py:130.

Test map:
  * test_second_review_reflects_updated_portfolio -- the issue AS WRITTEN does
    NOT reproduce (fresh per-request orchestrator re-runs tools). GREEN.
  * test_reused_orchestrator_replays_stale_market_result -- reproduces the real
    bug on current code and documents it. GREEN (asserts the buggy behavior).
  * test_reused_orchestrator_reruns_with_real_skills_after_fix -- the fix target.
    Asserts market_analyzer re-runs AND is handed real detected skills. Marked
    xfail(strict) until the fix lands; it should XPASS once C-03 is fixed, which
    strict mode turns into a failure to prompt removing the marker.
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
        by the orchestrator (the constant {} placeholder today) plus the
        execution number.
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

    def test_reused_orchestrator_replays_stale_market_result(self, tools, session_store):
        """REPRODUCE C-03 on current code: reused orchestrator replays stale result.

        With ONE Orchestrator instance reused across both reviews, its
        ContextManager persists. tech_detector's input changes with the portfolio
        so it re-runs, but market_analyzer always receives the constant
        {"detected_skills": {}} placeholder (orchestrator.py:130) -- an identical
        memo key -- so review 2 replays review 1's cached result instead of
        re-executing.

        This test asserts the BUGGY behavior so it passes today and documents the
        defect. When C-03 is fixed it will start failing, which is the signal to
        delete it in favour of the fix-target test below.
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

        # BUG: market_analyzer did NOT re-run -- the review-1 result is replayed.
        assert len(tools["market_analyzer"].calls) == 1, (
            "current code: market_analyzer is memoized on a constant input and "
            "is not re-run for the second review"
        )
        assert result2["tool_results"]["market_analyzer"]["run"] == 1

        # ROOT: the only call market_analyzer ever got carried the empty
        # placeholder, never any portfolio-derived skills.
        assert tools["market_analyzer"].calls[0]["detected_skills"] == {}

    @pytest.mark.xfail(
        reason="C-03 not yet fixed: reused orchestrator replays stale market "
        "results and market_analyzer is never handed real detected skills",
        strict=True,
    )
    def test_reused_orchestrator_reruns_with_real_skills_after_fix(self, tools, session_store):
        """FIX TARGET: reused orchestrator must re-run tools with real skills.

        A second review on a reused orchestrator must reflect the new portfolio
        for every tool -- including market_analyzer -- and market_analyzer must
        be handed the skills actually detected from the portfolio rather than the
        empty {} placeholder. Fails today (xfail); should pass once C-03 is fixed
        by (a) scoping/keying the cache per run and (b) populating
        market_analyzer's input from detected skills (orchestrator.py:130).
        """
        profile_id = "user-789"
        orch = Orchestrator(tools, session_store=session_store)

        # Review 1.
        orch.run(profile_id, self._portfolio(["a.py"]))

        # Review 2 on the SAME orchestrator, updated portfolio.
        result2 = orch.run(profile_id, self._portfolio(["b.rs"]))

        # market_analyzer must re-execute for the second review.
        assert len(tools["market_analyzer"].calls) == 2
        assert result2["tool_results"]["market_analyzer"]["run"] == 2

        # market_analyzer must receive real, portfolio-derived detected skills.
        assert tools["market_analyzer"].calls[-1]["detected_skills"], (
            "market_analyzer should be handed non-empty detected skills, not the " "{} placeholder"
        )
