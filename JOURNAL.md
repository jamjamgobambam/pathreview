# Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/153]

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [✓] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There is a bug that occurs when the faithfulness checker receives a chunk of text, where the text is the key but the value is `None`. The broken behavior stems from `chunk.get("text", "")`​ because it only uses the empty string when the key is missing. However, if the key has the value `None`​, it returns `None`​ but later fails because `" ".join(...)` expects strings. A successful fix should result in the faithfulness checker being able to handle both missing and empty chunk text without crashing and continue with its evaluation.

**Branch name:** [fix/153-faithfulness-none-text]

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue](https://github.com/ascherj/pathreview/commit/5b47b1e28e418f09d4f1f9c5c9a833feff0e1161)

**Reproduction summary:**
I created a script that called `FaithfulnessChecker().check()` with a context chunk that contained `{'text': None}`. This raised  `TypeError: sequence item 0: expected str instance, NoneType found`.

**PLAN.md link:** [link to PLAN.md in your fork](https://github.com/Namisa-Mbayo/pathreview/blob/fix/153-faithfulness-none-text/Plan.md)
