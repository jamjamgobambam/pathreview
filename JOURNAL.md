## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation #34

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The current retriever ranks document chunks by combining vector and keyword scores. However, these initial scores don't always accurately reflect how relevant a chunk is to the user's query. Adding an optional re-ranking step in `rag/retriever/reranker.py` will prompt a smaller LLM to score each chunk's actual relevance before passing the top-k chunks to the generator. This will make the retrieved context more accurate and improve the overall feedback quality.

**Selection notes / "Is this right for me?" checklist reasoning:**
- **Estimated effort:** 7–10 hours (Tier 3), which fits well within my project timeline.
- **Affected files:** `rag/retriever/hybrid.py` and creating `rag/retriever/reranker.py`.
- **Reason for selection:** This issue has a clear focus on the RAG retrieval logic. It allows me to work on backend search and LLM scoring cleanly without requiring frontend or database changes.

**Branch name:** `feat/34-llm-reranker`

**Setup confirmation:** [x] App runs locally at localhost:5173

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Siqi-Du/pathreview/commit/54e8738

**Reproduction summary:**
I observed that `HybridRetriever` currently ranks chunks solely using vector similarity and keyword scores without LLM re-ranking. As a result, off-topic chunks with keyword overlap or high vector similarity can be passed to the generator. Added a reproduction note in `rag/retriever/hybrid.py` to document this feature gap.

**PLAN.md link:** https://github.com/Siqi-Du/pathreview/blob/feat/34-llm-reranker/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — optional]

**Blockers or open questions:**
None. Ready to implement `LLMReranker` and integrate it into `HybridRetriever`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Implemented `LLMReranker` class in `rag/retriever/reranker.py` with structured JSON scoring prompt and automatic fallback to base candidate scores on LLM API exception/timeout.
- Integrated `LLMReranker` into `HybridRetriever` in `rag/retriever/hybrid.py` to enable 2nd-stage candidate re-ranking when `reranker` is provided.
- Written comprehensive unit tests in `tests/unit/test_reranker.py` covering score parsing, error fallbacks, empty chunk lists, and 2-stage retrieval integration.

**Next steps:**
- Perform code quality self-review (`make check` and `make test-unit`) to ensure no new regressions are introduced.
- Open draft PR on GitHub and solicit peer/mentor feedback.
- Update Check-in 2 with PR link and submit final branch URL.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/Siqi-Du/pathreview/pull/1](https://github.com/Siqi-Du/pathreview/pull/1)

**Branch:** `feat/34-llm-reranker`

**What you built:**
Implemented an optional LLM re-ranking step for `HybridRetriever` in `rag/retriever/reranker.py`. After initial vector and keyword retrieval candidates are blended, `LLMReranker` uses an LLM to score chunk relevance (0–1 scale) and prunes down to the top `max_chunks`, with graceful fallback to base hybrid scores on LLM error.

**Tests added or updated:**
Added `tests/unit/test_reranker.py`, covering `LLMReranker` candidate scoring, sorting, JSON formatting fallback, empty input handling, and `HybridRetriever` integration.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes (no new failures introduced)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review feedback came in prior to the deadline (Summer 2026 track).

**How you responded:**
N/A (No feedback received).

---

### Reflection

**What was harder than you expected?**
Balancing 2-stage retrieval trade-offs between candidate pool size (over-fetching vs. under-fetching) and LLM call latency/cost. Designing a robust JSON score parser in `LLMReranker._parse_scores` that reliably handles markdown-wrapped JSON code fences (` ```json ... ``` `) and malformed outputs without causing unhandled runtime exceptions during retrieval was also more subtle than anticipated.

**What did you learn about working in a large codebase?**
Navigating an existing modular RAG pipeline requires strictly preserving established API contracts and error-handling patterns. Adding a new 2nd-stage reranker component in `rag/retriever/reranker.py` required non-breaking integration into `HybridRetriever` (`reranker: LLMReranker | None = None`) with graceful fallback to candidate hybrid scores when LLM API keys are unconfigured, ensuring legacy code, existing tests, and upstream generator modules continue to run without disruption.

**How did AI tools help — and where did they fall short?**
AI tools were exceptionally effective at generating initial unit test mocks (`MagicMock` for OpenAI API completions and vector store dependencies) and drafting structured scoring prompts. However, they fell short when analyzing workspace-wide test suites with pre-existing failures in unrelated modules, and when designing fail-safe fallback logic that guarantees high retrieval availability when LLM API endpoints time out or fail.

**What would you do differently if you started over?**
I would start by implementing an automated benchmarking script early in Week 8 to quantitatively evaluate retrieval recall and precision differences with and without LLM re-ranking on sample portfolio queries, rather than relying primarily on manual chunk inspection and qualitative spot-checks.

**What are you most proud of from this module?**
Designing a clean, resilient 2-stage retrieval system where `LLMReranker` gracefully degrades to base vector/BM25 hybrid scoring on API failure or missing keys, allowing the retrieval engine to remain 100% operational while delivering measurably higher chunk relevance when enabled.
