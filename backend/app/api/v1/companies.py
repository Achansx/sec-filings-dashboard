"""API routes for company operations."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.company import (
    Company,
    CompanyCreate,
    CompanyUpdate,
    CompanyWithFilingsCount,
)
from app.services.company_service import company_service
from app.core.exceptions import NotFoundException
from app.utils.pagination import PaginationParams, paginate_query, create_pagination_response

router = APIRouter()


@router.get("", response_model=List[Company])
async def list_companies(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get list of companies with pagination.

    Args:
        skip: Number of companies to skip
        limit: Maximum number of companies to return
        session: Database session

    Returns:
        List of companies
    """
    companies = await company_service.get_multi(
        session,
        skip=skip,
        limit=limit,
        order_by="name",
    )
    return companies


@router.get("/search", response_model=List[Company])
async def search_companies(
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db),
):
    """
    Search companies by name.

    Args:
        q: Search term
        skip: Number of companies to skip
        limit: Maximum number of companies to return
        session: Database session

    Returns:
        List of matching companies
    """
    companies = await company_service.search_by_name(
        session,
        search_term=q,
        skip=skip,
        limit=limit,
    )
    return companies


@router.get("/{cik}", response_model=CompanyWithFilingsCount)
async def get_company(
    cik: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Get company by CIK.

    Args:
        cik: Central Index Key
        session: Database session

    Returns:
        Company with filings count

    Raises:
        HTTPException: If company not found
    """
    result = await company_service.get_company_with_filings_count(session, cik)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with CIK {cik} not found",
        )

    company = result["company"]
    return CompanyWithFilingsCount(
        **company.__dict__,
        filings_count=result["filings_count"],
    )


@router.post("", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_in: CompanyCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Create a new company.

    Args:
        company_in: Company creation data
        session: Database session

    Returns:
        Created company

    Raises:
        HTTPException: If company with CIK already exists
    """
    # Check if company already exists
    existing = await company_service.get_by_cik(session, company_in.cik)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Company with CIK {company_in.cik} already exists",
        )

    # Create company
    company = await company_service.create(session, company_in)
    await session.commit()
    return company


@router.patch("/{cik}", response_model=Company)
async def update_company(
    cik: str,
    company_in: CompanyUpdate,
    session: AsyncSession = Depends(get_db),
):
    """
    Update a company.

    Args:
        cik: Central Index Key
        company_in: Company update data
        session: Database session

    Returns:
        Updated company

    Raises:
        HTTPException: If company not found
    """
    company = await company_service.get_by_cik(session, cik)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with CIK {cik} not found",
        )

    company = await company_service.update(session, company, company_in)
    await session.commit()
    return company


@router.delete("/{cik}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    cik: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Delete a company.

    Args:
        cik: Central Index Key
        session: Database session

    Raises:
        HTTPException: If company not found
    """
    company = await company_service.get_by_cik(session, cik)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with CIK {cik} not found",
        )

    await session.delete(company)
    await session.commit()
