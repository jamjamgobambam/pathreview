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

    def test_orchestrator_swallows_tool_failure_without_logging_exc_info(
        self, orchestrator: Orchestrator
    ) -> None:
        """run() must not propagate a crashing tool's exception, but the
        error log it emits is missing exc_info/stack trace context -
        reproducing issue #44.
        """
        with capture_logs() as captured_logs:
            # This must complete normally - the bug is that the orchestrator
            # never lets the exception reach the caller.
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
            # ... but none of the entries carry exception/stack trace context,
            # which is exactly the diagnostic gap issue #44 is about: logging
            # str(e) instead of passing exc_info=True.
            assert "exc_info" not in entry
            assert "exception" not in entry
