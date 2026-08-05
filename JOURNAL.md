## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
PathReview's RAG pipeline currently ranks retrieved document chunks using a hybrid of vector similarity and BM25 keyword scores. While this approach is fast, it treats all high-scoring chunks equally without understanding whether each chunk actually answers the user's query. The issue proposes adding an optional re-ranking pass where a smaller LLM scores each retrieved chunk's relevance to the query before the top-k chunks are forwarded to the generator. The fix lives in `rag/retriever/`, adding a new `reranker.py` module and wiring it into `hybrid.py`. A successful implementation would improve answer quality on queries where the initial retrieval returns plausible but off-topic chunks.

**Is this right for me? — checklist reasoning:**
- The change is scoped to `rag/retriever/` with a clear interface boundary (existing `hybrid.py` retriever), so I can understand the full blast radius without reading the entire codebase.
- The new `reranker.py` will follow the same pattern as existing tools/parsers in the project, making the structure predictable.
- The LLM call is optional (re-ranking is a pass-through if disabled), so I can stub it and get tests passing before wiring up a real model.
- Estimated effort is 7–10 hours, which fits the module timeline.

**Branch name:** feat/34-llm-reranker

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/TianxinS/pathreview/commit/c8318c7

**Reproduction summary:**
Added `tests/unit/test_reranker.py` with 6 failing tests that document the expected interface for `LLMReranker`. All 6 fail because `rag/retriever/reranker.py` does not exist and `HybridRetriever.__init__` has no `reranker` parameter — confirming the feature gap is real and precisely located.

**PLAN.md link:** https://github.com/TianxinS/pathreview/blob/feat/34-llm-reranker/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Need to confirm whether the project has a shared LLM client factory in `agent/orchestrator.py` that `LLMReranker` should reuse, or whether it should accept a raw `openai.OpenAI` client like `ReviewGenerator` does.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from PLAN.md are complete. `LLMReranker` is implemented in `rag/retriever/reranker.py` with a `rerank()` method that prompts a Groq-hosted LLM to score each chunk 0.0–1.0 and returns them sorted descending. `build_reranker()` factory wires it into `HybridRetriever` via the optional `reranker` parameter added to `hybrid.py`. All 9 unit tests in `tests/unit/test_reranker.py` pass.

**Next steps:**
Finalize the PR description, mark as ready for review, and update JOURNAL.md with Check-in 2.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/860

**Branch:** `feat/34-llm-reranker`

**What you built:**
Added `LLMReranker` in `rag/retriever/reranker.py` that scores all retrieved chunks in a single Groq LLM call (one prompt with a numbered list, JSON array response) and re-sorts results by relevance before the final slice. Scoring uses `temperature=0` for determinism and falls back to the original blended score per chunk if the LLM response is missing, unparseable, or out of range. A `build_reranker()` factory returns `None` when `GROQ_API_KEY` is unset, making the feature fully opt-in. `HybridRetriever` in `hybrid.py` was updated to accept and call the optional reranker after blending vector and BM25 scores.

**Tests added or updated:**
`tests/unit/test_reranker.py` — 21 tests across three classes: `TestLLMReranker` covers module existence, return type, `rerank_score` field, empty-input short-circuit, descending sort, single API call per rerank (batch efficiency), `temperature=0` enforcement, and LLM failure fallback; `TestParseScores` covers valid JSON array, out-of-range values falling back, non-JSON responses, wrong score count, and arrays embedded in surrounding text; `TestBuildReranker` covers the factory returning `None` without a key, returning an `LLMReranker` with one set, and using the configured Groq model.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Note: `make check` has pre-existing ruff violations in `agent/`, `api/`, `core/`, and `ingestion/` unrelated to this PR — scoped run on changed files passes cleanly. `make test-unit` has 53 pre-existing failures in unrelated test files. My changes introduce no new failures in either command.

**Draft PR feedback received from:** peer reviewer (GitHub PR comment) — feedback covered three code issues: (1) `_parse_score` regex grabbing the wrong number when the response contains a preamble (e.g. "Chunk 3 scores 0.4" → 1.0), fixed by switching to JSON array parsing with out-of-range fallback; (2) one API call per chunk causing unnecessary sequential round trips, fixed by batching all chunks into a single prompt; (3) missing `temperature=0` causing non-deterministic scores, fixed by adding it to the API call. Reviewer also noted a presentation nit about the checklist boxes not matching the pre-existing failure note in the summary, addressed in the note above.
