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