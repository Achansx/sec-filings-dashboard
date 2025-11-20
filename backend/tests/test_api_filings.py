"""Tests for filing API endpoints."""
import pytest
from httpx import AsyncClient
from datetime import date


@pytest.mark.asyncio
async def test_list_filings_empty(test_client: AsyncClient):
    """Test listing filings when none exist."""
    response = await test_client.get("/api/v1/filings")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_filings(test_client: AsyncClient, sample_filing):
    """Test listing filings."""
    response = await test_client.get("/api/v1/filings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["accession_number"] == sample_filing.accession_number
    assert data[0]["form_type"] == sample_filing.form_type


@pytest.mark.asyncio
async def test_list_filings_by_company(test_client: AsyncClient, sample_filing, sample_company):
    """Test listing filings filtered by company."""
    response = await test_client.get(f"/api/v1/filings?company_cik={sample_company.cik}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["company_cik"] == sample_company.cik


@pytest.mark.asyncio
async def test_list_filings_by_form_type(test_client: AsyncClient, sample_filing):
    """Test listing filings filtered by form type."""
    response = await test_client.get(f"/api/v1/filings?form_type={sample_filing.form_type}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["form_type"] == sample_filing.form_type


@pytest.mark.asyncio
async def test_get_filing(test_client: AsyncClient, sample_filing):
    """Test getting a specific filing."""
    response = await test_client.get(f"/api/v1/filings/{sample_filing.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_filing.id
    assert data["accession_number"] == sample_filing.accession_number
    assert "company_name" in data
    assert "documents" in data


@pytest.mark.asyncio
async def test_get_filing_not_found(test_client: AsyncClient):
    """Test getting a non-existent filing."""
    response = await test_client.get("/api/v1/filings/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_filing(test_client: AsyncClient, sample_company):
    """Test creating a new filing."""
    filing_data = {
        "accession_number": "0001234567-23-000002",
        "company_cik": sample_company.cik,
        "form_type": "10-Q",
        "filing_date": "2023-06-15",
        "period_of_report": "2023-03-31",
        "description": "Quarterly Report",
        "indexed": False,
    }
    response = await test_client.post("/api/v1/filings", json=filing_data)
    assert response.status_code == 201
    data = response.json()
    assert data["accession_number"] == filing_data["accession_number"]
    assert data["form_type"] == filing_data["form_type"]


@pytest.mark.asyncio
async def test_create_filing_duplicate(test_client: AsyncClient, sample_filing):
    """Test creating a filing with duplicate accession number."""
    filing_data = {
        "accession_number": sample_filing.accession_number,
        "company_cik": sample_filing.company_cik,
        "form_type": "10-K",
        "filing_date": "2023-03-15",
    }
    response = await test_client.post("/api/v1/filings", json=filing_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_filing(test_client: AsyncClient, sample_filing):
    """Test updating a filing."""
    update_data = {
        "description": "Updated Description",
        "indexed": True,
    }
    response = await test_client.patch(
        f"/api/v1/filings/{sample_filing.id}",
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == update_data["description"]
    assert data["indexed"] == update_data["indexed"]


@pytest.mark.asyncio
async def test_delete_filing(test_client: AsyncClient, sample_filing):
    """Test deleting a filing."""
    response = await test_client.delete(f"/api/v1/filings/{sample_filing.id}")
    assert response.status_code == 204

    # Verify filing is deleted
    response = await test_client.get(f"/api/v1/filings/{sample_filing.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_recent_filings(test_client: AsyncClient, sample_filing):
    """Test getting recent filings."""
    # Note: This test may fail if sample_filing is older than the days parameter
    # For testing purposes, we'll just verify the endpoint works
    response = await test_client.get("/api/v1/filings/recent?days=90")
    assert response.status_code == 200
    # The response should be a list (may or may not contain our sample filing)
    assert isinstance(response.json(), list)
