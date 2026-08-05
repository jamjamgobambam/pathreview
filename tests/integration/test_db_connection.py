"""Smoke tests proving the integration test-database fixtures work end to end."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select, text

from core.models import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
class TestDatabaseConnection:
    """Verify the test DB connection, table creation, and app<->DB wiring."""

    @pytest.mark.asyncio
    async def test_session_can_query_test_database(self, db_session: AsyncSession) -> None:
        """The db_session fixture connects to pathreview_test and can query it."""
        result = await db_session.execute(text("SELECT current_database()"))
        assert result.scalar_one() == "pathreview_test"

    @pytest.mark.asyncio
    async def test_users_table_exists_and_is_empty(self, db_session: AsyncSession) -> None:
        """Tables are created by the fixture; a fresh test DB starts empty."""
        result = await db_session.execute(select(User))
        assert result.scalars().all() == []
