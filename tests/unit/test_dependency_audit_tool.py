"""Tests for DependencyAuditTool."""

import pytest

from agent.tools.dependency_audit_tool import DependencyAuditTool


@pytest.mark.unit
class TestDependencyAuditTool:
    """Test suite for dependency auditing."""

    def test_flags_requirements_dependency_more_than_one_major_behind(self) -> None:
        """Flag a Python dependency more than one major version behind."""

        def resolver(name: str, ecosystem: str) -> str | None:
            versions = {
                ("Django", "pypi"): "5.1.0",
                ("requests", "pypi"): "2.32.0",
            }
            return versions.get((name, ecosystem))

        tool = DependencyAuditTool(version_resolver=resolver)

        result = tool.execute(
            {"manifests": {"requirements.txt": ("Django==2.2.0\n" "requests>=2.31.0\n")}}
        )

        assert result.success is True
        assert result.error is None
        assert result.data["checked_count"] == 2
        assert len(result.data["outdated_dependencies"]) == 1

        finding = result.data["outdated_dependencies"][0]
        assert finding["name"] == "Django"
        assert finding["latest_version"] == "5.1.0"
        assert finding["major_versions_behind"] == 3
        assert finding["source_file"] == "requirements.txt"

    def test_does_not_flag_dependency_exactly_one_major_behind(self) -> None:
        """Do not flag a dependency exactly one major version behind."""

        def resolver(name: str, ecosystem: str) -> str | None:
            assert name == "react"
            assert ecosystem == "npm"
            return "19.1.0"

        tool = DependencyAuditTool(version_resolver=resolver)

        result = tool.execute(
            {
                "manifests": {
                    "package.json": """
                    {
                        "dependencies": {
                            "react": "^18.2.0"
                        }
                    }
                    """
                }
            }
        )

        assert result.success is True
        assert result.data["checked_count"] == 1
        assert result.data["outdated_dependencies"] == []

    def test_flags_package_json_dependency_two_majors_behind(self) -> None:
        """Audit npm dependencies and flag a two-major gap."""

        def resolver(name: str, ecosystem: str) -> str | None:
            versions = {
                ("lodash", "npm"): "4.17.21",
                ("react", "npm"): "19.1.0",
            }
            return versions.get((name, ecosystem))

        tool = DependencyAuditTool(version_resolver=resolver)

        result = tool.execute(
            {
                "manifests": {
                    "package.json": """
                    {
                        "dependencies": {
                            "lodash": "^2.4.0"
                        },
                        "devDependencies": {
                            "react": "^18.2.0"
                        }
                    }
                    """
                }
            }
        )

        assert result.success is True

        findings = result.data["outdated_dependencies"]
        assert len(findings) == 1
        assert findings[0]["name"] == "lodash"
        assert findings[0]["major_versions_behind"] == 2
        assert findings[0]["ecosystem"] == "npm"

    def test_parses_pyproject_dependencies(self) -> None:
        """Audit standard PEP 621 pyproject dependencies."""

        def resolver(name: str, ecosystem: str) -> str | None:
            versions = {
                ("fastapi", "pypi"): "0.116.0",
                ("pydantic", "pypi"): "4.0.0",
                ("pytest", "pypi"): "9.0.0",
            }
            return versions.get((name, ecosystem))

        tool = DependencyAuditTool(version_resolver=resolver)

        result = tool.execute(
            {
                "manifests": {
                    "pyproject.toml": """
                    [project]
                    name = "example"

                    dependencies = [
                        "fastapi>=0.109.0",
                        "pydantic>=1.10.0"
                    ]

                    [project.optional-dependencies]
                    dev = [
                        "pytest>=7.4.0"
                    ]
                    """
                }
            }
        )

        assert result.success is True
        assert result.data["checked_count"] == 3

        names = {finding["name"] for finding in result.data["outdated_dependencies"]}
        assert names == {"pydantic", "pytest"}

    def test_skips_version_spec_without_numeric_major(self) -> None:
        """Skip dependency specs whose major version cannot be determined."""
        calls: list[tuple[str, str]] = []

        def resolver(name: str, ecosystem: str) -> str | None:
            calls.append((name, ecosystem))
            return "5.0.0"

        tool = DependencyAuditTool(version_resolver=resolver)

        result = tool.execute(
            {
                "manifests": {
                    "package.json": """
                    {
                        "dependencies": {
                            "local-package": "workspace:*"
                        }
                    }
                    """
                }
            }
        )

        assert result.success is True
        assert result.data["checked_count"] == 0
        assert result.data["outdated_dependencies"] == []
        assert len(result.data["skipped_dependencies"]) == 1
        assert result.data["skipped_dependencies"][0]["name"] == "local-package"
        assert calls == []

    def test_registry_lookup_failure_does_not_crash_audit(self) -> None:
        """A failed package lookup should not fail the whole tool."""

        def resolver(name: str, ecosystem: str) -> str | None:
            raise RuntimeError(f"registry unavailable for {name}/{ecosystem}")

        tool = DependencyAuditTool(version_resolver=resolver)

        result = tool.execute({"manifests": {"requirements.txt": "Django==2.2.0\n"}})

        assert result.success is True
        assert result.data["checked_count"] == 0
        assert result.data["outdated_dependencies"] == []
        assert len(result.data["lookup_failures"]) == 1
        assert result.data["lookup_failures"][0]["name"] == "Django"

    def test_malformed_manifest_is_reported_without_crashing(self) -> None:
        """Malformed supported manifests should be reported gracefully."""
        tool = DependencyAuditTool(version_resolver=lambda name, ecosystem: "1.0.0")

        result = tool.execute(
            {
                "manifests": {
                    "package.json": "{not valid json",
                    "pyproject.toml": "[project\ninvalid = true",
                }
            }
        )

        assert result.success is True
        assert result.data["outdated_dependencies"] == []
        assert result.data["checked_count"] == 0
        assert len(result.data["parse_errors"]) == 2

    def test_empty_supported_manifest_set_returns_empty_success(self) -> None:
        """No supported manifests should produce an empty successful audit."""
        tool = DependencyAuditTool(version_resolver=lambda name, ecosystem: "1.0.0")

        result = tool.execute(
            {
                "manifests": {
                    "Pipfile": "requests = '*'",
                    "yarn.lock": "lockfile contents",
                }
            }
        )

        assert result.success is True
        assert result.data["manifest_files"] == []
        assert result.data["checked_count"] == 0
        assert result.data["outdated_dependencies"] == []

    def test_missing_input_returns_failure(self) -> None:
        """Repository identity or direct manifest content is required."""
        tool = DependencyAuditTool()

        result = tool.execute({})

        assert result.success is False
        assert result.data == {}
        assert result.error is not None

    def test_extract_major_version_handles_common_specs(self) -> None:
        """Extract major versions from common Python and npm constraints."""
        assert DependencyAuditTool._extract_major_version("==2.4.1") == 2
        assert DependencyAuditTool._extract_major_version(">=3.0") == 3
        assert DependencyAuditTool._extract_major_version("^18.2.0") == 18
        assert DependencyAuditTool._extract_major_version("~4.1.0") == 4
        assert DependencyAuditTool._extract_major_version("workspace:*") is None
