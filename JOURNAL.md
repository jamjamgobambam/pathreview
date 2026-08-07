# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The RAG retriever currently ranks chunks with a purely mechanical score — a
weighted blend of vector cosine similarity and BM25 keyword scores in
`HybridRetriever.retrieve()`. That blended score measures surface-level
similarity, not whether a chunk actually answers the query, so genuinely
relevant chunks can be pushed below the top-k cutoff and passed over before
generation. This issue asks for an optional second-stage re-ranking pass: after
hybrid retrieval produces its candidate set, prompt a smaller LLM to score each
candidate's relevance to the query and reorder them, so the top-k handed to the
generator reflects semantic relevance rather than just lexical/embedding
overlap. A successful fix adds a new `rag/retriever/reranker.py`, wires it into
`hybrid.py` behind a toggle (so the existing behavior stays the default), and is
covered by at least one new unit test — improving answer quality without
breaking the current retrieval path.

**Branch name:** feat/34-llm-chunk-reranking

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this right for me?" checklist reasoning

- **Understand it:** I can explain it in my own words (add an optional LLM
  re-scoring pass over the hybrid-retrieved chunks before the top-k reach the
  generator), located the referenced files (`rag/retriever/hybrid.py` + new
  `reranker.py`), and can describe the before/after behavior. 
- **Tier fit:** Labeled **tier-3** (RAG/AI-pipeline change); 7–10h estimate fits
  the Weeks 8–9 window and I'm accepting that scope knowingly. 
- **Codebase readiness:** Read `HybridRetriever.retrieve()` and the retriever
  subpackage end to end, so I know the chunk dict shape and the insertion point
  for the re-rank hook; reviewed `tests/unit/test_keyword_search.py` for test
  patterns and will add a new unit test with the LLM mocked. 
- **Scope & time:** No blockers or dependencies, the files already exist, and the
  estimate is realistic for my two weeks; still need to confirm the Claims count
  on the ledger. 

**Verdict:** Understanding and codebase boxes checked. Remaining actions: confirm
localhost:5173 runs and add the issue to the cohort ledger.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Vanshikashah318/pathreview/commit/b369655f8709cf4f5ff2bcb9396f569e035ee23d

**Reproduction summary:**
Traced the ranking path in `HybridRetriever.retrieve()` (`rag/retriever/hybrid.py`,
lines 92–97): the candidate chunks are filtered by `min_score`, sorted by the
blended vector+BM25 score, and sliced to `max_chunks` — with no LLM relevance
re-ranking anywhere between the sort and the top-k cut. Documented the gap with a
marker comment at the insertion point and a characterization test
(`tests/unit/test_reranker.py`) pinning the current mechanical-only ordering,
confirming exactly where the missing re-rank hook belongs.

**PLAN.md link:** https://github.com/Vanshikashah318/pathreview/blob/feat/34-llm-chunk-reranking/PLAN.md

**Walkthrough video (recommended):** [optional Loom link, ≤2 min]

**Blockers or open questions:**
Need to trace how `HybridRetriever` is constructed at its call site (likely
`agent/orchestrator.py` or a retrieval factory) to finalize the `__init__`
signature for the `reranker` / `enable_rerank` toggle. Separately, `make run`'s
frontend fails with a Node `crypto.getRandomValues` error (Node-version issue,
unrelated to this backend/RAG issue) — backend + unit tests run fine.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented all PLAN.md sub-tasks: added `rag/retriever/reranker.py`
(`LLMReranker` + `RerankConfig`), wired an off-by-default `enable_rerank` toggle
into `HybridRetriever`, and added `tests/unit/test_reranker.py` (9 unit tests, LLM
mocked — all passing). Ran the full unit suite with and without my changes: 53
pre-existing failures either way, +9 new passing tests, so my change introduces no
new failures.

**Next steps:**
Open the draft PR, incorporate peer/mentor review feedback, then mark ready.

**Blockers:**
Repo has pre-existing `ruff`/`mypy`/test failures unrelated to this issue; confirmed
my changes don't add to them.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/182

**Branch:** `feat/34-llm-chunk-reranking`

**What you built:**
An optional second-stage LLM re-ranking pass for the hybrid retriever. After
vector+BM25 blending, an opt-in reranker prompts a smaller LLM to score each
candidate chunk's relevance and reorders before the top-k cut, so semantically
strong chunks aren't dropped by purely mechanical scoring. Off by default, with a
safe fallback to blended order on any LLM/parse failure.

**Tests added or updated:**
`tests/unit/test_reranker.py` — 9 tests covering relevance reordering, empty input,
error and partial-response fallback, JSON/code-fence parsing, no input mutation, and
both states of the `enable_rerank` toggle.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
(All checks pass on the files I authored; the repo's pre-existing `ruff`/`mypy`/test
failures in unrelated modules are documented in the PR and unaffected by this change.)

**Draft PR feedback received from:** aishadeveloper

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes (peer review via Slack)  [ ] No — still awaiting review

**Summary of feedback:**
aishadeveloper reviewed the draft PR and raised five things: (1) the pre-commit
bypass wasn't needed — the `ruff`-flagged unused `all_chunks` local was in a file
I was already editing, so deleting it (and its `_get_all_chunks` call) was an honest
fix; (2) my `rerank()` sent LLM-unscored chunks to the bottom via `scores.get(i, 0.0)`,
which contradicted my own PLAN edge case and could bury a chunk the blend ranked #1;
(3) `_parse_scores` called `json.loads` directly and would silently fall back whenever
the model wrapped its JSON in a ```` ```json ```` fence; and (4) nits — `rerank()`
mutated the caller's chunk dicts, the prompt embedded full chunk texts with no
truncation, and the PR title didn't follow the conventional format.

**How you responded:**
Pushed `e595eb0` addressing all of it: removed the dead `all_chunks` fetch and the
orphaned `_get_all_chunks` method (removing a real per-`retrieve()` overhead, not just
silencing the linter); made a partial LLM response fall back to the blended order
instead of burying unscored chunks; added a fence-tolerant JSON loader plus a log line
when nothing parses; switched to copying chunk dicts (`dict(chunk, rerank_score=...)`);
capped prompt chunk text at `MAX_CHUNK_CHARS`; and renamed the PR to `feat(rag): ...`.
Tests went from 6 to 9, all passing. I also replied on the PR mapping each point to
its fix and thanking the reviewer.

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't the re-ranking logic — it was the *repo's own state*. On the
first `make test-unit` I saw 53 failing tests and briefly assumed I'd broken something;
it took stashing my changes and re-running (53 fail with or without my code) to prove
they were pre-existing. Then the pre-commit hooks disagreed with `make check`: `make
check` only type-checks `api/ core/ ingestion/ rag/ agent/ safety/`, but the pre-commit
`mypy` hook (with `disallow_untyped_defs = true`) also checks the test files, so my
first commit was blocked by pre-existing debt in files I never touched. Untangling
"which failures are mine vs. the codebase's" was more work than writing the feature.

**What did you learn about working in a large codebase?**
Discipline about scope. My instinct was to "fix" every red check, but in someone else's
production code the right move is usually the opposite: touch as little as possible,
document pre-existing failures, and prove your change adds zero new ones rather than
fixing the whole repo. I also learned to *match the house style* instead of my own —
conventional commits, `structlog` logging, the existing `openai.OpenAI` client pattern
in `review_generator.py`, and the fence-stripping already in `output_parser.py`. And
the value of an off-by-default toggle: it's what let me add a capability to a shared
`retrieve()` path without changing behavior for any existing caller.

**How did AI tools help — and where did they fall short?**
AI was most useful for navigation and pattern-matching — tracing `HybridRetriever.retrieve()`,
finding where the LLM config lived (`core/config.py`, OpenRouter + the free Gemma model),
and reusing existing conventions so my code didn't look bolted-on. It was also good at
scaffolding the mocked tests. Where it fell short was *judgment calls*: whether to bypass
a hook or fix pre-existing debt, how to keep the PR scoped, and reading the reviewer's
intent. It also couldn't do the parts that needed my credentials — pushing to my fork
kept hanging on auth until I ran it myself. AI accelerated the mechanical work; the
decisions were still mine.

**What would you do differently if you started over?**
Run `make check` and `make test-unit` and record the baseline *before* writing a single
line — I'd have saved an hour of "did I break this?" if I'd known the 53 failures were
there from the start. I'd also set up `gh`/git auth early instead of hitting push
failures at the end, and I'd have designed the partial-response fallback correctly the
first time instead of the reviewer catching that my code contradicted my own PLAN.

**What are you most proud of?**
That the review feedback made the code genuinely better and I engaged with all of it, especially turning "just silence the linter with
`--no-verify`" into an honest fix that removed real overhead. The reranker is opt-in,
fails safe, and is covered by tests that actually assert the behavior that matters
(a semantically-better chunk beating a higher blended score), not just that the code
runs.
