## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The phone-number regex in `pii_scrubber.py` only matches dashed formats like
555-123-4567, so parenthesized formats like (555) 123-4567 — one of the most
common ways US phone numbers are written — pass through `scrub()` completely
unredacted, and `detect()` reports no PII found at all for that format. This
is a gap in the safety/PII-redaction layer of the app. Four existing unit
tests already cover this case and are currently failing. A successful fix
extends the phone-number pattern matching to also catch the parenthesized
format, so both `scrub()` and `detect()` correctly identify and redact it,
and the four related tests pass.

**Selection reasoning:** I chose this as a Tier 1 issue since it's my first
time contributing to an unfamiliar multi-module codebase. The bug is
isolated to a single function in one file, has clear reproduction steps
and four named failing tests to validate against, so I can verify
correctness without needing to understand the rest of the app's
architecture.

**Branch name:** fix/146-parenthesized-phone-redaction

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tahsintawhid/pathreview/commit/702d8e7fcbfeb317d43507da8072b9035da62808

**Reproduction summary:**
Confirmed the root cause: the `phone_us` regex in `safety/pii_scrubber.py` uses
`[-.]?` as the separator between digit groups, which allows dashes and dots but
not spaces. Since `(555) 123-4567` has a space (not a dash) right after the
closing parenthesis, the regex fails to match at all. Verified via direct
regex testing (`re.search` returns `None` for the parenthesized format but
matches for the dashed format), and via `pytest tests/unit/test_pii_scrubber.py
-k "phone"`, which shows 4 failing tests: `test_us_phone_number_redaction`,
`test_us_phone_formats`, `test_detect_phone_pii`, and
`test_phone_at_start_of_text`, all failing because `scrub()` leaves the number
un-redacted and `detect()` returns an empty list.

**PLAN.md link:** [fill in — link to PLAN.md in your fork]

**Walkthrough video (recommended):** [optional — add if you record one]

**Blockers or open questions:**
`test_us_phone_formats` also tests `"+1 555 123 4567"`, a space-separated
format with no parentheses. It wasn't individually reported as failing since
the test loop's assert stops at the first failure, but it shares the same
root cause (space not in the separator character class) and will need to be
verified once the fix is in place.
