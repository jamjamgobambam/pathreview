"""Regression tests reproducing stale agent state across portfolio reviews."""

from copy import deepcopy

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import ToolResult


class RecordingTool:
    """Return the execution number so cache reuse is visible in assertions."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.calls += 1
        return ToolResult(
            success=True,
            data={"execution": self.calls, "input": deepcopy(input_data)},
        )


class FailAfterFirstTool(RecordingTool):
    """Succeed once, then fail so replacement of an old success is testable."""

    def execute(self, input_data: dict) -> ToolResult:
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError("current review failed")
        return ToolResult(
            success=True,
            data={"execution": self.calls, "input": deepcopy(input_data)},
        )


class SingleToolPlanOrchestrator(Orchestrator):
    """Build a controlled one-tool plan for cache-boundary tests."""

    def _build_plan(self, profile_data: dict) -> list[tuple[str, dict]]:
        return [("review_tool", deepcopy(profile_data))]


class DuplicateToolPlanOrchestrator(Orchestrator):
    """Schedule the same call twice inside one review."""

    def _build_plan(self, profile_data: dict) -> list[tuple[str, dict]]:
        tool_input = deepcopy(profile_data)
        return [("review_tool", tool_input), ("review_tool", tool_input)]


class FakeSessionStore(SessionStore):
    """In-memory stand-in with the same interface as the Redis session store."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}
        self.get_calls = 0

    def get(self, session_id: str) -> dict | None:
        self.get_calls += 1
        state = self.sessions.get(session_id)
        return deepcopy(state) if state is not None else None

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        self.sessions[session_id] = deepcopy(data)

    def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


@pytest.mark.unit
def test_second_review_reexecutes_tools_instead_of_reusing_first_review_cache() -> None:
    """A changed portfolio should start a fresh tool-execution session."""
    skill_extractor = RecordingTool("skill_extractor")
    market_analyzer = RecordingTool("market_analyzer")
    store = FakeSessionStore()
    orchestrator = Orchestrator(
        tools={
            "skill_extractor": skill_extractor,
            "market_analyzer": market_analyzer,
        },
        session_store=store,
    )

    orchestrator.run("profile-123", {"resume_text": "Skills: Python"})
    second_review = orchestrator.run("profile-123", {"resume_text": "Skills: Rust"})

    assert skill_extractor.calls == 2
    assert market_analyzer.calls == 2
    assert second_review["tool_results"]["market_analyzer"]["execution"] == 2


@pytest.mark.unit
def test_second_review_replaces_persisted_state_instead_of_merging_old_results() -> None:
    """Tools omitted from an updated portfolio must not remain in Redis state."""
    readme_scorer = RecordingTool("readme_scorer")
    skill_extractor = RecordingTool("skill_extractor")
    market_analyzer = RecordingTool("market_analyzer")
    store = FakeSessionStore()
    orchestrator = Orchestrator(
        tools={
            "readme_scorer": readme_scorer,
            "skill_extractor": skill_extractor,
            "market_analyzer": market_analyzer,
        },
        session_store=store,
    )

    orchestrator.run("profile-123", {"readme_content": "# Original project"})
    orchestrator.run("profile-123", {"resume_text": "Updated portfolio"})

    assert set(store.sessions["profile-123"]) == {
        "skill_extractor",
        "market_analyzer",
    }
    assert store.get_calls == 0


@pytest.mark.unit
def test_identical_reviews_without_session_store_do_not_share_cache() -> None:
    """Each run should reexecute identical tool inputs without Redis configured."""
    review_tool = RecordingTool("review_tool")
    orchestrator = SingleToolPlanOrchestrator(tools={"review_tool": review_tool})

    first_review = orchestrator.run("profile-123", {"resume_text": "Skills: Python"})
    second_review = orchestrator.run("profile-123", {"resume_text": "Skills: Python"})

    assert review_tool.calls == 2
    assert first_review["tool_results"]["review_tool"]["execution"] == 1
    assert second_review["tool_results"]["review_tool"]["execution"] == 2
    assert len(second_review["cached_results"]) == 1


@pytest.mark.unit
def test_same_tool_call_is_memoized_within_one_review() -> None:
    """Review-local isolation must preserve useful same-review memoization."""
    review_tool = RecordingTool("review_tool")
    orchestrator = DuplicateToolPlanOrchestrator(tools={"review_tool": review_tool})

    review = orchestrator.run("profile-123", {"resume_text": "Skills: Python"})

    assert review_tool.calls == 1
    assert review["tool_results"]["review_tool"]["execution"] == 1
    assert len(review["cached_results"]) == 1


@pytest.mark.unit
def test_empty_review_replaces_old_persisted_results_with_empty_state() -> None:
    """An empty plan should not retain tools produced by an earlier review."""
    readme_scorer = RecordingTool("readme_scorer")
    market_analyzer = RecordingTool("market_analyzer")
    store = FakeSessionStore()
    orchestrator = Orchestrator(
        tools={
            "readme_scorer": readme_scorer,
            "market_analyzer": market_analyzer,
        },
        session_store=store,
    )

    orchestrator.run("profile-123", {"readme_content": "# Original project"})
    empty_review = orchestrator.run("profile-123", {})

    assert empty_review["tool_results"] == {}
    assert empty_review["cached_results"] == {}
    assert store.sessions["profile-123"] == {}


@pytest.mark.unit
def test_different_profiles_with_identical_inputs_do_not_share_cache() -> None:
    """One orchestrator instance must isolate sequential reviews by profile."""
    review_tool = RecordingTool("review_tool")
    orchestrator = SingleToolPlanOrchestrator(tools={"review_tool": review_tool})

    first_profile = orchestrator.run("profile-a", {"resume_text": "Skills: Python"})
    second_profile = orchestrator.run("profile-b", {"resume_text": "Skills: Python"})

    assert review_tool.calls == 2
    assert first_profile["tool_results"]["review_tool"]["execution"] == 1
    assert second_profile["tool_results"]["review_tool"]["execution"] == 2


@pytest.mark.unit
def test_current_failure_replaces_older_successful_persisted_result() -> None:
    """A failed rerun should not leave an earlier successful result in storage."""
    review_tool = FailAfterFirstTool("review_tool")
    store = FakeSessionStore()
    orchestrator = SingleToolPlanOrchestrator(
        tools={"review_tool": review_tool},
        session_store=store,
    )

    orchestrator.run("profile-123", {"resume_text": "Original"})
    failed_review = orchestrator.run("profile-123", {"resume_text": "Updated"})

    expected_failure = {
        "error": "current review failed",
        "success": False,
    }
    assert failed_review["tool_results"]["review_tool"] == expected_failure
    assert store.sessions["profile-123"]["review_tool"] == expected_failure
