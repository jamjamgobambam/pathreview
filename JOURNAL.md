## Week 7 — Issue selection

**Issue link:** 
https://github.com/ascherj/pathreview/issues/36

**Issue title:** 
Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Why this issue / tier fit:**
I'm still getting oriented in the pathreview codebase, so I picked a Tier 1 issue on purpose rather than jumping into scoring or retrieval logic I don't fully understand yet. The scope is only limited to docs-only (`docs/ARCHITECTURE.md`). This does not require any editing of the project code base so it is low-risk to get wrong. This forces me to actually read and understand the hybrid retrieval scoring code well enough to explain it which is a good on-ramp before I try to modify that code directly in a later issue. The deliverable is to document the formula, default weights, and one worked example into ARCHITECTURE.md. This is a good match for my current comfort level with the codebase.

**Problem summary:**
The Issue
The docs/ARCHITECTURE.md file mentions that the hybrid retrieval system blends vector and keyword scores, but it fails to explain how this blending actually works.

What's Missing
The documentation currently lacks the specific mathematical formula used for the scoring logic, as well as the default weights assigned to the vector and keyword components.

What a Successful Fix Accomplishes
A successful update will provide developers with a clear, dedicated section explaining the exact scoring logic, complete with a concrete, step-by-step example. This will eliminate ambiguity, detail the default configuration, and make the hybrid search behavior fully transparent and reproducible.

**Branch name:** 
docs/36-Architecture-doc-doesn't-explain-the-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/jung8027/pathreview/commit/2c559c2d159027682e053952af970d652e66e969

**Reproduction summary:**
To reproduce the issue, I inspected the hybrid retrieval scoring implementation in rag/retriever/hybrid.py and compared it against docs/ARCHITECTURE.md. I observed that while docs/ARCHITECTURE.md describes hybrid retrieval as using vector similarity and BM25 keyword search, it lacks the specific blending formula (vector_weight * normalized_vector_score + keyword_weight * normalized_keyword_score), normalization details, and default weights (0.7 vector / 0.3 keyword). Additionally, I noted a runtime behavior bug where _get_all_chunks retrieves all chunks but fails to pass them to keyword_searcher.index() prior to searching, causing keyword scores to be empty unless indexed elsewhere.

**PLAN.md link:**
https://github.com/jung8027/pathreview/blob/docs/36-Architecture-doc-doesn't-explain-the-hybrid-retrieval-scoring-formula/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

**Scoring logic notes (research for the fix):**

`docs/ARCHITECTURE.md` currently says hybrid retrieval "fetches relevant context from the user's ingested documents" via "vector similarity + BM25 keyword" search, but stops there — it never states the blending formula or the default weights. This is the gap issue #36 asks to close. Below is what I found reading `rag/retriever/hybrid.py`, to carry over into the ARCHITECTURE.md update.

*The formula* (`HybridRetriever.retrieve`, [hybrid.py:78-81](rag/retriever/hybrid.py#L78-L81)):

```
blended_score = vector_weight * normalized_vector_score + keyword_weight * normalized_keyword_score
```

Each side is normalized to 0–1 before blending by dividing by the max score seen in that result set ([hybrid.py:58-59](rag/retriever/hybrid.py#L58-L59)):
- `normalized_vector_score = vector_score / max(vector_scores)`
- `normalized_keyword_score = bm25_score / max(bm25_scores)`

If a chunk was only returned by one of the two searches, the other side's score is treated as 0 rather than excluded.

*Default weights* ([hybrid.py:13-14](rag/retriever/hybrid.py#L13-L14)): `vector_weight=0.7`, `keyword_weight=0.3` — vector similarity dominates the ranking by default, keyword match is a secondary signal.

*Worked example:* query returns three candidate chunks:

| Chunk | Vector score | Normalized vector | BM25 score | Normalized keyword | Blended (0.7 / 0.3) |
|---|---|---|---|---|---|
| A (in both) | 0.90 | 0.90/0.90 = 1.00 | 8.0 | 8.0/8.0 = 1.00 | 0.7×1.00 + 0.3×1.00 = **1.00** |
| B (vector only) | 0.60 | 0.60/0.90 = 0.67 | — | 0 | 0.7×0.67 + 0.3×0 = **0.47** |
| C (keyword only) | — | 0 | 4.0 | 4.0/8.0 = 0.50 | 0.7×0 + 0.3×0.50 = **0.15** |

With the default `min_score=0.3` ([hybrid.py:29](rag/retriever/hybrid.py#L29)), chunk C would be filtered out entirely — it only cleared the bar because keyword_weight is small, which illustrates why the default weighting favors vector-only or both-matched chunks over keyword-only matches.

Note for the fix: `_get_all_chunks` fetches every chunk in the collection but its result is never passed into `keyword_searcher.index()` before `.search()` is called, so keyword scores may currently be empty at runtime unless the searcher was indexed elsewhere beforehand. Worth flagging separately since it's a behavior bug, not a docs gap — but it explains why the "keyword" half of hybrid search may look inactive when testing manually.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
1. Nothing have been written into ARCHITECTURE.md yet.
2. PLAN.md has been written and being reviewed.

**Next steps:**
1. complete JOURNAL.md
2. follow PLAN.md and write into ARCHITECTURE.md

**Blockers:**
1. Discovered a bug while reviewing the code.
2. Asked for advice on how to proceed and report it.

---

### Check-in 2 (end of week)

**PR link:**
https://github.com/ascherj/pathreview/pull/494

**Branch:**
docs/36-Architecture-doc-doesn't-explain-the-hybrid-retrieval-scoring-formula

**What you built:**
1. Analyzed the specific blending formula used
2. Written down the information into the JOURNAL.md
3. Compiled actionable steps in PLAN.md
4. Finished by writing the missing information into ARCHITECTURE.md

**PR description (mirrors the template filled out on GitHub):**

*Summary:* Documents the hybrid retrieval scoring formula in `docs/ARCHITECTURE.md` — the blend formula, score normalization, default weights, and a worked example — so the scoring behavior of `HybridRetriever` is fully reproducible from the docs alone, without reading `rag/retriever/hybrid.py`.

*Issue:* Closes #36 — `docs/ARCHITECTURE.md` mentioned that hybrid retrieval blends vector and keyword scores but never explained how the blending works.

*Changes:*
- Added a new "Hybrid Retrieval Scoring" subsection under RAG System in `docs/ARCHITECTURE.md`
- Documented the blend formula: `blended_score = vector_weight * normalized_vector_score + keyword_weight * normalized_keyword_score`
- Documented score normalization (divide by the max score in each result set) and the zero-score fallback for chunks matched by only one search method
- Documented the default weights (`vector_weight=0.7`, `keyword_weight=0.3`) and what they mean for ranking behavior
- Added a worked example with three candidate chunks (matched by both, vector-only, keyword-only) showing normalized and blended scores
- Noted the `min_score` filtering interaction, and flagged the `_get_all_chunks`/`keyword_searcher.index()` runtime bug found during reproduction as a known limitation, out of scope for this docs fix

*Notes for Reviewers:* The "Known limitation" callout about `keyword_searcher.index()` never being called on `_get_all_chunks` output is informational only; happy to split it into a separate follow-up issue if preferred. No production code was changed.

**Tests added or updated:**
This is a documentation-only change (issue #36 scope), so no new automated tests were added. The equivalent verification performed:
1. Re-read `docs/ARCHITECTURE.md`'s new "Hybrid Retrieval Scoring" subsection line-by-line against the live source it describes, confirming each claim against a specific reference: the blend formula against `HybridRetriever.retrieve` ([hybrid.py:78-81](rag/retriever/hybrid.py#L78-L81)), the normalization step against [hybrid.py:58-59](rag/retriever/hybrid.py#L58-L59), the default weights against [hybrid.py:13-14](rag/retriever/hybrid.py#L13-L14), and the `min_score` filtering behavior against [hybrid.py:29](rag/retriever/hybrid.py#L29).
2. Re-derived the worked example's three rows (both-matched, vector-only, keyword-only) by hand from the formula to confirm the blended scores in the doc's table (1.00 / 0.47 / 0.15) are arithmetically correct.
3. Ran `make check` and `make test-unit` to confirm this branch introduces no new failures beyond what already exists on `main` (see Self-review confirmation below).

**Self-review confirmation:**
Ran `make check` and `make test-unit` locally before opening the PR. Both fail, but only on pre-existing, unrelated issues — neither failure touches `docs/ARCHITECTURE.md` or anything else this branch changed:
- `make check`: [ ] fails at the `lint` step — 182 pre-existing `ruff` errors (e.g., `F841` unused-variable warnings in `tests/unit/test_tech_detector.py`). Reproducible on `main` before this branch's commits, so unrelated to this change.
- `make test-unit`: [ ] fails with 53 pre-existing failures (375 passing) in files unrelated to this change (`test_review_service.py`, `test_resume_parser.py`, `test_pii_scrubber.py`, etc.). None are in `docs/` or reference the hybrid retriever.
- This branch's diff is limited to `docs/ARCHITECTURE.md`, `JOURNAL.md`, and `PLAN.md` — no Python source changed, so it cannot have caused any of the above failures.

**Draft PR feedback received from:**
none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
I had to use AI to explain and break down the codebase to extract the exact blending formula from `HybridRetriever.retrieve` in [hybrid.py:78-81](rag/retriever/hybrid.py#L78-L81), since the normalization step and the score-fallback behavior for single-source matches weren't obvious from a quick read. While tracing through that logic I also found that `_get_all_chunks` never passes its results into `keyword_searcher.index()`, an undocumented runtime bug outside the scope of my docs-only issue. Deciding how to report that bug without scope-creeping my PR took more thought than the actual documentation work.

**What did you learn about working in a large codebase?**
Following the contribution guidelines closely — branch naming, PR templates, and commit conventions — mattered more than I expected, since a mismatch there could have blocked review before anyone even looked at the content. I also learned to always cross-reference documentation claims against specific line numbers in the source (e.g., citing [hybrid.py:13-14](rag/retriever/hybrid.py#L13-L14) for the default weights) rather than paraphrasing from memory, since that traceability is what lets a reviewer or future contributor trust the docs without re-deriving the formula themselves.

**How did AI tools help — and where did they fall short?**
AI was useful for quickly explaining what `HybridRetriever.retrieve` was doing structurally, but its first explanation of the normalization step was incomplete — it described dividing by the max score without mentioning that a chunk matched by only one search method gets the other side's score treated as 0 rather than excluded, which I only caught by re-reading [hybrid.py:58-59](rag/retriever/hybrid.py#L58-L59) myself. I had to manually verify every number in my worked example by hand-deriving the three blended scores (1.00 / 0.47 / 0.15) rather than trusting AI's arithmetic, since it initially miscalculated the keyword-only row before I corrected it against the formula.

**What would you do differently if you started over?**
I would read the CONTRIBUTING doc and learn the commit message and rebase conventions before starting, instead of discovering the correct commit-message format midway through and having to rebase to fix earlier commits. I'd also open a separate GitHub issue for the `keyword_searcher.index()` bug as soon as I found it, rather than only noting it in the PR description, so it gets tracked and prioritized independently of my docs fix.

**What are you most proud of from this module?**
I'm most proud of documenting my planning and reasoning clearly across JOURNAL.md and PLAN.md — especially cross-referencing every claim in ARCHITECTURE.md back to specific line numbers in hybrid.py, which made the doc verifiable rather than just asserted. I'm also proud of learning to use `git rebase` to clean up my commit history, since that's a skill I hadn't needed before this module and now feel comfortable using.