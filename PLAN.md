## Solution plan

**Issue:** [#88 — POST /reviews endpoint has no test for when the profile has no ingested documents](https://github.com/ascherj/pathreview/issues/88)

### Understand

**Root cause.** `POST /reviews` accepts a `profile_id`, creates a `pending`
review, and schedules `process_review` as a background task. Inside
`process_review` (`core/services/review_service.py`), the ingestion pipeline
(`_run_ingestion_pipeline`) correctly returns an **empty** source list when a
profile has no `github_username`, `portfolio_url`, or `resume_text`. But the
downstream steps never check whether ingestion produced anything:
`_run_agent_orchestration` and `_run_rag_retrieval_generation` return
hard-coded placeholder sections regardless of their inputs. As a result the
review is marked `"complete"` with fabricated feedback and a non-null
`overall_score`.

There is **no test** covering this empty-document path — the stated Tier-1
gap — so the fabrication goes unnoticed.

**Expected vs. actual** (for a profile with zero ingested documents):

| | Expected | Actual |
|---|---|---|
| Ingested sources | 0 | 0 |
| Review status | not `complete` (e.g. `failed` / `empty`) | `complete` |
| Sections | none / explanatory | 3 fabricated sections |
| overall_score | `None` | `0.81` |

Reproduced locally — see the reproduction commit and
[tests/unit/test_review_routes.py](tests/unit/test_review_routes.py).

### Map

Files/functions involved:

- [core/services/review_service.py](core/services/review_service.py)
  - `process_review` — needs an early guard after ingestion.
  - `_run_ingestion_pipeline` — source of the empty list (behaves correctly; no change expected).
- [api/routes/reviews.py](api/routes/reviews.py) — `create_review_endpoint` (endpoint under test; likely unchanged).
- [tests/unit/test_review_routes.py](tests/unit/test_review_routes.py) — where the new coverage lands (**primary deliverable**).
- [api/schemas/review.py](api/schemas/review.py) — confirm the shape a no-document review should return.

Files I expect to touch:
1. `tests/unit/test_review_routes.py` — add the empty-document test(s).
2. `core/services/review_service.py` — add the empty-ingestion guard.

### Plan

1. **Keep the reproduction tests** already added to `test_review_routes.py`
   (root-cause test + `xfail` desired-behavior test).
2. **Add the guard** in `process_review`: after `_run_ingestion_pipeline`, if
   `ingestion_results` is empty, stop the pipeline and set a terminal state
   (`status="failed"` with an empty `sections=[]` and `overall_score=None`),
   logging a `review_empty_profile` event — instead of running agent/RAG steps.
3. **Flip the `xfail`** into a passing assertion once the guard exists, and add
   companion tests: (a) empty profile → non-`complete` terminal status with no
   fabricated sections; (b) non-empty profile still reaches `complete`
   (regression guard so the fix doesn't break the happy path).
4. **Add an endpoint-level test** with FastAPI `TestClient`, overriding
   `get_current_user` / `get_db`, asserting `POST /reviews` returns a `pending`
   review immediately and that the background task leaves an empty profile in
   the terminal non-`complete` state.
5. **Run** `make test-unit` (or `pytest tests/unit -m unit`) and confirm green.

### Inputs & outputs

- **Input:** a `Profile` with all source fields empty/`None` (and a valid
  authenticated user), driven through `create_review` → `process_review`.
- **Output/change:** new assertions in the test suite; a small behavioral
  guard so an empty-document review terminates in a truthful state
  (`failed`/empty) rather than a fabricated `complete` one.

### Risks & unknowns

- **Which terminal state is "correct"?** `failed` vs. a new `empty`/`skipped`
  status vs. `complete` with empty sections. Need to confirm the intended
  contract with the maintainer / `docs/API.md`; the frontend may branch on
  `status`. I'll default to `failed` + `sections=[]` and flag it in the PR.
- **Scope creep:** the issue is framed as *test coverage*. The guard is a
  minimal behavior change to make the desired test pass; if maintainers prefer
  tests-only, I can land the tests as `xfail` documenting the gap and open the
  behavior change separately.
- **Pre-existing async-mock failures** in `test_review_service.py` (13 fail due
  to `AsyncMock().scalars()` returning a coroutine) — out of scope, but I'll use
  plain `Mock` result objects to avoid the same trap.

### Edge cases

- Profile with **some** sources missing but at least one present → must still
  reach `complete` (only *fully* empty profiles are affected).
- Profile that doesn't exist → already handled (`status="failed"`).
- Whitespace-only / empty-string `resume_text` (`""`) → treated as no source
  (falsy), should follow the empty path; confirm with a test.
- Background-task exceptions → existing `except` sets `status="failed"`; the
  new guard should not mask genuine failures.
