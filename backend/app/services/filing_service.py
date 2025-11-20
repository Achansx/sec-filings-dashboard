"""Service layer for filing operations."""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload

from app.models.filing import Filing, FilingDocument
from app.models.company import Company
from app.schemas.filing import FilingCreate, FilingUpdate, FilingDocumentCreate
from app.core.crud import CRUDBase
from app.core.exceptions import NotFoundException


class FilingService(CRUDBase[Filing, FilingCreate, FilingUpdate]):
    """Service for filing-related operations."""

    async def get_by_accession_number(
        self,
        session: AsyncSession,
        accession_number: str,
    ) -> Optional[Filing]:
        """
        Get filing by accession number.

        Args:
            session: Database session
            accession_number: SEC accession number

        Returns:
            Filing instance or None
        """
        return await self.get_by_field(session, "accession_number", accession_number)

    async def get_with_company(
        self,
        session: AsyncSession,
        filing_id: int,
    ) -> Optional[Filing]:
        """
        Get filing with company information.

        Args:
            session: Database session
            filing_id: Filing ID

        Returns:
            Filing instance with company loaded, or None
        """
        query = (
            select(Filing)
            .options(joinedload(Filing.company))
            .where(Filing.id == filing_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_documents(
        self,
        session: AsyncSession,
        filing_id: int,
    ) -> Optional[Filing]:
        """
        Get filing with all documents.

        Args:
            session: Database session
            filing_id: Filing ID

        Returns:
            Filing instance with documents loaded, or None
        """
        query = (
            select(Filing)
            .options(joinedload(Filing.documents))
            .where(Filing.id == filing_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_company(
        self,
        session: AsyncSession,
        company_cik: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Filing]:
        """
        Get filings for a specific company.

        Args:
            session: Database session
            company_cik: Company CIK
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filings
        """
        query = (
            select(Filing)
            .where(Filing.company_cik == company_cik)
            .order_by(Filing.filing_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_form_type(
        self,
        session: AsyncSession,
        form_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Filing]:
        """
        Get filings by form type.

        Args:
            session: Database session
            form_type: Form type (e.g., '10-K', '10-Q')
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filings
        """
        query = (
            select(Filing)
            .where(Filing.form_type == form_type)
            .order_by(Filing.filing_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Filing]:
        """
        Get filings within a date range.

        Args:
            session: Database session
            start_date: Start date
            end_date: End date
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filings
        """
        query = (
            select(Filing)
            .where(and_(Filing.filing_date >= start_date, Filing.filing_date <= end_date))
            .order_by(Filing.filing_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_recent_filings(
        self,
        session: AsyncSession,
        days: int = 7,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Filing]:
        """
        Get recent filings from the last N days.

        Args:
            session: Database session
            days: Number of days to look back
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filings
        """
        from datetime import timedelta
        cutoff_date = date.today() - timedelta(days=days)

        query = (
            select(Filing)
            .where(Filing.filing_date >= cutoff_date)
            .order_by(Filing.filing_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_unindexed_filings(
        self,
        session: AsyncSession,
        limit: int = 100,
    ) -> List[Filing]:
        """
        Get filings that haven't been indexed yet.

        Args:
            session: Database session
            limit: Maximum number of records to return

        Returns:
            List of unindexed filings
        """
        query = (
            select(Filing)
            .where(Filing.indexed == False)
            .order_by(Filing.created_at)
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def mark_as_indexed(
        self,
        session: AsyncSession,
        filing_id: int,
    ) -> Optional[Filing]:
        """
        Mark a filing as indexed.

        Args:
            session: Database session
            filing_id: Filing ID

        Returns:
            Updated filing instance or None
        """
        filing = await self.get(session, filing_id)
        if filing:
            filing.indexed = True
            session.add(filing)
            await session.flush()
            await session.refresh(filing)
        return filing


class FilingDocumentService(CRUDBase[FilingDocument, FilingDocumentCreate, dict]):
    """Service for filing document operations."""

    async def get_by_filing(
        self,
        session: AsyncSession,
        filing_id: int,
    ) -> List[FilingDocument]:
        """
        Get all documents for a filing.

        Args:
            session: Database session
            filing_id: Filing ID

        Returns:
            List of filing documents
        """
        query = (
            select(FilingDocument)
            .where(FilingDocument.filing_id == filing_id)
            .order_by(FilingDocument.sequence)
        )
        result = await session.execute(query)
        return list(result.scalars().all())


# Create service instances
filing_service = FilingService(Filing)
filing_document_service = FilingDocumentService(FilingDocument)
