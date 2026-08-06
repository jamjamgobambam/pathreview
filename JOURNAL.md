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

**PR link:** _to be filled in — see "Submission" note below_

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

**Draft PR feedback received from:** none yet — draft PR opened for peer review in Slack