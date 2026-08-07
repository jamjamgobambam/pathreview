"""Unit tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.main import app

client = TestClient(app)


def test_health_check_redis_healthy() -> None:  # ✅ Added -> None
    """Test health check when Redis is running."""
    # Mock Redis connection to return healthy
    with patch("api.routes.health.redis.Redis") as mock_redis:
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_redis.from_url.return_value = mock_instance
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["dependencies"]["redis"] == "healthy"


def test_health_check_redis_unhealthy() -> None:  # ✅ Added -> None
    """Test health check when Redis is down."""
    # Mock Redis connection to raise exception
    with patch("api.routes.health.redis.Redis") as mock_redis:
        mock_redis.from_url.side_effect = Exception("Connection refused")
        
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["dependencies"]["redis"] == "unhealthy"


def test_health_check_postgres_healthy() -> None:  # ✅ Added -> None
    """Test health check when PostgreSQL is healthy."""
    # Mock database connection
    with patch("api.routes.health.get_db") as mock_db:
        mock_conn = MagicMock()
        mock_conn.execute.return_value = None
        mock_db.return_value.__aenter__.return_value = mock_conn
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["dependencies"]["postgres"] == "healthy"


def test_health_check_postgres_unhealthy() -> None:  # ✅ Added -> None
    """Test health check when PostgreSQL is down."""
    # Mock database to raise exception
    with patch("api.routes.health.get_db") as mock_db:
        mock_db.return_value.__aenter__.side_effect = Exception("Connection failed")
        
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["dependencies"]["postgres"] == "unhealthy"