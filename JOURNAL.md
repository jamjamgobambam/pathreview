## Week 7 — Issue selection

**Issue link:** [#146 — PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` is responsible for detecting and redacting personally identifiable information, like phone numbers, from text before it's processed or stored. Its phone number pattern currently matches dash-separated formats like `555-123-4567`, but it fails to match the common parenthesized format `(555) 123-4567`. As a result, when text contains a number written that way, `scrub()` leaves the phone number fully exposed instead of replacing it with `[REDACTED]`, and `detect()` reports no phone PII at all (returning an empty list). I confirmed this by running the four related tests in `tests/unit/test_pii_scrubber.py`, which fail because the parenthesized number passes straight through unredacted. A successful fix would update the phone number regular expression so parenthesized numbers are detected and redacted, while keeping the already working dash separated format intact, turning those four failing tests green. When I ran the suite, a fifth test also failed (`test_mixed_pii_and_text`), but that's caused by a separate over redaction bug unrelated to phone numbers, so it's outside the scope of this issue.

## "Is This Right for Me?" Checklist & Selection Notes
- **Part 1 — The affected area is the `safety` module. I located `safety/pii_scrubber.py` and confirmed the phone-number pattern lives there. "Done" means `(555) 123-4567` is redacted by `scrub()` and reported by `detect()`, with the dashed format still working.

- **Part 2 — Tier Fit:** This is a Tier 1 issue and it matches my experience, as a first time contributor to this codebase, I wanted a localized, single-file fix rather than a cross module change. I'm not reaching for a Tier 3 to "challenge myself" before completing a Tier 1.

- **Part 3 — Codebase Readiness:** I opened `safety/pii_scrubber.py` and read the `scrub()` and `detect()` functions and the phone regex. I read the relevant tests in `tests/unit/test_pii_scrubber.py` and ran the suite to reproduce the four failures.
- 
**Part 4 — Scope & Time:** No blockers or dependencies are listed. The scope fits the Tier 1 estimate (3–6 hrs) — likely less, since it's a single regex change. I'm confident I can complete it before the Week 9 deadline. I checked the issue comments and the ledger Claims count and I'm comfortable with how many others are on it.

**Branch name:** `fix/146-pii-scrubber-parenthesized-phone`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue # 146 added to cohort ledger




## Week 8 — Reproduction & solution planning

**Reproduction commit link:**

https://github.com/ascherj/pathreview/commit/dcd409f7596533f3cb64edea77ee9514911aa839

**Reproduction summary:**
I reproduced issue #146 by running `pytest tests/unit/test_pii_scrubber.py -q` with the virtual environment active, which produced `5 failed, 20 passed`. The four phone-related tests (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`) fail because the parenthesized format `(555) 123-4567` is not redacted. I also confirmed it interactively:
`PIIScrubber().scrub('Call me at (555) 123-4567 or 555-123-4567')` returns `'Call me at (555) 123-4567 or [REDACTED]'` — the dashed number is redacted but the parenthesized one is left exposed and `detect()` returns an empty list for it.

**PLAN.md link:**

https://github.com/KingJNF/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md


**Walkthrough video (recommended):** N/A

**Blockers or open questions:**