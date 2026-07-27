# Contribution Journal — PathReview

**Contributor:** Shawn Blackman (@sh4wnbk)
**Course:** CodePath AI 201, Module 3

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/13

**Issue title:** Add a content hash to detect unchanged documents and skip re-embedding

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview re-embeds every submitted document, even when the content hasn't changed, wasting embedding API calls on identical re-submissions. The pieces for skipping already exist — `ingestion/pipeline.py` computes a SHA256 content hash, and the `IngestedSource` model in `core/models/ingested_source.py` has an indexed `content_hash` column — but they're never connected: `_check_skip()` queries a placeholder string instead of the ORM model, and `_record_ingested_source()` only logs without writing a database row. A successful fix records each ingested source with its hash and skips the embedding step when the same content is re-submitted, while changed content still ingests normally.

**Selection notes ("Is this right for me?" checklist):**
- **Tier fit:** Tier 2 — the change spans the ingestion pipeline, the ORM model, and the database session. Five prior AI 201 projects (including a RAG pipeline and a Flask backend with an injected data store) cover the same kind of cross-module work. This exact pattern also replicates content-hash caching built for a geospatial research pipeline, so the design decisions (what to hash, where to store it, how to handle a miss) carry over directly.
- **Codebase readiness:** Both referenced files located and read, including the placeholder `_check_skip()` and `_record_ingested_source()` functions the fix will replace.
- **Tests:** No `tests/unit/test_pipeline.py` exists — the required test will be newly authored, following existing unit test patterns.
- **Scope and time:** Unclaimed at time of claiming, no blockers or dependencies; the 4–6 hour estimate fits the Week 8–9 window.

**Branch name:** `feat/13-content-hash-skip-reembedding`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

