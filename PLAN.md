## Solution plan

**Issue:** POST /reviews endpoint has no test for when the profile has no ingested documents — https://github.com/ascherj/pathreview/issues/88

### Understand
This is a **test-coverage gap**, not a functional bug in the usual sense. `POST /reviews`
(`api/routes/reviews.py`) creates a review with `status="pending"`, returns immediately,
and hands the real work to the background task `process_review`
(`core/services/review_service.py`). One realistic input is a profile with **no ingested
documents** — no `github_username`, no `portfolio_url`, and no `resume_text`. Nothing in
the test suite exercises this path, so the empty-profile contract is undefined and a future
change could silently break it.

Reproducing the path locally revealed the concrete behavior it currently produces:

- `_run_ingestion_pipeline(db, profile)` correctly returns `[]` (zero sources) for an empty
  profile.
- **However**, `_run_agent_orchestration` and `_run_rag_retrieval_generation` are placeholders
  that ignore `ingestion_results` and return hardcoded sections. `_run_safety_checks` then
  passes.
- Net result: `process_review` marks the review **`complete`** with **3 fabricated sections**
  and `overall_score=0.81`, even though there was zero real input.

**Expected:** the empty-document path is pinned down by an explicit, focused test so its
behavior is intentional and protected against regressions.
**Actual:** no test covers it; the empty path silently produces fabricated feedback.

### Map
Files involved (read/understand):
- `api/routes/reviews.py` — the `POST /reviews` handler (`create_review_endpoint`).
- `core/services/review_service.py` — `create_review`, `process_review`, and
  `_run_ingestion_pipeline` (the function whose output depends on the profile's sources).
- `core/models/profile.py` — the `Profile` model; the three nullable fields
  (`github_username`, `portfolio_url`, `resume_text`) that define "no ingested documents".
- `api/schemas/review.py` — `ReviewCreate` / `ReviewResponse` contract.
- `tests/unit/test_review_service.py` — existing tests; the `AsyncMock`/`Mock` fixture
  pattern to follow.

Files I expect to **touch**:
- `tests/unit/test_review_service.py` — add the new focused test(s) and an empty-profile
  fixture. (No product code changes — this is test-only work per the Tier 1 scope.)

### Plan
1. **Confirm the intended contract.** Clarify on the issue / with maintainers whether the
   empty-profile path should (a) still complete, (b) short-circuit to a distinct status, or
   (c) simply not error. The test's assertions must match the design, not just the current
   placeholder behavior.
2. **Add an empty-profile fixture** mirroring the existing `mock_profile` fixture but with
   `github_username=None`, `portfolio_url=None`, `resume_text=None`, `resume_filename=None`.
3. **Write the focused test** asserting the confirmed contract. The most tractable and
   deterministic assertion is that `_run_ingestion_pipeline` returns an empty list `[]` for an
   empty profile (the exact "no ingested documents" condition), and — if the contract calls
   for it — that `process_review` handles the empty result without raising.
4. **Follow the existing async mocking pattern** (`AsyncMock` session, `Mock()` for
   `db.add`, patched `Review`) so the new test passes reliably in the current environment.
5. **Run and lint:** `make test-unit`, then `ruff check .` / `black .`. Ensure the new test
   passes and I have not disturbed existing tests.

### Inputs & outputs
- **Input:** a `Profile` with no ingested sources (all three source fields `None`), plus a
  mocked async DB session.
- **Output:** one or more new **passing tests** in `tests/unit/test_review_service.py` that
  assert the empty-document contract. No product behavior changes; the deliverable is added
  test coverage that closes the gap.

### Risks & unknowns
- **Contract ambiguity (primary unknown):** the current placeholder returns fabricated
  feedback for zero input. If I assert that behavior verbatim, I would be codifying something
  that may be unintended. I need maintainer confirmation before locking in the assertion —
  otherwise the "fix" cements a possibly-wrong behavior.
- **Pre-existing failing tests:** 13 of 19 tests in `tests/unit/test_review_service.py`
  currently fail locally (`AsyncMock`/asyncio-mode setup, e.g. `scalars().all()` on an
  awaited mock). I must not build my test on the same broken pattern; I'll model it on a
  test that passes (e.g. `test_create_review_calls_db_add`).
- **Testing a background task:** `process_review` is `async` and commits to the DB; asserting
  its end state requires careful mocking of `db.execute`/`db.commit` and possibly patching
  the placeholder helpers.
- **Endpoint vs service level:** the issue names the endpoint, but the empty-document logic
  lives in the service. A true endpoint test needs auth + DB dependency overrides; a
  service-level unit test is lower-risk and targets the actual behavior. I'll decide based on
  the confirmed contract.

### Edge cases the fix should consider
- All three source fields `None` (the core case).
- Source fields present but empty strings (`""`) vs `None` — both should count as "no
  documents".
- A profile that exists but whose ingestion attempts all fail (still zero sources).
- Partial sources (e.g. `github_username` set but no resume/portfolio) — the non-empty path,
  used as a contrast to confirm the empty path is what's being asserted.
- `process_review` when the profile is not found (already handled: status set to `failed`).
