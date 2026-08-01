## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation
 #34

**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
This issue calls for another layer of chunk ranking in the retrieval step of the `rag` (Retrieval-Augmented Generation) portion of the codebase. Essentially, it requests the addition of a light-weight LLM ranker which will go above the current top-k chunk retrieval layer which only uses vector similarity and keyword scores. Once successfully added, this LLM-based enhancement to the retrieval process will strengthen the validity of top-k chunks, specifically in terms of their ranked relevance to the query.

**Branch name:** fix/34-re-ranking-LLM-retriever-step

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/neparkes-81/ai201-finalproject-pathreview/blob/fix/34-re-ranking-LLM-retriever-step/JOURNAL.md

**Reproduction summary:**<!-- [1–2 sentences: How did you reproduce the issue? What did you observe?] -->
This issue did not require reproduction as it is an enhancement, but I did run the code the visualize how it is currently functioning.

**PLAN.md link:** https://github.com/neparkes-81/ai201-finalproject-pathreview/blob/fix/34-re-ranking-LLM-retriever-step/PLAN.md

**Walkthrough video (recommended):** ...

**Blockers or open questions:** ...
<!-- [Anything you're still uncertain about going into Week 9, or leave blank] -->

*Note*: The current handling of chunks can be found in `rag/retriever/hybrid.py`. I gather how this process works and I will need to build upon the output of `_get_all_chunks()` to fill the issue gap.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
In terms of my `PLAN.md`, I completed the first 2 steps. These essentially consist of configuration and step up of my LLM reranker as a standalone entity.

**Next steps:**
Connecting my reranker to the entire rag pipeline, specifically through `hybrid.py`. Then, creating tests to validate code.

**Blockers:**
As the llm_provider defaults to "mock", in the case that this is to run offline I need to incorporate some sort of "MockReranker", something deterministic and doesn't require no network. Otherwise, my current code will run into errors. Also, I ran into linter errors so I need to clean up my code to align with anticipated style.

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