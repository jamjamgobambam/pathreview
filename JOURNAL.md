## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** Tier 1

**Problem summary:**
The phone-number pattern used in pii_scrubber.py only matches dashed formats like 324-901-1234. It does not match the parenthesized format (324) 901-1234, which is one of the most common ways US phone numbers are written.
As a result,
scrub() leaves numbers in this format completely unredacted in the output.
detect() incorrectly reports that no PII is present when the text contains a parenthesized phone number.

Expected behavior:
Both detect() and scrub() should recognize (324) 901-1234 as a phone number, alongside already-supported formats like 324-901-1234.

**Issue Selection Criteria**
- I understood the issue and the expected behavior clearly.
- I've located the relevant files and confirmed they exist in the codebase
- I've understood the surrounding code well
- I can describe clearly what the user sees before the fix and what they see after.
- I've selected Tier 1, as the scope is realistic for this first open source contribution. 
- It is self contained and there are no blockers and dependencies.
- I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- I've found the test file and read the related unit test cases.

**Branch name:** fix/146-PII-US-phone-no-format-parenthesis

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
- https://github.com/Thenmani/pathreview/commit/8c1280f, 
- https://github.com/Thenmani/pathreview/commit/6204c9f

**Reproduction summary:**
Wrote few failing test cases to confirm that both `detect()`
and `scrub()` fail to recognize parenthesized US phone numbers like `(324) 901-1234`.
`detect()` returns an empty list and `scrub()` leaves the number unredacted, confirming
the root cause is the `phone_us` regex in `safety/pii_scrubber.py`.

**Reproduction steps:**
1. Located the relevant file: `safety/pii_scrubber.py`, and the test file: `tests/unit/test_pii_scrubber.py`.
2. Added test cases, `test_paren_phone_reproduces_bug`, `test_paren_phone_detect_reproduces_bug`, `test_paren_phone_scrub_reproduces_bug` that calls `detect()` and `scrub()` on the input `"Call me at (324) 901-1234"`.
3. Ran the test.
4. Test failed, confirming the bug.

**Additional test cases written, to reproduce the bugs:**
Beyond the single required reproduction test, I wrote several more to explore
the shape of the bug more thoroughly. All of these currently fail, since the fix hasn't been applied yet.
- `test_phone_paren_no_space_after_close` — `(555)123-4567`
- `test_phone_paren_dash_after_close` — `(555)-123-4567`
- `test_phone_paren_dot_after_close` — `(555).123.4567`
- `test_detect_paren_phone_no_space` — confirms `detect()` also misses the no-space case
- `test_paren_phone_only_pii_detected` — confirms the false-negative when the
  parenthesized number is the only PII in the text
- `test_paren_phone_no_false_positive_on_short_numbers` — guards against short
  parenthesized numbers (e.g. footnote references like `(12)`) being misdetected
  as phone numbers

**PLAN.md link:** https://github.com/Thenmani/pathreview/blob/fix/146-PII-US-phone-no-format-parenthesis/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Identified the root cause: the `phone_us` separator class `[-.]?` did not
  include whitespace, so `(555) 123-4567` failed to match at the space after
  the closing parenthesis.
- Came up with an initial working fix — extended all three separator slots from
  `[-.]?` to `[-.\s]?` and replaced the leading `\b` with `(?<!\w)` for
  reliable boundary matching next to parentheses. Verified all reproduction
  tests passed.
- Optimized the fix further by removing unused capture groups `([0-9]{3})` →
  `[0-9]{3}` since `scrub()` uses a fixed replacement string and `detect()`
  reads the whole match — no backreferences needed.
- All reproduction tests now pass (`test_paren_phone_detect_reproduces_bug`,
  `test_paren_phone_scrub_reproduces_bug`).
- Added 3 additional edge-case tests: country code + parens combined,
  multiple phone numbers in one string, and a negative case for malformed
  2-digit area codes.
- Full suite: 37 passed, 1 failed — the one failure is a **pre-existing,
  unrelated bug** in the `street_address` pattern (`test_mixed_pii_and_text`):
  the pattern incorrectly matches the substring "Pl" inside the word
  "applications", partially redacting it as "[REDACTED]ications". This is out
  of scope for issue #146 and was present before this fix was applied.

**Fix implementation note:**
While committing `safety/pii_scrubber.py`, the pre-commit hooks (ruff) blocked
the commit due to 2 pre-existing errors in untouched lines:
- `B007` — unused loop variable `pii_type` in both `scrub()` and `detect()`
- `E501` — `street_address` pattern line too long (283 chars)

Fixed both as part of the commit:
- Renamed `pii_type` to `_pii_type` in both loops (underscore prefix signals
  intentionally unused to ruff).
- Split the `street_address` pattern across multiple lines using implicit
  string concatenation.

**Lesson learned:** During the rename, `detect()` accidentally referenced
the old `pii_type` name in the loop body while the loop variable was already
renamed to `_pii_type` — caused 11 test failures. Caught immediately by
running the full test suite. Also missed the same rename in `scrub()` on
the first attempt — ruff caught it on the next commit try. Run tests after
every change, even one-character renames.

**Self-review against contribution standards:**
Ran `make check` and `make test-unit` before opening the draft PR.

- `ruff check safety/pii_scrubber.py tests/unit/test_pii_scrubber.py` returned
  6 errors initially. Two were in my files (trailing whitespace in
  `test_pii_scrubber.py`) — fixed using `ruff check --fix`. The remaining 4
  errors are pre-existing in `safety/pii_scrubber.py` (unsorted imports,
  street_address pattern too long, unused loop variable, logger line too long)
  — none introduced by my changes.
- `make test-unit` result: 391 passed, 49 failed. All 49 failures are
  pre-existing across unrelated modules. Zero new failures introduced.
- In `tests/unit/test_pii_scrubber.py` specifically: 37 passed, 1 failed.
  The single failure (`test_mixed_pii_and_text`) is the pre-existing
  `street_address` false-positive bug — not related to this fix.

**Result:** My changes introduce no new failures in either `make check`
or `make test-unit`.

**Next steps:**
- Add remaining edge-case tests before final PR merge.
- Address any draft PR review feedback.
- Record Loom walkthrough video.
- Update `JOURNAL.md` with final Week 9 summary once all steps are complete.

**Blockers or open questions:**
None currently.

### Check-in 2 (end of week)

**PR link:** https://github.com/[upstream-repo]/pathreview/pull/391

**Branch:** `fix/146-PII-US-phone-no-format-parenthesis`

**What you built:**
Updated the `phone_us` regex in `safety/pii_scrubber.py` to accept
whitespace as a valid separator between number groups, so parenthesized
US phone numbers like `(555) 123-4567` are correctly detected and
redacted alongside already-supported dashed and dotted formats. Also
replaced the leading `\b` boundary anchor with `(?<!\w)` for reliable
matching next to parentheses, and removed unused capture groups to
simplify the pattern.

**Tests added or updated:**
- `tests/unit/test_pii_scrubber.py` — added 18 new tests covering:
  reproduction of the original bug (independently verified for both
  `detect()` and `scrub()`), parenthesized format variations (no space,
  dash, dot after closing paren), country code + parens combined,
  multiple numbers in one string, trailing punctuation, inside quotes,
  all-spaces separator, and negative cases (2-digit area code, 4-digit
  area code, 7-digit number, letters mixed in, year range, SSN shape,
  raw 10-digit number).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Loom walkthrough:** https://www.loom.com/share/7b2425dc1c98438d86a0d21f7b527a7e

**Draft PR feedback received from:** Received PR feedback from Jess, a senior at UC San Diego studying Data Science & Business, who is currently building risk models at Wells Fargo using traditional ML methods and LLM to automize previously manual process.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
A reviewer verified the fix locally — reproduced the bug on `main`, confirmed
my reproduction tests fail on `main` and pass on my branch, and confirmed the
full unit suite went from 53 to 49 failures with zero new failures introduced
(4 cleared). They also pressure-tested edge cases I hadn't explicitly called
out (long digit strings not over-matching, the `(55)` negative case holding,
the country-code variant working) and called out the reproduce-first tests
and negative case test as a strength.

They raised one substantive design question: the separator class `[-.\s]?`
uses `\s`, which matches not just spaces but also `\n` and `\t`. This meant
`scrub("324\n901\n1234")` — three unrelated numbers stacked on separate
lines, e.g. table columns — would get merged and redacted as a single fake
phone number. They noted over-redaction is arguably fine for a scrubber
(fail-safe bias) but flagged it as worth understanding as a design choice
rather than an accident.

**How you responded:**
Verified the concern directly — confirmed `"324\n901\n1234"` was in fact
matching as one number under the original pattern. Agreed it was an
unintended side effect rather than an intentional design choice, since
nothing in scope ever required tab or newline as a valid separator.
Narrowed the separator class from `[-.\s]?` to `[-. ]?` (literal space
only) in all three separator slots. Confirmed all existing tests still
passed with the narrower class, then added a new regression test,
`test_phone_does_not_merge_across_newlines`, to lock in the corrected
behavior. Committed and pushed the fix, then replied to the reviewer
explaining the change and thanking her for reviewing and pressure-testing the edges.

---

### Reflection

**What was harder than you expected?**
The regex fix itself was the easy part — the harder part was the mechanics
around it. I lost committed work twice when switching between PowerShell
and Git Bash mid-session, ended up with silently duplicated test methods
after a messy paste (Python just keeps the last definition, so pytest was
quietly running 43 tests when the file actually had 55 defined), and spent
real time chasing pre-commit hook failures (ruff, black, mypy) that had
nothing to do with my actual change but still blocked every commit until
resolved. None of that was visible from the issue description — it only
showed up by actually doing the work.

**What did you learn about working in a large codebase?**
A one-line bug fix is never really one line. Getting it merged means
understanding pre-existing lint/type debt well enough to prove your change
didn't cause it, running the full test suite (not just the file you touched)
to catch failures in unrelated modules, and documenting all of that clearly
enough that a reviewer doesn't have to take your word for it. I also learned
that "done" for a fix and "done" for a mergeable PR are different bars —
the second one includes tests, self-review, and being honest about what's
still broken elsewhere in the codebase. Peer review also turned out to
matter more than I expected: I had tested plenty of edge cases myself, but
the reviewer caught something I hadn't considered — `\s` matching newlines
and tabs, not just spaces — simply by testing an input I hadn't thought to
try. A second, independent set of eyes catches things that self-review
alone genuinely misses, even after you think you've covered every case.

**How did AI tools help — and where did they fall short?**
AI was most useful for two things: systematically generating and verifying
edge cases (running dozens of inputs against the regex before writing tests,
rather than guessing), and untangling git/terminal issues in the moment —
diagnosing why a commit was blocked, why 12 tests silently disappeared, why
"nothing to commit" showed up after a terminal switch. Where it fell short
was catching my own copy-paste mistakes before they happened — the duplicate
test methods and indentation errors came from me pasting code by hand, and
AI could only help diagnose them after the fact, not prevent them. 

**What would you do differently if you started over?**
I'd verify the test file's actual state (`grep -c "def test_"`) after every
paste instead of assuming the edit landed correctly — that would have caught
the duplicate methods immediately instead of after a confusing "1 failed,
26 passed" surprise. I'd also stick to one terminal environment for the
whole session instead of switching between PowerShell and Git Bash, since
that's what caused me to lose staged changes twice.

**What are you most proud of from this module?**
What stands out most is having carried the complete open-source contribution workflow through
to the end (Reproduce, plan, fix, test, self-review, draft PR, raise PR, respond
to review feedback, fix and iterate). Also the moment of handling reviewer's feedback
on the `\s` separator issue, smoothly closing the loop with validating, fixing, regression testing and responding, so the same
issue can't silently return.
