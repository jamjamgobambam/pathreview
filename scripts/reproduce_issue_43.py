"""Verification script for Issue #43: Agent session state not cleared between reviews.

Originally written to REPRODUCE the bug; now asserts the FIX holds. It drives
Orchestrator.run() twice for the same profile_id (README-only, then resume-only)
and checks that neither stale-state layer leaks run 1 into run 2:

  Layer 1 - SessionStore (Redis): run() must persist only the current review's
      results, with no merge of prior state keyed by `profile_id`.

  Layer 2 - ContextManager (in-memory): reset per review, so (a) `cached_results`
      do not accumulate across reviews, and (b) `market_analyzer` - always called
      with the constant input {"detected_skills": {}} - recomputes each review
      instead of serving a stale memoized result.

Exit code 0 = fix verified (all layers clean); non-zero = a layer regressed.
"""

import importlib.util
import os
import sys
from unittest.mock import MagicMock

# Add root project directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Gracefully handle missing dependencies if running outside project venv
if importlib.util.find_spec("structlog") is None:
    sys.modules["structlog"] = MagicMock()

if importlib.util.find_spec("redis") is None:
    sys.modules["redis"] = MagicMock()

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator


class FakeRedis:
    """In-memory dictionary mock for redis.Redis."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, time: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class DummyTool:
    """Dummy tool that returns constant data for orchestrator execution."""

    def __init__(self, name: str, mock_data: dict) -> None:
        self.name = name
        self.mock_data = mock_data

    def execute(self, tool_input: dict) -> dict:
        return self.mock_data


class CountingTool:
    """Spy tool that records how many times it actually executed.

    Used to detect ContextManager cache hits: if execute() is not called on a
    subsequent run, the orchestrator served a stale memoized result instead of
    recomputing. Returns the current call number so the stale value is visible.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def execute(self, tool_input: dict) -> dict:
        self.calls += 1
        return {
            "call_number": self.calls,
            "detected_skills_seen": tool_input.get("detected_skills"),
        }


def _has_tool_result(cached_results: dict, tool_name: str) -> bool:
    """Return True if cached_results holds a result for tool_name.

    ContextManager keys are formatted as '<tool_name>:<input_hash>'.
    """
    return any(key.startswith(f"{tool_name}:") for key in cached_results)


def main() -> int:
    print("=" * 60)
    print("VERIFYING FIX FOR ISSUE #43: Session state cleared across reviews")
    print("=" * 60)

    # 1. Setup mock storage and orchestrator
    fake_redis = FakeRedis()
    session_store = SessionStore(fake_redis)  # type: ignore[arg-type]  # in-memory test double

    # market_analyzer is a spy so we can detect a stale ContextManager cache hit.
    market_analyzer = CountingTool("market_analyzer")
    tools = {
        "readme_scorer": DummyTool("readme_scorer", {"score": 95, "feedback": "Great README"}),
        "skill_extractor": DummyTool("skill_extractor", {"skills": ["Python", "FastAPI"]}),
        "market_analyzer": market_analyzer,
    }

    orchestrator = Orchestrator(tools=tools, session_store=session_store)
    profile_id = "user_profile_43"

    # 2. Run 1: User submits profile with README only
    print("\n--- RUN 1: Review request with README content ---")
    profile_data_run1 = {"readme_content": "# My Portfolio Project\nA cool open-source project."}
    result_1 = orchestrator.run(profile_id, profile_data_run1)

    print("Run 1 Tool Results:", result_1["tool_results"])
    session_state_after_run1 = session_store.get(profile_id)
    print("SessionStore state after Run 1:", session_state_after_run1)
    print("market_analyzer executions after Run 1:", market_analyzer.calls)
    assert session_state_after_run1 is not None, "Run 1 should persist session state"
    assert "readme_scorer" in session_state_after_run1, "Run 1 should store readme_scorer result"
    assert market_analyzer.calls == 1, "Run 1 should execute market_analyzer once"

    # 3. Run 2: SAME user submits a subsequent review with RESUME only (no README content)
    print("\n--- RUN 2: Subsequent review request with RESUME content only (No README) ---")
    profile_data_run2 = {
        "resume_text": "Jane Doe - Senior Software Engineer with 5 years experience."
    }
    result_2 = orchestrator.run(profile_id, profile_data_run2)

    print("Run 2 Tool Results (from execution plan):", result_2["tool_results"])
    session_state_after_run2 = session_store.get(profile_id)
    print("SessionStore state after Run 2:", session_state_after_run2)
    print("Run 2 cached_results keys:", list(result_2["cached_results"].keys()))
    print("market_analyzer executions after Run 2:", market_analyzer.calls)
    assert session_state_after_run2 is not None, "Run 2 should persist session state"

    # 4. Check for bug conditions across BOTH caching layers
    print("\n" + "=" * 60)
    print("ANALYSIS OF STALE STATE (two layers):")
    print("=" * 60)

    # Layer 1 - SessionStore (Redis) merge leak
    layer1_sessionstore = "readme_scorer" in session_state_after_run2

    # Layer 2a - ContextManager cached_results accumulation across reviews
    layer2_accumulation = _has_tool_result(result_2["cached_results"], "readme_scorer")

    # Layer 2b - ContextManager stale cache hit: market_analyzer never re-executed on Run 2
    layer2_market_stale = market_analyzer.calls == 1

    def flag(hit: bool) -> str:
        return "[X] STALE" if hit else "[ ] clean"

    print(
        f"{flag(layer1_sessionstore)}  Layer 1 (SessionStore): "
        f"'readme_scorer' from Run 1 still in persisted state for '{profile_id}'"
    )
    print(
        f"{flag(layer2_accumulation)}  Layer 2a (ContextManager): "
        f"'readme_scorer' from Run 1 still in Run 2 cached_results"
    )
    print(
        f"{flag(layer2_market_stale)}  Layer 2b (ContextManager): "
        f"'market_analyzer' served a stale cache hit (executed {market_analyzer.calls}x total, "
        f"expected 2 if it recomputed)"
    )

    if not (layer1_sessionstore or layer2_accumulation or layer2_market_stale):
        print("\n[FIX VERIFIED]")
        print("Neither caching layer leaks prior-review state into subsequent reviews:")
        print("  - SessionStore: run() persists only the current review's results,")
        print("    so keys from a previous review are cleared.")
        print("  - ContextManager: reset per review, so cached_results do not accumulate")
        print("    and market_analyzer recomputes instead of serving a stale memoized result.")
        return 0

    print("\n[REGRESSION DETECTED]")
    print("One or more layers leaked prior-review state for Run 2 (see [X] STALE above).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
