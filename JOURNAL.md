## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/80

**Issue title:** DELETE /profiles/{profile_id} doesn't cascade to delete associated reviews and embeddings


**Tier:** [ ] Tier 1  [✅] Tier 2  [ ] Tier 3
I selected a Tier 2 issue because I could understand what part of the app was affected and I wanted to challenge myself to pick a Tier 2 issue even though I've never made an open source contribution before.

**Problem summary:**
The issue lies with the fact that when a user's profile is deleted from the database, the vector store embeddings and review records related to that profile aren't removed. A successful fix would get rid of all associated information related to the profile that needs to be deleted from the database and the vector store database. The part of the codebase the issue affects is the ChromaDB vector store deletion path in `profile_service.py`.

**Branch name:** fix/80-profile-cascade-deletion

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproducing issue #80:** 
- Ran the app, created a profile, added sources, and then tried deleting a profile after which I queried Postgres and all ingestions and reviews related to the profile were deleted 
- Went through `delete_profile` in `profile_service.py` and noticed there's no import for ChromaDB, only ingested sources, reviews, and the profile itself are deleted from Postgres, leaving information still in the vector database
- I then went to the retriever folder and investigated `vector_store.py` and noticed that there was a method to delete individual sources based on their id, but no method to delete a whole profile collection (`profile_{profile_id}`) which is why there were orphaned embeddings

**Reproduction commit link:** https://github.com/aks778/pathreview/commit/8d9310f80a07b7170b5a6dd8fe5555634054d68d

**Reproduction summary:**
I reproduced the issue by creating a profile, then deleting it, which I noticed correctly got rid of the reviews and sources from Postgres, but after looking into the issue further I saw the `delete_profile` method doesn't access ChromaDB. And so the profile's embeddings remain orphaned because there's no way for them to be deleted.


**PLAN.md link:** https://github.com/aks778/pathreview/blob/fix/80-profile-cascade-deletion/PLAN.md

**Blockers or open questions:** None


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All three PLAN.md sub-tasks are done. I added a `delete_collection(collection_name)` method to `vector_store.py` that deletes a profile's whole ChromaDB collection and catches `NotFoundError` so deleting a profile with no embeddings is safe. I then wired it into `delete_profile` in `profile_service.py` so the `profile_{profile_id}` collection is deleted as part of the cascade (before the Postgres commit, so a failure rolls back rather than keeping orphaned data). I also added unit tests in `tests/unit/test_profile_delete_service.py` covering the happy path (embeddings deleted) and the not-found path (returns `False`, never touches ChromaDB).

**Next steps:**
I will open a draft PR and request peer feedback, and then mark the PR ready for review once I've received feedback. 

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/539

**Branch:** `fix/80-profile-cascade-deletion`

**What you built:**
A cascade so that deleting a profile also removes its embeddings from ChromaDB. `delete_profile` now builds the `profile_{profile_id}` collection name and calls a new `VectorStore.delete_collection` method, which deletes the whole collection.

**Tests added or updated:**
Added `tests/unit/test_profile_delete_service.py` with 2 unit tests. One confirms the correct ChromaDB collection is deleted when the profile exists, and one confirms a missing profile returns `False` without opening a ChromaDB connection.

**Self-review confirmation:** [✅] make check passes  [✅] make test-unit passes

**Draft PR feedback received from:** None


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [✅] No — still awaiting review

**Summary of feedback:**
No review has come in yet.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
Getting the commit through was harder than the actual fix — the pre-commit hooks kept failing on pre-existing mypy and ruff issues in files I'd barely touched, so I had to work out what was mine versus what was already broken.

**What did you learn about working in a large codebase?**
I spent a lot of time tracing how `delete_profile`, `VectorStore`, and ChromaDB actually connect. Since it was a large codebase, it took some time for me to orient myself.

**How did AI tools help — and where did they fall short?**
AI was great at explaining errors but it couldn't decide things like which ChromaDB backend the app really uses or whether the pre-existing failures were my responsibility.

**What would you do differently if you started over?**
I would spend more time in the planning phase and understand the issue better before writing any code, because not fully grasping the issue slowed me down during the implementation phase.

**What are you most proud of from this module?**
I'm most proud of opening my first open source PR. After noting back in Week 7 that I'd never contributed to open source before, actually submitting a real PR t to someone else's project was something that made me proud of myself.
