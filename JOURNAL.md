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

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1025

**Branch:** `feat/34-llm-reranker`

**What you built:**
An optional LLM-based reranker for `HybridRetriever`. `Reranker.rerank()` batch-scores
retrieved chunks against the query in one LLM call and uses that score to override the
blended vector/keyword ranking for final ordering, falling back to the original
blended order if the LLM call fails or its response can't be parsed.

**Tests added or updated:**
- `tests/unit/test_reranker.py` (new): 9 tests covering reordering by LLM score,
  fenced-JSON and raw-JSON parsing, fallback on LLM error, fallback on unparseable
  response, empty input, `top_k` truncation, missing chunk ids, call parameters
  (temperature/model), and prompt truncation for long chunk text.
- `tests/unit/test_hybrid_retriever.py` (updated): added a second test class
  proving the reranker fixes the exact decoy-outranks-genuine gap demonstrated in
  the Week 8 reproduction test, plus a test confirming graceful fallback to blended
  order when the LLM call fails.

Verified via a before/after full-suite comparison (last commit before this week's
work vs. now, run in an isolated worktree): 53 pre-existing failures, unrelated to
this issue, identical count before and after. This PR adds 11 new passing tests and
introduces zero new lint or type errors in any file it touches.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both pass for every file this PR touches; pre-existing repo-wide lint/mypy/test
failures are documented above and in the PR's "Notes for Reviewers" section, and
this PR does not add to them)

**Draft PR feedback received from:** none (reviewer feedback is not a feature in
Summer 2026 per course note; peer/mentor review not obtained before marking ready)

## Week 10: Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No, still awaiting review

**Summary of feedback:**
No feedback arrived. Reviewer feedback is not a feature in Summer 2026 per the
course note, so this is expected rather than a stalled review.

**How you responded:**
N/A, no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Reproducing this issue took more digging than I expected, because the bug wasn't
where the issue description implied. Before I could even write a repro, I had to
trace `HybridRetriever.retrieve()` through to `review_generator.py` and
`review_service.py`, and discovered the retriever had zero callers anywhere in the
app. The RAG pipeline was a stub returning hardcoded feedback. That reframed the
whole task: I wasn't reproducing a live bug users would hit, I was reproducing a
gap in an isolated, unwired module. Separately, the tooling threw a real curveball
late in Week 9: my PR creation failed with a cryptic GitHub error, and it turned
out `shraavb/pathreview` had never been a properly registered GitHub fork of the
upstream repo, just an independently pushed copy. Fixing that meant renaming the
old repo, creating a real fork, and re-pushing branches, a repo administration
problem I didn't expect to hit this late.

**What did you learn about working in a large codebase?**
You can't trust an issue's framing at face value. I had to verify the claim myself
by tracing the actual call graph, and it turned out to be narrower in scope than
the issue implied. I also learned to check existing test conventions before writing
new ones (matching `test_relevance_scorer.py`'s fixture style) and to distinguish
similarly named but unrelated code (`rag/evaluator/relevance_scorer.py` vs. the
reranker) before assuming reuse. Small pre-existing issues (a dead `all_chunks`
variable, missing type annotations, an invalid commit scope) surface constantly in
real codebases, and part of the job is deciding what's in scope to fix versus what
to leave alone and just document.

**How did AI tools help, and where did they fall short?**
AI was most useful for mechanical and investigative work: tracing which files
called `HybridRetriever`, matching exact mock return shapes to real method
signatures, running before/after test suite comparisons in an isolated worktree,
and researching current OpenRouter free tier model availability. It fell short on
the judgment calls that actually shaped the design: choosing a domain appropriate
reproduction pair (leadership/bakery vs. a generic example), deciding whether the
LLM score should replace or blend with the existing score, and deciding what
config pattern fit this specific codebase's conventions. Those needed my reasoning
and preferences, not just generation.

**What would you do differently if you started over?**
I'd verify the fork was properly registered with GitHub in Week 7, before any work
went into it. That mistake didn't surface until I tried to open a PR in Week 9, by
which point fixing it meant repo surgery instead of a five minute setup check. I'd
also trace the actual call graph (is this retriever even wired into the app?)
before finalizing my problem summary in Week 7, since it changed how I scoped the
whole issue.

**What are you most proud of?**
The reproduction test itself: building a concrete, domain realistic failure case
(a bakery shift scheduling chunk outranking a genuine leadership chunk) that
isolates exactly why the current scoring approach fails, rather than a vague
"sometimes retrieval is bad" claim. It's the kind of test that makes the bug
undeniable to a reviewer instead of asking them to trust a description.
