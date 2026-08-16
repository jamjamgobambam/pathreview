## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/24]

**Issue title:** Hybrid retriever over-weights keyword results when query contains technology names

**Tier:** [ ] Tier 1  [✓] Tier 2  [ ] Tier 3

**Problem summary:**
The hybrid retriever currently combines vector similarity and BM25 keyword scores using fixed equal weights. When a query includes common technology names such as Python or React, keyword matches can receive too much importance and return chunks from the wrong document. This issue affects the scoring logic in rag/retriever/hybrid.py. A successful fix should improve the weighting strategy so that relevant semantic matches are ranked above unrelated chunks that only share technology keywords.


**Branch name:** [fix/24-hybrid-retriever-keyword-weighting]

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/GarabKDorji/pathreview/commit/141b3e433788faa8f0b9371a66f1c3ca4a49cecb)

**Reproduction summary:**
I reproduced the hybrid-retriever ranking issue by adding unit tests in tests/unit/test_hybrid.py. The failing tests show that a keyword-only result, or a weaker vector result with a strong BM25 boost, can outrank a more semantically relevant vector result.

**PLAN.md link:** (https://github.com/GarabKDorji/pathreview/blob/fix/24-hybrid-retriever-keyword-weighting/PLAN.md)

**Walkthrough video (recommended):** https://drive.google.com/file/d/1PTOnbrvv-nu3mmv85VzRiT0O8M7N_fPp/view?usp=sharing

**Blockers or open questions:**
I still need to determine which score-combination strategy is the most appropriate. I plan to compare Weighted Reciprocal Rank Fusion, BM25 score saturation or capping, and reducing the keyword contribution for chunks with weak or missing vector relevance. I also need to confirm why the issue description refers to equal weights when the current implementation defaults to 0.7 vector weight and 0.3 keyword weight.

## Week 9 — Solution Building and PR Submission

### Check-in 1 (Mid-week)

**Current progress:**

I completed Steps 1 through 5 of `PLAN.md`.

I traced how the vector and keyword scores move through `retrieve()` and identified the cause of the ranking issue.

The method normalizes the vector and BM25 score lists separately by dividing every score by the highest score in that list. As a result, the top vector result and the top BM25 result both receive a normalized score of `1.0`.

The current implementation then combines them as two independent contributions:

```python
blended_score = (
    0.7 * vector_score
    + 0.3 * keyword_score
)
```

Because the keyword contribution is independent of semantic relevance, a chunk can receive the full keyword contribution of `0.30` even when its vector score is `0`.

The reproduction test demonstrates this problem:

* A chunk that matches only the keyword `"Python"` has a vector score of `0` and the highest BM25 score. Its blended score is:

```text
0.7 * 0 + 0.3 * 1.0 = 0.30
```

* A chunk that is semantically relevant to the query has a normalized vector score of `0.4` but no keyword match. Its blended score is:

```text
0.7 * 0.4 + 0.3 * 0 = 0.28
```

The keyword-only chunk therefore ranks above the semantically relevant chunk.

After comparing the three strategies described in `PLAN.md`, I selected Option 3: reduce the keyword contribution when a chunk has weak or missing vector relevance.

The implementation requires one change in `rag/retriever/hybrid.py`:

```python
blended_score = (
    self.vector_weight * vector_score
    + self.keyword_weight * keyword_score * vector_score
)
```

This can also be written as:

```text
vector_score * (vector_weight + keyword_weight * keyword_score)
```

With the default weights, the keyword match adjusts the vector score by a multiplier between `0.7` and `1.0`.

This makes semantic relevance the foundation of the final score. A chunk with a vector score of `0` can no longer be promoted by its keyword score alone. A chunk that performs well in both searches still receives the strongest possible blended score.

I also evaluated weighted Reciprocal Rank Fusion, resolving the first open question from Week 8.

RRF uses each chunk’s rank position rather than its original retrieval score. Therefore, it cannot preserve the difference between two chunks that occupy the same rank position in separate test cases.

For example, my third test produced the same fused score of `0.01621` when the second-ranked vector result had a score of `0.6` and when it had a score of `0.1`. RRF only recognized that the chunk was ranked second; it did not recognize the large difference in semantic relevance.

RRF would also require changing how `min_score` and the returned score fields are interpreted. The current threshold expects a score on a meaningful `0–1` scale, while RRF produces much smaller rank-based values.

RRF may be a reasonable option for a larger retriever redesign because it avoids directly combining cosine similarity and BM25 scores. However, it fails two of my six tests because its behavior does not match the requirements of this issue. It would also require broader changes outside the intended scope of this PR.

I resolved the second open question as well. Nothing outside the test suite constructs `HybridRetriever`, so the default weights of `0.7` and `0.3` are not overridden elsewhere in the application. The issue description refers to equal weights, but the current implementation does not use equal weights.

All six tests in `tests/unit/test_hybrid.py` now pass.

**Next steps:**

I will complete Step 6 by running the broader test suite to check for regressions. I will then run:

```bash
make check
make test-unit
```

After confirming that my changes introduce no new failures, I will open a draft PR and request feedback from a peer or mentor.

I considered revising one reproduction test and decided against it.

In `test_keyword_score_boosts_weaker_vector_chunk_above_stronger_vector_chunk`, `keyword_boosted_chunk` has a vector score of `0.6` even though its text is only repeated occurrences of `"Python"` and the query is about weather forecasting. That value arguably overstates how relevant the embedding model would find the chunk.

I checked whether the fix depends on that value. Under the new formula the chunk's blended score reduces to exactly its normalized vector score, because `0.7 * 0.6 + 0.3 * 1.0 * 0.6 = 0.6`, and `relevant_chunk` scores `0.7`. The test therefore passes for any vector score below `0.7`, so lowering it was unnecessary.

I left both reproduction tests exactly as I committed them in Week 8. This makes the change easier to review, because the only difference in the PR is the single line in `rag/retriever/hybrid.py`, and the original failing tests now pass without any adjustment to their data.

**Blockers:**

There are no blockers affecting the scoring fix itself. However, while tracing the retrieval flow, I identified three separate issues that I do not believe should be included in this PR:

1. `keyword_searcher.index()` is not called anywhere in the application. `retrieve()` fetches `all_chunks` but does not use them, and `_get_all_chunks()` appears to exist only for that unused operation. Without indexing the chunks, `KeywordSearcher.search()` returns an empty result list. This means the keyword path may currently be inactive in production, while the behavior described in issue 24 is reachable only through mocked tests.


2. `retrieve()` normalizes vector scores by dividing them by the highest score in the current batch. This forces the top result to `1.0` regardless of its absolute quality and removes information from the vector similarity scale.


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/764

**Branch:** `fix/24-hybrid-retriever-keyword-weighting`

**What you built:**
I changed the score blending in `HybridRetriever.retrieve()` so the keyword contribution is scaled by semantic relevance instead of being added independently. The keyword term is now multiplied by `vector_score`, which makes the formula `vector_score * (vector_weight + keyword_weight * keyword_score)`. A chunk that only repeats a common technology name has no vector relevance to scale, so it can no longer outrank a chunk the query is actually about, while a chunk found by both searches still receives the full keyword boost.

**Tests added or updated:**
`tests/unit/test_hybrid.py`. The two reproduction tests from Week 8 now pass: `test_semantic_vector_chunk_should_outrank_keyword_only_chunk` and `test_keyword_score_boosts_weaker_vector_chunk_above_stronger_vector_chunk`.  The four existing tests covering the both-searches boost, the `min_score` filter, empty results, and the `max_chunks` limit are unchanged and still pass.

**Self-review confirmation:** [✓] make check passes  [✓] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received. The PR is still open and awaiting maintainer review. GitHub currently shows no reviewer comments or submitted reviews.

**How you responded:**
No response or additional changes were needed because no reviewer feedback was provided.

---

### Reflection

**What was harder than you expected?**
The hardest part was understanding how the hybrid retriever actually combined vector and keyword scores. At first, I thought the issue would only require changing the weights, but after tracing the code I found that the real problem was that the keyword score was added independently of semantic relevance. I also had to separate failures caused by my changes from failures that already existed in the repository, which took more investigation than I expected.

**What did you learn about working in a large codebase?**
I learned that working in someone else's codebase requires much more investigation before making changes. In my own projects, I usually know how everything is connected, but here I had to trace the retrieval flow, understand existing tests, and make sure I was not changing behavior outside the issue's scope. I also learned that it is important to keep a contribution focused instead of trying to fix every unrelated problem I discover.

**How did AI tools help — and where did they fall short?**
AI tools helped me understand unfamiliar parts of the codebase, reason through the scoring formula, compare possible solutions such as Reciprocal Rank Fusion, and debug errors during testing. They were also useful for explaining Git and open-source workflows. However, AI could not determine the correct solution by itself. I still had to inspect the actual code, run the tests, compare different approaches, and verify whether suggestions matched the behavior of the repository.

**What would you do differently if you started over?**
I would spend more time at the beginning tracing the full execution path and running the complete test suite before making changes. That would help me identify pre-existing failures earlier and understand the baseline state of the repository. I would also document findings as I discover them instead of waiting until later, because several important details, such as the unused keyword indexing path and the difference between the issue description and the actual default weights, only became clear after deeper investigation.

**What are you most proud of from this module?**
I am most proud that I did more than simply change one line of code. I reproduced the bug with tests, traced the cause of the ranking problem, compared multiple possible solutions, implemented a focused fix, and verified that all six hybrid retriever tests passed. I also identified additional issues in the retrieval flow without expanding the scope of my PR unnecessarily. This gave me a better understanding of how a real open-source contribution should be investigated, tested, and documented.