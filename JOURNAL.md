## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The POST /reviews endpoint has no test for creating a profile that has no ingested documents. Add a test that verifies the endpoint returns an appropriate error rather than crashing. 

**Branch name:** test/88-missing-ingested-docs-test

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Ran make test-unit to check which failures exist before I started working on this issue and whether any are relevant to Issue 88. I found that none of them were; there were 10 failures in test_review_service.py, but they do not call get_review or list_review services that are uwed by the POST /reviews endpoint.

- Discovered there are actually no precondition checks in create_review_endpoint that rejects when a profile has no github_username, resume_text, or portfolio_url.

- Reproduced issue: Created a profile via POST /profiles with no GitHub username, resume, or portfolio URL, then called POST /reviews against it directly via Swagger UI (bypassing the frontend, which does block this through required-field validation). The endpoint accepted the request and, after the background task ran, returned status: "complete" with a fabricated overall_score: 0.81 and three generic feedback sections — no error, no rejection. Confirms there is currently no server-side validation for zero-source profiles; the issue is broader than a missing test, since the endpoint silently produces misleading fabricated output.



**Next steps:**
Write tests/unit/test_review_routes.py::test_create_review_with_no_ingested_documents_does_not_reject, get it passing, run make check/make test-unit to confirm no regressions, then open the PR with the fabrication-bug finding called out in the description.

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** test/88-missing-ingested-docs-test

**What you built:**
Added a route-level test for POST /reviews confirming that a profile with no ingested documents (no GitHub username, resume, or portfolio URL) is currently accepted and completes with fabricated review content instead of returning an error — documenting a real gap rather than fixing it, per this issue's scope as a testing-only issue.

**Tests added or updated:**
tests/unit/test_review_routes.py (new file) — one test verifying current POST /reviews behavior for a zero-source profile via FastAPI TestClient with mocked auth/DB dependencies.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]