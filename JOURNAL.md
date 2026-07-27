# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber (`safety/pii_scrubber.py`) is supposed to catch phone numbers
before any generated feedback reaches a user, but the `phone_us` regex only
reliably matches dashed formats like `555-123-4567`. The pattern opens with a
`\b` word boundary, and `\b` only matches between a word character and a
non-word character — when a number starts with `(` (as in `(555) 123-4567`),
the character before it is usually a space, so both sides of that gap are
non-word characters and the boundary never fires, letting the whole number
through unredacted. I reproduced this locally by importing `PIIScrubber` and
running the exact steps from the issue: in the same string, the dashed number
got replaced with `[REDACTED]` but the parenthesized one right next to it
didn't, and `detect()` returned an empty list for text that was nothing but a
parenthesized phone number. Since parenthesized format is one of the most
common ways people write a US phone number on a resume, this isn't an edge
case — it's a real hole in the safety layer. A correct fix adjusts the
`phone_us` pattern so the leading boundary check tolerates a `(` immediately
after it, which should get all four related tests in
`tests/unit/test_pii_scrubber.py` passing.

**Branch name:** fix/146-pii-scrubber-phone-numbers

**Setup confirmation:** [ ] App runs locally at localhost:5173
(Docker and Python 3.11 aren't installed on this machine yet — need to get
those set up before Week 8 so I can actually run the test suite and verify
a fix.)

**Cohort ledger:** [ ] Issue added to cohort ledger
