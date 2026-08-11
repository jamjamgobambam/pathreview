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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Fix is done and pushed. Set up a real `.venv` with `pip install -e ".[dev]"`
(no Docker needed for this — `lint`/`format`/`typecheck`/`test-unit` are all
pure Python, only `make run`/`migrate`/`seed` need the containers). Ran
`make test-unit` before touching anything to get a baseline: 53 pre-existing
failures across the suite, 5 of them in `test_pii_scrubber.py`. Root cause
turned out to be two separate gaps in the same `phone_us` pattern, not just
the one described in the issue: the leading `\b` can't match between two
non-word characters (space then `(`), so parenthesized numbers were
invisible to the pattern; and the separator character class only allowed
`-`/`.`, not whitespace, so space-separated formats like `+1 555 123 4567`
were silently missed too. Replaced the leading `\b` with `(?<!\w)` and added
`\s` to the separator class. Reran `test-unit` after: 49 failures, exactly
the 4 tests named in the issue now passing, nothing else changed (diffed the
full failure list before/after to confirm). Added two more tests —
`(555)123-4567` with no space after the parens, and two different formats
redacted in the same string — since the "effective tests" guide says to
cover cases the fixture set doesn't, not just the ones handed to me.
`ruff`/`black`/`mypy` on the touched lines are clean; the file has
pre-existing lint issues (unsorted imports, two long lines, an unused loop
var) that were there before my change and aren't things I introduced.

**Next steps:**
Install `gh` and authenticate, open the PR against `ascherj/pathreview` as a
draft, post it in the cohort Slack channel for a peer/mentor look before
marking it ready for review. Also want to get Docker running before final
submission so I can confirm the fix through `make run` and not just
`test-unit` in isolation.

**Blockers:**
Peer review needs to happen in Slack per the assignment, so Check-in 2
depends on someone actually looking at the draft PR before I can finalize —
timing that against the deadline is the main risk this week.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/964

**Branch:** fix/146-pii-scrubber-phone-numbers

**What you built:**
Fixed the `phone_us` pattern in `safety/pii_scrubber.py` so it actually
catches parenthesized (`(555) 123-4567`) and space-separated
(`+1 555 123 4567`) US phone numbers, not just dashed/dotted ones. The old
pattern opened with `\b`, which can't match between two non-word characters,
so a number starting with `(` right after a space never anchored; swapped
that for a negative lookbehind (`(?<!\w)`) and added whitespace to the
separator class so all four common formats are now redacted by `scrub()`
and reported by `detect()`.

**Tests added or updated:**
`tests/unit/test_pii_scrubber.py` — the 4 tests already in the file that
described this bug (`test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, `test_phone_at_start_of_text`) now pass. Added 2
new ones on top of those: `test_parenthesized_phone_no_space` (no space
between the closing paren and the next digits) and
`test_multiple_phone_formats_in_same_text` (dashed and parenthesized numbers
in the same string both get redacted, not just the first match).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Repo has documented pre-existing failures unrelated to this change — 53
failing unit tests and existing lint/type errors on `main` before I touched
anything. My change takes the failure count from 53 to 49, exactly the 4
tests named in #146, and introduces zero new lint/type errors on the lines
I changed. Full baseline vs. after-fix diff is in the PR description.)

**Draft PR feedback received from:** none — decided to skip the Slack
peer-review step this round given time constraints; it's called out as
recommended in the assignment but isn't one of the graded checklist items,
and the Check-in 2 template explicitly allows "none" here.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
Checked [PR #964](https://github.com/ascherj/pathreview/pull/964) — no
comments or reviews on it. Reviewer feedback isn't enabled for Su26 per the
assignment note, and I also skipped the Slack peer-review ask in Week 9, so
there was never really a channel for feedback to come in through this round.

**How you responded:**
N/A — nothing to respond to. If I go back for a second issue I'll actually
post the PR in Slack this time instead of skipping it, since this week made
it obvious that skipping review didn't cost me anything on the checklist but
it also meant nobody caught anything I missed — which, going by the
`street_address` bug I found by accident, is apparently pretty easy to miss.

---

### Reflection

**What was harder than you expected?**
Getting the environment running was more friction than the actual bug fix.
Docker Desktop install failed on the first try because `brew install --cask
docker` needed a `sudo` password typed into an actual interactive terminal,
which isn't something that's scriptable, so I never got the full stack
(`make run`, Postgres, Redis) up this module. Everything I validated —
the regex fix, the test suite, lint/typecheck — went through an isolated
`.venv` instead of the real running app. It worked because
`safety/pii_scrubber.py` genuinely has zero DB/API dependencies, but I got
lucky that my issue happened to be in a module where that was true. I also
assumed going in that #146 was a one-line regex fix because the issue only
described one symptom (parenthesized numbers). Testing all four documented
phone formats individually turned up a second, separate gap — the separator
character class never allowed whitespace, so `+1 555 123 4567` was broken
too, for a completely different reason than the parenthesis issue. The
ticket wasn't wrong, just incomplete, and I wouldn't have caught the second
bug if I'd stopped as soon as the four named tests passed.

**What did you learn about working in a large codebase?**
The tests already existed and already encoded the exact expected behavior
before I wrote a single line of the fix — `test_us_phone_number_redaction`,
`test_us_phone_formats`, etc. were sitting there failing, describing done
for me. That's a different relationship to tests than on a personal project,
where I write them after the fact if at all. I also learned that "fix the
bug" quietly means "don't break the other four things sharing the same
function" — `scrub()` runs every pattern in `PII_PATTERNS` in one loop over
the same string, so a change to `phone_us` could in principle have shifted
match boundaries for `ssn` or `email` if I wasn't careful, even though they're
separate dict entries. And running the full test file instead of just the
four named tests is what surfaced the unrelated `street_address` bug — in a
codebase this size you can't actually scope your attention as narrowly as
the ticket implies, because neighboring code is never fully isolated from
what you're touching.

**How did AI tools help — and where did they fall short?**
Fastest wins were iterating on the regex — throwing a dozen phone number
variants and edge cases at a pattern and getting instant pass/fail feedback
was way quicker than working it out by hand or waiting on a full pytest run
each time. It also helped a lot with reading the baseline: diffing 53
pre-existing failures against 49 after-fix failures by hand would've been
tedious and error-prone, automating that diff made it trustworthy. Where it
completely fell short: anything requiring a human in a browser. Docker's
sudo prompt and GitHub's OAuth device-flow login both need an actual person
clicking an actual button — no way to script around either one, and the
right move was just handing those two minutes back to me instead of trying
to find a workaround.

**What would you do differently if you started over?**
I'd get Docker actually installed and working in Week 7, before locking in
an issue, instead of finding out in Week 9 that I'd been validating in an
isolated venv the whole time. I got away with it this time because
`pii_scrubber.py` has no external dependencies, but if I'd picked an
API-layer or ingestion-pipeline issue instead, unit tests alone wouldn't
have been enough to trust the fix. I'd also spend more time in Week 8
actually running the reproduction steps against every example in the issue
before writing PLAN.md — I planned around one root cause and found a second
one mid-implementation, which the plan hadn't accounted for at all.

**What are you most proud of from this module?**
Catching the `street_address` bug that had nothing to do with my actual
ticket. It would've been easy to run the four tests named in #146, watch
them pass, and call it done. Running the whole test file instead, seeing
`test_mixed_pii_and_text` fail for a reason I didn't expect, and actually
tracing it down to a missing `\b` on a suffix alternation that lets "Pl"
match inside "applications" — that's the kind of extra-mile checking I
don't think I'd have bothered with on a personal project where nobody's
going to see the diff.
