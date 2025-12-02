"""
Structured logging configuration for the ArcGIS client application.

Provides JSON-formatted logging with context support for production deployments,
with fallback to human-readable format for development.
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from src.config import get_config


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "context"):
            log_data["context"] = record.context

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        return json.dumps(log_data)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual information to log records."""

    def process(self, msg: str, kwargs: Any) -> tuple:
        """
        Process log message and add context.

        Args:
            msg: Log message.
            kwargs: Additional keyword arguments.

        Returns:
            Tuple of (message, kwargs) with context added.
        """
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging() -> None:
    """
    Configure application logging based on settings.

    Sets up formatters, handlers, and log levels according to the
    application configuration.
    """
    config = get_config()
    log_config = config.logging

    log_level = getattr(logging, log_config.level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    root_logger.handlers.clear()

    if log_config.format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_config.file_path:
        file_path = Path(log_config.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(file_path),
            maxBytes=log_config.max_bytes,
            backupCount=log_config.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str, **context: Any) -> ContextAdapter:
    """
    Get a logger with optional context.

    Args:
        name: Logger name (typically __name__).
        **context: Additional context to include in all log messages.

    Returns:
        ContextAdapter: Logger adapter with context support.
    """
    logger = logging.getLogger(name)
    return ContextAdapter(logger, context)


class LogContext:
    """Context manager for adding temporary context to log messages."""

    def __init__(self, logger: ContextAdapter, **context: Any):
        """
        Initialize log context.

        Args:
            logger: The logger adapter to use.
            **context: Context key-value pairs to add.
        """
        self.logger = logger
        self.context = context
        self.original_extra = {}

    def __enter__(self) -> ContextAdapter:
        """Enter context and add context to logger."""
        self.original_extra = self.logger.extra.copy()
        self.logger.extra.update(self.context)
        return self.logger

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and restore original logger state."""
        self.logger.extra = self.original_extra


def log_execution_time(logger: logging.Logger, operation: str):
    """
    Decorator to log function execution time.

    Args:
        logger: Logger instance to use.
        operation: Description of the operation being timed.

    Returns:
        Decorated function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"{operation} completed",
                    extra={"duration_ms": duration_ms, "operation": operation}
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{operation} failed",
                    extra={
                        "duration_ms": duration_ms,
                        "operation": operation,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


setup_logging()
