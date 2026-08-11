"""Structured logging configuration using structlog."""

import logging
import sys

import structlog

from core.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure structlog to emit through the standard logging pipeline."""
    global _CONFIGURED

    if _CONFIGURED:
        return

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging so pytest caplog can capture structlog output.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level,
        force=True,
    )
    _CONFIGURED = True


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name, typically __name__ from the calling module

    Returns:
        Bound logger instance with context
    """
    configure_logging()
    return structlog.get_logger(name)


configure_logging()
