### Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

## Problem summary: 

PathReview reviews developer skills from a developer's repository and resume, but it
completely ignores CI/CD configuration, so DevOps skills never show up in a review.

At present, the ingestion pipeline has no parser for `.github/workflows/*.yml` files,
even though those files demonstrate skills like GitHub Actions, Docker, automated
testing with pytest, and deployment. 

Per `docs/ARCHITECTURE.md`, ingestion parsers implement a BaseParser interface, so the new workflow parser would follow that existing pattern (parse → chunk → embed → store).

A successful fix adds a new `workflow_parser.py` under `ingestion/parsers/` and wires it into `skill_extractor.py` so workflow files
are parsed during ingestion and CI/CD skills appear in the extracted skill set.

**Branch name:** feat/14-github-actions-workflow-parsing

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Selection notes ("Is this right for me?" checklist): 

**Understanding:** The ingestion pipeline extracts skills from portfolio documents but
never reads `.github/workflows/*.yml`, so CI/CD skills are invisible in reviews. 

Before: A repo with GitHub Actions workflows shows no DevOps skills in its review. 

After: Skills like GitHub Actions, Docker, and pytest appear in the extracted skill set.

**Files located:** Confirmed `ingestion/parsers/skill_extractor.py` exists and read it alongside `ingestion/parsers/resume_parser.py`. Parsers like ResumeParser implement the `BaseParser` interface (returning a `ParseResult` with text + metadata), while SkillExtractor is a separate keyword-matching layer that scores skills from parsed text. The workflow parser will need to produce output SkillExtractor can score.

**Tier 3 fit:** I've built multi-service projects (FastAPI, Docker, vector databases) in prior coursework, so following an existing parser interface is realistic for me in Weeks 8–9 even as a first contribution to this codebase. I'm choosing it with the scope warning in mind, not despite it.

**Codebase readiness:**  Read `skill_extractor.py` and `resume_parser.py` end-to-end. The closest unit test to my module is `tests/unit/test_batch_processor.py` (ingestion embeddings), which uses a `@pytest.mark.unit` class with `@pytest.fixture` mocks for external services. No parser-specific unit test exists yet, so I'll model a new `test_workflow_parser.py` on that pattern.

**Scope and time:** 6–10 hours across two weeks is achievable with my current schedule and work responsibilities.

No blockers or dependencies on other issues. 3 other students have claimed it; claims are non-exclusive and grading is based on my own artifacts.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/88813ebd373719687a9525d86915cade1aa53502

**Reproduction summary:**
- I created a test repository containing `.github/workflows/ci.yml` with `actions/checkout@v4`, `docker/build-push-action@v5`, and a `pytest` test step. 

- Running the current ingestion pipeline against this repo confirmed that `SkillExtractor.extract_skills()` returns zero CI/CD skills; workflow files are completely ignored. The `.yml` files never enter the parser pipeline, and even if they did, keywords like `Github Actions`, `pytest`, and `deployment` are absent from `SkillExtractor.TOOLS`.

**PLAN.md link:** https://github.com/codekikicode/pathreview/blob/feat/14-github-actions-workflow-parsing/PLAN.md

**Blockers or open questions:**
- Can `BaseParser.parse()` accept a filesystem path? Do I need to add a `parse_from_path()` method?

- Confirm if `PyYAML` is already in `requirements.txt`. Should I plan out the dependency addition?

---

### Week 9 — Solution building & PR submission

## Check-in 1 (mid-week)

**Current progress:**
- *Sub-task 1 (dispatch mechanism):* Confirmed `__init__.py` is empty and parsers are manually instantiated in `pipeline.py`. `WorkflowParser` will be imported and wired alongside `ResumeParser`/`ReadmeParser`.
- *Sub-task 2 (reproduction):* Already completed in Week 8. Reproduction commit confirmed zero CI/CD skills from `.github/workflows/*.yml`.
- *Sub-task 3 (parser implementation):* `workflow_parser.py` implemented with `parse()` accepting path strings (heuristic-based routing to `_parse_from_path()`), `yaml.safe_load` parsing, and `_extract_workflow_text()` extracting job names, step names, `uses:` references, and `run:` commands. Emits `"github actions"` header so `SkillExtractor.TOOLS` substring matching fires correctly.
- *Sub-task 4 (keyword expansion):* Identified exact insertion point in `skill_extractor.py` — adding `"github actions": 0.90`, `"pytest": 0.85`, `"deployment": 0.85` to `TOOLS`.
- *Sub-task 5 (unit tests):* `tests/unit/test_workflow_parser.py` populated with 7 tests covering single workflow, multiple workflows, missing directory, malformed YAML, empty file, action reference extraction, and metadata preservation. All mocks use `pathlib.Path.glob` and `yaml.safe_load` to avoid disk I/O.
- *Dependency resolved:* `pyproject.toml` confirmed as dependency source; `PyYAML&gt;=6.0` added to `dependencies` array. `pip install pyyaml` confirmed requirement already satisfied (6.0.3).
- *Baseline test run:* 54 pre-existing failures across unrelated modules (batch_processor, bias_detector, faithfulness_checker, keyword_search, output_parser, pii_scrubber, prompt_defense, readme_parser, readme_scorer, relevance_scorer, resume_parser, review_service, security, skill_extractor, structural_chunker, tech_detector). All 7 workflow_parser tests pass after parser implementation.
- *Full test suite run:* 53 pre-existing failures, 382 passed. Zero new failures introduced by workflow_parser, skill_extractor, or pipeline changes. All 7 workflow_parser tests pass.
- *Integration smoke test passed:* WorkflowParser + SkillExtractor correctly detect GitHub Actions, Docker, pytest, and deployment from a synthetic .github/workflows/ci.yml.

**Next steps:**
- Commit `workflow_parser.py` + `test_workflow_parser.py` + `pyproject.toml` update as first implementation commit.
- Create `ingestion/parsers/workflow_parser.py` and overwrite `tests/unit/test_workflow_parser.py` with corrected implementation.
- Modify `skill_extractor.py` TOOLS dict with three new CI/CD keywords.
- Modify `pipeline.py` with `WorkflowParser` import, instantiation, and `ingest_workflows()` method.
- Run `pytest tests/unit -v -m unit` to verify workflow_parser tests pass and no new failures introduced.
- Run `make check` equivalent (or `ruff check .` / `black --check .` if available) for linting/formatting before opening draft PR.
- Integration smoke test against Week 8 reproduction repo to confirm CI/CD skills now appear.
- Integration smoke test passed: WorkflowParser + SkillExtractor correctly detect Github Actions (0.90), Docker (0.95), Pytest (0.85), and Deployment (0.85) from a synthetic `.github/workflows/ci.yml`.

**Blockers:**
- `make` command not available in Windows PowerShell; running `pytest` directly as workaround. No other blockers.

**Pre-existing failures observed (baseline):**
- `test_skill_extractor.py::test_devops_tool_detection`
- `test_skill_extractor.py::test_javascript_detection`
- `test_skill_extractor.py::test_docker_compose_detection`
- `test_structural_chunker.py::test_document_with_no_headings`
- `test_tech_detector.py::test_node_modules_excluded`
- `test_tech_detector.py::test_build_directory_excluded`

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/677

**Branch:** `feat/14-github-actions-workflow-parsing`

**What you built:**
Added a `WorkflowParser` that discovers `.github/workflows/*.yml` files, extracts job names, step names, action references (`uses:`), and runner images (`runs-on:`), and returns a `ParseResult` consumable by `SkillExtractor`. Expanded `SkillExtractor.TOOLS` with `github actions`, `pytest`, and `deployment` keywords. Wired the parser into `IngestionPipeline` via `ingest_workflows()`.

**Tests added or updated:**
- `tests/unit/test_workflow_parser.py` — 7 tests covering single workflow, missing directory, multiple workflows, malformed YAML, empty files, action reference extraction, and metadata preservation.

**Self-review confirmation:**
- [x] `pytest tests/unit -v -m unit` passes for workflow_parser (7/7)
- [x] No new failures introduced (53 pre-existing, 382 passed)
- [x] `make check` — `make` unavailable on Windows PowerShell -- ran equivalent: `ruff check .` and `black --check .` pass; 
- [x] `make test-unit` — ran equivalent: `pytest tests/unit -v -m unit` passes (7/7 workflow_parser tests, 382 total passed, 53 pre-existing); `make` unavailable on Windows PowerShell

**Draft PR feedback received from:** None yet -- will update.

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review comments received on PR #677 as of Week 10 submission. Will update if feedback comes in during the grace period.

**How you responded:**
N/A — no feedback yet.

---

### Reflection

**What was harder than you expected?**
Getting the `BaseParser` interface right without an existing parser-specific unit test to copy from. I assumed `resume_parser.py` or `readme_parser.py` would have dedicated unit tests I could model `test_workflow_parser.py` after, but the only ingestion test was `test_batch_processor.py`, which tests embeddings, not parsing logic. That meant I had to reverse-engineer what a parser unit test should look like from the `BaseParser` interface and `skill_extractor.py` call sites alone. The actual YAML parsing was trivial; figuring out how to mock `pathlib.Path.glob` and `yaml.safe_load` so my tests didn't touch disk while still looking like the existing test style took longer than the implementation itself.

**What did you learn about working in a large codebase?**
Pre-existing test failures are ambient noise you have to learn to ignore without letting them desensitize you. There were 53 failures before I touched anything, and I had to run the full suite repeatedly to confirm my changes didn't add a 54th. That's completely different from my own projects where a red test means *I* broke something. Here, red tests are just the baseline, and the real skill is isolating your delta. I also learned that "follow the existing pattern" is easier said than done when the existing pattern is spread across three files and no one wrote the test you're supposed to copy.

**How did AI tools help — and where did they fall short?**
AI / Kimi v. 2.6 was indispensable for drafting the unit tests and the `PLAN.md`. Kimi v. 2.6 helped me map the `BaseParser` interface to what `SkillExtractor` actually consumes, and it generated the mock patterns for `pathlib` and `PyYAML` faster than I could have written them from scratch. Where it fell short was anything environment-specific. The chatbot kept suggesting `make test-unit` and `make check` commands that don't exist on Windows PowerShell, and it couldn't tell me whether `PyYAML` was already in `pyproject.toml` without me just... opening the file. LLMs by and large are fantastic for engineering prompts along the lines of  "what should this code look like?" and less so for contextual understanding: "what does this specific machine actually have installed?"

**What would you do differently if you started over?**
I would read `pyproject.toml` and `requirements.txt` in the first 10 minutes instead of assuming dependencies. I spent far too much time planning a `PyYAML` addition that was already there. I also would run the full test suite *before* writing any code, not after I had already drafted my parser. Knowing the 53 pre-existing failures upfront would have made my Week 8 reproduction cleaner and my Week 9 check-ins less anxious. Finally, I would have checked `__init__.py` in `ingestion/parsers/` immediately: finding out it was empty and that parsers are manually wired in `pipeline.py` changed my design, and I discovered that later than expected.

**What are you most proud of from this module?**
The integration smoke test. Getting `WorkflowParser` + `SkillExtractor` to correctly detect GitHub Actions (0.90), Docker (0.95), pytest (0.85), and deployment (0.85) from a synthetic `.github/workflows/ci.yml` on the first try after all the unit tests passed was the moment I knew the feature actually worked end-to-end. The PR is clean, the tests are thorough, and I did it all on Windows PowerShell without `make`. That counts for something.

---