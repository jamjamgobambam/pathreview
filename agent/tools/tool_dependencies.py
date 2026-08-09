"""Tool dependencies and plan validation engine.

This module defines the explicit prerequisites/dependencies for agent tools
and provides the validation engine (PlanValidator) that checks proposed plans
for cyclic loops and topological constraint compliance.
"""

import structlog

logger = structlog.get_logger()


# Explicit prerequisite mapping for each agent tool
TOOL_DEPENDENCIES = {
    "github_tool": [],
    "tech_detector": [],
    "readme_scorer": [],
    "skill_extractor": ["tech_detector"],
    "market_analyzer": ["skill_extractor"],
}


class PlanValidationError(ValueError):
    """Custom exception raised when plan validation fails."""

    pass


class PlanValidator:
    """Validator for tool execution plans based on a dependency DAG."""

    def __init__(self, dependencies: dict[str, list[str]] | None = None):
        """Initialize the validator with a dependency dictionary.

        Args:
            dependencies: Optional mapping of tool name to list of prerequisite tool names.
                          Defaults to TOOL_DEPENDENCIES if None.
        """
        self.dependencies = dependencies if dependencies is not None else TOOL_DEPENDENCIES

    def check_for_cycles(self) -> None:
        """Check for cycles in the tool dependencies DAG.

        Uses Depth First Search (DFS) graph coloring to detect cycles:
        - 0: Unvisited
        - 1: Visiting (Gray)
        - 2: Fully Visited (Black)

        Raises:
            PlanValidationError: If a circular dependency is detected.
        """
        state = {node: 0 for node in self.dependencies}

        def dfs(node: str) -> None:
            if state.get(node, 0) == 1:
                raise PlanValidationError(f"Circular dependency detected involving tool: {node}")
            if state.get(node, 0) == 2:
                return

            state[node] = 1  # visiting
            for neighbor in self.dependencies.get(node, []):
                # Only run DFS on defined neighbor tools
                if neighbor in self.dependencies:
                    dfs(neighbor)
                else:
                    # Self-loop check for custom undefined neighbors
                    if neighbor == node:
                        raise PlanValidationError(
                            f"Circular dependency detected involving tool: {node}"
                        )
            state[node] = 2  # visited

        for node in self.dependencies:
            if state[node] == 0:
                dfs(node)

    def topological_sort(self, plan: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
        """Topologically sorts the proposed plan based on the dependency DAG.

        Re-orders tools in the plan so that all prerequisites run before their
        dependent tools, making the plan correct and valid for execution.

        Args:
            plan: The proposed list of (tool_name, tool_input) tuples.

        Returns:
            A new list of (tool_name, tool_input) tuples sorted topologically.

        Raises:
            PlanValidationError: If a circular dependency is detected.
        """
        self.check_for_cycles()

        tool_inputs = {name: inp for name, inp in plan}
        planned_tools = set(tool_inputs.keys())

        visited = set()
        sorted_plan = []

        def visit(node: str) -> None:
            if node in visited:
                return
            # Visit prerequisites that are also in the proposed plan
            for prereq in self.dependencies.get(node, []):
                if prereq in planned_tools:
                    visit(prereq)
            visited.add(node)
            sorted_plan.append((node, tool_inputs[node]))

        for name, _ in plan:
            if name not in visited:
                visit(name)

        return sorted_plan

    def validate_plan(self, plan: list[tuple[str, dict]], cached_results: dict) -> None:
        """Validates the proposed execution plan.

        Ensures that:
        - There are no circular dependencies.
        - Every tool in the plan is known (exists in the dependency map).
        - For every tool in the plan, all of its prerequisites are either already completed
          (present in cached_results) or scheduled earlier in the plan.

        Args:
            plan: The sequence of (tool_name, tool_input) proposed for execution.
            cached_results: Pre-existing successful tool results from session context.

        Raises:
            PlanValidationError: If any validation checks fail.
        """
        # 1. Detect cycles
        self.check_for_cycles()

        # 2. Extract completed tools from cached results
        completed_tools = set()
        for key in cached_results:
            if ":" in key:
                tool_name = key.split(":")[0]
                completed_tools.add(tool_name)
            else:
                completed_tools.add(key)

        # 3. Iterate through proposed plan and verify prerequisites
        for tool_name, _ in plan:
            if tool_name not in self.dependencies:
                raise PlanValidationError(f"Unknown tool '{tool_name}' in proposed execution plan.")

            prereqs = self.dependencies[tool_name]
            for prereq in prereqs:
                if prereq not in completed_tools:
                    raise PlanValidationError(
                        f"Prerequisite '{prereq}' for tool '{tool_name}' is not satisfied. "
                        f"Ensure it runs earlier or exists in cached results."
                    )

            # Mark current tool as completed since its prerequisites are validated
            completed_tools.add(tool_name)

        logger.info("plan_validated_successfully", plan_length=len(plan))
