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
[Anything you're still uncertain about going into Week 9, or leave blank]