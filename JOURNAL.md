# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber currently fails to detect and redact US phone numbers when they use parentheses around the area code. This causes some phone numbers containing personally identifiable information to remain exposed. The issue affects the PII detection logic, and the successful fix should update the phone number matching pattern so common US formats are properly recognized and redacted.

**Branch name:** fix/146-pii-scrubber-phone-redaction

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


**Issue selection notes:**
I chose this issue because it is a Tier 1 bug with a clearly defined scope. The expected fix focuses on improving an existing detection pattern rather than changing major parts of the application. This makes it a realistic first contribution while allowing me to learn the repository structure and contribution workflow.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Paste the GitHub link to your reproduction commit after you push it.]

**Reproduction summary:**

I reproduced Issue #146 by running the PII scrubber unit tests with:

`.venv/bin/python -m pytest tests/unit/test_pii_scrubber.py -v`

The tests confirmed that phone numbers formatted as `(555) 123-4567` are not detected or redacted. Specifically, the tests `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, and `test_phone_at_start_of_text` failed, confirming the bug described in the issue.

**PLAN.md link:** [Paste the GitHub link to your PLAN.md file after you push it.]

**Walkthrough video (recommended):**

Not recorded.

**Blockers or open questions:**

During testing, I also noticed an unrelated failing test (`test_mixed_pii_and_text`) involving address redaction. Since this is outside the scope of Issue #146, I will focus only on fixing the phone number redaction bug.