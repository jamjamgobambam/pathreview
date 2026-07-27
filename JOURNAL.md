## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` API route is missing a test for the case where a profile exists but has no ingested documents. Without that coverage, the endpoint could crash or return an unclear error and nobody would catch it. A successful fix adds a unit test (likely in `tests/unit/test_review_routes.py` or the existing review test files) that confirms the endpoint returns an appropriate error instead of failing unexpectedly. Scope is focused on tests for one edge case on the API layer, not a full feature rewrite.

**Branch name:** test/88-reviews-no-ingested-documents

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes — "Is this right for me?" checklist

| Check | Notes |
|---|---|
| Can I explain the bug in my own words? | Yes — profile exists, no ingested docs, review endpoint should error cleanly, and we need a test for that path. |
| Do I know which area of the codebase it touches? | Yes — API review routes + unit tests under `tests/unit/` (issue points at `test_review_routes.py`). |
| Is the scope small enough for Module 3? | Yes — Tier 1 / good first issue; estimated 2–3 hours; mostly adding one test case, not redesigning the review pipeline. |
| Do my skills match? | Yes — writing/asserting API unit tests is a good fit; I don't need deep RAG/agent work for this issue. |
| Is it still available / claimed? | I commented on the issue to claim it (AI 201 section 2a). Several others also commented, so I'll coordinate if needed and keep the work clearly scoped to the missing test. |
| Why this issue over others? | Clear acceptance criteria, named files, Tier 1, and it strengthens error-path coverage on a real API endpoint. |

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** empty

**Reproduction summary:**
Confirmed the gap locally: `tests/unit/test_review_routes.py` does not exist, and no unit test covers `POST /reviews` when a profile has no ingested content. `create_review` / `create_review_endpoint` never check for `IngestedSource` rows (or empty ingestible profile fields) before creating a `pending` review, so the empty-content path is untested and has no intentional 4xx error contract yet.

**PLAN.md link:** https://github.com/kevin-luk-3/pathreview/blob/test/88-reviews-no-ingested-documents/PLAN.md


**Blockers or open questions:**
Still need to decide exact error contract (400 vs 404) and whether “no ingested content” means zero `IngestedSource` rows at POST time vs. a profile with no resume/github/portfolio fields. May need a small validation change in the route/service so the new test asserts real behavior, not only mocks.
