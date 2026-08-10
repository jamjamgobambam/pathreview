# PathReview: Module 3 Journal

## Week 7: Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The current retriever in `rag/retriever/hybrid.py` ranks chunks using only a blend of
vector similarity and keyword (BM25) scores, with no semantic judgment of whether a
retrieved chunk actually answers the query. This can surface chunks that score well
numerically but are only tangentially relevant, which degrades the quality of the
context passed to the generator. A successful fix adds an optional re-ranking pass,
a new `reranker.py` module, that takes the top-k chunks from the hybrid retriever and
uses a smaller/cheaper LLM to score each chunk's relevance to the query before the
top results are passed on to generation, improving the precision of what the model
actually sees.

**Selection notes ("Is this right for me?" checklist):**
- *Is it actually open?* Yes, no assignee, no linked PR yet. Several other cohort
  students have also commented interest; I claimed it knowing the work may end up
  overlapping and I'm fine building my own implementation regardless.
- *Is the scope clear?* Yes, the issue names the exact mechanism (LLM-scored
  re-ranking pass), the new file to add (`rag/retriever/reranker.py`), and the
  existing file it plugs into (`rag/retriever/hybrid.py`).
- *Is it the right size?* Tier-3, estimated 7 to 10 hours, touching one new file plus
  one integration point, larger than a starter issue but bounded, not sprawling
  across services.
- *Is the maintainer active?* Yes, the repo had commits pushed within the last day.
- *Does it match where I am?* Yes, this is core RAG/LLM-engineering work (prompting
  a model to score relevance), which is the skill area I want more depth in from
  this course, as opposed to a pure test-writing or docs issue.

**Branch name:** `feat/34-llm-reranker`

**Setup confirmation:** [x] App runs locally (frontend confirmed responding on
localhost:5173, after temporarily freeing the port from an unrelated local project's
container; backend confirmed on localhost:8000/docs)

**Cohort ledger:** [ ] Issue added to cohort ledger, *pending, add manually*

## Week 8: Reproduction & solution planning

**Reproduction commit link:** https://github.com/shraavb/pathreview/commit/e97eb8fa004acc98d3544e15f5d9a537fbac7a97

**Reproduction summary:**
Added `tests/unit/test_hybrid_retriever.py`, mocking `VectorStore` and `KeywordSearcher`
so `HybridRetriever.retrieve()` sees two candidate chunks for the query "leadership and
team management experience": a genuinely relevant chunk ("led a team of 4 engineers")
and a topically off-target decoy ("managed weekend shift schedule at campus bakery").
The decoy is given higher vector/keyword scores. Running the real `retrieve()` logic
confirms the decoy outranks the genuine match, proving `retrieve()` has no semantic
check to catch a chunk that merely shares vocabulary/embedding-space proximity with
the query but doesn't actually answer it.

**PLAN.md link:** https://github.com/shraavb/pathreview/blob/feat/34-llm-reranker/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
The RAG pipeline (`core/services/review_service.py`) is currently a stub and never
calls `HybridRetriever` in production, so the reranker will be correct but unwired
until that gets built out separately (see Risks & Unknowns in PLAN.md). Still deciding
whether the LLM relevance score should fully replace the blended vector/keyword score
or be combined as a third signal.

## Week 9: Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md's Plan section are implemented:
1. Designed the `Reranker` interface (`rerank(query, chunks, top_k)`), matching
   `HybridRetriever`'s constructor-injection style so it can be unit-tested with a
   mock client, the same way `HybridRetriever` is tested with mock stores.
2. Implemented the batch LLM scoring call in `rag/retriever/reranker.py`, reusing
   `output_parser.py`'s fenced-JSON parsing convention.
3. Resolved the score-handling question from PLAN.md: the LLM score replaces the
   blended score for final ordering, with a fallback to the original blended order
   if the LLM call fails or its response can't be parsed.
4. Wired `HybridRetriever` to optionally call the reranker between the blended-score
   sort and the `max_chunks` slice, gated behind an opt-in constructor param.
5. Added `tests/unit/test_reranker.py` (9 tests: reordering, JSON-fence parsing,
   fallback on error, fallback on unparseable response, empty input, `top_k`,
   missing-id handling, call parameters, prompt truncation) and extended
   `tests/unit/test_hybrid_retriever.py` with 2 tests proving the reranker fixes
   the exact decoy-outranks-genuine gap from the Week 8 reproduction.

Also resolved two open PLAN.md risks by comparing options directly: the reranker
reads config from `core/config.py`'s `Settings` singleton rather than a standalone
config class (matches how the rest of the app is built, and avoids adding a second
unused config pattern alongside the already-dead `ReviewConfig`), and added a
dedicated `reranker_model` setting so the reranker can use a smaller/cheaper model
independent of `openrouter_model`.

Ran a before/after comparison of the full test suite (Week 8's last commit vs. now,
via a throwaway worktree so the working tree stayed untouched): 53 pre-existing
failures unrelated to this issue, identical count before and after. My changes add
11 new passing tests and introduce no new failures. `make lint` and `make typecheck`
show zero errors in any file I touched; all existing errors are pre-existing and
outside this issue's scope.

**Next steps:**
Open a draft PR against `upstream` and request peer/mentor review in Slack before
marking it ready. Then address feedback, fill in the PR template, and submit.

**Blockers:**
None currently.
