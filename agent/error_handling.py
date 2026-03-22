"""Retry logic with exponential backoff."""

import time
import functools
import structlog

logger = structlog.get_logger()


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0,
                       exceptions: tuple = (Exception,)):
    """Decorator for retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None

            while attempt < max_retries:
                try:
                    result = func(*args, **kwargs)
                    return result

                except exceptions as e:
                    last_exception = e
                    attempt += 1

                    if attempt < max_retries:
                        wait_time = backoff_factor ** (attempt - 1)
                        logger.warning("retry_attempt", func=func.__name__,
                                     attempt=attempt, max_retries=max_retries,
                                     wait_seconds=wait_time, error=str(e))
                        time.sleep(wait_time)
                    else:
                        logger.error("retry_exhausted", func=func.__name__,
                                   max_retries=max_retries, error=str(e))

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class RetryContext:
    """Context manager for retry logic with exponential backoff."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0,
                 exceptions: tuple = (Exception,)):
        """Initialize retry context.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
            exceptions: Tuple of exceptions to catch and retry
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
        self.attempt = 0
        self.last_exception = None

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and handle retries."""
        if exc_type is None:
            return False

        if not issubclass(exc_type, self.exceptions):
            return False

        self.attempt += 1
        self.last_exception = exc_val

        if self.attempt < self.max_retries:
            wait_time = self.backoff_factor ** (self.attempt - 1)
            logger.warning("retry_context_attempt", attempt=self.attempt,
                         max_retries=self.max_retries, wait_seconds=wait_time,
                         error=str(exc_val))
            time.sleep(wait_time)
            return True  # Suppress exception and retry

        logger.error("retry_context_exhausted", attempt=self.attempt,
                   max_retries=self.max_retries, error=str(exc_val))
        return False  # Re-raise exception
