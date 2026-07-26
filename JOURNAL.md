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
