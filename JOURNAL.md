## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

This is my first time resolving a bug in a large codebase, so I'm starting with Tier 1, which is a
self-contained fix in one file that I could fully trace and reproduce before claiming it.

**Problem summary:**
The issue occurs in the rag/evaluator/faithfulness_checker.py when a context chunk contains a text field with the value None. The current implementation assumes every text value is a string, so joining the context raises a TypeError instead of handling the missing content gracefully. A successful fix will ensure that None values are treated as empty strings (or otherwise ignored), preventing the crash while allowing the faithfulness check to continue. The related unit test should also pass after the fix.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
I reproduced issue #153 by running:

```python
from rag.evaluator.faithfulness_checker import FaithfulnessChecker

FaithfulnessChecker().check("Knows Python.", [{"text": None}])
```
The program throws:

```python
TypeError: sequence item 0: expected str instance, NoneType found
```
![alt text](<Pasted Graphic.png>)

This occurs because chunk.get("text", "") returns None when the key exists with a None value, causing " ".join() to fail since the check() function only accepts string type.

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]