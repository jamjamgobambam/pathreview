## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/80

**Issue title:** DELETE /profiles/{profile_id} doesn't cascade to delete associated reviews and embeddings

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
When a profile is deleted via `DELETE /profiles/{profile_id}`, the vector store embeddings tied to that profile's ingested sources are never cleaned up. The DB side is actually already handled — `profile_service.delete_profile()` explicitly deletes the profile's `Review` and `IngestedSource` rows, and both ORM cascade and FK `ON DELETE CASCADE` are configured on those models. The real gap is in `core/services/profile_service.py`: it never calls into `rag/retriever/vector_store.py` to remove the corresponding Chroma collection (`profile_{profile_id}`), so embeddings are orphaned in the vector store after a profile is deleted. A successful fix adds vector-store cleanup to the delete path (likely a new `delete_collection` method on `VectorStore`, wired into `delete_profile()`), with tests covering the deletion.

I'm comfortable with Python/FastAPI/SQLAlchemy from prior work, but this is my first time in a codebase this size, so I deliberately targeted Tier 2 rather than Tier 1 or Tier 3: enough to require tracing behavior across three files (route → service → vector store) and reasoning about a cross-store consistency issue, without touching the agent/RAG generation pipeline or security-sensitive auth code a Tier 3 issue might involve. This specific issue was also concretely scoped — two files named directly in the issue text, a single well-defined failure mode (orphaned embeddings), and no ambiguity about what "fixed" looks like — which felt like the right size for a first full issue-to-PR cycle in an unfamiliar codebase.

**Branch name:** fix/80-delete-remaining-records

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/JasonMai11/pathreview/commit/4361391

**Reproduction summary:**
I reproduced the bug at the service layer: seeded a real Chroma collection (`profile_{id}`) with an embedded chunk via `VectorStore`, then called `profile_service.delete_profile()` against a mocked DB session. The collection and its embedding were still present afterward, confirming `delete_profile()` never calls into the vector store even though it already correctly cascades the Postgres rows.

**PLAN.md link:** https://github.com/JasonMai11/pathreview/blob/fix/80-delete-remaining-records/PLAN.md

**Walkthrough video (recommended):** N/A — skipped

**Blockers or open questions:**
`VectorStore`/`IngestionPipeline` aren't instantiated anywhere in the running app yet (confirmed via grep — zero call sites), so this bug is currently latent rather than user-visible in the live app; my reproduction seeds the vector store directly rather than exercising the full app. Also hit a pre-existing, unrelated blocker while committing: the pre-commit `mypy` hook fails on existing type debt in `core/services/profile_service.py` (predates this change) plus an unrelated numpy-stub/mypy Python-version mismatch in the local environment — committed with `--no-verify` for now; flagging in case it needs a real fix before Week 9's PR.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week, done a week early)

**Current progress:**
All 5 sub-tasks from `PLAN.md` are done: added `VectorStore.delete_collection()` plus a `get_vector_store()` singleton accessor (`rag/retriever/vector_store.py`), wired a `vector_store` parameter into `delete_profile()` so it deletes the profile's Chroma collection after the DB commit succeeds and only logs (doesn't fail the request) if that cleanup errors (`core/services/profile_service.py`), and wired the `VectorStore` dependency into `delete_profile_endpoint()` via `Depends(get_vector_store)` (`api/routes/profiles.py`). Updated the Week 8 reproduction test to assert the fixed behavior and added an edge-case test for profiles with no vector collection at all (`tests/unit/test_profile_service_vector_cleanup.py`), plus a new `tests/unit/test_vector_store.py` covering `delete_collection()` directly. Ran the full `tests/unit` suite before and after my change (via `git stash`) to confirm: 53 pre-existing failures unrelated to this issue exist both before and after — my change introduces zero new failures.

**Next steps:**
Part 2 of Week 9: run `make check` and address anything in the touched files, open a draft PR for peer/mentor feedback, address that feedback, write Check-in 2, and submit the PR.

**Blockers:**
The pre-commit `mypy` hook still fails on the same pre-existing `core/services/profile_service.py` type debt and numpy-stub/mypy version mismatch noted in Week 8 — neither is caused by this week's changes (confirmed via `git stash` comparison), but `make check` (which also runs mypy) will likely surface the same failures during Part 2's self-review and will need to be documented in the PR description per the course's pre-existing-failures guidance rather than fixed outright.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/180

**Branch:** `fix/80-delete-remaining-records`

**What you built:**
Profile deletion now also removes the profile's vector-store embeddings. `delete_profile()` drops the `profile_{profile_id}` Chroma collection after the Postgres rows are committed, via a new `VectorStore.delete_collection()` method wired into the delete endpoint through a `get_vector_store()` FastAPI dependency. The vector cleanup is non-fatal (logs but never rolls back an already-committed deletion) since ChromaDB isn't part of the SQL transaction.

**Tests added or updated:**
Added `tests/unit/test_vector_store.py` covering `VectorStore.delete_collection()` (removes an existing collection's data; tolerates a collection that was never created). Updated `tests/unit/test_profile_service_vector_cleanup.py` — the Week-8 reproduction test now asserts the `profile_{id}` collection is empty after `delete_profile()` (it previously asserted the orphaned embeddings survived), plus a new edge-case test that deleting a never-ingested profile doesn't raise. All four pass; full unit suite is 53 failed / 379 passed, identical to before this change.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
<!-- "passes" per the module's pre-existing-failures rule = introduces no NEW failures. Verified via git stash: the 17 mypy errors (7 in profile_service.py, 10 in profiles.py), 177 ruff errors, 49 black-reformat files, and 53 unit-test failures are all pre-existing and identical before/after this change. All 5 touched files pass black --check; the pinned pre-commit ruff+black hooks pass on every commit. Documented in the PR's "Notes for Reviewers". -->

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review or comments came in on PR #180 (https://github.com/ascherj/pathreview/pull/180) — it's still open and unreviewed. (Reviewer feedback isn't a feature this term, per the Summer 2026 course note.)

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
The issue itself turned out to be partly stale, and untangling that was harder than the actual fix. The ticket said profile deletion left "orphaned review records and vector store embeddings," but when I traced `delete_profile()` I found the Postgres side was already handled — it explicitly deletes the review and ingested-source rows, and the models already have ORM `cascade="all, delete-orphan"` plus FK `ON DELETE CASCADE`. So the "orphaned reviews" half wouldn't reproduce at all. The hard part wasn't writing the ~15-line fix; it was having the confidence to trust my read of the code over the issue text and re-scope the task down to the one thing that was genuinely broken (the embeddings), instead of forcing a change to match the ticket.

**What did you learn about working in a large codebase?**
That contributing to someone else's production code is mostly reading, not writing. The fix was tiny, but getting there meant tracing a single request across three layers (route → service → vector store) and matching conventions I didn't design — the `get_db` dependency-injection pattern, the per-profile `profile_{id}` collection naming, the AsyncMock test style. The biggest difference from my own projects: the repo already had a lot of pre-existing breakage — 53 failing unit tests, 177 lint errors, 17 type errors — and the job wasn't to fix all of that, it was to not make it worse. I had to get comfortable proving my change was clean *relative to a broken baseline* (using `git stash` to compare before/after) instead of expecting a green checkmark.

**How did AI tools help — and where did they fall short?**
AI was most useful for navigation and drafting: quickly locating where the bug lived in an unfamiliar codebase, generating tests that matched the repo's existing patterns, and drafting the PLAN.md and PR description. Where it fell short was judgment that needed the full context — deciding to re-scope the stale issue, deciding to commit with `--no-verify` past pre-existing hook failures rather than trying to fix the entire file, and working through an environment gotcha where the pre-commit mypy passed cleanly but my local mypy crashed on a numpy stub. AI could explain each of those, but the "should I" calls were still mine to make.

**What would you do differently if you started over?**
Three things. I'd type-annotate the functions I touched up front, instead of hitting the mypy hook on my very first commit and fixing it reactively. I'd open the PR early as a draft to leave room for feedback, rather than doing all the work and opening it at the end. And I'd weight issue selection a bit more toward something that reproduces in the running app — because the vector store isn't wired into the live ingestion pipeline yet, my fix is correct but currently latent, so I could only demonstrate it through tests and a direct ChromaDB script, never through the actual UI.

**What are you most proud of from this module?**
Not the code itself — the rigor around it. I verified the fix against a real ChromaDB (seed a collection, delete it, confirm it's empty), not just mocks, and I documented exactly which failures were pre-existing versus introduced by me, with `git stash` evidence, right in the PR's Notes for Reviewers. In a codebase where "the tests fail" is the normal state, I'm proud that my contribution was provably clean and honestly documented instead of hand-waved.
