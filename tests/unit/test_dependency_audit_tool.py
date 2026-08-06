"""Tests for dependency_audit_tool.py."""

import json

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.dependency_audit_tool import DependencyAuditTool


@pytest.mark.unit
class TestDependencyAuditTool:
    """Test suite for DependencyAuditTool."""

    @pytest.fixture
    def tool(self) -> DependencyAuditTool:
        """Create a DependencyAuditTool instance."""
        return DependencyAuditTool()

    def test_requirements_flags_only_dependencies_over_one_major_behind(
        self,
        tool: DependencyAuditTool,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Flag a dependency only when it is more than one major behind."""
        latest_versions: dict[tuple[str, str], str] = {
            ("old-package", "pypi"): "3.2.0",
            ("near-current", "pypi"): "3.0.0",
        }

        def fake_latest_version(name: str, ecosystem: str) -> str | None:
            return latest_versions.get((name, ecosystem))

        monkeypatch.setattr(tool, "_get_latest_version", fake_latest_version)

        result = tool.execute(
            {
                "dependency_files": {
                    "requirements.txt": ("old-package==1.4.0\n" "near-current>=2.0.0\n")
                }
            }
        )

        assert result.success is True
        assert result.data["manifests_found"] == ["requirements.txt"]
        assert result.data["dependencies_checked"] == 2

        outdated = result.data["outdated_dependencies"]
        assert len(outdated) == 1
        assert outdated[0] == {
            "name": "old-package",
            "ecosystem": "pypi",
            "declared_version": "1.4.0",
            "latest_version": "3.2.0",
            "major_versions_behind": 2,
            "source_file": "requirements.txt",
        }

    def test_package_json_dependencies_are_audited(
        self,
        tool: DependencyAuditTool,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Audit npm dependencies from package.json."""
        latest_versions: dict[tuple[str, str], str] = {
            ("react", "npm"): "19.0.0",
            ("vite", "npm"): "6.0.0",
        }

        def fake_latest_version(name: str, ecosystem: str) -> str | None:
            return latest_versions.get((name, ecosystem))

        monkeypatch.setattr(tool, "_get_latest_version", fake_latest_version)

        package_json = json.dumps(
            {
                "dependencies": {
                    "react": "^16.0.0",
                },
                "devDependencies": {
                    "vite": "^5.0.0",
                },
            }
        )

        result = tool.execute({"dependency_files": {"package.json": package_json}})

        assert result.success is True
        assert result.data["dependencies_checked"] == 2

        outdated = result.data["outdated_dependencies"]
        assert len(outdated) == 1
        assert outdated[0]["name"] == "react"
        assert outdated[0]["ecosystem"] == "npm"
        assert outdated[0]["major_versions_behind"] == 3

    def test_pyproject_dependencies_are_audited(
        self,
        tool: DependencyAuditTool,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Audit standard and Poetry dependencies from pyproject.toml."""
        latest_versions: dict[tuple[str, str], str] = {
            ("old-python-package", "pypi"): "3.0.0",
            ("legacy-lib", "pypi"): "4.1.0",
        }

        def fake_latest_version(name: str, ecosystem: str) -> str | None:
            return latest_versions.get((name, ecosystem))

        monkeypatch.setattr(tool, "_get_latest_version", fake_latest_version)

        pyproject = """
[project]
dependencies = [
    "old-python-package>=1.2.0",
]

[tool.poetry.dependencies]
python = "^3.11"
"legacy-lib" = "^2.0.0"
"""

        result = tool.execute({"dependency_files": {"pyproject.toml": pyproject}})

        assert result.success is True
        assert result.data["dependencies_checked"] == 2

        outdated_names = {dependency["name"] for dependency in result.data["outdated_dependencies"]}
        assert outdated_names == {"old-python-package", "legacy-lib"}

    def test_no_supported_manifests_returns_empty_audit(
        self,
        tool: DependencyAuditTool,
    ) -> None:
        """Return an empty successful audit when no manifests are provided."""
        result = tool.execute({"dependency_files": {}})

        assert result.success is True
        assert result.data["manifests_found"] == []
        assert result.data["dependencies_checked"] == 0
        assert result.data["outdated_dependencies"] == []

    def test_missing_input_returns_error(
        self,
        tool: DependencyAuditTool,
    ) -> None:
        """Require direct manifest contents or GitHub repository details."""
        result = tool.execute({})

        assert result.success is False
        assert result.data == {}
        assert result.error is not None


@pytest.mark.unit
def test_orchestrator_adds_dependency_audit_for_github_project() -> None:
    """Add dependency auditing when a GitHub project is available."""
    orchestrator = Orchestrator(tools={})

    plan = orchestrator._build_plan(
        {
            "github_username": "octocat",
            "projects": [{"github_repo": "hello-world"}],
        }
    )

    assert (
        "dependency_audit",
        {
            "github_username": "octocat",
            "repo_name": "hello-world",
        },
    ) in plan
