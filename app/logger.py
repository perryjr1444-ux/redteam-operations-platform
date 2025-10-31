"""Structured logging configuration."""

import logging
import sys
from typing import Any
import json
from datetime import datetime

from .config import settings


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    """Configure application logging."""

    logger = logging.getLogger("redteam_app")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Global logger instance
logger = setup_logging()


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    if name:
        return logging.getLogger(f"redteam_app.{name}")
    return logger
