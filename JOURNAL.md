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

**Cohort ledger:** [ ] Issue added to cohort ledger
