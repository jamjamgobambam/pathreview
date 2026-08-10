# Solution plan

**Issue:** `DELETE /profiles/{profile_id}` doesn't cascade to delete associated reviews and embeddings — https://github.com/ascherj/pathreview/issues/80

> **Status (Week 9): implemented.** See the "Resolved in Week 9" notes inline below for how each risk/unknown played out.

### Understand

**Root cause.** Deleting a profile has two data stores to clean up: PostgreSQL (relational rows) and ChromaDB (vector embeddings). The current `delete_profile` service in `core/services/profile_service.py` only handles Postgres — it deletes the profile's `Review` and `IngestedSource` rows (and the models also declare `ondelete="CASCADE"` FKs, so Postgres would enforce that anyway). It makes **zero** calls into the vector store. Each profile's embeddings live in a dedicated ChromaDB collection named `profile_{profile_id}` (see `rag/retriever/hybrid.py:42`), and nothing deletes that collection when the profile is deleted.

**Expected vs. actual.**
- *Expected:* after `DELETE /profiles/{id}` returns 204, no data keyed to that profile survives in either store — no review rows, no ingested-source rows, and no embeddings in the `profile_{id}` collection.
- *Actual:* the Postgres rows are removed, but the `profile_{id}` ChromaDB collection and all its embeddings remain orphaned forever. My reproduction test (`tests/integration/test_profile_delete_cascade_repro.py`) confirms the embeddings survive the current deletion path.

Note: the endpoint docstring already *claims* "cascade delete reviews and ingested sources," so the DB half is intentional; the embeddings half is the real gap.

### Map

Files touched:
- **`rag/retriever/vector_store.py`** — added `delete_collection(collection_name)`, wrapping `self.client.delete_collection(...)` and catching `chromadb.errors.NotFoundError` specifically so it's a safe no-op when nothing was ever ingested for that profile.
- **`core/services/profile_service.py`** — `delete_profile` now takes an optional `vector_store: VectorStore | None` param (for test injection; defaults to constructing its own `VectorStore()`) and calls `delete_collection(f"profile_{profile_id}")` *before* the Postgres deletes, so a vector-store failure aborts cleanly without touching Postgres.
- **`api/routes/profiles.py`** — docstring only, updated to say embeddings are cascaded too. Pre-existing lint issues in this file (import order, unused import, FastAPI `Depends`-in-default patterns) were **not** touched — not caused by this change, out of scope.
- **`tests/integration/test_profile_delete_cascade.py`** — renamed from `test_profile_delete_cascade_repro.py`; `xfail` removed, now a real regression test (embeddings gone after delete, a second profile's collection is untouched, no-embeddings profile is a safe no-op).
- **`tests/unit/test_vector_store.py`** *(new)* — unit coverage for `delete_collection` itself.
- **`tests/unit/test_profile_service.py`** *(new)* — unit coverage for `delete_profile`'s cascade ordering, error handling, and the default-vs-injected `VectorStore` paths.

Files read but not modified: `core/models/profile.py`, `core/models/review.py`, `core/models/ingested_source.py` (FK cascades were already correct).

### Plan

1. **Add `delete_collection` to `VectorStore`.** Wrap `self.client.delete_collection(name=collection_name)`; treat "collection does not exist" as a no-op (idempotent) and log the outcome, matching the logging style of `delete_by_source_id`.
2. **Wire vector cleanup into `delete_profile`.** After the existing Postgres deletions and before/around `db.commit()`, construct a `VectorStore` and call `delete_collection(f"profile_{profile_id}")`. Decide ordering so a vector-store failure can't silently leave Postgres committed but embeddings behind (see Risks).
3. **Make the reproduction test a real regression test.** Remove the `xfail` marker; assert the `profile_{id}` collection is empty/absent after deletion. Add a second assertion that a *different* profile's collection is untouched.
4. **Run the full check + unit suite** (`make check && make test-unit`) and the new integration test; fix any lint/type issues (e.g. import placement, mypy on the new method signature).
5. **Update the endpoint/service docstrings** to accurately state that embeddings are also removed, so the docs stop under-describing the behavior.

### Inputs & outputs

- **Input:** a `profile_id` (UUID) whose owner matches the authenticated user, arriving at `DELETE /profiles/{profile_id}`.
- **Output / change:** the profile row, its `reviews` rows, its `ingested_sources` rows, **and** its `profile_{profile_id}` ChromaDB collection are all removed. The endpoint still returns `204 No Content` on success and `404` when the profile doesn't exist or isn't owned by the caller. No orphaned embeddings remain.

### Risks & unknowns

- **Cross-store atomicity.** Postgres and ChromaDB can't share a transaction. If `db.commit()` succeeds but `delete_collection` throws (or vice-versa), I get a partial delete.
  - *Resolved:* `delete_profile` now deletes the vector store collection **first**, before touching Postgres. If it throws, the existing `except`/`rollback` fires and nothing in Postgres has changed — the whole request 500s and is safely retryable. Covered by `test_vector_store_failure_leaves_postgres_untouched` in `tests/unit/test_profile_service.py`.
- **VectorStore construction / persist path.** Needed to confirm which store the running app actually writes embeddings to, so deletion targets the same one.
  - *Resolved:* traced every call site — `VectorStore` and `IngestionPipeline` are never instantiated anywhere in the app (no route or orchestrator wires them up yet; ingestion is scaffolding with unit tests but isn't called from the API). There's no existing instantiation pattern to match, so `delete_profile` constructs `VectorStore()` with its class default (`persist_dir=".chromadb"`), and accepts an optional `vector_store` param for dependency injection in tests. Verified end-to-end against a live server: registered a user, created a profile, seeded embeddings directly into `.chromadb` under `profile_{id}`, called the real `DELETE /profiles/{id}` endpoint (got `204`), confirmed `GET` afterward returns `404` and the ChromaDB collection is gone.
- **`_record_ingested_source` is a placeholder.** In `ingestion/pipeline.py` it only logs — it doesn't actually write `IngestedSource` rows. Confirmed and left as-is; out of scope for this issue.
- **Chroma version drift.** The container pins `chromadb/chroma:0.4.22` (which crash-loops on numpy 2.0), while the installed library is `1.5.9`.
  - *Resolved for this fix:* `delete_collection` raises `chromadb.errors.NotFoundError` on a missing collection on the installed `1.5.9` client — caught specifically (not a bare `except`) so real connection failures still propagate. HTTP-mode (the `vector-db` Docker container) behavior is still unverified, but nothing in the app currently talks to that container (see above), so it doesn't affect this fix.

### Edge cases

- **Profile with no embeddings** (never ingested / collection never created): `delete_collection` must be a safe no-op, not a 500.
- **Profile not found or not owned by caller:** must still return 404 and touch neither store (existing behavior preserved).
- **Reviews/sources present but embeddings absent** (and the reverse): each store's cleanup must be independent so one empty store doesn't skip the other.
- **Concurrent/duplicate delete** of the same profile: second call should 404 cleanly and not error on an already-missing collection.
- **Deleting one profile must not touch another profile's collection** — collection targeting must be exact (`profile_{profile_id}`), asserted by the regression test.
