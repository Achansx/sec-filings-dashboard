"""Service layer for company operations."""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.company import Company
from app.models.filing import Filing
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.core.crud import CRUDBase
from app.core.exceptions import NotFoundException, ConflictException


class CompanyService(CRUDBase[Company, CompanyCreate, CompanyUpdate]):
    """Service for company-related operations."""

    async def get_by_cik(self, session: AsyncSession, cik: str) -> Optional[Company]:
        """
        Get company by CIK.

        Args:
            session: Database session
            cik: Central Index Key

        Returns:
            Company instance or None
        """
        return await self.get_by_field(session, "cik", cik)

    async def get_by_ticker(self, session: AsyncSession, ticker: str) -> Optional[Company]:
        """
        Get company by ticker symbol.

        Args:
            session: Database session
            ticker: Stock ticker symbol

        Returns:
            Company instance or None
        """
        return await self.get_by_field(session, "ticker", ticker)

    async def get_or_create(
        self,
        session: AsyncSession,
        cik: str,
        obj_in: CompanyCreate,
    ) -> Tuple[Company, bool]:
        """
        Get existing company or create new one.

        Args:
            session: Database session
            cik: Central Index Key
            obj_in: Company creation data

        Returns:
            Tuple of (Company instance, created flag)
        """
        # Try to get existing company
        company = await self.get_by_cik(session, cik)
        if company:
            return company, False

        # Create new company
        company = await self.create(session, obj_in)
        return company, True

    async def search_by_name(
        self,
        session: AsyncSession,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Company]:
        """
        Search companies by name.

        Args:
            session: Database session
            search_term: Search term for company name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching companies
        """
        query = (
            select(Company)
            .where(Company.name.ilike(f"%{search_term}%"))
            .offset(skip)
            .limit(limit)
            .order_by(Company.name)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_companies_by_industry(
        self,
        session: AsyncSession,
        sic_code: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Company]:
        """
        Get companies by SIC code.

        Args:
            session: Database session
            sic_code: Standard Industrial Classification code
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of companies
        """
        query = (
            select(Company)
            .where(Company.sic_code == sic_code)
            .offset(skip)
            .limit(limit)
            .order_by(Company.name)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_company_with_filings_count(
        self,
        session: AsyncSession,
        cik: str,
    ) -> Optional[dict]:
        """
        Get company with total filings count.

        Args:
            session: Database session
            cik: Central Index Key

        Returns:
            Dict with company data and filings count, or None
        """
        # Get company
        company = await self.get_by_cik(session, cik)
        if not company:
            return None

        # Get filings count
        count_query = select(func.count()).where(Filing.company_cik == cik)
        result = await session.execute(count_query)
        filings_count = result.scalar_one()

        return {
            "company": company,
            "filings_count": filings_count,
        }


# Create service instance
company_service = CompanyService(Company)
