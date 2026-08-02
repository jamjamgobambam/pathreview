## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/146](https://github.com/ascherj/pathreview/issues/146)

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The code used to hide sensitive personal information is currently missing a common phone number format: parenthesized US phone numbers. 

While it successfully catches numbers formatted with dashes (like 555-123-4567), it overlooks numbers written with parentheses (like (555) 123-4567). 

Because of this gap, parenthesized phone numbers slip through the system without being hidden or flagged as private data. A successful fix will make sure this standard phone number style is properly protected.

**Branch name:** [paste branch name here]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Is This Issue Right for Me?

### Part 1 — Understanding the Issue
- [x] Can I explain what this issue is asking for in my own words?
- [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
- [x] Do I understand which part of the app is affected?
- [x] I've located the relevant files and confirmed they exist in the codebase.
- [x] Do I understand what "done" looks like?
- [x] Can you describe what the app should do (or not do) once the issue is fixed? 
- [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

### Part 2 — Tier Fit
Issues in the tracker are tagged with a tier level. Here's what each one means:

#### Tier	Description	Typical scope
_Tier 1	Self-contained, localized fix. The change lives in one or two files and doesn't require understanding how the whole system fits together.	Bug fix, missing validation, broken test, documentation update_

_Tier 2	Requires understanding how two or more modules interact. May involve a service layer, database model, or API endpoint.	Feature addition, refactor, data flow bug_

_Tier 3	Requires understanding the full system — multiple modules, possibly infrastructure or AI pipeline changes.	Architecture change, cross-cutting behavior, RAG or agent modification_

- [x] Is the tier a realistic match for where I am right now?

### Part 3 — Codebase Readiness

_Can I find the relevant code?_

- [x] I've found and read the specific code the issue references (not just the file — the function or section).
Do I understand the surrounding code well enough to change it safely?
- [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
- [x] I've found the test file for my module and read at least one test end-to-end.

### Part 4 — Scope and Time

- [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- [x] Is the scope realistic for Weeks 8–9?
- [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
- [x] This issue has no open blockers or dependencies on other unresolved issues.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
__[link to commit documenting the reproduced issue]__

[Commit 5d1ee4c](https://github.com/novamapp/pathreview/commit/5d1ee4ceb81ee16698571db448c00fed9eda3a2e)

**Reproduction summary:**
__[1–2 sentences: How did you reproduce the issue? What did you observe?]__

I went to the file (`pii_scrubber.py`) contacting the root of my chosen issue [#146](https://github.com/ascherj/pathreview/issues/146). I added the code in the `Steps to reproduce` section of my issue and ran the code to reproduce the issue.

I also ran the test file (`tests/unit/test_pii_scrubber.py`) mentioned in my selected issue and confirmed that the relevant tests are failing.

**PLAN.md link:** 
__[link to PLAN.md in your fork]__

[PLAN.md](PLAN.md)

**Walkthrough video (recommended):** 
__[link to your Loom video, ≤2 min — recommended, not graded]__

[walkthrough video](media/issue_walkthrough.mkv)

**Blockers or open questions:**
N/A

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Not midweek but here is my progress. Completed the initial failure analysis. By reviewing the failing unit tests in `tests/test_pii_scrubber.py`—specifically `test_us_phone_formats` and `test_detect_phone_pii`—I identified the specific edge cases and delimiter combinations (such as `+1` country codes and non-standard spacing) that are currently bypassing the regex patterns in `PIIScrubber`.

**Next steps:**
- Draft and test updated pattern expressions for US phone numbers.
- Run `pytest` to confirm all previously failing phone redaction and detection tests pass.
- Address applicable linting and pre-commit issues by running `ruff check --fix` and `ruff format` prior to committing.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** 

[https://github.com/ascherj/pathreview/pull/559](https://github.com/ascherj/pathreview/pull/559)

**Branch:** fix/146-enhance-pii-scrubber

**What you built:**

The issue is that, in the class `PIIScrubber`, the `scrub` function fails to redact some common phone number patterns, and the `detect` function in the same class cannot detect this PII phone number information in these common patterns either. The root cause of this is likely that the regular expression programmed into the `PII_PATTERNS` constant (below) in the `PIIScrubber` class is inefficient at catching some of the common phone number patterns.

```Python
# current PII_PATTERNS constant in PIIScrubber class used to detect and scrub PII
PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_us": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
        "phone_intl": r"\+[0-9]{1,3}[-.]?[0-9]{1,14}",
        "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
        "street_address": r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Park|Pl|Plaza|Place|Drive|Dr|Way|Parkway|Pkwy|Point|Pt|Pike|Run|Summit|Summit|Terrace|Ter|Trail|Trl|Tunnel|Turnpike|View|Vista|Vlg|Village|Vly|Valley)",
    }
```

I hypothesized that the root cause of this is likely that the regular expression programmed into the `PII_PATTERNS` constant in the `PIIScrubber` class is inefficient at catching some of the common phone number patterns. To fix this, using the help of Gemini, I improved the US phone pattern to handle spaces, dashes, dots, and optional +1 country code. I also improved international phone pattern to handle spaces between blocks of digits.

**Tests added or updated:**

The test file relevant to these changes is `tests/test_pii_scrubber.py`.

My code resolved failures in the following existing tests:
- `test_us_phone_number_redaction`: 
    - Covers verifying that standard US phone numbers formatted with parentheses and dashes (e.g., `(555) 123-4567`) are correctly redacted to `[REDACTED]`.
- `test_us_phone_formats`: 
    - Covers checking that various common US phone number formats—including hyphenated, dot-delimited, space-separated, and country code-prefixed (`+1`) variations—are reliably detected and redacted.
- `test_detect_phone_pii`: 
    - Covers verifying that `detect()` identifies US phone numbers, categorizes them under the `phone_us` PII type, and returns their match metadata.
- `test_phone_at_start_of_text`: 
    - Covers ensuring that boundary anchor matching works correctly when a phone number appears at the very beginning of a string.

I also added a new unit test, `test_phone_number_partially_formatted_redaction`, which covers the edge case where a US phone number uses mixed delimiters (such as combining parentheses with dot separators like `(800).555.0199`) to ensure it is fully detected and redacted.


**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
NOTE: both of these checks pass in relation to my bug fix. There were existing failures for both checks that pre-date my fix. This is documented in my PR.

**Draft PR feedback received from:** [name or Slack handle, or "none"]
none