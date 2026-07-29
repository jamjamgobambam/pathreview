## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber's phone number detection, located in pii_scrubber.py, uses a
regex pattern that only matches dashed phone formats like 555-123-4567. It
does not account for the parenthesized format (555) 123-4567, which is one
of the most common ways US phone numbers are written. As a result, scrub()
lets these numbers pass through unredacted and detect() fails to flag them
as PII at all. A successful fix will update the phone-matching pattern to
also catch parenthesized formats, closing this gap in the safety layer, and
get the related unit tests passing (test_us_phone_number_redaction,
test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text).

**Branch name:** fix/146-pii-scrubber-parenthesized-phone

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 reproduction notes

Ran python -m pytest tests/unit/test_pii_scrubber.py -v on branch fix/146-pii-scrubber-parenthesized-phone. Confirmed issue #146: 5 tests fail, all related to parenthesized phone format (555) 123-4567 not being detected or redacted by PIIScrubber.detect()/scrub(). Dashed and dotted formats pass; parenthesized format returns 0 detections.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/grcyaa0-eng/pathreview/commit/e74d09925d39898676ee941823aa7fbff5f6c42d

**Reproduction summary:**
Ran the existing test suite for the PII scrubber and confirmed 5 tests fail,
all related to the parenthesized US phone format (555) 123-4567 not being
detected or redacted. Traced the cause to the phone_us regex in
pii_scrubber.py, which only allows a hyphen or period as a separator after
the closing parenthesis, not a space.

**PLAN.md link:** https://github.com/grcyaa0-eng/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Noticed a separate, likely unrelated bug in test_mixed_pii_and_text where
part of the word "Python" gets redacted along with nearby PII. Flagged it
in PLAN.md as a risk to watch for but it's not in scope for issue #146.
