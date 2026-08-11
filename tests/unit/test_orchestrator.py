"""Tests for orchestrator.py"""
import pytest

from agent.orchestrator import Orchestrator


class StubTool:
    """Fake tool that records how many times it actually executes."""

    name = "stub_tool"

    def __init__(self) -> None:
        self.call_count = 0

    def execute(self, tool_input: dict) -> dict:
        self.call_count += 1
        return {"call_number": self.call_count}


@pytest.mark.unit
class TestOrchestrator:
    """Test suite for Orchestrator."""

    @pytest.fixture
    def stub_tool(self):
        """Create a StubTool instance."""
        return StubTool()

    @pytest.fixture
    def orchestrator(self, stub_tool):
        """Create an Orchestrator wired up with a single stub tool."""
        return Orchestrator(tools={"github_tool": stub_tool})

    @pytest.fixture
    def profile_data(self):
        """Profile data that triggers exactly one tool call (github_tool)."""
        return {
            "github_username": "someuser",
            "projects": [{"github_repo": "my-portfolio-site"}],
        }

    def test_tool_executes_on_first_review(self, orchestrator, stub_tool, profile_data):
        """Test that the tool actually runs on the first review."""
        orchestrator.run(profile_id="user-123", profile_data=profile_data)

        assert stub_tool.call_count == 1

    def test_tool_re_executes_on_second_review_same_input(
        self, orchestrator, stub_tool, profile_data
    ):
        """Regression test for #43: a second review for the same user with
        the same tool input must re-run the tool rather than returning a
        cached result from the previous review."""
        orchestrator.run(profile_id="user-123", profile_data=profile_data)
        orchestrator.run(profile_id="user-123", profile_data=profile_data)

        assert stub_tool.call_count == 2

    def test_second_review_returns_fresh_result_not_stale(
        self, orchestrator, stub_tool, profile_data
    ):
        """Regression test for #43: the tool_results from a second review
        must reflect a fresh execution, not the first review's cached data."""
        first = orchestrator.run(profile_id="user-123", profile_data=profile_data)
        second = orchestrator.run(profile_id="user-123", profile_data=profile_data)

        assert first["tool_results"]["github_tool"]["call_number"] == 1
        assert second["tool_results"]["github_tool"]["call_number"] == 2

    def test_different_users_do_not_share_cache(self, profile_data):
        """Test that two different users' reviews don't leak cached results
        between each other."""
        stub_tool = StubTool()
        orchestrator = Orchestrator(tools={"github_tool": stub_tool})

        orchestrator.run(profile_id="user-A", profile_data=profile_data)
        orchestrator.run(profile_id="user-B", profile_data=profile_data)

        assert stub_tool.call_count == 2
