## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The system currently misses valuable CI/CD and DevOps skills (like GitHub Actions, Docker, pytest, or deployment tasks) because they typically do not appear in standard `import` statements or README text. To fix this, a new `workflow_parser.py` is needed within the `ingestion/parsers/` directory. A successful implementation will read `.github/workflows/*.yml` files, infer these DevOps skills, and integrate seamlessly with `skill_extractor.py` to ensure users get credit for maintaining CI/CD pipelines.

**Branch name:** feat/14-github-actions-parser

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Builder106/pathreview/commit/d04a3dd0b803c77d5801973e32a4605b69833616

**Reproduction summary:**
I added a new failing unit test in `test_skill_extractor.py` that verifies the `SkillExtractor` is currently unable to extract CI/CD skills (e.g., GitHub Actions, pytest) from standard `.github/workflows/*.yml` workflow definitions. This proves that parsing support for workflow files is missing.

**PLAN.md link:** https://github.com/Builder106/pathreview/blob/feat/14-github-actions-parser/PLAN.md

**Walkthrough video (recommended):** [Not recorded yet, but repository is updated with the required deliverables]

**Blockers or open questions:**
`pyyaml` is not currently in `pyproject.toml`. I will need to clarify if it is acceptable to add it as a new dependency to parse YAML properly, or if a robust regex-based extraction mechanism should be used instead.
