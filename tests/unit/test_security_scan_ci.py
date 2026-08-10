"""Tests that the dependency vulnerability scan stays wired into CI and tooling.

These guard issue #128: CI must fail on high-severity dependency vulnerabilities.
They assert the *configuration* is present (pip-audit + npm audit, a `security-scan`
CI job, a `make audit` target) so a future edit that silently drops the gate fails
here instead of shipping an unscanned pipeline.
"""

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
class TestSecurityScanWiring:
    """Verify the dependency vulnerability scan is present across CI and tooling."""

    @pytest.fixture
    def ci_workflow(self) -> str:
        """Return the text of the CI workflow file."""
        return (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()

    @pytest.fixture
    def makefile(self) -> str:
        """Return the text of the Makefile."""
        return (REPO_ROOT / "Makefile").read_text()

    def test_pip_audit_is_a_dev_dependency(self) -> None:
        """pip-audit must be declared so CI and `make audit` can run it."""
        pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
        dev_deps = pyproject["project"]["optional-dependencies"]["dev"]
        assert any(dep.startswith("pip-audit") for dep in dev_deps)

    def test_ci_has_security_scan_job(self, ci_workflow: str) -> None:
        """The CI workflow must define a dedicated security-scan job."""
        assert "security-scan:" in ci_workflow

    def test_ci_runs_pip_audit(self, ci_workflow: str) -> None:
        """CI must scan Python dependencies with pip-audit."""
        assert "pip-audit" in ci_workflow

    def test_ci_frontend_scan_fails_on_high_severity(self, ci_workflow: str) -> None:
        """CI must run npm audit and fail on high+ severity findings."""
        assert "npm audit" in ci_workflow
        assert "--audit-level=high" in ci_workflow

    def test_makefile_has_audit_target(self, makefile: str) -> None:
        """A `make audit` target must exist for local parity with CI."""
        assert "\naudit:" in makefile

    def test_makefile_audit_runs_both_scanners(self, makefile: str) -> None:
        """The audit target must run both the Python and frontend scanners."""
        audit_section = makefile.split("\naudit:", 1)[1]
        assert "pip-audit" in audit_section
        assert "npm audit" in audit_section
