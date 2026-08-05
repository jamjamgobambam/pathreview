"""Tests for orchestrator.py"""

from typing import Any

import pytest
from structlog.testing import capture_logs

from agent.orchestrator import Orchestrator


class CrashingTool:
    """A tool stub that always raises, simulating an unhandled tool crash."""

    name = "tech_detector"

    def execute(self, tool_input: dict[str, Any]) -> None:
        raise AttributeError("Simulated tool crash")


@pytest.mark.unit
class TestOrchestratorExceptionLogging:
    """Test suite covering issue #44: tool failures are swallowed without
    structured stack trace context, making them undiagnosable in production.
    """

    @pytest.fixture
    def orchestrator(self, monkeypatch: pytest.MonkeyPatch) -> Orchestrator:
        """Create an Orchestrator wired to a single crashing tool.

        The retry backoff sleep is patched out so the test doesn't pay the
        real ~1s `retry_with_backoff(max_retries=2, backoff_factor=1.5)`
        delay, and `_build_plan` is patched to deterministically schedule
        only the crashing tool (bypassing the profile_data heuristics that
        are irrelevant to this test).
        """
        orch = Orchestrator(
            tools={"tech_detector": CrashingTool()},
            session_store=None,
            tool_timeout=5.0,
        )
        monkeypatch.setattr("agent.error_handling.time.sleep", lambda seconds: None)
        monkeypatch.setattr(
            orch,
            "_build_plan",
            lambda profile_data: [("tech_detector", {"files": ["app.py"]})],
        )
        return orch

    def test_orchestrator_logs_exc_info_on_tool_failure(
        self, orchestrator: Orchestrator
    ) -> None:
        """run() must not propagate a crashing tool's exception, and the
        error log it emits must retain exc_info/stack trace context -
        verifying the fix for issue #44.
        """
        with capture_logs() as captured_logs:
            # This must complete normally - the orchestrator swallows the
            # exception internally and records a failure result instead.
            result = orchestrator.run("profile-123", {"files": ["app.py"]})

        # The orchestrator swallowed the crash and kept going.
        assert result["tool_results"]["tech_detector"] == {
            "error": "Simulated tool crash",
            "success": False,
        }

        # An error *was* logged for the failing tool ...
        failure_entries = [
            entry
            for entry in captured_logs
            if entry.get("tool") == "tech_detector" and entry["log_level"] == "error"
        ]
        assert len(failure_entries) >= 1, "expected the tool failure to be logged"

        for entry in failure_entries:
            assert entry["error"] == "Simulated tool crash"
            # ... and now carries exception/stack trace context. Depending on
            # the configured processor chain, structlog surfaces this as
            # either a truthy "exc_info" flag (the raw kwarg, when no
            # exception-formatting processor runs) or a rendered "exception"
            # traceback string (once one does) - either is proof the fix for
            # issue #44 is in place.
            assert entry.get("exc_info") or entry.get("exception"), (
                "expected exception/stack trace context to be present"
            )
