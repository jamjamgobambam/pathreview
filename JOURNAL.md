## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/24]

**Issue title:** [Hybrid retriever over-weights keyword results when query contains technology names #24]

**Tier:** [Tier 2 ]

**Problem summary:**
[ if BM25 score is high from common keywords while its vector score is low, that big BM25 half can still push the chunk's final score high enough to rank it near the top. This will affect the final score leading to a wrong context retrieval because BM25 itself has 50% wait on the entire output or final score.

A successfull fix is to rebalance that 50/50 to trust vector similarity more, or adjust weights based on the query so keyword only matches can't ride into the top results.]

**Affected parts of the codebase:**

- `rag/retriever/hybrid.py` — `HybridRetriever.retrieve()`. This is the core of the issue: the blend happens at `blended_score = self.vector_weight * vector_score + self.keyword_weight * keyword_score`. The weights are hardcoded constructor defaults — this is the single place the weights live and where any rebalancing/adaptive-weighting fix goes. **Fix applied:** rebalanced from 50/50 to **`vector_weight=0.8, keyword_weight=0.2`** so vector (meaning) similarity dominates and keyword-only matches on shared tech terms can't ride into the top results.
- `rag/retriever/keyword_search.py` — `KeywordSearcher.search()`. Produces the BM25 keyword score (via `rank_bm25.BM25Okapi`) that is over-rewarded for common tech terms. Tokenization is a naive lowercase whitespace split, which offers no protection against shared vocabulary across documents.
- `rag/retriever/vector_store.py` — `VectorStore.query()`. Produces the vector similarity score (`similarity = 1 / (1 + distance)` over ChromaDB distances) — the "meaning" half that gets drowned out.
- `rag/generator/review_generator.py` — `_format_context()` / `generate_section()`. The downstream consumer: it assembles the top retrieved chunks into the LLM prompt, so wrong chunks here become wrong context for the model's answer.
- Config: there is **no** weight constant in `core/config.py` or elsewhere — the weights only exist as the defaults in `hybrid.py:14`. Making them configurable is part of a clean fix.
- Caveat: `core/services/review_service.py` (`_run_rag_retrieval_generation()`) is still a placeholder and does not yet call `HybridRetriever`, so the scoring path isn't wired into the live request flow yet.

**Issue Fit and Selection Reasoning:**

- **Right tier / scope.** As a Tier 2 issue it's substantial enough to be meaningful but bounded — the root cause lives in a single function (`HybridRetriever.retrieve()`), so the change surface is small and easy to reason about.
- **Clear, single root cause.** The problem traces cleanly to one thing: the fixed blend weight giving BM25 too much say. There's no ambiguity about *where* to fix it, which lowers the risk of scope creep.
- **Well-understood behavior.** The failure mode (shared tech terms like "React"/"Python" inflating keyword scores and pulling in wrong-document chunks) is concrete and reproducible, making it straightforward to reason about before and after the change.
- **High-impact for low effort.** Retrieval quality directly determines the context the LLM answers from, so a small weight change has an outsized effect on end output quality — a good return on a modest fix.
- **Testable in isolation.** Because scoring is a pure blend of two normalized scores, the fix can be validated at the retriever level without needing the full generation pipeline (which is still a placeholder in `review_service.py`).
- **Room to extend.** The issue also opens a natural follow-up path (making weights configurable, or query-adaptive weighting), so it's a clean foundation rather than a dead-end patch.

**Branch name:** [fix/24-hybrid-scoring-weight-tuning]

**Setup confirmation:** [App runs locally at localhost:5173]

**Cohort ledger:** [Issue added to cohort ledger]

**Issue 24 Reproduction:**

*Goal: show the issue is real and pin down exactly where it lives (the score blend in `rag/retriever/hybrid.py`).*

**Where it lives:** `rag/retriever/hybrid.py` — `HybridRetriever.retrieve()`, the blend at
`blended_score = self.vector_weight * vector_score + self.keyword_weight * keyword_score`.

**Repro script:** `scripts/repro_issue_24.py`. It exercises the *real* `retrieve()` method with lightweight fakes for the vector store and keyword searcher, so no ChromaDB or embeddings are needed — the only thing under test is the scoring blend.

**Steps:**

1. From the repo root, run: `.venv/bin/python scripts/repro_issue_24.py`
2. The script sets up one query, `"React"`, and two chunks:
   - `resume-1` (**correct** doc) — high vector similarity (0.85), low BM25 (3.0): mentions React once, in context.
   - `readme-1` (**wrong** doc) — low vector similarity (0.50), high BM25 (9.0): keyword-stuffed with "react".
3. It runs the blend twice — once at the issue's **50/50** weights, once at the proposed **0.8/0.2** fix — and prints the ranking each time.

**Observed output:**

```
weights = vector 0.5 / keyword 0.5
  #1  readme-1  doc=readme  final=0.794  (vec=0.588 kw=1.000)
  #2  resume-1  doc=resume  final=0.667  (vec=1.000 kw=0.333)
  => top result: readme-1 — WRONG doc on top (bug)

weights = vector 0.8 / keyword 0.2
  #1  resume-1  doc=resume  final=0.867  (vec=1.000 kw=0.333)
  #2  readme-1  doc=readme  final=0.671  (vec=0.588 kw=1.000)
  => top result: resume-1 — correct doc on top
```

**What this proves:** at 50/50, the README chunk wins purely on its BM25 keyword score (`kw=1.000`) despite the resume chunk being the better semantic match (`vec=1.000`) — exactly the wrong-document retrieval the issue describes. Shifting weight toward vector similarity (0.8/0.2) reverses the ranking, confirming both the root cause and the fix location.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/guiradoul/pathreview/commit/1733d798c9f0539ec4fc9ed5ce948b9e1d3f6e02]

**Reproduction summary:**
I drove the real `HybridRetriever.retrieve()` blend (via `scripts/repro_issue_24.py`, using lightweight fakes so only the scoring step is under test) with the query "React" against two chunks — a semantically-relevant resume chunk and a keyword-stuffed but irrelevant README chunk. At the issue's 50/50 weighting the wrong README chunk ranked #1 (final 0.794 vs 0.667) purely on its BM25 score, confirming the bug lives in the fixed-weight blend in `rag/retriever/hybrid.py`.

**PLAN.md link:** [https://github.com/guiradoul/pathreview/blob/fix/24-hybrid-scoring-weight-tuning/PLAN.md]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[I have already implemented the fix and was working on the unit test]

**Next steps:**
[I was working on the unit test for the rest of the week]

**Blockers:**
[]

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/184]

**Branch:** [`fix/24-hybrid-scoring-weight-tuning`]

**What you built:**
Rebalanced the hybrid retriever's score blend in `rag/retriever/hybrid.py` from an equal weighting to `vector_weight=0.8 / keyword_weight=0.2`, so `HybridRetriever.retrieve()` weights semantic (vector) similarity more heavily than the BM25 keyword score. This stops keyword-only matches on shared technology names (e.g. "React", "Python") from riding wrong-document chunks to the top of the results — and therefore out of the context handed to the LLM. Also added `tests/unit/test_hybrid_retriever.py` to lock in the corrected ranking and guard against a regression back to the 50/50 behavior.

**Tests added or updated:**
Added `tests/unit/test_hybrid_retriever.py` (new — there was no existing coverage for `HybridRetriever`). It drives the real `retrieve()` blend with lightweight fakes for the vector store and keyword searcher, so only the scoring step is under test. The 8 tests cover:

- **The fix** — at the tuned 0.8/0.2 weights the semantically-relevant chunk ranks #1.
- **Regression guard** — at 50/50 the keyword-stuffed wrong-document chunk wins, locking in the reproduced bug so a revert to equal weights fails CI.
- **Blend math** — the blended score equals `weight·normalized-vector + weight·normalized-keyword`.
- **Weight edge cases** — pure-vector (keyword weight 0) and pure-keyword (vector weight 0) modes.
- **Robustness** — empty vector/keyword results return `[]` with no divide-by-zero, a chunk present in only one retriever scores 0.0 on the other side, and the `min_score` threshold filters low-blend chunks.

All 8 pass (`.venv/bin/pytest tests/unit/test_hybrid_retriever.py`).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** ["none"]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
[no review came in.]

**How you responded:**
[ ]

---

### Reflection

**What was harder than you expected?**
[Another Person was working on the same issue. That fix was merged when I was in the middle of implementing my fix with a different solution. I have made a comment in my PR proposing my fix as 0.8/0.2 is a defensible, safe-margin choice.]

**What did you learn about working in a large codebase?**
[For someone else's production code there are rules to follow and code review process is involved. For 
my own project I set all the rules. There is no PR review process in personel project.]

**How did AI tools help — and where did they fall short?**
[AI assistance were most useful when it comes to understanding the codebase and implementing the actual fix. I needed to discuss and find a convincing answer for the reviewer to accept my proposed fix.]

**What would you do differently if you started over?**
[When it comes to the issue selection I would make sure none is working or will be working on my selected issue.]

**What are you most proud of from this module?**
[This module simulates and end to end process of fixing and issue in a production codebase and I was able to completed.]