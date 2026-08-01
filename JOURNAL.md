# Module 3 Journal

A running record of my Module 3 work on PathReview. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The résumé ingestion parser fails to recognize section headers whenever the
extracted text carries leading indentation. `_detect_sections()` in
`ingestion/parsers/resume_parser.py` anchors every header pattern to the very
start of a line (e.g. `^Experience`, `\nExperience`), but text pulled out of PDFs
routinely preserves leading spaces or tabs — so an indented single-column résumé
matches nothing and `detected_sections` comes back empty. That silent failure
matters because downstream review generation relies on knowing which sections a
résumé contains (Education, Skills, Experience, …), so an empty result quietly
degrades the entire review. A successful fix makes the header patterns tolerant
of leading whitespace, brings the three currently-failing unit tests
(`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
`test_detect_sections`) back to green, and adds coverage for indented input —
all contained within `resume_parser.py` and `tests/unit/test_resume_parser.py`.

**Branch name:** fix/147-resume-section-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes — "Is this right for me?" checklist

- **Scope is small and well-bounded.** The fix lives in a single module
  (`resume_parser.py`) plus its test file; no cross-cutting changes to the RAG,
  agent, safety, or API layers. Labeled `tier-1` / `good first issue`.
- **Reproducible and testable.** The issue ships an exact repro snippet and names
  three existing failing tests, so I have a clear pass/fail signal and can work
  test-first.
- **I understand the domain.** It's a plain text-parsing / regex bug in the
  ingestion pipeline — no external services or credentials required to reproduce.
- **Clear definition of done.** Indented headers are detected, the three named
  tests pass, and new coverage guards the leading-whitespace case.
- **Right-sized effort.** Estimated a few hours — appropriate for a first
  Module 3 contribution without risking scope creep.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/newairforces/pathreview/commit/fa08842a68b223aa42e4f08e1ab51dc626037d25

**Reproduction summary:**
I added a failing regression test (`test_detect_sections_with_leading_whitespace`)
and reproduced the bug directly: `_detect_sections()` returns
`['Education', 'Experience']` for flush-left text but `[]` for the identical text
indented with leading whitespace, which also causes the three previously-failing
tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
`test_detect_sections`) to fail because their fixtures are indented.

**PLAN.md link:** https://github.com/newairforces/pathreview/blob/fix/147-resume-section-leading-whitespace/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm CRLF (`\r\n`) line endings from PDF extraction are handled by the
relaxed leading anchor, and verify no downstream consumer treats an empty
`detected_sections` as a meaningful signal rather than a bug.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix is implemented and committed. `_detect_sections()` now inserts `[ \t]*`
after each line anchor (`^` / `\n`) so indented headers are detected, while the
trailing `\s*$` / `\s*[:|-]` boundary is preserved to avoid substring false
positives. This completes PLAN.md steps 1–3: the three fixture-driven tests plus
the #147 regression test (`test_detect_sections_with_leading_whitespace`) are now
green. I also resolved the two open questions from Week 8 — CRLF is handled (the
`^`-under-MULTILINE anchor plus horizontal-only `[ \t]*` covers `\r\n`), and a grep
confirmed the only consumer of `detected_sections` is logging in
`ingestion/pipeline.py`, so an empty result was purely a silent bug.

**Next steps:**
PLAN.md step 4 (extend coverage — tabs, mixed indent, first line, CRLF, negative
mid-sentence case) and step 5 (full-suite regression run). Then self-review against
CONTRIBUTING.md, open the PR, and request peer feedback in Slack.

**Blockers:**
None on the fix itself. One thing to flag: the repo has a large set of pre-existing
failures unrelated to #147 — `make test-unit` shows 54 failing tests on the branch
before my change (e.g. `test_review_service`, `test_skill_extractor`,
`test_tech_detector`), and `make check` reports 182 ruff / 52 black / 103 mypy
issues repo-wide. Two of the six `test_resume_parser.py` failures
(`test_strip_markdown_syntax`, `test_parse_markdown_resume`) are also pre-existing —
they live in `_strip_markdown`, a different method, and fail on `main` too. Per the
Week 9 pre-existing-failure guidance, I'm scoping my PR to `_detect_sections` and
documenting these; my change introduces zero new failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/newairforces/pathreview/pull/1

**Branch:** `fix/147-resume-section-leading-whitespace`

**What you built:**
Made resume section-header detection tolerant of leading indentation. PDF text
extraction routinely preserves leading spaces/tabs, so headers like
`"    Experience:"` previously matched none of the anchored regex patterns and
`detected_sections` came back empty — silently degrading downstream review
generation. The fix inserts a horizontal-only `[ \t]*` run after each line anchor
so indentation is absorbed without letting a match leak across a newline, and keeps
the trailing field boundary so substrings like `"Work Experience Highlights"` are
not falsely detected.

**Tests added or updated:**
`tests/unit/test_resume_parser.py` — the Week 8 regression test now passes, and I
added five sibling cases: tab-indented headers, mixed space/tab indentation, an
indented header on the first line, CRLF line endings, and a negative case asserting
a mid-sentence occurrence is not falsely detected.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Notes: interpreted per the Week 9 pre-existing-failure policy — "passes" means my
changes introduce **no new failures**. `make test-unit` goes from 54 → 50 failures:
my change fixes exactly the 4 #147 detection tests and adds zero new failures
(verified by diffing the failure set before/after). The remaining 50 failures, and
all `make check` findings (182 ruff / 52 black / 103 mypy repo-wide), are
pre-existing and unrelated to this PR — my two touched files carry the same ruff
findings as baseline and `resume_parser.py` is mypy-clean.

**Draft PR feedback received from:** none
