"""Structured JSON logging utilities."""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import uuid

from app.core.config import settings

# Context variable for correlation ID tracking
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_ctx.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up JSON logging for production and human-readable logging for development.
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Use JSON formatter in production, simple formatter in development
    if settings.ENVIRONMENT == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID in context.

    Args:
        correlation_id: Correlation ID to set, or None to generate a new one

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_ctx.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID from context.

    Returns:
        Current correlation ID or None
    """
    return correlation_id_ctx.get()


def log_request(method: str, path: str, **kwargs: Any) -> None:
    """
    Log HTTP request.

    Args:
        method: HTTP method
        path: Request path
        **kwargs: Additional fields to log
    """
    logger = get_logger("api.request")
    logger.info(
        f"{method} {path}",
        extra={
            "type": "request",
            "method": method,
            "path": path,
            **kwargs,
        }
    )


def log_response(method: str, path: str, status_code: int, duration_ms: float, **kwargs: Any) -> None:
    """
    Log HTTP response.

    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional fields to log
    """
    logger = get_logger("api.response")
    logger.info(
        f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
        extra={
            "type": "response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **kwargs,
        }
    )
