"""
FastAPI application entry point.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import close_db
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
)
from app.core.middleware import LoggingMiddleware, TimingMiddleware
from app.core.health import check_all_components
from app.dependencies import get_session
from app.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    setup_logging()
    logger.info("Starting up SEC Filings Dashboard API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    yield
    # Shutdown
    logger.info("Shutting down SEC Filings Dashboard API...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG,
    description="SEC Filings Dashboard API - Monitor and analyze SEC filings in real-time",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(LoggingMiddleware)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns API information including version and environment.
    """
    return {
        "message": "SEC Filings Dashboard API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json",
    }


@app.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """
    Health check endpoint.

    Checks connectivity to all required services:
    - PostgreSQL database
    - Redis cache
    - Elasticsearch

    Returns overall health status and individual component statuses.
    """
    health_status = await check_all_components(session)
    return health_status


@app.get("/ready")
async def readiness_check(session: AsyncSession = Depends(get_session)):
    """
    Readiness probe endpoint.

    Checks if the application is ready to serve requests.
    Verifies database connectivity and essential services.

    Returns readiness status.
    """
    try:
        # Check database
        from sqlalchemy import text
        await session.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "message": "Application is ready to serve requests",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "status": "not_ready",
            "message": f"Application is not ready: {str(e)}",
        }


# Include API routers
from app.api.v1 import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)
