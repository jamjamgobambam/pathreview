# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In the RAG system, the faithfulness checker assumes every retrieved context chunk has string text, so a chunk with `text: None` throws an error instead of being handled. A successful fix would skip or safely handle null-text chunks so the check runs without crashing.

**Branch name:** fix/153-faithfulness-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Is this right for me?
- Scope is small and isolated to one RAG check, so it fits a Tier 1 effort.
- The bug is a clear null-handling case with an obvious success condition (no crash).


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/maanyaS/pathreview/commit/774f9f7d7b50022ad0670a6ca0c453c5ba6c7343

**Reproduction summary:**
I ran the issue's one-liner against my local venv — `FaithfulnessChecker().check("Knows Python.", [{"text": None}])` — and got the exact reported `TypeError: sequence item 0: expected str instance, NoneType found` at `rag/evaluator/faithfulness_checker.py:43`, and the repo's existing `test_none_context_chunk_text` fails with the same error. It reproduces every run: `dict.get("text", "")` only falls back to `""` for a *missing* key, so a present-but-`None` value flows straight into `" ".join(...)` and blows up. I committed a comment at the exact failing line documenting the trace and the repro command.

**PLAN.md link:** https://github.com/maanyaS/pathreview/blob/fix/153-faithfulness-none-text-crash/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
- No blockers — the fix itself is a few lines. The open design question is whether silently skipping a null chunk is right, since it turns a loud crash into a quietly lower faithfulness score. I plan to log when the assembled context ends up empty so it's still diagnosable, but I'd like a mentor's read on that.
- `relevance_scorer.py:32` uses the identical `chunk.get("text", "")` idiom and has the same latent crash. I'm leaving it out of this PR to keep the scope on #153 and will flag it in the PR description — worth confirming that's the preferred call.
- Still unsure whether `text: None` is itself a symptom of an upstream ingestion/chunker bug rather than just bad caller input.