# Module 3 Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88
**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, the codebase lacks a unit test to verify how the `POST /reviews` endpoint behaves when a user profile attempts to generate a review but has zero ingested documents. This gap in test coverage means potential edge-case failures or unhandled exceptions under empty document states might go unnoticed. A successful fix will involve writing mock test cases in the backend test suite to ensure the system gracefully handles empty-document profiles, returning the correct error code or empty response payload. This directly affects the backend routing and review service modules.

**Branch name:** test/88-review-endpoint-missing-documents
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/lakshita1212/pathreview/commit/323b79b5b283bbd6a8e8dbdf5c7bab89c4da7532

**Reproduction summary:**
Ran `process_review` against a mocked profile with zero ingested documents (no GitHub, portfolio, or resume). Ingestion correctly returned 0 sources, yet the review was still marked `complete` with 3 fabricated sections and `overall_score=0.81` — because the agent/RAG steps return hard-coded placeholder output regardless of input. Captured this in [tests/unit/test_review_routes.py](tests/unit/test_review_routes.py) as a passing root-cause test plus a strict `xfail` test pinning the desired behavior.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** _not recorded_

**Blockers or open questions:**
Which terminal state is the intended contract for an empty-document review — `failed`, a new `empty` status, or `complete` with empty sections? Need to confirm with the maintainer / `docs/API.md` since the frontend may branch on `status`. The issue is framed as test-coverage, so I may need to confirm whether the accompanying behavior guard is in scope or should ship separately.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Resolved the Week 8 open question about the terminal state without needing to
wait on the maintainer, by reading the contract off the code: `core/models/review.py`
documents the status vocabulary as `pending`/`processing`/`complete`/`failed`, and
the frontend pins it as a closed union in `frontend/src/types/index.ts`. The polling
hook (`useReviewStatus.ts`) only stops on `complete` or `failed`, so inventing an
`empty` status would leave the UI polling forever, and `ReviewPage.tsx` already
renders `error_message` for failed reviews. That made `failed` + `error_message`
the clear choice — and it needs no migration, since `error_message` already exists
on the model and on `ReviewResponse`.

Done from PLAN.md: steps 1–4. The guard is implemented in `process_review`
(step 2), the `xfail` test is flipped to a passing assertion, and the companion
plus endpoint-level tests are written — `tests/unit/test_review_routes.py` went
from 2 tests to 7, all passing.

**Next steps:**
Step 5 — full verification against contribution standards, then the draft PR.

**Blockers:**
None remaining. `make` isn't available on my Windows setup, so I run the Makefile
targets through `.venv/Scripts/python.exe` directly.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/993

**Branch:** `test/88-review-endpoint-missing-documents`

**What you built:**
`POST /reviews` was marking reviews `complete` with three fabricated feedback
sections and `overall_score=0.81` for profiles that had ingested zero documents,
because the agent and RAG steps return hard-coded placeholder output regardless
of their input. I added an early guard in `process_review` that stops right after
ingestion when no sources were produced, recording `status="failed"` with empty
sections, a null score, and an explanatory `error_message` the existing UI already
knows how to display.

**Tests added or updated:**
`tests/unit/test_review_routes.py` — expanded from 2 tests to 7, covering the
terminal state, the error message, that the agent/RAG steps are skipped entirely,
the empty-string `resume_text` edge case, a regression guard that populated
profiles still reach `complete`, and an endpoint-level `TestClient` test asserting
`POST /reviews` returns `pending` immediately before the background task resolves
the review to `failed`. I confirmed the tests genuinely catch the bug by removing
the guard and re-running: 5 of the 7 fail, and the 2 that still pass are exactly
the ones that should.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both pass in the sense the course defines for a codebase with documented
pre-existing failures — my changes introduce no new ones. Measured in the same
environment before and after: **46 failed / 299 passed / 1 xfailed** before,
**46 failed / 305 passed** after, with an identical set of failing tests (I diffed
the `FAILED`/`ERROR` lines). The +6 passing are my 5 net-new tests plus the
previously-`xfail` test that now passes. `ruff` is clean on both changed files and
`mypy` reports the same 7 pre-existing errors before and after — 0 introduced.
Pre-existing issues I did not touch: 13 `AsyncMock().scalars()` failures in
`test_review_service.py`, and collection errors from `tiktoken`/`httpx`, which are
declared in `pyproject.toml` but were missing from my local venv.
`make test-integration` was not run — it requires Docker services I don't have.

**Draft PR feedback received from:** none — PR #993 was opened directly as ready
for review rather than as a draft, so no peer feedback was gathered before
submission.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback came in. PR #993 is still open with no reviews, no reviewer
assignments, and no comments. This is expected for Summer 2026, where reviewer
feedback isn't part of the course. Worth noting that the upstream repo had ~807
open PRs when I submitted, so a real maintainer response was never likely on a
one-week horizon.

I did retitle the PR after submitting. GitHub had auto-generated the title from
my branch name (`Test/88 review endpoint missing documents`), which doesn't match
the Conventional Commits standard in `docs/CONTRIBUTING.md`. Since maintainers on
a repo that size almost certainly squash-merge using the PR title, that would
have put a non-conforming commit on `main`. It's now
`fix(api): stop fabricating reviews for profiles with no documents`.

**How you responded:**
No feedback to respond to.

---

### Reflection

**What was harder than you expected?**

Verifying my own work was harder than writing it. The fix itself was about 15
lines; establishing that it was correct took longer than implementing it.

The sharpest example: to prove my tests actually caught the bug, I removed the
guard and re-ran them. The script I wrote to do this crashed on a Windows path
issue *before* it modified anything — but the test run afterward still printed
`7 passed`, which read exactly like confirmation. I nearly accepted that as proof
my tests were sound, when it proved nothing at all: the tests passed because the
fix was still in place. Re-running it properly showed 5 of 7 tests failing without
the guard, and that the 2 still passing were exactly the two that should (the
ingestion root-cause test and the happy-path regression guard). The failure mode
that scared me wasn't a broken test, it was a green result that meant nothing.

The second hard part was separating my breakage from the repo's. The suite had 45
failures and 7 collection errors before I touched anything, so "did the tests
pass?" was the wrong question. I had to diff the *set* of failing tests before and
after in the same environment. That also caught a red herring: an "un-awaited
coroutine" warning that pytest attributed to an unrelated `test_tech_detector`
test. It looked like mine. It wasn't — it came from the pre-existing
`AsyncMock().scalars()` misuse in `test_review_service.py`, and reproduced with my
file excluded entirely.

**What did you learn about working in a large codebase?**

That the answers to design questions are usually already written down in the code,
just not where you'd look for them.

I went into Week 9 with an open question I'd flagged as needing a maintainer:
should an empty-document review be `failed`, a new `empty` status, or `complete`
with no sections? I expected to be blocked. Instead I found the contract stated in
three places — `core/models/review.py` comments the vocabulary as
`pending`/`processing`/`complete`/`failed`, `frontend/src/types/index.ts` pins it
as a closed TypeScript union, and `useReviewStatus.ts` only stops polling on
`complete` or `failed`. That last one settled it: a new `empty` status would have
left the UI polling forever. And `ReviewPage.tsx` already renders `error_message`
for failed reviews, so the honest failure state had a UI path with no new work.

That's the real difference from my own projects. In my own code I *am* the
contract, so a question like this is a preference. Here the decision was already
constrained by consumers I didn't write and wouldn't have thought to check — the
frontend was the deciding evidence for a backend change. Reading outward from the
change to everything that depends on it is a habit my own projects never taught me,
because nothing else ever depended on them.

The other lesson: the blast radius of a "small" change is a judgment call. My issue
was framed as *test coverage*, but writing an honest test meant asserting behavior
that didn't exist, which meant changing behavior. I flagged that scope tension
explicitly in the PR rather than quietly expanding it, and noted I'd be happy to
split the guard into a separate PR if maintainers preferred tests-only.

**How did AI tools help — and where did they fall short?**

Most useful for orientation and for mechanical correctness. Tracing how
`process_review` reached the fabricated output, finding every place the status
vocabulary was defined across both the Python and TypeScript sides, and matching
the existing test file's mocking conventions were all much faster than they would
have been by hand. It was also good at the boring rigor — remembering to diff the
failure set before and after rather than eyeballing a pass count, checking that
`mypy` reported the same 7 errors before and after rather than assuming.

Where it fell short: it can't tell you what's *correct*, only what's *consistent*.
The `failed`-vs-`empty` decision came from reading the frontend and reasoning about
what would strand the UI — AI surfaced the evidence quickly but the call was a
judgment about a product contract. Same with scope: nothing in the tooling tells
you that a test-framed issue shouldn't quietly become a behavior change.

And it produced the exact failure I described above — a verification script that
silently no-opped and returned a result that looked like success. The tooling was
confident; the output was meaningless. What actually caught it was noticing the
result didn't square with what I expected to see. That's the part I couldn't
delegate: not generating the check, but being suspicious of a green one.

A limitation I'll own rather than paper over — my tests are heavily mocked. They
pin the guard's logic precisely, but they'd miss a real SQLAlchemy session or
migration problem, and I never ran the integration suite because it needs Docker
services I don't have. I'm confident about the branch I added, not about the full
path through a live database.

**What would you do differently if you started over?**

Open the draft PR early, in Week 8, instead of going straight to a finished PR in
Week 9. I skipped the peer-review step entirely and documented it honestly as
"none," but that was the one part of the process I actually lost value from. My
Week 8 open question about the terminal state was exactly the kind of thing a
draft PR exists to resolve — I ended up answering it myself by reading the
frontend, and I think the answer is right, but I never got it checked. A draft with
"is `failed` the contract you want here?" in the description would have cost
nothing.

I'd also set the environment up properly on day one. `make` isn't available on my
Windows setup, and `tiktoken` and `httpx` were declared in `pyproject.toml` but
missing from my venv — which meant 7 test modules couldn't even be collected. I
worked around that for two weeks by invoking `.venv/Scripts/python.exe` directly
before finally just installing the missing packages. The workaround was slower
than the fix, and it muddied my baseline measurements until I fixed it.

**What are you most proud of from this module?**

Not the fix — the moment I distrusted a passing test run.

Everything about that result said I was done: 7 tests, all green, on a fix I'd
just written. Chasing down why it *shouldn't* be trusted, and finding that my
verification had silently never run, is the thing I'd want to be judged on. The
guard itself is fifteen lines that any competent developer would write. Knowing
that "the tests pass" and "the tests would catch this bug" are different claims —
and building the experiment that separates them — is the part I didn't have four
weeks ago.

The related thing I'll keep: writing the failing test first, as a strict `xfail` in
Week 8. It meant that by the time I wrote the fix, the definition of "correct" was
already committed to the repo and couldn't quietly bend to whatever I happened to
implement.