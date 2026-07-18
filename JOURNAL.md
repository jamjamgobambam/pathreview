## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
Currently, `SkillExtractor` (`ingestion/parsers/skill_extractor.py`) infers a developer's skills only from source code, import statements, and README, so DevOps practices like CI/CD pipelines, containerization, and automated deployment go completely undetected even when a candidate's repo has a working `.github/workflows/*.yml` pipeline. There is no parser in `ingestion/parsers/` that reads GitHub Actions workflow YAML, so signals like `uses: docker/build-push-action`, `pytest` test steps, or deploy jobs never make it into the skill graph. A successful fix adds a `workflow_parser.py` that parses `.github/workflows/*.yml` into structured data (triggers, jobs, actions used, run commands) and extends `skill_extractor.py` to infer skills such as "GitHub Actions," "Docker," "pytest," and "deployment" from that structure.

**Branch name:** https://github.com/sindhunaydu/pathreview/tree/feat/14-github-actions-parser

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger