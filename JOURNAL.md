# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The safety layer's PII scrubber (`safety/pii_scrubber.py`) is supposed to catch
and redact personal information, including US phone numbers, before text is
stored or displayed. Its `phone_us` regex only allows `-` or `.` between the
number groups, so a common format like `(555) 123-4567` — where a space follows
the closing parenthesis — is never matched and passes through unredacted. This
is a real privacy leak, since a phone number a user expects to be hidden stays
visible. A successful fix updates the regex to also accept a space (and the
parenthesized area-code form) as a valid separator, adds a test covering that
format, and leaves the existing phone/email/SSN cases still passing.

**Branch name:** fix/146-parenthesized-phone-redaction

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/yenscastro/pathreview/commit/71f526d71edbff00a53bb5e8b4b1d40fa432e1fc

**Reproduction summary:**
I ran the phone tests in `tests/unit/test_pii_scrubber.py` and added a dedicated
failing test (`test_repro_issue_146_parenthesized_phone`). Running
`pytest tests/unit/test_pii_scrubber.py -k phone` shows 4 tests failing, and
`scrub("Call me at (555) 123-4567 or 555-123-4567")` returns
`"Call me at (555) 123-4567 or [REDACTED]"` — the dashed number is redacted but
the parenthesized `(555) 123-4567` leaks through, confirming the bug.

**PLAN.md link:** https://github.com/yenscastro/pathreview/blob/fix/146-parenthesized-phone-redaction/PLAN.md

**Walkthrough video (recommended):** [add Loom link here if you record one]

**Blockers or open questions:**
Main open question is how loose to make the regex without introducing false
positives (e.g. version numbers like `1.2.3` or spaced digit runs in prose). I
need to confirm the guard tests `test_text_with_no_pii` and
`test_detect_no_false_positives` still pass after widening the separator.
