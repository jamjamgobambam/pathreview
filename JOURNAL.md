## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker's `check()` method builds its context string using
`chunk.get("text", "")`, which only substitutes an empty string when the
`text` key is missing — not when it's present but set to `None`. When a
context chunk has `text: None`, `.get()` returns `None`, and the subsequent
`" ".join()` call raises a `TypeError`, crashing the safety-layer's
faithfulness check entirely. A successful fix normalizes `None` values to
empty strings at this boundary, since the checker sits in the RAG
evaluation layer and shouldn't assume its inputs are always well-formed.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/batyrkhan9/pathreview/commit/59e4cba6e746810a266a572801d1c517a01d370e

**Reproduction summary:**
The bug was reproduced by inspecting the original implementation before my
Week 7 fix: `chunk.get("text", "")` only supplies the default when the key
is missing, so a chunk with `text: None` caused `" ".join()` to raise
`TypeError: sequence item 0: expected str instance, NoneType found`. This is
documented in the diff of commit 59e4cba, which shows the original buggy
line and the corrected version.

**PLAN.md link:** https://github.com/batyrkhan9/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** (skipped — not graded)

**Blockers or open questions:**
Not yet sure why some chunks end up with `text: None` upstream — treating
it as an unknown for now and guarding at the checker boundary.