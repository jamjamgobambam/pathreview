# Contribution Journal — Module 3

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The ingestion pipeline's skill extractor (`ingestion/parsers/skill_extractor.py`) is supposed to detect technologies from resume and portfolio text, but the JavaScript/TypeScript family is essentially invisible to it. The class defines a `JS_TS_KEYWORDS` constant that is never actually used — JS/TS detection relies only on the optional `filename` argument (which is `None` for free text) and an import regex that requires whitespace after the keyword, so real-world code like `require('fs')` never matches. The same class of bug affects Docker detection: `_detect_tools` only looks for the literal word "docker", so a Dockerfile (`FROM`/`RUN`/`EXPOSE`) or a docker-compose YAML is never recognized. A successful fix makes the four failing tests in `tests/unit/test_skill_extractor.py` pass by detecting JS/TS from language keywords and syntax in the text itself, and Docker from Dockerfile/compose structure — without changing the Python, database, or framework detection that already works. This matters because skill detection feeds the RAG feedback pipeline, so a portfolio full of JavaScript work currently gets reviewed as if those skills don't exist.

**Branch name:** `fix/148-skill-extractor-js-ts-detection`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Issue-fit checklist notes (scope reasoning)

- **Understanding:** I can reproduce the bug directly — `SkillExtractor().extract_skills('Wrote index.js using const arrow functions')` returns `[]`. I traced each of the four failing tests to a specific root cause (unused `JS_TS_KEYWORDS` set, filename-only detection, `\b(import|require)\s+` regex missing `require(`, and literal-word-only Docker matching).
- **Tier fit:** Tier 1 and my first contribution to a large codebase — the change lives in one implementation file plus its test file.
- **Codebase readiness:** I read the full implementation and test file. The parser `SkillExtractor` is imported only by its own tests (verified by grep), so the change is isolated and the tests define the acceptance contract. Note: there is a separate `SkillExtractor` agent tool in `agent/tools/` that this issue does *not* touch.
- **Scope and time:** Estimated 3–6 hours (keyword/regex logic plus tests) — realistic for the Week 8–9 window. Three other students have claimed the issue, which is on the low end for tier-1 issues in this cohort; claims are non-exclusive.
- **Blockers:** None. I verified that no open PR modifies `ingestion/parsers/skill_extractor.py` (PR #162 touches the tech detector, chunker, faithfulness checker, and PII scrubber — different files).
- **Extra finding while reading:** `tests/unit/test_skill_extractor.py:138` has a pre-existing bug of its own (`skill_names = [s.name for s in skill_names]` — a `NameError` from referencing the variable being defined). It's out of scope for #148 but worth flagging.

### Environment setup notes

Setup on Windows hit four stacked issues before `make setup` succeeded, all worth documenting:

1. Missing `.env` — the app's built-in default `DATABASE_URL` points at port 5432; copying `.env.example` to `.env` (which uses 5433) is required.
2. Port conflicts from other projects: a native Windows PostgreSQL service on 5432, plus leftover Docker containers from another project squatting 5433 and 6379 (they auto-start with Docker Desktop and had to be stopped).
3. The pathreview db container was first created while its port was taken, so it needed `docker compose up -d --force-recreate db` to bind correctly.
4. `scripts/seed_db.py` prints ✓/✗ characters that crash on the default Windows cp1252 console, masking real errors — running with `PYTHONUTF8=1 make setup` fixes it.

Verified working: frontend at localhost:5173 (HTTP 200), API docs at localhost:8000/docs, and a successful login with a seeded test account returning a JWT.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AdithNG/pathreview/commit/c050e23727f4ac8d3a56fc1e6919d08758048e40

**Reproduction summary:**
I reproduced the issue two ways in my local environment: by running
`pytest tests/unit/test_skill_extractor.py`, which fails 5 of 18 tests (the 4 named in the
issue plus one unrelated pre-existing test bug), and by calling `extract_skills()` directly
on the samples from the issue body. JavaScript text returns an empty list, TypeScript text
returns only `['React']`, and Dockerfile/compose text returns no Docker detection at all —
matching the reported behavior exactly.

**PLAN.md link:** https://github.com/AdithNG/pathreview/blob/fix/148-skill-extractor-js-ts-detection/PLAN.md

**Walkthrough video (recommended):** None — this deliverable is recommended but not graded, so I
put the time into the written reproduction and plan instead.

**Blockers or open questions:**
- `test_database_technology_detection` also fails, but it is **not** one of the four tests
  named in issue #148. It fails first on its own bug (`skill_names = [s.name for s in skill_names]`
  at line 138 — a `NameError`), and I confirmed that even after fixing that line the assertion
  still fails, because `psycopg2` is not in the `DATABASES` map (only `postgresql` is). That
  means it needs an implementation change of its own. I plan to leave it out of my PR and
  mention it in the PR description rather than expand scope, but I may ask the maintainer
  whether they'd prefer it included.
- I need to decide how strict the new JavaScript keyword matching should be. Detection that is
  too loose creates false positives (see the `import psycopg2` finding below); too strict and
  the issue's own sample text won't be detected.

### Reproduction steps and observed output

```
$ PYTHONUTF8=1 .venv/Scripts/python -m pytest tests/unit/test_skill_extractor.py -v
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_text_with_typescript_files
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_database_technology_detection
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_devops_tool_detection
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_javascript_detection
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_docker_compose_detection
5 failed, 13 passed in 1.30s
```

Calling the extractor directly (`SkillExtractor().extract_skills(text)`):

| Input | Expected | Observed |
|---|---|---|
| `Wrote index.js using const arrow functions and async/await callbacks` | JavaScript | `[]` |
| `Built app.tsx and types.ts with strict TypeScript interfaces` | TypeScript | `['React']` |
| `const fs = require('fs'); ... console.log(data)` | JavaScript | `[]` |
| `export interface User { id: string; }` (TS) | TypeScript | `['Python']` |
| `FROM python:3.9 / RUN pip install / EXPOSE 8000` (Dockerfile) | Docker | `['Python']` |
| `version: '3.8' / services: / build: .` (compose) | Docker | `[]` |

### Root causes confirmed during reproduction

All five located in `ingestion/parsers/skill_extractor.py`:

1. **`JS_TS_KEYWORDS` is dead code** (lines 30–41). I grepped the whole repo: the set is
   defined and never referenced. `PYTHON_KEYWORDS` is unused in the same way, but Python
   still gets detected through other signals, which is why only JS/TS visibly breaks.
2. **`require(` never matches.** `_detect_languages` uses `re.search(r"\b(import|require)\s+", text)`,
   which demands whitespace after the keyword, so `require('fs')` fails to match.
3. **TypeScript vs JavaScript is decided only by filename** (line 186:
   `lang = "TypeScript" if ".ts" in str(filename or "").lower() else "JavaScript"`). For free
   text with no filename — the normal case for resume/portfolio content — TypeScript can never
   be detected, even when the text says "TypeScript" and names `.ts` files.
4. **Docker is matched as a literal word only.** `_detect_tools` does `if tool in text_lower`,
   so a real Dockerfile (`FROM`/`RUN`/`EXPOSE`) or a compose file (`services:`/`build:`) is
   never recognized as Docker.
5. **False positive found while reproducing:** plain Python `import psycopg2` is currently
   reported as **JavaScript**, because the shared `\b(import|require)\s+` regex matches Python
   import statements too. So the current behavior is both missing real JS and inventing fake JS.

A sixth, related quirk: the Python type-annotation regex `:\s*(int|str|float|bool|list|dict)`
matches TypeScript's `: string` (because `str` is a prefix of `string`), which is why the
TypeScript sample above is misreported as Python.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1–5 of the seven in PLAN.md are done. I recorded the baseline first (step 1) and found
the repo has substantial pre-existing breakage — 53 failing unit tests and 182 ruff errors before I
touched anything — so I saved the sorted failure list to diff against later. For step 2 I added a
`JS_SYNTAX_PATTERNS` constant holding syntax Python does not share (`require(`, arrow functions,
`console.log(`, `import ... from '...'`, `export default`, and `const`/`let`/`var` declarations
with an assignment), and wired up `JS_TS_KEYWORDS` as supporting evidence rather than as the
primary signal. That decision came out of step 3: four of its ten entries (`import`, `async`,
`await`, `class`) are also Python keywords, so using it as the primary signal is exactly what makes
`import psycopg2` report JavaScript. Step 4 added text-based TypeScript detection in a new
`_detect_js_ts()` helper plus the missing `\b` on the Python annotation regex, and step 5 added
`_detect_docker()` for Dockerfile instructions and Compose service definitions.

All four tests named in the issue now pass, and I verified the fix against the exact reproduction
cases from the issue body plus three false-positive cases of my own.

**Next steps:**
Steps 6 and 7 — write the regression tests I specified in PLAN.md (especially the
`import psycopg2` guard, since that false positive is the main risk in my approach), then run the
full verification and diff the failure list against my baseline before opening the PR.

**Blockers:**
One, now resolved. The pre-commit `mypy` hook has no file filter, so it type-checks staged files
under `tests/`. No test module in this repo is annotated and `make typecheck` only covers
`api/ core/ ingestion/ rag/ agent/ safety/`, so the hook rejected *any* commit touching *any* test
file — 27 errors, 21 of them in test methods I did not write. Rather than annotate 24 methods
against the project's own convention (0 of 21 test files use annotations), I added
`exclude: ^tests/` to the hook so it matches the Makefile's documented scope. It is in its own
commit so it can be split out if the maintainer prefers.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/330

**Branch:** `fix/148-skill-extractor-js-ts-detection`

**What you built:**
The skill extractor now detects JavaScript and TypeScript from the text itself instead of relying
on a `filename` argument that is absent for free-form resume content: JavaScript is established
from syntax Python does not share, and TypeScript from type-level syntax, `.ts`/`.tsx` references,
or the language name. Docker is detected from Dockerfile instructions and Compose service
definitions rather than only from the literal word "docker". The fix also removes a false positive
I found while reproducing the issue, where plain Python `import` statements were reported as
JavaScript, and adds a word boundary to the Python type-annotation pattern so TypeScript's
`: string` is no longer counted as Python's `: str`.

**Tests added or updated:**
`tests/unit/test_skill_extractor.py` — seven new tests, taking the file from 18 tests to 25. Three
cover the new detection paths:
TypeScript detected from prose with no filename argument, JavaScript detected from ES6
`import ... from` / `export default` syntax, and Docker detected from a Dockerfile whose text never
contains the word "docker". Three are regression guards against false positives: `import psycopg2`
must not yield JavaScript, English prose using "let"/"run"/"function"/"class" must not yield
JavaScript, and a single capitalised word in prose must not be read as a Dockerfile. A seventh test
asserts that TypeScript's `: string` is no longer reported as Python.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both are true in the sense the contribution guidance defines for a repo with documented
pre-existing failures — my changes introduce no new failures:

| Check | Before | After |
|---|---|---|
| `pytest tests/unit -m unit` | 53 failed, 375 passed | 49 failed, 386 passed |
| `ruff check .` | 182 errors | 177 errors |
| `mypy` on the `make typecheck` paths | 5 errors in 4 files | 5 errors in 4 files (identical) |

Diffing the sorted failure lists shows zero new failures and exactly four tests fixed — the four
named in issue #148. Both files I changed pass ruff, black, and mypy individually. The remaining
49 failures and 177 ruff errors are pre-existing in other modules, and I documented them in the PR
description.

**Draft PR feedback received from:** None. I opened the PR ready for review rather than as a draft,
and have asked for a peer look in Slack. Any feedback that arrives will be recorded with my
response in the Week 10 section.

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has arrived. As of the end of Week 10, PR #330 has zero reviews, zero inline comments,
and zero conversation comments. I checked the PR's review and comment endpoints directly rather
than relying on GitHub notifications, so I am confident nothing was missed. This matches the
course note that reviewer feedback is not part of the Summer 2026 term, and it is also normal for
open source generally — the repository has over 150 open PRs against a single maintainer.

**How you responded:**
No response was required, but I did not treat the absence of review as the end of the work. In the
PR description I left two open questions under "Notes for Reviewers" that I would want a maintainer
to weigh in on: whether `JS_TS_KEYWORDS` was intended as the primary detection signal (I
deliberately demoted it to supporting evidence, which is a visible departure from how the issue
describes the root cause), and whether reporting both JavaScript and TypeScript for the same text
is desirable or whether TypeScript should suppress JavaScript the way the original code did. I also
flagged two things that belong in separate issues rather than in my PR: the `psycopg2` driver is not
mapped to PostgreSQL in the `DATABASES` dict, which is why
`test_database_technology_detection` still fails, and the pre-commit `mypy` hook blocks every
commit that touches a test file. If a reviewer disagrees with any of my judgement calls, the
implementation is isolated in `_detect_js_ts()` and `_detect_docker()` and would be
straightforward to change.

---

### Reflection

**What was harder than you expected?**
Getting the environment running was by far the hardest part, and none of the difficulty was in the
project's own code. My `make setup` failed with
`asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "pathreview"`,
and I hit that same error message twice for two completely different reasons: first because I had
never copied `.env.example` to `.env`, so the app used its built-in default of port 5432 where a
native Windows `postgres.exe` service was listening, and then again because a leftover container
from an unrelated project of mine was already bound to port 5433 — the exact port PathReview remaps
to in order to avoid conflicts. On top of that, `scripts/seed_db.py` prints ✓ and ✗ characters that
crash on the default Windows cp1252 console, so a `UnicodeEncodeError` was burying the real error
and making even successful runs exit non-zero until I ran everything with `PYTHONUTF8=1`. I had
budgeted my time for the fix and almost none for setup, and the ratio ended up being closer to the
reverse.

**What did you learn about working in a large codebase?**
The most useful thing I did all module was record a baseline before touching anything. The repo had
53 failing unit tests and 182 ruff errors before my first edit, so "does the suite pass" was
a meaningless question — I had to save the sorted failure list and diff against it afterwards to
prove I had fixed exactly four tests and broken nothing. Without that, my final run showing 49
failures would have looked like I had broken things. I also learned to check who calls the code
before changing it: grep showed the parser `SkillExtractor` is imported only by its own test file,
which told me the change was isolated and that its tests were the real contract. Relatedly, there
are two different classes named `SkillExtractor` in this repo — one in `ingestion/parsers/` and one
in `agent/tools/` — and reading the issue's file list carefully was the only thing that kept me in
the right one. Finally, matching local convention beat applying general best practice: when the
pre-commit `mypy` hook demanded type annotations on my new tests, I checked and found that 0 of 21
test files in the repo annotate anything, so annotating mine would have made my file the odd one
out.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and for the mechanical parts of verification. It let me map six
subsystems in one session instead of a week, and it caught things I would not have thought to look
for — that the entire review pipeline in `core/services/review_service.py` is hardcoded
placeholders, that the safety layer is never actually wired into the request flow, and that
`GET /health` returns 503 unconditionally because it passes a raw SQL string to `db.execute()`.
Knowing all of that up front kept me away from issues that looked small but depended on a pipeline
that does not run end to end. Where it fell short was judgement about intent. The issue frames the
root cause as "`JS_TS_KEYWORDS` is defined but never used," and the obvious move — and the one an
AI will happily implement, because it explains what code *does* rather than what it *should* do —
is to wire that constant up as the primary detection signal. Doing that literally reintroduces a
bug, because four of its ten entries (`import`, `async`, `await`, `class`) are Python keywords, so
`import psycopg2` gets reported as JavaScript. I only found that by actually running the extractor
on Python input and reading the output, not by reasoning about the code. The other thing AI could
not tell me was the repo's social reality: that a neighbouring test in the file I had to edit was
broken in a way that made ruff reject every commit, and that the fix for it was out of my issue's
scope.

**What would you do differently if you started over?**
Three things. First, I would set up and verify the environment before selecting an issue instead of
after — I chose #148 while my `make setup` was still failing, and if setup had turned out to be
genuinely broken I would have burned selection time twice. Second, I would check for port conflicts
from my own other Docker projects at the very start, since that one habit would have saved most of
a night. Third, and most importantly for the process, I would open the draft PR early in the week
instead of opening a finished PR at the deadline. I got no peer feedback at all, which is entirely
my own sequencing, and I had two genuine design questions that a second pair of eyes would have
settled faster than my own reasoning did. I would also probably pick a less crowded issue: five
other students had claimed #148 by the time I finished, and a less contested one would likely have
meant more useful discussion.

**What are you most proud of from this module?**
The bug nobody asked me to find. The issue listed four failing tests, and the fastest path to a
green suite was to make those four pass and stop. But while reproducing the problem I ran the
extractor on plain Python code and saw `import psycopg2` come back as
`['Python', 'JavaScript']` — a false positive that no test covered and the issue never mentioned,
caused by the same regex the issue was complaining about. Fixing it changed my whole approach: it
is why I used `JS_TS_KEYWORDS` as supporting evidence instead of as the primary signal, and why
three of my seven new tests are regression guards for inputs that must *not* be detected rather than
inputs that must be. I am more proud of that than of the four tests I was asked to fix, because it
came from actually understanding the code instead of satisfying the test names in the issue.


