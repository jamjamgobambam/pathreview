"""Reproduction test for issue #154.

SQLAlchemy 2.x rejects bare strings passed to Session.execute(); the health
probe in api/routes/health.py does exactly this with "SELECT 1", so the
probe raises ArgumentError and /health reports Postgres as unhealthy even
when the DB is reachable.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session


def test_raw_sql_string_raises_under_sqlalchemy_2x() -> None:
    """Reproduce #154: a bare SQL string must raise ArgumentError under SQLAlchemy 2.x.

    This is the same call the health probe makes (just synchronously).
    It should raise ArgumentError, which is why /health marks Postgres unhealthy.
    """
    engine = create_engine("sqlite:///:memory:")
    with Session(engine) as session, pytest.raises(ArgumentError):
        session.execute("SELECT 1")


def test_wrapped_sql_string_does_not_raise() -> None:
    """Sanity check: wrapping in text() is the fix (should pass)."""
    engine = create_engine("sqlite:///:memory:")
    with Session(engine) as session:
        # This should NOT raise — confirms text() is the correct remedy.
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
