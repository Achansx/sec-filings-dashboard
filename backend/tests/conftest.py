"""
Pytest configuration and fixtures for testing.
"""
import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base
from app.api.deps import get_db  # Import from deps, not database
from app.main import app


# Test database URL - only replace the database name at the end of the URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL
if not TEST_DATABASE_URL:
    # Replace only the last occurrence (the database name) not the username
    parts = settings.DATABASE_URL.rsplit('/', 1)
    if len(parts) == 2:
        TEST_DATABASE_URL = f"{parts[0]}/{settings.POSTGRES_DB}_test"
    else:
        TEST_DATABASE_URL = settings.DATABASE_URL + "_test"


# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    poolclass=NullPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Creates tables before each test and drops them after,
    ensuring complete test isolation.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a session
    async with TestSessionLocal() as session:
        yield session

    # Drop all tables to ensure clean state for next test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_app(db_session: AsyncSession):
    """
    Create test FastAPI application with overridden database dependency.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        # Each request gets the same session so changes are isolated
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    yield app

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_client(test_app):
    """
    Create test HTTP client.
    """
    from httpx import AsyncClient

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def sample_company(db_session: AsyncSession):
    """
    Create a sample company for testing.
    """
    from app.models.company import Company

    company = Company(
        cik="0001234567",
        name="Test Company Inc.",
        ticker="TEST",
        sic_code="1234",
        industry_description="Technology",
        fiscal_year_end="1231",
        state_of_incorporation="DE",
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest.fixture(scope="function")
async def sample_filing(db_session: AsyncSession, sample_company):
    """
    Create a sample filing for testing.
    """
    from app.models.filing import Filing
    from datetime import date

    filing = Filing(
        accession_number="0001234567-23-000001",
        company_cik=sample_company.cik,
        form_type="10-K",
        filing_date=date(2023, 3, 15),
        period_of_report=date(2022, 12, 31),
        description="Annual Report",
        document_count=5,
        file_url="https://www.sec.gov/Archives/edgar/data/1234567/000123456723000001/test.htm",
        indexed=False,
    )
    db_session.add(filing)
    await db_session.commit()
    await db_session.refresh(filing)
    return filing
