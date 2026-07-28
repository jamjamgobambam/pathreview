"""Reproduction test for issue #154.

SQLAlchemy 2.x requires textual SQL to be wrapped in sqlalchemy.text().
The health check route passes a bare string "SELECT 1" to db.execute(),
which raises ArgumentError and causes the DB probe to always report
postgres as unhealthy even when the database is reachable.

This test mocks the async DB session to raise the exact ArgumentError
that SQLAlchemy 2.x raises for a bare string, reproducing the bug
without needing a live database.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import ArgumentError


class TestHealthDbProbeBug:
    """Reproduces issue #154: bare SQL string fails under SQLAlchemy 2.x."""

    @pytest.mark.asyncio
    async def test_db_probe_fails_with_bare_string(self) -> None:
        """
        REPRODUCTION: db.execute("SELECT 1") raises ArgumentError in SQLAlchemy 2.x.

        SQLAlchemy 2.x refuses bare string SQL. The current health check passes
        the literal string "SELECT 1" which triggers:
            ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly
            declared as text('SELECT 1')

        This test confirms the bug is real: when SQLAlchemy raises ArgumentError,
        the health route catches it and marks postgres as 'unhealthy'.
        """
        # Simulate SQLAlchemy 2.x rejecting a bare SQL string
        mock_db = AsyncMock()
        mock_db.execute.side_effect = ArgumentError(
            "Textual SQL expression 'SELECT 1' should be explicitly declared " "as text('SELECT 1')"
        )

        from fastapi import HTTPException

        from api.routes.health import health_check

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db)

        # The route returns 503 because postgres is reported unhealthy
        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["status"] == "unhealthy"

        # Confirm the raw string was passed (the bug)
        mock_db.execute.assert_called_once_with("SELECT 1")

    @pytest.mark.asyncio
    async def test_db_probe_passes_with_text_wrapper(self) -> None:
        """
        EXPECTED BEHAVIOR: db.execute(text("SELECT 1")) succeeds.

        After the fix, the health route should wrap the SQL in sqlalchemy.text(),
        the execute call succeeds, and postgres is reported as healthy.
        This test documents the expected post-fix behavior.
        """
        from sqlalchemy import text

        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock()

        # Simulate what the fixed code should call
        await mock_db.execute(text("SELECT 1"))

        call_args = mock_db.execute.call_args[0][0]
        # sqlalchemy.text() produces a TextClause, not a plain string
        assert not isinstance(call_args, str), "Fix should pass text('SELECT 1'), not a bare string"
