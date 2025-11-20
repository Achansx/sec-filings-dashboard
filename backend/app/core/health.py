"""Health check utilities for monitoring system components."""
from typing import Dict, Any
import redis.asyncio as aioredis
from elasticsearch import AsyncElasticsearch
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def check_database(session: AsyncSession) -> Dict[str, Any]:
    """
    Check database connectivity.

    Args:
        session: Database session

    Returns:
        Dict with status and details
    """
    try:
        # Execute simple query
        result = await session.execute(text("SELECT 1"))
        result.scalar_one()
        return {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }


async def check_redis() -> Dict[str, Any]:
    """
    Check Redis connectivity.

    Returns:
        Dict with status and details
    """
    try:
        # Create Redis client
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

        # Ping Redis
        await redis_client.ping()
        await redis_client.close()

        return {
            "status": "healthy",
            "message": "Redis connection successful",
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
        }


async def check_elasticsearch() -> Dict[str, Any]:
    """
    Check Elasticsearch connectivity.

    Returns:
        Dict with status and details
    """
    try:
        # Create Elasticsearch client
        es_client = AsyncElasticsearch([settings.ELASTICSEARCH_URL])

        # Check cluster health
        health = await es_client.cluster.health()
        await es_client.close()

        return {
            "status": "healthy" if health["status"] in ["yellow", "green"] else "unhealthy",
            "message": "Elasticsearch connection successful",
            "cluster_status": health["status"],
        }
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Elasticsearch connection failed: {str(e)}",
        }


async def check_all_components(session: AsyncSession) -> Dict[str, Any]:
    """
    Check all system components.

    Args:
        session: Database session

    Returns:
        Dict with overall status and component details
    """
    # Check all components
    db_health = await check_database(session)
    redis_health = await check_redis()
    es_health = await check_elasticsearch()

    # Determine overall status
    all_healthy = all([
        db_health["status"] == "healthy",
        redis_health["status"] == "healthy",
        es_health["status"] == "healthy",
    ])

    return {
        "status": "healthy" if all_healthy else "degraded",
        "components": {
            "database": db_health,
            "redis": redis_health,
            "elasticsearch": es_health,
        },
    }
