"""Tests for dependency_audit_tool.py"""

import pytest

from agent.tools.dependency_audit_tool import DependencyAuditTool


@pytest.mark.unit
class TestDependencyAuditTool:
    """Test suite for DependencyAuditTool."""

    @pytest.fixture
    def tool(self):
        """Create a DependencyAuditTool instance."""
        return DependencyAuditTool()

    def test_flags_dependencies_more_than_one_major_version_behind(self, tool):
        """Test dependencies with a major-version gap greater than one are flagged."""
        result = tool.execute(
            {
                "files": {
                    "requirements.txt": "fastapi==0.90.0\nhttpx>=0.26.0",
                    "package.json": '{"dependencies": {"react": "^16.14.0"}}',
                },
                "latest_versions": {
                    "fastapi": "0.115.0",
                    "httpx": "0.28.0",
                    "react": "19.1.0",
                },
            }
        )

        assert result.success is True
        outdated = result.data["outdated_dependencies"]

        assert len(outdated) == 1
        assert outdated[0]["name"] == "react"
        assert outdated[0]["declared_version"] == "16.14.0"
        assert outdated[0]["latest_version"] == "19.1.0"
        assert outdated[0]["major_gap"] == 3
        assert outdated[0]["status"] == "outdated"

    def test_does_not_flag_dependencies_only_one_major_version_behind(self, tool):
        """Test dependencies only one major version behind are treated as current."""
        result = tool.execute(
            {
                "files": {
                    "package.json": '{"dependencies": {"vite": "^5.0.0"}}',
                },
                "latest_versions": {"vite": "6.0.0"},
            }
        )

        assert result.success is True
        assert result.data["outdated_dependencies"] == []
        assert result.data["audited_dependencies"][0]["status"] == "current"
        assert result.data["audited_dependencies"][0]["major_gap"] == 1

    def test_parses_pyproject_dependencies(self, tool):
        """Test pyproject.toml dependencies are included in the audit."""
        result = tool.execute(
            {
                "files": {"pyproject.toml": """
                    [project]
                    dependencies = ["pydantic>=1.10.0", "httpx>=0.26.0"]

                    [tool.poetry.dependencies]
                    python = "^3.11"
                    redis = "^3.5.0"
                    """},
                "latest_versions": {
                    "pydantic": "2.8.0",
                    "httpx": "0.28.0",
                    "redis": "5.0.0",
                },
            }
        )

        audited_by_name = {
            dependency["name"]: dependency for dependency in result.data["audited_dependencies"]
        }

        assert result.success is True
        assert audited_by_name["pydantic"]["status"] == "current"
        assert audited_by_name["redis"]["status"] == "outdated"
        assert audited_by_name["redis"]["major_gap"] == 2
        assert "python" not in audited_by_name

    def test_handles_malformed_and_unsupported_files_without_crashing(self, tool):
        """Test malformed manifests return warnings and unsupported files are skipped."""
        result = tool.execute(
            {
                "files": {
                    "package.json": '{"dependencies": ',
                    "README.md": "# Demo",
                    "requirements.txt": "flask\n",
                },
                "latest_versions": {"flask": "3.0.0"},
            }
        )

        audited_by_name = {
            dependency["name"]: dependency for dependency in result.data["audited_dependencies"]
        }

        assert result.success is True
        assert "README.md" in result.data["skipped_files"]
        assert result.data["warnings"]
        assert audited_by_name["flask"]["status"] == "unpinned"

    def test_non_mapping_files_input_returns_warning(self, tool):
        """Test invalid file input returns a warning instead of raising an exception."""
        result = tool.execute({"files": ["requirements.txt"]})

        assert result.success is True
        assert result.data["audited_dependencies"] == []
        assert result.data["outdated_dependencies"] == []
        assert result.data["warnings"] == ["Expected files to be a mapping of path to contents."]
