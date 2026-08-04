"""Smoke tests proving the integration test-database fixtures work end to end."""

import pytest
from sqlalchemy import select, text

from core.models import User


@pytest.mark.integration
class TestDatabaseConnection:
    """Verify the test DB connection, table creation, and app<->DB wiring."""

    @pytest.mark.asyncio
    async def test_session_can_query_test_database(self, db_session):
        """The db_session fixture connects to pathreview_test and can query it."""
        result = await db_session.execute(text("SELECT current_database()"))
        assert result.scalar_one() == "pathreview_test"

    @pytest.mark.asyncio
    async def test_users_table_exists_and_is_empty(self, db_session):
        """Tables are created by the fixture; a fresh test DB starts empty."""
        result = await db_session.execute(select(User))
        assert result.scalars().all() == []

    @pytest.mark.asyncio
    async def test_seeded_user_is_visible(self, db_session, test_user):
        """The test_user fixture inserts a real, queryable row."""
        result = await db_session.execute(select(User).where(User.email == test_user["email"]))
        user = result.scalar_one()
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_app_health_endpoint_through_client(self, client):
        """The AsyncClient reaches the real app over HTTP."""
        resp = await client.get("/")
        assert resp.status_code == 200
