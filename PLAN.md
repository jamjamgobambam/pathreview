# PLAN — Issue #88

**Issue:** [`POST /reviews` endpoint has no test for when the profile has no ingested documents](https://github.com/ascherj/pathreview/issues/88)

## Reproduction

The endpoint's own code path was exercised directly (bypassing HTTP, calling the
route function and service layer as plain async functions with mocked DB/objects)
to see what actually happens today. Script: `scripts/repro_issue_88.py`.

**Step 1 — `POST /reviews` never checks the profile at all.**
`create_review_endpoint` (`api/routes/reviews.py`) takes only a `profile_id` and
immediately calls `create_review(db, profile_id, user_id)`, which inserts a
`Review` row with `status="pending"` and returns `200` — there is no lookup of
the `Profile` row and no check of whether it has any ingested content. Confirmed
by calling the endpoint function with a `profile_id` for a profile that has no
`github_username`, `portfolio_url`, or `resume_text`: it returns normally with
`status="pending"` and schedules the background task, exactly as it would for a
fully-populated profile.

**Step 2 — the background job doesn't error either, it fabricates feedback.**
`process_review` (`core/services/review_service.py`) was run against a `Profile`
with all three content fields set to `None`. Output:

```
ingestion_pipeline_completed   sources_count=0
agent_orchestration_completed  sections_count=2
rag_retrieval_completed
safety_checks_passed
review_processing_completed    overall_score=0.81
final review.status: complete
sections count: 3
overall_score: 0.81
```

`_run_ingestion_pipeline` correctly returns an empty list when there's nothing to
ingest, but `_run_agent_orchestration` and `_run_rag_retrieval_generation` are
placeholder implementations that return the same canned "Technical Skills /
Project Experience / Career Growth" sections regardless of input. `_run_safety_checks`
only validates structure (non-empty sections, valid confidence range), so it
passes. The review ends up `status="complete"` with a plausible-looking
`overall_score` — fabricated feedback for a profile with zero real content, and
nothing about the response tells the caller that happened.

**Conclusion:** there's no crash anywhere on this path, which is arguably worse
than the issue title suggests — the endpoint silently succeeds and returns
generic, made-up feedback instead of surfacing a clear error. This is why the
issue is filed as "no test," but a test alone would just be pinning down broken
behavior; a small validation fix is the more honest resolution.

## Root Cause

No code between the route handler and `create_review` ever fetches the `Profile`
row to check for ingestable content (`github_username`, `portfolio_url`,
`resume_text`, or rows in `ingested_source`). The gap is at the API boundary,
not in the ingestion/agent/RAG placeholders themselves (those are expected to be
stubs per `core/services/review_service.py`'s own docstrings).

## Proposed Solution

1. Add a small guard, e.g. `profile_has_ingestable_content(profile) -> bool` in
   `core/services/review_service.py`, checking `github_username`,
   `portfolio_url`, and `resume_text`.
2. In `create_review_endpoint`, fetch the `Profile` for `data.profile_id` before
   calling `create_review`. If it doesn't exist, return `404` (not currently
   handled either). If it exists but has no ingestable content, return `400`
   with a clear `detail` message instead of creating a review.
3. Keep `create_review()` itself unchanged — the guard belongs in the route
   layer so existing service-level tests (`tests/unit/test_review_service.py`)
   that call `create_review` directly keep passing unmodified.

## Test Plan

New file: `tests/unit/test_review_routes.py`, following the mock-based pattern
already used in `tests/unit/test_review_service.py` (mock `AsyncMock` DB
session, mock `Profile`/`User` objects, call the route function directly rather
than spinning up a real HTTP client/DB, matching how the rest of this codebase's
unit tests are written).

Planned cases:
- `test_create_review_returns_400_when_profile_has_no_ingested_content` — mock
  profile with `github_username=portfolio_url=resume_text=None`, assert the
  endpoint raises `HTTPException(400)` and that `db.add`/background task
  scheduling are **not** called.
- `test_create_review_returns_404_when_profile_not_found` — covers the other
  gap found during reproduction (no profile-existence check at all).
- `test_create_review_succeeds_when_profile_has_github_username` — regression
  guard so the happy path isn't broken by the new check.

## Files to Change

- `api/routes/reviews.py` — add profile lookup + validation in
  `create_review_endpoint`
- `core/services/review_service.py` — add `profile_has_ingestable_content`
  helper
- `tests/unit/test_review_routes.py` — new file, tests above

## Risks / Edge Cases

- Must not break `tests/unit/test_review_service.py`'s existing
  `create_review` tests — the new check stays in the route layer.
- A profile with rows in `ingested_source` but no `github_username`/
  `portfolio_url`/`resume_text` set directly (e.g. content added via another
  path) should probably also count as "has content" — worth confirming
  against `core/models/ingested_source.py` before finalizing the check in the
  actual PR.
- `make check` and `make test-unit` need to pass before opening the PR per
  `docs/CONTRIBUTING.md`.

## Pre-existing `make check` failures (verified before/after, per Week 9 guidance)

Before touching any code, `mypy` already failed on both files (missing type
annotations on `create_review`, `get_review`, `list_reviews`, `process_review`,
`_run_ingestion_pipeline` in `review_service.py`, and all four route handlers
in `reviews.py`). I type-annotated the `db` parameter (as `AsyncSession`) and
added return types everywhere it was safe to do so, since `make check`'s mypy
hook analyzes whole files, not just diff hunks.

Two functions -- `list_reviews` and `process_review` -- were deliberately left
with `db` untyped (their original, already-failing state). Typing them fully
exposes two *additional*, unrelated pre-existing bugs that only become visible
once mypy can see through the previously-`Any`-masked `db` parameter:
- `list_reviews`: `result.scalars().all()` returns `Sequence[Review]`, not the
  `list[Review]` the function signature promises.
- `process_review`: `review.sections = [...]` assigns a `list[dict]` to a
  column typed `Mapped[dict | None]` -- looks like an actual schema/logic
  mismatch worth its own issue, not something to guess-fix here.

Fixing either is out of scope for issue #88 and risks changing behavior other
reviewers depend on, so I left those two functions exactly as they already
were (still failing with the *original* "missing annotation" error, not a new
one) rather than trading one error for a different, unrelated one.

**Update after running the real pre-commit hooks (pinned tool versions, not
my sandbox approximation):** two more pre-existing issues surfaced once
`db` was fully typed on `get_review` (`review_service.py`) and, via the new
`get_profile` import, on `get_profile` (`profile_service.py`, also had to be
type-annotated for the same "mypy checks the whole file" reason described
above): both leak `Any` from `result.scalars().first()` back out of a
function declared to return a concrete `X | None` type
(`no-any-return`), independent of whether `db` is typed -- confirmed by the
fact that the *original* pristine `review_service.py` already had this exact
error (`get_review`, before any of my typing changes). This looks like a
SQLAlchemy stub limitation with this project's exact `.where()` clause
shapes, not a bug worth chasing down as part of #88.

Separately, my own new `-> ReviewResponse` return-type annotations on
`create_review_endpoint` and `get_review_endpoint` (previously these
functions had **no** return annotation at all, which is why mypy never
checked them) exposed that `ReviewResponse.model_validate(...)` also
resolves to `Any` under this pydantic stub version. Since I *did* introduce
that specific annotation, I fixed it properly rather than leaving it:
wrapped both calls in `typing.cast(ReviewResponse, ...)`, which is the
standard, honest way to tell mypy "this is safe" without hiding a real bug
(pydantic's `model_validate` always returns the correct instance type at
runtime; this is purely a stub-typing artifact).

Verified with a clean-room diff (mypy/ruff against `git show HEAD:<file>` vs.
my modified version, for both files): every remaining `mypy` error after my
change already existed, unchanged in kind, in the pristine original --
including the six "str vs UUID" `arg-type` errors (`current_user.id` is `str`
on the `User` model but every service function types `user_id: UUID`; my one
new `get_profile(...)` call follows this exact same pre-existing, already-
broken convention used by every other call in the file). `ruff` shows the
identical story: 14 pre-existing errors in `reviews.py` and 1 in
`review_service.py`, both before and after my change; my two new files
(`scripts/repro_issue_88.py`, `tests/unit/test_review_routes.py`) are fully
clean under `ruff check` and `black --check`.

**Net result:** my change fixes several pre-existing mypy errors (the
"missing annotation" ones on the functions I touch) and introduces zero new
ones. `make check` will still report pre-existing failures unrelated to #88 --
documented above, to be called out in the PR description per the Week 9
instructions on pre-existing failures.

**Whole-repo `make check` numbers (verified on the real dev environment, not
the sandbox):**
- `.venv/bin/mypy api/ core/ ingestion/ rag/ agent/ safety/` on this branch:
  5 errors, all missing-stub-package / numpy-version issues (`types-passlib`,
  `rank_bm25`, a numpy stub syntax error) that abort mypy before it reaches
  `api/routes/reviews.py` or `core/services/review_service.py` at all --
  entirely unrelated to #88.
- `.venv/bin/ruff check .` (whole repo): **182 errors on this branch, 182 on
  `main`** -- exact match, confirmed by running the identical command on both
  branches back to back. My change adds zero new ruff errors repo-wide.
- `.venv/bin/pytest tests/unit -v -m unit`: **53 failed / 384 passed on this
  branch, 53 failed / 375 passed on `main`** -- identical 53 failures on both,
  confirmed by running the identical command on both branches back to back.
  The 9-test delta (384 vs 375) is exactly my new `test_review_routes.py`
  tests, all passing.

The 53 pre-existing failures span many unrelated files -- several are
literally the *other* curated tier-1 issues from the tracker that classmates
are working (`test_readme_scorer.py::test_readme_with_all_quality_signals` is
#156, `test_relevance_scorer.py::test_query_with_partial_overlap` is #157,
`test_structural_chunker.py::test_document_with_no_headings` is #149,
`test_tech_detector.py::test_node_modules_excluded`/
`test_build_directory_excluded` is #150), confirming these are intentionally-
seeded, pre-existing bugs, not anything from my change. The 13
`test_review_service.py` failures (`test_get_review_*`, `test_list_reviews_*`)
are a separate `AsyncMock` chaining issue in that file, also verified
pre-existing (reproduced against the pristine, untouched file with zero code
changes).

**Summary for PR description:** `make check`/`make test-unit` were run on
both `main` and this branch. `ruff`: 182/182 (no new errors). `pytest
tests/unit`: 53 failed/384 passed here vs. 53 failed/375 passed on `main`
(exact same 53 failures; the extra 9 passes are this PR's new tests, zero
regressions). `mypy`: pre-existing missing-stub/numpy-version errors abort
the whole-repo run before reaching the files this PR touches; scoped to just
`api/routes/reviews.py` and `core/services/review_service.py`, this PR fixes
several "missing type annotation" errors and introduces none (verified via
clean-room diff against `git show HEAD:<file>`).
