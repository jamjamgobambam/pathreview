## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/24

**Issue title:** Hybrid retriever over-weights keyword results when query contains technology names

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is that the keywords are being matched incorrectly and the model will return irrelevant chunks from the wrong document because of similar wordings. What is currently broken is the RAG retrieval system in `rag/retriever/hybrid.py` and a successful fix would be that the correct chunks are being returned for the model to use.

**Branch name:** fix/24-hybrid-retriver

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/scnoder/pathreview/commit/0c6168bc2fd051bd759f4422745c6aa4924a5a7b

**Reproduction summary:**
I reproduced the issue by uploading my own resume. There didn't seem to be much errors however, there were some slight variability for the same resume across different accounts.

**PLAN.md link:** https://github.com/scnoder/pathreview/blob/fix/24-hybrid-retriever/PLAN.md

**Blockers or open questions:**
I am still uncertain about where the error exactly is and what type of logic error it is.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have looked through `hybrid.py` and I have deduced what the error might be. I have located possible locations to fix this error as well.

**Next steps:**
I am working on narrowing down the location and fixing the error. I plan to have this done by the end of the week.

**Blockers:**
Since this is a logic error, there are many places where the error could reside.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
I touched `hybrid.py` and `keyword_search.py` because the focus on the BM25 scoring which is what the model uses to run.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]