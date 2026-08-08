## Week 7 — Issue selection

**Issue link:** <https://github.com/ascherj/pathreview/issues/14>

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The system currently misses valuable CI/CD and DevOps skills (like GitHub Actions, Docker, pytest, or deployment tasks) because they typically do not appear in standard `import` statements or README text. To fix this, a new `workflow_parser.py` is needed within the `ingestion/parsers/` directory. A successful implementation will read `.github/workflows/*.yml` files, infer these DevOps skills, and integrate seamlessly with `skill_extractor.py` to ensure users get credit for maintaining CI/CD pipelines.

**Branch name:** feat/14-github-actions-parser

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** <https://github.com/Builder106/pathreview/commit/d04a3dd0b803c77d5801973e32a4605b69833616>

**Reproduction summary:**
I added a new failing unit test in `test_skill_extractor.py` that verifies the `SkillExtractor` is currently unable to extract CI/CD skills (e.g., GitHub Actions, pytest) from standard `.github/workflows/*.yml` workflow definitions. This proves that parsing support for workflow files is missing.

**PLAN.md link:** <https://github.com/Builder106/pathreview/blob/feat/14-github-actions-parser/PLAN.md>

**Walkthrough video (recommended):** [Not recorded yet, but repository is updated with the required deliverables]

**Blockers or open questions:**
`pyyaml` is not currently in `pyproject.toml`. I will need to clarify if it is acceptable to add it as a new dependency to parse YAML properly, or if a robust regex-based extraction mechanism should be used instead.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Implemented `ingestion/parsers/workflow_parser.py` with the `WorkflowParser` class to extract CI/CD skills from GitHub Actions YAML files using lightweight regex matching for `uses:` actions and `run:` commands without requiring external dependencies like `pyyaml`. Updated `ingestion/parsers/skill_extractor.py` to route `.github/workflows/*.yml` files to `WorkflowParser` and moved `SkillDetection` to `ingestion/parsers/base.py` to prevent circular imports.

**Next steps:** Write unit tests in `tests/unit/test_workflow_parser.py` covering action mappings, single-line/block run steps, confidence bounds, edge cases, and non-workflow filtering. Update `tests/unit/test_skill_extractor.py` to verify workflow path delegation. Run quality checks (`make check` and `make test-unit`), commit changes, open the pull request against `ascherj/pathreview`, and complete Check-in 2.

**Blockers:** None.

---

### Check-in 2 (end of week)

**PR link:** <https://github.com/ascherj/pathreview/pull/340>

**Branch:** feat/14-github-actions-parser

**What you built:** Added `WorkflowParser` to parse `.github/workflows/*.yml` files using regex patterns for `uses:` actions and `run:` steps. Integrated it into `SkillExtractor` so that CI/CD skills like GitHub Actions, Docker, pytest, AWS, and Kubernetes are detected automatically from workflow definitions.

**Tests added or updated:** Created `tests/unit/test_workflow_parser.py` with 25 unit tests covering action parsing (`uses:`), single-line and block-scalar run steps (`run:`), confidence scores bounded between 0.0 and 1.0, edge cases with empty files or invalid input types, and filtering out non-workflow YAML files. Updated `tests/unit/test_skill_extractor.py` with `test_github_actions_workflow_detection` to verify delegation for workflow files.

**Self-review confirmation:**
[x] make check passes
[x] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes [ ] No

**Summary of feedback:**
The reviewer commended the zero-dependency, regex-based `WorkflowParser` design choice over adding `pyyaml` as a pragmatic approach, noting that documenting the trade-off in `PLAN.md` demonstrated good engineering judgment. However, the reviewer highlighted two key areas for improvement:
1. **Module Architecture & Circular Dependencies:** Moving `SkillDetection` into `ingestion/parsers/base.py` solved the immediate circular import, but signals that responsibilities between modules could have been more clearly separated from the outset. In future work, sketching out dependency relationships prior to coding will prevent reactive refactor cycles.
2. **Test Suite Maintainability & Robustness:** While 25 unit tests provided good coverage, test setup shared repetitive inline YAML strings that should be refactored into shared test fixtures or helper functions. Furthermore, regex parsing should be validated against real-world workflow files from open-source repos to catch complex formatting such as YAML comments interspersed with `uses:` lines or multi-line `run:` blocks containing heredoc syntax.

**How you responded:**
- Documented reviewer feedback in `JOURNAL.md` and checked the feedback received confirmation.
- Reflected on module design choices: recognized that defining clean abstractions and shared data models (`SkillDetection`) early in the design phase prevents circular dependency workarounds.
- Identified actionable test suite improvements: planned refactoring inline test strings into modular pytest fixtures and designing integration test cases with real-world open-source GitHub Actions workflow files to test edge cases like heredoc block scalars and inline comments.

---

### Reflection

**What was harder than you expected?**
Navigating internal architectural constraints without introducing circular imports was harder than expected. When introducing `WorkflowParser` into the ingestion pipeline, `SkillExtractor` and existing parser modules had tight type annotations and shared data models like `SkillDetection`. Resolving the circular import cycle by extracting `SkillDetection` into `ingestion/parsers/base.py` required careful module isolation. Additionally, ensuring a zero-dependency regex approach robustly extracted `uses:` actions and `run:` steps without breaking on unusual YAML constructs required meticulous pattern tuning.

**What did you learn about working in a large codebase?**
I learned that architectural planning upfront saves significant refactoring effort down the line. Sketching module dependency graphs prior to implementation helps separate core domain models from parser implementations before circular dependencies arise. Furthermore, I learned the importance of test suite maintainability: using shared pytest fixtures instead of repeating inline string construction keeps tests clean, and testing against real-world open-source fixtures ensures parsing resilience against edge cases like heredocs or interspersed comments.

**How did AI tools help — and where did they fall short?**
AI tools were helpful for rapidly prototyping initial regex patterns and generating repetitive unit test boilerplate for `test_workflow_parser.py` across single-line and multi-line scenarios. However, AI tools fell short when reasoning about high-level circular import cycles across multiple Python modules, where human architectural tracing was needed to determine how to isolate `base.py`. They also missed real-world YAML edge cases—such as heredoc syntax inside multi-line `run:` blocks or comments intermingled with `uses:` lines—which required human inspection to address.

**What would you do differently if you started over?**
If starting over, I would map out module dependencies on paper before writing code to establish shared data structures (`SkillDetection`) cleanly from day one, avoiding reactive import-fix refactors. I would also design the test suite using pytest fixtures from the start and include a dedicated suite of real-world open-source `.github/workflows/*.yml` sample files as test fixtures to validate complex syntax upfront.

**What are you most proud of from this module?**
I am most proud of designing and implementing a zero-dependency `WorkflowParser` that cleanly extracts CI/CD skills (like GitHub Actions, Docker, pytest, AWS, and Kubernetes) from workflow files, writing 25 comprehensive unit tests to verify its behavior, and earning positive reviewer recognition for documenting engineering trade-offs in `PLAN.md`.
