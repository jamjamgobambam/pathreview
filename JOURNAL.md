# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1 [ ] Tier 2 [x] Tier 3

**Problem summary:**
The ingestion pipeline currently infers a developer's skills from things like
import statements and README text, but it has no parser for `.github/workflows/*.yml`
files. That means CI/CD practices — setting up GitHub Actions, building Docker
images, running test suites in CI, deploying on merge — go completely
undetected, even though maintaining these workflows is a real signal of DevOps
skill. A successful fix adds a new `workflow_parser.py` under
`ingestion/parsers/` that implements the existing `BaseParser` interface,
reads workflow YAML files, and extracts skills like `GitHub Actions`, `Docker`,
`pytest`, and `deployment` (likely via `ingestion/parsers/skill_extractor.py`),
then registers the new parser in the ingestion pipeline.

**Branch name:** feat/14-github-workflow-parser

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

Selection Reasoning:

- **Part 1**: I completely understand the issue and have contributed to similar features in my job
- **Part 2**: I already contributed to open source and have expansive experience in large codebases
- **Part 3**: I read the `parsers/` flow and have sufficient understanding and confidence to implement the new feature
- **Part 4**: I have alot of time, the scope is realistic to me, and there are no blockers on the issue

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Y4dd/pathreview/commit/6d607cefb3de1dfc4f852c64fce077f6a7feb762

**Reproduction summary:**
Added `tests/unit/test_workflow_parser.py`, which imports the not-yet-existent
`ingestion.parsers.workflow_parser`. Running `pytest tests/unit/test_workflow_parser.py -v`
fails at collection with `ModuleNotFoundError: No module named 'ingestion.parsers.workflow_parser'`,
confirming the pipeline has no parser for `.github/workflows/*.yml` and therefore cannot detect
CI/CD skills.

**PLAN.md link:** https://github.com/Y4dd/pathreview/blob/feat/14-github-workflow-parser/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
ChromaDB requires scalar metadata values (str/int/float/bool), so the extracted `skills` cannot be
stored as a raw list, still deciding between a comma-joined string and boolean flags
(`has_docker`, `runs_pytest`, `has_deployment`). Also weighing whether to rely on `SkillExtractor`'s
substring matching (which over-matches, e.g. `git` inside `github`) versus inspecting structured
`uses:`/`run:` values directly in the parser.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All implementation sub-tasks from PLAN.md are complete. Added `ingestion/parsers/workflow_parser.py`
(`WorkflowParser`), which parses workflow YAML and detects GitHub Actions, Docker, pytest, and
deployment structurally from the workflow's triggers/jobs/steps; wired it into
`IngestionPipeline.ingest_workflow()` and routed `"workflow"` sources to the structural chunker;
declared `pyyaml` / `types-pyyaml`; and extended `tests/unit/test_workflow_parser.py` from the 4
reproduction tests to 15 (edge cases: empty/whitespace input, non-workflow YAML, malformed YAML, the
`on:`-key YAML 1.1 gotcha, matrix builds, reusable job-level `uses:`, ChromaDB-scalar metadata, and
`SkillExtractor` reuse). All 15 pass.

Resolved both Week 8 open questions: skills are serialized to a comma-joined string plus boolean
flags (ChromaDB-safe), and the parser does its own structural detection rather than relying on
`SkillExtractor`'s substring matching — `SkillExtractor` is still called for supplementary signal
(`extracted_skills`), honoring the issue's "reuse it" note without depending on it.

**Next steps:**
Gather peer/mentor feedback on the draft PR, address it, and mark the PR ready for review by the end
of the week.

**Blockers:**
None. The repo has documented pre-existing `make check` / `make test-unit` failures (53 failing unit
tests, ~103 mypy errors — all pre-existing); this change introduces no new failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/887 (open, marked ready for review)

**Branch:** `feat/14-github-workflow-parser`

**What you built:**
A `WorkflowParser` for `.github/workflows/*.yml` that detects CI/CD and DevOps skills (GitHub
Actions, Docker, pytest, deployment) structurally from the workflow's triggers, jobs, and steps, and
reuses the existing `SkillExtractor` for supplementary signal. It is wired into the ingestion
pipeline as a new `workflow` source type with structural chunking.

**Tests added or updated:**
`tests/unit/test_workflow_parser.py` — 15 unit tests covering the `ParseResult` shape, the four #14
skills, bytes/invalid input, empty/whitespace, non-workflow and malformed YAML, the `on:`-key gotcha,
matrix builds, reusable job-level `uses:`, ChromaDB-scalar metadata, and `SkillExtractor` reuse.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Per the Week 9 pre-existing-failures rule, "passes" = introduces no new failures. Both commands have
documented pre-existing failures in this repo; this change adds none, and the new/edited files are
ruff-, black-, and mypy-clean. Details in the PR's Notes for Reviewers.)

**Draft PR feedback received from:** None — the PR did not receive a formal peer/mentor review this
cycle. The approach was discussed at team standups (where I shared the PLAN.md), but no PR-level
review was obtained.
