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
