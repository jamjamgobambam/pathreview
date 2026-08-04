"""Integration test that migrations apply cleanly and match the models.

Drives scripts/validate_migrations.sh end to end: the script resets a database
to an empty schema, applies every Alembic migration in order, round-trips a full
downgrade/upgrade, and runs ``alembic check`` to confirm the resulting schema
matches ``Base.metadata`` (the SQLAlchemy models in core/models/). The test
passes only if all of that succeeds, so it fails on an un-appliable migration, a
broken ``downgrade()``, or drift between the migrations and the models.

The test is invoked as a subprocess because the repository's top-level
``alembic/`` migrations directory shadows the installed ``alembic`` library,
so the real Alembic CLI cannot be imported in-process from the repo root.

Requires a reachable Postgres via ``DATABASE_URL`` and therefore runs only in
the integration suite (``make test-integration`` / the CI integration job).
"""

import shutil
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_migrations.sh"


@pytest.mark.integration
class TestMigrationValidation:
    """Verify the migration chain builds a schema consistent with the models."""

    def test_validate_migrations_script_succeeds(self) -> None:
        """scripts/validate_migrations.sh exits 0 against a fresh database."""
        bash = shutil.which("bash")
        if bash is None:
            pytest.skip("bash is required to run scripts/validate_migrations.sh")
        # pytest.skip() raises, so bash is a str below; assert guides the type checker.
        assert bash is not None

        result = subprocess.run(
            [bash, str(_SCRIPT)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            "Migration validation failed:\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        assert "Migration validation passed." in result.stdout
