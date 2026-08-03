# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber (`safety/pii_scrubber.py`) is supposed to catch phone numbers
before any generated feedback reaches a user, but the `phone_us` regex only
reliably matches dashed formats like `555-123-4567`. The pattern opens with a
`\b` word boundary, and `\b` only matches between a word character and a
non-word character — when a number starts with `(` (as in `(555) 123-4567`),
the character before it is usually a space, so both sides of that gap are
non-word characters and the boundary never fires, letting the whole number
through unredacted. I reproduced this locally by importing `PIIScrubber` and
running the exact steps from the issue: in the same string, the dashed number
got replaced with `[REDACTED]` but the parenthesized one right next to it
didn't, and `detect()` returned an empty list for text that was nothing but a
parenthesized phone number. Since parenthesized format is one of the most
common ways people write a US phone number on a resume, this isn't an edge
case — it's a real hole in the safety layer. A correct fix adjusts the
`phone_us` pattern so the leading boundary check tolerates a `(` immediately
after it, which should get all four related tests in
`tests/unit/test_pii_scrubber.py` passing.

**Selection notes (scope check):**
Went through the "is this right for me" checklist before claiming this one.
Scope-wise it's contained to a single file (`safety/pii_scrubber.py`, ~60
lines total) with no other modules importing the specific pattern I need to
touch, so a fix shouldn't ripple into other subsystems. It already has
failing tests that describe the expected behavior (`test_us_phone_number_redaction`,
`test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`),
so I have a concrete definition of "done" instead of having to invent test
cases from scratch. It's regex-only, no new dependencies, no schema/API
changes, no frontend involvement, which keeps the surface area small for a
first PR. The main risk I can see is a bad regex fix breaking one of the
other PII patterns (ssn, email, address) that share the same `scrub()` loop,
so whatever I write needs to run the full `test_pii_scrubber.py` file, not
just the four listed tests, before I call it done. Effort-wise this feels
closer to the 1-3 hour end than something that'll eat a whole week, so if it
goes faster than expected I may pick up a Tier 2 issue afterward per the
"second issue" note in the assignment.

**Branch name:** fix/146-pii-scrubber-phone-numbers

**Setup confirmation:** [ ] App runs locally at localhost:5173
(Docker and Python 3.11 aren't installed on this machine yet — need to get
those set up before Week 8 so I can actually run the test suite and verify
a fix.)

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/welzo/pathreview/commit/c1898510b13d9d067b157eac9946f8090a174f58

**Reproduction summary:**
Docker still isn't set up on this machine, but `pii_scrubber.py` has no
DB/API dependency, so I installed Python 3.11 via Homebrew, made a throwaway
venv with just `pytest` + `structlog`, and ran the actual
`tests/unit/test_pii_scrubber.py` against the real `PIIScrubber` class — 5 of
25 tests failed (the 4 named in the issue, plus one unrelated one I traced
down separately), confirming parenthesized phone numbers pass through both
`scrub()` and `detect()` untouched while dashed ones are correctly redacted.
Full steps and output are in `docs/repro-146-pii-phone-numbers.md`.

**PLAN.md link:** https://github.com/welzo/pathreview/blob/fix/146-pii-scrubber-phone-numbers/PLAN.md

**Walkthrough video (recommended):** Not recorded this week — it's optional
and not graded, skipping for now given time constraints. May record one
before Week 9 if I have time, to get early feedback in office hours.

**Blockers or open questions:**
- Docker Desktop install failed partway through (needed a `sudo` password
  prompt in an interactive terminal). Still need to get `make setup`/`make run`
  working before Week 9 so I can validate the fix through the real API path,
  not just in an isolated venv.
- While reproducing, I found `test_mixed_pii_and_text` also fails, for a
  reason unrelated to phone numbers — the `street_address` pattern is
  over-matching into unrelated words (traced in the repro doc). It's not in
  the issue's scope and I'm not planning to fix it as part of #146, but I
  want to ask in Slack/office hours whether that's the right call or whether
  it should get filed as its own issue.
