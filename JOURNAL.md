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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Steps 1–3 of PLAN.md are implemented and committed. Content-based JavaScript
detection replaces the old `\b(import|require)\s+` regex with an anchored
`JS_SIGNALS` set — `require(...)` with or without a space, ES6
`import ... from '...'`, `export`, `const`/`let`, arrow functions, `function`
declarations, and `console.*`. Content-based TypeScript detection adds a
`TS_SIGNALS` set for `interface X {`, `type X =`, `enum X {`, primitive type
annotations, `: Promise<`, and `as` assertions. Docker detection moved off the
bare `"docker"` substring into `_detect_docker_content()`, which reads Dockerfile
directives and Compose structure. All four tests named in issue #148 now pass.

I resolved both Week 8 open questions. On the JS signal set: the guards hold —
plain prose, `import os` / `from typing import List`, and `from enum import Enum`
all stay clean, because the ES6 import pattern cannot cross a `;` or newline and
the structural TS patterns require their opening brace or `=`. On the Docker
threshold: I went with both options rather than choosing. A line-leading
uppercase `FROM` is trusted alone since it is the mandatory first instruction of
every Dockerfile, and every other directive needs at least one partner, so prose
like "Copy the text FROM the page and ADD it to your notes" is not misread.

**Next steps:**
Finish PLAN.md steps 4–5: expand the regression tests beyond the four issue
tests, re-run the full unit suite against the baseline I captured at `17768dc`,
and confirm no new lint/type errors. Then open the draft PR for peer review.

**Blockers:**
The repo does not pass `make check` or `make test-unit` as it stands — 53 failing
unit tests, 182 ruff errors, and 5 mypy errors before I touched anything — so I
recorded a baseline first and I am measuring against that rather than against
green. Local setup also needed work: `make setup` assumes a `.venv` that did not
exist, and the system Python is 3.9 while `pyproject.toml` requires ≥3.11, so I
built the venv with Homebrew Python 3.14.3.

---

### Check-in 2 (end of week)

**PR link:** _(to be filled in — branch is pushed and the PR body is ready; see
"PR status" below)_

**Branch:** `fix/148-skill-extractor-js-ts`

**What you built:**
The skill extractor now identifies JavaScript, TypeScript, and Docker from the
content itself rather than from filenames and literal substrings, so
`require('fs')`, a body of `interface`/typed declarations with no filename, and
Dockerfile or Compose content that never spells out "docker" are all detected.
TypeScript is treated as a superset of JavaScript: when both signal sets fire the
text is reported once, as TypeScript, with the JavaScript evidence folded in.
The public API, dataclass shape, return type, and confidence sort order are
unchanged.

**Tests added or updated:**
`tests/unit/test_skill_extractor.py`. The four tests named in the issue —
`test_javascript_detection`, `test_text_with_typescript_files`,
`test_devops_tool_detection`, `test_docker_compose_detection` — now pass, and I
added ten regression tests covering `require()` with and without a space,
arrow-function-only JavaScript, a `package.json` filename, a TypeScript type
alias with no filename, a `.ts` file with an empty body, TypeScript superseding
JavaScript when both fire, a lone Dockerfile `FROM`, Compose content with no
literal "docker", prose not being misdetected as code, and content detections
carrying evidence.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both boxes mean "introduces no new failures", per the pre-existing-failure
guidance. Neither command passes outright on this repo, so I captured a baseline
at the branch point (`17768dc`) before starting and compared against it:

| Command | Before | After | Delta |
|---|---|---|---|
| `make test-unit` | 53 failed / 375 passed | 49 failed / 389 passed | 4 issue tests fixed, 10 new tests, 0 new failures |
| `ruff check .` | 182 errors | 179 errors | −3, all in the files I touch |
| `black --check .` | 52 files to reformat | 50 files | −2, both files I touch |
| `mypy` | 5 errors | 5 errors | unchanged |

Both files I touch are now fully ruff-clean, black-clean, and mypy-clean. The 49
remaining test failures, 179 ruff errors, and 5 mypy errors are all pre-existing
and untouched by this change; they are documented in the PR description.

One pre-existing failure sits in the file I modified and I left it deliberately:
`test_database_technology_detection` raises `UnboundLocalError` from a typo on
line 138 (`for s in skill_names` should be `for s in result`). Fixing the typo
does not make the test pass — the input is `import psycopg2` and the extractor
has no driver-to-database mapping, so the `postgres`/`sql` assertion still fails.
That needs new psycopg2 → PostgreSQL detection, which is a different bug from
#148, so I scoped it out and flagged it in the PR.

**Draft PR feedback received from:** none — see below.

**PR status:**
The branch is pushed to `origin`. I was not able to open the PR from this
environment: the GitHub CLI is not installed and there is no authenticated
GitHub session available, so the PR still needs to be created by hand from the
prepared description, marked ready for review, and its link pasted into the
**PR link** field above. The Slack peer-review request and the course-portal
submission of
`https://github.com/ktran37/pathreview/tree/fix/148-skill-extractor-js-ts`
also still need to be done manually.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]