# Journal

## Week 7 — Choosing an issue

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/84

**Issue title:** Add pagination to GET /reviews list endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue requests adding `page` and `page_size` query parameters to `GET /reviews` so users with a large number of reviews do not receive one oversized response. After reviewing the code, I found that this functionality had already been implemented. Both `api/routes/reviews.py` and `core/services/review_service.py` already supported `page` and `page_size`, converted them into offset and limit values, and used a default page size of 20.

The remaining issue was the way the total review count was being determined. The code loaded every matching review row into memory and then called `len()` on the resulting list instead of asking Postgres to calculate the count directly. This meant that even though the returned response was paginated, the server still performed a complete scan of the user’s matching reviews on every request. That creates essentially the same performance concern the original issue was meant to solve.

I narrowed the scope of my change to this problem: replace the existing count logic with a SQL `COUNT()` query so the database returns the total without loading all rows into memory.

**Scope notes:**
Before selecting the issue, I worked through the “is this right for me” checklist. It was labeled Tier 1 and good first issue, the required change was isolated to one file, and I could validate the behavior end to end by signing into the running application and calling the endpoint with a real authentication token rather than only reviewing the source code.

The main thing that made me hesitate was realizing that the issue, as it was literally described, had already been handled in the repository. I tested the endpoint through the live local app before assuming the issue was fully complete, and that testing is what helped me find the remaining count-query performance problem underneith it.

**Branch name:** perf/84-reviews-count-query

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** n/a Done as TF assignment

## Week 8 — Reproduction and solution planning

**Reproduction commit link:** [320d5cb — test(safety): reproduce parenthesized US phone number scrub gap](https://github.com/srijanipre/pathreview/commit/320d5cb)

**Reproduction summary:**
I moved to issue [#146](https://github.com/jamjamgobambam/pathreview/issues/146). The pagination issue selected during Week 7 turned out to already be effectively implemented, and I had already narrowed that work to the count-query performance improvement on the `perf/84-reviews-count-query` branch.

I ran the exact reproduction example from the issue description against `PIIScrubber` and confirmed the failure. Calling `scrub('Call me at (555) 123-4567 or 555-123-4567')` leaves the parenthesized number unchanged while correctly redacting the dashed number. Calling `detect('Call me at (555) 123-4567')` returns `[]`.

I added a strict `xfail` test called `test_parenthesized_phone_number_reproduction` that captures this exact behavior. I also confirmed that five existing tests were already failing because of the same underlying problem: `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, and `test_phone_at_start_of_text`. The fifth failing test, `test_mixed_pii_and_text`, was traced to a seperate, unrelated pre-existing bug in the street-address regex.

**PLAN.md link:** [PLAN.md](https://github.com/srijanipre/pathreview/blob/fix/146-parenthesized-phone-redaction/PLAN.md)

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
There are two items that need to be resolved before implementation next week.

First, I need to confirm whether expanding the separator character class to support whitespace will cause `phone_us` and `phone_intl` to both match phone numbers formatted like `+1 555 123 4567`.

Second, I need to determine how to handle the pre-commit hooks for `tests/unit/test_pii_scrubber.py`. The file currently fails because of existing linting and type-checking problems that are unrelated to my change. I verified that these failures existed before my edit by stashing my changes and running the checks again. After discussing it with a reviewer, I committed the reproduction test using `--no-verify`.

I am also documenting, but not fixing, the unrelated `street_address` false-positive involving `"Pl"` that appears in `test_mixed_pii_and_text`. That problem looks like it should be reported and handled as its own seperate issue.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the actual regex fix for issue #146 in safety/pii_scrubber.py. The phone_us pattern now allows whitespace as a seperator (not just dash or dot), and I swapped the leading \b for a (?<!\w) lookbehind so the optional opening paren actually gets included in the match instead of getting dropped. This was the exact root cause I wrote up in PLAN.md, so this week was mostly just executing that plan rather then discovering anything new.

Removed the strict xfail marker on test_parenthesized_phone_number_reproduction since it passes for real now. Ran the full pii_scrubber test file and confirmed all 4 target tests pass (test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text), plus the reproduction test.

Also ran the whole make test-unit and make check across the repo to check i didnt break anything else. Baseline before my change was 53 failed / 375 passed / 1 xfailed. After my change its 49 failed / 380 passed — exactly the 4 tests I targeted flipped to passing, zero new failures. make check has 181 pre-exisitng ruff errors repo wide and thats identical before and after my change too, so nothing new there either.

**Next steps:**
Fill out the PR template fully, including documenting the pre-existing failures so they dont get mistaken for something my change broke. Then adress any feedback and finalize.

**Blockers:**
None really. The one thing that took extra time was making sure the pre-existing failures (49 of them, mostly totally unrelated modules like test_review_service.py and test_bias_detector.py) were actually pre-existing and not something I accidentally touched — had to stash my change and rerun the suite to double check the before/after counts line up.

---

### Check-in 2 (end of week)

**PR link:** [to be filled in once opened — see PR draft instructions]

**Branch:** `fix/146-parenthesized-phone-redaction`

**What you built:**
Fixed the phone_us regex in the PII scrubber so it also catches parenthesized and space-seperated US phone numbers like "(555) 123-4567" and "+1 555 123 4567", which were previously passing through scrub() completely unredacted. The fix is a one line regex change plus removing the xfail marker from the reproduction test added in week 8.

**Tests added or updated:**
tests/unit/test_pii_scrubber.py — the reproduction test from week 8 (test_parenthesized_phone_number_reproduction) no longer needs its xfail marker since it passes for real now. No new test files needed, the existing suite already had the coverage (test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text) — they were just failing before the fix.

**Self-review confirmation:** [x] make check passes (for my changed files — repo-wide has 181 pre-exisitng ruff errors unrelated to this change, documented in PR description) [x] make test-unit passes (49 pre-exisitng unrelated failures documented in PR description, my change fixes 4 and introduces 0 new ones)

**Draft PR feedback received from:** 
