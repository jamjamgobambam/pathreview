# Context & Alignment: Issue #54 Plan Validation Step

*Hey there! As a basic Python intern on the team, I've spent time diving deep into how our multi-module AI agent portfolio review assistant manages tool execution. This document establishes our team's Ubiquitous Language, documents my /grill-with-docs learning session on DAGs, and outlines our DAG-based plan validation strategy so we're completely aligned before we start coding.*

---

## 1. Ubiquitous Language (Domain Glossary)

To ensure clear, unambiguous communication across the engineering team, we define the following key terms:

*   **Orchestrator (`Orchestrator`)**: The core component in `agent/orchestrator.py` that schedules, plans, and executes analysis tools on user profile data.
*   **Analysis Plan (Plan)**: A linear sequence of `(tool_name, tool_input)` tuples compiled by the Orchestrator to run on a profile.
*   **Tool Dependency Graph (DAG)**: A Directed Acyclic Graph representing tools as nodes and their dependency requirements as directed edges. E.g., `market_analyzer -> skill_extractor -> tech_detector` means `tech_detector` must run before `skill_extractor`, which must run before `market_analyzer`.
*   **Prerequisite (Dependency)**: An upstream tool that must run and produce a successful outcome before a downstream tool can safely execute.
*   **Topological Sort**: A linear ordering of the vertices of a directed graph such that for every directed edge $u \rightarrow v$, vertex $u$ comes before $v$ in the ordering. Used to determine a valid execution sequence.
*   **Plan Validation**: The preprocessing step performed by the validation engine *before* any tools in the plan are executed, ensuring all prerequisites are met and no circular loops exist.
*   **Cycle (Circular Dependency)**: An invalid configuration where a tool directly or indirectly depends on itself (e.g., `Tool A -> Tool B -> Tool A`), rendering topological sorting impossible.
*   **PlanValidationError**: A dedicated exception class that the validator raises immediately if a validation check fails.

---

## 2. Refined DAG-Based Validation Strategy

### The Core Problem (Intern Perspective)
Currently, our `Orchestrator` is super trusting. It builds a list of tools and runs them one-by-one. If a tool in the middle fails, or if we request a tool whose prerequisites aren't in the plan, the orchestrator doesn't notice until a runtime crash occurs or we get useless empty/zero results (like a market alignment score of `0.0`).

### The Solution: A DAG Validator
We will introduce a `PlanValidator` in a new file `agent/tools/tool_dependencies.py`. Before executing any tools in `Orchestrator.run()`, we will feed the plan to this validator.

The validator will perform three key checks:
1.  **Tool Prerequisite Presence**: Ensure that if a tool is planned, all of its required prerequisites are either also in the plan or already stored as cached results from a prior execution.
2.  **Order Validation (Topological Feasibility)**: Ensure the current plan is sorted in a valid topological order. If the plan specifies a dependent tool before its prerequisites, the validator can either re-order them automatically or throw a `PlanValidationError`. (Throwing a clear validation error is safer and more predictable).
3.  **Cycle Detection**: Verify that there are no circular dependencies in our defined tool dependency graph using a Depth-First Search (DFS) node-coloring algorithm (White/Gray/Black).

---

## 3. Explicit Tool Dependencies

Based on how our tools pass data through the session context, here is the official dependency mapping:

```
                  +-------------------+
                  |   github_tool     |
                  +---------+---------+
                            |
                            | (optional repo_metadata)
                            v
+-------------------+     +-------------------+
|   tech_detector   +---->+  skill_extractor  |
+-------------------+     +---------+---------+
                                    |
                                    | (detected_skills)
                                    v
                          +-------------------+
                          |  market_analyzer  |
                          +-------------------+
```

1.  **`github_tool`**: No prerequisites.
2.  **`tech_detector`**: No prerequisites.
3.  **`readme_scorer`**: No prerequisites.
4.  **`skill_extractor`**: Depends on **`tech_detector`** (uses its language and framework counts to enrich resume skill extraction) or **`github_tool`** (uses repo_metadata).
5.  **`market_analyzer`**: Depends on **`skill_extractor`** (uses its output `detected_skills` to compare against market demand values).
