## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `PIIScrubber` class in `safety/pii_scrubber.py` uses a regex pattern (`phone_us`) to detect and redact US phone numbers before resume/profile text is processed. That pattern only allows a hyphen or period as the separator right after a parenthesized area code, but not a space, so phone numbers written as `(555) 123-4567` — the most common way people format US numbers — are never matched and pass through completely un-redacted. I confirmed this by running the existing test suite: 5 tests fail as a direct result, including `test_us_phone_number_redaction`, `test_us_phone_formats`, and `test_detect_phone_pii`, all of which use the parenthesized-with-space format. A successful fix updates the regex so this format is correctly detected and redacted, without breaking the phone formats that currently pass (hyphenated, dotted, and international).

**Branch name:** fix/146-parenthesized-phone-redaction

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
