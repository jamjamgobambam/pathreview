## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/146)

**Issue title:** [PII scrubber fails to redact parenthesized US phone numbers
 #146

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber currently recognizes US phone numbers written with dashes (such as 555-123-4567), but it does not detect or redact the common parenthesized format (555) 123-4567. As a result, scrub() leaves these numbers unredacted, and detect() incorrectly reports that no PII is present. This issue affects the phone number matching logic in pii_scrubber.py. A successful fix would update the phone number pattern so both dashed and parenthesized US phone number formats are correctly detected and redacted, allowing the related unit tests to pass.

**Branch name:** fix/146-pii-scrub-phone-num

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger





## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/sr-0397/pathreview/tree/fix/146-pii-scrub-phone-num)


**Reproduction summary:**
Ran the repro script (the scratch_repro.py) from issue #146 locally and confirmed scrub() leaves
"(555) 123-4567" unredacted while the dashed format is caught, and detect()
returns [] for the parenthesized number. Confirmed via 4 failing tests in
tests/unit/test_pii_scrubber.py.

**PLAN.md link:** (https://github.com/sr-0397/pathreview/tree/fix/146-pii-scrub-phone-num)

**Blockers or open questions:**
Not sure how to deal w edge cases yet...
- Phone number at the very start or end of a string
- Multiple phone numbers, mixed formats, in one string
- Numbers with a leading "+1" country code plus parens





## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for 146 by updating the phone_us regex in
safety/pii_scrubber.py to accept whitespace as a valid separator
alongside dashes and dots, which resolves the boundary/separator issue
that was blocking parenthesized phone numbers like "(555) 123-4567"
from being matched. Verified locally: all 6 phone-related tests in
tests/unit/test_pii_scrubber.py now pass, including the 4 that were
previously failing (test_us_phone_number_redaction, test_us_phone_formats,
test_detect_phone_pii, test_phone_at_start_of_text). Ran a full
make test-unit before/after comparison via git stash to confirm scope:
53 failed/375 passed before my change vs. 49 failed/379 passed after —
a net swing of exactly 4 tests (fail to pass), with no new failures
introduced anywhere else in the suite. Also confirmed via ruff check
that the 4 pre-existing lint issues in pii_scrubber.py predate this
change and aren't caused by the edited line.

**Next steps:**
Run make check across the full repo, review docs/CONTRIBUTING.md for
branch naming and commit message conventions, open a draft PR for peer
feedback

**Blockers:**


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/179

**Branch:** fix/146-pii-scrub-phone-num

**What you built:**
Fixed the phone_us regex in safety/pii_scrubber.py so it correctly
matches and redacts parenthesized US phone numbers (e.g. "(555) 123-4567"),
by allowing whitespace as a valid separator character in addition to
dashes and dots.

**Tests added or updated:**
tests/unit/test_pii_scrubber.py — no new tests added; the 4 existing
tests tied to this bug (test_us_phone_number_redaction,
test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text)
now pass.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** not yet




## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review came in

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Getting the environment running was more friction than I expected —
missing structlog, then missing pytest, before I could even confirm the
bug was real. Once I got past that, the regex fix itself looked simple
on paper but had a subtle trap: my first fix (allowing whitespace as a
separator) worked perfectly for the target bug, but it also caused an
unrelated test (test_mixed_pii_and_text) to fail. Tracing that down
took real work — running each PII pattern individually against the test
text to isolate which one was actually matching "Python appl..." It
turned out to be a completely different bug in the street_address
pattern that had nothing to do with my change, but I couldn't have known
that without digging in and comparing before/after with git stash.

**What did you learn about working in a large codebase?**
The biggest shift was realizing that "my tests pass" isn't the same as
"my change is safe." Running make test-unit surfaced 53 pre-existing
failures across files I never touched, and I had to learn to
distinguish "did I break this" from "was this already broken." The
git stash before/after comparison became my main tool for that — it's
not something I'd have needed on a solo project where I know every line
I wrote. Scoping a PR to exactly the tests relevant to my issue, and
documenting the rest as pre-existing rather than trying to fix
everything, was a different mindset than "make the whole test suite
green."

**How did AI tools help — and where did they fall short?**
AI was most useful for explaining *why* the regex failed at the
character level — walking through how \b interacts with non-word
characters like "(" and why an optional separator class doesn't mean
"optional whitespace." That kind of regex-engine reasoning would have
taken me much longer to work out by trial and error alone. Where it
fell short was catching the side effect of my own fix — I had to
actually run the tests myself and bring the failure back before we
could diagnose the street_address regression together. AI didn't
predict that my change would interact with an unrelated pattern; I had
to discover that empirically.

**What would you do differently if you started over?**
I'd run the full test suite baseline (make check and make test-unit)
before writing any fix, not after — having the "before" numbers ready
from the start would've made it faster to prove scope once I had a
working fix, instead of doing the stash comparison retroactively. I'd
also probably test my first regex draft against a wider set of inputs
(not just the phone formats) before considering it done, since that's
exactly what would've caught the street_address interaction earlier.

**What are you most proud of from this module?**
Catching the regression myself before it went into the PR. It would've
been easy to see "4 tests I care about now pass" and stop there — but
running the full suite and noticing test_mixed_pii_and_text had flipped
status is what kept the fix honest. That habit of checking the blast
radius, not just the target, feels like the most useful thing I'm
taking out of this week.