## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** `review_service unit tests misconfigure async mocks — 13 of 19 tests fail` 

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`review_service` unit tests are misconfigured to use Async mocks for the review `results` object, which leads to 13 tests out of 19 failing trying to call `.first()` on a coroutine (`AttributeError: 'coroutine' object has no attribute 'first'`). A successful fix would use `AsyncMock` for `execute` but use `MagicMock` for the review object, leading to a full passing suite.

**Selection reasoning:**

I chose this Tier 1 issue for several reasons including:

- This is my first time contributing to an open-source project (even if simulated).
- The fix is limited only to a unit test file `tests/unit/test_review_service.py` and doesn't need me to touch the actual review service itself, so I can get used to navigating the repo's test setup and conventions before tackling an issue that requires more knowledge of the codebase.
- I have little experience in pytest and I find it really interesting to understand the library and TDD in general.

**Branch name:** `fix/158-reviewservice-tests-fail`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/rnossair/pathreview/commit/bdff0e3064fbac2d9f9b68533de7104cee48ff71

**Reproduction summary:**
I ran `pytest tests/unit/test_review_service.py -v` after `make setup` and saw 13 of 19 tests fail with `AttributeError: 'coroutine' object has no attribute 'first'` (or `'all'`), plus a `RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited` — confirming the `mock_result = AsyncMock()` mismatch described in the Week 7 problem summary.

**PLAN.md link:** [PLAN.md](https://github.com/rnossair/pathreview/blob/bdff0e3064fbac2d9f9b68533de7104cee48ff71/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
No major blockers — root cause and fix are fully scoped in PLAN.md. Going into Week 9, the main thing I want to double check is whether any other test files in the repo have the same `AsyncMock`/`MagicMock` mismatch, so I can flag or fix those too rather than just this one file.

## Week 9 — Solution building & PR submission

### Check-in (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/555

**Branch:** `fix/158-reviewservice-tests-fail`

**What you built:**
`tests/unit/test_review_service.py` built its DB query-result mock as `AsyncMock()` with no `spec`, so `.scalars()`/`.first()`/`.all()` returned live coroutines instead of their configured return values — only `db.execute()` itself is genuinely async in real SQLAlchemy. Switching `mock_result` to `MagicMock()` across the 13 affected tests fixed the mismatch. I also had to bump `[tool.mypy] python_version` to 3.12 and scope the local pre-commit mypy hook to match CI's, since a pre-existing numpy/mypy version mismatch was blocking any commit that touched a `.py` file at all.

**Tests added or updated:**
Only `tests/unit/test_review_service.py` — no new tests needed, since the existing 19 already covered `create_review`, `get_review`, and `list_reviews` correctly; they just couldn't run due to the mock misconfiguration. Went from 6/19 to 18/19 passing (the 1 remaining failure is a separate, pre-existing bug out of scope for #158 — documented in the PR).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
(Both fail at the full-repo level on pre-existing, unrelated issues — 174 ruff errors, 103 mypy errors, and 41 failing unit tests elsewhere in the repo, none introduced by this PR. Scoped to the files this PR touches, lint/typecheck are clean and `test_review_service.py` is 18/19.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review came in for the PR so far.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
The firat part was understanding the unit tests framework in Python as someone who has up until now mostly worked with Ts/Js codebases. Afterwards was understanding the different Mock classes and why choosing the wrong one caused so many tests to fail.

**What did you learn about working in a large codebase?**
Working in a large codebase means you're held to a pre-existing standard when contributing to it; styling conventions, test coverage expectations, and infrastructure constraints (like pre-commit hooks) shape your work in ways that don't exist in personal projects.

**How did AI tools help — and where did they fall short?**
AI Assistance was most helpful when understanding new frameworks or understanding how some services functionned, but I oftentimes found myself searching online for more details about some specific classes.

**What would you do differently if you started over?**
I think if I had more time this summer, I would have liked to choose a Tier 2 issue that would challenge me a bit further. I believe it would have been more beneficial for me if I had the chance to explore the codebase with more details, especially using AI.

**What are you most proud of from this module?**
I feel like this module gave me the confidence and knowledge to kick-off a first real open-source contribution, and I'm excited to see myself grow more and more adaptable as I navigate new codebases and hope to have a PR merged into a real project.