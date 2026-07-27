## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `check()` method in `FaithfulnessChecker` builds its context by calling
`chunk.get("text", "")` on each context chunk, assuming this will fall back to
an empty string if text is missing. However, `.get()` only applies its default
when the key itself is absent — if a chunk has `"text": None`, `.get()` returns
`None` instead. This value then gets passed into a `" ".join(...)` call, which
raises a `TypeError` because `join()` expects a list of strings, not `None`.
The fix involves handling the case where `text` is present but `None`, likely
by falling back to an empty string in that case too. This affects the
`rag/evaluator/faithfulness_checker.py` module.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Checklist reasoning ("Is this right for me?"):**

*Part 1 — Understanding the issue:* Yes. The bug is that `check()` calls
`chunk.get("text", "")`, but `.get()` only applies its default when the key
is missing — if a chunk has `"text": None`, `.get()` returns `None` instead
of falling back to `""`. That `None` then gets passed into `" ".join(...)`,
which raises a `TypeError` because `join()` requires a list of strings.
Before the fix: passing a chunk with `text: None` crashes the checker.
After the fix: it should handle `None` the same way it handles a missing
key, treating it as empty text instead of raising.

*Part 2 — Tier fit:* This is my first open-source contribution, and #153
is labeled Tier 1 — a localized, single-method fix in one file. Good match
for where I am right now.

*Part 3 — Codebase readiness:* I opened
`rag/evaluator/faithfulness_checker.py` and read the `check()` method
directly, not just the file listing. I also opened
`tests/unit/test_faithfulness_checker.py` and read through
`test_none_context_chunk_text` (and at least one other test) to see how
the test fixtures and assertions are structured, so I know the pattern
to follow for my own test.

*Part 4 — Scope and time:* I checked the issue comments and the Claims
count in the cohort ledger's Issue Catalog tab before claiming. The fix
itself is small (one conditional or a safer `.get()` pattern), so I'm
confident I can implement, test, and PR it well within the Weeks 8–9
window. There are no "blocked by" references or unresolved dependencies
noted on the issue.
