## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now the ingestion pipeline only infers skills from import statements and README text, so contributors who set up and maintain CI/CD pipelines get no credit for that work — their DevOps experience is invisible to the skill extractor. This issue asks for a new parser that reads `.github/workflows/*.yml` files in a repo and infers skills like GitHub Actions, Docker, pytest, and deployment from the workflow configuration (jobs, steps, actions used, etc.). The fix touches the ingestion pipeline: a new `ingestion/parsers/workflow_parser.py` module plus changes to `ingestion/parsers/skill_extractor.py` to wire the new parser's output into the overall skill extraction results. Estimated effort is 6–10 hours, and it's labeled tier-3 since it involves adding a new architectural piece to the ingestion/skill-detection system rather than a small isolated fix.

**Branch name:** feat/14-github-action-parser-for-skills

**Setup confirmation:** [x] (https://github.com/ascherj/pathreview/issues/14) App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger