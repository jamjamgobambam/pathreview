## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/82

**Issue title:** Concurrent review requests for the same profile can produce inconsistent results

**Tier:** [x] Tier 3

**Problem summary:**
When two review requests for the same profile are submitted at nearly the same time,
`create_review()` has no check for an existing in-flight review before starting a new
one. Each request independently triggers `process_review()`, which re-runs the full
ingestion pipeline and writes its own `IngestedSource` and `Review` rows with no
coordination between the two runs. In practice this produces duplicate ingested data
for one profile and two competing review results with no clear "correct" outcome for
the client to read. A successful fix adds a guard — a per-profile lock, a DB-level
constraint, or a rejection of the second request — so that only one review can be
in progress for a given profile at a time. This affects `api/routes/reviews.py` and
`core/services/review_service.py`.

Scope-fit checklist — Is this right for me?

This issue sits at the right difficulty for where I am right now — hard enough that I have to make a real design decision instead of applying a mechanical patch, but bounded enough (two files, one traceable root cause) that I can actually finish it and reproduce it with confidence rather than getting lost in an open-ended problem. The full reasoning behind that verdict is below.

How I located the relevant files: The issue lists api/routes/reviews.py and core/services/review_service.py as relevant files. I didn't take that at face value — I read both files in full before committing to the issue, and traced the actual code path: POST /reviews in reviews.py calls create_review(), which hands off to process_review() in review_service.py. Neither function checks for an existing in-flight review before starting a new one, which is the actual root cause, not just a description of one.

What's the root cause, concretely? create_review() has no guard against two requests for the same profile_id running concurrently. Each call independently triggers process_review(), which re-runs _run_ingestion_pipeline() — so two overlapping requests produce duplicate IngestedSource rows and two competing Review records with no coordination between them.

**Branch name:** fix/82-concurrent-review-race

**Setup confirmation:** [x] App runs locally at localhost:5173
*(needs `docker compose up -d db`, `alembic upgrade head`, backend + frontend running — confirm once you've done this)*

**Cohort ledger:** [x] Issue added to cohort ledger
*(comment on #82 claiming it, then add it to whatever ledger/sheet your course uses)*