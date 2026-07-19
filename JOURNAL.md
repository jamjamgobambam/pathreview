## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser fails to detect section headers when the resume text contains leading whitespace, which commonly occurs in text extracted from PDFs. As a result, the parser returns an empty list of detected sections instead of identifying sections like "Education" and "Skills." A successful fix should allow section detection even when section headers are indented.

**Selection reasoning ("Is this right for me?"):**
I chose this issue because it has a clear reproduction case, a well-defined scope, and focuses on improving the resume parser without requiring changes across many parts of the codebase. It also provides related tests that will help verify the fix.

**Branch name:** fix/147-resume-section-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Add GitHub commit link after committing your reproduction]

**Reproduction summary:**
I reproduced the issue by using the provided resume parser example with resume text containing leading whitespace before section headers. The parser failed to detect the expected sections because _detect_sections() only matches section headers that begin at the start of a line.

**PLAN.md link:** [Add GitHub link to PLAN.md after creating it]

**Walkthrough video (recommended):** [Optional Loom link]

**Blockers or open questions:**
None at this time.