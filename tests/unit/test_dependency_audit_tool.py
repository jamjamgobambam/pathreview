"""Reproduction test for issue #53."""

from importlib.util import find_spec

import pytest


@pytest.mark.unit
def test_dependency_audit_tool_module_exists() -> None:
    """Confirm the dependency audit agent tool is available."""
    assert find_spec("agent.tools.dependency_audit_tool") is not None, (
        "Issue #53 reproduced: " "agent.tools.dependency_audit_tool does not exist"
    )
