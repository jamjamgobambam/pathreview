# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** Tier 1

**Selection reasoning:**
I'm comfortable with Python and testing generally, but this is my first time working
in the pathreview codebase specifically, so I chose a Tier 1 issue on purpose rather
than defaulting to it out of caution. My goal for this first issue is to learn the
repo's contribution workflow end-to-end — branch naming, commit conventions, test
layout, and the PR process — on a change that's small and well-scoped, before taking
on a Tier 2/3 issue that touches more of the architecture. This issue in particular
is a good fit: it's isolated to a single method (`_detect_sections()`) in one parser
file, has three existing failing tests that already define "done," and doesn't
require touching the API, RAG pipeline, or agent layer, so I can focus on
understanding the ingestion module in depth rather than juggling multiple subsystems.

**Problem summary:**
The `_detect_sections()` method in `ingestion/parsers/resume_parser.py` uses regex
patterns anchored with `^` and `\n` to find section headers like "Education" or
"Skills". When PDF text extraction preserves leading indentation/whitespace on
each line, those patterns no longer match, so `detected_sections` comes back
empty even though the sections are clearly present in the text. A successful
fix will make section detection tolerant of leading whitespace so resumes with
indented text (a common PDF extraction artifact) are parsed correctly, fixing
the related failing tests `test_parse_single_column_resume_text`,
`test_parse_resume_no_work_experience`, and `test_detect_sections`.

**Branch name:** fix/147-resume-parser-whitespace

**Setup confirmation:** Yes, the app runs locally at localhost:5173

**Cohort ledger:** I've added the issue to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Gourav-praneeth/pathreview/commit/90f7ed5

**Reproduction summary:**
Reproduced the bug two ways: ran the three failing unit tests named in the issue
(all failed with `AssertionError` on empty/missing detected sections), and called
`ResumeParser._detect_sections()` directly on indented vs. unindented versions of
the same text — the indented version returned `[]` while the unindented version
correctly returned `['Education', 'Skills']`, confirming leading whitespace is
what breaks the regex anchors.

**PLAN.md link:** https://github.com/Gourav-praneeth/pathreview/blob/fix/147-resume-parser-whitespace/PLAN.md

**Blockers or open questions:**
Not yet sure how much leading whitespace real PDF extraction actually produces
(plain spaces vs. tabs vs. non-breaking spaces) — planning to keep the fix scoped
to spaces/tabs unless a real fixture surfaces something wider.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md's implementation steps are done. Updated the four
regex patterns in `_detect_sections()` to allow `[ \t]*` between the line-start
anchor and the section keyword, so leading spaces/tabs no longer block detection.
Re-ran the three originally failing tests (`test_parse_single_column_resume_text`,
`test_parse_resume_no_work_experience`, `test_detect_sections`) — all pass now.
Ran the full `test_resume_parser.py` file and the full unit suite to check for
regressions: went from 53 pre-existing failures to 50 (exactly the 3 fixed, no
new breaks). Added a new regression test for tab-indented headers, since the
issue only explicitly covered spaces. Along the way I found two more failing
tests in the same file (`test_parse_markdown_resume`, `test_strip_markdown_syntax`)
caused by the identical whitespace-anchoring bug, but in `_strip_markdown()`
rather than `_detect_sections()` — decided to leave those out of scope since
issue #147 only names the section-detection tests, and documented them as
pre-existing failures instead.

**Next steps:**
Open a draft PR against `ascherj/pathreview` and request peer/mentor feedback in
Slack. Before finalizing, re-run `make check` and `make test-unit` one more time
against the final diff and fill in the PR template completely.

**Blockers:**
Hit one bit of local tooling friction: the mypy pre-commit hook has no path
filter, so it flags all 10 pre-existing untyped test methods in
`test_resume_parser.py` (unrelated to this change), even though `make typecheck`
— the project's documented gate — explicitly excludes `tests/`. Fixed one
unrelated pre-existing `B904` lint issue in `resume_parser.py` since it was a
trivial 1-line fix, but skipped the mypy hook for that one commit rather than
add annotations to 10 unrelated test methods. Not a blocker for the PR itself,
just noting the discrepancy in case it comes up in review.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/833

**Branch:** `fix/147-resume-parser-whitespace`

**What you built:**
Fixed `ResumeParser._detect_sections()` so it detects resume section headers
(Education, Skills, Experience, etc.) even when the header line has leading
whitespace, by allowing optional spaces/tabs between the line-start anchor and
the section keyword in all four regex patterns. Previously, indented text (as
produced by real PDF extraction, or by indented test fixtures) caused
`detected_sections` to come back empty.

**Tests added or updated:**
Updated `tests/unit/test_resume_parser.py` — the three pre-existing failing
tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
`test_detect_sections`) now pass against the fix, and I added a new
`test_detect_sections_with_tab_indentation` to cover tab-indented headers, since
the issue only described the space-indented case.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(with documented pre-existing failures unrelated to this change — see PR
description and Check-in 1 for the exact before/after counts; my changes
introduce no new failures)

**Draft PR feedback received from:** none yet — just opened as a draft

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
Checked PR #833 directly via the GitHub API (issue comments, PR reviews, and
inline review comments — all three endpoints returned empty) as well as the
PR page itself. No maintainer or peer has commented, reviewed, approved, or
requested changes as of this entry. The PR is still in draft status.

**How you responded:**
N/A — nothing to respond to yet. If feedback arrives after this submission,
I'll follow up with the maintainer directly and update this section, but per
the assignment instructions I'm noting the lack of feedback and moving on
rather than blocking on it.

---

### Reflection

**What was harder than you expected?**
Getting the environment running at all was harder than the actual bug fix.
My `.venv` had been built against the system Python (3.9) instead of the
3.11+ the project requires, so `pip install -e ".[dev]"` failed silently on
version resolution and nothing — including `uvicorn` — ever got installed.
On top of that, Postgres/Redis needed Docker running and a `.env` file that
didn't exist yet. None of this was related to the issue itself, but it ate
real time before I could even run a test. It was a good reminder that "make
run doesn't work" is often an environment problem, not a code problem, and
the fix is to read the Makefile/setup scripts carefully rather than guess.

**What did you learn about working in a large codebase?**
The biggest difference from my own projects is that "done" isn't just "my
change works" — it's "my change works AND I've proven the rest of the
codebase's existing problems aren't mine." I had to run `make check` and
`make test-unit` *before* touching anything just to get a baseline, because
this codebase already has 53 failing unit tests and 182 lint errors that
have nothing to do with resume parsing. Without that baseline, I'd have had
no way to tell my reviewer (or myself) whether a failing test was something
I broke or something that was already broken. I also learned that local
tooling (the pre-commit mypy hook) can be stricter than the project's own
documented CI gate (`make typecheck` excludes `tests/`, the hook doesn't) —
in a codebase you don't own, you have to notice and document that gap
rather than just quietly overriding it.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical, wide-surface-area work:
diagnosing the venv/Docker setup chain step by step, running and parsing
large `pytest`/`ruff`/`mypy` outputs to isolate exactly which failures were
pre-existing versus newly introduced, and drafting the reproduction doc,
PLAN.md, and PR description in a consistent format. Where it fell short was
scope judgment — when I found that `_strip_markdown()` had the identical
whitespace-anchoring bug as `_detect_sections()`, the AI could point out the
pattern immediately, but deciding whether to fix it in this PR or leave it
out of scope was a judgment call I had to make myself, not something it
could decide for me. It's genuinely good at "here are the facts and the
tradeoffs," not at "here's what you should actually want."

**What would you do differently if you started over?**
I'd run the full environment setup and baseline `make check`/`make
test-unit` in Week 7, before writing the problem summary, instead of
discovering the Python version mismatch in Week 9 while trying to implement
the fix. Having the baseline numbers early would have made the whole
contribution cycle feel less like it was happening in the wrong order.

**What are you most proud of from this module?**
Catching the `_strip_markdown()` bug that shared the same root cause as the
issue I was assigned. I had the discipline to *not* fix it just because I
could — I stayed inside the scope of #147 and documented the related bug
instead of quietly expanding the PR. It would have been easy to justify
folding it in since it was "basically the same fix," but that's exactly the
kind of scope creep that makes PRs harder to review.
