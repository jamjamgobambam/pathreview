# Module 3 Journal — Abhilash Gorle

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview runs every piece of user-submitted text through a PII scrubber in
the `safety/` module before storing or processing it, so personal details
like phone numbers are supposed to get replaced with `[REDACTED]`. The bug is
that the regex in `safety/pii_scrubber.py` only recognizes dashed phone
numbers like `555-123-4567` — if the same number is written as
`(555) 123-4567`, which is probably the most common way people format numbers
on resumes, both `scrub()` and `detect()` miss it completely. I confirmed
this on my machine with the two-line snippet from the issue: the
parenthesized number came back untouched and `detect()` returned an empty
list. A successful fix means widening the pattern to handle parenthesized
(and other common US) formats, verified by the four tests in
`tests/unit/test_pii_scrubber.py` that currently fail going green, with no
other tests breaking.

**"Is this right for me?" notes:**
- Reproducible in under a minute: two-line Python snippet from the issue
  confirms the bug on my machine.
- Objectively verifiable: the issue names four failing unit tests that
  define "done" (`test_us_phone_number_redaction`, `test_us_phone_formats`,
  `test_detect_phone_pii`, `test_phone_at_start_of_text`).
- Self-contained scope: one regex in one file in the `safety/` module — no
  dependency on the RAG pipeline, agent, or vector DB.
- Not trivial: phone-format regexes have real edge cases (spacing variants,
  country codes), so there is genuine design thinking to document.

**Branch name:** fix/146-pii-scrubber-parenthesized-phones

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/GORLEABHILASH/pathreview/commit/c9bfaf19e139d727fe7aeafb1c46351583902d4a

**Reproduction summary:**
Ran `.venv/bin/python -m pytest tests/unit/test_pii_scrubber.py -v` on this
branch: the four tests named in issue #146 all fail because `scrub()` returns
`(555) 123-4567` untouched and `detect()` finds no phone match — the
`phone_us` regex's separator class `[-.]?` has no way to match the space after
the closing paren. I also observed an unexpected fifth failure
(`test_mixed_pii_and_text`), caused by a pre-existing `street_address`
false positive unrelated to phones — documented in PLAN.md.

```
5 failed, 20 passed in 1.13s
FAILED test_us_phone_number_redaction
FAILED test_us_phone_formats
FAILED test_detect_phone_pii
FAILED test_phone_at_start_of_text
FAILED test_mixed_pii_and_text  (pre-existing street_address bug, see PLAN.md)
```

**PLAN.md link:** https://github.com/GORLEABHILASH/pathreview/blob/fix/146-pii-scrubber-parenthesized-phones/PLAN.md

**Walkthrough video (recommended):** _Not recorded yet (optional)._

**Blockers or open questions:**
- Is the `test_mixed_pii_and_text` failure (the `street_address` pattern's
  `Pl` abbreviation redacting part of "applications") in scope for #146, or
  should it be filed separately? Planning to ask maintainers before the PR.
- If `phone_us` learns to match `+1 555 123 4567`, `detect()` may report the
  same number under both `phone_us` and `phone_intl` — need to pin expected
  behavior with a test.

## Week 9 — Implementation & PR

### Check-in 1 (mid-week)

**Current progress:**
Steps 1–3 of PLAN.md are done. I wrote down the target format list first
(the four formats from `test_us_phone_formats`, plus `+1 (555) 123-4567`
and the must-not-match strings — version numbers and SSNs), then widened
the `phone_us` separator class from `[-.]?` to `[-.\s]?` in
`safety/pii_scrubber.py`. That alone wasn't enough: the pattern's leading
`\b` can never sit between a space and an opening paren, so matches
started *after* the paren and `scrub()` produced `([REDACTED]`. Replacing
`\b` with a `(?<!\w)` lookbehind fixed it. All four tests named in issue
#146 now pass.

**Next steps:**
- Run the full unit suite and diff failures against a clean checkout to
  confirm zero regressions (PLAN.md step 4).
- Resolve the `test_mixed_pii_and_text` / `street_address` scope question
  (PLAN.md step 5).
- Add tests for the `+1 (555) 123-4567` combined format and full-paren
  redaction, then open the PR.

**Blockers:**
Whether the pre-existing `street_address` false positive (the `Pl`
abbreviation matching inside "applications") is in scope for #146 — it
blocks a green run of the test module either way.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/920

**Branch:** fix/146-pii-scrubber-parenthesized-phones

**What was built:**
Fixed the `phone_us` regex in `safety/pii_scrubber.py` so parenthesized
and space-separated US phone numbers — `(555) 123-4567`,
`+1 555 123 4567` — are redacted by `scrub()` and reported by `detect()`.
Also anchored the `street_address` pattern with a trailing `\b` to fix a
pre-existing false positive that was the real cause of the fifth failing
test in the module (called out for reviewers as a scope question in the
PR).

**Tests:**
Modified `tests/unit/test_pii_scrubber.py`: added a case for the
`+1 (555) 123-4567` combined format, an assertion that the opening paren
is included in the redaction (no leftover `([REDACTED]`), and a
regression test that words containing street-type abbreviations (e.g.
"applications") are not partially redacted by the `street_address`
pattern. All 28 tests in the module pass, including the 4 named in issue
#146.

**Self-review:**
- [x] `make check` passes — clean on both touched files
  (`safety/pii_scrubber.py`, `tests/unit/test_pii_scrubber.py`),
  including the stricter pre-commit mypy hook; repo-wide lint errors in
  unrelated files pre-date this branch and are untouched.
- [x] `make test-unit` passes — all 28 tests in the touched module pass;
  the repo-wide failures in unrelated files (review service, skill
  extractor, etc.) exist identically before and after this change,
  verified by diffing the failure lists with the change stashed vs.
  applied.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer comments have come in on PR #920 as of the end of Week 10
(reviewer feedback is not provided in the Summer 2026 cohort). The PR
remains open with the scope question about the `street_address` fix
flagged in the "Notes for Reviewers" section so a maintainer can ask for
it to be split out if they prefer.

**How you responded:**
N/A — no feedback received.

---

### Reflection

**What was harder than you expected?**
Debugging a one-line regex took far longer than writing it. I went in
expecting to "add parentheses support," but PLAN.md's root-cause step
showed the parens were already allowed — the real bug was the separator
class `[-.]?` having no way to match the space after the closing paren.
Then the fix surfaced a second subtlety: the pattern's leading `\b` can
never match between a space and `(` (both non-word characters), so the
paren was silently excluded and `scrub()` emitted `([REDACTED]`. Getting
from "tests fail" to *why* a word boundary fails next to punctuation was
the hardest hour of the module.

**What did you learn about working in a large codebase?**
The verification burden is completely different from my own projects. The
repo's unit suite had ~48 pre-existing failures in unrelated files, so
"run the tests and see green" was not an available signal — I had to
establish a baseline first, then diff the failure lists with my change
stashed vs. applied to prove I introduced zero regressions. I also
learned to verify blast radius instead of assuming it: a grep showed
`PIIScrubber` had no runtime call sites outside the unit tests, which is
what made a regex change to a safety module safe to ship confidently.

**How did AI tools help — and where did they fall short?**
AI was most useful at enumerating edge cases I would not have listed
myself — the SSN pattern owning `123-45-6789`, version strings like
`1.2.3`, scrub idempotency, and the `phone_us`/`phone_intl` double-report
risk all went into PLAN.md before I touched the regex. It fell short in
two places: regex explanations sound confident whether or not they are
right, so every claim (like the `\b`-next-to-paren behavior) had to be
verified empirically in a REPL before I trusted it; and it could not make
the scope call on the `street_address` fix — that took reading
CONTRIBUTING.md's requirement that the touched module's suite pass and
making a judgment I then had to defend in the PR description.

**What would you do differently if you started over?**
Run the full test suite on day one, before committing to the issue. The
fifth failing test (`test_mixed_pii_and_text`) and the repo-wide
pre-existing failures were both mid-module surprises that reshaped my
plan; a baseline run in Week 7 would have surfaced them when they were
free to absorb. I would also ask the maintainers the scope question in
the issue thread early in Week 8 instead of deciding unilaterally at PR
time and offering to split it after the fact.

**What are you most proud of from this module?**
The verification story in the PR, more than the fix itself. The diff is
about two characters of regex, but the PR proves it is safe: before/after
failure-list diffs showing zero regressions, an explicit check that
`+1`-prefixed numbers are not double-reported by both phone patterns, and
a regression test pinning the false-positive fix. A reviewer who has
never seen the code can verify every claim in it — that is the standard I
want my future PRs held to.
