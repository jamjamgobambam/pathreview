"""Tests for dependency audit planning in orchestrator.py"""

import pytest

from agent.orchestrator import Orchestrator


@pytest.mark.unit
class TestOrchestratorDependencyAudit:
    """Test suite for dependency audit orchestration."""

    def test_build_plan_adds_dependency_audit_for_dependency_files(self):
        """Test dependency manifests are added to the agent execution plan."""
        orchestrator = Orchestrator(tools={})

        plan = orchestrator._build_plan(
            {
                "dependency_files": {
                    "requirements.txt": "fastapi==0.90.0",
                    "src/app.py": "print('hello')",
                },
                "latest_versions": {"fastapi": "0.115.0"},
            }
        )

        assert (
            "dependency_audit",
            {
                "files": {"requirements.txt": "fastapi==0.90.0"},
                "latest_versions": {"fastapi": "0.115.0"},
            },
        ) in plan

    def test_build_plan_skips_dependency_audit_without_manifest_contents(self):
        """Test dependency audit is skipped when only file paths are available."""
        orchestrator = Orchestrator(tools={})

        plan = orchestrator._build_plan({"files": ["requirements.txt"]})

        tool_names = [tool_name for tool_name, _tool_input in plan]
        assert "dependency_audit" not in tool_names
