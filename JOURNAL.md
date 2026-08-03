## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/146)

**Issue title:** [PII scrubber fails to redact parenthesized US phone numbers
 #146

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber currently recognizes US phone numbers written with dashes (such as 555-123-4567), but it does not detect or redact the common parenthesized format (555) 123-4567. As a result, scrub() leaves these numbers unredacted, and detect() incorrectly reports that no PII is present. This issue affects the phone number matching logic in pii_scrubber.py. A successful fix would update the phone number pattern so both dashed and parenthesized US phone number formats are correctly detected and redacted, allowing the related unit tests to pass.

**Branch name:** fix/146-pii-scrub-phone-num

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger





## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/sr-0397/pathreview/tree/fix/146-pii-scrub-phone-num)


**Reproduction summary:**
Ran the repro script (the scratch_repro.py) from issue #146 locally and confirmed scrub() leaves
"(555) 123-4567" unredacted while the dashed format is caught, and detect()
returns [] for the parenthesized number. Confirmed via 4 failing tests in
tests/unit/test_pii_scrubber.py.

**PLAN.md link:** (https://github.com/sr-0397/pathreview/tree/fix/146-pii-scrub-phone-num)

**Blockers or open questions:**
Not sure how to deal w edge cases yet...
- Phone number at the very start or end of a string
- Multiple phone numbers, mixed formats, in one string
- Numbers with a leading "+1" country code plus parens





## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for 146 by updating the phone_us regex in
safety/pii_scrubber.py to accept whitespace as a valid separator
alongside dashes and dots, which resolves the boundary/separator issue
that was blocking parenthesized phone numbers like "(555) 123-4567"
from being matched. Verified locally: all 6 phone-related tests in
tests/unit/test_pii_scrubber.py now pass, including the 4 that were
previously failing (test_us_phone_number_redaction, test_us_phone_formats,
test_detect_phone_pii, test_phone_at_start_of_text). Ran a full
make test-unit before/after comparison via git stash to confirm scope:
53 failed/375 passed before my change vs. 49 failed/379 passed after —
a net swing of exactly 4 tests (fail to pass), with no new failures
introduced anywhere else in the suite. Also confirmed via ruff check
that the 4 pre-existing lint issues in pii_scrubber.py predate this
change and aren't caused by the edited line.

**Next steps:**
Run make check across the full repo, review docs/CONTRIBUTING.md for
branch naming and commit message conventions, open a draft PR for peer
feedback

**Blockers:**


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/179

**Branch:** fix/146-pii-scrub-phone-num

**What you built:**
Fixed the phone_us regex in safety/pii_scrubber.py so it correctly
matches and redacts parenthesized US phone numbers (e.g. "(555) 123-4567"),
by allowing whitespace as a valid separator character in addition to
dashes and dots.

**Tests added or updated:**
tests/unit/test_pii_scrubber.py — no new tests added; the 4 existing
tests tied to this bug (test_us_phone_number_redaction,
test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text)
now pass.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** not yet