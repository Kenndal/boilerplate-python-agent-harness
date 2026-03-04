import json
import logging
import os
import time
from datetime import datetime, timezone, UTC
from typing import Any


class ConsoleFormatter(logging.Formatter):
    """Plain-text formatter with dot-separated milliseconds and correlation ID.

    Output: 2023-03-08 15:48:21.450 - trace_id - logger_name - LEVEL - message
    """

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        ct = self.converter(record.created)
        t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        return f"{t}.{int(record.msecs):03d}"


class JsonFormatter(logging.Formatter):
    """Structured JSON formatter for file output."""

    def format(self, record: logging.LogRecord) -> str:
        dt = datetime.fromtimestamp(record.created, tz=UTC)
        timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{int(record.msecs):03d}Z"
        return json.dumps(
            {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "trace_id": getattr(record, "correlation_id", "-"),
            }
        )


def get_logging_config(log_file_path: str, log_level: str = "INFO") -> dict[str, Any]:
    log_dir = os.path.dirname(log_file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": "asgi_correlation_id.CorrelationIdFilter",
                "default_value": "-",
            }
        },
        "formatters": {
            "console": {
                "()": "src.config.logging_config.ConsoleFormatter",
                "fmt": "%(asctime)s - %(correlation_id)s - %(name)s - %(levelname)s - %(message)s",
            },
            "json": {
                "()": "src.config.logging_config.JsonFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "filters": ["correlation_id"],
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "json",
                "filters": ["correlation_id"],
                "filename": log_file_path,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn": {"handlers": [], "propagate": True},
            "uvicorn.access": {"handlers": [], "propagate": True},
            "uvicorn.error": {"handlers": [], "propagate": True},
            "alembic": {"handlers": [], "propagate": True},
        },
    }