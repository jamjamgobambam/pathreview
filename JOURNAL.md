# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/27

**Issue title:** Vector store returns stale embeddings after a document is re-ingested

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
PathReview ingests a user's documents (README, resume, repo files), splits them
into chunks, embeds them, and stores the vectors in a ChromaDB collection that the
RAG retriever later searches. The bug is in how the system handles re-ingestion.
When embeddings are written, the ingestion pipeline makes a raw `vector_db.add(...)`
call, which appends rather than replaces. There is a `VectorStore.delete_by_source_id()`
method meant to clean up a document's old vectors, but nothing in the codebase ever
calls it. This is made worse by how chunk IDs are assigned: each chunk's `source_id`
comes from a content hash, so editing a document and re-ingesting it produces a
brand-new `source_id`. The old vectors are never overwritten, and they linger in the
collection as stale results that retrieval can still return and feed into the
generated review.

A correct fix wires cleanup into the re-ingestion path, either deleting a source's
prior vectors before adding the new ones or upserting with stable IDs, so that after
a document is re-ingested the store holds exactly one current set of chunks. The
change touches the RAG retriever (`rag/retriever/vector_store.py`) and the ingestion
pipeline (`ingestion/pipeline.py`, `ingestion/embeddings/batch_processor.py`), which
is what makes this a whole-pipeline (Tier 3) change rather than a localized fix.

**Selection notes — "Is this right for me?" checklist:**
- Tier 3 fit: I work as a junior full-stack engineer and have contributed to large
  codebases, so per the checklist ("if I've contributed to large codebases before,
  Tier 2 or 3 is fair game") Tier 3 is appropriate. This issue requires
  understanding how ingestion, embedding storage, and RAG retrieval interact —
  multiple modules and the AI pipeline — which matches the Tier 3 definition.
- I can explain the problem in my own words without re-reading the issue (above).
- I located the exact code: `delete_by_source_id` in
  `rag/retriever/vector_store.py` (and confirmed via grep that it is never called),
  the append-only `vector_db.add(...)` in
  `ingestion/embeddings/batch_processor.py`, and the content-hash `source_id` built
  in `ingestion/pipeline.py`. I read each end to end.
- Concrete before/after: before, re-ingesting an edited document leaves its old
  vectors in the store, so stale chunks can be retrieved and fed into the review;
  after, only the current set of chunks for that source remains.
- Test plan exists: `tests/unit/test_batch_processor.py` already mocks a
  `vector_db`; I can extend it (or add `tests/unit/test_vector_store.py`) to ingest
  content, re-ingest an edited version, and assert the old chunk IDs are gone —
  deterministic with an in-memory fake.
- Scope/time: estimated ~6–9 hours across Weeks 8–9, achievable before the
  deadline. Not claimed (0 comments, not in the ledger), no blockers or
  dependencies.

**Branch name:** fix/27-stale-embeddings-reingest

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/aishani-muk/pathreview/commit/87be3beba1608072dbccfd66c0d8986233f85bea

**Reproduction summary:**
Added a deterministic unit test (`tests/unit/test_reingest_stale_embeddings.py`) that
drives `IngestionPipeline.ingest_readme` twice — once with an original README and once
with an edited version — against an in-memory fake vector collection, then asserts the
first version's vectors are gone. Run with `--runxfail` it fails: the store still holds
the original version's `source_id` (`readme_profile-1_repoX_50e5629b…`) alongside the
new one, so two content versions coexist instead of one. This confirms stale embeddings
from the prior version survive re-ingestion. The test is committed as `xfail(strict=True)`
so the suite stays green until the Week 9 fix removes the marker.

**PLAN.md link:** https://github.com/aishani-muk/pathreview/blob/fix/27-stale-embeddings-reingest/PLAN.md

**Walkthrough video (recommended):** (optional — not recorded)

**Blockers or open questions:**
Need to confirm in `core/services/review_service.py` whether the pipeline is handed a
raw ChromaDB collection or the `VectorStore` wrapper, since that determines where the
delete-before-store call lives. Also deciding how to handle legacy vectors written
before the fix (no `base_source_id` field to filter on).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented PLAN.md sub-tasks 1–4: derived a stable, unhashed `base_source_id` in
`ingest_resume`/`ingest_readme`/`ingest_repo_metadata` (chunkers preserve it, the batch
processor persists it) and added a `_purge_stale_vectors()` helper. Resolved the Week 8 open
question: the real ingestion path receives a raw ChromaDB collection and
`review_service._run_ingestion_pipeline` is a stub, so the fix lives entirely in `pipeline.py`.
The Week 8 reproduction test now passes with the `xfail` removed.

**Next steps:**
Add edge-case tests (identical re-ingest, first-time no-op, per-repo isolation, multi-chunk),
compare `make test-unit`/`make check` against the pre-existing baseline, fill the PR template,
and open the PR.

**Blockers:**
The seeded codebase has documented pre-existing failures unrelated to #27 (53 failing unit
tests, 182 ruff errors, mypy erroring on a NumPy-2/Python-3.13 stub). Confirmed my change adds
none; documenting per the pre-existing-failures guidance.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/433

**Branch:** fix/27-stale-embeddings-reingest

**What you built:**
Made document re-ingestion idempotent: the pipeline derives a stable `base_source_id`, upserts
the new chunks, and then deletes any older vectors for that source (`source_id != current`), so
editing and re-ingesting a document no longer leaves stale embeddings for retrieval to surface.
Storing before deleting means a mid-store failure can't wipe the old version.

**Tests added or updated:**
`tests/unit/test_reingest_stale_embeddings.py` — un-xfailed the reproduction test and added
seven more (8 total): edited re-ingest purges the old version for the readme, resume, and repo
paths; identical re-ingest keeps a single version; first-time purge is a safe no-op; per-repo
scoping leaves another repo's vectors intact; a multi-chunk case removes every old chunk; and a
store-failure case confirms the previous version survives when embedding the new one fails.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(pre-existing failures documented in the PR; my change introduces no new failures)

**Draft PR feedback received from:** none (peer review optional this session)

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No, still awaiting review

**Summary of feedback:**
No reviewer feedback came in. Peer and maintainer review is not part of the Summer 2026 session. I
opened the PR as ready for review and it stays open pending any response.

**How you responded:**
N/A. There was no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
The fix was about forty lines, but trusting the codebase was the hard part. The seeded repo did not
match its own issue tracker. Two issues I first considered (#76 and #77) were already fixed in the
code, and the vector store had a `delete_by_source_id()` method that looked like the answer until I
grepped and found nothing ever called it. The environment also fought me: the `docker` CLI was
missing from my PATH, the ChromaDB container crashed on a NumPy 2 error, and `make test-unit`
already had 53 failing tests before I changed anything. Telling my bug apart from the repo's
pre-existing noise took more discipline than the fix did.

**What did you learn about working in a large codebase?**
In my own projects I hold the whole thing in my head. Here I had to trace one call path, from
`ingest_readme` into `batch_processor.process` into `_store_embedding` into the raw `vector_db`
write, across four files before I understood where the bug lived. The clearest lesson was that a
function's name can mislead: `review_service._run_ingestion_pipeline` looked like the ingestion
entry point but was a stub, and the real path was only exercised by tests. Fitting in mattered too.
I used Conventional Commits, matched the mock-based test style already in `test_batch_processor.py`,
and deliberately did not reformat 52 files of pre-existing style drift just because the linter
wanted to.

**How did AI tools help, and where did they fall short?**
AI was most useful for reconnaissance and bookkeeping at scale. It mapped the ingestion and RAG
modules, confirmed which chunkers preserved metadata so a new `base_source_id` key would propagate,
baselined the 53 failing tests and 182 ruff errors so I could prove my change added none, and
scaffolded the in-memory `FakeCollection` test double. It also fell short. It first framed the issue
in the tracker's words until I ran the code and saw the real state, it could not run a real
integration test because the ChromaDB container was broken, and when it suggested a
delete-before-store ordering I had to reject it because that version could wipe a user's data on a
failed write. The judgment calls were mine.

**What would you do differently if you started over?**
I would confirm the issue actually reproduces in the real code before writing my Week 7 problem
summary, because I nearly committed to issues that were already fixed. I would also get ChromaDB
running early in Week 8 by swapping the pinned image past the NumPy 2 break, so I could ship a real
integration test instead of only a fake-backed unit test. And I would distrust my first green
solution sooner, since my initial fix passed every test but still had a data-loss flaw.

**What are you most proud of from this module?**
Catching the atomicity flaw in my own solution. My delete-before-store version worked and the suite
was green, but I realized a failed embedding write would delete a user's existing vectors and store
nothing in their place, which is worse than the original bug. I reordered it to upsert the new
chunks first and then delete only the stale ones, and added
`test_store_failure_preserves_previous_version` to lock that behavior in. The habit I am keeping is
that passing tests and being robust are not the same thing.
