"""Tests for the Alembic migration chain and model/migration parity.

These cover the parts of migration health that can be checked without a
database. The parts that need a real database — that every migration applies
to an empty schema, and that the resulting schema matches the models — are
covered by `scripts/validate_migrations.sh` in the `validate-migrations` CI job.

The revision metadata is read with `ast` rather than by importing the migration
modules: the repo ships its own `alembic/` package directory, which shadows the
installed `alembic` distribution once the repo root is on `sys.path` (as it is
under pytest), so `from alembic import op` fails at collection time.
"""

import ast
from pathlib import Path

import pytest
from sqlalchemy import UniqueConstraint

from core.models import Base

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = REPO_ROOT / "alembic" / "versions"


class Migration:
    """The revision metadata of a single Alembic migration file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.module = ast.parse(path.read_text())
        self.revision = self._assigned_value("revision")
        self.down_revision = self._assigned_value("down_revision")
        self.functions = {
            node.name for node in self.module.body if isinstance(node, ast.FunctionDef)
        }

    def _assigned_value(self, name: str) -> str | None:
        """Return the literal assigned to a module-level name, or None."""
        for node in self.module.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == name for target in node.targets
            ):
                value = ast.literal_eval(node.value)
                return None if value is None else str(value)
        return None

    def __repr__(self) -> str:
        return f"<Migration {self.path.name} revision={self.revision}>"


def load_migrations() -> list[Migration]:
    """Load every migration in alembic/versions/, ignoring package files."""
    return [
        Migration(path)
        for path in sorted(VERSIONS_DIR.glob("*.py"))
        if not path.name.startswith("__")
    ]


@pytest.mark.unit
class TestMigrationChain:
    """Test suite for the structure of the Alembic revision chain."""

    def test_migrations_are_present(self) -> None:
        """Test the versions directory actually contains migrations.

        Guards the rest of this suite from passing vacuously if the glob
        stops matching.
        """
        assert load_migrations()

    def test_revision_ids_are_unique(self) -> None:
        """Test no two migrations claim the same revision id."""
        revisions = [migration.revision for migration in load_migrations()]

        assert len(revisions) == len(set(revisions)), f"duplicate revisions in {revisions}"

    def test_single_head(self) -> None:
        """Test exactly one migration is a head.

        A head is a revision no other migration points back to. Two heads mean
        two branches were never merged, and `alembic upgrade head` fails with
        an ambiguous-head error.
        """
        migrations = load_migrations()
        pointed_at = {migration.down_revision for migration in migrations}
        heads = [
            migration.revision for migration in migrations if migration.revision not in pointed_at
        ]

        assert len(heads) == 1, f"expected one head, found {heads}"

    def test_single_base(self) -> None:
        """Test exactly one migration starts the chain with down_revision = None."""
        bases = [
            migration.revision for migration in load_migrations() if migration.down_revision is None
        ]

        assert len(bases) == 1, f"expected one base revision, found {bases}"

    def test_every_down_revision_resolves(self) -> None:
        """Test each down_revision names a migration that exists.

        A dangling down_revision breaks `alembic upgrade head` with a
        "can't locate revision" error.
        """
        migrations = load_migrations()
        known = {migration.revision for migration in migrations}

        for migration in migrations:
            if migration.down_revision is not None:
                assert (
                    migration.down_revision in known
                ), f"{migration.path.name} points at unknown revision {migration.down_revision}"

    def test_every_revision_has_upgrade_and_downgrade(self) -> None:
        """Test each migration defines both upgrade() and downgrade()."""
        for migration in load_migrations():
            assert "upgrade" in migration.functions, f"{migration.path.name}: no upgrade()"
            assert "downgrade" in migration.functions, f"{migration.path.name}: no downgrade()"


@pytest.mark.unit
class TestModelMigrationParity:
    """Test suite for model declarations that the migrations depend on."""

    def test_user_model_declares_uq_users_email(self) -> None:
        """Test the User model declares the uq_users_email constraint.

        Migration 001 creates this constraint. When the model doesn't declare
        it, `alembic check` sees drift and autogenerates a remove_constraint —
        the drift this issue's CI job exists to catch.
        """
        users = Base.metadata.tables["users"]

        unique_constraints = {
            constraint.name
            for constraint in users.constraints
            if isinstance(constraint, UniqueConstraint)
        }

        assert "uq_users_email" in unique_constraints

    def test_user_email_index_is_unique(self) -> None:
        """Test ix_users_email stays a unique index, as migration 001 creates it."""
        users = Base.metadata.tables["users"]

        email_index = next(index for index in users.indexes if index.name == "ix_users_email")

        assert email_index.unique is True
