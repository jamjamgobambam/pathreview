# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/153
<!-- ⚠️ VERIFY: replace with the exact URL from your browser's address bar on the
     issue page. This is my best guess based on the `upstream` remote. -->

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3
<!-- ⚠️ VERIFY: confirm the tier from the label on the GitHub issue itself.
     Marked Tier 1 because it's a small, single-file null-handling crash fix. -->

**Problem summary:**
<!-- DRAFT written from reading the code — read it, make sure you understand it,
     then rewrite it in your own voice before submitting. -->
The faithfulness checker in the RAG evaluation suite scores how well generated
feedback is actually supported by the retrieved context chunks. In
`rag/evaluator/faithfulness_checker.py`, it joins all the chunk texts together
with `" ".join([chunk.get("text", "") for chunk in context_chunks])`. The
`.get("text", "")` fallback only kicks in when the `text` key is *missing* — if
a chunk has the key present but set to `None`, `.get()` returns `None`, and
joining a list that contains `None` raises a `TypeError` that crashes the whole
check. A successful fix makes the checker treat a `None` chunk text the same as
an empty string (so it's skipped instead of crashing), keeps the existing
scoring behavior unchanged for normal chunks, and adds a regression test in
`tests/unit/test_faithfulness_checker.py` covering the `text: None` case.

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
