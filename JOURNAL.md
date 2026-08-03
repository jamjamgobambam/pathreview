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
- [ ] `make check` — not run (Windows PowerShell, `make` unavailable)
- [ ] `make test-unit` — not run (Windows PowerShell, `make` unavailable)

**Draft PR feedback received from:** None yet -- will update.

---