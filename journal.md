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

**Branch name:** fix/82-concurrent-review-race

**Setup confirmation:** [x] App runs locally at localhost:5173
*(needs `docker compose up -d db`, `alembic upgrade head`, backend + frontend running — confirm once you've done this)*

**Cohort ledger:** [x] Issue added to cohort ledger
*(comment on #82 claiming it, then add it to whatever ledger/sheet your course uses)*