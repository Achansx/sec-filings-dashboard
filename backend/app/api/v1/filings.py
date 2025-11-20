"""API routes for filing operations."""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.filing import (
    Filing,
    FilingCreate,
    FilingUpdate,
    FilingWithCompany,
    FilingDetail,
)
from app.services.filing_service import filing_service
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.get("", response_model=List[Filing])
async def list_filings(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    company_cik: Optional[str] = Query(None, description="Filter by company CIK"),
    form_type: Optional[str] = Query(None, description="Filter by form type"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get list of filings with optional filters.

    Args:
        skip: Number of filings to skip
        limit: Maximum number of filings to return
        company_cik: Filter by company CIK
        form_type: Filter by form type (e.g., '10-K', '10-Q')
        start_date: Filter by filing date (start)
        end_date: Filter by filing date (end)
        session: Database session

    Returns:
        List of filings
    """
    # Apply filters
    if company_cik:
        filings = await filing_service.get_by_company(
            session,
            company_cik=company_cik,
            skip=skip,
            limit=limit,
        )
    elif form_type:
        filings = await filing_service.get_by_form_type(
            session,
            form_type=form_type,
            skip=skip,
            limit=limit,
        )
    elif start_date and end_date:
        filings = await filing_service.get_by_date_range(
            session,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
    else:
        filings = await filing_service.get_multi(
            session,
            skip=skip,
            limit=limit,
            order_by="-filing_date",
        )

    return filings


@router.get("/recent", response_model=List[Filing])
async def get_recent_filings(
    days: int = Query(7, ge=1, le=settings.MAX_RECENT_FILINGS_DAYS, description="Number of days to look back"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db),
):
    """
    Get recent filings from the last N days.

    Args:
        days: Number of days to look back (max: configurable via MAX_RECENT_FILINGS_DAYS)
        skip: Number of filings to skip
        limit: Maximum number of filings to return
        session: Database session

    Returns:
        List of recent filings
    """
    filings = await filing_service.get_recent_filings(
        session,
        days=days,
        skip=skip,
        limit=limit,
    )
    return filings


@router.get("/{filing_id}", response_model=FilingDetail)
async def get_filing(
    filing_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Get filing by ID with company information and documents.

    Args:
        filing_id: Filing ID
        session: Database session

    Returns:
        Filing with details

    Raises:
        HTTPException: If filing not found
    """
    # Get filing with company and documents
    filing = await filing_service.get_with_company(session, filing_id)
    if not filing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filing with ID {filing_id} not found",
        )

    # Get documents
    from app.services.filing_service import filing_document_service
    documents = await filing_document_service.get_by_filing(session, filing_id)

    # Build response
    return FilingDetail(
        **filing.__dict__,
        company_name=filing.company.name if filing.company else None,
        company_ticker=filing.company.ticker if filing.company else None,
        documents=documents,
    )


@router.post("", response_model=Filing, status_code=status.HTTP_201_CREATED)
async def create_filing(
    filing_in: FilingCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Create a new filing.

    Args:
        filing_in: Filing creation data
        session: Database session

    Returns:
        Created filing

    Raises:
        HTTPException: If filing with accession number already exists
    """
    # Check if filing already exists
    existing = await filing_service.get_by_accession_number(
        session,
        filing_in.accession_number,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Filing with accession number {filing_in.accession_number} already exists",
        )

    # Create filing
    filing = await filing_service.create(session, filing_in)
    await session.commit()
    return filing


@router.patch("/{filing_id}", response_model=Filing)
async def update_filing(
    filing_id: int,
    filing_in: FilingUpdate,
    session: AsyncSession = Depends(get_db),
):
    """
    Update a filing.

    Args:
        filing_id: Filing ID
        filing_in: Filing update data
        session: Database session

    Returns:
        Updated filing

    Raises:
        HTTPException: If filing not found
    """
    filing = await filing_service.get(session, filing_id)
    if not filing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filing with ID {filing_id} not found",
        )

    filing = await filing_service.update(session, filing, filing_in)
    await session.commit()
    return filing


@router.delete("/{filing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filing(
    filing_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Delete a filing.

    Args:
        filing_id: Filing ID
        session: Database session

    Raises:
        HTTPException: If filing not found
    """
    filing = await filing_service.get(session, filing_id)
    if not filing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filing with ID {filing_id} not found",
        )

    await session.delete(filing)
    await session.commit()
