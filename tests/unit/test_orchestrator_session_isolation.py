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


class FakeSessionStore(SessionStore):
    """In-memory stand-in with the same interface as the Redis session store."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}

    def get(self, session_id: str) -> dict | None:
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
