## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The unit tests in test_review_service.py fail because the async
database mock is set up incorrectly. The service code properly awaits
db.execute(...) and then calls .scalars().first() or .scalars().all()
on the result, but the test mocks make execute() itself return a plain
coroutine instead of a mock result object, so scalars() is called on a
coroutine rather than a proper mock — causing an AttributeError. The
service logic in review_service is actually correct; only the test
mocks need to be reworked (e.g. using AsyncMock for execute() and a
MagicMock for the returned result object) so that 13 currently-failing
tests pass.

**Selection reasoning:**
I chose this issue because it's scoped to a single test file
(test_review_service.py) with a clearly reproducible failure command,
which fits my comfort level as a first-time contributor to a large
codebase. The fix only requires adjusting mock configuration (AsyncMock/
MagicMock), not touching the service logic itself, so the blast radius
is small and easy to verify by re-running pytest. This matches the
Tier 1 label — a good first issue that lets me practice the branch/PR
workflow without needing deep familiarity with the RAG or agent systems yet.

**Branch name:** fix/158-review-service-async-mocks

**Setup confirmation:** [x] App runs locally at localhost:5173
![alt text](image.png)

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tbnguye9/pathreview/commit/b41420d6413b53a4011b70427b5b1f4e5398861d

**Reproduction summary:**
Ran `python -m pytest tests/unit/test_review_service.py -q` in the local
venv and observed `13 failed, 6 passed` with `AttributeError: 'coroutine'
object has no attribute 'first'` / `'all'`. Confirmed the root cause: each
failing test builds the DB result object as an `AsyncMock`, so calling
`result.scalars()` returns a coroutine, and the service's synchronous
`.first()` / `.all()` call on that coroutine raises. The service logic is
correct — only the test mocks are misconfigured. Reproduction steps and a
mock experiment proving the fix direction are in
[docs/reproduction-158.md](docs/reproduction-158.md).

**PLAN.md link:** https://github.com/tbnguye9/pathreview/blob/fix/158-review-service-async-mocks/PLAN.md

**Walkthrough video (recommended):** _(not recorded yet — optional)_

**Blockers or open questions:**
Need to confirm CI's Python version matches my local 3.14 so `unittest.mock`
semantics are identical. Also deciding whether to hoist the repeated mock
setup into a shared fixture (cleaner, prevents regression) or keep the diff
minimal with an inline change per test — will pick based on maintainer
preference in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md. In `tests/unit/test_review_service.py` I
imported `MagicMock` and changed the result object in the 13 failing tests
from `AsyncMock()` to `MagicMock()`, keeping `db.execute` as an `AsyncMock`
(it is awaited). Running `pytest tests/unit/test_review_service.py -q` went
from `13 failed, 6 passed` to `18 passed, 1 failed`. The last failure
(`test_list_reviews_ordered_by_created_at`) turned out to be a *second*,
separate assertion bug: it asserted `execute.assert_called_once()`, but
`list_reviews` issues two queries (count + page), so `execute` is called
twice. Fixed that assertion → `19 passed`.

**Next steps:**
Run the full `make test-unit` and `make check` to document pre-existing
failures, commit and push, open a draft PR for peer feedback, then finalize.

**Blockers:**
The repo's pre-commit hooks (ruff/black/mypy) and `make check` fail on
pre-existing, repo-wide issues unrelated to #158 (untyped functions across
the whole codebase, etc.). Confirming the "no new failures" interpretation
holds for grading.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/371

**Branch:** `fix/158-review-service-async-mocks`

**What you built:**
A test-only fix for issue #158. The `review_service` unit tests mocked the
SQLAlchemy result object as an `AsyncMock`, so `result.scalars()` returned a
coroutine and the service's synchronous `.first()`/`.all()` calls raised
`AttributeError`. Switching the result object to `MagicMock` (while keeping
the awaited `execute` as `AsyncMock`) fixes it; I also corrected one
assertion that expected `execute` to be called once when `list_reviews`
legitimately calls it twice.

**Tests added or updated:**
`tests/unit/test_review_service.py` — reconfigured async mocks in the 13
tests covering `get_review` and `list_reviews`, and fixed the call-count
assertion in `test_list_reviews_ordered_by_created_at`. The file now passes
19/19 (was 13 failed, 6 passed).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
> Interpreted per the pre-existing-failure guidance: this change introduces
> **no new failures**. Baseline `make test-unit`: 53 failed → 40 failed after
> my change (13 fixed, all in `test_review_service.py`). `make check`
> (ruff/black/mypy) has documented pre-existing failures repo-wide; none are
> introduced by this test-only change. Details in the PR description.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in. Per the Summer 2026 course note, maintainer
review is not part of the program this term, and PR #158
(https://github.com/ascherj/pathreview/pull/371) shows no comments — only the
expected "review required / merging blocked" status that applies to any
outside contributor without write access.

**How you responded:**
No changes required, since no feedback arrived. The PR remains open and Ready
for review (not draft) so a maintainer could pick it up. If a reviewer had
asked for the shared-fixture refactor I flagged as an optional follow-up, I
would have added a `mock_result_first` / `mock_result_all` fixture to remove
the repeated mock setup across the 13 tests.

---

### Reflection

**What was harder than you expected?**
The bug looked like a one-line swap, but understanding *why* it was wrong took
real care. The trap is that `db.execute` and the result object need *opposite*
mock types: `execute` is awaited so it must stay an `AsyncMock`, but the
result proxy is used synchronously (`result.scalars().first()`), so it must be
a `MagicMock`. With an `AsyncMock`, `scalars()` silently returns a coroutine
instead of erroring at the mock, and the failure only surfaces later as
`AttributeError: 'coroutine' object has no attribute 'first'`. The harder part
was that fixing the 13 mocks exposed a *second*, undocumented bug the issue
never mentioned: `test_list_reviews_ordered_by_created_at` asserted
`execute.assert_called_once()`, but `list_reviews` runs two queries (count +
page), so execute is called twice. That assertion had been masked all along
because the test crashed on the `AttributeError` before ever reaching it.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is mostly about *restraint*.
Running `make test-unit` showed 53 pre-existing failures and `make check`
flagged 182 ruff errors and 52 files black wanted to reformat — almost none of
it related to #158. My instinct on my own project would be to "clean it all
up," but here the right move was the opposite: keep the diff surgical (2 files,
only the mock type and one assertion), *not* run `black`/`ruff --fix` across
the file, and instead document the pre-existing state in the PR so a reviewer
can see my change introduces zero new failures (53 → 40, all 13 fixed in one
file). I also had to respect conventions I didn't set — Conventional Commit
messages, the `fix/<issue>-<slug>` branch name, and the PR template — because
in a shared repo those are contracts, not preferences.

**How did AI tools help — and where did they fall short?**
AI was strongest at *tracing and verifying*: reproducing the failure,
explaining the AsyncMock-returns-a-coroutine mechanism, and running a tiny
throwaway experiment (`good = MagicMock(); good.scalars().first()`) to prove
the fix direction before touching the real file. Where it fell short was
*judgment about contribution etiquette* — the decisions that weren't in the
code: whether to commit with `--no-verify` when the pre-commit hooks fail on
repo-wide debt I can't fix, whether fixing the second assertion bug was in
scope for #158, and whether a minimal diff or a fully-formatted diff would
serve the reviewer better. Those were trade-offs I had to reason through
myself; AI could lay out the options but not decide what a maintainer of *this*
repo would prefer.

**What would you do differently if you started over?**
I would run the *full* `make test-unit` and `make check` baseline on day one,
before writing any code. I discovered the 53 pre-existing failures and the
broken pre-commit hooks late, which forced some rework in how I framed the PR.
Knowing the baseline up front would have let me plan the "no new failures"
argument from the start. I'd also have read `test_list_reviews_ordered_by_created_at`
more skeptically earlier — the double-execute behavior was visible in the
service code the whole time.

**What are you most proud of?**
Catching and fixing the second assertion bug that wasn't in the issue at all.
The issue asked me to rework the async mocks; getting all 19 tests green
required noticing that one test's `assert_called_once()` was simply wrong about
how `list_reviews` queries the database. Going one step past the literal ask —
while still keeping the fix disciplined and well-documented — is the part that
felt like real engineering rather than just following instructions.