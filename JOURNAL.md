## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/FahmidaAz/pathreview/commit/4fe7555

**Reproduction summary:**
Ran the existing test suite for `tests/unit/test_skill_extractor.py` and
confirmed 4 tests fail exactly as the issue describes. Also manually
reproduced via the Python shell using the exact repro snippet from the
issue — `extract_skills()` returned `[]` for JavaScript text and `['React']`
(no TypeScript) for TypeScript text.

**PLAN.md link:** https://github.com/FahmidaAz/pathreview/blob/fix/148-skill-extractor-js-ts-detection/PLAN.md

**Walkthrough video (recommended):** (leave blank if you don't record one)

**Blockers or open questions:**
Need to decide exactly how many distinct JS/TS keyword matches should be
required before flagging a language, to avoid false positives on
Python-only text that happens to use `class`/`async`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full fix in `ingestion/parsers/skill_extractor.py` per PLAN.md:
JS/TS keyword-based detection using the previously-unused JS_TS_KEYWORDS set,
TypeScript-specific syntax indicators for correct labeling, and Dockerfile/
docker-compose syntax detection in `_detect_tools()`. All 4 target tests
(`test_javascript_detection`, `test_text_with_typescript_files`,
`test_devops_tool_detection`, `test_docker_compose_detection`) now pass.

**Next steps:**
Run `make check` and `make test-unit` for a final confirmation, write the PR
description, and open the pull request against `ascherj/pathreview`.

**Blockers:**
None. Note: `make check` surfaced ~180 pre-existing lint errors and
`make test-unit` surfaced 49 pre-existing test failures across unrelated
files (other students' curated issues) — confirmed my changed file
(`skill_extractor.py`) is clean on all three checks (ruff/black/mypy) and
introduces no new test failures.
### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/487

**Branch:** fix/148-skill-extractor-js-ts-detection

**What you built:**
Fixed `extract_skills()` in `ingestion/parsers/skill_extractor.py` to detect JavaScript/TypeScript from keyword and syntax patterns (not just filenames/imports), and to detect Docker/docker-compose usage from Dockerfile/YAML syntax even when the literal word "docker" never appears.

**Tests added or updated:**
No new tests added — the 4 existing tests named in issue #148 (`test_javascript_detection`, `test_text_with_typescript_files`, `test_devops_tool_detection`, `test_docker_compose_detection`) already defined the target behavior and now all pass.

**Self-review confirmation:** [x] make check passes (clean on changed file; confirmed via ruff/black/mypy)  [x] make test-unit passes (no new failures; 49 pre-existing failures unrelated to this change, documented in PR)

**Draft PR feedback received from:** none yet