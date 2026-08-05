## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber module in `safety/pii_scrubber.py` uses a regex pattern that
correctly matches dashed US phone formats like `555-123-4567`, but fails to
match the equally common parenthesized format `(555) 123-4567`. As a result,
`scrub()` leaves these numbers unredacted in text output, and `detect()`
incorrectly reports no PII present when a parenthesized number is the only
match. This is a gap in the safety layer meant to prevent sensitive personal
data from leaking through review output. A successful fix extends the phone
regex to cover the parenthesized format without breaking existing dashed-format
matching, and passes the four related unit tests already written for this bug.

**Scope reasoning ("Is this right for me?" checklist):**

*Part 1 — Understanding the issue*
The bug is in `safety/pii_scrubber.py`: the phone-number regex matches dashed
formats like `555-123-4567` but not parenthesized formats like `(555) 123-4567`,
so `scrub()` leaves those numbers unredacted and `detect()` reports no PII found.
Done looks like: both formats get redacted by `scrub()`, `detect()` correctly
flags parenthesized numbers as PII, and the four related tests in
`tests/unit/test_pii_scrubber.py` pass.

*Part 2 — Tier fit*
Labeled tier-1 and good-first-issue. This is my first contribution to a large
codebase, so a Tier 1 fix is the right starting point — it's a single-file
regex/logic change, not a cross-module feature.

*Part 3 — Codebase readiness*
[x] Confirm after opening the file: I've located `pii_scrubber.py` and read the
current phone-matching regex and the `scrub()`/`detect()` functions closely
enough to sketch a fix.
[x] Confirm after opening the file: I've read `tests/unit/test_pii_scrubber.py`,
specifically `test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, and `test_phone_at_start_of_text`, to understand the
expected input/output shape.

*Part 4 — Scope and time*
No blockers or dependencies mentioned in the issue. PR #162 is linked but
claims are non-exclusive per the course guidelines, so I checked the comments/
ledger claims count and am comfortable proceeding. This is a small, well-scoped
regex fix — I estimate 3-4 hours, well within the Tier 1 range and the Week 8-9
window.

**Branch name:** fix/146-pii-phone-regex

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
https://github.com/deathtaco1408/pathreview/commit/9a10094

**Reproduction summary:**
Ran `PIIScrubber().scrub()` and `.detect()` against `(555) 123-4567` and
confirmed the parenthesized format passed through unredacted and undetected,
while the dashed format redacted correctly — confirming the bug was in the
regex's boundary handling, not the surrounding scrub/detect logic.

**PLAN.md link:**
https://github.com/deathtaco1408/pathreview/commit/07ddb06

**Walkthrough video (recommended):** 

**Blockers or open questions:**
None currently — the `street_address` false-positive bug found during
testing is unrelated to this issue and out of scope; may raise it as a
separate issue.

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full fix from PLAN.md — updated the `phone_us` regex to
move the word-boundary check after the optional opening parenthesis and
widened digit-group separators to accept whitespace. All sub-tasks from
PLAN.md are complete: the four named tests pass, the full
`test_pii_scrubber.py` suite passes except the pre-existing unrelated
`street_address` bug, and the file is clean under ruff/black/mypy.

**Next steps:**
Run `make check` and `make test-unit` at the full-project level to confirm
no pre-existing failures elsewhere are affected, open a draft PR, and get
peer/mentor feedback in Slack before marking it ready for review.

**Blockers:**
None currently.

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/822)

**Branch:** fix/146-pii-phone-regex

**What you built:**
Fixed the PII scrubber's phone-number regex so it correctly redacts and
detects parenthesized and whitespace-separated US phone formats, which
previously passed through unredacted.

**Tests added or updated:**
No new test file changes — the existing tests in
`tests/unit/test_pii_scrubber.py` (`test_us_phone_number_redaction`,
`test_us_phone_formats`, `test_detect_phone_pii`,
`test_phone_at_start_of_text`) already covered the expected behavior and
now pass against the fixed regex.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [fill in after Slack review]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer/maintainer feedback has come in on the PR as of this writing.
(Note: per the Su26 course note, reviewer feedback isn't an active feature
this term.) I did receive feedback from an outside reviewer, but on
unrelated files (`review_service.py`, `error_handling.py`) that I never
touched in this PR — I followed up to clarify whether it was meant for a
different submission before acting on it, rather than making unrequested
changes to files outside my PR's scope.

**How you responded:**
Asked for clarification on the scope mismatch rather than assuming the
feedback applied to my change. No code changes made yet, pending that
clarification.

---

### Reflection

**What was harder than you expected?**
Getting the local environment running took longer than I expected — I hit
a missing `docker compose up -d` step, then Docker itself wasn't installed,
then a bcrypt/passlib version warning during seeding. None of these were
hard individually, but they added up before I'd even looked at the actual
bug. The regex fix itself was conceptually simple once I found the root
cause (the `\b` boundary sitting before the optional parenthesis instead of
after it), but pre-commit hooks (ruff catching a pre-existing long line and
an unused loop variable, then black reformatting on top of that) meant I
had to go through several failed-commit cycles before anything actually
landed. I didn't expect "the fix works" and "the commit succeeds" to be two
separate hurdles.

**What did you learn about working in a large codebase?**
The biggest lesson was scope discipline. Running the full test suite
surfaced 49 failing tests and 178 lint errors across the codebase that had
nothing to do with my issue. In my own projects I'd be tempted to fix
everything I see broken; here, the right move was to isolate what was
pre-existing (verified with `git stash` against `main`) versus what my
change actually affected, and explicitly document that boundary in the PR
description instead of quietly expanding scope. I also learned to be
careful about what actually belongs in a PR — I'd accidentally picked up an
unrelated root-level `package.json`/`package-lock.json` from a stray `npm
install docker` and some lockfile drift in `frontend/package-lock.json`,
and had to consciously strip those out to keep the diff to exactly the
three files it needed to touch.

**How did AI tools help — and where did they fall short?**
AI was most useful for the regex root-cause analysis — walking through
exactly why `\b(?:\+?1[-.]?)?\(?...` failed on `(555) 123-4567` character
by character was faster with a second set of "eyes" than staring at the
pattern myself. It was also useful for catching a subtle git-hash typo
before I put a broken link in JOURNAL.md, and for helping me structure the
PLAN.md and PR description consistently against the assignment's rubric.
Where it fell short: it couldn't run my actual environment, so I still had
to be the one pasting in real terminal output, catching that a file lived
in `docs/JOURNAL.md` instead of the repo root, and independently verifying
that the extra `package.json` diff wasn't something to keep. AI is good at
reasoning about code I show it, but it can't replace actually running
`make test-unit` myself and reading the output critically.

**What would you do differently if you started over?**
I'd claim the issue by directly checking the linked PR #162 status before
starting, instead of assuming it was safe — the checklist clarified claims
are non-exclusive, but I'd still want that context up front rather than
mid-stream. I'd also run `make check` and `make test-unit` once, cold, on
`main` before touching any code, so I had a clean baseline of pre-existing
failures documented from minute one instead of reconstructing it via
`git stash` after the fact.

**What are you most proud of from this module?**
Recognizing the `street_address` regex bug in `test_mixed_pii_and_text` and
deliberately choosing *not* to fix it, even though I could see exactly what
was wrong and how to fix it. Staying inside the Tier-1 scope, documenting
the out-of-scope bug clearly instead of just patching it, was a harder call
than the actual code fix.