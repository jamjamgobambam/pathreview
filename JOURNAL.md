## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/24

**Issue title:** Hybrid retriever over-weights keyword results when query contains technology names

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Issue #24 is about how the app decides which resume/README chunks are "relevant" to a search. Right now it always weighs two signals — meaning-based matching and exact keyword matching — by the same fixed amount, no matter what you search for. The problem is that words like "React" or "Python" show up a lot in both resumes and READMEs, so when someone searches for a tech name, the keyword-matching signal overpowers the meaning-based one and pulls in chunks from the wrong document. A good fix would make the app rely less on keyword matching when the search includes a common tech name, so it picks results based on actual relevance instead of just word overlap. This lives in the retrieval code (rag/retriever/hybrid.py), the part of the app that decides what information gets pulled in before an answer is generated.

**Branch name:** fix/24-hybrid-retriever-keyword-weighting

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/GutamaKev/pathreview/commit/ac93e56

**Reproduction summary:**
Reproduced by writing a unit test (`tests/unit/test_hybrid_retriever.py`) that indexes a resume chunk genuinely describing Python/React work alongside a README chunk that just repeats "Python React" several times, then queries for the candidate's Python/React experience. Confirmed the keyword-stuffed README chunk outranked the genuinely relevant resume chunk, because `hybrid.py` normalized BM25 scores by dividing by the batch's own max score, letting the repeated-term chunk set the scale for the whole result set.

**PLAN.md link:** https://github.com/GutamaKev/pathreview/blob/fix/24-hybrid-retriever-keyword-weighting/PLAN.md


**Blockers or open questions:**
None currently — the reproduction test now passes after switching the blend from batch-max normalization to weighted Reciprocal Rank Fusion (RRF), and the fix is committed and pushed. Still open: whether the RRF `k=10` constant needs further tuning against real (non-hand-built) profile data before this ships.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 7 sub-tasks from `PLAN.md`'s Plan section are implemented and committed (`ac93e56`, pushed to `fix/24-hybrid-retriever-keyword-weighting`): the `_rank_map()` helper, the weighted RRF blend replacing batch-max normalization, `k=10` with worst-rank handling for chunks missing from one side, the `_tokenize()` punctuation fix, removal of the `xfail` marker (test now genuinely passes), both retriever test suites verified green, and a new test confirming keyword matching still wins for an exact rare-term case. Baseline established and compared: `make test-unit` has 53 pre-existing failures unrelated to this issue, identical before and after this change (verified via `git stash`); repo-wide `ruff`/`black`/`mypy` also have substantial pre-existing debt entirely outside the files this PR touches. Self-review against `docs/CONTRIBUTING.md` is complete — everything conforms except the commit message is missing its Conventional Commits `(scope)` segment (`fix: ...` instead of `fix(rag): ...`); decided to leave it as-is rather than rewrite pushed history.

**Next steps:**
Draft PR is open (https://github.com/ascherj/pathreview/pull/1024) — request peer/mentor review via the course Slack channel, address feedback, then mark ready for review and submit the branch URL to the course portal.

**Blockers:**
None currently — resolved a GitHub CLI authentication issue (a stale `GITHUB_TOKEN` env var was overriding normal login) and the draft PR is now open.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1024

**Branch:** fix/24-hybrid-retriever-keyword-weighting

**What you built:**
Replaced `HybridRetriever`'s per-batch max-score normalization with weighted Reciprocal Rank Fusion (RRF), so a chunk that inflates its own BM25 score by repeating query terms (e.g. tech names) can no longer set the normalization scale for the whole result batch. Also fixed `KeywordSearcher._tokenize()` to strip punctuation around tokens (so "Python," and "React." match query terms) without breaking tokens like "c++"/"node.js", and made tie-breaking deterministic instead of depending on Python's hash-randomized set iteration order.

**Tests added or updated:**
`tests/unit/test_hybrid_retriever.py` — removed the `xfail` marker on the issue #24 regression test (now genuinely passes); added `test_keyword_match_breaks_a_near_tied_vector_ranking` (confirms an exact rare-term keyword match still wins over a near-tied vector competitor, so RRF doesn't overcorrect into vector-only ranking); added `test_tied_scores_break_deterministically_by_id` (confirms identical ordering across repeated calls on tied scores). `tests/unit/test_keyword_search.py` verified unchanged/still passing (19/20; the 1 pre-existing failure is an unrelated `ZeroDivisionError` in the `rank_bm25` library on an empty corpus).

**Self-review confirmation:** [x] make check passes (on files changed in this PR — repo-wide pre-existing debt documented above) [x] make test-unit passes (378 passing, 53 pre-existing failures unrelated to this change, identical before/after)

**Draft PR feedback received from:** _pending — draft PR not yet opened_