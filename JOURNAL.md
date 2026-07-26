## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
Currently, `SkillExtractor` (`ingestion/parsers/skill_extractor.py`) infers a developer's skills only from source code, import statements, and README, so DevOps practices like CI/CD pipelines, containerization, and automated deployment go completely undetected even when a candidate's repo has a working `.github/workflows/*.yml` pipeline. There is no parser in `ingestion/parsers/` that reads GitHub Actions workflow YAML, so signals like `uses: docker/build-push-action`, `pytest` test steps, or deploy jobs never make it into the skill graph. A successful fix adds a `workflow_parser.py` that parses `.github/workflows/*.yml` into structured data (triggers, jobs, actions used, run commands) and extends `skill_extractor.py` to infer skills such as "GitHub Actions," "Docker," "pytest," and "deployment" from that structure.

**Reasoning:** 
I have a particular interest in CI/CD and DevOps work, and issues involving GitHub Actions are a great fit for me. I'm an experienced software engineer comfortable taking on Tier 3 issues and I'm interested in desiging and building new parser module + integration into an existing extraction pipeline.

**Branch name:** https://github.com/sindhunaydu/pathreview/tree/feat/14-github-actions-parser

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (added in this commit, see `tests/unit/test_workflow_parser_reproduction.py`)

**Reproduction summary:**
Added `tests/unit/test_workflow_parser_reproduction.py`, which confirms `ingestion.parsers.workflow_parser` does not exist and shows that `SkillExtractor.extract_skills` cannot detect "GitHub Actions," "Pytest," or "Deployment" from a real GitHub Actions workflow YAML — it only matches the literal word "docker" in text, with no structural parsing of jobs/steps. Both tests pass today, which is expected: they document the current (missing) behavior.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
Still deciding whether workflow ingestion should be its own `source_type` in `ingestion/pipeline.py` or folded into the existing "repo" source type — see Risks & unknowns in PLAN.md.
