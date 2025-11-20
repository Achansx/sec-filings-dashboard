"""
SEC API client service using EdgarTools.

This module provides a wrapper around the edgartools library with:
- Rate limiting integration
- Error handling and retries
- Structured logging
- Company and filing retrieval
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from functools import wraps

from edgar import Company, Filing, set_identity
from edgar.company_reports import TenK, TenQ, EightK
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.core.exceptions import (
    NotFoundException,
    ExternalServiceException,
)

logger = logging.getLogger(__name__)


# Initialize EdgarTools with user identity
set_identity(settings.SEC_API_USER_AGENT)


class SECClientException(ExternalServiceException):
    """Custom exception for SEC API client errors."""
    pass


class SECClient:
    """
    Client for interacting with SEC EDGAR API via EdgarTools.

    Provides methods for:
    - Company lookup (by CIK, ticker)
    - Filing retrieval
    - Document parsing
    - Error handling and resilience
    """

    def __init__(self):
        """Initialize SEC API client."""
        self.user_agent = settings.SEC_API_USER_AGENT
        logger.info(f"Initialized SEC API client with user agent: {self.user_agent}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def get_company_by_cik(self, cik: str) -> Dict[str, Any]:
        """
        Get company information by CIK.

        Args:
            cik: Central Index Key (with or without leading zeros)

        Returns:
            Dict containing company information

        Raises:
            NotFoundException: If company not found
            SECClientException: If SEC API error occurs
        """
        try:
            # Normalize CIK (remove leading zeros, then pad to 10 digits)
            normalized_cik = str(int(cik)).zfill(10)

            logger.info(f"Fetching company by CIK: {normalized_cik}")
            company = Company(normalized_cik)

            if not company:
                raise NotFoundException(f"Company with CIK {cik} not found")

            company_data = {
                "cik": normalized_cik,
                "name": company.name,
                "ticker": getattr(company, 'tickers', [None])[0] if hasattr(company, 'tickers') else None,
                "sic_code": company.sic,
                "sic_description": getattr(company, 'sic_description', None),
                "exchange": getattr(company, 'exchange', None),
                "website": getattr(company, 'website', None),
                "industry": getattr(company, 'category', None),
                "description": getattr(company, 'description', None),
                "fiscal_year_end": getattr(company, 'fiscal_year_end', None),
                "state_of_incorporation": getattr(company, 'state_of_incorporation', None),
                "ein": getattr(company, 'ein', None),
                "phone": getattr(company, 'phone', None),
                "address": self._format_address(company),
            }

            logger.info(f"Successfully fetched company: {company_data['name']}")
            return company_data

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching company by CIK {cik}: {str(e)}")
            raise SECClientException(f"Failed to fetch company: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def get_company_by_ticker(self, ticker: str) -> Dict[str, Any]:
        """
        Get company information by ticker symbol.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dict containing company information

        Raises:
            NotFoundException: If company not found
            SECClientException: If SEC API error occurs
        """
        try:
            logger.info(f"Fetching company by ticker: {ticker.upper()}")
            company = Company(ticker.upper())

            if not company:
                raise NotFoundException(f"Company with ticker {ticker} not found")

            # Reuse get_company_by_cik for consistent data structure
            return await self.get_company_by_cik(company.cik)

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching company by ticker {ticker}: {str(e)}")
            raise SECClientException(f"Failed to fetch company: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def get_filings(
        self,
        cik: str,
        form_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get filings for a company.

        Args:
            cik: Central Index Key
            form_type: Optional form type filter (e.g., '10-K', '10-Q', '8-K')
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of filings to return

        Returns:
            List of filing dictionaries

        Raises:
            NotFoundException: If company not found
            SECClientException: If SEC API error occurs
        """
        try:
            normalized_cik = str(int(cik)).zfill(10)
            logger.info(f"Fetching filings for CIK: {normalized_cik}, form_type: {form_type}")

            company = Company(normalized_cik)
            if not company:
                raise NotFoundException(f"Company with CIK {cik} not found")

            # Get filings from company
            filings = company.get_filings(form=form_type)

            # Apply date filtering if specified
            if start_date or end_date:
                filings = self._filter_filings_by_date(filings, start_date, end_date)

            # Limit results
            filings_list = list(filings)[:limit]

            # Convert to dict format
            result = []
            for filing in filings_list:
                filing_data = self._parse_filing_metadata(filing, normalized_cik)
                result.append(filing_data)

            logger.info(f"Successfully fetched {len(result)} filings for CIK {normalized_cik}")
            return result

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching filings for CIK {cik}: {str(e)}")
            raise SECClientException(f"Failed to fetch filings: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def get_filing_by_accession(
        self,
        accession_number: str,
    ) -> Dict[str, Any]:
        """
        Get a specific filing by accession number.

        Args:
            accession_number: SEC accession number (e.g., '0001193125-21-000000')

        Returns:
            Dict containing filing information and documents

        Raises:
            NotFoundException: If filing not found
            SECClientException: If SEC API error occurs
        """
        try:
            logger.info(f"Fetching filing by accession number: {accession_number}")

            # EdgarTools can fetch filing directly by accession number
            filing = Filing(accession_number)

            if not filing:
                raise NotFoundException(f"Filing with accession {accession_number} not found")

            # Get company info
            company = Company(filing.cik)

            filing_data = self._parse_filing_metadata(filing, filing.cik)
            filing_data['company_name'] = company.name if company else None

            # Get documents
            filing_data['documents'] = self._parse_filing_documents(filing)

            logger.info(f"Successfully fetched filing: {accession_number}")
            return filing_data

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching filing {accession_number}: {str(e)}")
            raise SECClientException(f"Failed to fetch filing: {str(e)}")

    async def parse_filing_content(
        self,
        filing: Filing,
        extract_text: bool = True,
        extract_html: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse filing content and extract relevant data.

        Args:
            filing: Filing object from EdgarTools
            extract_text: Whether to extract plain text
            extract_html: Whether to extract HTML content

        Returns:
            Dict containing parsed content
        """
        try:
            content = {}

            # Try to get structured content based on form type
            form_type = filing.form

            if form_type == '10-K':
                content['structured'] = self._parse_10k(filing)
            elif form_type == '10-Q':
                content['structured'] = self._parse_10q(filing)
            elif form_type == '8-K':
                content['structured'] = self._parse_8k(filing)

            # Extract text if requested
            if extract_text:
                content['text'] = filing.text() if hasattr(filing, 'text') else None

            # Extract HTML if requested
            if extract_html:
                content['html'] = filing.html() if hasattr(filing, 'html') else None

            return content

        except Exception as e:
            logger.error(f"Error parsing filing content: {str(e)}")
            return {"error": str(e)}

    def _parse_filing_metadata(self, filing: Filing, cik: str) -> Dict[str, Any]:
        """Extract metadata from filing object."""
        return {
            "accession_number": filing.accession_number,
            "company_cik": cik,
            "form_type": filing.form,
            "filing_date": filing.filing_date,
            "acceptance_datetime": getattr(filing, 'acceptance_datetime', None),
            "period_of_report": getattr(filing, 'period_of_report', None),
            "report_date": getattr(filing, 'report_date', None),
            "document_count": len(filing.documents) if hasattr(filing, 'documents') else 0,
            "size_bytes": getattr(filing, 'size', None),
            "filing_url": filing.url if hasattr(filing, 'url') else None,
        }

    def _parse_filing_documents(self, filing: Filing) -> List[Dict[str, Any]]:
        """Extract document information from filing."""
        documents = []

        if hasattr(filing, 'documents'):
            for doc in filing.documents:
                documents.append({
                    "sequence": getattr(doc, 'sequence', None),
                    "description": getattr(doc, 'description', None),
                    "document_type": getattr(doc, 'type', None),
                    "filename": getattr(doc, 'filename', None),
                    "url": getattr(doc, 'url', None),
                    "size_bytes": getattr(doc, 'size', None),
                })

        return documents

    def _parse_10k(self, filing: Filing) -> Dict[str, Any]:
        """Parse 10-K specific content."""
        try:
            report = TenK(filing)
            return {
                "business": getattr(report, 'item_1', None),
                "risk_factors": getattr(report, 'item_1a', None),
                "md_and_a": getattr(report, 'item_7', None),
                "financial_statements": getattr(report, 'item_8', None),
            }
        except Exception as e:
            logger.warning(f"Could not parse 10-K: {str(e)}")
            return {}

    def _parse_10q(self, filing: Filing) -> Dict[str, Any]:
        """Parse 10-Q specific content."""
        try:
            report = TenQ(filing)
            return {
                "financial_info": getattr(report, 'item_1', None),
                "md_and_a": getattr(report, 'item_2', None),
            }
        except Exception as e:
            logger.warning(f"Could not parse 10-Q: {str(e)}")
            return {}

    def _parse_8k(self, filing: Filing) -> Dict[str, Any]:
        """Parse 8-K specific content."""
        try:
            report = EightK(filing)
            return {
                "items": getattr(report, 'items', []),
            }
        except Exception as e:
            logger.warning(f"Could not parse 8-K: {str(e)}")
            return {}

    def _filter_filings_by_date(
        self,
        filings,
        start_date: Optional[date],
        end_date: Optional[date],
    ):
        """Filter filings by date range."""
        filtered = filings

        if start_date:
            filtered = [f for f in filtered if f.filing_date >= start_date]

        if end_date:
            filtered = [f for f in filtered if f.filing_date <= end_date]

        return filtered

    def _format_address(self, company: Company) -> Optional[Dict[str, str]]:
        """Format company address from company object."""
        try:
            if hasattr(company, 'addresses'):
                business_addr = company.addresses.business if hasattr(company.addresses, 'business') else None
                if business_addr:
                    return {
                        "street1": getattr(business_addr, 'street1', None),
                        "street2": getattr(business_addr, 'street2', None),
                        "city": getattr(business_addr, 'city', None),
                        "state": getattr(business_addr, 'state', None),
                        "zip_code": getattr(business_addr, 'zip', None),
                    }
        except Exception as e:
            logger.warning(f"Could not parse address: {str(e)}")

        return None


# Create singleton instance
sec_client = SECClient()
