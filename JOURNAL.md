## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/13

**Issue title:** Add a content hash to detect unchanged documents and skip re-embedding

**Tier:** [ ] Tier 1  [*] Tier 2  [ ] Tier 3

**Problem summary:**
The ingestion pipeline re-embeds every resume, README, and repo submission from scratch on every ingestion call, even when the content is byte-for-byte identical to something already processed. The dedup logic already existed in shape — a content hash was computed and folded into `source_id`, and the `IngestedSource` model even had an unused `content_hash` column — but the wiring was never finished: the skip-check queried a placeholder instead of the real database model and always returned nothing, and the record-keeping step only logged instead of writing to the database. On top of that, the database session is async-only but the pipeline's methods were synchronous, so even a corrected query couldn't have worked as written. A successful fix detects when resubmitted content is unchanged and skips parsing, chunking, and embedding entirely, cutting unnecessary embedding-API calls and redundant vector-store writes without touching the case where content actually changed.

**"Is this right for me?" checklist reasoning:**
I wasn't able to retrieve the course page's own "Is this right for me?" checklist (behind course-portal auth), so this is my scope reasoning based on what's actually verifiable about the issue:
- **Tier fit:** Manifest labels this tier-2 with an estimated 4–6 hours. Reasonable for a fix that touches a well-scoped, single-pipeline concern rather than a cross-cutting or architectural change.
- **Files touched matched the estimate at first glance:** the manifest listed `ingestion/pipeline.py` and `core/models/ingested_source.py` — both were touched, plus a migration and a new test file, which is normal for a tier-2 DB-touching change.
- **Where the real scope exceeded the estimate:** the pipeline's DB calls were dead code (a string-literal query, a log-only "record" stub), and the codebase's only DB session type is async — so the fix also required converting several methods to `async def`, which the manifest entry didn't call out. Still within tier-2 territory, just more plumbing than the one-line description suggested.
- **Verdict:** right-sized for the tier — self-contained, testable in isolation with mocks (no live Postgres/Chroma needed), and didn't require touching unrelated systems (RAG, agent, safety) to complete.

**Branch name:** feat/13-hashtodetect-unchange

**Setup confirmation:** [*] App runs locally at localhost:5173

**Cohort ledger:** [*] Issue added to cohort ledger