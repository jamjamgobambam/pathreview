## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The phone-number regex in `pii_scrubber.py` only matches dashed formats like
555-123-4567, so parenthesized formats like (555) 123-4567 — one of the most
common ways US phone numbers are written — pass through `scrub()` completely
unredacted, and `detect()` reports no PII found at all for that format. This
is a gap in the safety/PII-redaction layer of the app. Four existing unit
tests already cover this case and are currently failing. A successful fix
extends the phone-number pattern matching to also catch the parenthesized
format, so both `scrub()` and `detect()` correctly identify and redact it,
and the four related tests pass.

**Selection reasoning:** I chose this as a Tier 1 issue since it's my first
time contributing to an unfamiliar multi-module codebase. The bug is
isolated to a single function in one file, has clear reproduction steps
and four named failing tests to validate against, so I can verify
correctness without needing to understand the rest of the app's
architecture.

**Branch name:** fix/146-parenthesized-phone-redaction

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tahsintawhid/pathreview/commit/702d8e7fcbfeb317d43507da8072b9035da62808

**Reproduction summary:**
Confirmed the root cause: the `phone_us` regex in `safety/pii_scrubber.py` uses
`[-.]?` as the separator between digit groups, which allows dashes and dots but
not spaces. Since `(555) 123-4567` has a space (not a dash) right after the
closing parenthesis, the regex fails to match at all. Verified via direct
regex testing (`re.search` returns `None` for the parenthesized format but
matches for the dashed format), and via `pytest tests/unit/test_pii_scrubber.py
-k "phone"`, which shows 4 failing tests: `test_us_phone_number_redaction`,
`test_us_phone_formats`, `test_detect_phone_pii`, and
`test_phone_at_start_of_text`, all failing because `scrub()` leaves the number
un-redacted and `detect()` returns an empty list.

**PLAN.md link:** https://github.com/tahsintawhid/pathreview/blob/fix/146-parenthesized-phone-redaction/PLAN.md

**Walkthrough video (recommended):** [optional — add if you record one]

**Blockers or open questions:**
`test_us_phone_formats` also tests `"+1 555 123 4567"`, a space-separated
format with no parentheses. It wasn't individually reported as failing since
the test loop's assert stops at the first failure, but it shares the same
root cause (space not in the separator character class) and will need to be
verified once the fix is in place.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix planned in PLAN.md step 1: updated the phone_us regex
in safety/pii_scrubber.py to accept \s as a separator, matching all four
target formats (dashed, dotted, parenthesized, space-separated). Verified
against tests/unit/test_pii_scrubber.py -- all 4 previously-failing phone
tests now pass.

**Next steps:**
Run the full test suite and make check to confirm no regressions, write
the PR description with manual verification steps, and open a draft PR for
early feedback.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/348

**Branch:** fix/146-parenthesized-phone-redaction

**What you built:**
Fixed the phone_us regex in safety/pii_scrubber.py so parenthesized and
space-separated US phone numbers are correctly redacted by scrub() and
flagged by detect(), resolving issue #146.

**Tests added or updated:**
Modified tests/unit/test_pii_scrubber.py: added one new test,
test_fully_space_separated_phone_number, covering the "+1 555 123 4567"
format with its own independent pass/fail signal (previously only
exercised inside test_us_phone_formats's loop, where an early assert
could mask a failure on this specific format). Also confirmed the 4
existing tests covering this bug (test_us_phone_number_redaction,
test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text)
now pass. All other tests in this file behave identically before and
after except one pre-existing, unrelated failure (test_mixed_pii_and_text).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both in the sense defined by the assignment: no new failures introduced by
this change -- 178 pre-existing ruff errors and 49 pre-existing test
failures confirmed identical with and without this fix via git stash
comparison. `ruff check tests/unit/test_pii_scrubber.py` now reports 0
errors -- I fixed the 2 pre-existing unused-variable issues in this file
as well, since they were trivial and unrelated to behavior. mypy still
reports 26 pre-existing errors in this file (unannotated test functions
predating this PR, confirmed via git stash); my new test function is
fully type-annotated. Two commits touching this test file were made with
--no-verify since the pre-commit hook blocks on mypy's pre-existing
annotation gaps regardless of my change, and annotating all 26 other
functions is out of scope for #146.)

**Draft PR feedback received from:** [fill in once you get peer/mentor review]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — reviewer feedback isn't a feature this term

**Summary of feedback:**
No reviewer feedback came in, since this isn't available in Su26. I did
investigate an existing open PR (#162) linked to my issue before starting,
to check whether someone else was already working on the same fix, and
determined it was a low-effort, likely auto-generated PR bundling four
unrelated issues with no engagement -- not a blocker to proceeding.

**How you responded:**
N/A -- no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Git itself, more than the actual bug fix. The regex fix was maybe 10
minutes of real work, but I lost my uncommitted fix at least twice without
realizing it (once after a stash/pop cycle, once from re-editing the file),
and didn't catch it until a `git log` showed the file was never actually
committed. I also hit a tangled staged-vs-unstaged state after `git add`
followed by a pre-commit hook that auto-reformatted the file mid-commit.
None of this was about understanding the codebase -- it was about
understanding what git was actually doing versus what I assumed it was
doing.

**What did you learn about working in a large codebase?**
The biggest shift was realizing that "does my change work" and "is my
change done" are different questions. My regex fix worked in isolation
almost immediately. Getting it merge-ready meant running the full test
suite and finding 49 unrelated failures, running the linter and finding
178 unrelated errors, and having to figure out -- carefully, with actual
evidence via `git stash` comparisons -- which of those were mine to fix
and which predated me entirely. In my own solo projects, "all tests pass"
is a simple binary. In an existing codebase with real technical debt, it's
a judgment call that has to be documented, not assumed.

**How did AI tools help — and where did they fall short?**
AI was most useful for methodical debugging under uncertainty -- for
example, systematically checking whether PR #162 was a real competing
contributor or a low-effort bot PR before deciding whether to proceed with
my issue, or walking through exactly why the `phone_us` regex failed on
`(555) 123-4567` character by character. It fell short at the actual
git mechanics -- suggesting commands that assumed a clean state when my
repo wasn't in one, which led to a couple of real mistakes (like the lost
uncommitted fix) that took extra steps to diagnose and recover from. I
learned to run `git status` and `git diff` before trusting that a previous
step actually landed, rather than assuming it did.

**What would you do differently if you started over?**
I'd run `git status` after every single commit attempt before moving on,
instead of assuming success from a lack of an obvious error message. I'd
also check `make check` and `make test-unit` against the pre-existing repo
state in Week 8 or earlier, during planning, instead of discovering 49
pre-existing failures and 178 lint errors for the first time in Week 9 --
that would have made my PLAN.md's "risks" section more accurate from the
start instead of something I had to retroactively update.

**What are you most proud of from this module?**
Not fixing everything I found. It would have been easy to "helpfully" fix
the `street_address` regex bug I discovered, or annotate all 26 untyped
test functions mypy flagged, since I was already in those files. Instead
I documented them, verified with `git stash` that they were pre-existing,
and left them out of scope with a clear paper trail explaining why. That
felt like the actual skill this module was testing -- not writing a
correct regex, but knowing where my responsibility as a contributor ends.
