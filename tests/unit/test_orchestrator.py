"""Tests for orchestrator.py"""

from unittest.mock import Mock, patch

import pytest

from agent.orchestrator import Orchestrator


@pytest.mark.unit
class TestOrchestrator:
    """Test suite for Orchestrator."""

    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool that succeeds."""
        tool = Mock()
        tool.name = "github_tool"
        tool.execute = Mock(return_value={"stars": 42})
        return tool

    @pytest.fixture
    def failing_tool(self):
        """Create a mock tool that always raises."""
        tool = Mock()
        tool.name = "github_tool"
        tool.execute = Mock(side_effect=RuntimeError("boom"))
        return tool

    @pytest.fixture
    def orchestrator(self, mock_tool):
        """Create an Orchestrator with a single succeeding tool."""
        return Orchestrator(tools={"github_tool": mock_tool})

    @pytest.fixture
    def profile_data(self):
        """Return a minimal profile_data dict with a GitHub repo."""
        return {
            "github_username": "alice",
            "projects": [{"github_repo": "myrepo"}],
        }

    def test_orchestrator_init_stores_tools(self, mock_tool):
        """
        Orchestrator init should correctly store the provided tools dictionary.
        """
        orch = Orchestrator(tools={"github_tool": mock_tool})

        assert "github_tool" in orch.tools

    def test_orchestrator_init_sets_default_timeout(self, mock_tool):
        """
        Orchestrator init should set the default tool_timeout to 30.0 seconds.
        """
        orch = Orchestrator(tools={"github_tool": mock_tool})

        assert orch.tool_timeout == 30.0

    def test_orchestrator_init_sets_custom_timeout(self, mock_tool):
        """
        Orchestrator init should respect a provided custom tool_timeout value.
        """
        orch = Orchestrator(tools={"github_tool": mock_tool}, tool_timeout=10.0)

        assert orch.tool_timeout == 10.0

    def test_run_valid_profile_returns_profile_id(self, orchestrator, profile_data):
        """
        run() should return a dictionary containing the provided profile_id.
        """
        result = orchestrator.run("alice-001", profile_data)

        assert result["profile_id"] == "alice-001"

    def test_run_valid_profile_returns_tool_results_key(self, orchestrator, profile_data):
        """
        run() should return a dictionary containing a 'tool_results' key.
        """
        result = orchestrator.run("alice-001", profile_data)

        assert "tool_results" in result

    def test_run_empty_profile_returns_empty_results(self, orchestrator):
        """
        run() with an empty profile should return empty tool results.
        """
        result = orchestrator.run("p-empty", {})

        assert result["tool_results"] == {}

    def test_run_profile_with_repo_calls_github_tool(self, mock_tool, profile_data):
        """
        run() should execute the github_tool when the profile contains a GitHub repo.
        """
        orch = Orchestrator(tools={"github_tool": mock_tool})

        orch.run("alice-001", profile_data)

        mock_tool.execute.assert_called_once()

    def test_run_profile_without_repo_skips_github_tool(self, mock_tool):
        """
        run() should not execute the github_tool if the profile has no github_repo.
        """
        orch = Orchestrator(tools={"github_tool": mock_tool})
        profile_data = {
            "github_username": "carol",
            "projects": [{"title": "no repo here"}],
        }

        orch.run("carol-001", profile_data)

        mock_tool.execute.assert_not_called()

    def test_run_tool_failure_stores_error_result(self, failing_tool, profile_data):
        """
        run() should record an error result for a tool that raises an exception.
        """
        orch = Orchestrator(tools={"github_tool": failing_tool})

        result = orch.run("dave-001", profile_data)

        assert result["tool_results"]["github_tool"]["success"] is False

    def test_run_tool_failure_stores_error_message(self, failing_tool, profile_data):
        """
        run() should include the exception message in the tool's error result.
        """
        orch = Orchestrator(tools={"github_tool": failing_tool})

        result = orch.run("dave-001", profile_data)

        assert "boom" in result["tool_results"]["github_tool"]["error"]

    def test_run_tool_failure_logs_exc_info(self, failing_tool, profile_data):
        """
        run() should log the tool failure with exc_info=True.

        This guarantees stack traces are recorded when a tool crashes (Issue #44).
        """
        orch = Orchestrator(tools={"github_tool": failing_tool})

        with patch("agent.orchestrator.logger") as mock_logger:
            orch.run("dave-001", profile_data)

        error_calls = [
            c for c in mock_logger.error.call_args_list
            if c.args and c.args[0] in ("tool_execution_failed", "tool_execution_error")
        ]
        assert error_calls
        for c in error_calls:
            assert c.kwargs.get("exc_info") is True

    def test_run_tool_failure_continues_execution(self):
        """
        run() should continue executing subsequent tools even if one tool fails.
        """
        failing = Mock()
        failing.name = "github_tool"
        failing.execute = Mock(side_effect=RuntimeError("fail"))

        passing = Mock()
        passing.name = "readme_scorer"
        passing.execute = Mock(return_value={"score": 80})

        orch = Orchestrator(tools={"github_tool": failing, "readme_scorer": passing})
        profile_data = {
            "github_username": "frank",
            "projects": [{"github_repo": "repo"}],
            "readme_content": "# Hello",
        }

        result = orch.run("frank-001", profile_data)

        assert result["tool_results"]["readme_scorer"]["score"] == 80

    def test_execute_tool_unknown_tool_raises_value_error(self, orchestrator):
        """
        _execute_tool() should raise a ValueError when called with an unregistered tool name.
        """
        with pytest.raises(ValueError, match="Unknown tool"):
            orchestrator._execute_tool("no_such_tool", {})

    def test_execute_tool_success_returns_result(self, mock_tool):
        """
        _execute_tool() should return the successful result data from the tool.
        """
        orch = Orchestrator(tools={"github_tool": mock_tool})

        result = orch._execute_tool("github_tool", {"github_username": "x", "repo_name": "y"})

        assert result == {"stars": 42}

    def test_execute_tool_exception_reraises_exception(self, failing_tool):
        """
        _execute_tool() should re-raise any exception thrown by the tool's execute method.
        """
        orch = Orchestrator(tools={"github_tool": failing_tool})

        with pytest.raises(RuntimeError, match="boom"):
            orch._execute_tool("github_tool", {"github_username": "x", "repo_name": "y"})

    def test_execute_tool_timeout_logs_with_exc_info(self):
        """
        _execute_tool() should log TimeoutErrors with exc_info=True.
        """
        timeout_tool = Mock()
        timeout_tool.name = "github_tool"
        timeout_tool.execute = Mock(side_effect=TimeoutError("timed out"))
        orch = Orchestrator(tools={"github_tool": timeout_tool}, tool_timeout=0.0)

        with patch("agent.orchestrator.logger") as mock_logger, pytest.raises(TimeoutError):
            orch._execute_tool("github_tool", {"github_username": "x", "repo_name": "y"})

        error_calls = [
            c for c in mock_logger.error.call_args_list
            if c.args and c.args[0] in ("tool_timeout", "tool_execution_error")
        ]
        assert error_calls
        for c in error_calls:
            assert c.kwargs.get("exc_info") is True

    def test_build_plan_empty_profile_returns_empty_list(self, orchestrator):
        """
        _build_plan() should return an empty execution plan for an empty profile.
        """
        plan = orchestrator._build_plan({})

        assert plan == []

    def test_build_plan_github_data_includes_github_tool(self, orchestrator, profile_data):
        """
        _build_plan() should include github_tool if the profile contains repo information.
        """
        plan = orchestrator._build_plan(profile_data)

        tool_names = [name for name, _ in plan]
        assert "github_tool" in tool_names

    def test_build_plan_readme_content_includes_readme_scorer(self, orchestrator):
        """
        _build_plan() should include readme_scorer if the profile contains readme content.
        """
        plan = orchestrator._build_plan({"readme_content": "# Hello World"})

        tool_names = [name for name, _ in plan]
        assert "readme_scorer" in tool_names

    def test_build_plan_nonempty_plan_includes_market_analyzer(self, orchestrator):
        """
        _build_plan() should append market_analyzer whenever other tools are scheduled.
        """
        plan = orchestrator._build_plan({"readme_content": "# Hello World"})

        tool_names = [name for name, _ in plan]
        assert "market_analyzer" in tool_names

    def test_build_plan_empty_plan_excludes_market_analyzer(self, orchestrator):
        """
        _build_plan() should not append market_analyzer if no other tools are in the plan.
        """
        plan = orchestrator._build_plan({})

        tool_names = [name for name, _ in plan]
        assert "market_analyzer" not in tool_names

    def test_run_with_session_store_calls_set(self, mock_tool, profile_data):
        """
        run() should persist the results to the session store if one is provided.
        """
        mock_store = Mock()
        mock_store.get = Mock(return_value=None)
        mock_store.set = Mock()
        orch = Orchestrator(tools={"github_tool": mock_tool}, session_store=mock_store)

        orch.run("p-session", profile_data)

        mock_store.set.assert_called_once()

    def test_run_with_session_store_loads_previous_state(self, mock_tool, profile_data):
        """
        run() should load existing state from the session store if available.
        """
        mock_store = Mock()
        mock_store.get = Mock(return_value={"previous": "data"})
        mock_store.set = Mock()
        orch = Orchestrator(tools={"github_tool": mock_tool}, session_store=mock_store)

        orch.run("p-load", profile_data)

        mock_store.get.assert_called_once_with("p-load")
