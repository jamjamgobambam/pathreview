## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser fails to detect section headers when the input text contains leading whitespace, which is common in text extracted from PDFs. The _detect_sections() function only matches headers that begin at the very start of a line (e.g., ^Education), so indented headers like Education: or Skills: are ignored. As a result, detected_sections is returned as an empty list even though valid sections are present.

**Branch name:** fix/147-resume-parsing-breaks-on-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/karthikkatu/pathreview/commit/bd52bb4

**Reproduction summary:**
Wrote a minimal test feeding `_detect_sections()` resume text with indented section headers (e.g. `        Education:`) — it returned an empty list instead of detecting "Education" and "Skills", confirming the regex patterns don't tolerate leading whitespace. Notably, 5 pre-existing tests in the suite were already failing for the same reason without anyone noticing.

**PLAN.md link:** https://github.com/karthikkatu/pathreview/blob/fix/147-resume-parsing-breaks-on-whitespace/PLAN.md

**Walkthrough video (recommended):** _not recorded_

**Blockers or open questions:**
`_strip_markdown()`'s header-stripping regex (`^#+\s+`) has the same whitespace-anchoring flaw and causes one more pre-existing test failure (`test_strip_markdown_syntax`) — planning to leave it out of scope for #147 and flag it as a separate follow-up issue rather than bundling an unrelated fix into this PR. Also unconfirmed: whether real PDF extraction ever emits non-space whitespace (e.g. non-breaking spaces) before headers, since I've only tested against synthetic text fixtures so far.