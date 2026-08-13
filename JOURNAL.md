## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/1

**Issue title:** Resume parser raises `IndexError` on resumes with no work experience section

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `resume_parser.py` module assumes that every uploaded resume contains at least one work experience section entry. When a candidate or new graduate with no prior formal work history uploads a resume, the parser attempts to access index 0 of the experience section array without checking if the key exists or if the list is empty, resulting in an unhandled `IndexError` crash. A successful fix will add safe bounds checking and defensive fallback logic to ensure resumes without work experience are parsed gracefully without raising exceptions.

**Branch name:** fix/1-resume-parser-index-error

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Unheat/pathreview/commit/8076fd324d32933d61a6a23cf4a7aa170bf0313d

**Reproduction summary:**
Reproduced by executing unit tests against `ResumeParser` with a resume string lacking an `Experience` section. Verified that indexing `sections['experience'][0]` directly without checking key existence or bounds causes an unhandled `IndexError`.

**PLAN.md link:** https://github.com/Unheat/pathreview/blob/fix/1-resume-parser-index-error/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
None at this time. Ready for implementation in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented defensive section extraction and bounds checking in `ingestion/parsers/resume_parser.py`. Updated regex section header detection to account for leading whitespace and markdown headers, and added `extract_sections()` with default empty list fallbacks for all standard section headers.

**Next steps:**
Verify unit test suite coverage, run self-review checks (`make check` / `make test-unit`), commit changes, push to remote branch, and open pull request.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1

**Branch:** fix/1-resume-parser-index-error

**What you built:**
Added defensive bounds checking, enhanced section matching, and safe empty list fallbacks to `ResumeParser`. Resumes lacking work experience sections are parsed gracefully without raising unhandled `IndexError` or `KeyError` exceptions.

**Tests added or updated:**
Added `test_extract_sections_no_experience` to `tests/unit/test_resume_parser.py` and updated section detection and markdown stripping test cases to verify resumes without work experience sections.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received by the end of the week.

**How you responded:**
N/A — awaiting maintainer review.

---

### Reflection

**What was harder than you expected?**
Navigating edge cases in text parsing and regular expression section matching across heterogeneous resume layouts was harder than anticipated. Ensuring section header detection didn't accidentally misclassify custom headings (like "Projects" or "Volunteer Experience") while robustly handling resumes completely missing standard sections required careful regex tuning and boundary testing.

**What did you learn about working in a large codebase?**
I learned the critical importance of defensive programming and preserving strict public API contracts in production codebases. In a larger project, small assumptions like expecting a dictionary key or list index `0` to always exist can cascade into unexpected runtime failures downstream in ingestion pipelines. Reading architectural docs, writing targeted unit tests, and adhering to established project standards ensure contributions integrate smoothly without regressions.

**How did AI tools help — and where did they fall short?**
AI tools were exceptionally useful for rapid code exploration, generating boilerplate unit test cases for missing sections, and structuring step-by-step reproduction plans. However, AI fell short in identifying subtle domain-specific edge cases, such as handling malformed markdown headers with leading whitespace or trailing punctuation, requiring manual code inspection, debugging, and verification against actual test payloads.

**What would you do differently if you started over?**
If starting over, I would invest more time up front creating a broader suite of edge-case test payloads—including totally blank documents, unconventional heading titles, and non-standard markdown—before implementing the fix. Having an exhaustive reproduction test suite early in the cycle makes refining regex patterns and fallback structures much faster and safer.

**What are you most proud of from this module?**
I am most proud of taking an open-ended bug report (`IndexError` on missing work experience) and delivering a clean, fully tested, and resilient fix backed by thorough documentation and passing unit tests.
