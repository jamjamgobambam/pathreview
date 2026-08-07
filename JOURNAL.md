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

**PR link:** [https://github.com/ascherj/pathreview/pull/862](https://github.com/ascherj/pathreview/pull/862)

**Branch:** `fix/34-re-ranking-LLM-retriever-step`

**What you built:**
I built a mandatory second layer to the chunking algorithm within the RAG feature of this project. This new layer uses an LLM to reranker retrieved chunks in order of relevance. I also implemented a mock reranker that permits the layer to run without connection to a network/LLM API.

**Tests added or updated:**
I added tests in their own separate file for the reranker under the name `test_reranker.py`. The test suite utilized a non-network reliant mock client and data to probe reranker behavior in various scenarios and edge cases.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No feedback was received.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
I found it harder than I expected to wrap my head around how the issue code fit into the project as a whole. Specifically, when it came to testing, I had to really take my time to understand what problems arose from my specific issue and not others, to avoid scope-creep. 

**What did you learn about working in a large codebase?**
Working in a large codebase takes a lot of mindful backtracking. When it is your own personal project, which you built from the ground up, it is easier to isolate issues as you know how each part is set up. Although, joining and contributing to a large codebase invites a lot of unknowns that requires you to need to take the time to figure out how one change might impact other parts of the project.

**How did AI tools help — and where did they fall short?**
I utilized AI tools to help build out the integration of my code into the current chunking pipeline of the rag system. I wanted to ensure that I was covering all my bases in terms of files and functions I would need to alter. I had to take things into my own hands when it came to testing decisions as the AI hoped to push fixes into other sectors outside my concern.

**What would you do differently if you started over?**
If I could start over, I would change my approach to how I went about planning. I did not build out my steps very detailed and I think this made me do more work than I anticipated in the actual build process. Whereas if I made it more detailed, it would have streamlined the creation process with clear steps and expectations.

**What are you most proud of from this module?**
I am proud of how I was able to take everything I have learned and genuinely implement it into this project. It felt like a full-circle moment and I look forward to what I will be capable of following this class.