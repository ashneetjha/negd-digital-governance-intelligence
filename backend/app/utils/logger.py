"""
Structured logger using structlog.
Production-safe configuration compatible with FastAPI & uvicorn.
"""

import logging
import sys
import structlog


def _configure_logging() -> None:
    # Configure stdlib logging first
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog to use stdlib logger
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),  # switch to JSONRenderer in prod if needed
        ],
        context_class=dict,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

_configure_logging()

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)