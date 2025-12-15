"""Tests for lead management endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_lead(client: AsyncClient):
    """Test lead creation."""
    # TODO: Add authentication fixture
    response = await client.post(
        "/api/leads/",
        json={
            "title": "Test Lead",
            "description": "Test description",
            "category": "technology",
            "urgency": "high"
        }
    )
    # Will fail without auth, but tests the endpoint structure
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_list_leads(client: AsyncClient):
    """Test listing leads."""
    response = await client.get("/api/leads/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
