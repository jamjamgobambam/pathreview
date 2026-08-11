"""Unit tests for Orchestrator mid-run checkpointing and resume (issue #47)."""

from __future__ import annotations

from typing import Any

import pytest

from agent.memory.context_manager import ContextManager
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class FakeSessionStore:
    """In-memory stand-in for Redis SessionStore."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self.set_calls = 0

    def get(self, session_id: str) -> dict[str, Any] | None:
        return self._data.get(session_id)

    def set(self, session_id: str, data: dict[str, Any], ttl_seconds: int = 3600) -> None:
        self.set_calls += 1
        self._data[session_id] = dict(data)

    def delete(self, session_id: str) -> None:
        self._data.pop(session_id, None)


class CountingTool(BaseTool):
    """Tool that records how many times it was executed."""

    def __init__(self, name: str, fail: bool = False) -> None:
        self.name = name
        self.description = f"Counting mock for {name}"
        self.call_count = 0
        self.fail = fail

    def execute(self, input_data: dict) -> ToolResult:
        self.call_count += 1
        if self.fail:
            raise RuntimeError(f"{self.name} failed")
        return ToolResult(
            success=True,
            data={"tool": self.name, "call": self.call_count, "input": input_data},
        )


def _profile_data() -> dict[str, Any]:
    return {
        "github_username": "test-user",
        "projects": [{"github_repo": "test-repo"}],
        "files": ["main.py"],
        "readme_content": "# Test",
        "resume_text": "Python engineer",
        "repo_metadata": {},
    }


def _tools(**overrides: CountingTool) -> dict[str, CountingTool]:
    tools = {
        "github_tool": CountingTool("github_tool"),
        "tech_detector": CountingTool("tech_detector"),
        "readme_scorer": CountingTool("readme_scorer"),
        "skill_extractor": CountingTool("skill_extractor"),
        "market_analyzer": CountingTool("market_analyzer"),
    }
    tools.update(overrides)
    return tools


@pytest.mark.unit
class TestAgentStatePersistence:
    """Checkpoint after each tool; resume skips completed steps."""

    def test_checkpoints_after_each_tool(self) -> None:
        store = FakeSessionStore()
        tools = _tools()
        orch = Orchestrator(tools=tools, session_store=store)

        orch.run("profile-1", _profile_data())

        # One Redis write per planned tool (5-step plan)
        assert store.set_calls == 5
        session = store.get("profile-1")
        assert session is not None
        assert len(session) == 5

    def test_resume_skips_completed_tools(self) -> None:
        store = FakeSessionStore()
        tools = _tools()
        orch = Orchestrator(tools=tools, session_store=store)
        profile = _profile_data()

        # Seed a partial checkpoint as if we died after github_tool
        plan = orch._build_plan(profile)
        first_name, first_input = plan[0]
        step_key = Orchestrator._step_key(first_name, first_input)
        store.set(
            "profile-1",
            {step_key: {"tool": first_name, "call": 1, "resumed": True}},
        )

        result = orch.run("profile-1", profile)

        # First tool restored from Redis — never executed
        assert tools["github_tool"].call_count == 0
        assert result["tool_results"]["github_tool"]["resumed"] is True

        # Remaining tools still ran
        assert tools["tech_detector"].call_count == 1
        assert tools["readme_scorer"].call_count == 1
        assert tools["skill_extractor"].call_count == 1
        assert tools["market_analyzer"].call_count == 1

    def test_full_resume_executes_nothing(self) -> None:
        store = FakeSessionStore()
        tools = _tools()
        orch = Orchestrator(tools=tools, session_store=store)
        profile = _profile_data()

        # Complete first run
        first = orch.run("profile-1", profile)
        assert all(t.call_count == 1 for t in tools.values())

        # Reset counters; second run should skip everything
        for tool in tools.values():
            tool.call_count = 0

        second = orch.run("profile-1", profile)
        assert all(t.call_count == 0 for t in tools.values())
        assert second["tool_results"].keys() == first["tool_results"].keys()

    def test_no_session_store_still_runs(self) -> None:
        tools = _tools()
        orch = Orchestrator(tools=tools, session_store=None)

        result = orch.run("profile-1", _profile_data())

        assert len(result["tool_results"]) == 5
        assert all(t.call_count == 1 for t in tools.values())

    def test_failed_tool_is_checkpointed(self) -> None:
        store = FakeSessionStore()
        tools = _tools(github_tool=CountingTool("github_tool", fail=True))
        orch = Orchestrator(tools=tools, session_store=store)
        profile = _profile_data()

        result = orch.run("profile-1", profile)

        assert result["tool_results"]["github_tool"]["success"] is False
        session = store.get("profile-1")
        assert session is not None
        plan = orch._build_plan(profile)
        step_key = Orchestrator._step_key(plan[0][0], plan[0][1])
        assert step_key in session
        assert session[step_key]["success"] is False

        # Resume should not retry the failed step
        tools["github_tool"].call_count = 0
        orch.run("profile-1", profile)
        assert tools["github_tool"].call_count == 0

    def test_step_key_includes_input_hash(self) -> None:
        key_a = Orchestrator._step_key("github_tool", {"repo": "a"})
        key_b = Orchestrator._step_key("github_tool", {"repo": "b"})
        assert key_a != key_b
        assert key_a.startswith("github_tool:")
        assert ContextManager.hash_input({"repo": "a"}) in key_a
