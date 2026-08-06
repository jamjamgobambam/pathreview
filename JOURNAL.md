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

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
A peer reviewer commented on the GitHub PR with four observations: (1) the `_parse_score` regex found the first number in the response rather than a leading float, so model outputs like "Chunk 3 scores 0.4" silently became 1.0 after clamping; (2) calling the LLM once per chunk meant 20 sequential round trips for a 20-chunk result set, dominating response time and giving the model no comparative context; (3) the API call was missing `temperature=0`, so the same chunk could score differently on identical queries; (4) a presentation nit — the checklist boxes for `make lint` and `make typecheck` were checked but the pre-existing failures in those commands were only documented in the summary, not next to the checkboxes themselves.

**How you responded:**
Addressed all three code issues in a single follow-up commit (`fix(rag): batch LLM scoring, anchor score parsing, add temperature=0`). Replaced the per-chunk `_score_chunk()` method with a batch `_score_chunks()` method that sends all chunks in one numbered prompt and parses a JSON array response. Replaced `_parse_score()` with `_parse_scores()` which extracts scores from a JSON array and uses the original blended score as a per-entry fallback when a value is out of the [0, 1] range rather than clamping it. Added `temperature=0` to the API call. Expanded the test suite from 9 to 21 tests, adding a `TestParseScores` class that specifically covers the parsing edge cases the reviewer identified. Also added the pre-existing failure note next to the checklist boxes in the PR description to address the presentation nit.

---

### Reflection

**What was harder than you expected?**
The git workflow around fixing commit messages was more friction than expected. Two commits were missing the required `(rag)` scope, and fixing them with `git rebase -i` was blocked by unstaged changes — which then required stashing, rebasing, and popping in the right order. I had read `CONTRIBUTING.md` before writing code but didn't internalize the commit message format until the self-review step, which was too late to avoid the rebase entirely. The mechanics weren't difficult in isolation, but stacking them under time pressure was.

**What did you learn about working in a large codebase?**
The biggest difference from building your own project is that the codebase already has opinions about everything — import order, docstring style, test structure, commit format — and you are responsible for matching them before you touch a single line of logic. In my own projects, `make check` failing is a signal to fix something. Here, `make check` failing with 50+ pre-existing violations means you have to first audit whether the failures are yours or the repo's, document the baseline, and make sure you don't add to the count. That due-diligence step doesn't exist when you own the whole codebase.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for three things: writing the initial implementation of `LLMReranker` and `build_reranker()` quickly while matching the project's existing patterns (structlog, openai SDK style, Google-style docstrings); drafting the PR description with the right level of detail; and catching that the PR needed to target `ascherj/pathreview` rather than my fork after I had already opened it in the wrong place. Where it fell short: it could not run the interactive rebase (`git rebase -i` is blocked in the tool), could not actually call the Groq API to verify the prompt worked end-to-end, and could not tell me from the start that my draft PR was going to the wrong repo — I had to look at another student's PR to figure that out.

**What would you do differently if you started over?**
Read `CONTRIBUTING.md` before writing the first commit, not before opening the PR. The commit scope convention (`feat(rag):` not `feat:`) is the kind of thing that costs 30 seconds to learn up front and 20 minutes to fix after the fact. I would also open the draft PR to the upstream repo on day one of the week, post in the course channel immediately, and tag a specific classmate rather than waiting for someone to notice it. Peer feedback arrived late because I posted late, not because classmates were unavailable.

**What are you most proud of from this module?**
The safety design of the reranker. `build_reranker()` returning `None` when `GROQ_API_KEY` is unset, the LLM failure path falling back to the original blended score rather than dropping the chunk, scores clamped and out-of-range values routed to fallback rather than silently becoming 1.0, and no new dependency added because the existing `openai` SDK already speaks Groq's API. The reviewer called these four decisions out specifically as things that mean the feature "can't break retrieval for anyone who doesn't turn it on." That was the goal from the start, and it held up under review.
