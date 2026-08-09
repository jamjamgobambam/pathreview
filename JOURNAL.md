## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/27

**Issue title:** Vector store returns stale embeddings after a document is re-ingested

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When a README is edited and re-ingested, the ingestion pipeline adds new embeddings for the updated content but never removes the embeddings from the prior version. Both the old and new chunks end up coexisting in the vector store under the same source, since nothing currently deletes stale entries before or after a re-ingest. As a result, the retriever can return outdated chunks — content that no longer matches the current document — alongside or instead of the up-to-date version. This affects the ingestion pipeline (`ingestion/pipeline.py`) and the vector store layer (`rag/retriever/vector_store.py`), which currently lacks a way to delete existing chunks by source before adding new ones. A successful fix would ensure re-ingesting a source clears its old embeddings first, so only the current version is ever retrievable.

**"Is this right for me?" checklist reasoning:**

*Part 1 — Understanding the issue:* I can explain the problem without re-reading it: re-ingesting a README adds new embeddings but never deletes the old ones, so the vector store accumulates stale chunks and the retriever can surface outdated content. "Done" means re-ingestion clears prior embeddings for that source before adding the new ones, leaving only current content retrievable.

*Part 2 — Tier fit:* This is my first formal contribution to this codebase, which per the checklist would normally point me to Tier 1. I'm choosing Tier 3 anyway because I already work with this exact class of problem professionally as an Analytics Engineer — Slowly Changing Dimensions (SCD Type 2) solve the same underlying issue in a data warehouse context: when a record is updated, the old version must be closed out or removed rather than left alongside the new one, or queries can return stale data. I've built and maintained pipelines that explicitly guard against this. The unfamiliarity the checklist guards against is with this specific codebase, not the underlying concept — I recognize this bug pattern immediately from professional experience, which narrows the real risk to codebase navigation rather than domain knowledge.

*Part 3 — Codebase readiness:* I've read both `ingestion/pipeline.py` and `rag/retriever/vector_store.py` in full, including the specific ingestion function and the vector store's storage/query methods, and can sketch a rough plan for the fix: add a delete-by-source-id method to `vector_store.py`, and call it at the start of the re-ingest flow in `pipeline.py` before new chunks are added.

*Part 4 — Scope and time:* I've checked the issue comments and the ledger's Claims column and confirmed the current claim count and no open blockers. I'm targeting completion well before the Week 9 deadline, with Week 10 held as buffer rather than my actual estimate.

**Branch name:** fix/27-stale-vectordb-embeddings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger`

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Aniruthan-0709/pathreview/commit/fffceaa

**Reproduction summary:**
Added a failing unit test (`tests/unit/test_stale_embeddings_repro.py`) that drives the real `IngestionPipeline` against an in-memory ChromaDB collection. Ingesting a README, then re-ingesting an edited version, leaves both versions' chunks in the store — the edited README gets a new content-hashed `source_id` and its chunks are added without deleting the old ones. Observed: after re-ingesting v2, v1's unique marker text is still retrievable (4 chunks in the store instead of 2), confirming the retriever can return stale content.

**PLAN.md link:** https://github.com/Aniruthan-0709/pathreview/blob/fix/27-stale-vectordb-embeddings/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
- Where should the "current version" hash live — read back from chunk metadata (keeps the fix inside the files the issue names) or implement real `IngestedSource` persistence? Leaning toward metadata for scope.
- Delete/add ordering: a naive "delete old then add new" risks wiping the good version if embedding fails. Deciding whether to delete only after the new chunks embed successfully.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Captured a baseline of pre-existing `make check` / `make test-unit` failures, then implemented the #27 fix in `ingestion/pipeline.py` per PLAN.md — all three sub-tasks: stable `source_id` + `content_hash` in metadata, content-based skip detection, and delete-before-add to clear stale chunks.

**Next steps:**
Finish the regression tests (replace / skip / orphan cases), confirm no new failures vs baseline, open a draft PR for feedback, then mark ready.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/510

**Branch:** `fix/27-stale-vectordb-embeddings`

**What you built:**
Re-ingesting an edited README now replaces the previous version's chunks instead of leaving them behind. A README is identified by a stable `source_id` with a separate `content_hash`; unchanged content is skipped, and changed content deletes the old chunks (by `source_id`) before storing the new ones, so the retriever only ever sees the current version.

**Tests added or updated:**
`tests/unit/test_stale_embeddings_repro.py` — the Week 8 reproduction, now a passing regression suite: stable-identity, replace-on-edit (the original repro), skip-on-identical, and no-orphans-on-shorter-edit.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(In this codebase "passes" = no new failures: unit 54→53 with only the #27 repro fixed; ruff 182→182, mypy 5→5, black 52→52 — zero new issues.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
Reviewer feedback is not a feature in Summer 2026, and no comments came in on PR #510 ([ascherj/pathreview#510](https://github.com/ascherj/pathreview/pull/510)) by the end of the week.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Finding the *real* root cause. My first instinct from the plan — "call `delete_by_source_id` before adding the new chunks" — turned out to be wrong: the `source_id` embedded the content hash, so it changed on every edit and a delete keyed on it would have matched nothing. I only saw this by tracing the full ingest flow line by line. Two more surprises: the repo had two disconnected "worlds" (`IngestionPipeline` writing to a raw ChromaDB collection vs. an unused `VectorStore` wrapper), and the running app didn't even wire ingestion into the vector store, so I couldn't reproduce the bug in the app — I had to reproduce it at the unit level instead. Locating where the bug actually lived, versus where the issue text pointed, was the hard part.

**What did you learn about working in a large codebase?**
Navigating this RAG project end-to-end (ingestion → chunking → embedding → vector-store retrieval, plus the agent/tool-call and safety/guardrail layers) taught me how a production RAG system actually fits together — very different from a toy project. On contributing to someone else's code specifically: scope discipline matters more than cleverness. I deliberately fixed only the README path and left the resume/repo paths alone, matched the existing test style and formatting conventions instead of imposing my own, and — crucially — learned to work in a codebase that's already failing its own checks. Rather than "fix everything," I captured a baseline (54 failing unit tests, 182 ruff, 5 mypy) before touching anything and proved my change added zero new failures. Minimal, reviewable diffs and reading before writing were the recurring themes.

**How did AI tools help — and where did they fall short?**
AI was strongest at fast codebase navigation — tracing how metadata flows through the pipeline, mapping which files mattered, and drafting the reproduction test, regression cases, and PR description. Where it fell short: its first reproduction test had a real bug (a ChromaDB in-memory client name collision) that only surfaced when I ran it and watched it fail — a reminder to verify AI output by executing it, not trusting it. More importantly, the judgment calls were mine: choosing SCD Type 1 (overwrite) over Type 2 (keep history), accepting the delete-before-add atomicity tradeoff, and keeping scope to README-only. AI also can't verify behavior in the real running app, and would have happily committed straight through the pre-existing failures if I hadn't decided to baseline first. I chose to write the test myself so I actually understood the reproduction instead of pasting generated code.

**What would you do differently if you started over?**
I'd verify the runtime wiring earlier — I initially assumed `IngestionPipeline` was live in the app and lost a little time before discovering it wasn't. I'd also lock down the open design decisions (where the content hash lives, how to handle atomicity) before writing code instead of resolving them mid-implementation. Issue selection I'd keep the same — picking a stale-data problem that mirrors the SCD Type 2 work I already knew from analytics engineering was a good fit.

**What are you most proud of?**
The rigor of the process, not just the fix: a failing test that proved the bug was real, a documented before/after baseline showing zero new failures, and an honest PR description that left the "tests pass" boxes unchecked and openly documented both the pre-existing failures and the atomicity limitation. It would have been easier to overclaim — I'm proud that the contribution is trustworthy.
