"""Structlog configuration for the PM agent.

Configures structlog with shared processors and stdlib integration so that
both our code (via structlog.get_logger) and third-party libraries (via
stdlib logging, including ADK/google-genai) produce consistent structured
output.

Call configure_logging() once at startup (in settings.py) before any
loggers are used.

Dev mode  -> pretty console output with colors
Prod mode -> JSON lines, one event per line, machine-parseable
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(*, json_logs: bool = True, log_level: str = "INFO") -> None:
    """Set up structlog + stdlib logging for the entire process.

    Args:
        json_logs: JSON output (True) or pretty console output (False).
        log_level: Root log level name (e.g. "INFO", "DEBUG").
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Shared processors run on every log event regardless of output format.
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # JSON mode: structlog renders the final JSON line.
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Console mode: colorized, human-friendly output.
        renderer = structlog.dev.ConsoleRenderer()

    # Configure structlog itself (for structlog.get_logger() calls).
    structlog.configure(
        processors=[
            *shared_processors,
            # Prepare the event dict for stdlib's ProcessorFormatter if the
            # event originated from structlog, otherwise format it directly.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging so that third-party libraries (ADK, google-genai,
    # httpx, etc.) also go through structlog's processors.
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet down noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "urllib3", "google.auth", "grpc"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
