"""Tool dependency graph and plan validation for the agent orchestrator.

The orchestrator builds a plan as an ordered list of ``(tool_name, tool_input)``
pairs. Some tools consume the output of others — for example ``market_analyzer``
needs the skills produced by ``skill_extractor`` and the stack produced by
``tech_detector``. This module models those relationships as a directed acyclic
graph (DAG) and provides helpers to validate a plan *before* it runs and to
gate individual tools *during* execution.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger()

# Directed acyclic graph of tool prerequisites: each tool maps to the tools that
# must have run successfully before it. Edges reflect the data a tool consumes.
#
# Note: ``skill_extractor`` is intentionally NOT given ``github_tool`` as a hard
# prerequisite. It operates correctly on ``resume_text`` alone, so requiring the
# GitHub step would wrongly block valid resume-only analyses. The dependency that
# causes issue #54's reported bug — ``market_analyzer`` running without upstream
# results — is modeled explicitly below.
TOOL_DEPENDENCIES: dict[str, list[str]] = {
    "github_tool": [],
    "tech_detector": [],
    "readme_scorer": [],
    "skill_extractor": [],
    "market_analyzer": ["skill_extractor", "tech_detector"],
}


class PlanValidationError(Exception):
    """Raised when an execution plan is structurally invalid."""


def find_cycle(dependencies: dict[str, list[str]]) -> list[str] | None:
    """Detect a cycle in a dependency graph.

    Args:
        dependencies: Map of tool name -> list of prerequisite tool names.

    Returns:
        The cycle as a list of tool names (with the start node repeated at the
        end), or ``None`` if the graph is acyclic.
    """
    white, grey, black = 0, 1, 2
    color: dict[str, int] = {node: white for node in dependencies}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = grey
        stack.append(node)
        for dep in dependencies.get(node, []):
            state = color.get(dep, white)
            if state == grey:
                start = stack.index(dep)
                return stack[start:] + [dep]
            if state == white:
                found = visit(dep)
                if found is not None:
                    return found
        color[node] = black
        stack.pop()
        return None

    for node in dependencies:
        if color[node] == white:
            found = visit(node)
            if found is not None:
                return found
    return None


def validate_plan(
    plan: list[tuple[str, dict]],
    dependencies: dict[str, list[str]] | None = None,
) -> list[str]:
    """Validate a plan against the tool dependency graph before execution.

    Two structural checks are performed:

    * the dependency graph must be acyclic; and
    * any prerequisite that also appears in the plan must be ordered *before*
      the tool that depends on it.

    A prerequisite that is simply *absent* from the plan is not reported here —
    the orchestrator handles unmet prerequisites at run time by skipping the
    dependent tool (see :func:`unmet_prerequisites`). This keeps optional
    upstream tools from failing an otherwise valid plan.

    Args:
        plan: Ordered ``(tool_name, tool_input)`` pairs from the planner.
        dependencies: Dependency graph; defaults to :data:`TOOL_DEPENDENCIES`.

    Returns:
        A list of human-readable error messages; empty if the plan is valid.
    """
    deps = dependencies if dependencies is not None else TOOL_DEPENDENCIES
    errors: list[str] = []

    cycle = find_cycle(deps)
    if cycle is not None:
        errors.append("dependency graph has a cycle: " + " -> ".join(cycle))
        # Ordering checks are meaningless on a cyclic graph.
        return errors

    first_position: dict[str, int] = {}
    for index, (tool_name, _tool_input) in enumerate(plan):
        first_position.setdefault(tool_name, index)

    for index, (tool_name, _tool_input) in enumerate(plan):
        for prereq in deps.get(tool_name, []):
            prereq_pos = first_position.get(prereq)
            if prereq_pos is not None and prereq_pos > index:
                errors.append(
                    f"'{tool_name}' (step {index}) runs before its "
                    f"prerequisite '{prereq}' (step {prereq_pos})"
                )

    return errors


def unmet_prerequisites(
    tool_name: str,
    completed: dict[str, bool],
    dependencies: dict[str, list[str]] | None = None,
) -> list[str]:
    """Return the prerequisites of a tool that have not completed successfully.

    Args:
        tool_name: The tool about to be executed.
        completed: Map of tool name -> whether it has run successfully so far.
        dependencies: Dependency graph; defaults to :data:`TOOL_DEPENDENCIES`.

    Returns:
        Prerequisite tool names that are missing from ``completed`` or that did
        not succeed. Empty if every prerequisite is satisfied.
    """
    deps = dependencies if dependencies is not None else TOOL_DEPENDENCIES
    return [prereq for prereq in deps.get(tool_name, []) if not completed.get(prereq, False)]
