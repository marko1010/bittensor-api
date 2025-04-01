import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from unittest.mock import AsyncMock, patch
from bson import ObjectId

@pytest.fixture
def client():
    return TestClient(app)

INVALID_API_KEY = "invalid_key"
TEST_NETUID = 1

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {settings.API_KEY}"}

@pytest.fixture
def invalid_auth_headers():
    return {"Authorization": f"Bearer {INVALID_API_KEY}"}

def test_get_tao_dividends_success(client, auth_headers):
    """Test successful retrieval of Tao dividends"""
    response = client.get(
        f"{settings.API_V1_PREFIX}/tao_dividends?netuid={TEST_NETUID}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "data" in data
    assert isinstance(data["data"], dict)

def test_get_tao_dividends_unauthorized(client, invalid_auth_headers):
    """Test unauthorized access to Tao dividends"""
    response = client.get(
        f"{settings.API_V1_PREFIX}/tao_dividends",
        headers=invalid_auth_headers
    )
    assert response.status_code == 403
    assert "detail" in response.json()

def test_get_subnet_sentiment_success(client, auth_headers):
    """Test successful retrieval of subnet sentiment"""
    response = client.get(
        f"{settings.API_V1_PREFIX}/sentiment/{TEST_NETUID}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "sentiment_score" in data
    assert -100 <= data["sentiment_score"] <= 100

def test_invalid_api_key(client, invalid_auth_headers):
    """Test invalid API key handling"""
    response = client.get(
        f"{settings.API_V1_PREFIX}/tao_dividends",
        headers=invalid_auth_headers
    )
    assert response.status_code == 403
    assert "detail" in response.json()

def test_invalid_endpoint(client, auth_headers):
    """Test handling of non-existent endpoints"""
    response = client.get(
        f"{settings.API_V1_PREFIX}/non_existent",
        headers=auth_headers
    )
    assert response.status_code == 404 