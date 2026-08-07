"""Tests for orchestrator.py, covering issue #47.

Agent state wasn't persisted across API restarts, causing in-progress
reviews to be lost. `Orchestrator.run()` used to call `session_store.set()`
exactly once, after its entire tool-execution loop finished. If the API
process died mid-review, none of the already-completed tool results had
ever been written to Redis, and even when a previous session *was* loaded,
nothing used it to skip work already done.
"""

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import ToolResult


class FakeRedis:
    """Minimal in-memory stand-in for redis.Redis, just enough for SessionStore."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, _ttl, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


class FakeTool:
    """Stands in for a real analysis tool (e.g. one repo scan)."""

    def __init__(self, name):
        self.name = name

    def execute(self, input_data: dict) -> ToolResult:
        return ToolResult(success=True, data={"tool": self.name, "input": input_data})


class CountingTool(FakeTool):
    """A FakeTool that tracks how many times it was actually executed.

    Used to prove that resumed tools are *not* re-executed, and that tools
    without a usable prior result are.
    """

    def __init__(self, name):
        super().__init__(name)
        self.call_count = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.call_count += 1
        return super().execute(input_data)


class SimulatedCrash(BaseException):
    """Stands in for the API process dying mid-review (e.g. an OOM kill or
    deploy restart interrupting the request).

    Subclasses BaseException rather than Exception so it escapes both
    `retry_with_backoff`'s `except Exception` and `Orchestrator.run()`'s
    per-tool `except Exception` handling -- a real process kill isn't a
    recoverable tool error, it just stops execution wherever it was.
    """


class CrashingTool(FakeTool):
    """A tool whose execution simulates the process dying instead of failing."""

    def execute(self, input_data: dict) -> ToolResult:
        raise SimulatedCrash("process killed mid-tool-execution")


def profile_with_five_plan_steps() -> dict:
    """Profile data shaped to make Orchestrator._build_plan() emit exactly
    5 steps, in this order: github_tool, tech_detector, readme_scorer,
    skill_extractor, market_analyzer (see agent/orchestrator.py:_build_plan).
    """
    return {
        "github_username": "octocat",
        "projects": [{"github_repo": "hello-world"}],
        "files": ["main.py"],
        "readme_content": "# Hello",
        "resume_text": "Experienced engineer",
    }


@pytest.mark.unit
class TestOrchestrator:
    """Test suite for Orchestrator."""

    @pytest.fixture
    def session_store(self):
        """Create a SessionStore backed by a fresh FakeRedis."""
        return SessionStore(FakeRedis())

    def test_partial_progress_survives_a_mid_review_restart(self, session_store):
        """Test that tool results completed before a mid-review crash are
        persisted to Redis, not just the ones from a fully-finished run."""
        profile_id = "profile-123"
        tools = {
            "github_tool": FakeTool("github_tool"),
            "tech_detector": FakeTool("tech_detector"),
            "readme_scorer": FakeTool("readme_scorer"),
            "skill_extractor": CrashingTool("skill_extractor"),
            "market_analyzer": FakeTool("market_analyzer"),
        }
        orchestrator = Orchestrator(tools=tools, session_store=session_store)

        # The 4th of 5 planned tools "crashes" instead of completing --
        # simulating the API process dying partway through a review.
        with pytest.raises(SimulatedCrash):
            orchestrator.run(profile_id, profile_with_five_plan_steps())

        # A restart spins up a brand new process/Orchestrator. The only
        # thing that can survive that is whatever made it into Redis
        # before the crash.
        resumed_session = session_store.get(profile_id)

        assert resumed_session is not None, (
            "3 of 5 tool results were computed but nothing was persisted to "
            "Redis -- a restart here loses all in-progress review work."
        )
        assert set(resumed_session) == {"github_tool", "tech_detector", "readme_scorer"}

    def test_resumed_run_skips_already_completed_tools(self, session_store):
        """Test that a fresh Orchestrator resuming a partially-completed
        session only executes the tools that weren't already done."""
        profile_id = "profile-456"

        # Simulate a prior run that made it through the first 3 tools
        # before a restart -- exactly what the test above proves gets
        # persisted.
        already_done = {
            "github_tool": {"tool": "github_tool", "resumed": True},
            "tech_detector": {"tool": "tech_detector", "resumed": True},
            "readme_scorer": {"tool": "readme_scorer", "resumed": True},
        }
        session_store.set(profile_id, already_done)

        tools = {
            "github_tool": CountingTool("github_tool"),
            "tech_detector": CountingTool("tech_detector"),
            "readme_scorer": CountingTool("readme_scorer"),
            "skill_extractor": CountingTool("skill_extractor"),
            "market_analyzer": CountingTool("market_analyzer"),
        }
        orchestrator = Orchestrator(tools=tools, session_store=session_store)

        result = orchestrator.run(profile_id, profile_with_five_plan_steps())

        for name in ("github_tool", "tech_detector", "readme_scorer"):
            assert tools[name].call_count == 0, (
                f"{name} already completed before the restart and should "
                "not have been re-executed"
            )
            assert result["tool_results"][name] == already_done[name]

        for name in ("skill_extractor", "market_analyzer"):
            assert (
                tools[name].call_count == 1
            ), f"{name} had not completed yet and should execute exactly once"

    def test_resume_retries_tool_that_previously_errored(self, session_store):
        """Test that a tool recorded as a failure on a previous attempt is
        re-executed on resume rather than treated as done."""
        profile_id = "profile-789"

        # A previous attempt recorded a failure for readme_scorer -- this
        # must not be treated as "done", or a transient failure would block
        # the review forever.
        session_store.set(profile_id, {"readme_scorer": {"error": "boom", "success": False}})

        readme_scorer = CountingTool("readme_scorer")
        tools = {"readme_scorer": readme_scorer, "market_analyzer": FakeTool("market_analyzer")}
        orchestrator = Orchestrator(tools=tools, session_store=session_store)

        result = orchestrator.run(profile_id, {"readme_content": "# Hello"})

        assert readme_scorer.call_count == 1
        assert result["tool_results"]["readme_scorer"] == {
            "tool": "readme_scorer",
            "input": {"readme_content": "# Hello"},
        }

    def test_run_without_session_store_still_works(self):
        """No session_store configured (None) must behave exactly like an
        in-memory-only run -- no crash, no resume, normal results."""
        tools = {
            "readme_scorer": FakeTool("readme_scorer"),
            "market_analyzer": FakeTool("market_analyzer"),
        }
        orchestrator = Orchestrator(tools=tools, session_store=None)

        result = orchestrator.run("profile-no-store", {"readme_content": "# Hello"})

        assert set(result["tool_results"]) == {"readme_scorer", "market_analyzer"}

    def test_resume_ignores_stale_session_state_from_a_renamed_tool(self, session_store):
        """If a deploy renames/removes a plan step between the crashed run
        and the resume, the old key simply has no counterpart in the new
        plan -- it should be ignored, not crash the run."""
        profile_id = "profile-drift"
        session_store.set(profile_id, {"old_repo_scanner": {"some": "stale data"}})

        readme_scorer = CountingTool("readme_scorer")
        market_analyzer = CountingTool("market_analyzer")
        tools = {"readme_scorer": readme_scorer, "market_analyzer": market_analyzer}
        orchestrator = Orchestrator(tools=tools, session_store=session_store)

        result = orchestrator.run(profile_id, {"readme_content": "# Hello"})

        assert readme_scorer.call_count == 1
        assert market_analyzer.call_count == 1
        assert set(result["tool_results"]) >= {"readme_scorer", "market_analyzer"}
