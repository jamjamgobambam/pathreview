# Journal

## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/147](https://github.com/ascherj/pathreview/issues/147)

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`ResumeParser._detect_sections()` (in `ingestion/parsers/resume_parser.py`) is supposed to scan a resume's extracted text and report which standard sections it finds — Education, Skills, Experience, and so on — so the rest of the ingestion pipeline knows what structure the document has. Its regex patterns are anchored to the very start of a line, with no tolerance for leading whitespace before a header. PDF-extracted text and indented markdown resumes commonly have that leading whitespace, so `detected_sections` comes back completely empty even when the sections are clearly present to a human reader. A correct fix makes header detection tolerant of leading whitespace without introducing false positives, so indented and unindented resumes are scored the same, and the existing test suite (plus the indented-text case from the issue) passes.

**Branch name:** `fix/147-resume-section-whitespace`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Selection notes — scope reasoning

I'm new to contributing to a project this size and have never had a PR merged into an unfamiliar codebase before, so I deliberately picked Tier 1 rather than reaching for something more architecturally ambitious. My goal for this module isn't to prove I can handle the hardest issue available — it's to actually practice the full loop the module is teaching: read and understand a large, unfamiliar codebase, choose a well-scoped bug to work, investigate and explain the bug clearly, propose a fix, and back it with a new test that guards the specific edge case so a future change doesn't silently reintroduce the same bug. A Tier 1 issue lets me go deep on that full loop on a small surface area instead of spending most of my time just tracing how services connect.

Why this issue specifically fits my "is this right for me" check:

- **Contained blast radius.** It's scoped to one file, `ingestion/parsers/resume_parser.py`, with no changes needed in the API, agent, or frontend layers — small enough that I can hold the whole relevant context in my head while I learn how the ingestion pipeline is put together.
- **Objectively verifiable.** The bug has a precise, reproducible trigger (indented input text), and the issue body already includes a minimal repro script and names the three failing tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections` in `tests/unit/test_resume_parser.py`), so I can check my understanding — and later my fix — against a concrete pass/fail signal instead of guessing at "done."
- **No hidden design decisions.** It's a regex/string-handling bug, not an architecture choice — there's a clear right answer, so I can focus my first contribution on process (root-causing the bug, writing a correct fix, adding a regression test for the leading-whitespace edge case) rather than also having to make judgment calls I'm not yet equipped for.

I confirmed this by actually reproducing the bug locally (not just reading the issue): `_detect_sections()` returns `[]` for indented text exactly as described, and all three named tests fail. I also found the same anchoring bug independently breaks `_strip_markdown()` (2 more failing tests not mentioned in the issue: `test_parse_markdown_resume`, `test_strip_markdown_syntax`) — worth accounting for when I write the fix and plan next week, since the full correct fix is slightly bigger than the issue body alone suggests.

### Setup notes

- Forked to `bnguyen142/pathreview`; `origin` is my fork, `upstream` is set to `ascherj/pathreview`. Note: this repo's own README uses an older clone URL, `jamjamgobambam/pathreview` — that resolves to the same GitHub account (confirmed via `gh repo view`: identical owner ID and issue list), it's just a redirected handle, not a separate fork.
- **Backing services (Postgres, Redis, ChromaDB) run via Apple's native `container` tool + the third-party `container-compose` bridge, not Docker Desktop.** Both installed via Homebrew (`brew install container container-compose`). `container-compose` reads the existing `docker-compose.yml` as-is — no changes needed to the compose file itself, since all three images (`postgres:16-alpine`, `redis:7-alpine`, `chromadb/chroma`) publish native arm64 builds.
  - Chose Apple's `container` tool partly to try newer tooling, and partly to avoid Docker Desktop's Rosetta-based amd64 emulation path, since all three service images publish native arm64 builds anyway.
  - Rough edge encountered: first-time `container system start` needed an interactive kernel download confirmation (`kata-containers` kernel) — had to auto-confirm it non-interactively. Otherwise setup was a straightforward drop-in replacement for `docker compose up -d`.
  - Postgres also needed one fix beyond plain `docker-compose.yml`: `initdb` refused to start because the container runtime's volume mount left a `lost+found` directory at the mount root, which Postgres treats as "not empty." Fixed by setting `PGDATA` to a subdirectory of the mount (`/var/lib/postgresql/data/pgdata`) instead of the mount root itself — a one-line addition to the `db` service's environment in `docker-compose.yml`.
- Confirmed `make run` serves the frontend at `http://localhost:5173` (200, correct app shell/title) and the API at `http://localhost:8000` (Swagger docs reachable). The `/health` endpoint itself reports Postgres/Redis as unhealthy, but that's a separate known bug (issues #154, #155) — verified both services directly (`SELECT 1` over asyncpg, `redis.ping()`) and they're genuinely up.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [1f793a1](https://github.com/bnguyen142/pathreview/commit/1f793a1)

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_resume_parser.py -v` locally. Result: **6 failed, 5 passed**. Five of the six failures were pre-existing (predicted in the Week 7 investigation); the sixth (`test_parse_pdf_with_indented_sections`) is a new regression test I added this week specifically to cover the PDF ingestion path:

```text
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_single_column_resume_text
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_resume_no_work_experience
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_pdf_with_indented_sections
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_markdown_resume
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_detect_sections
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_strip_markdown_syntax
```

The first three (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) are named directly in issue #147. `test_parse_markdown_resume` and `test_strip_markdown_syntax` fail for the same root cause (regex patterns in `_strip_markdown()` anchored to `^`/`\n` with no leading-whitespace tolerance) but aren't mentioned in the issue body. `test_parse_pdf_with_indented_sections` is new: none of the issue's named tests exercise `_parse_pdf()` at all, even though the issue specifically calls out PDF-extracted text as the real-world trigger — so I added a test mocking `PdfReader` (following the existing `test_parse_multipage_pdf` pattern) with indented `Experience:`/`Education:`/`Skills:` headers, confirming the exact same bug reproduces through the PDF code path, not just markdown/plain-text.

Full-suite baseline (`.venv/bin/pytest tests/unit -v -m unit`, run before making any production code change): **54 failed, 375 passed**. Only 6 of those 54 belong to `test_resume_parser.py` — the other 48 are pre-existing failures across ~15 unrelated modules, unrelated to this issue.

**Exact keyword misses observed:**

`_detect_sections()` checks each of the 13 known keywords in `SECTION_HEADERS` (resume_parser.py:9-23) against the whole document independently. The keywords actually exercised by these test fixtures are `experience`, `education`, and `skills`. For each, all 4 patterns (resume_parser.py:134-138) require the keyword immediately after `^` or `\n`, with zero whitespace tolerance before it:

| Raw header line (repr, whitespace visible) | Pattern that should match | Exact miss |
| --- | --- | --- |
| `'    Experience:'` (4-space indent, `sample_resume_text` fixture) | `` ^experience\s*[:\|-] `` | `^` requires `e` as the very next character; finds a space instead |
| `'        Education:'` (8-space indent, `test_parse_resume_no_work_experience`) | `` ^education\s*[:\|-] `` | same — 8 spaces sit between `^` and `e` |
| `'        Skills: Python, JavaScript'` (8-space indent, `test_detect_sections`) | `` ^skills\s*[:\|-] `` | same — regex has no allowance before `s` |

`_strip_markdown()`'s single header regex (resume_parser.py:102, `r"^#+\s+"`) has the identical miss on `'        # Header'` and `'        ## Contact'` / `'        ## Experience'` / `'        ## Skills'` (`test_strip_markdown_syntax`, `test_parse_markdown_resume`): `^#+` requires `#` immediately at line-start, finds a space instead, so the `#`/`##` is never stripped.

**Confirmed the bug also reproduces through the PDF path:** none of the 5 failing tests actually exercise `_parse_pdf()` — they're all markdown/plain-text input. Ran a one-off diagnostic (mocking `PdfReader` the same way `test_parse_multipage_pdf` does, with a page returning indented `Experience:`/`Education:`/`Skills:` headers) and confirmed `parser.parse(pdf_bytes)` also returns `detected_sections: []`. This matters because the issue names PDF-extracted text as the real-world trigger — this confirms the fix needs a dedicated PDF-path regression test (see `PLAN.md` Plan step 5), not just coverage through the markdown path.

**PLAN.md link:** [PLAN.md](https://github.com/bnguyen142/pathreview/blob/fix/147-resume-section-whitespace/PLAN.md)

**Walkthrough video (recommended):** [Week 8 walkthrough](https://youtu.be/I53GGVbN0T4)

**Blockers or open questions:**
Hit and resolved one blocker this week: committing the new `test_parse_pdf_with_indented_sections` test tripped the `mypy` pre-commit hook, which flagged 12 missing-type-annotation errors in `test_resume_parser.py` — 11 of them pre-existing, in tests I didn't write. Root cause: `make typecheck` (the Makefile target `CONTRIBUTING.md` points to) excludes `tests/` entirely, so this file's lack of type annotations had never been caught before, while the pre-commit hook has no such exclusion. Fixed by adding proper type annotations to all 12 functions, plus two `# type: ignore[arg-type]` comments on tests that intentionally pass invalid types to verify runtime validation. Verified all three hooks (ruff, black, mypy) now pass, and the actual test results are unchanged (6 failed / 5 passed). Documented as a general risk in `PLAN.md` for Week 9.

Remaining open question for the fix itself: how to make the regex leading-whitespace-tolerant without introducing false positives (e.g. a bullet point or code snippet that happens to start with a section-header word after indentation) — captured in `PLAN.md`'s Risks & Unknowns.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Format note:** This cohort's mid-week check-in was done live during Tuesday's class session, in small groups with classmates, rather than as a written submission by Wednesday — per instructor guidance that check-in cadence/format can vary by cohort. Recording the same content here in writing as well, so Check-in 1 still stands on its own for grading.

**Current progress:**
Responded to Week 7/8 grader feedback before starting implementation: `PLAN.md`'s risk analysis had deferred two unknowns that were cheaply testable rather than resolving them. Closed both — generated a real indented PDF and confirmed `pypdf`'s `extract_text()` returns plain ASCII spaces only (no `\xa0`), and re-examined the CRLF mechanics to confirm a stray `\r` never lands in the leading-whitespace gap the fix targets. Both are documented with method and reasoning in `PLAN.md`'s Risks & Unknowns section.

Implemented the fix per `PLAN.md` steps 1-2: added `[ \t]*` leading-whitespace tolerance to `_strip_markdown()`'s header regex (resume_parser.py:102) and all four `_detect_sections()` patterns (resume_parser.py:134-138). Added the negative-case regression test from step 4 (`test_detect_sections_tabs_and_no_false_positive`) covering tab-indentation and the false-positive guard (an indented bullet mentioning a section keyword mid-sentence must not register as a header).

Verified: `test_resume_parser.py` now 12/12 passing (up from the Week 8 baseline of 5/11). Full suite: 48 failed / 382 passed — the same 48 pre-existing failures from the Week 8 baseline, unchanged; the only movement is the resume-parser tests going green plus the one new test. Confirmed via `git stash` that none of these pre-existing failures are affected by this change.

Also surfaced and explicitly scoped out a repo-wide `make check`/`make typecheck` breakage: `pyproject.toml` pins `numpy>=1.26.0` with no upper bound, current installs resolve to numpy 2.5.1 (stubs require Python 3.12+ syntax), and `[tool.mypy]` still targets `python_version = "3.11"` — so mypy crashes before checking anything. Confirmed identical on `main` via `git stash` (predates this branch), and confirmed via a scoped `--python-version 3.12` run that unblocking it would surface 103 pre-existing type errors across 26 unrelated files. Documented in `PLAN.md`'s "Out of scope" section rather than absorbed into this fix, per the pre-existing-failures guidance for Week 9: `make test-unit` is clean, and `make check`'s failure is pre-existing and unrelated. Confirmed this out-of-scope call with tech fellow Raeesah Iram during Tuesday's in-class small group — touching the 26 unrelated files needed to fix it is not appropriate scope for this Tier 1 PR (full reasoning in `PLAN.md`'s "Out of scope" section).

**Next steps:**
Run `make check`'s lint/format steps in isolation to confirm the diff itself is clean (separate from the broken typecheck step). Review `docs/CONTRIBUTING.md` for branch naming/commit message/docstring conventions before committing. Open a draft PR early this week for peer/mentor review per the Week 9 guidance, with a PR description that documents the pre-existing `make check` failures and states this change doesn't affect them. Address any review feedback, then mark ready for review and complete Check-in 2.

**Blockers:**
None blocking progress. Flagging the `make check`/`make typecheck` repo-wide breakage here so it doesn't read as an oversight in Check-in 2 — per the Week 9 "pre-existing failures" guidance, the self-review checkbox will reflect that `make test-unit` passes and `make check`'s failure is documented as pre-existing and unaffected by this change, not a literal clean pass.

---

### Check-in 2 (end of week)

**PR link:** [#525](https://github.com/ascherj/pathreview/pull/525)

**Branch:** `fix/147-resume-section-whitespace`

**What you built:**
Fixed issue #147: `_detect_sections()`'s four regex patterns and `_strip_markdown()`'s header-stripping regex were all anchored directly to `^`/`\n` with no tolerance for leading whitespace, so indented section headers (a common artifact of PDF-extracted text and indented markdown) were silently skipped. Added `[ \t]*` leading-whitespace tolerance to all five patterns so indented headers are detected/stripped the same as flush-left ones, without introducing false positives for section keywords appearing indented mid-sentence.

**Tests added or updated:**
`tests/unit/test_resume_parser.py` — added `test_detect_sections_tabs_and_no_false_positive`, covering tab-indented headers plus a negative case (an indented bullet mentioning a section keyword mid-sentence must not be detected as a header). Also relies on `test_parse_pdf_with_indented_sections`, added during Week 8 reproduction, which verifies the fix through the PDF ingestion path specifically. Full file: 12/12 passing (up from 5/11 baseline). Full suite: 48 pre-existing failures unchanged, 382 passed (up from 375, accounting for the 6 resume-parser tests going green plus the 1 new test).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(`make test-unit` passes cleanly. `make check`'s typecheck step fails repo-wide due to a pre-existing numpy/mypy version-drift issue, confirmed via `git stash` to predate this branch and unrelated to this change — documented in `PLAN.md`'s "Out of scope" section and the PR's Notes for Reviewers. Per the Week 9 guidance on pre-existing failures, "passes" here means this change introduces no new failures, which is confirmed.)*

**Draft PR feedback received from:** None — per the Week 9 lecture (Solution Implementation, slide 21), this cohort doesn't do code review this term; self-reviewed against the "Seven Conditions for Done" instead (fix works, existing tests pass, new tests written, follows codebase conventions, linter/pre-existing-failure state documented, docstrings updated, PR description written).

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback came in. Per the Week 9 lecture's explicit note, reviewer feedback isn't a feature this term (Su26) — so this isn't a case of "no one got to it," it's expected by design. [PR #525](https://github.com/ascherj/pathreview/pull/525) has no comments as of this writing.

**How you responded:**
N/A — nothing to respond to. Self-review substituted for reviewer feedback throughout Week 9: I ran the "Seven Conditions for Done" checklist against my own diff, and separately confirmed one specific scope call (leaving the numpy/mypy `make check` breakage out of the PR) with a tech fellow rather than just deciding it alone.

---

### Reflection

**What was harder than you expected?**
Not the regex fix itself — that part was small and mechanical once I'd traced the root cause. What actually took time was everything adjacent to it. The repo's pre-commit hook blocked me twice on issues I didn't introduce: once in Week 8 (12 missing type annotations in a test file I hadn't written most of), and again this week (a pre-existing `except...raise` without exception chaining in `resume_parser.py`, in a function I wasn't even touching). Both times I had to stop, confirm the issue really was pre-existing (`git stash` became my go-to for this), and decide whether to fix it inline or push back. I also didn't expect a routine `make check` run to turn into its own mini-investigation — it crashed outright on a numpy/mypy version mismatch, and figuring out *how* pre-existing that was, and how big the blast radius would be if I "fixed" it (103 errors across 26 files, it turned out), took more effort than the actual bug fix.

**What did you learn about working in a large codebase?**
That a "clean" bug fix is never just the two lines that fix the bug. Over the course of this issue I found four things beyond the original regex bug: the same anchoring bug independently breaking `_strip_markdown()`, a docker-compose.yml environment fix I'd made just to get local services running, a pre-existing lint/type-check issue blocking my commit, and a repo-wide numpy/mypy dependency-drift issue. Each one needed a separate scope decision — fix it here, fix it separately, or just document and leave it — and I couldn't apply one rule to all four. `_strip_markdown()` got fixed here because it shared the exact root cause. The docker-compose.yml fix got pulled back out of the branch (after I'd already pushed it) once I realized it had no connection to the actual issue. The lint issue got fixed inline because it was blocking the commit gate on a file I was already touching. The numpy/mypy issue got explicitly documented and left alone because absorbing it would have meant touching 26 files I had no business touching for a whitespace bug.

The harder realization underneath all four of those decisions is that I default to wanting to resolve everything I find — every bug, every lint error, every unrelated issue in view. That instinct is actually the wrong one on a team. Working solo, more fixing is strictly better. On a real team, an uncovered bug that needs real investigation isn't mine to silently absorb into an unrelated PR — it's something the team needs to see and decide on together: is this worth the time right now, or is it a note for later? Development isn't a solo adventure, and staying in scope isn't about avoiding extra work, it's about keeping the whole team's shared picture of the project accurate. That's a different skill than the one this course started with — Week 7 was about solving one contained problem; by Week 9 the actual skill being tested was factoring scope, scale, and effort against what one contribution should reasonably own.

**How did AI tools help — and where did they fall short?**
The biggest help was bridging exactly the gap a junior dev can't close by reading docs alone: a lot of what makes a senior developer fast is unspoken, accumulated knowledge — knowing `git stash` is the quick way to prove something's pre-existing, knowing what a maintainer actually expects in a PR description, knowing which pre-commit failure is worth fixing inline versus pushing back on. Having that available on demand, instead of learning it slowly over years, measurably accelerated how fast I went from "the tests pass" to "this is actually ready to submit." It also changed *how* I followed conventions — I don't like doing something just because a style guide says so, and getting the reasoning behind a convention (why `from e` actually matters, why a docstring needs updating when behavior changes, why scope discipline matters) meant I was applying judgment instead of copying a rule. It made exploring the codebase and arguing through different approaches genuinely engaging — closer to a game of widening how much of the system I understood than a checklist. And using it to review my own git history like a senior reviewer — catching the `docker-compose.yml` scope leak, the missing exception chain, the unrelated lockfile drift — caught mistakes I wouldn't have caught reading my own diff, because I already knew what I meant by it.

Where it fell short: unspoken conventions only get caught if I think to ask, or something explicitly points them out — an AI doesn't know what it doesn't know about a specific codebase's unwritten norms any more than I do on my own. I had to build the habit of manually reviewing every edit myself and following up with direct questions to confirm something actually got done the way I asked, not just claimed done. The most reliable check turned out to be opening a completely new chat and asking for a fresh review of the code with no prior context — that consistently caught things the original working session's accumulated assumptions had smoothed over.

**What would you do differently if you started over?**
Resolve unknowns earlier and more systematically, not just when a grader flags it. The Week 7/8 grader feedback specifically called out that I'd left cheaply-testable risks (what `pypdf` actually emits for indented PDFs, whether a stray `\r` from CRLF line endings mattered) as open questions in `PLAN.md` instead of just testing them — and once I actually ran the experiments, both resolved in about ten minutes each. I only did that because it was pointed out to me. If I started over, I'd build "can I just test this right now" into planning by default rather than treating it as a follow-up. I'd also do the "does my diff touch anything outside this issue's files" check earlier — I found the docker-compose.yml scope issue during a deliberate end-of-week review pass, but it had already been sitting in three commits and gotten pushed before I caught it.

The Week 9 grading feedback on the PR itself added a fourth thing I'd change: it confirmed the fix "is clean, well-scoped, and correctly targeted," but called out that `PLAN.md` and `JOURNAL.md`'s volume of analysis "significantly outweighs the size of the actual code change" — five regex tweaks and two test functions, documented across pages of risk analysis. That's a fair hit. I optimized for showing my reasoning process completely, on the assumption that more visible thinking reads as more rigorous, but a real reviewer has to read all of it to find the five-line diff underneath, and at some point that volume becomes a cost to them rather than evidence of care. If I started over, I'd write the root-cause explanation and plan at roughly the length the change itself warrants — a paragraph and a short list for a Tier 1 whitespace bug — and reserve the long-form risk-by-risk write-up for issues where the blast radius or design ambiguity actually justifies it. Knowing how much documentation a change deserves is its own skill, separate from writing the fix correctly, and this module is the first time I've had it named as something to calibrate rather than just maximize.

**What are you most proud of from this module?**
Not the PR itself — the moment I'm most proud of is going back and pulling the docker-compose.yml commit back out of the branch after it was already pushed to my fork. It would have been easy to leave it; it was a real, working fix, already committed, already public, and removing it meant an interactive rebase and a force-push, which is more effort than just leaving well enough alone. But it didn't belong in a PR about a whitespace regex, and recognizing that *after* the work was technically "done" — and being willing to redo it properly instead of letting it ride — is the habit I actually want to keep from this module, more than any specific line of code I wrote.

More broadly, this is the first module in the course that's felt less like solving an assigned problem and more like the actual work I've always wanted to do — reasoning about scope, arguing through tradeoffs, understanding a codebase deeply enough to know what *not* to touch. Not glamorous, but the curiosity is real, and it's genuinely fostered by having AI to explore the codebase and argue different approaches with. I'm looking forward to AI301, the next course after this one, being closer to independent work on a real, live open source project, because that's the direction I want this to keep going — assuming I get in, of course 😉.
