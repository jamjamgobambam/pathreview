## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/ARCHITECTURE.md` mentions that PathReview's retrieval step uses "hybrid retrieval" — blending vector similarity search with BM25 keyword scoring — but it never explains how the two scores are combined or what weights are applied by default. This makes the RAG pipeline's retrieval behavior opaque to anyone reading the architecture doc, especially new contributors trying to understand or tune retrieval quality. A successful fix adds a clear section to `docs/ARCHITECTURE.md` that walks through the scoring formula, states the default weight values, and includes a worked example showing how a document's final relevance score is calculated from its vector and keyword scores. The affected area is documentation only (`rag` module concepts), with no code changes required.

**Branch name:** docs/36-hybrid-retrieval-scoring-formula

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue checklist reasoning:**
This is a Tier 1 / "good first issue" labeled purely as documentation work — no code paths to modify, no tests to write or break, and a stated estimate of 2–3 hours. Scope is tightly bounded to one file (`docs/ARCHITECTURE.md`), which limits merge-conflict risk and review back-and-forth. The main prerequisite is actually locating the hybrid scoring logic in the `rag` module's code to describe it accurately rather than guessing, which I'll do before writing the doc update.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/oimahawong/pathreview/commit/968c806

**Reproduction summary:**
I traced the doc gap to `rag/retriever/hybrid.py` (`HybridRetriever.retrieve`) and confirmed the exact formula, default weights (`vector_weight=0.7`, `keyword_weight=0.3`), and `min_score=0.3` threshold that `docs/ARCHITECTURE.md` never mentions. I added an inline comment at the relevant line in `docs/ARCHITECTURE.md` documenting these specifics so the fix is grounded in the real implementation rather than guesswork.

**PLAN.md link:** https://github.com/oimahawong/pathreview/blob/docs/36-hybrid-retrieval-scoring-formula/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
I couldn't find any call site in the codebase that actually constructs `HybridRetriever(...)` outside its own file — no tests, no service-layer wiring located yet. I'm not yet certain the 0.7/0.3 defaults are the values used in production versus overridden somewhere I haven't found. I'll either track down the call site in Week 9 or document the weights explicitly as "constructor defaults" rather than confirmed production values.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix: added a "Hybrid Retrieval Scoring" subsection to `docs/ARCHITECTURE.md` covering the two signals, per-query normalization, the blend formula, the `min_score` cutoff, both edge cases (empty result set, single-method chunk), and a worked example (`0.7*0.8 + 0.3*0.4 = 0.68`). Re-confirmed there's no `HybridRetriever(...)` call site anywhere in the codebase, so the weights are documented explicitly as constructor defaults rather than confirmed production values, per the plan's fallback. Committed as `289069d`.

**Next steps:**
Run `make check` and `make test-unit` locally and confirm the change introduces no new failures (the codebase has pre-existing ruff/test failures unrelated to this change — docs-only edits can't touch them, and pre-commit's ruff/black/mypy hooks skipped with "no files to check" on this commit, confirming it). Then push, open a draft PR, and request peer/mentor review.

**Blockers:**
None. The Week 8 open question (whether 0.7/0.3 are confirmed production defaults) is resolved by documenting them as constructor defaults, per the plan's fallback — no call site was ever found.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]

