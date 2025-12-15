"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "testvendor",
            "role": "vendor",
            "pgp_public_key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n...\n-----END PGP PUBLIC KEY BLOCK-----"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "challenge" in data
    assert data["username"] == "testvendor"


@pytest.mark.asyncio
async def test_login_challenge(client: AsyncClient):
    """Test login challenge generation."""
    # First register a user
    await client.post(
        "/api/auth/register",
        json={
            "username": "testvendor",
            "role": "vendor",
            "pgp_public_key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n...\n-----END PGP PUBLIC KEY BLOCK-----"
        }
    )
    
    # Request login challenge
    response = await client.post(
        "/api/auth/login/challenge",
        json={"username": "testvendor"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "challenge" in data
