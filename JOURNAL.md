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
stored as a raw list — still deciding between a comma-joined string and boolean flags
(`has_docker`, `runs_pytest`, `has_deployment`). Also weighing whether to rely on `SkillExtractor`'s
substring matching (which over-matches, e.g. `git` inside `github`) versus inspecting structured
`uses:`/`run:` values directly in the parser.
