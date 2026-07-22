## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber faisl to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
<!--In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.] -->
This issue lies within the safety directory in pii_scrubber.py. Currently a number like "750-345-5346" will go through and not be detected as PII. A fix would have the parentheses scrubbed from the number and it detected as PII so that a user's information is properly funneled into the proper protective/safety channels. After fixing that mathcing issue, a few failing tests must pass before this issue is considered complete.


**Branch name:** fix/146-pii-scrubber-fails-parenthesized-phone-number-redaction

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger