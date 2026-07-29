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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/spicyneutrino/pathreview/commit/<hash>

**Reproduction summary:**
Ran the scrub() and detect() methods locally against a string containing
both a dashed and parenthesized phone number. Confirmed the parenthesized
format passes through unredacted and detect() returns an empty list,
matching the issue description. Also ran the four named failing tests in
test_pii_scrubber.py and confirmed they fail as expected.

**PLAN.md link:** https://github.com/spicyneutrino/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Need to confirm whether the phone_us pattern is a single regex or several
patterns, before finalizing the exact fix approach in Week 9.