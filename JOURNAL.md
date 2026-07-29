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
