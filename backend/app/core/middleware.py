"""Middleware for FastAPI application."""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.logging import (
    get_logger,
    set_correlation_id,
    get_correlation_id,
    log_request,
    log_response,
)

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses with correlation ID tracking."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        # Set correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        correlation_id = set_correlation_id(correlation_id)

        # Log request
        log_request(
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id,
            query_params=str(request.query_params) if request.query_params else None,
            client_ip=request.client.host if request.client else None,
        )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Log response
        log_response(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
        )

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware for adding timing information to responses."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add timing information to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response with timing header
        """
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        return response
