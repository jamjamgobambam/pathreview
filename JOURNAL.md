## Week 7 — Issue Selection

**Issue:** [#34 — Implement a re-ranking step that uses an LLM to score retrieved chunks before generation](https://github.com/ascherj/pathreview/issues/34)

**Problem Summary:**

Issue: Add an LLM-based re-ranking step to the RAG retrieval pipeline.

Current behavior: `rag/retriever/hybrid.py` ranks retrieved chunks using vector similarity and keyword scores only. There's no semantic relevance check, so numerically high-ranked chunks may still be off-topic.

Desired behavior: After hybrid retrieval, an optional re-ranking pass prompts a smaller LLM to score each chunk's relevance to the query, then passes only the top-k re-ranked chunks to the generator.

Scope: New module `rag/retriever/reranker.py` for the scoring logic, plus a modification to `hybrid.py` to call it as an optional step. Tier 3 — touches how retrieval and generation connect.

Why it matters: Filters out chunks that pass vector/keyword thresholds but are semantically irrelevant, improving feedback quality without adding a heavier model to the always-on path.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented LLMReranker (rag/retriever/reranker.py) and wired it into
HybridRetriever.retrieve() as an opt-in step via a new use_reranker
parameter (default False -- existing behavior unchanged). Added unit
tests: 10 for the reranker (sorting, top_k, fallback on LLM failure/
unparseable/out-of-range output, prompt content) and 5 for the hybrid
wiring (opt-in behavior, backward compatibility). All 15 new tests
passing.

**Next steps:**
Run make check / make test-unit, document pre-existing failures,
open PR, request review, finalize PR description.

**Blockers:**
None blocking; noted two pre-existing mypy errors (vector_store.py,
keyword_search.py) and 53 pre-existing test-unit failures, both
unrelated to this change -- documented in PR description.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/969

**Branch:** feat/34-llm-chunk-reranker

**What you built:**
Added an optional LLM-based re-ranking step to the RAG retrieval
pipeline. LLMReranker scores each retrieved chunk's relevance to the
query via an LLM call, then returns the top-k re-ranked results. It's
wired into HybridRetriever.retrieve() as an opt-in parameter
(use_reranker), so default retrieval behavior is unchanged unless a
reranker is explicitly configured and enabled. Falls back to the
existing blended score if an LLM call fails or returns unparseable
output.

**Tests added or updated:**
- tests/unit/test_reranker.py (10 tests): covers sorting by LLM score,
  top_k limiting, preserving original chunk fields, and fallback
  behavior on LLM failure, unparseable output, and out-of-range scores.
- tests/unit/test_hybrid.py (5 tests): covers that the reranker is not
  called by default, is called when explicitly enabled, receives the
  correct query/chunks/top_k, and that output shape is unchanged when
  no reranker is configured.

**Self-review confirmation:** [x] make check passes (my files only --
2 pre-existing mypy errors in vector_store.py/keyword_search.py,
unrelated to this change)  [x] make test-unit passes (53 pre-existing
failures unrelated to this change; all 15 new tests pass, no
regressions in the 390 previously-passing tests)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [— still awaiting review

**Summary of feedback:**
No review came in yet. 

**How you responded:**
N/A — no feedback received. If comments come in after submission, I'll
follow up and document the response here.

---

### Reflection

**What was harder than you expected?**
Getting the local environment right was harder than the actual implementation.
I kept running `pytest` and `python` from my base anaconda install instead of
the project's `.venv`, which produced a confusing `ModuleNotFoundError` that
had nothing to do with my code. It cost real time before I realized the fix
was just activating `.venv`. I also didn't expect pre-commit hooks (ruff,
black, mypy) to block commits repeatedly — black kept reformatting my files
after I thought I was done, so I had to re-stage and recommit several times.

**What did you learn about working in a large codebase?**
The biggest thing was learning to distinguish "my bug" from "pre-existing
issue." When `make test-unit` came back with 53 failures, my first instinct
was that I'd broken something — but almost none of those failures touched
the files I changed. I had to learn to verify scope (which files were
actually affected) rather than assume every red test was mine to fix. I also
had to match existing conventions (the `openai.OpenAI` client pattern from
`review_generator.py`, the `Mock`/`patch` testing style from
`test_batch_processor.py`) instead of inventing my own approach, which
required actually reading code I didn't write before writing any of my own.

**How did AI tools help — and where did they fall short?**
AI was most useful for pattern-matching: once I showed it the existing
`ReviewGenerator` class and an existing test file, it could follow those
conventions closely for the new reranker code and tests, which saved a lot
of time versus writing boilerplate from scratch. Where it fell short: it
couldn't see my actual terminal state, so when a heredoc paste went wrong or
a file ended up in the wrong place (I accidentally duplicated code into
`rag/retriever/__init__.py` at one point), I had to be the one to notice
something looked off and ask it to help me diagnose and fix it. AI also
can't tell you what your instructor actually expects when a course doc is
ambiguous (like where the "cohort ledger" lives) — I still had to make
judgment calls there.

**What would you do differently if you started over?**
I'd activate the project's `.venv` and run `make check`/`make test-unit`
once, immediately after cloning, before writing any code — that alone would
have caught the environment issue on day one instead of mid-implementation.
I'd also budget time across the week instead of compressing Week 9 into a
single day; skipping the draft-PR-for-feedback step meant I lost the chance
to catch issues before finalizing, which is exactly the step the module was
trying to teach.

**What are you most proud of from this module?**
Getting the reranker to fail gracefully. Instead of letting a bad LLM
response crash retrieval, I built in a fallback to the existing blended
score, and wrote tests specifically for that failure path (LLM call
errors, unparseable output, out-of-range scores). That's the kind of
edge-case thinking I wouldn't have prioritized without slowing down enough
to ask "what happens when this goes wrong," and it's the part of the PR I'd
feel best defending to a reviewer.