"""Tests for the Alembic migration history.

Static checks over the migration scripts -- no database required. They guard
the invariants the CI migration-validation job relies on
(see scripts/validate_migrations.sh): a single, linear, complete history.

The scripts are parsed directly rather than imported: the project ships a
local ``alembic/`` directory that shadows the installed ``alembic`` package,
so a plain ``import alembic.config`` fails under pytest.
"""

import ast
from pathlib import Path

import pytest

VERSIONS_DIR = Path(__file__).resolve().parents[2] / "alembic" / "versions"


def _load_revisions() -> dict:
    """Return {revision_id: down_revision} parsed from each migration file."""
    revisions: dict = {}
    for path in VERSIONS_DIR.glob("[0-9]*.py"):
        module = ast.parse(path.read_text(encoding="utf-8"))
        assignments = {}
        for node in module.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    assignments[target.id] = ast.literal_eval(node.value)
        assert "revision" in assignments, f"{path.name} has no revision id"
        revisions[assignments["revision"]] = assignments.get("down_revision")
    return revisions


@pytest.mark.unit
class TestMigrations:
    """Test suite for the Alembic migration history."""

    def test_revisions_exist(self) -> None:
        """There should be migration scripts to validate."""
        revisions = _load_revisions()
        assert revisions, "Expected at least one migration revision"

    def test_single_base(self) -> None:
        """Exactly one revision may have no parent (the base)."""
        revisions = _load_revisions()
        bases = [rev for rev, down in revisions.items() if down is None]
        assert len(bases) == 1, f"Expected a single base revision, found: {bases}"

    def test_single_head(self) -> None:
        """Exactly one revision is a head so `upgrade head` is unambiguous."""
        revisions = _load_revisions()
        referenced: set = set()
        for down in revisions.values():
            if down is None:
                continue
            referenced.update(down if isinstance(down, tuple) else (down,))
        heads = [rev for rev in revisions if rev not in referenced]
        assert len(heads) == 1, f"Expected a single migration head, found: {heads}"

    def test_every_parent_exists(self) -> None:
        """Every down_revision must reference a known revision."""
        revisions = _load_revisions()
        known = set(revisions)
        for rev, down in revisions.items():
            if down is None:
                continue
            for parent in down if isinstance(down, tuple) else (down,):
                assert parent in known, f"Revision {rev} references unknown parent {parent}"
