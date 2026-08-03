"""
Integration tests for the health check endpoint.

These tests verify that the health check endpoint correctly:
- Connects to PostgreSQL
- Detects when dependencies are healthy or unhealthy
- Returns appropriate HTTP status codes
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.integration
class TestHealthCheck:
    """Test suite for GET /health endpoint."""

    async def test_health_check_returns_200_when_postgres_healthy(
        self, client: AsyncClient
    ):
        """
        Test that health check returns 200 when PostgreSQL is up.
        
        This test reproduces the SQLAlchemy 2.x issue:
        - Before fix: Raw SQL string "SELECT 1" fails with CompileError
        - After fix: Wrapped in text("SELECT 1") succeeds
        """
        response = await client.get("/health")
        
        # Should return 200, not 503
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["dependencies"]["postgres"] == "healthy"
        assert "timestamp" in data
        assert "safety_events_last_hour" in data

    async def test_health_check_has_all_dependencies(self, client: AsyncClient):
        """Test that health check response includes all expected dependencies."""
        response = await client.get("/health")
        
        data = response.json()
        assert "postgres" in data["dependencies"]
        assert "redis" in data["dependencies"]
        assert "vector_db" in data["dependencies"]

    async def test_health_check_response_structure(self, client: AsyncClient):
        """Test that health check response has the expected structure."""
        response = await client.get("/health")
        
        data = response.json()
        assert "status" in data
        assert "dependencies" in data
        assert "timestamp" in data
        assert "safety_events_last_hour" in data
        assert data["safety_events_last_hour"] == 0