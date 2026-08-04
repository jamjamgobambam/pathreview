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




## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the core fix from my PLAN.md. I updated the `phone_us` regex in `safety/pii_scrubber.py` so the separators accept whitespace, which makes the parenthesized `(555) 123-4567` format match. Sub-tasks 1 and 2 from my plan are done. The regex is modified, and running `pytest tests/unit/test_pii_scrubber.py -q`
confirmed the four target tests now pass (went from 5 failed/20 passed to 1 failed/24 passed) 

**Next steps:**
Add a test for the parenthesized-no-space edge case (`(555)123-4567`), re-verify that no new lint/test failures were introduced, then open the PR to pathreview and fill in the template.

**Blockers:**
None. The one remaining test failure (`test_mixed_pii_and_text`) is a pre-existing `street_address` over-redaction bug, unrelated to my change and out of scope.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/281

**Branch:** `fix/146-pii-scrubber-parenthesized-phone`

**What you built:**
I broadened the `phone_us` regex in `safety/pii_scrubber.py` so its separators also accept whitespace, allowing the common `(555) 123-4567` format to be matched and redacted by both `scrub()` and `detect()`. Previously these numbers passed through completely unredacted. No function signatures changed as only the regex pattern was updated.

**Tests added or updated:**
I added `test_us_phone_parenthesized_no_space` in `tests/unit/test_pii_scrubber.py`, covering the parenthesized-with-no-space format `(555)123-4567`. This complements the four existing phone tests my fix repairs (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`). After my changes the suite shows 25 passed, 1 pre-existing unrelated failure.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [ ] No — still awaiting review

**Summary of feedback:**
[TO FILL NEAR DEADLINE — check PR #281 and summarize any reviewer comments here.]

**How you responded:**
[TO FILL NEAR DEADLINE — describe changes made or replies given.]

---

### Reflection

**What was harder than you expected?**
The setup was harder than the actual fix. Getting the local environment running was a pain. Docker containers for PostgreSQL and Redis, plus the virtual environment took much longer than I anticipated, and I couldn't run a single test until it was all correct. By contrast, the fix for issue #146 came down to changing a few characters in one regex. I expected the coding to be the challenge, but the real friction was almost everything before it like the setup, git mechanics, and figuring out what "done" actually meant in someone else's repo.

**What did you learn about working in a large codebase?**
The biggest shift was learning that "passing" doesn't mean the whole codebase is clean. When I ran `make check` I got 182 lint errors, and `make test-unit` had a failing test (`test_mixed_pii_and_text`) that had nothing to do with my issue. The `street_address` regex was over-redacting and swallowing the word "Python." In my
own projects I'd assume any red meant I broke something, but here I had to record a baseline first and then prove my change added no *new* failures. Contributing to production code someone else owns is as much about tight scoping and leaving unrelated things alone as it is about writing the fix itself.

**How did AI tools help and where did they fall short?**
AI was most useful for tracing exactly why the `phone_us` regex failed. walking the pattern against `(555) 123-4567` character by character and showing that the `[-.]?` separator rejected the space after the closing paren made the fix (`[-.]?` →`[-.\s]?`) obvious. It also helped me structure my PLAN.md and PR description. Where
it fell short was it couldn't run anything for me. I still had to reproduce the failure, run pytest, and confirm the count moved from five failed tests to one failed test myself. AI could reason about the code, but it couldn't verify the true state of my machine or confirm the pre-existing failures were genuinely pre-existing until I ran the baseline commands.

**What would you do differently if you started over?**
I'd budget far more time for environment setup instead of underestimating it, and I'd capture the `make check` / `make test-unit` baseline on day one rather than discovering the 182 lint errors and the pre-existing failing test partway through. That would have saved some anxiety about whether I'd broken something. On the planning
side, the edge cases I listed in PLAN.md (like the no-space `(555)123-4567` format) turned out to be genuinely useful, so I'd write those edge-case tests earlier in the process instead of adding them near the end.

**What are you most proud of from this module?**
I'm most proud of how cleanly I kept my change scoped. It was tempting to "fix" the 182 lint errors or the `street_address` over-redaction bug I stumbled on, but I documented those as out-of-scope in my PLAN.md and PR instead, and shipped a focused fix that turned four failing tests green plus one edge-case test I added myself.
Submitting a real PR (#281) to a repository I didn't create and having it be a tight, well-documented contribution rather than a sprawling one feels like a genuine milestone.