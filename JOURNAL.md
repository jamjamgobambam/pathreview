# Week 7 — Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** ☐ Tier 1 ☐ Tier 2 ☑ Tier 3

## Problem Summary

Currently, the system relies solely on vector and keyword scores to rank retrieved document chunks, which may not always capture the nuance of semantic relevance to a user's query. This issue involves building a re-ranking layer that utilizes a smaller, efficient LLM to evaluate the relevance of these initial chunks before they are sent to the primary generator. A successful implementation will prune less relevant results, ultimately increasing the accuracy and quality of the context provided to the LLM. This work will primarily involve creating a new `reranker.py` module in the `rag/retriever/` directory and integrating it into the existing flow within `rag/retriever/hybrid.py`.

## Setup

- **Branch name:** `feat/34-llm-chunk-reranker`
- **Setup confirmation:** ☑ App runs locally at `localhost:5173`
- **Cohort ledger:** ☑ Issue added to cohort ledger

## "Is this right for me?" Checklist Reasoning

**Part 1 — Understanding the Issue:** I can clearly define the problem: the current system lacks a secondary relevance check after initial retrieval, leading to potentially noisy context. The expected behavior is that retrieved chunks will pass through an LLM re-ranker, which will score and filter them before the generator receives them.

**Part 2 — Tier Fit:** While this is a Tier 3 issue, it is a realistic match for my background in RAG architectures and Python engineering. I have already built full RAG pipelines, which provides the necessary foundation to navigate this architectural change safely.

**Part 3 — Codebase Readiness:** I have located `rag/retriever/hybrid.py` and identified where the integration point for the new `reranker.py` module belongs. I have reviewed the existing retrieval logic and feel confident that I can inject the re-ranking logic without destabilizing the current flow.

**Part 4 — Scope and Time:** The estimated effort is 7–10 hours. Given my familiarity with the codebase and the upcoming two-week window for implementation and testing, this is well within my capacity for the Week 9 deadline. There are no blockers or dependencies listed on the issue.


## Week 8 — Reproduction & Solution Planning

**Reproduction commit link:** https://github.com/BradshawAsher/pathreview/commit/046fb0f4677d29945c093bf1b6818ade6a097d46

**Reproduction commit branch link:** https://github.com/BradshawAsher/pathreview/tree/feat/34-llm-chunk-reranker

**Reproduction summary:**
Confirmed that `rag/retriever/hybrid.py` returns hybrid search results directly to the generator with no LLM re-ranking pass, and that `rag/retriever/reranker.py` does not exist (no `rerank` references anywhere in the codebase). Documented the gap with a reproduction test at `tests/unit/test_reranker.py`: one test passes because the reranker module is absent, and one `xfail` test defines the desired `rerank()` behavior. Running `pytest tests/unit/test_reranker.py -v` yields `1 passed, 1 xfailed`; the xfail will flip to xpass once the reranker is implemented.

**PLAN.md link:** https://github.com/BradshawAsher/pathreview/blob/feat/34-llm-chunk-reranker/PLAN.md

**Walkthrough video (recommended):** _Insert Loom link if recorded, or leave blank_

**Blockers or open questions:**
None at the moment — one open question is which model to configure for the re-ranking pass (a small/fast model to keep latency low).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All three sub-tasks from PLAN.md are implemented:
1. Created `rag/retriever/reranker.py` with `LLMReranker` + `RerankConfig`. It scores each retrieved chunk's relevance (0–10) via a small, low-temperature LLM, normalizes to 0–1, and re-sorts. Score parsing tolerates prose and out-of-range values (clamped to 0–10).
2. Integrated the reranker into `rag/retriever/hybrid.py` — `HybridRetriever` takes an optional `reranker`; when supplied, `min_score`-filtered candidates are re-ranked before truncation to `max_chunks`. Backward-compatible (behavior unchanged when omitted).
3. Wrote 21 unit + integration tests in `tests/unit/test_reranker.py` that mock the LLM, replacing the Week 8 reproduction stub.

Also handled the PLAN's edge cases (empty results, missing text, LLM/API failure → fall back to hybrid score) and captured a baseline of pre-existing test/lint failures before starting.

**Next steps:**
Open a draft PR, request peer/mentor review in Slack, address any feedback, then mark it ready for review and finalize.

**Blockers:**
None. Open question (non-blocking): which model to configure for the re-ranking pass once the retrieval pipeline is wired into a live orchestrator.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/514

**Branch:** `feat/34-llm-chunk-reranker`

**What you built:**
An optional LLM re-ranking step for the hybrid retriever (issue #34). After hybrid search blends vector and keyword scores, a small LLM re-scores each candidate chunk's relevance to the query and re-sorts before the top-k are sent to the generator. It is defensive: any LLM/API failure or unparseable output falls back to the existing hybrid score, so results never degrade below plain hybrid ranking.

**Tests added or updated:**
`tests/unit/test_reranker.py` — 21 tests covering LLM-driven re-sorting, score normalization + clamping, `top_k` truncation, original-field preservation, and graceful fallback on API failure / unparseable output / empty / missing text; plus integration tests asserting `HybridRetriever` delegates to the reranker when provided and preserves pure hybrid ordering when not. (Pre-existing baseline: 83 test failures/errors unrelated to this issue; my changes introduce zero new failures — 83 before, 83 after.)

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(“passes” = no new failures vs. the documented pre-existing baseline; see the PR’s Notes for Reviewers.)_

**Draft PR feedback received from:** none (skipped peer review for time; performed a self-review instead — notes below)

**Self-review notes:**
- **Backward compatibility:** `HybridRetriever` behaves identically when no `reranker` is passed — the reranking pass is guarded by `if self.reranker is not None`. Covered by `test_retrieve_without_reranker_unchanged`.
- **Fallback safety:** verified graceful degradation on LLM/API failure, unparseable output, and empty/missing text — each falls back to the chunk's existing hybrid `score`, so results never drop below plain hybrid ranking. Covered by dedicated tests.
- **Ordering:** the reranker re-scores the full `min_score`-filtered candidate pool (up to `2 * max_chunks`) before truncation, so a genuinely relevant chunk can be promoted above a keyword-heavy but off-topic one.
- **Observation / follow-up:** `rerank()` attaches a new `rerank_score` and sorts by it, but preserves the original hybrid `score`. Downstream display code (`ReviewGenerator._format_context`) still reads `score`, so the shown "relevance" would remain the hybrid score after reranking. Not a bug for this PR (the reranker isn't wired into the generator yet), but worth aligning when the pipeline is assembled.
- **Known cost:** per-chunk scoring means N LLM calls per retrieval; mitigated by a small/fast model + low `max_tokens`. Batching is a possible optimization.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received (Summer 2026 cohort / awaiting review).

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Building robust, defensive error handling for non-deterministic LLM responses in a core retrieval pipeline was significantly more challenging than standard software engineering. While a simple system prompt ("rate from 0 to 10") sounds straightforward, real LLM outputs can be chatty (e.g., "Relevance score: 8/10"), return unexpected formatting, or fail entirely due to API rate limits or network issues. Designing regex score extraction (`re.compile(r"[-+]?\d*\.?\d+")`), clamping out-of-range floats to `[0.0, 10.0]`, and implementing a graceful fallback to original hybrid scores (`float(chunk.get("score", 0.0))`) required much more edge-case planning than expected. Additionally, working against a repo with an 83-test pre-existing failure baseline meant I had to strictly isolate my test suite (`tests/unit/test_reranker.py`) to verify that zero new regressions were introduced.

**What did you learn about working in a large codebase?**
I learned the vital importance of preserving backward compatibility and loose coupling when extending existing architectures. Injecting `LLMReranker` into `HybridRetriever` required making the `reranker` parameter optional so that existing callers, pipelines, and test suites would function without modification when `reranker=None`. Contributing to production code is vastly different from building a personal project from scratch: you cannot rewrite existing signatures or ignore surrounding conventions like `structlog` logging and `OpenAI` client SDK patterns. Every change must feel native to the existing system architecture.

**How did AI tools help — and where did they fall short?**
AI tools were exceptionally helpful for generating repetitive unit test scaffolding, mocking `OpenAI.chat.completions.create` responses, and drafting initial regex patterns for string parsing. However, AI fell short on system-level defensive architecture and latency considerations. AI initially suggested basic `float(response)` parsing, which would crash with a `ValueError` on conversational model output, and missed the risk of unhandled API exceptions breaking the retrieval pipeline. Human judgment was required to design the zero-downtime fallback strategy (falling back to hybrid search scores on API error) and to evaluate the operational tradeoff of per-chunk LLM API calls ($N$ requests per query).

**What would you do differently if you started over?**
If I were to start over, I would design the re-ranking step with asynchronous batching (`asyncio.gather` or batch prompting) from day one rather than sequential per-chunk scoring loops. Sequential LLM calls introduce $N$ network round-trips per retrieval, which adds latency overhead. Secondly, I would align the score property naming upfront across the pipeline—`LLMReranker` assigns a `rerank_score` while downstream context formatters (`ReviewGenerator._format_context`) still read `score`. Explicitly standardizing how re-ranked scores propagate to downstream generation components would make the end-to-end integration cleaner.

**What are you most proud of from this module?**
I am most proud of building a production-grade, defensive LLM feature with zero-downtime fallback guarantees. Rather than creating a fragile proof-of-concept, I engineered `LLMReranker` so that any model failure, timeout, rate limit, or unparseable output gracefully degrades to standard hybrid search ordering without throwing exceptions or returning empty results. Delivering 21 comprehensive unit and integration tests covering every fallback path—and verifying zero new regressions against the codebase baseline—gives me high confidence in the reliability of this contribution.