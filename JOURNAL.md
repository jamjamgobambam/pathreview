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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [scripts/repro_146.py](https://github.com/ascherj/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/scripts/repro_146.py) (see commit "test: add reproduction script for issue #146")

**Reproduction summary:**
I wrote `scripts/repro_146.py`, which runs the *old* pre-fix `phone_us` regex (copied
inline from before commit `06230ad`) against sample text like
`"Call me at (555) 123-4567 or 555-123-4567"` and confirms it redacts only the dashed
number, leaving `(555) 123-4567` and `+1 555 123 4567` untouched. Running the same
samples through the current pattern in `safety/pii_scrubber.py` confirms all formats are
now redacted.

**PLAN.md link:** [PLAN.md](https://github.com/ascherj/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md)

**Walkthrough video (recommended):** No screen-recorded video this week (screen-recording
permission wasn't available in my environment). Instead, here's an animated GIF walking
through the reproduction script's output, showing the old pattern failing on
`(555) 123-4567` and the current pattern redacting it:
[docs/repro_146_demo.gif](https://github.com/ascherj/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/docs/repro_146_demo.gif)

**Blockers or open questions:**
While running the full `tests/unit/` suite as a regression check (Plan step 5), I found
`test_mixed_pii_and_text` fails independently of this fix — the `street_address` pattern's
`Pl` alternative matches case-insensitively inside unrelated words like "applications". This
is unrelated to #146 (it's the `street_address` pattern, not `phone_us`) and out of scope
for this issue, but I've noted it in PLAN.md's Risks section in case it comes up in review.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix itself (Plan steps 1–4: reproduce, extend the `phone_us` separator class to accept
whitespace, replace the leading `\b` with `(?<!\d)`) was already implemented and committed
in `06230ad` during Week 8's reproduction work, since the change is a single regex line and
was small enough to verify alongside reproduction. All four target tests
(`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`,
`test_phone_at_start_of_text`) pass.

**Next steps:**
Run the full `make check` / `make test-unit` regression pass (Plan step 5), document any
pre-existing failures separately from this change, write the PR description, and open the
PR.

**Blockers:**
Docker Desktop wasn't available in Week 7–8; it's now running, but full `make setup`/`make run`
against Postgres + Redis still hasn't been exercised for this issue since the fix and its
tests are pure-Python and don't touch the database.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/kneha07/pathreview/pull/1

**Branch:** `fix/146-pii-scrubber-parenthesized-phone`

**What you built:**
Fixed the `phone_us` regex in `safety/pii_scrubber.py` so `PIIScrubber.scrub()` and
`.detect()` correctly match space-separated parenthesized US phone numbers (e.g.
`(555) 123-4567`) and `+1 555 123 4567`, which previously slipped through both methods
untouched.

**Tests added or updated:**
No new tests were added — the fix makes four existing tests in
`tests/unit/test_pii_scrubber.py` pass that were previously failing:
`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`,
`test_phone_at_start_of_text`. I also added `scripts/repro_146.py`, a standalone
reproduction script (not a test) comparing the old and new patterns.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass with no *new* failures introduced by this change. `make check` has ~182
pre-existing lint errors across the codebase — 5 of them in files this PR touches
(`safety/pii_scrubber.py`, `tests/unit/test_pii_scrubber.py`), all present before this
branch's commit. `make test-unit` has 49 pre-existing failures, including
`test_mixed_pii_and_text` in the same file as this fix — I confirmed it fails identically
on the pre-fix version of `safety/pii_scrubber.py`, so it's caused by an unrelated bug in
the `street_address` pattern, not this change. Details in the PR's "Notes for Reviewers.")

**Draft PR feedback received from:** none yet — opened ready for review; will request
feedback in the cohort Slack channel per instructor guidance.
