"""Structured logging configuration."""
import logging
import sys
import json
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add location info
        if record.pathname:
            log_data["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class StructuredLogger(logging.Logger):
    """Logger with structured logging support."""

    def _log_with_extra(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info: Any = None,
        extra: dict | None = None,
        **kwargs
    ):
        if extra is None:
            extra = {}
        extra["extra_fields"] = kwargs
        super()._log(level, msg, args, exc_info=exc_info, extra=extra)

    def info(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.INFO, msg, args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.WARNING, msg, args, **kwargs)

    def error(self, msg: str, *args, exc_info: bool = False, **kwargs):
        self._log_with_extra(logging.ERROR, msg, args, exc_info=exc_info, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.DEBUG, msg, args, **kwargs)


def setup_logging(json_output: bool = True, level: str = "INFO"):
    """Configure application logging."""
    logging.setLoggerClass(StructuredLogger)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if json_output:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )

    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return logging.getLogger(name)
