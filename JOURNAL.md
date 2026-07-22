## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker's `check()` method builds context text by pulling the `"text"` key out of each context chunk using `chunk.get("text", "")`. This works fine when the key is missing entirely, since `.get()` falls back to an empty string — but it breaks when the key exists and is explicitly set to `None`, because `.get()` only applies its default for missing keys, not for keys with a `None` value. When that happens, the code tries to join a list of strings that includes a `None`, which raises a `TypeError` and crashes the checker. A successful fix will treat a chunk with `text: None` the same as an empty or missing chunk, so the faithfulness check can run without crashing on this edge case, and the existing test `test_none_context_chunk_text` will pass.

**Branch name:** fix/153-faithfulness-none-context-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Scope reasoning:**
I chose a Tier 1 issue since this is my first time contributing to a large, unfamiliar codebase, and Tier 1 issues are scoped to a single file/function rather than requiring system-wide understanding. This issue is well-scoped: the bug is isolated to one function (`check()`) in one file (the faithfulness checker in `rag/`), the root cause is already clearly identified in the issue description, and there's an existing failing test I can use to verify my fix. I estimate this will take 3-6 hours of focused work, which fits comfortably within the Week 8-9 timeline. Several other students are also working on this issue, but since claims are non-exclusive and grading is based on my own submitted artifacts, that doesn't change my choice. There are no blockers or dependencies noted on the issue.