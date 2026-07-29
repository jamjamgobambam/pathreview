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

