"""Tests for error_handling.py"""

from unittest.mock import patch

import pytest

from agent.error_handling import RetryContext, retry_with_backoff


@pytest.mark.unit
class TestRetryWithBackoff:
    """Test suite for the retry_with_backoff decorator."""

    def test_retry_with_backoff_always_succeeds_returns_value(self):
        """
        retry_with_backoff() should return the value immediately when no exception occurs.
        """
        @retry_with_backoff(max_retries=3)
        def always_ok():
            return 42

        result = always_ok()

        assert result == 42

    def test_retry_with_backoff_transient_failure_retries_and_succeeds(self):
        """
        retry_with_backoff() should retry the function and eventually succeed on transient failures.
        """
        call_count = {"n": 0}

        @retry_with_backoff(max_retries=3, backoff_factor=0)
        def flaky():
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise ValueError("not yet")
            return "ok"

        with patch("time.sleep"):
            result = flaky()

        assert result == "ok"
        assert call_count["n"] == 2

    def test_retry_with_backoff_exhausted_retries_raises_exception(self):
        """
        retry_with_backoff() should re-raise the original exception when all retries fail.
        """
        @retry_with_backoff(max_retries=2, backoff_factor=0)
        def always_fails():
            raise RuntimeError("always")

        with patch("time.sleep"), pytest.raises(RuntimeError, match="always"):
            always_fails()

    def test_retry_with_backoff_retry_attempt_logs_warning(self):
        """
        retry_with_backoff() should log a warning on each retry attempt.
        """
        call_count = {"n": 0}

        @retry_with_backoff(max_retries=3, backoff_factor=0)
        def sometimes_fails():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("try again")
            return "done"

        with patch("agent.error_handling.logger") as mock_logger, patch("time.sleep"):
            sometimes_fails()

        assert mock_logger.warning.called

    def test_retry_with_backoff_exhausted_retries_logs_error(self):
        """
        retry_with_backoff() should log an error when all retries are consumed.
        """
        @retry_with_backoff(max_retries=2, backoff_factor=0)
        def always_fails():
            raise RuntimeError("nope")

        with (
            patch("agent.error_handling.logger") as mock_logger,
            patch("time.sleep"),
            pytest.raises(RuntimeError),
        ):
            always_fails()

        assert mock_logger.error.called

    def test_retry_with_backoff_exhausted_retries_logs_with_exc_info(self):
        """
        retry_with_backoff() should include exc_info=True when logging retry exhaustion.

        This ensures the full traceback is captured for debugging (Issue #44).
        """
        @retry_with_backoff(max_retries=2, backoff_factor=0)
        def always_fails():
            raise RuntimeError("trace me")

        with (
            patch("agent.error_handling.logger") as mock_logger,
            patch("time.sleep"),
            pytest.raises(RuntimeError),
        ):
            always_fails()

        exhausted_calls = [
            c for c in mock_logger.error.call_args_list
            if c.args and c.args[0] == "retry_exhausted"
        ]
        assert exhausted_calls
        for c in exhausted_calls:
            assert c.kwargs.get("exc_info") is True

    def test_retry_with_backoff_unspecified_exception_not_retried(self):
        """
        retry_with_backoff() should not retry exceptions that are not in the exceptions tuple.
        """
        call_count = {"n": 0}

        @retry_with_backoff(max_retries=3, exceptions=(ValueError,), backoff_factor=0)
        def raises_type_error():
            call_count["n"] += 1
            raise TypeError("wrong type")

        with patch("time.sleep"), pytest.raises(TypeError):
            raises_type_error()

        assert call_count["n"] == 1

    def test_retry_with_backoff_between_attempts_calls_sleep(self):
        """
        retry_with_backoff() should call time.sleep between retry attempts.
        """
        @retry_with_backoff(max_retries=3, backoff_factor=2.0)
        def always_fails():
            raise RuntimeError("fail")

        with patch("time.sleep") as mock_sleep, pytest.raises(RuntimeError):
            always_fails()

        assert mock_sleep.call_count == 2

    def test_retry_with_backoff_wraps_preserves_function_name(self):
        """
        retry_with_backoff() should preserve the original function's name using functools.wraps.
        """
        @retry_with_backoff(max_retries=3)
        def my_special_function():
            return True

        assert my_special_function.__name__ == "my_special_function"

    def test_retry_with_backoff_max_retries_one_runs_once(self):
        """
        retry_with_backoff() with max_retries=1 should only execute the function once.
        """
        call_count = {"n": 0}

        @retry_with_backoff(max_retries=1, backoff_factor=0)
        def always_fails():
            call_count["n"] += 1
            raise RuntimeError("fail")

        with patch("time.sleep"), pytest.raises(RuntimeError):
            always_fails()

        assert call_count["n"] == 1

    def test_retry_with_backoff_arguments_are_passed_through(self):
        """
        retry_with_backoff() should correctly forward all positional and keyword arguments.
        """
        received = {}

        @retry_with_backoff(max_retries=2)
        def record(a, b, c=None):
            received.update({"a": a, "b": b, "c": c})
            return a + b

        result = record(1, 2, c=3)

        assert result == 3
        assert received == {"a": 1, "b": 2, "c": 3}


@pytest.mark.unit
class TestRetryContext:
    """Test suite for the RetryContext context manager."""

    def test_retrycontext_no_exception_exits_cleanly(self):
        """
        RetryContext should exit cleanly without modifying attempt count when no exception occurs.
        """
        with RetryContext(max_retries=3) as ctx:
            pass

        assert ctx.attempt == 0

    def test_retrycontext_retries_remaining_suppresses_exception(self):
        """
        RetryContext should suppress exceptions when retries remain, returning True.
        """
        ctx = RetryContext(max_retries=3, backoff_factor=0)

        with patch("time.sleep"):
            result = ctx.__exit__(ValueError, ValueError("x"), None)

        assert result is True

    def test_retrycontext_retries_exhausted_reraises_exception(self):
        """
        RetryContext should return False (re-raise) when max_retries is reached.
        """
        ctx = RetryContext(max_retries=1, backoff_factor=0)

        with patch("time.sleep"):
            ctx.__exit__(ValueError, ValueError("first"), None)
            result = ctx.__exit__(ValueError, ValueError("second"), None)

        assert result is False

    def test_retrycontext_retry_attempt_logs_warning(self):
        """
        RetryContext should log a warning when an exception is caught and suppressed.
        """
        ctx = RetryContext(max_retries=3, backoff_factor=0)

        with patch("agent.error_handling.logger") as mock_logger, patch("time.sleep"):
            ctx.__exit__(ValueError, ValueError("warn me"), None)

        assert mock_logger.warning.called

    def test_retrycontext_exhausted_retries_logs_error_with_exc_info(self):
        """
        RetryContext should log an error with exc_info=True when retries are exhausted.

        This prevents silent failures and helps debugging (Issue #44).
        """
        ctx = RetryContext(max_retries=1, backoff_factor=0)

        with patch("agent.error_handling.logger") as mock_logger, patch("time.sleep"):
            ctx.__exit__(RuntimeError, RuntimeError("exhausted"), None)

        exhausted_calls = [
            c for c in mock_logger.error.call_args_list
            if c.args and c.args[0] == "retry_context_exhausted"
        ]
        assert exhausted_calls
        for c in exhausted_calls:
            assert c.kwargs.get("exc_info") is True

    def test_retrycontext_unspecified_exception_returns_false(self):
        """
        RetryContext should not suppress exceptions that don't match the configured types.
        """
        ctx = RetryContext(max_retries=3, exceptions=(ValueError,))

        result = ctx.__exit__(TypeError, TypeError("nope"), None)

        assert result is False

    def test_retrycontext_no_exception_type_returns_false(self):
        """
        RetryContext __exit__ should return False when no exception occurred.
        """
        ctx = RetryContext(max_retries=3)

        result = ctx.__exit__(None, None, None)

        assert result is False

    def test_retrycontext_retry_attempt_calls_sleep(self):
        """
        RetryContext should call time.sleep when a retry is attempted.
        """
        ctx = RetryContext(max_retries=3, backoff_factor=2.0)

        with patch("time.sleep") as mock_sleep:
            ctx.__exit__(ValueError, ValueError("x"), None)

        mock_sleep.assert_called_once()

    def test_retrycontext_exception_stores_last_exception(self):
        """
        RetryContext should store the most recently caught exception in last_exception.
        """
        ctx = RetryContext(max_retries=3, backoff_factor=0)
        exc = ValueError("remember me")

        with patch("time.sleep"):
            ctx.__exit__(ValueError, exc, None)

        assert ctx.last_exception is exc

    def test_retrycontext_exception_increments_attempt(self):
        """
        RetryContext should increment its internal attempt counter upon each exception.
        """
        ctx = RetryContext(max_retries=3, backoff_factor=0)

        with patch("time.sleep"):
            ctx.__exit__(ValueError, ValueError("first"), None)

        assert ctx.attempt == 1
