# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` uses a regular expression to find and
redact US phone numbers. That regex only recognizes the dashed format, like
`555-123-4567`. It misses the parenthesized area code format, like
`(555) 123-4567`, even though that's a very common way people write phone
numbers. Because of this, `scrub()` leaves parenthesized numbers untouched in
the output text, and `detect()` reports no PII found when a parenthesized
number is present in the input. That's a false negative in a component whose
whole job is catching this kind of data. A correct fix updates the phone number
pattern so it matches both formats, which should make the existing failing
tests pass: `test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, and `test_phone_at_start_of_text`.

**Branch name:** fix/146-parenthesized-phone-regex

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jaystopthinkingjuststart/pathreview/commit/5e68e7d

**Reproduction summary:**
Ran the four tests named in the issue (`test_us_phone_number_redaction`,
`test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`)
and confirmed all four fail on `main`. Also isolated the root cause directly:
the `phone_us` regex in `safety/pii_scrubber.py` starts with `\b`, and `\b`
never matches at a position between a space and a `(`, since neither side is
a word character. So any phone number written as `(555) 123-4567` is silently
skipped by both `scrub()` and `detect()`, while the dashed format
`555-123-4567` matches fine.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to decide the exact replacement for the leading `\b` (negative lookbehind
vs. restructuring the optional group) and confirm it doesn't change match
priority against the `phone_intl` pattern for inputs like `+1 555 123 4567`.

## Week 9 — Implementation

**Fix commit:** 09e9cd9

**What changed:**
`safety/pii_scrubber.py` — replaced the leading `\b` in the `phone_us`
pattern with a negative lookbehind `(?<![\w)])`, and widened the
`[-.]?` separators to `[-.\s]?`. The lookbehind fix alone wasn't
enough: the original separator also never allowed for the space after
a closing paren (`(555) 123-4567`), so `(555) 123-4567` still didn't
match even once the `\b` boundary issue was fixed. Verified against
all formats in the test file plus a few extra ones by hand
(`(555)123-4567`, `555 123 4567`, `Phone:(555) 123-4567`) and
confirmed `phone_intl` still claims `+44 20 7946 0958` untouched by
`phone_us`.

**Tests:** All four originally-failing tests
(`test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, `test_phone_at_start_of_text`) now pass.

**Pre-existing failures observed (not introduced by this change):**
- `tests/unit/test_pii_scrubber.py::test_mixed_pii_and_text` fails on
  `main` before this fix too: the unrelated `street_address` pattern
  has no trailing `\b`/anchor, so its `[A-Za-z\s]+` capture backtracks
  onto the literal substring `"pl"` inside "applications" and
  over-redacts. Confirmed via `git stash` that this test already fails
  on the pre-fix tree.
- `make test-unit` has 53 pre-existing failures across the suite on
  `main` (49 after this fix, since it resolves 4 of them). Confirmed
  via `git stash` diff of failure counts before/after.
- `make check` (ruff, black, mypy) has pre-existing findings
  throughout the repo unrelated to this issue — e.g. `black` was not
  clean on `safety/pii_scrubber.py` before this change, and the repo's
  test files broadly lack type annotations that `mypy`'s
  `disallow_untyped_defs` config would otherwise require. This PR
  fixed the specific ruff findings (`E501`, `B007`) already present in
  `safety/pii_scrubber.py` (the file I was editing) so the pre-commit
  hooks could run, but did not attempt to annotate or reformat
  unrelated files/tests — that's out of scope for a phone-regex fix.
