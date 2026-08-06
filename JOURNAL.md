## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
<!--In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.] -->
This issue lies within the safety directory in pii_scrubber.py. Currently a number like "750-345-5346" will go through and not be detected as PII. A fix would have the parentheses scrubbed from the number and it detected as PII so that a user's information is properly funneled into the proper protective/safety channels. After fixing that mathcing issue, a few failing tests must pass before this issue is considered complete.

**Branch name:** fix/146-pii-scrubber-fails-parenthesized-phone-number-redaction

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Is this right for me?**

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** N/A - mypy and ruff specifies test constraints I have not been able to meet.

**Reproduction summary:**
I used the reproduction code given on the issue's page. I observed the scrub() function failing to scrub a phone number with parentheses around a set of its numbers and the detect() function failing to detect the same phone number as PII.

**PLAN.md link:** [PLAN.md](https://github.com/IGS1I/guided-PathReview/blob/fix/146-pii-scrubber-fails-parenthesized-phone-number-redaction/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
I am still unsure how to properly recreate the PII phone number issue within the launched app since the login credentials do not work.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Nothing completed so far. Having issues getting account user and passowrd to work for the pathreview app.

**Next steps:**
Skip the authenitcation issue, implment my fix and test with unit test (test/unit/test_pii_scrubber.py)

**Blockers:**
Laziness and other work I have set up.

### Check-in 2 (end of week)

**PR link:** [PR-915](https://github.com/ascherj/pathreview/pull/915)

**Branch:** fix/146-pii-scrubber-parenthesized-phone-number-redaction

---

**What you built:**
The update was for the PII_PATTERNS dictionary in pii_scrubber.py. The dictionary holds the parameters/conditions for PIIs. "\b" looks for characters and does not account for non-characters like parentheses '()', so the fix to recognize parentheses phone numbers with PII_Scrubber.detect() and hide parentheses phone numbers with PII_Scrubber.scrub() was to add `(?<!\d)` at the front of the phone_us entry in PII_PATTERNS.

A seperate addition was `\b` at the end of the street address entry of PII_PATTERNS since another test, regarding street addresses, in the unit test for the PII_Scrubber was failing.

**Tests added or updated:**
No unit tests added, used the default tests that interact with the pii_scrubber.

However, added tests/security/debug_pii.py script to test scrub() and detect().

**Self-review confirmation:** [x] python pytest tests/unit/test_pii_scrubber.py -v passes

~~[ ] make check passes  [] make test-unit passes~~

**Draft PR feedback received from:** [stephanyTF](https://github.com/ascherj/pathreview/pull/915#issuecomment-5195409304) on GitHub and Stephany Lam on Slack
