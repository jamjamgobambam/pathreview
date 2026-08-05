"""Tests for error_handling.py

Covers a latent bug found while investigating issue #44: with
max_retries=0, the `while attempt < max_retries` loop in
retry_with_backoff() never executes, `last_exception` stays None, and the
wrapper falls through returning None -- silently, with no exception raised
and nothing logged. Not reachable via the current Orchestrator (which
always passes max_retries=2), but a real defect in a function this issue
lists as relevant.
"""

import pytest

from agent.error_handling import retry_with_backoff


@pytest.mark.unit
class TestRetryWithBackoff:
    def test_max_retries_zero_raises_value_error(self):
        """max_retries=0 must raise immediately rather than silently
        returning None without ever calling the wrapped function."""
        with pytest.raises(ValueError, match="max_retries"):

            @retry_with_backoff(max_retries=0)
            def _never_called():
                raise AssertionError("should not be called")

    def test_succeeds_on_first_attempt(self):
        calls = []

        @retry_with_backoff(max_retries=3, backoff_factor=0.0)
        def _succeeds():
            calls.append(1)
            return "ok"

        assert _succeeds() == "ok"
        assert len(calls) == 1

    def test_succeeds_after_transient_failure(self):
        attempts = {"count": 0}

        @retry_with_backoff(max_retries=3, backoff_factor=0.0)
        def _fails_once_then_succeeds():
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise ValueError("transient")
            return "ok"

        assert _fails_once_then_succeeds() == "ok"
        assert attempts["count"] == 2

    def test_raises_last_exception_after_exhausting_retries(self):
        @retry_with_backoff(max_retries=2, backoff_factor=0.0)
        def _always_fails():
            raise ValueError("persistent failure")

        with pytest.raises(ValueError, match="persistent failure"):
            _always_fails()
