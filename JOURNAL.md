## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The system currently misses valuable CI/CD and DevOps skills (like GitHub Actions, Docker, pytest, or deployment tasks) because they typically do not appear in standard `import` statements or README text. To fix this, a new `workflow_parser.py` is needed within the `ingestion/parsers/` directory. A successful implementation will read `.github/workflows/*.yml` files, infer these DevOps skills, and integrate seamlessly with `skill_extractor.py` to ensure users get credit for maintaining CI/CD pipelines.

**Branch name:** feat/14-github-actions-parser

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
