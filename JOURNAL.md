## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/153]

**Issue title:** [Faithfulness checker crashes when a context chunk has text: None]

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[The Faithfullness Checker function crashes because there is no error checking. There should be adequate error checking in the function for when the text is set to None so that it fails gracefully. Fixing this bug will make for a better user experience.]

**Branch name:** [bug/153-faithfullnesschecker-crashes-when-text-none]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jocelynGonzalez/pathreview/commit/23dc974

**Reproduction summary:**
I called `FaithfulnessChecker.check("Has Python skills", [{"text": None}])` against the current code
and it raised `TypeError: sequence item 0: expected str instance, NoneType found` at
`rag/evaluator/faithfulness_checker.py:34`. The cause is `chunk.get("text", "")` — its `""` default
only applies when the key is missing, so a present-but-`None` value passes `None` into `" ".join(...)`.
A control chunk with the key missing (`{"content": ...}`) returned `0.0` without crashing, confirming
the crash is specific to an explicit `None`. The repo's own test `test_none_context_chunk_text`
(`tests/unit/test_faithfulness_checker.py:231`) encodes the expected graceful behavior and currently
fails with this same error.

**PLAN.md link:** https://github.com/jocelynGonzalez/pathreview/blob/bug/153-faithfullnesschecker-crashes-when-text-none/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Open question: the same unsafe `chunk.get("text", "")` / `chunk["text"]` pattern also exists in
`rag/evaluator/relevance_scorer.py`, `rag/generator/review_generator.py`, and
`rag/retriever/keyword_search.py`. I plan to keep #153 scoped to the faithfulness checker and raise
the others separately unless a mentor advises otherwise.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: in `rag/evaluator/faithfulness_checker.py`, changed the context
join to `(chunk.get("text") or "")` so a chunk whose `text` is `None` (or missing, or empty) is
treated as empty context instead of crashing `" ".join(...)`. Verified the previously-crashing case
now returns `0.0` and that a `None` chunk mixed with a valid chunk still scores the valid one.
Updated `tests/unit/test_faithfulness_checker.py`: tightened `test_none_context_chunk_text` to assert
`score == 0.0` and added `test_none_text_mixed_with_valid_chunk`. (PLAN sub-tasks 1–2, and 4, done.)

**Next steps:**
Run `make test-unit` and `make check` in a full dev environment to confirm no new failures (PLAN
sub-tasks 3 and 5), open a draft PR for peer/mentor review, then finalize.

**Blockers:**
None. (Still tracking the scope question about the sibling files noted in Week 8.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/918

**Branch:** `bug/153-faithfullnesschecker-crashes-when-text-none`

**What you built:**
Fixed `FaithfulnessChecker.check()` crashing with a `TypeError` when a retrieved context chunk had
`text: None`. The context join now uses `(chunk.get("text") or "")`, so a null/missing/empty chunk
text is treated as empty context and scoring proceeds gracefully instead of raising.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — tightened `test_none_context_chunk_text` to assert
`score == 0.0`, and added `test_none_text_mixed_with_valid_chunk` (a `None` chunk alongside a valid
one still scores the valid one).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_("Passes" = introduces no new failures. The repo has documented pre-existing failures — full unit
suite went from 53→52 failed after my change, which fixes one and adds one passing test; ruff/mypy
have pre-existing findings repo-wide but my changed lines add none and `faithfulness_checker.py`
type-checks cleanly. Details in the PR's "Notes for Reviewers".)_

**Draft PR feedback received from:** none yet — draft PR shared in cohort Slack for peer review

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
There was no feedback provided. 

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
For me, working with a large code base where I am unfamiliar with the code was harder than expected. The ticket I chose did make it easier to find the bug as it was specific to the function, but I later found other bugs related to the same function. 

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
I learned that there are many ways to do one task and it's a good way to learn about different implementations/approaches. It was also difficult to get an understanding of how someone else structures their code. 

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
Claude helped me get a good understanding/overview of the code repo without me having to sift through everything. For this simple task, it didn't lack many skills and performed fairly well.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I would have chosen a slightly harder problem as I am already familiar with working on large code bases to give myself an extra challenge. 

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I am proud of learning how to efficiently use AI to help me navigate an unfamiliar code repo. I think this is a valuable skill to have and makes me a faster developer. 