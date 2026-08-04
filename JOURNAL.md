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

**Reproduction commit link:** https://github.com/yenscastro/pathreview/commit/e901ce4

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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md. Widened the `phone_us` regex separator in
`safety/pii_scrubber.py` from `[-.]?` (dash/dot only) to `[-. ]?` (dash, dot, or
a single literal space). PLAN sub-tasks 1–4 are done: separator widened,
parenthesized branch re-checked, phone tests pass, and the guard tests
(`test_text_with_no_pii`, `test_detect_no_false_positives`) still pass — the
scrubber test file went from 6 failing to 1 failing, and that remaining failure
(`test_mixed_pii_and_text`) is a pre-existing, unrelated `street_address` bug
that also failed before my change.

**Next steps:**
Run `make check` and `make test-unit` in a full dev environment, open a draft PR
early for peer/mentor feedback, then fill in the PR template and mark it ready.

**Blockers:**
None on the fix itself. Still need to run the full `make check` / `make test-unit`
in a complete environment (my local venv only has the deps needed for the safety
module).

---

### Check-in 2 (end of week)

**PR link:** [add after opening the PR against ascherj/pathreview]

**Branch:** `fix/146-parenthesized-phone-redaction`

**What you built:**
Fixed a PII-redaction bug where the US phone-number regex only allowed dashes or
dots between number groups, so space-separated and parenthesized formats like
`(555) 123-4567` and `+1 555 123 4567` were never redacted. Widening the three
separators to also accept a single literal space fixes both `scrub()` and
`detect()`, since they share the same pattern.

**Tests added or updated:**
`tests/unit/test_pii_scrubber.py` — added `test_repro_issue_146_parenthesized_phone`
(Week 8) which now passes and acts as the regression test. The four existing
phone tests (`test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, `test_phone_at_start_of_text`) now pass as well.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
