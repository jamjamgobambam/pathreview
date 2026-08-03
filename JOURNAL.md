## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers


**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Reasoning:**
I chose this issue beause it's a self-contained Tier 1 bug which is a good fit for my first open source contribution. It lives entirely in one file (pii_scrubber.py), so I can understand the full scope without needing to trace through multiple modules or services. I also picked it because it gave me a chance to sharpen my regex skills by working through a concrete word boundary edge case rather than just reading about one. At the time I found it, there was no one else who was working on it and it had no blockers. This made me confident that I could realistically finish it within the Weeks 8-9 timeline. 

**Problem summary:**
Formats like (555) 123-4567 go through the function unredacted and dashed formates like 555-123-4567 are caught. In pii_scrubber.py, the phone number regex uses a \b word boundary that fails whenever a number starts with "(" because there's no valid boundary between a space and a parenthesis. A sucessful fix replaces the boundary anchors with digit-based checks and allows spaces as separators, so both fromats get redacted and all four failing tests pass. 

**Branch name:** fix/146-pii-scrubber-phone-parens

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [ea6b593](https://github.com/malhiya/pathreview/commit/ea6b5938f8b2626455b6659e1c98e8754ffc6b46)

**Reproduction summary:**
<!-- [1–2 sentences: How did you reproduce the issue? What did you observe?] -->
In the terminal, I created a short python script that created a PIIScrubber() object, and passed a text input with a parenthisized phone number (555) 123-4567 and the dashed format 555-123-4567  into the scrub() and detect() methods. Both functions were observed to only recognize/redact the dashed format and not flag/redact the parenthisized format, confirming the bug. 

```bash
python3 -c "
from safety.pii_scrubber import PIIScrubber
s = PIIScrubber()
print(s.scrub('Call me at (555) 123-4567 or 555-123-4567'))
print(s.detect('Call me at (555) 123-4567'))
print(s.detect('Call me at 555-123-4567'))
"
```

**Output:**
```
Call me at (555) 123-4567 or [REDACTED]
[]
[{'type': 'phone_us', 'value': '555-123-4567', 'start': 11, 'end': 24}]
```

**PLAN.md link:** [PLAN.md](https://github.com/malhiya/pathreview/blob/fix/146-pii-scrubber-phone-parens/PLAN.md)

<!-- **Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded] -->

**Blockers or open questions:**
Anything you're still uncertain about going into Week 9, or leave blank


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
<!-- [What have you implemented so far? Which sub-tasks from PLAN.md are done?] -->
Completed sub-task 1 from PLAN.md by updating the phone_us regex in src/safety/pii_scrubber.py, replacing the word boundaries with digit-based lookarounds and adding whitespace as a valid separator. Also cleaned up two overly long lines and removed an unused loop variable to satisfy the linter. The fix is committed and pushed to the fix/146-pii-scrubber-phone-parens branch.

**Next steps:**
<!-- [What are you working on for the rest of the week?] -->
Re-run the full test suite to confirm the four previously-failing tests pass along with the false-positive test. Add a new test case for the parenthesized format if it's not already covered, then manually check a few edge cases before opening the PR.

**Blockers:**
<!-- [Anything slowing you down? Or leave blank.] -->
None currently.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `fix/146-pii-scrubber-phone-parens`

**Branch Link:** https://github.com/malhiya/pathreview/tree/fix/146-pii-scrubber-phone-parens

**What you built:**
<!-- [1–3 sentences summarizing what your fix does and how it works] -->
Fixed the phone_us regex in pii_scrubber.py so it correctly matches parenthesized phone numbers like (555) 123-4567, which previously slipped through scrub() and detect() untouched. The fix replaces the \b word boundary with digit-based lookarounds ((?<!\d) and (?!\d)), since a leading ( broke the original boundary check, and also allows whitespace as a valid separator between digit groups.

**Tests added or updated:**
<!-- [Which test files did you touch? What do they cover?] -->
Updated tests/unit/test_pii_scrubber.py. Added two new tests: 

1. test_parenthesized_phone_no_space, which checks a parenthesized phone number with no space before the next digit group

2. test_detect_parenthesized_phone_value_accurate, which confirms detect() captures the full parenthesized phone number as its matched value.

The four pre-existing tests tied to this issue (test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text) now pass as a result of the regex fix.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

<!-- **Draft PR feedback received from:** [name or Slack handle, or "none"] -->
