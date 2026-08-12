"""Unit tests for the database migration validation workflow."""

import ast
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = REPO_ROOT / "alembic" / "versions"
CORRECTIVE_MIGRATION = VERSIONS_DIR / "003_drop_redundant_users_email_constraint.py"


def _parse_migration(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def _assignment_value(tree: ast.Module, name: str) -> str | None:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} is not declared in the migration")


def _operation_calls(tree: ast.Module, function_name: str) -> list[ast.Call]:
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    return [node for node in ast.walk(function) if isinstance(node, ast.Call)]


@pytest.mark.unit
def test_migration_history_has_one_complete_revision_chain() -> None:
    revisions: dict[str, str | None] = {}
    for path in VERSIONS_DIR.glob("[0-9]*.py"):
        tree = _parse_migration(path)
        revisions[_assignment_value(tree, "revision")] = _assignment_value(tree, "down_revision")

    assert revisions == {"001": None, "002": "001", "003": "002"}


@pytest.mark.unit
def test_corrective_migration_drops_only_redundant_constraint() -> None:
    calls = _operation_calls(_parse_migration(CORRECTIVE_MIGRATION), "upgrade")

    assert len(calls) == 1
    call = calls[0]
    assert isinstance(call.func, ast.Attribute)
    assert call.func.attr == "drop_constraint"
    assert [ast.literal_eval(argument) for argument in call.args] == [
        "uq_users_email",
        "users",
    ]
    assert {keyword.arg: ast.literal_eval(keyword.value) for keyword in call.keywords} == {
        "type_": "unique"
    }


@pytest.mark.unit
def test_corrective_migration_restores_constraint_on_downgrade() -> None:
    calls = _operation_calls(_parse_migration(CORRECTIVE_MIGRATION), "downgrade")

    assert len(calls) == 1
    call = calls[0]
    assert isinstance(call.func, ast.Attribute)
    assert call.func.attr == "create_unique_constraint"
    assert [ast.literal_eval(argument) for argument in call.args] == [
        "uq_users_email",
        "users",
        ["email"],
    ]


@pytest.mark.unit
def test_validation_script_rejects_missing_database_url() -> None:
    environment = os.environ.copy()
    environment.pop("DATABASE_URL", None)

    result = subprocess.run(
        ["bash", "scripts/validate_migrations.sh"],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "DATABASE_URL must be set" in result.stderr
