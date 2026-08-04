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

## Reproduction — Issue #146

Ran `python -m pytest tests/unit/test_pii_scrubber.py -v` on branch `fix/146-pii-scrubber-parenthesized-phone`.

**Result:** 5 failed, 20 passed.

**Failures directly related to Issue #146 (parenthesized phone numbers not detected):**
- `test_us_phone_number_redaction` — `(555) 123-4567` not redacted
- `test_us_phone_formats` — parenthesized format `(555) 123-4567` not redacted (other formats pass)
- `test_detect_phone_pii` — `detect()` returns 0 phone matches for `(555) 123-4567`
- `test_phone_at_start_of_text` — `(555) 123-4567` at start of string not redacted

**Root cause:** In `safety/pii_scrubber.py`, the `phone_us` regex (line 15) opens with `\b(?:\+?1[-.]?)?\(?`. Since `\b` requires a word-boundary transition and `(` is a non-word character, `\b` fails to match immediately before a literal `(`. Additionally, `[-.]?` after the closing `)?` does not account for a space, which is the standard separator in `(555) 123-4567`.

**Unrelated pre-existing failure (not in scope for #146):**
- `test_mixed_pii_and_text` fails because the `street_address` pattern's `Pl` (Place) alternative case-insensitively matches inside "a**pl**ications", greedily consuming text back to a preceding digit. This is a separate bug in the `street_address` pattern, not the phone regex, and is not part of Issue #146. Documenting here per pre-existing-failure policy; will note in PR description that this fix does not affect it.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for Issue #146: updated the `phone_us` regex in `safety/pii_scrubber.py` (line 15) to accept whitespace as a separator after the closing parenthesis, in addition to hyphen and period. Ran the existing test suite and confirmed the four previously-failing phone tests now pass (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`). Ran `mypy`, `ruff check`, and `black --check` on the modified file; `mypy` passes clean, and the `ruff`/`black` findings are all on pre-existing lines unrelated to this change. Opened draft PR #827 on ascherj/pathreview.

**Next steps:**
Request peer or mentor feedback on the draft PR in Slack. Address any feedback received, then mark the PR ready for review, add Check-in 2 with the final PR link, and submit the branch URL via the course portal.

**Blockers:**
None currently.
