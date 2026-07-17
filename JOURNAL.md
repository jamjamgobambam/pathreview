## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser fails to detect section headers when the input text contains leading whitespace, which is common in text extracted from PDFs. The _detect_sections() function only matches headers that begin at the very start of a line (e.g., ^Education), so indented headers like Education: or Skills: are ignored. As a result, detected_sections is returned as an empty list even though valid sections are present.

**Branch name:** fix/147-resume-parsing-breaks-on-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger