"""Unit tests for agent/error_handling.py's retry_with_backoff decorator.

Orchestrator.run()'s fix for issue #44 (surfacing tool failures via a
top-level success/failed_tools indicator) depends on retry_with_backoff
re-raising the original exception once retries are exhausted, rather than
swallowing it. These tests confirm that contract directly.
"""

from unittest.mock import patch

import pytest

from agent.error_handling import retry_with_backoff


@pytest.mark.unit
def test_retry_with_backoff_retries_then_succeeds() -> None:
    """A function that fails twice then succeeds should return the success value."""
    attempts = []

    @retry_with_backoff(max_retries=3, backoff_factor=1.0)
    def flaky() -> str:
        attempts.append(1)
        if len(attempts) < 3:
            raise ValueError("not yet")
        return "ok"

    with patch("agent.error_handling.time.sleep") as mock_sleep:
        result = flaky()

    assert result == "ok"
    assert len(attempts) == 3
    assert mock_sleep.call_count == 2


@pytest.mark.unit
def test_retry_with_backoff_raises_after_exhausting_retries() -> None:
    """Once max_retries is exhausted, the original exception must propagate,
    not be swallowed - this is what Orchestrator.run()'s except block relies on
    to receive a real exception to record in failed_tools."""

    @retry_with_backoff(max_retries=2, backoff_factor=1.0)
    def always_fails() -> None:
        raise RuntimeError("simulated failure")

    with (
        patch("agent.error_handling.time.sleep"),
        pytest.raises(RuntimeError, match="simulated failure"),
    ):
        always_fails()


@pytest.mark.unit
def test_retry_with_backoff_respects_exception_filter() -> None:
    """An exception type outside the `exceptions` filter must propagate
    immediately on the first attempt, without retrying."""
    attempts = []

    @retry_with_backoff(max_retries=3, backoff_factor=1.0, exceptions=(ValueError,))
    def wrong_error_type() -> None:
        attempts.append(1)
        raise TypeError("not a ValueError")

    with (
        patch("agent.error_handling.time.sleep") as mock_sleep,
        pytest.raises(TypeError, match="not a ValueError"),
    ):
        wrong_error_type()

    assert len(attempts) == 1
    mock_sleep.assert_not_called()
