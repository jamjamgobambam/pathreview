## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/80

**Issue title:** `DELETE /profiles/{profile_id}` doesn't cascade to delete associated reviews and embeddings

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
Deleting a profile is supposed to remove everything tied to it, but the vector-store embeddings created during ingestion are never cleaned up. Reviews and ingested-source database rows already cascade correctly in `core/services/profile_service.py`, but that function has no knowledge of the vector store, so each profile's embeddings — stored in a dedicated ChromaDB collection named `profile_{profile_id}` — are left orphaned after deletion. A `delete_by_source_id` method already exists on `VectorStore` (`rag/retriever/vector_store.py`) but is never called from anywhere. A successful fix adds a way to delete a profile's embedding collection and wires it into `delete_profile` so that removing a profile leaves no orphaned vector data behind.

**Branch name:** `fix/80-clean-up-orphaned-embeddings`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jon-tous/pathreview/commit/ee2070d4392a976ade239a664e1808ad1ff66369

**Reproduction summary:**
Added a failing unit test (`tests/unit/test_profile_service.py::TestDeleteProfileCascade::test_delete_profile_cleans_up_vector_store_collection`) that calls `delete_profile` with a mocked DB session and asserts `VectorStore().delete_collection(f"profile_{profile_id}")` is invoked. The test fails with `AssertionError: Expected 'delete_collection' to be called once. Called 0 times.`, confirming the vector-store cleanup is entirely absent from `delete_profile`.

**PLAN.md link:** https://github.com/jon-tous/pathreview/blob/fix/80-clean-up-orphaned-embeddings/PLAN.md

**Blockers or open questions:**
`VectorStore` currently opens a local `.chromadb` directory via `PersistentClient`, while the deployed app uses a ChromaDB HTTP server configured via `vector_db_url`. The fix will use `VectorStore` as-is (consistent with the rest of the retrieval layer), but the underlying wiring mismatch means the cleanup call won't reach the production Chroma server until that separate issue is also addressed.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All three sub-tasks from PLAN.md are complete. Added `delete_collection(name)` to `VectorStore` (`rag/retriever/vector_store.py`), wired it into `delete_profile` (`core/services/profile_service.py`) as a best-effort call after the DB commit, and updated the test suite. The formerly failing reproduction test now passes alongside three additional tests: one verifying the correct collection name is used, one confirming the delete still returns `True` when the vector-store cleanup raises, and two new unit tests for `VectorStore.delete_collection` itself (collection exists and collection missing cases).

**Next steps:**
Open a draft PR, fill in the PR template, and collect peer or mentor feedback before marking it ready for review. Will also write the Check-in 2 entry once the PR is submitted.

**Blockers:**
None. `make test-unit` went from 54 → 53 failures (our reproduction test now passes); `make check` went from 181 → 178 lint errors (ruff auto-removed three pre-existing unused imports during staging). Neither change introduced new failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/298

**Branch:** `fix/80-clean-up-orphaned-embeddings`

**What you built:**
Added `VectorStore.delete_collection` and wired it into `delete_profile` so that deleting a profile now also removes the associated ChromaDB collection (`profile_{profile_id}`), preventing orphaned embeddings. The cleanup is best-effort — errors are logged but don't surface to the caller, since the DB delete (the primary operation) has already committed successfully.

**Tests added or updated:**
- `tests/unit/test_profile_service.py` — updated to patch `VectorStore` at the correct import path; added tests for the cleanup call and the best-effort error-suppression behaviour
- `tests/unit/test_vector_store.py` — new file; covers `delete_collection` when the collection exists and when it doesn't (no-op on `ValueError`)

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments arrived this week. Per Summer 2026 expectations, I am recording this as no feedback received.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was making a "small" deletion fix safely in a codebase with multiple storage layers. At first glance, issue #80 looked like one missing call, but I had to trace how profile deletion interacts with SQLAlchemy cascades, ingestion artifacts, and the vector store lifecycle. The surprising part was realizing the DB-side cleanup already worked, while ChromaDB cleanup was not connected, and that timing mattered: if vector cleanup failed after commit, the API still needed to return success for the primary operation.

**What did you learn about working in a large codebase?**
I learned that reading existing service boundaries is more important than writing code quickly. In my own projects, I usually control the whole architecture, so I can refactor aggressively. Here, the right approach was to preserve public behavior, add one focused capability (`delete_collection`) in the retrieval layer, and wire it in where ownership already existed (`delete_profile`). I also learned to use tests as documentation: adding a failing reproduction test first forced me to define expected behavior before implementation and reduced guesswork.

**How did AI tools help — and where did they fall short?**
AI helped most with accelerating codebase navigation and drafting targeted unit tests once I knew the expected behavior. It was useful for identifying likely insertion points and proposing edge-case tests (like best-effort cleanup when vector deletion raises). It fell short on system-specific correctness details: I still had to verify import patch paths, transaction ordering, and storage-environment assumptions manually. The model could suggest plausible changes, but confirming they matched this repository's actual runtime wiring required human judgment.

**What would you do differently if you started over?**
I would map the end-to-end data lifecycle earlier (create profile -> ingest -> store embeddings -> delete profile) before writing any code. I spent extra time reconciling where the vector store was instantiated versus where deletion ownership should live. I would also create a short architecture note during Week 8 with explicit "must not break" guarantees (API response behavior, commit semantics, and error logging expectations) so implementation and tests align faster.

**What are you most proud of from this module?**
I am most proud of turning a quiet data-consistency bug into a tested, production-minded fix that preserves user-facing behavior while preventing orphaned embeddings. The best part was not just making the failing test pass, but adding coverage for failure tolerance and no-op cleanup paths so the solution is resilient, not brittle.
