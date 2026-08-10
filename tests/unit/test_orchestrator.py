"""Regression tests for issue #43: agent session state leaking across reviews.

Two consecutive reviews on a single *reused* Orchestrator (README-only, then
resume-only for the same profile_id) must not let the first review's state
survive into the second, across both cache layers:

* Layer 1 - the Redis-backed SessionStore (persisted state).
* Layer 2 - the in-memory ContextManager (within-session memoization), which
  also caused market_analyzer to serve a stale result because its input is the
  constant ``{"detected_skills": {}}`` every run.

Each assertion is written so it would FAIL if the corresponding fix regressed.
For market_analyzer we assert re-execution by *call count* (not by output),
because identical input yields identical output whether the result was cached
or freshly computed.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator


class FakeRedis:
    """Minimal in-memory stand-in for the Redis calls SessionStore makes."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class DummyTool:
    """Deterministic tool that always returns the same result dict."""

    def __init__(self, name: str, result: dict) -> None:
        self.name = name
        self.result = result

    def execute(self, tool_input: dict) -> dict:
        return self.result


class SpyTool:
    """Tool whose execute() is a Mock (so we can assert call_count) and that
    tags each result with its call number, making the two runs observably
    distinct even though market_analyzer receives the same input every run."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._calls = 0
        self.execute = Mock(side_effect=self._execute)

    def _execute(self, tool_input: dict) -> dict:
        self._calls += 1
        return {
            "call_number": self._calls,
            "detected_skills_seen": tool_input.get("detected_skills"),
        }


@pytest.mark.unit
class TestOrchestratorClearsStateBetweenReviews:
    """#43: a reused Orchestrator must not leak one review's state into the next."""

    @pytest.fixture
    def market_analyzer(self) -> SpyTool:
        return SpyTool("market_analyzer")

    @pytest.fixture
    def session_store(self) -> SessionStore:
        # FakeRedis implements only the calls SessionStore uses; the real
        # constructor is typed for redis.Redis, so silence that arg-type check.
        return SessionStore(FakeRedis())  # type: ignore[arg-type]

    @pytest.fixture
    def orchestrator(self, market_analyzer: SpyTool, session_store: SessionStore) -> Orchestrator:
        tools = {
            "readme_scorer": DummyTool("readme_scorer", {"score": 95, "feedback": "Great README"}),
            "skill_extractor": DummyTool("skill_extractor", {"skills": ["Python", "FastAPI"]}),
            "market_analyzer": market_analyzer,
        }
        return Orchestrator(tools=tools, session_store=session_store)

    @pytest.fixture
    def reviews(self, orchestrator: Orchestrator) -> SimpleNamespace:
        """Run two reviews on the SAME orchestrator: README-only, then resume-only."""
        profile_id = "user_profile_43"
        result1 = orchestrator.run(profile_id, {"readme_content": "# My Project"})
        result2 = orchestrator.run(profile_id, {"resume_text": "Experienced Python developer"})
        return SimpleNamespace(profile_id=profile_id, result1=result1, result2=result2)

    def test_run1_executes_readme_and_market_tools(self, reviews: SimpleNamespace) -> None:
        # Sanity: the README-only review really ran readme_scorer + market_analyzer.
        assert "readme_scorer" in reviews.result1["tool_results"]
        assert reviews.result1["tool_results"]["market_analyzer"]["call_number"] == 1

    def test_redis_state_holds_only_current_review(
        self, reviews: SimpleNamespace, session_store: SessionStore
    ) -> None:
        # Layer 1 (SessionStore): run 2's persisted state must not carry run 1's
        # readme_scorer, and must contain run 2's own tool (skill_extractor).
        persisted = session_store.get(reviews.profile_id)
        assert persisted is not None
        assert "readme_scorer" not in persisted
        assert "skill_extractor" in persisted

    def test_cached_results_not_accumulated_across_reviews(self, reviews: SimpleNamespace) -> None:
        # Layer 2a (ContextManager): run 2's cached_results must not include the
        # readme_scorer entry memoized during run 1. Keys are "<tool>:<hash>".
        cached_keys = reviews.result2["cached_results"].keys()
        assert not any(key.startswith("readme_scorer:") for key in cached_keys)
        assert any(key.startswith("skill_extractor:") for key in cached_keys)

    def test_market_analyzer_recomputes_each_review(
        self, reviews: SimpleNamespace, market_analyzer: SpyTool
    ) -> None:
        # Layer 2b (ContextManager): market_analyzer receives the constant input
        # {"detected_skills": {}} every run, so a stale cache would serve run 1's
        # result and skip execution. Assert it actually re-executed in run 2 via
        # call count -- output alone can't distinguish a cache hit from a fresh run.
        assert market_analyzer.execute.call_count == 2
        assert reviews.result2["tool_results"]["market_analyzer"]["call_number"] == 2
