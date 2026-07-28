## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents
 

**Tier:** [Y] Tier 1  [ ] Tier 2  [ ] Tier 3
**Scope Reasoning**
[is this right for me?]
The issue is understandable, the reasoning behind it,as to why the review feature would be required, The consequences of not fixing it and what a successful fix looks like are all clear and explained clearly. The surrounding context and related file have been accessed.
The ideal fix has been decided.

**Problem summary:**
The POST /reviews endpoint has no test covering the case where a profile has no ingested documents. It doesn't crash — it silently succeeds, which is worse: `_run_ingestion_pipeline`correctly returns zero sources, but `process_review` never checks that before continuing, so the review is marked `complete` with fabricated sections and a score built from no real data. A successful fix adds that check, returns an honest response instead of invented feedback,
and includes a test verifying it.
**Branch name:** 
fix/88-no-profile-associated-ingested-content-review-endpoint

**Setup confirmation:** [Yes ] App runs locally at localhost:5173

**Cohort ledger:** [ Yes] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
https://github.com/rohitpeets/pathreview/commit/9379711

**Reproduction summary:**
I reproduced this issue by calling 'process_review' (in 'core/services/review_service.py') directly against a 'No Ingested document' state with a mocked async DB session , a profile with github_username=None,portfolio_url=None, and resume_text=None.
This was possible because every source field in profileCreate is optional with no 

_run_ingestion_pipeline` correctly returned zero sources, but `process_review` still marked the review `status="complete"` with 3 fabricated sections and `overall_score=0.81`, and the safety checks passed it.

The Issue reproduction pytest lives at 'tests/unit/test_issue88_reproduction.py'.

**PLAN.md link:**\https://github.com/rohitpeets/pathreview/blob/fix/88-no-profile-associated-ingested-content-review-endpoint/PLAN.md


**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm the intended contract for the zero-source case — reuse status="failed" with
an error_message, add a new status, or reject at the endpoint with a 4xx. The issue also
names tests/unit/test_review_routes.py, which doesn't exist yet, so I need to confirm whether route-level coverage is expected in addition to the service-level reproduction.