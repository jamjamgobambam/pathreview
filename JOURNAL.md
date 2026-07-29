# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The skill extractor in the ingestion pipeline is supposed to look at source
text and report which languages, frameworks, and tools a candidate has used,
but its JavaScript/TypeScript detection almost never fires. In
`ingestion/parsers/skill_extractor.py`, `_detect_languages()` only flags JS when
the filename ends in `.js`/`.ts` or when the text matches `\b(import|require)\s+`
— so a real call like `require('fs')` (no space before the paren) slips through,
and TypeScript is only ever labeled from a `.ts` filename, never from actual TS
syntax such as `interface` or type annotations. As a result the extractor
returns an empty or Python-only list for clearly JS/TS code, and several unit
tests (`test_javascript_detection`, `test_text_with_typescript_files`) fail. A
successful fix makes detection content-based — recognizing JS/TS from
`require(...)` calls, `export`/`const`/arrow-function/`async` usage, and TS-only
signals like `interface` and typed declarations — so the four failing tests pass
without breaking the existing Python detection.

**Branch name:** fix/148-skill-extractor-js-ts

**Setup confirmation:** [ ] App runs locally at localhost:5173
<!-- Pending: this machine has no Docker installed and no .env yet. To confirm:
     install Docker Desktop, `cp .env.example .env` and add OPENROUTER_API_KEY,
     then `docker compose up -d && make setup && make run`, and check the box. -->

**Cohort ledger:** [ ] Issue added to cohort ledger
<!-- Pending: add name + GitHub username (ktran37) + issue #148 on your
     section's tab of the cohort ledger, then check this box. -->

### "Is this right for me?" checklist — scope reasoning

- **Tier 1 / good first issue:** Yes — labeled `tier-1`, `good first issue`,
  `ingestion`. Appropriate as a first contribution to a large codebase.
- **Self-contained:** The change is confined to one module,
  `ingestion/parsers/skill_extractor.py` (the `_detect_languages` method), with
  no API, database, or frontend changes required.
- **Clear definition of done:** Four named failing tests in
  `tests/unit/test_skill_extractor.py` (`test_javascript_detection`,
  `test_text_with_typescript_files`, `test_devops_tool_detection`,
  `test_docker_compose_detection`) define exactly when the fix is complete.
- **Reproducible:** The issue includes concrete repro snippets, and I can run
  the affected tests locally with `make test-unit`.
- **Estimated effort:** 2–3 hours per the issue label — realistic for the
  scope of extending the detection patterns.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ktran37/pathreview/commit/dd893af297afb902a1fd78e3a9e80c57f4dcc9cf

**Reproduction summary:**
Ran `python3 -m pytest tests/unit/test_skill_extractor.py -q` and confirmed the
four tests named in the issue fail — `test_javascript_detection`,
`test_text_with_typescript_files`, `test_devops_tool_detection`, and
`test_docker_compose_detection`. The extractor returns no JavaScript/TypeScript
skill for `require('fs')` or content-only TS (`interface`), and no Docker skill
for Dockerfile/compose content, because detection is filename- and
literal-substring-driven. I marked the exact buggy lines in
`ingestion/parsers/skill_extractor.py` with `BUG(#148)` comments in the
reproduction commit. (A fifth failure, `test_database_technology_detection`, is
an `UnboundLocalError` from a typo in the test itself on line 138 — a separate
pre-existing bug, not part of #148.)

**PLAN.md link:** https://github.com/ktran37/pathreview/blob/fix/148-skill-extractor-js-ts/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
Need to confirm the JS signal set (`const`, `=>`, `async`) is specific enough to
avoid false positives on non-JS prose, and decide the exact threshold for the
Docker content heuristic (single `FROM` directive vs. requiring ≥2 co-occurring
directives) before writing the fix in Week 9.
