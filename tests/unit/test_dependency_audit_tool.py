"""Reproduction test for issue #53 — DependencyAuditTool.

https://github.com/ascherj/pathreview/issues/53

STATUS: RED (reproduction). This test currently FAILS at import time because
`agent/tools/dependency_audit_tool.py` does not exist yet — that absence *is*
the gap this issue describes. The agent has tools to detect a repo's tech stack
(`tech_detector`) but nothing that reads dependency manifests and flags
dependencies that are more than one major version behind their latest release.

Week 9 will implement `DependencyAuditTool` and these expectations should turn
green. The proposed I/O contract below is provisional and is finalized in
PLAN.md; adjust these assertions when the contract is locked.
"""

import pytest

from agent.tools.base import ToolResult

# NOTE: the import below fails today with ModuleNotFoundError (see module
# docstring) — that is the reproduction of issue #53.
from agent.tools.dependency_audit_tool import DependencyAuditTool


@pytest.mark.unit
class TestDependencyAuditToolReproduction:
    """Expected behavior of the not-yet-implemented DependencyAuditTool."""

    @pytest.fixture
    def auditor(self) -> DependencyAuditTool:
        return DependencyAuditTool()

    def test_tool_conforms_to_base_interface(self, auditor: DependencyAuditTool) -> None:
        """Tool exposes name/description and returns a ToolResult."""
        assert auditor.name == "dependency_audit"
        assert isinstance(auditor.description, str) and auditor.description

    def test_flags_python_dependency_more_than_one_major_behind(
        self, auditor: DependencyAuditTool
    ) -> None:
        """A requirements.txt pin >1 major version behind latest is flagged."""
        manifests = {"requirements.txt": "django==2.2.0\n"}
        result = auditor.execute({"manifests": manifests, "latest_versions": {"django": "5.0.0"}})

        assert isinstance(result, ToolResult)
        assert result.success is True
        outdated = {item["name"]: item for item in result.data["outdated"]}
        assert "django" in outdated

    def test_does_not_flag_current_dependency(self, auditor: DependencyAuditTool) -> None:
        """A dependency at (or within one major of) latest is NOT flagged."""
        manifests = {"package.json": '{"dependencies": {"react": "18.2.0"}}'}
        result = auditor.execute({"manifests": manifests, "latest_versions": {"react": "18.3.1"}})

        assert result.success is True
        flagged = {item["name"] for item in result.data["outdated"]}
        assert "react" not in flagged

    def test_empty_input_is_handled_gracefully(self, auditor: DependencyAuditTool) -> None:
        """No manifests should succeed with an empty outdated list, not crash."""
        result = auditor.execute({})
        assert result.success is True
        assert result.data["outdated"] == []
