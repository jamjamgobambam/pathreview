## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers


**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Reasoning:**
I chose this issue beause it's a self-contained Tier 1 bug which is a good fit for my first open source contribution. It lives entirely in one file (pii_scrubber.py), so I can understand the full scope without needing to trace through multiple modules or services. I also picked it because it gave me a chance to sharpen my regex skills by working through a concrete word boundary edge case rather than just reading about one. At the time I found it, there was no one else who was working on it and it had no blockers. This made me confident that I could realistically finish it within the Weeks 8-9 timeline. 

**Problem summary:**
Formats like (555) 123-4567 go through the function unredacted and dashed formates like 555-123-4567 are caught. In pii_scrubber.py, the phone number regex uses a \b word boundary that fails whenever a number starts with "(" because there's no valid boundary between a space and a parenthesis. A sucessful fix replaces the boundary anchors with digit-based checks and allows spaces as separators, so both fromats get redacted and all four failing tests pass. 

**Branch name:** fix/146-pii-scrubber-phone-parens

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger