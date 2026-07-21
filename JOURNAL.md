# Module 3 Journal — Abhilash Gorle

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's safety module is supposed to strip personal information out of
user-submitted text before it goes anywhere else, but the phone-number regex
in `safety/pii_scrubber.py` only matches dashed numbers like `555-123-4567`.
The parenthesized format `(555) 123-4567` — one of the most common ways US
numbers are written on resumes — passes through `scrub()` unredacted, and
`detect()` doesn't flag it as PII at all. I reproduced this locally in two
lines of Python. A successful fix widens the pattern to cover parenthesized
(and ideally other common) formats so that the four currently-failing tests
in `tests/unit/test_pii_scrubber.py` pass without breaking the rest of the
suite.

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
