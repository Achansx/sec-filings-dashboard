"""
Tests for database models.
"""
import pytest
from datetime import date, datetime
from sqlalchemy import select

from app.models import Company, Filing, FilingDocument, User, UserAlert, AlertMatch, AuditLog


@pytest.mark.asyncio
async def test_create_company(db_session):
    """Test creating a company."""
    company = Company(
        cik="0000320193",
        name="Apple Inc.",
        ticker="AAPL",
        sic_code="3571",
        industry_description="Electronic Computers"
    )
    db_session.add(company)
    await db_session.commit()

    # Query company
    result = await db_session.execute(select(Company).where(Company.cik == "0000320193"))
    saved_company = result.scalar_one()

    assert saved_company.name == "Apple Inc."
    assert saved_company.ticker == "AAPL"
    assert saved_company.created_at is not None


@pytest.mark.asyncio
async def test_create_filing(db_session):
    """Test creating a filing with company relationship."""
    # Create company first
    company = Company(
        cik="0000789019",
        name="Microsoft Corporation",
        ticker="MSFT"
    )
    db_session.add(company)
    await db_session.commit()

    # Create filing
    filing = Filing(
        accession_number="0000789019-23-000001",
        company_cik="0000789019",
        form_type="10-K",
        filing_date=date(2023, 7, 27),
        period_of_report=date(2023, 6, 30),
        indexed=False
    )
    db_session.add(filing)
    await db_session.commit()

    # Query filing
    result = await db_session.execute(
        select(Filing).where(Filing.accession_number == "0000789019-23-000001")
    )
    saved_filing = result.scalar_one()

    assert saved_filing.form_type == "10-K"
    assert saved_filing.company_cik == "0000789019"
    assert saved_filing.indexed is False


@pytest.mark.asyncio
async def test_filing_cascade_delete(db_session):
    """Test that deleting a company cascades to filings."""
    # Create company with filing
    company = Company(cik="0000012345", name="Test Corp", ticker="TEST")
    db_session.add(company)
    await db_session.commit()

    filing = Filing(
        accession_number="0000012345-23-000001",
        company_cik="0000012345",
        form_type="10-Q",
        filing_date=date(2023, 1, 1)
    )
    db_session.add(filing)
    await db_session.commit()

    # Delete company
    await db_session.delete(company)
    await db_session.commit()

    # Check filing is also deleted
    result = await db_session.execute(select(Filing).where(Filing.company_cik == "0000012345"))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_create_user_with_alert(db_session):
    """Test creating a user with an alert."""
    # Create user
    user = User(
        email="test@example.com",
        full_name="Test User",
        oauth_provider="google",
        oauth_id="12345"
    )
    db_session.add(user)
    await db_session.commit()

    # Create alert
    alert = UserAlert(
        user_id=user.id,
        name="Apple 10-K Filings",
        conditions={"company_cik": "0000320193", "form_types": ["10-K"]},
        notification_method="email",
        frequency="immediate"
    )
    db_session.add(alert)
    await db_session.commit()

    # Query alert
    result = await db_session.execute(select(UserAlert).where(UserAlert.user_id == user.id))
    saved_alert = result.scalar_one()

    assert saved_alert.name == "Apple 10-K Filings"
    assert saved_alert.conditions["company_cik"] == "0000320193"
    assert saved_alert.is_active is True
