## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [] Tier 2  [x] Tier 3

**Problem summary:**
The current retrieval pipeline ranks document chunks using a combination of vector similarity and keyword-based scores. Although this hybrid approach identifies potentially useful chunks, the highest-scoring results may not always be the most relevant to the user’s specific query. This issue will add an optional LLM-based re-ranking step that scores the retrieved candidate chunks for relevance before the final top-k chunks are passed to the generator. A successful implementation will preserve the existing retrieval behavior when re-ranking is disabled and use the LLM-produced relevance scores when the feature is enabled.

**Branch name:** `feat/34-llm-chunk-reranking`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes

I selected this issue because it involves a meaningful improvement to the project’s retrieval-augmented generation pipeline and aligns closely with the AI engineering concepts covered in this course. I can explain the expected before-and-after behavior: currently, chunks are ranked only by hybrid vector and keyword scores, while the completed feature will optionally use a smaller LLM to evaluate semantic relevance and reorder the candidates before generation.

The issue identifies a focused implementation area in `rag/retriever/`, including a new `reranker.py` file and changes to `hybrid.py`. However, it requires understanding how retrieval results are represented, how the existing LLM client is called, how top-k selection works, and how the generator receives its context. I will review those functions and the relevant test files before modifying the implementation.

The estimated effort is 7–10 hours, which is realistic for me to complete during Weeks 8 and 9. My initial plan is to implement a reranker abstraction, request structured relevance scores from the existing LLM client, sort the candidate chunks by those scores, preserve a fallback path when re-ranking is disabled or fails, and add tests using mocked LLM responses. I will also confirm through the issue comments and cohort ledger that I am comfortable with the number of other students working on the issue and that there are no unresolved dependencies.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [reproduction commit](https://github.com/mehakgupta9/pathreview/commit/1f3234e7d6207635d53f53290ebc9ff4561bc04e)

**Reproduction summary:**
Since this is a feature-gap issue, I reproduced it by confirming — through code inspection — that the re-ranking step does not exist and locating exactly where it would live. Running `grep -rin "rerank"` across `rag/`, `core/`, `api/`, and `agent/` returns no matches, and `rag/retriever/reranker.py` is absent. Reading `HybridRetriever.retrieve()` confirms the gap: at `rag/retriever/hybrid.py:94` the candidate chunks are sorted purely by the blended vector+keyword `score` and the top-k are handed straight to the generator (`rag/generator/review_generator.py:39`), with no LLM relevance step in between. This documents that the highest-scoring chunks are chosen by a lexical/embedding proxy rather than judged for relevance to the specific query.

Reproduction steps (anyone can re-run these):
1. `grep -rin "rerank" rag/ core/ api/ agent/` → no results (feature absent).
2. `ls rag/retriever/reranker.py` → No such file or directory.
3. Read `rag/retriever/hybrid.py:92-104` → chunks ordered only by blended hybrid score, no LLM re-ranking.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** _(optional — add Loom link if recorded)_

**Blockers or open questions:**
- Whether to score each chunk with a separate LLM call or batch all candidates into one scoring prompt (latency/cost vs. simplicity), given the free `google/gemma-3-27b-it:free` model configured in `core/config.py`.
- Whether to construct the OpenAI client inside `LLMReranker` or inject it (leaning toward injection for testability, matching `ReviewGenerator`).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented all of PLAN.md. Added opt-in re-ranking settings to `core/config.py`
(`enable_reranking`, `rerank_model`, `rerank_candidate_multiplier`, all defaulting
off). Built the `LLMReranker` class in `rag/retriever/reranker.py` — it scores each
candidate chunk for relevance via the LLM, parses/clamps the score, keeps ties
stable, and falls back to the incoming hybrid order on any LLM failure. Wired an
optional typed `reranker` and a `rerank` flag into `HybridRetriever.retrieve()`;
when disabled (the default) retrieval behavior is unchanged. Added 13 unit tests
(`tests/unit/test_reranker.py`, `tests/unit/test_hybrid_retriever.py`), all passing,
with the LLM fully mocked (no network calls).

**Next steps:**
Open a draft PR, request peer/mentor feedback in Slack, address it, then mark the
PR ready for review and fill in Check-in 2.

**Blockers:**
None functionally. Documented pre-existing repo state (not caused by my change):
`make test-unit` shows 53 failing tests on `main` (baseline 53 failed / 375 passed;
after my change 53 failed / 388 passed — my 13 tests are the only delta).
`make check` also fails on `main` (177 pre-existing `ruff` errors and missing type
stubs). My changed files pass `ruff`, `black`, and `mypy` individually.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/183

**Branch:** `feat/34-llm-chunk-reranking`

**What you built:**
An optional LLM re-ranking step for retrieval: when enabled, the LLM scores each
retrieved chunk for relevance to the query and reorders the candidates before the
top-k are passed to generation; when disabled (default), retrieval is unchanged. A
`build_hybrid_retriever(settings, ...)` factory consumes the opt-in settings; live
pipeline wiring is deferred because the RAG pipeline is still a stub.

**Tests added or updated:**
`tests/unit/test_reranker.py` (12 tests) and `tests/unit/test_hybrid_retriever.py`
(8 tests) — reorder-by-score, top_k limit, empty input, total/partial LLM-failure
fallback, tie stability, score parsing/clamping, client-boundary path, candidate-pool
widening, disabled-vs-enabled paths, and the settings factory. All mock the LLM (no
network). 20 tests total, all passing.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Per the assignment's pre-existing-failure rule: "passes" = my changes introduce no
new failures. After my change the suite is 395 passed / 53 failed — the 53 failures
and the `make check` errors pre-exist on `main` and are documented in the PR.)

**Draft PR feedback received from:** aishadeveloper — reviewed the draft PR and
flagged the PR title, unused config, a candidate over-fetch bug, coarse LLM-failure
handling, and test/nit cleanups. All addressed in commit `4afb8b4` (widened fetch,
per-chunk fallback, settings factory, removed dead code, client-boundary test).

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes (peer review)  [ ] No — still awaiting review

The feedback below
came from the Week 9 peer review, by aishadeveloper.

**Summary of feedback:**
The reviewer called the layering and test suite clean but flagged five concrete
issues before merge: (1) the PR title still read "docs: add Week 7…" instead of a
`feat(rag)` title; (2) the new config settings (`enable_reranking`, `rerank_model`,
`rerank_candidate_multiplier`) were dead — nothing constructed the retriever, so the
feature couldn't actually be enabled; (3) a real bug — `retrieve()` still fetched
`max_chunks * 2` candidates even when reranking, so slicing `[:max_chunks * 3]` asked
for more candidates than were ever fetched; (4) the `try/except` in `rerank()` wrapped
the whole scoring loop, so one failed LLM call discarded every successful score; and
(5) nits — an unused `_get_all_chunks`, and tests that mocked the private
`_score_chunk` rather than the client boundary.

**How you responded:**
I agreed with all five and fixed them in commit `4afb8b4`: widened the actual
vector/keyword fetch to `max_chunks * multiplier` when reranking (with tests proving
the pool grows and that the disabled path is unchanged); replaced the loop-wide
`try/except` with a per-chunk `_safe_score` that falls back to a chunk's hybrid score
so one failure no longer discards the rest; added `LLMReranker.from_settings` and a
`build_hybrid_retriever(settings, ...)` factory so the config is consumed and tested
(noting in a docstring that end-to-end wiring is deferred because the RAG pipeline is
still a stub); removed `_get_all_chunks`; and added a client-boundary test that drives
the full path through the mocked LLM. Test count went from 13 to 20, all passing. I
posted a point-by-point reply on the PR so the reviewer could see each item addressed.

---

### Reflection

**What was harder than you expected?**
Two things. First, the production RAG pipeline I was plugging into
(`_run_rag_retrieval_generation` in `core/services/review_service.py`) turned out to be
a stub that returns hardcoded data — so I could never actually run my feature
end-to-end and watch it rerank real chunks. All my confidence had to come from unit
tests and reading code, which felt unnervingly indirect at first. Second, the repo's
tooling fought me: `make check` fails on `main` with 177 pre-existing ruff errors, the
suite has 53 pre-existing test failures, and the pre-commit hook strict-type-checks
files (and tests) that the repo itself never made pass. Figuring out that "passes"
meant "introduces no *new* failures," and proving that with a documented baseline, was
harder and more nuanced than just "make the checks green."

**What did you learn about working in a large codebase?**
That the constraints are different from a solo project. In my own code I'd just fix
whatever's broken; here the right move was the opposite — don't touch the 177
pre-existing lint errors or the stubbed pipeline, keep my change surgical, and make the
feature strictly opt-in (`rerank=False` by default) so existing behavior is
byte-for-byte unchanged. I spent as much effort matching conventions (Conventional
Commits with the `rag` scope, the repo's untyped-test style, Google-style docstrings)
and documenting pre-existing state as I did writing the actual logic. Contributing is
as much about not breaking things and being legible to a reviewer as it is about the
feature.

**How did AI tools help — and where did they fall short?**
AI was genuinely fast at tracing the codebase (finding how retrieval fed the generator,
how the OpenAI client was constructed, where config lived) and at scaffolding the tests
and boilerplate in the house style. Where it fell short was exactly the stuff the peer
reviewer caught: the first implementation had a real over-fetch bug (fetching `2x` but
slicing `3x`) and a coarse whole-loop `try/except` that would discard all scores on a
single failure. The AI-generated version *looked* clean and passed its tests, but those
tests didn't probe the fetch width or partial failure — so the gaps survived until a
human read it critically. The lesson: AI accelerates writing plausible code, but
judgment about edge cases, tradeoffs (e.g. whether bypassing the broken pre-commit hook
with `--no-verify` was acceptable), and "is this actually correct under load" still had
to be mine.

**What would you do differently if you started over?**
I'd pick an issue whose feature I could exercise end-to-end rather than one gated behind
a stubbed pipeline — being able to actually run it would have caught the fetch bug
before review. I'd also capture the `make check` / `make test-unit` baseline on day one
(I did it eventually, but only once commits started failing the hook), and I'd open the
draft PR earlier to get the review round in sooner instead of near the deadline. On the
code itself, I'd write the edge-case tests (partial failure, pool width) *first*, since
those were exactly the gaps that slipped through.

**What are you most proud of?**
The graceful-degradation design. After the review, the reranker degrades cleanly at
every level — empty input skips the LLM entirely, one failed chunk falls back to its
hybrid score instead of nuking the batch, and a fully unavailable LLM just returns the
original hybrid order. A retrieval quality feature should never be able to break the
core pipeline, and by the end it genuinely can't. I'm also proud that I handled the peer
review professionally — agreed on the real bugs, fixed them properly with tests.
