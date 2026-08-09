## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146#

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** Tier 1

**Problem summary:**
The personal information scrubbery in pii_scrubber.py is not redacting phone numbers with a parenthesized beginning format. The scrub is not redacting and the format is not being detected. A successful fix would lead to the parenthesized format of phone numbers being detected and redacted from text. This file is in the safety folder, but I cannot find reference to it outside the test suite. So I assume it is not integrated into the project and not affecting other files. 

**Branch name:** fix/146-pii-scrubber-phone-number

**Setup confirmation:** Yes, app runs locally at localhost:5173.

**Cohort ledger:** Yes, issue was added to cohort ledger.

## "Is this right for me?" Checklist:
### Tier Fit
- Is this an appropriate tier for my experience? Yes, because I have not done open source contributions, and I have fixed similar bugs before.

### Codebase Readiness
- **Relevant function/module found:** pii_scrubber.py
- **Rough implementation plan:**
  1. Run relevant tests to replicate the bug.
  2. Read the file.
  3. Identify the code likely responsible.
  4. Propose the fix.
  5. Test the fix
  6. Run entire test suite. 
  7. Repeat if issue is not reolved.

- **Relevant test files:**
- test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text in tests/unit/test_pii_scrubber.py

### Scope & Time
- **Others already working on it?** When I first went to claim it no, but now there are many others working on it.
- **Estimated time:** 2-3 hrs
- **Can I finish before the deadline?** Yes, seems like a minor issue. I have solved similar bugs before.
- **Dependencies/blockers:** None

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue](https://github.com/a-maryam/pathreview/commit/7ac52cff2e60e3c8cf7efe38fd7847ba22a823be)

**Reproduction summary:**
I reproduced the issue by following the instructions for the bug on github: 

I ran the following script in the project root:
```
# script to reproduce pii bug
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pii_scrubber import PIIScrubber
s = PIIScrubber()
print(s.scrub('Call me at (555) 123-4567 or 555-123-4567'))
# observed: 'Call me at (555) 123-4567 or [REDACTED]'
print(s.detect('Call me at (555) 123-4567'))
# observed: []
```
**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed all steps. Came up with a fix, applied code fix, wrote tests, ran full test suite. 

**Next steps:**
Check formatting and make all necessary commits/journals.

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** [link to submitted pull request\](https://github.com/ascherj/pathreview/pull/1017)

**Branch:** fix/146-pii-scrubber-phone-number

**What you built:**
I fixed the regex, so that a space counts as a separator and the matching doesn't break after the ). Also put \b before the first digit group so that the position there is a boundary between a word character and a non-word character. Fixes the regex of the redactor to catch phone number formats of the type (555) 774-3242

**Tests added or updated:**
test_pii_scrubber.py. Added tests to check that phone numbers of the type (555) 123-4567 are redacted. Tested (555)-123-4567, a similar type. Added test to check that similar pattern not meeting phone number length was not matched. Tested detect() to make sure that it was catching the full phone number. 

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** [none]
