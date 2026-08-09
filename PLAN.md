# Technical Execution Plan: DAG-Based Tool Prerequisite Validator

*Author: Python Developer Intern*
*Issue Reference: #54*
*Framework: Elite Engineering SDLC Framework (Six-Part Specification)*

---

## 1. Understand (Problem & Motivation)

### The Core Issue
Our AI portfolio review assistant runs various specialized analysis tools (e.g., `tech_detector`, `skill_extractor`, `market_analyzer`). These tools have sequential and semantic dependencies:
- To analyze market alignment, we first need to extract the developer's skills.
- To extract skills accurately from repository metadata, we first need to detect the technologies and primary languages of the repository.

Currently, `agent/orchestrator.py` builds an execution plan and runs each tool in a simple `for` loop without verifying if that tool's prerequisites are actually met. If a tool runs out of order or if its dependencies are missing/failed, it either crashes at runtime or silently continues with empty/meaningless data (e.g., executing the market analyzer without any extracted skills, yielding a $0.0$ score).

### Objective
Implement a robust, graph-based (DAG) plan validation engine. Before any tool in the execution plan starts, the Orchestrator will run this validation engine to assert that:
- Every tool in the plan has all of its prerequisites satisfied (either present earlier in the plan or already completed in the session context).
- The execution plan follows a correct topological sort order.
- The dependency definitions do not contain any cyclic loops (circular dependencies).

---

## 2. Map (Architecture & Files)

We will modify or create the following files in our subsystem:

```
agent/
│
├── orchestrator.py                 # Modify: Invoke validation engine before running tools
│
└── tools/
    ├── __init__.py
    └── tool_dependencies.py        # New File: Define dependencies, PlanValidator, and PlanValidationError
```

- **`agent/tools/tool_dependencies.py` (New)**:
  - Define explicit tool prerequisite rules.
  - Implement a `PlanValidator` class with cycle detection (DFS with white/gray/black tracking) and topological sort verification.
  - Implement a custom `PlanValidationError` exception.
- **`agent/orchestrator.py` (Modify)**:
  - Import `PlanValidator` and `PlanValidationError`.
  - Instantiate `PlanValidator` and invoke `.validate_plan(plan, cached_results)` in `run()`.
- **`tests/unit/test_tool_dependencies.py` (Modify in next project phase)**:
  - Add green/positive assertions once the validation logic is active to test valid/invalid/cyclic execution scenarios.

---

## 3. Plan (Implementation Steps)

### Phase 1: Dependency Mapping & Schema Definition
1. Define a global dictionary of dependencies in `agent/tools/tool_dependencies.py`:
   ```python
   TOOL_DEPENDENCIES = {
       "github_tool": [],
       "tech_detector": [],
       "readme_scorer": [],
       "skill_extractor": ["tech_detector"],
       "market_analyzer": ["skill_extractor"]
   }
   ```
2. Define `PlanValidationError` inheriting from `ValueError`.

### Phase 2: Implement PlanValidator Engine
1. Implement `PlanValidator.has_cycle()` using Depth First Search (DFS) node coloring:
   - `0` (Unvisited)
   - `1` (Visiting/Gray - cycle detected if reached again)
   - `2` (Fully Visited/Black)
2. Implement topological order verification:
   - Walk the proposed plan. Maintain a set of "already run or planned before this point" tools.
   - For each tool `T` in the plan, assert that all elements of `TOOL_DEPENDENCIES[T]` are in the "already run or planned" set. If not, raise `PlanValidationError`.
3. Support checking session cache / cached results. If a prerequisite tool was already executed in a previous session (present in `cached_results`), it does not need to be in the current plan.

### Phase 3: Integrate with Orchestrator
1. Import `PlanValidator` and `PlanValidationError` in `agent/orchestrator.py`.
2. In `Orchestrator.run(profile_id, profile_data)`:
   - Right after building the execution plan (`plan = self._build_plan(profile_data)`), invoke the validator:
     ```python
     validator = PlanValidator()
     validator.validate(plan, self.context_manager.get_all_results())
     ```
3. Gracefully handle `PlanValidationError` by logging an error and returning a structured response containing the validation error message, or let it propagate depending on the desired error policy.

---

## 4. Inputs & Outputs (Contract)

### Validator Input
- `plan`: List of `(tool_name, tool_input)` tuples.
- `cached_results`: Dictionary of cached/completed tool results from `ContextManager.get_all_results()`.

### Validator Output
- Returns `None` if the plan is valid.
- Raises `PlanValidationError` with a clear, user-friendly descriptive message if invalid.

```python
class PlanValidator:
    def validate(self, plan: list[tuple[str, dict]], cached_results: dict) -> None:
        """Validates the proposed execution plan.

        Args:
            plan: The sequence of (tool_name, tool_input) proposed for execution.
            cached_results: Pre-existing successful tool results from session context.

        Raises:
            PlanValidationError: If a circular dependency is detected, or if a tool
                                is executed before/without its prerequisites.
        """
```

---

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Accidental Cycles** | Infinite recursion or hang during dependency resolution. | Implement formal cycle detection (graph coloring) with an explicit maximum recursion depth guard. |
| **Strict Blockers on Non-Critical Tools** | If a tool is added to the plan but its prerequisite failed, the entire workflow blocks. | Allow the orchestrator or validation config to flag certain prerequisites as optional/non-blocking if suitable, or fail-fast for safety. |
| **Performance Overhead** | Checking graph properties on every execution. | The tool dependency graph is very small (under 10 nodes); the DFS and topological sort checks will complete in sub-millisecond times, causing zero noticeable overhead. |

---

## 6. Edge Cases Handled

1.  **Empty Execution Plan**: An empty plan is always valid.
2.  **Partially Completed Pipelines**: If `skill_extractor` is cached in the context from a previous execution, we should be able to run `market_analyzer` in the current plan without needing to re-run `skill_extractor` or `tech_detector`.
3.  **Unknown Tools**: If a plan contains a tool not present in `TOOL_DEPENDENCIES`, raise a descriptive `PlanValidationError`.
4.  **Self-Looping Dependencies**: A tool that lists itself as a dependency (e.g., `Tool A -> Tool A`) will be flagged immediately as a cycle.
