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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
A classmate (ayc325) left two comments on [PR #1](https://github.com/kneha07/pathreview/pull/1) on 2026-08-04:
1. The PR is opened against my own fork's `main` branch, not the upstream `ascherj/pathreview:main` — so it never actually reached the project maintainers as a real contribution.
2. They would have liked to see more, smaller commits mapping to each subtask in PLAN.md, instead of the work landing in a few larger commits.

**How you responded:**
In standup I walked through the issue and fix, then acknowledged both points directly: the wrong-base-repo mistake is a real process error I need to fix by opening a new PR against `ascherj/pathreview:main`, and the commit-granularity feedback is fair — future work should commit at each PLAN.md subtask boundary rather than batching. I'm tracking the corrected upstream PR as a follow-up action for this module.

---

### Reflection

**What was harder than you expected?**
The fix itself — extending one character class in the `phone_us` regex — took maybe twenty minutes. What took the rest of the time was everything around it: setting up a working local environment without Docker for the first two weeks, figuring out which of the 49 failing unit tests were pre-existing versus caused by my change, and writing a PR description precise enough that a reviewer wouldn't have to re-derive that distinction themselves. I underestimated how much of "fixing a one-line bug" is actually verification and communication overhead, not code. I also didn't expect a process mistake — opening the PR against my own fork instead of upstream — to be the thing a reviewer flagged first, ahead of anything about the code itself.

**What did you learn about working in a large codebase?**
The biggest shift was learning to draw a hard boundary around scope. I found a second, unrelated bug (`street_address` matching case-insensitively inside words like "applications") while running the regression suite, and the instinct in a personal project would've been to just fix it too since I was already in the file. Here, touching it would have inflated the diff, mixed two unrelated concerns into one review, and made the PR harder to reason about. Documenting it in PLAN.md's Risks section and moving on was the harder but more professional choice. I also learned to distrust a clean test run — 49 pre-existing failures meant "tests pass" wasn't a meaningful signal on its own; I had to diff behavior against the pre-fix regex specifically to prove causation.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical, low-risk parts: drafting the regex alternatives to consider, writing the reproduction script structure, and sanity-checking the PR description for clarity. It fell short on judgment calls that needed project-specific context: whether the `street_address` bug was in-scope (it wasn't — I had to actually read the issue and Tier 1 guidance to decide), and whether my test failures were pre-existing (only running the suite against the actual pre-fix commit settled that, not reasoning from general regex knowledge). AI is good at generating candidate explanations; confirming which one is *true* still required running real commands against the real repo.

**What would you do differently if you started over?**
I'd try to get Docker Desktop installed and `make run` verified in Week 7 instead of letting it slide for two weeks, even though the fix itself never touched Postgres/Redis — it left me without full end-to-end confidence going into the PR, only unit-test confidence. I'd also start the "which failures are pre-existing" regression check earlier rather than in Week 9, since it's the kind of task that reveals scope questions (like the `street_address` bug) that are better to know about while still planning than while trying to finish. And I'd double-check the PR's base repo before opening it, and commit at each PLAN.md subtask boundary instead of batching — both were avoidable and both were the actual feedback I received.

**What are you most proud of from this module?**
Catching and correctly triaging the `street_address` false-positive bug without letting it derail the actual issue. It would have been easy to either ignore it (and ship a PR that looks incomplete next to a suite with unexplained failures) or scope-creep into fixing it (and turn a one-line fix into a multi-file PR). Documenting it clearly instead, with evidence that it predates my change, felt like the most "professional open-source contributor" moment of the whole module, more so than the regex fix itself.
