## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146
**Issue title:** PII scrubber fails to redact parenthesized US phone numbers
**Tier:** [x] Tier 1

**Problem summary:**
The phone-number regex in pii_scrubber.py uses a \b word-boundary anchor,
but ( is not a word character, so the pattern never matches when a number
opens with a parenthesized area code like (555) 123-4567. Dashed formats
like 555-123-4567 still match correctly. Because of this, scrub() leaves
parenthesized numbers in plaintext instead of redacting them, and detect()
returns an empty list even when a phone number is clearly present, which is
a real gap in a safety layer meant to catch PII. The fix is to broaden the
regex to also accept a leading parenthesis, verified by the four failing
tests already named in the issue.

**Branch name:** fix/146-pii-scrubber-parenthesized-phone
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger
