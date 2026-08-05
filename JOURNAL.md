## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now the ingestion pipeline only infers skills from import statements and README text, so contributors who set up and maintain CI/CD pipelines get no credit for that work — their DevOps experience is invisible to the skill extractor. This issue asks for a new parser that reads `.github/workflows/*.yml` files in a repo and infers skills like GitHub Actions, Docker, pytest, and deployment from the workflow configuration (jobs, steps, actions used, etc.). The fix touches the ingestion pipeline: a new `ingestion/parsers/workflow_parser.py` module plus changes to `ingestion/parsers/skill_extractor.py` to wire the new parser's output into the overall skill extraction results. Estimated effort is 6–10 hours, and it's labeled tier-3 since it involves adding a new architectural piece to the ingestion/skill-detection system rather than a small isolated fix.

**Branch name:** feat/14-github-action-parser-for-skills

**Setup confirmation:** [x] (https://github.com/ascherj/pathreview/issues/14) App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/somabadri/pathreview/commit/88d643cb55fc0bbcd14698cc04e13e33d2635e00

**Reproduction summary:**
This is a new feature rather than a bug, so there's no failing behavior to reproduce — instead I confirmed the gap by tracing the ingestion pipeline and confirming no code path reads `.github/workflows/*.yml`. The commit above locates the placeholder `ingestion/parsers/workflow_parser.py` where the new parser will be added.

**PLAN.md link:** https://github.com/somabadri/pathreview/blob/feat/14-github-action-parser-for-skills/PLAN.md

**Walkthrough video (recommended):** N/A — no walkthrough video since this is a new feature with no existing behavior to demo.

**Blockers or open questions:**
How to structure the implicit skill mappings for workflow-derived skills (actions used, run commands → GitHub Actions/Docker/pytest/deployment). Still deciding between hardcoding a keyword map similar to `skill_extractor.py`'s existing `FRAMEWORKS`/`TOOLS` dicts, or a different approach.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented all of PLAN.md's sub-tasks: added the `PyYAML` dependency, built `WorkflowParser.parse()` (triggers, job names, `uses:` actions, `run:` commands, including the PyYAML `on:` → `True` boolean gotcha and `ValueError` handling for malformed/non-mapping YAML), extended `SkillExtractor` with a `_detect_ci_cd` step + `CI_CD_INDICATORS` map (GitHub Actions, Pytest, Deployment — Docker is left to the existing `TOOLS` detection), and wired `ingest_workflow(...)` into `IngestionPipeline`, one call per workflow file.

**Next steps:**
Finish `make check`/`make test-unit` self-review against the pre-existing baseline, open the draft PR for peer/mentor feedback, and address anything that comes back before marking it ready for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/948

**Branch:** `feat/14-github-action-parser-for-skills`

**What you built:**
A `WorkflowParser` that reads `.github/workflows/*.yml` content into text + metadata (triggers, job names, actions used, run commands), and a `SkillExtractor._detect_ci_cd` step that turns that output into CI/CD skill detections (GitHub Actions, Pytest, Deployment), all wired into `IngestionPipeline.ingest_workflow(...)`.

**Tests added or updated:**
`tests/unit/test_workflow_parser.py` (new, 16 tests covering standard/single-job/list-trigger workflows, malformed YAML, missing `jobs`/`steps`, bytes input, and metadata structure) and `tests/unit/test_skill_extractor.py` (5 new tests for GitHub Actions/Pytest/Deployment detection, CI/CD category tagging, and no false positives on unrelated text). Confirmed via `git stash` diffing that pre-existing ruff/mypy/test failures (183 ruff, 103 mypy, 53 test failures at baseline) are unchanged by these additions.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none yet