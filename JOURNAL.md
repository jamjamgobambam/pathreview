## Week 9 — Solution building and PR submission

**PR link:** https://github.com/ascherj/pathreview/pull/370

**Branch name:** fix/146-parenthesized-phone-redaction

**Draft PR opened:** [x] Yes

**Test results before fix:** 5 failed / 20 passed (`test_pii_scrubber.py`)

**Test results after fix:** 1 failed / 25 passed — all 4 issue-related tests passing (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, and one more), plus new regression test `test_parenthesized_phone_with_space_separator`

**Self-review against contribution standards:** [x] Completed

**Draft PR feedback received from:** Sandhya Rimal

**Feedback summary:** Approved, no changes requested

**Ready for review:** [x] Yes