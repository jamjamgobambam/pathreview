# JOURNAL

**Issue link:** https://github.com/ascherj/pathreview/issues/82

**Issue title:** Concurrent review requests for the same profile can produce inconsistent results

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Selection Reasoning:**

1. **I understand the problem.** Concurrent `POST /reviews` for the same profile race in `api/routes/reviews.py` and `core/services/review_service.py` — no per-profile lock, no idempotency, stale in-memory state across long awaits, no `IngestedSource` dedup. Before the fix: two overlapping runs overwrite each other's `sections` and double-insert evidence rows. After: duplicates are rejected up front, or serialized safely with consistent output. See problem summary below.

2. **Tier 3 is a scope match.** I've contributed to large codebases before, so navigating multi-file changes across `api/`, `core/services/`, and the DB layer isn't new territory. The problem sits squarely in mutex + caching territory, which I'm actively studying — so the difficulty is a stretch, not a leap.

3. **I've read the actual code, not just the issue.** I traced the request path through the two files, identified where the session leaks into the background task and where the state transition needs a lock + version guard, and posted a rough fix plan in [issue #82 comment](https://github.com/ascherj/pathreview/issues/82#issuecomment-5014425733).

4. **The claim count is fine (4–5), no blockers, and I've scoped it to fit before the Week 9 deadline.**

**Problem summary:**

Concurrent review requests for the same profile can produce inconsistent results because the pipeline in `api/routes/reviews.py` and `core/services/review_service.py` has no protection against overlapping runs. The request-scoped DB session leaks into the background task, `POST /reviews` has no idempotency check, the `Review` row has no lock or version guard, the in-memory review is held stale across long ingestion/agent/RAG awaits, and `IngestedSource` inserts have no dedup — so two loops can overwrite each other's `sections` and pile up duplicate ingestion rows. A successful fix gives the background task its own session, rejects duplicate in-flight creates for the same profile, gates the state transition on a per-profile lock and optimistic version, and enforces ingestion dedup so overlapping runs cannot double-insert. After the fix, two concurrent reviews should either converge on one consistent result or be safely serialized without lost writes or duplicated evidence.

**Out of scope**: LLM sampling non-determinism, external source drift, and orphaned `"processing"` rows from crashed tasks — separate issues.

**Branch name:** `fix/82-concurrent-reviews-races`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
