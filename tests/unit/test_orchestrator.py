"""Tests for agent/orchestrator.py"""

from unittest.mock import Mock

import pytest

from agent.orchestrator import Orchestrator


def make_tool(name: str, data: dict | None = None, raises: Exception | None = None) -> Mock:
    """Build a fake tool whose execute() returns an object with a .data attr."""
    tool = Mock()
    tool.name = name
    if raises is not None:
        tool.execute.side_effect = raises
    else:
        result = Mock()
        result.data = data if data is not None else {"ok": True}
        tool.execute.return_value = result
    return tool


@pytest.mark.unit
class TestBuildPlan:
    """Plan construction is the orchestrator's core branching logic."""

    def test_empty_profile_produces_empty_plan(self) -> None:
        orch = Orchestrator(tools={})
        assert orch._build_plan({}) == []

    def test_market_analyzer_appended_only_when_other_tools_present(self) -> None:
        orch = Orchestrator(tools={})
        plan = orch._build_plan({"readme_content": "# Hi"})
        tool_names = [name for name, _ in plan]
        assert "readme_scorer" in tool_names
        assert tool_names[-1] == "market_analyzer"

    def test_no_market_analyzer_when_nothing_else_matched(self) -> None:
        orch = Orchestrator(tools={})
        plan = orch._build_plan({"irrelevant": "value"})
        assert plan == []

    def test_github_tool_added_for_first_repo_only(self) -> None:
        orch = Orchestrator(tools={})
        profile = {
            "github_username": "octocat",
            "projects": [
                {"github_repo": "repo-one"},
                {"github_repo": "repo-two"},
            ],
        }
        plan = orch._build_plan(profile)
        github_entries = [inp for name, inp in plan if name == "github_tool"]
        assert len(github_entries) == 1
        assert github_entries[0]["repo_name"] == "repo-one"

    def test_github_username_without_repo_adds_no_github_tool(self) -> None:
        orch = Orchestrator(tools={})
        profile = {"github_username": "octocat", "projects": [{"name": "no repo"}]}
        plan = orch._build_plan(profile)
        assert "github_tool" not in [name for name, _ in plan]

    def test_each_data_source_maps_to_its_tool(self) -> None:
        orch = Orchestrator(tools={})
        profile = {
            "files": ["main.py"],
            "readme_content": "# Title",
            "resume_text": "Engineer",
        }
        tool_names = [name for name, _ in orch._build_plan(profile)]
        assert "tech_detector" in tool_names
        assert "readme_scorer" in tool_names
        assert "skill_extractor" in tool_names


@pytest.mark.unit
class TestExecuteTool:
    """Single-tool execution: caching and unknown-tool guarding."""

    def test_unknown_tool_raises_value_error(self) -> None:
        orch = Orchestrator(tools={})
        with pytest.raises(ValueError, match="Unknown tool"):
            orch._execute_tool("nope", {})

    def test_result_is_cached_and_reused(self) -> None:
        tool = make_tool("readme_scorer", data={"score": 1})
        orch = Orchestrator(tools={"readme_scorer": tool})

        first = orch._execute_tool("readme_scorer", {"readme_content": "x"})
        second = orch._execute_tool("readme_scorer", {"readme_content": "x"})

        assert first is second
        # Second call served from cache -> underlying tool executed only once.
        assert tool.execute.call_count == 1

    def test_different_input_is_not_a_cache_hit(self) -> None:
        tool = make_tool("readme_scorer", data={"score": 1})
        orch = Orchestrator(tools={"readme_scorer": tool})

        orch._execute_tool("readme_scorer", {"readme_content": "a"})
        orch._execute_tool("readme_scorer", {"readme_content": "b"})

        assert tool.execute.call_count == 2


@pytest.mark.unit
class TestRun:
    """End-to-end orchestration loop."""

    def test_run_collects_results_and_returns_expected_shape(self) -> None:
        tool = make_tool("readme_scorer", data={"score": 0.9})
        orch = Orchestrator(
            tools={"readme_scorer": tool, "market_analyzer": make_tool("market_analyzer")}
        )

        output = orch.run("profile-1", {"readme_content": "# Hi"})

        assert output["profile_id"] == "profile-1"
        assert output["tool_results"]["readme_scorer"] == {"score": 0.9}
        assert "cached_results" in output

    def test_failing_tool_is_captured_not_raised(self) -> None:
        good = make_tool("readme_scorer", data={"score": 1})
        bad = make_tool("market_analyzer", raises=RuntimeError("boom"))
        orch = Orchestrator(tools={"readme_scorer": good, "market_analyzer": bad})

        output = orch.run("p", {"readme_content": "# Hi"})

        assert output["tool_results"]["readme_scorer"] == {"score": 1}
        assert output["tool_results"]["market_analyzer"]["success"] is False
        assert "boom" in output["tool_results"]["market_analyzer"]["error"]

    def test_unknown_tool_in_plan_becomes_error_entry(self) -> None:
        # market_analyzer is planned (because readme matched) but not registered.
        orch = Orchestrator(tools={"readme_scorer": make_tool("readme_scorer")})

        output = orch.run("p", {"readme_content": "# Hi"})

        assert output["tool_results"]["market_analyzer"]["success"] is False

    def test_run_without_session_store_does_not_crash(self) -> None:
        orch = Orchestrator(tools={"readme_scorer": make_tool("readme_scorer")}, session_store=None)
        output = orch.run("p", {"readme_content": "# Hi"})
        assert output["profile_id"] == "p"

    def test_session_store_is_loaded_and_persisted(self) -> None:
        store = Mock()
        store.get.return_value = {"prior": "state"}
        orch = Orchestrator(
            tools={"readme_scorer": make_tool("readme_scorer", data={"score": 1})},
            session_store=store,
        )

        orch.run("profile-9", {"readme_content": "# Hi"})

        store.get.assert_called_once_with("profile-9")
        store.set.assert_called_once()
        saved_id, saved_state = store.set.call_args.args
        assert saved_id == "profile-9"
        # Existing state is preserved and new results merged in.
        assert saved_state["prior"] == "state"
        assert "readme_scorer" in saved_state
