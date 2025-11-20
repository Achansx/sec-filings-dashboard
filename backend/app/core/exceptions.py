"""Custom exceptions and exception handlers for the application."""
from typing import Union, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

from app.utils.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base exception for application-specific errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Union[Dict[str, Any], None] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Union[Dict[str, Any], None] = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)


class BadRequestException(AppException):
    """Exception raised for bad requests."""

    def __init__(self, message: str = "Bad request", details: Union[Dict[str, Any], None] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class UnauthorizedException(AppException):
    """Exception raised for unauthorized access."""

    def __init__(self, message: str = "Unauthorized", details: Union[Dict[str, Any], None] = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


class ForbiddenException(AppException):
    """Exception raised for forbidden access."""

    def __init__(self, message: str = "Forbidden", details: Union[Dict[str, Any], None] = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, details)


class ConflictException(AppException):
    """Exception raised for resource conflicts."""

    def __init__(self, message: str = "Resource conflict", details: Union[Dict[str, Any], None] = None):
        super().__init__(message, status.HTTP_409_CONFLICT, details)


class ExternalServiceException(AppException):
    """Exception raised when external service (like SEC API) fails."""

    def __init__(self, message: str = "External service error", details: Union[Dict[str, Any], None] = None):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY, details)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handler for application-specific exceptions.

    Args:
        request: FastAPI request
        exc: Application exception

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "details": exc.details,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "path": request.url.path,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for request validation errors.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSON response with validation error details
    """
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "path": request.url.path,
        },
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler for database errors.

    Args:
        request: FastAPI request
        exc: SQLAlchemy error

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
        },
        exc_info=True,
    )

    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Database integrity error",
                "details": {"message": "Resource already exists or constraint violation"},
                "path": request.url.path,
            },
        )

    # Generic database error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error",
            "details": {"message": "An error occurred while processing your request"},
            "path": request.url.path,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for all unhandled exceptions.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": {"message": "An unexpected error occurred"},
            "path": request.url.path,
        },
    )
