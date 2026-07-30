"""Reproduction script for issue #44.

Demonstrates that when a tool fails, the orchestrator logs the error
internally but the top-level return value gives no indication that
anything went wrong — a caller has to manually inspect every entry
in tool_results for a "success": False key.
"""

from typing import Any

from agent.orchestrator import Orchestrator


class FailingTool:
    """A tool that always raises an exception."""

    name = "failing_tool"

    def execute(self, tool_input: dict[str, Any]) -> Any:
        raise ValueError("Simulated tool failure")


def fake_plan(profile_data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return [("failing_tool", {})]


def main() -> None:
    orchestrator = Orchestrator(tools={"failing_tool": FailingTool()})
    orchestrator._build_plan = fake_plan  # type: ignore[method-assign]

    result = orchestrator.run(profile_id="test-profile", profile_data={})

    print("Top-level result keys:", list(result.keys()))
    print(
        "Does top level show any failure indicator? ->",
        "has_errors" in result or "failed_tools" in result,
    )
    print("Actual tool_results:", result["tool_results"])


if __name__ == "__main__":
    main()
