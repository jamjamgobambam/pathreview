# Issue Selection and Planning: Project 7

## 1. Issue Analysis
Selected Issue: **Add a plan validation step that checks tool prerequisites before executing the plan**
- **Issue Number:** #54
- **Repository:** ascherj/pathreview
- **Status:** Open, Active, Unassigned
- **Category:** Agent System / DevOps / Enhancement
- **Difficulty Tier:** Tier 3

### Problem Summary:
The current orchestrator in `agent/orchestrator.py` constructs a plan of tools to run on profile data, but executes them sequentially without validating their respective prerequisites. For example:
- The skill extractor tool depends on portfolio ingestion being complete and having resume text.
- The market analyzer depends on the skill extractor and tech detector tools having run first to supply valid skills.
Without any tool prerequisite validation, executing a tool with missing dependencies results in failures or useless empty results. The goal of this issue is to introduce a DAG-based plan validator in the `agent` subsystem, defining explicit tool prerequisites and validating the plan before execution.

---

## 2. Verification
- **Direct GitHub Issue Link:** https://github.com/ascherj/pathreview/issues/54
- **Activity Status:** The issue is currently open, active, and has not been closed or assigned to any contributor on the `ascherj/pathreview` repository. This ensures it is a valid target for the upcoming implementation phases of Project 7.

---

## 3. Rationale & Feasibility
- **Stated Skill Level & Fit:** As a basic Python intern, choosing a Tier 3 issue might seem challenging, but it provides an optimal learning path. It aligns perfectly with my goal to develop deep familiarity with the PathReview codebase, particularly its multi-tool agentic architecture. By reasoning about how tools depend on each other, I will learn how information flows through the system, bridging the gap from a basic intern to a proficient software developer.
- **Brief Impact Assessment:**
  - **Likely Root Cause:** The orchestrator (`agent/orchestrator.py`) handles tool execution by compiling a linear list of tools based on the presence of certain keys in `profile_data` (e.g., if there's a resume file, add `skill_extractor`). However, there is no validation step to ensure that preceding tools in the chain have completed successfully and generated the necessary output data, or that mandatory prerequisites are available.
  - **Affected Files:**
    - `agent/orchestrator.py`: Needs update to invoke the validator before starting the tool execution loop.
    - `agent/tools/tool_dependencies.py` (New File): Will define the tool dependency graph/DAG, prerequisite criteria for each tool, and the validation engine.
    - `tests/unit/test_tool_dependencies.py` (New File): Will test the dependency validation logic and cycle detection.
  - **Step-by-Step Implementation Approach:**
    1. Define the tool requirements and inputs/outputs mapping.
    2. Create `agent/tools/tool_dependencies.py` and implement a simple Directed Acyclic Graph (DAG) validator. It should check that for every tool in the plan, all dependencies are also planned or completed and no circular dependencies exist.
    3. Update `agent/orchestrator.py` to integrate the validation step after building the execution plan.
    4. Write comprehensive unit tests in `tests/unit/test_tool_dependencies.py` to verify valid plans, detect missing prerequisites, and handle edge cases (e.g., circular dependencies, empty plans).

---

## 4. Anticipated Challenges
1. **Managing Dynamic Tool Context:** Downstream tools depend on results loaded into the context by upstream tools. As a basic Python intern, understanding and mocking this context flow correctly in tests could be tricky. To approach this, I will carefully study how `ContextManager` behaves and isolate the dependency validation from the actual tool execution logic using mock states.
2. **Circular Dependency Risks:** Defining tool prerequisites could accidentally lead to circular dependency loops if tool schemas change. To mitigate this, the DAG validator must implement a standard cycle detection algorithm (e.g., depth-first search colors) and raise a descriptive validation error if a loop is detected.
