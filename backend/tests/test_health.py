"""Tests for health check endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(test_client: AsyncClient):
    """Test root endpoint returns API information."""
    response = await test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "environment" in data
    assert data["message"] == "SEC Filings Dashboard API"


@pytest.mark.asyncio
async def test_readiness_check(test_client: AsyncClient):
    """Test readiness probe endpoint."""
    response = await test_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ready"
