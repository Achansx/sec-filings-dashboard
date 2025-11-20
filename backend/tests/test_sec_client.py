"""
Tests for SEC API client.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import date, datetime

from app.services.sec_client import (
    SECClient,
    SECClientException,
)
from app.core.exceptions import NotFoundException


@pytest.fixture
def sec_client():
    """Create a test SEC client instance."""
    return SECClient()


@pytest.fixture
def mock_company():
    """Create a mock Company object from EdgarTools."""
    company = MagicMock()
    company.cik = "0000320193"
    company.name = "Apple Inc."
    company.tickers = ["AAPL"]
    company.sic = "3571"
    company.sic_description = "Electronic Computers"
    company.exchange = "NASDAQ"
    company.website = "https://www.apple.com"
    company.category = "Technology"
    company.description = "Technology company"
    company.fiscal_year_end = "0930"
    company.state_of_incorporation = "CA"
    company.ein = "94-2404110"
    company.phone = "408-996-1010"

    # Mock address
    address = MagicMock()
    address.street1 = "One Apple Park Way"
    address.street2 = None
    address.city = "Cupertino"
    address.state = "CA"
    address.zip = "95014"

    addresses = MagicMock()
    addresses.business = address
    company.addresses = addresses

    return company


@pytest.fixture
def mock_filing():
    """Create a mock Filing object from EdgarTools."""
    filing = MagicMock()
    filing.accession_number = "0000320193-23-000001"
    filing.cik = "0000320193"
    filing.form = "10-K"
    filing.filing_date = date(2023, 11, 3)
    filing.acceptance_datetime = datetime(2023, 11, 3, 16, 30, 0)
    filing.period_of_report = date(2023, 9, 30)
    filing.report_date = date(2023, 9, 30)
    filing.size = 1024000
    filing.url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000001/aapl-20230930.htm"

    # Mock documents
    doc = MagicMock()
    doc.sequence = 1
    doc.description = "10-K"
    doc.type = "10-K"
    doc.filename = "aapl-20230930.htm"
    doc.url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000001/aapl-20230930.htm"
    doc.size = 1024000

    filing.documents = [doc]

    return filing


class TestSECClient:
    """Test suite for SEC API client."""

    def test_initialization(self, sec_client):
        """Test SEC client initialization."""
        assert sec_client.user_agent is not None
        assert isinstance(sec_client, SECClient)

    @pytest.mark.asyncio
    async def test_get_company_by_cik_success(self, sec_client, mock_company):
        """Test successful company retrieval by CIK."""
        with patch('app.services.sec_client.Company', return_value=mock_company):
            result = await sec_client.get_company_by_cik("320193")

            assert result['cik'] == "0000320193"
            assert result['name'] == "Apple Inc."
            assert result['ticker'] == "AAPL"
            assert result['sic_code'] == "3571"
            assert result['address']['city'] == "Cupertino"

    @pytest.mark.asyncio
    async def test_get_company_by_cik_normalization(self, sec_client, mock_company):
        """Test CIK normalization (padding with zeros)."""
        with patch('app.services.sec_client.Company', return_value=mock_company):
            # Test with short CIK
            result = await sec_client.get_company_by_cik("320193")
            assert result['cik'] == "0000320193"

            # Test with already padded CIK
            result = await sec_client.get_company_by_cik("0000320193")
            assert result['cik'] == "0000320193"

    @pytest.mark.asyncio
    async def test_get_company_by_cik_not_found(self, sec_client):
        """Test company not found error."""
        with patch('app.services.sec_client.Company', return_value=None):
            with pytest.raises(NotFoundException) as exc_info:
                await sec_client.get_company_by_cik("9999999999")

            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_company_by_cik_api_error(self, sec_client):
        """Test handling of SEC API errors."""
        with patch('app.services.sec_client.Company', side_effect=Exception("API Error")):
            with pytest.raises(SECClientException) as exc_info:
                await sec_client.get_company_by_cik("320193")

            assert "Failed to fetch company" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_company_by_ticker_success(self, sec_client, mock_company):
        """Test successful company retrieval by ticker."""
        with patch('app.services.sec_client.Company', return_value=mock_company):
            result = await sec_client.get_company_by_ticker("AAPL")

            assert result['name'] == "Apple Inc."
            assert result['ticker'] == "AAPL"

    @pytest.mark.asyncio
    async def test_get_company_by_ticker_case_insensitive(self, sec_client, mock_company):
        """Test that ticker lookup is case insensitive."""
        with patch('app.services.sec_client.Company', return_value=mock_company) as mock_constructor:
            await sec_client.get_company_by_ticker("aapl")

            # Should convert to uppercase
            mock_constructor.assert_called_with("AAPL")

    @pytest.mark.asyncio
    async def test_get_filings_success(self, sec_client, mock_company, mock_filing):
        """Test successful filing retrieval."""
        mock_company.get_filings.return_value = [mock_filing]

        with patch('app.services.sec_client.Company', return_value=mock_company):
            result = await sec_client.get_filings(
                cik="320193",
                form_type="10-K",
                limit=10
            )

            assert len(result) == 1
            assert result[0]['accession_number'] == "0000320193-23-000001"
            assert result[0]['form_type'] == "10-K"
            assert result[0]['company_cik'] == "0000320193"

    @pytest.mark.asyncio
    async def test_get_filings_with_date_filter(self, sec_client, mock_company, mock_filing):
        """Test filing retrieval with date filtering."""
        mock_company.get_filings.return_value = [mock_filing]

        with patch('app.services.sec_client.Company', return_value=mock_company):
            result = await sec_client.get_filings(
                cik="320193",
                form_type="10-K",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31),
                limit=10
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_filings_limit(self, sec_client, mock_company, mock_filing):
        """Test that filing limit is respected."""
        # Create multiple mock filings
        filings = [mock_filing] * 100

        mock_company.get_filings.return_value = filings

        with patch('app.services.sec_client.Company', return_value=mock_company):
            result = await sec_client.get_filings(
                cik="320193",
                limit=10
            )

            assert len(result) == 10

    @pytest.mark.asyncio
    async def test_get_filings_company_not_found(self, sec_client):
        """Test filings retrieval when company not found."""
        with patch('app.services.sec_client.Company', return_value=None):
            with pytest.raises(NotFoundException):
                await sec_client.get_filings(cik="9999999999")

    @pytest.mark.asyncio
    async def test_get_filing_by_accession_success(self, sec_client, mock_filing, mock_company):
        """Test successful retrieval of filing by accession number."""
        with patch('app.services.sec_client.Filing', return_value=mock_filing):
            with patch('app.services.sec_client.Company', return_value=mock_company):
                result = await sec_client.get_filing_by_accession(
                    "0000320193-23-000001"
                )

                assert result['accession_number'] == "0000320193-23-000001"
                assert result['company_name'] == "Apple Inc."
                assert 'documents' in result
                assert len(result['documents']) == 1

    @pytest.mark.asyncio
    async def test_get_filing_by_accession_not_found(self, sec_client):
        """Test filing by accession number not found."""
        with patch('app.services.sec_client.Filing', return_value=None):
            with pytest.raises(NotFoundException):
                await sec_client.get_filing_by_accession("0000000000-00-000000")

    @pytest.mark.asyncio
    async def test_parse_filing_content_10k(self, sec_client, mock_filing):
        """Test parsing 10-K filing content."""
        mock_filing.form = "10-K"
        mock_filing.text.return_value = "Filing text content"
        mock_filing.html.return_value = "<html>Filing HTML</html>"

        # Mock TenK
        mock_report = MagicMock()
        mock_report.item_1 = "Business section"
        mock_report.item_1a = "Risk factors"
        mock_report.item_7 = "MD&A"
        mock_report.item_8 = "Financial statements"

        with patch('app.services.sec_client.TenK', return_value=mock_report):
            result = await sec_client.parse_filing_content(
                mock_filing,
                extract_text=True,
                extract_html=True
            )

            assert 'structured' in result
            assert result['structured']['business'] == "Business section"
            assert result['text'] == "Filing text content"
            assert result['html'] == "<html>Filing HTML</html>"

    @pytest.mark.asyncio
    async def test_parse_filing_content_10q(self, sec_client, mock_filing):
        """Test parsing 10-Q filing content."""
        mock_filing.form = "10-Q"

        mock_report = MagicMock()
        mock_report.item_1 = "Financial info"
        mock_report.item_2 = "MD&A"

        with patch('app.services.sec_client.TenQ', return_value=mock_report):
            result = await sec_client.parse_filing_content(
                mock_filing,
                extract_text=False,
                extract_html=False
            )

            assert 'structured' in result
            assert result['structured']['financial_info'] == "Financial info"
            assert 'text' not in result
            assert 'html' not in result

    @pytest.mark.asyncio
    async def test_parse_filing_content_8k(self, sec_client, mock_filing):
        """Test parsing 8-K filing content."""
        mock_filing.form = "8-K"

        mock_report = MagicMock()
        mock_report.items = ["Item 1.01", "Item 2.02"]

        with patch('app.services.sec_client.EightK', return_value=mock_report):
            result = await sec_client.parse_filing_content(mock_filing)

            assert 'structured' in result
            assert result['structured']['items'] == ["Item 1.01", "Item 2.02"]

    @pytest.mark.asyncio
    async def test_parse_filing_content_error_handling(self, sec_client, mock_filing):
        """Test error handling in filing content parsing."""
        mock_filing.form = "10-K"

        with patch('app.services.sec_client.TenK', side_effect=Exception("Parse error")):
            result = await sec_client.parse_filing_content(mock_filing)

            # Should return empty structured content on error
            assert result.get('structured', {}) == {}

    def test_parse_filing_metadata(self, sec_client, mock_filing):
        """Test parsing filing metadata."""
        result = sec_client._parse_filing_metadata(mock_filing, "0000320193")

        assert result['accession_number'] == "0000320193-23-000001"
        assert result['company_cik'] == "0000320193"
        assert result['form_type'] == "10-K"
        assert result['filing_date'] == date(2023, 11, 3)
        assert result['document_count'] == 1

    def test_parse_filing_documents(self, sec_client, mock_filing):
        """Test parsing filing documents."""
        result = sec_client._parse_filing_documents(mock_filing)

        assert len(result) == 1
        assert result[0]['sequence'] == 1
        assert result[0]['description'] == "10-K"
        assert result[0]['filename'] == "aapl-20230930.htm"

    def test_filter_filings_by_date(self, sec_client, mock_filing):
        """Test date filtering of filings."""
        filings = [mock_filing]

        # Test with date in range
        result = sec_client._filter_filings_by_date(
            filings,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        assert len(result) == 1

        # Test with date out of range
        result = sec_client._filter_filings_by_date(
            filings,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        assert len(result) == 0

    def test_format_address(self, sec_client, mock_company):
        """Test address formatting."""
        result = sec_client._format_address(mock_company)

        assert result is not None
        assert result['street1'] == "One Apple Park Way"
        assert result['city'] == "Cupertino"
        assert result['state'] == "CA"
        assert result['zip_code'] == "95014"

    def test_format_address_no_address(self, sec_client):
        """Test address formatting when no address available."""
        mock_company = MagicMock()
        mock_company.addresses = None

        result = sec_client._format_address(mock_company)
        assert result is None

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self, sec_client, mock_company):
        """Test that client retries on connection errors."""
        with patch('app.services.sec_client.Company') as mock_constructor:
            # Fail twice, then succeed
            mock_constructor.side_effect = [
                ConnectionError("Connection failed"),
                ConnectionError("Connection failed"),
                mock_company
            ]

            result = await sec_client.get_company_by_cik("320193")

            # Should succeed after retries
            assert result['name'] == "Apple Inc."
            assert mock_constructor.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, sec_client):
        """Test behavior when all retries are exhausted."""
        with patch('app.services.sec_client.Company') as mock_constructor:
            # Fail all retries
            mock_constructor.side_effect = ConnectionError("Connection failed")

            with pytest.raises(ConnectionError):
                await sec_client.get_company_by_cik("320193")

            # Should retry 3 times
            assert mock_constructor.call_count == 3
