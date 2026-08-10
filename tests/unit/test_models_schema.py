"""Schema-level regression tests for the SQLAlchemy models.

Guards against duplicate index definitions: declaring both ``index=True`` on a
column and an explicit ``Index(...)`` of the same auto-generated name makes
``Base.metadata.create_all`` emit ``CREATE INDEX`` twice, which aborts the whole
transaction with a DuplicateTableError and prevents the app from starting.
"""

from collections import Counter

import pytest

import core.models  # noqa: F401  -- ensure every model is registered on Base
from core.database import Base


@pytest.mark.unit
class TestModelIndexDefinitions:
    """Index names must be unique so create_all() can build the schema."""

    def test_no_duplicate_index_names(self):
        names = [index.name for table in Base.metadata.tables.values() for index in table.indexes]
        duplicates = sorted(name for name, count in Counter(names).items() if count > 1)

        assert duplicates == [], f"Duplicate index names defined: {duplicates}"

    def test_indexed_foreign_keys_have_exactly_one_index(self):
        """The FK columns that previously collided keep a single index each."""
        expected = {
            "profiles": "ix_profiles_user_id",
            "reviews": "ix_reviews_profile_id",
            "ingested_sources": "ix_ingested_sources_profile_id",
        }
        for table_name, index_name in expected.items():
            table = Base.metadata.tables[table_name]
            matching = [idx for idx in table.indexes if idx.name == index_name]
            assert len(matching) == 1, (
                f"{table_name} should define {index_name} exactly once, " f"found {len(matching)}"
            )
