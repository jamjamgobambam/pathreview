"""Reproduction test for issue #154.

Health check DB probe passes a raw SQL string to ``connection.execute()``.
Under SQLAlchemy 2.x a bare string is no longer an accepted executable and
raises ``ArgumentError`` — so the ``GET /health`` probe reports Postgres as
"unhealthy" even when the database is perfectly reachable.

https://github.com/ascherj/pathreview/issues/154

The failing probe lives at ``api/routes/health.py`` line 31:

    await db.execute("SELECT 1")

The ``ArgumentError`` is raised during SQLAlchemy's statement coercion, which
is identical for sync and async engines, so this test reproduces the exact
failure with the built-in SQLite driver (no async plugins required).

``test_raw_string_probe_fails`` documents the bug (the raw ``"SELECT 1"``
call raises). ``test_text_wrapped_probe_succeeds`` shows the intended fix
(wrapping the query in ``sqlalchemy.text()``) works against a live session.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import ArgumentError


@pytest.fixture
def db_connection() -> Iterator[Connection]:
    """A live, reachable DB connection (in-memory SQLite)."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def test_raw_string_probe_fails(db_connection: Connection) -> None:
    """Reproduces #154: the current probe raises instead of returning a row.

    ``api/routes/health.py`` runs ``db.execute("SELECT 1")``. Against a fully
    working database this still raises, which is why the health check falsely
    reports Postgres as unhealthy.
    """
    with pytest.raises(ArgumentError):
        db_connection.execute("SELECT 1")


def test_text_wrapped_probe_succeeds(db_connection: Connection) -> None:
    """The intended fix: wrapping the probe in ``text()`` works normally."""
    result = db_connection.execute(text("SELECT 1"))
    assert result.scalar() == 1
