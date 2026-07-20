# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3
<!-- Confirmed from the issue's GitHub labels: bug, good first issue, rag, tier-1. -->

**Problem summary:**
The faithfulness checker's job is to check whether the feedback the system
generates is actually grounded in the retrieved context, instead of being made
up. Right now it crashes when one of the context chunks has its `text` value set
to `None`. The cause is in how the code builds the context string: our
`chunk.get("text", "")` call only defaults to an empty string when the `text`
key is missing entirely, so it doesn't account for the key being present with a
value of `None` — that `None` then gets passed into `" ".join(...)` and raises a
`TypeError`. A successful fix treats a `None` text value the same as an empty
string so the checker skips it instead of crashing, while keeping the scoring
behavior for normal chunks unchanged. I'll also add a regression test in
`tests/unit/test_faithfulness_checker.py` that covers the `text: None` case.

**Is this right for me? — scope reasoning:**
<!-- DRAFT — adjust to reflect your own reasoning after working the checklist. -->
- **Scope is small and contained:** the bug lives in one function in one file
  (`rag/evaluator/faithfulness_checker.py`), and the fix is a null-safety change.
- **I can reproduce and explain it:** the crash path is clear (`{"text": None}`
  → `" ".join` → `TypeError`), so I understand the root cause, not just the symptom.
- **There's a clear success signal:** a regression test in the existing
  `tests/unit/test_faithfulness_checker.py` that fails before the fix and passes
  after.
- **Low blast radius:** the change only affects how missing/None chunk text is
  handled; normal chunks behave exactly as before.

**Branch name:** `fix/153-faithfulness-none-chunk`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
<!-- Do this yourself: add your name, GitHub username (mayoayileka09), and issue
     #153 to your section's tab in the cohort ledger. -->
