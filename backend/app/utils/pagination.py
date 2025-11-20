"""Pagination utilities for API endpoints."""
from typing import Generic, TypeVar, List, Optional, Any, Dict
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql.selectable import Select

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""

    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of items to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""

    items: List[T] = Field(default_factory=list, description="List of items")
    total: int = Field(0, description="Total number of items")
    skip: int = Field(0, description="Number of items skipped")
    limit: int = Field(100, description="Number of items per page")
    has_more: bool = Field(False, description="Whether there are more items")


async def paginate_query(
    session: AsyncSession,
    query: Select,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[Any], int]:
    """
    Paginate a SQLAlchemy query.

    Args:
        session: Database session
        query: SQLAlchemy select query
        skip: Number of items to skip
        limit: Number of items to return

    Returns:
        Tuple of (items, total_count)
    """
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await session.execute(count_query)
    total = result.scalar_one()

    # Get paginated items
    paginated_query = query.offset(skip).limit(limit)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    return list(items), total


def create_pagination_response(
    items: List[T],
    total: int,
    skip: int,
    limit: int,
) -> PaginatedResponse[T]:
    """
    Create a paginated response.

    Args:
        items: List of items
        total: Total number of items
        skip: Number of items skipped
        limit: Number of items per page

    Returns:
        PaginatedResponse instance
    """
    has_more = (skip + len(items)) < total

    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )


def get_pagination_params(skip: int = 0, limit: int = 100) -> PaginationParams:
    """
    Get pagination parameters with validation.

    Args:
        skip: Number of items to skip
        limit: Number of items to return

    Returns:
        PaginationParams instance
    """
    return PaginationParams(skip=skip, limit=limit)
