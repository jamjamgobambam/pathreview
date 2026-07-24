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