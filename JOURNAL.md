# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The current retriever in `rag/retriever/hybrid.py` ranks chunks using only a blend of
vector similarity and keyword (BM25) scores, with no semantic judgment of whether a
retrieved chunk actually answers the query. This can surface chunks that score well
numerically but are only tangentially relevant, which degrades the quality of the
context passed to the generator. A successful fix adds an optional re-ranking pass —
a new `reranker.py` module — that takes the top-k chunks from the hybrid retriever and
uses a smaller/cheaper LLM to score each chunk's relevance to the query before the
top results are passed on to generation, improving the precision of what the model
actually sees.

**Selection notes ("Is this right for me?" checklist):**
- *Is it actually open?* Yes — no assignee, no linked PR yet. Several other cohort
  students have also commented interest; I claimed it knowing the work may end up
  overlapping and I'm fine building my own implementation regardless.
- *Is the scope clear?* Yes — the issue names the exact mechanism (LLM-scored
  re-ranking pass), the new file to add (`rag/retriever/reranker.py`), and the
  existing file it plugs into (`rag/retriever/hybrid.py`).
- *Is it the right size?* Tier-3, estimated 7–10 hours, touching one new file plus
  one integration point — larger than a starter issue but bounded, not sprawling
  across services.
- *Is the maintainer active?* Yes — the repo had commits pushed within the last day.
- *Does it match where I am?* Yes — this is core RAG/LLM-engineering work (prompting
  a model to score relevance), which is the skill area I want more depth in from
  this course, as opposed to a pure test-writing or docs issue.

**Branch name:** `feat/34-llm-reranker`

**Setup confirmation:** [x] App runs locally (frontend confirmed responding on
localhost:5173 — after temporarily freeing the port from an unrelated local project's
container; backend confirmed on localhost:8000/docs)

**Cohort ledger:** [ ] Issue added to cohort ledger — *pending, add manually*
