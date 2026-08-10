# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/80

**Issue title:** `DELETE /profiles/{profile_id}` doesn't cascade to delete associated reviews and embeddings

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
When a profile is deleted through the `DELETE /profiles/{profile_id}` endpoint, only the profile row itself is removed from the database. The reviews that were generated for that profile, and the vector store embeddings created from its resume/portfolio content, are never cleaned up — they stay behind as orphaned records keyed to a profile ID that no longer exists. This affects `api/routes/profiles.py` (the delete endpoint) and `core/services/profile_service.py` (the deletion logic), and likely also touches the RAG vector store client in `rag/retriever/vector_store.py` since embeddings live outside the relational database. A correct fix deletes (or cascades the deletion of) the associated reviews and embeddings whenever a profile is deleted, so no orphaned data is left querying against a nonexistent profile.

**Branch name:** fix/80-cascade-delete-profile-reviews

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AbdoulayeSedego/pathreview/commit/5327f961da922fd428dfb2644f76f3dc6ed2f007

**Reproduction summary:**
I added an integration test (`tests/integration/test_profile_delete_cascade_repro.py`) that ingests embeddings into a `profile_{id}` ChromaDB collection, runs the deletion path the way `delete_profile` does it today, then asserts the collection is empty. It XFAILs — the embeddings survive, proving the orphaning. Reproducing this also refined my Week 7 understanding: `delete_profile` already deletes the `reviews` and `ingested_sources` rows in Postgres (and the models declare `ondelete="CASCADE"` FKs), so the real gap is purely the vector store — the service never removes the `profile_{id}` collection, and `VectorStore` has no method to delete a whole collection.

**PLAN.md link:** https://github.com/AbdoulayeSedego/pathreview/blob/fix/80-cascade-delete-profile-reviews/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
- Cross-store atomicity: Postgres and ChromaDB can't share a transaction, so I need to decide the delete order and how to handle a partial failure (best-effort + logging vs. compensating retry).
- Which ChromaDB the running app actually writes to — the embedded `PersistentClient` (`.chromadb`) vs. the `vector_db_url` HTTP container — so the fix deletes from the same store ingestion wrote to.
- `_record_ingested_source` in `ingestion/pipeline.py` is currently a logging-only placeholder, so `ingested_sources` rows may not be populated on real data; I'll confirm this doesn't change the fix's scope.

## Week 9 — Solution building & PR submission

*Note: both check-ins below were completed in one working session rather than split Wednesday/Sunday — logging that here for transparency rather than implying a cadence that didn't happen.*

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md's "Plan" section are implemented:
1. Added `VectorStore.delete_collection()` in `rag/retriever/vector_store.py`, catching `chromadb.errors.NotFoundError` specifically (not a bare `except`) so it's a safe no-op when a profile was never ingested.
2. Wired it into `delete_profile` in `core/services/profile_service.py`, called *before* the Postgres deletes — resolves the Week 8 atomicity question: if the vector store throws, nothing in Postgres is touched and the whole request is safely retryable.
3. Converted the Week 8 `xfail` reproduction into a real regression test (renamed `test_profile_delete_cascade_repro.py` → `test_profile_delete_cascade.py`), plus added a cross-profile isolation test and a no-embeddings-profile edge case.
4. Ran `make test-unit`/`make check` before and after, diffed the failure lists — zero new failures.
5. Updated the endpoint/service docstrings to describe the embeddings cascade.

Also resolved the two Week 8 open questions: traced every call site and confirmed nothing in the app currently instantiates `VectorStore` or `IngestionPipeline` anywhere (ingestion is unwired scaffolding), so there's no existing pattern to match — `delete_profile` just constructs `VectorStore()` with its class default, with an optional `vector_store` param for test injection. Verified this for real: brought up a live server + Postgres, registered a user, created a profile, seeded embeddings directly into `.chromadb`, called the real `DELETE /profiles/{id}` endpoint, confirmed `204` → `GET` now `404` → ChromaDB collection gone.

**Next steps:**
Added unit tests for `delete_collection` and for `delete_profile`'s ordering/error-handling/default-vs-injected paths (8 new tests, all passing). Filled out PLAN.md's risk section with how each risk actually resolved. Opening a draft PR and sharing it in the course Slack for peer/mentor feedback before marking it ready for review.

**Blockers:**
None on the implementation itself. Caught and fixed one process mistake worth noting: an early `git add` with a bad pathspec silently staged nothing, so my first "fix" commit only contained the test files, not the actual code change — caught it by diffing my branch against `upstream/main` before opening the PR and seeing the production files weren't in the diff. Fixed with a follow-up commit rather than force-pushing over the already-pushed commit.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/662 (open, marked ready for review)

**Branch:** `fix/80-cascade-delete-profile-reviews`

**What you built:**
`DELETE /profiles/{profile_id}` already cascaded to Postgres (`reviews`, `ingested_sources`) but never touched the vector store, leaving each deleted profile's embeddings orphaned forever in a ChromaDB collection named `profile_{profile_id}`. The fix adds `VectorStore.delete_collection()` and calls it from `delete_profile` before the Postgres deletes, so a vector-store failure aborts cleanly instead of leaving the two stores disagreeing.

**Tests added or updated:**
- `tests/unit/test_vector_store.py` (new) — `delete_collection` removes an existing collection, is a no-op on a missing one, and only touches the named collection.
- `tests/unit/test_profile_service.py` (new) — `delete_profile` calls `delete_collection` with the exact `profile_{id}` name, deletes reviews/sources/profile, aborts before touching Postgres if the vector store fails, and falls back to constructing its own `VectorStore()` when none is injected.
- `tests/integration/test_profile_delete_cascade.py` (renamed from the Week 8 repro, `xfail` removed) — real ChromaDB end-to-end: embeddings gone after delete, a second profile's collection untouched, no-embeddings profile is a safe no-op.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Both against a documented pre-existing baseline, per the Week 9 instructions: `make test-unit` has 53 pre-existing failures unrelated to this change — mostly an `AsyncMock`-attribute-chaining issue under Python 3.14 in `test_review_service.py`, plus unrelated assertion mismatches in `test_skill_extractor.py`/`test_tech_detector.py`/`test_resume_parser.py`/`test_structural_chunker.py`/`test_security.py`. I diffed the full failing-test list before and after my change — identical, plus 8 new passing tests. `make lint`/`make format` have pre-existing repo-wide findings (182→180 and 52→50 respectively, both improved by cleanup in files I touched); `make typecheck` hard-stops repo-wide on a pre-existing numpy/mypy-vs-Python-3.14 incompatibility before reaching any file I changed — confirmed byte-identical output before/after. Full details in the PR description.)*

**Draft PR feedback received from:** none — opened directly for review rather than requesting a Slack pre-review pass, given time constraints.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
Checked PR #662 directly against the GitHub API (`gh pr view --json comments,reviews` and the review-comments endpoint) — zero comments, zero reviews as of this writing. This lines up with the course note that reviewer feedback isn't a live feature this term, so I'm not reading anything into the silence.

**How you responded:**
N/A — nothing to respond to. In lieu of PR feedback, I got real review practice a different way this module: I did an actual line-by-line review of a classmate's PR (#705, issue #151, the bias-detector false-positive fix) at their request. I pulled the real diff instead of trusting the PR description, and empirically verified my concern by running their changed file against constructed inputs rather than reasoning about it abstractly — confirmed 7/7 realistic, non-biased code-review sentences (e.g. "This uses a testing scaffold that lacks proper mocking") got flagged as biased, because their new substring-matching approach had no word-boundary or proximity checks ("old" matches inside "scaffold"; "lack" anywhere in the text combined with "bootcamp" anywhere else, even in an unrelated clause). I also caught a stray, accidental paste that had corrupted `docs/CONTRIBUTING.md`, and a committed video file bloating repo history. Writing that review from the reviewer's seat — and having to back every claim with a reproducible example instead of "I think this might false-positive" — sharpened exactly the skill this section is meant to build, even though it happened outbound instead of inbound.

---

### Reflection

**What was harder than you expected?**
Getting the environment running in Week 7 turned out to be entirely unrelated to the codebase: `make setup` failed because my machine already had another project's Postgres container squatting on port 5433, and I hadn't copied `.env.example` to `.env` yet. Neither of those show up by reading source code — they only show up by actually running the command and reading the real error, which is a habit I had to lean on repeatedly. The second surprise was how much narrower the actual bug was than the issue title suggested. "Doesn't cascade to delete associated reviews and embeddings" reads like the whole delete path is broken, but the Postgres half (reviews, ingested_sources) was already correctly cascaded via `ondelete="CASCADE"` FKs — the endpoint docstring even claimed it. The real gap was specifically the vector store, a completely separate system with no shared transaction with Postgres, which reframed the whole problem from "add cascade logic" to "handle two data stores that can each fail independently." I also hit a genuine process failure I hadn't planned for: an early `git add` with a bad pathspec silently staged nothing, so my first "fix" commit only contained the new tests, not the actual implementation. I only caught it by diffing my branch against `upstream/main` before opening the PR and noticing the production files weren't there.

**What did you learn about working in a large codebase?**
Docstrings and comments describe intent, not necessarily current behavior — the profiles.py docstring said "cascade delete reviews and ingested sources" as if that already covered everything, when the actual gap was elsewhere entirely. I couldn't have found the real bug without reading the actual service code and models, not just the doc comment. I also learned to check whether code is even reachable before deciding how conservative to be about changing it: `VectorStore` and `IngestionPipeline` turned out to have zero call sites anywhere in the running app outside of tests, which meant there was no existing "how do we normally construct a VectorStore" convention to match — I had to make that decision myself and document why, rather than copy a pattern that didn't exist. And establishing a baseline before touching anything (53 pre-existing test failures, 182 pre-existing lint errors, a hard-failing typecheck) mattered more than I expected going in — without it, I couldn't have proven my change introduced zero new failures in a codebase that was already far from green.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the fast, wide tracing work: grepping and reading across a dozen files at once to figure out where collections are named, where `VectorStore` is or isn't instantiated, and why `docker compose up` was actually failing (a port conflict, not a code bug) instead of guessing and trying fixes one at a time. It also helped structure the reproduction test and the PR description so the reasoning was easy for a reviewer to follow. It fell short — or rather, needed me to actively push past a first answer — on judgment calls: deciding to delete the vector-store collection *before* the Postgres rows (so a vector-store failure is safely retryable instead of leaving the two stores disagreeing) was a reliability tradeoff that needed explicit reasoning about failure ordering, not just picking whichever order the AI wrote first. The clearest case was reviewing PR #705: the author's PR description made a specific, verifiable claim ("all 40 test cases passed"), and it was true — but true and correct aren't the same thing. Confirming the fix was actually broken required constructing new adversarial inputs and running the code against them, not just reading the diff and reasoning about whether it looked right. That's the part AI can propose but a human still has to actually go verify.

**What would you do differently if you started over?**
I'd check what's already running locally (`docker ps`, ports in use) before the first `make setup` attempt, given I already had several other projects' containers running on this machine — that would have skipped a failed run entirely. I'd also double-check what `git add` actually staged after every commit rather than trusting the command silently, since that mistake could have shipped an incomplete fix if I hadn't diffed against upstream before opening the PR. And I'd try to get a real Slack peer-review pass before marking the PR ready, instead of opening it directly for review under deadline pressure — I made a deliberate tradeoff there given time constraints, but it's the one part of the process I didn't get to do as designed.

**What are you most proud of from this module?**
Not the fix itself, but the verification behind it. It would have been easy to stop at "the reported symptom is gone" — embeddings get deleted now — and call it done. Instead I traced the issue enough to realize the DB-cascade half was already correct (so I didn't touch what wasn't broken), verified the actual fix end-to-end against a live server with real seeded embeddings rather than trusting unit tests alone, and documented a byte-identical before/after diff of a pre-existing 53-test failure baseline to prove the change introduced nothing new in a codebase that was already far from clean. That same instinct — verify empirically, don't take a description at face value — is what let me catch a real, reproducible false-positive bug in a classmate's PR by actually running their code against inputs their own test suite hadn't considered, rather than just reading their diff and assuming it was fine because the tests were green.
