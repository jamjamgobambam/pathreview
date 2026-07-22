"""Project-wide Python initialization for logging compatibility."""

from __future__ import annotations

import logging
import os
import sys

import structlog


def _configure_structlog() -> None:
    """Configure structlog so it emits through the standard logging system."""
    if getattr(structlog, "_pathreview_configured", False):
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

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
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)
    structlog._pathreview_configured = True


_configure_structlog()
