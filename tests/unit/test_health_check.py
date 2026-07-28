"""Reproduction test for issue #154.

api/routes/health.py:31 calls `await db.execute("SELECT 1")` with a raw
Python string. SQLAlchemy 2.x no longer accepts raw strings as SQL — the
string must be wrapped with `sqlalchemy.text()`. The raw-string call raises
`ObjectNotExecutableError` (a subclass of `ArgumentError`), which the
health check's broad `except Exception` swallows, so `/health` reports
postgres as "unhealthy" even when the database is fully reachable.

These tests reproduce the failure directly against SQLAlchemy's engine
(no live Postgres needed, since the error is raised before a query is
ever sent to the database) and confirm that wrapping the string in
`text()` is what fixes it.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError, ObjectNotExecutableError


@pytest.mark.unit
def test_raw_string_execute_reproduces_issue_154() -> None:
    """Mirrors api/routes/health.py:31 — passing a raw string to execute()."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        with pytest.raises(ObjectNotExecutableError) as exc_info:
            conn.execute("SELECT 1")

        assert isinstance(exc_info.value, ArgumentError)


@pytest.mark.unit
def test_text_wrapped_query_succeeds() -> None:
    """Confirms `text("SELECT 1")` is the fix for the raw-string call above."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
