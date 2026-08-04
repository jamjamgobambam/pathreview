"""Tests for dependency_audit_tool.py (issue #53).

https://github.com/ascherj/pathreview/issues/53

Started as a failing reproduction test (the tool did not exist); now a full unit
suite for `DependencyAuditTool`, which parses dependency manifests and flags
dependencies more than one major version behind their latest release.
"""

import pytest

from agent.tools.base import ToolResult
from agent.tools.dependency_audit_tool import DependencyAuditTool


@pytest.mark.unit
class TestDependencyAuditTool:
    """Test suite for DependencyAuditTool."""

    @pytest.fixture
    def auditor(self) -> DependencyAuditTool:
        return DependencyAuditTool()

    # ---- interface / basics ----

    def test_tool_conforms_to_base_interface(self, auditor: DependencyAuditTool) -> None:
        """Tool exposes name/description and returns a ToolResult."""
        assert auditor.name == "dependency_audit"
        assert isinstance(auditor.description, str) and auditor.description

    def test_empty_input_is_handled_gracefully(self, auditor: DependencyAuditTool) -> None:
        """No manifests should succeed with an empty outdated list, not crash."""
        result = auditor.execute({})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data["outdated"] == []
        assert result.data["checked"] == 0

    def test_result_structure(self, auditor: DependencyAuditTool) -> None:
        """Result data always exposes outdated/checked/skipped."""
        result = auditor.execute(
            {
                "manifests": {"requirements.txt": "django==2.2.0\n"},
                "latest_versions": {"django": "5.0.0"},
            }
        )
        assert set(result.data) >= {"outdated", "checked", "skipped"}
        item = result.data["outdated"][0]
        assert set(item) == {"name", "ecosystem", "current", "latest", "majors_behind"}

    # ---- core flagging behavior ----

    def test_flags_python_dependency_more_than_one_major_behind(
        self, auditor: DependencyAuditTool
    ) -> None:
        """A requirements.txt pin >1 major version behind latest is flagged."""
        result = auditor.execute(
            {
                "manifests": {"requirements.txt": "django==2.2.0\n"},
                "latest_versions": {"django": "5.0.0"},
            }
        )
        outdated = {item["name"]: item for item in result.data["outdated"]}
        assert "django" in outdated
        assert outdated["django"]["ecosystem"] == "pypi"
        assert outdated["django"]["majors_behind"] == 3

    def test_does_not_flag_current_dependency(self, auditor: DependencyAuditTool) -> None:
        """A dependency at (or within one major of) latest is NOT flagged."""
        result = auditor.execute(
            {
                "manifests": {"package.json": '{"dependencies": {"react": "18.2.0"}}'},
                "latest_versions": {"react": "18.3.1"},
            }
        )
        flagged = {item["name"] for item in result.data["outdated"]}
        assert "react" not in flagged
        assert result.data["checked"] == 1

    def test_exactly_one_major_behind_not_flagged_by_default(
        self, auditor: DependencyAuditTool
    ) -> None:
        """Default threshold flags only when >1 major behind, so 1 is safe."""
        result = auditor.execute(
            {
                "manifests": {"requirements.txt": "flask==2.0.0\n"},
                "latest_versions": {"flask": "3.0.0"},
            }
        )
        assert result.data["outdated"] == []
        assert result.data["checked"] == 1

    def test_max_major_lag_override_flags_one_behind(self, auditor: DependencyAuditTool) -> None:
        """A stricter per-call threshold flags a single major behind."""
        result = auditor.execute(
            {
                "manifests": {"requirements.txt": "flask==2.0.0\n"},
                "latest_versions": {"flask": "3.0.0"},
                "max_major_lag": 0,
            }
        )
        assert {item["name"] for item in result.data["outdated"]} == {"flask"}

    # ---- requirements.txt parsing ----

    def test_requirements_ignores_comments_options_and_markers(
        self, auditor: DependencyAuditTool
    ) -> None:
        """Comments, pip options, extras, and env markers are handled."""
        content = (
            "# a comment\n"
            "-r base.txt\n"
            "\n"
            "flask==2.0.0  # inline comment\n"
            "django[argon2]==2.2.0\n"
            'requests==2.0.0 ; python_version >= "3.8"\n'
        )
        result = auditor.execute(
            {
                "manifests": {"requirements.txt": content},
                "latest_versions": {"flask": "3.0.0", "django": "5.0.0", "requests": "2.31.0"},
            }
        )
        # flask 1 behind (not flagged), django 3 behind (flagged), requests current.
        assert {item["name"] for item in result.data["outdated"]} == {"django"}
        assert result.data["checked"] == 3
        assert result.data["skipped"] == []

    def test_requirements_skips_vcs_and_url_lines(self, auditor: DependencyAuditTool) -> None:
        """git+/URL requirements are skipped rather than mis-parsed."""
        content = "git+https://github.com/x/y.git#egg=y\nhttps://example.com/pkg.whl\n"
        result = auditor.execute({"manifests": {"requirements.txt": content}})
        assert result.data["checked"] == 0
        assert result.data["outdated"] == []

    # ---- pyproject.toml parsing ----

    def test_pyproject_pep621_dependencies(self, auditor: DependencyAuditTool) -> None:
        """PEP 621 [project].dependencies are parsed and compared."""
        content = (
            "[project]\n" 'name = "x"\n' 'dependencies = ["django>=2.0", "requests==2.31.0"]\n'
        )
        result = auditor.execute(
            {
                "manifests": {"pyproject.toml": content},
                "latest_versions": {"django": "5.0.0", "requests": "2.31.0"},
            }
        )
        assert {item["name"] for item in result.data["outdated"]} == {"django"}

    def test_pyproject_poetry_skips_python_entry(self, auditor: DependencyAuditTool) -> None:
        """Poetry's `python` constraint is not treated as a dependency."""
        content = "[tool.poetry.dependencies]\n" 'python = "^3.11"\n' 'django = "^2.2"\n'
        result = auditor.execute(
            {"manifests": {"pyproject.toml": content}, "latest_versions": {"django": "5.0.0"}}
        )
        flagged = {item["name"] for item in result.data["outdated"]}
        assert flagged == {"django"}
        assert "python" not in flagged

    # ---- package.json parsing ----

    def test_package_json_includes_dev_dependencies(self, auditor: DependencyAuditTool) -> None:
        """devDependencies are audited alongside dependencies."""
        content = '{"devDependencies": {"webpack": "3.0.0"}}'
        result = auditor.execute(
            {"manifests": {"package.json": content}, "latest_versions": {"webpack": "5.0.0"}}
        )
        outdated = {item["name"]: item for item in result.data["outdated"]}
        assert "webpack" in outdated
        assert outdated["webpack"]["ecosystem"] == "npm"

    def test_package_json_skips_non_registry_specs(self, auditor: DependencyAuditTool) -> None:
        """file:/git/workspace specs are ignored, not compared."""
        content = '{"dependencies": {"mylib": "file:../mylib", "react": "16.0.0"}}'
        result = auditor.execute(
            {"manifests": {"package.json": content}, "latest_versions": {"react": "18.0.0"}}
        )
        assert {item["name"] for item in result.data["outdated"]} == {"react"}
        assert result.data["checked"] == 1  # only react was comparable

    # ---- version prefixes / edge cases ----

    def test_semver_range_prefixes_are_stripped(self, auditor: DependencyAuditTool) -> None:
        """Caret/tilde/compound ranges resolve to their major version."""
        content = '{"dependencies": {"vue": "^2.6.0", "next": ">=12.0.0 <13"}}'
        result = auditor.execute(
            {
                "manifests": {"package.json": content},
                "latest_versions": {"vue": "3.4.0", "next": "14.0.0"},
            }
        )
        flagged = {item["name"] for item in result.data["outdated"]}
        assert flagged == {"next"}  # vue 1 behind, next 2 behind

    def test_name_normalization_matches_latest_versions(self, auditor: DependencyAuditTool) -> None:
        """`Django` in a manifest matches `django` in latest_versions."""
        result = auditor.execute(
            {
                "manifests": {"requirements.txt": "Django==2.2.0\n"},
                "latest_versions": {"django": "5.0.0"},
            }
        )
        assert {item["name"] for item in result.data["outdated"]} == {"Django"}

    def test_zero_major_versions_supported(self, auditor: DependencyAuditTool) -> None:
        """0.x dependencies are compared like any other major."""
        result = auditor.execute(
            {
                "manifests": {"requirements.txt": "somelib==0.4.0\n"},
                "latest_versions": {"somelib": "2.0.0"},
            }
        )
        assert {item["name"] for item in result.data["outdated"]} == {"somelib"}

    # ---- skipping / robustness ----

    def test_unpinned_dependency_is_skipped(self, auditor: DependencyAuditTool) -> None:
        """A dependency with no comparable version is skipped, not flagged."""
        result = auditor.execute(
            {"manifests": {"requirements.txt": "flask\n"}, "latest_versions": {"flask": "3.0.0"}}
        )
        assert result.data["outdated"] == []
        assert any(s.get("name") == "flask" for s in result.data["skipped"])

    def test_unknown_latest_version_is_skipped(self, auditor: DependencyAuditTool) -> None:
        """Offline with no supplied latest version -> skipped, not flagged."""
        result = auditor.execute({"manifests": {"requirements.txt": "obscurelib==1.0.0\n"}})
        assert result.data["outdated"] == []
        assert any(s.get("name") == "obscurelib" for s in result.data["skipped"])

    def test_malformed_manifest_does_not_crash(self, auditor: DependencyAuditTool) -> None:
        """A malformed manifest is recorded as skipped; the run still succeeds."""
        result = auditor.execute({"manifests": {"package.json": "{not valid json"}})
        assert result.success is True
        assert any(s.get("file") == "package.json" for s in result.data["skipped"])

    def test_multiple_manifests_audited_together(self, auditor: DependencyAuditTool) -> None:
        """Findings from several manifests are aggregated and sorted."""
        result = auditor.execute(
            {
                "manifests": {
                    "requirements.txt": "django==2.2.0\n",
                    "package.json": '{"dependencies": {"webpack": "3.0.0"}}',
                },
                "latest_versions": {"django": "5.0.0", "webpack": "5.0.0"},
            }
        )
        names = [item["name"] for item in result.data["outdated"]]
        assert set(names) == {"django", "webpack"}
        # Sorted most-outdated first (django is 3 behind, webpack 2 behind).
        assert names[0] == "django"
