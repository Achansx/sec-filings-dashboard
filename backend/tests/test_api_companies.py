"""Tests for company API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_companies_empty(test_client: AsyncClient):
    """Test listing companies when none exist."""
    response = await test_client.get("/api/v1/companies")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_companies(test_client: AsyncClient, sample_company):
    """Test listing companies."""
    response = await test_client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cik"] == sample_company.cik
    assert data[0]["name"] == sample_company.name


@pytest.mark.asyncio
async def test_get_company(test_client: AsyncClient, sample_company):
    """Test getting a specific company."""
    response = await test_client.get(f"/api/v1/companies/{sample_company.cik}")
    assert response.status_code == 200
    data = response.json()
    assert data["cik"] == sample_company.cik
    assert data["name"] == sample_company.name
    assert "filings_count" in data


@pytest.mark.asyncio
async def test_get_company_not_found(test_client: AsyncClient):
    """Test getting a non-existent company."""
    response = await test_client.get("/api/v1/companies/9999999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_company(test_client: AsyncClient):
    """Test creating a new company."""
    company_data = {
        "cik": "0009876543",
        "name": "New Company Inc.",
        "ticker": "NEW",
        "sic_code": "5678",
        "industry_description": "Finance",
    }
    response = await test_client.post("/api/v1/companies", json=company_data)
    assert response.status_code == 201
    data = response.json()
    assert data["cik"] == company_data["cik"]
    assert data["name"] == company_data["name"]


@pytest.mark.asyncio
async def test_create_company_duplicate(test_client: AsyncClient, sample_company):
    """Test creating a company with duplicate CIK."""
    company_data = {
        "cik": sample_company.cik,
        "name": "Duplicate Company",
    }
    response = await test_client.post("/api/v1/companies", json=company_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_company(test_client: AsyncClient, sample_company):
    """Test updating a company."""
    update_data = {
        "name": "Updated Company Name",
        "ticker": "UPDT",
    }
    response = await test_client.patch(
        f"/api/v1/companies/{sample_company.cik}",
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["ticker"] == update_data["ticker"]


@pytest.mark.asyncio
async def test_update_company_not_found(test_client: AsyncClient):
    """Test updating a non-existent company."""
    update_data = {"name": "Updated Name"}
    response = await test_client.patch("/api/v1/companies/9999999999", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_company(test_client: AsyncClient, sample_company):
    """Test deleting a company."""
    response = await test_client.delete(f"/api/v1/companies/{sample_company.cik}")
    assert response.status_code == 204

    # Verify company is deleted
    response = await test_client.get(f"/api/v1/companies/{sample_company.cik}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_companies(test_client: AsyncClient, sample_company):
    """Test searching companies by name."""
    response = await test_client.get("/api/v1/companies/search?q=Test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(company["cik"] == sample_company.cik for company in data)
