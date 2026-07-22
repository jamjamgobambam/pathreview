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
