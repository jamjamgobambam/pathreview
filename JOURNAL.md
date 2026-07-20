# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `PIIScrubber` class in `safety/pii_scrubber.py` uses a regex to detect and redact
US phone numbers, but the pattern only reliably matches formats where digits follow
directly after a closing parenthesis (e.g. `(555)123-4567`). Common parenthesized
phone formats that include a space after the area code, like `(555) 123-4567`, slip
through both `scrub()` (so the number isn't redacted) and `detect()` (so it isn't
reported as PII at all). I confirmed this locally by running the regex against
`"Call me at (555) 123-4567 or 555-123-4567"` — only the dashed number gets redacted.
A successful fix updates the `phone_us` pattern to also match the space-separated
parenthesized format, and gets the four related tests in
`tests/unit/test_pii_scrubber.py` passing (`test_us_phone_number_redaction`,
`test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`).

**Branch name:** fix/146-pii-scrubber-parenthesized-phone

**Setup confirmation:** [ ] App runs locally at localhost:5173
(Docker Desktop is not yet installed on this machine — the `brew install --cask docker`
step needs an interactive sudo password prompt that couldn't be completed non-interactively.
I set up a Python venv and installed the backend dev dependencies directly, and confirmed the
fix by running `pytest tests/unit/test_pii_scrubber.py` — all four target tests
(`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`,
`test_phone_at_start_of_text`) now pass. Full `make setup` / `make run` against
Postgres + Redis still needs Docker Desktop installed and running.)

**Cohort ledger:** [ ] Issue added to cohort ledger
(To be completed manually — I don't have access to the shared cohort spreadsheet/ledger link.)

**Scope check ("Is this right for me?"):**
- I chose Tier 1 deliberately: this is my first time working in `pathreview`'s
  codebase, and I don't yet have a mental map of how `safety/`, `api/`, and the
  rest of the modules connect, so I wanted an issue contained to one file rather
  than one that would force me to trace behavior across the app while I'm still
  orienting myself.
- Single file, single regex change — no cross-module ripple.
- Labeled `good first issue`, Tier 1, with a clear repro script in the issue body.
- Four existing named unit tests already define "done" — no ambiguity about scope.
- No new dependencies or schema/API changes required.
