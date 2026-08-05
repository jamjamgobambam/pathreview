## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The FaithfulnessChecker's `check()` method builds its context by reading each
chunk's text with `chunk.get("text", "")`. That empty-string default only
applies when the `"text"` key is missing — if the key exists but holds `None`,
`.get()` returns `None`, which then gets passed into `" ".join(...)`. Since
`join` only accepts strings, it raises a `TypeError` instead of handling the
chunk. So any retrieved context chunk with a null text value crashes the
faithfulness evaluation in `rag/evaluator/faithfulness_checker.py`. A successful
fix treats a `None` text the same as empty/missing (coerce to `""` or skip it)
so the join succeeds and the existing `test_none_context_chunk_text` passes.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Selection notes ("Is this right for me?"):**
Tier 1, tightly scoped. The bug, its cause, a reproduction, and the exact
failing test are all named in the issue, so scope is clear and small — a
one-line-ish fix in a single file plus verifying one existing test. It needs no
Chroma or external services to reproduce or fix, which keeps the setup burden
low. Good first contribution to a large codebase.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/JoshuaE92/pathreview/commit/a4365836decf9ccece65d182affc7902ec6dc1cb

**Reproduction summary:**
I ran the existing failing test with
`python -m pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v`.
It fails at `rag/evaluator/faithfulness_checker.py:34` with
`TypeError: sequence item 0: expected str instance, NoneType found`, confirming
that a context chunk with `text: None` reaches `" ".join(...)` as `None` and
crashes the faithfulness evaluation exactly as issue #153 describes.

**PLAN.md link:** https://github.com/JoshuaE92/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** [optional — add Loom link if recorded]

**Blockers or open questions:**
None blocking. Open question for Week 9: whether to coerce `None` with
`chunk.get("text") or ""` (simplest) vs. an explicit `is not None` check, and
whether to add a mixed None/valid multi-chunk test to strengthen coverage.

## Week 9 — Implementation & PR submission

### Mid-week check-in

**Progress:**
Implemented the fix in `rag/evaluator/faithfulness_checker.py`: the context
concatenation now uses `chunk.get("text") or ""`, so a chunk whose `text` is
`None` (or missing) is coerced to an empty string before `" ".join(...)`. Added
two edge-case tests following the existing patterns in
`tests/unit/test_faithfulness_checker.py`: `test_none_text_mixed_with_valid_chunks`
(a `None` chunk must not discard valid sibling chunks) and
`test_all_chunks_none_text` (all-`None` context returns a valid float, no crash).

**Verification:** `test_none_context_chunk_text` now passes, as do the two new
tests. The faithfulness module went from 18 passed / 4 failed to 21 passed /
3 failed.

**Scoping note (honest self-assessment):** The 3 still-failing tests
(`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
`test_multiple_claims_varying_support`) are **pre-existing and unrelated** to
issue #153 — they fail because of the scoring threshold in `_is_supported`
(requires 2+ meaningful token overlaps), not the `None` crash. They fail on the
base branch before my change, so I am intentionally leaving them out of scope.
Likewise, CI runs `black --check .` and `ruff check .` repo-wide, and the
existing codebase is not black-formatted, so those jobs are already red on
`main`. I kept my diff minimal and matched the file's existing style rather than
reformatting unrelated code.

### Submission check-in

**PR link:** https://github.com/ascherj/pathreview/pull/854

**What I built:** A scoped fix for issue #153 plus two edge-case tests and inline
documentation explaining why `None` text is coerced to `""`.

**Files changed:**
- `rag/evaluator/faithfulness_checker.py` — coerce `None`/missing text to `""`
- `tests/unit/test_faithfulness_checker.py` — two new edge-case tests

**How to test:**
`python -m pytest tests/unit/test_faithfulness_checker.py -k "none" -v`

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(In this codebase "passes" means my changes introduce no new failures. `make check`
is already red repo-wide on pre-existing `ruff`/`black` formatting, and 3 pre-existing
scoring tests in this module fail on `main`; my change adds no new failures and removes
one — `test_none_context_chunk_text` — see the scoping note in the mid-week check-in.)

**Draft PR feedback received from:** none (cohort was told peer review is not required)

**Blockers or open questions:**
None. Pre-existing scoring failures and repo-wide formatting are documented above
as out of scope for this issue.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments came in. PR #854 remained open with no review
comments, review threads, or requested changes through the end of the week. (Per
the Summer 2026 cohort guidance, peer/maintainer review was not a required part of
the process this term.)

**How you responded:**
No feedback to respond to. I did a final self-review of the diff before the deadline
to confirm it was still minimal and correctly scoped.

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't the fix — it was everything around it. The one-line change
(`chunk.get("text", "")` → `chunk.get("text") or ""`) was clear from the issue. What
surprised me was the ambiguity of "does the build pass?" in a real repo: `make check`
was already red repo-wide because the existing code isn't `black`/`ruff` formatted,
and three scoring tests in the same module fail on `main` for reasons unrelated to my
bug. Figuring out which failures were mine versus pre-existing, and being able to
prove it, took more care than writing the fix. The upstream repo had also been renamed
(`jamjamgobambam` → `ascherj`), so even pointing my remotes and PR at the right target
was a small investigation.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is mostly about restraint. On my own
project I'd have "cleaned up" the formatting and maybe touched the scoring logic while
I was in there. Here, the right move was the opposite: keep the diff to exactly what
issue #153 needed, match the file's existing style instead of reformatting, and
document the pre-existing failures rather than silently absorbing them into my PR.
I also learned to read the *tests* to understand expected behavior — the existing
`test_none_context_chunk_text` told me precisely what a correct fix looked like before
I wrote a line. Scope discipline and being able to defend "this is out of scope" turned
out to be the real skills.

**How did AI tools help — and where did they fall short?**
AI was most useful for navigation and verification: exploring an unfamiliar codebase,
discovering the repo had moved, confirming via the GitHub API that no PR existed yet,
distinguishing my test results from pre-existing failures, and drafting the PR
description and journal entries against the templates. Where it fell short was
judgment: deciding *which* fix idiom to use, deciding what to leave out of scope, and
confirming the honest framing of "passes = no new failures." It also can't do the
parts that are actually mine to own — opening the PR, marking it ready, and submitting
the branch URL to the portal. AI accelerated the mechanical work; the decisions still
had to be mine.

**What would you do differently if you started over?**
I'd open the draft PR earlier in the week instead of near the deadline, so the "PR is
live" step wasn't the last thing standing between me and being done. I'd also verify
the canonical upstream repo up front rather than discovering the rename mid-process,
and I'd keep my working tree clean from the start — a couple of stray files (`=0.29.0`,
a `package-lock.json` change) crept in and had to be stashed out before the PR so they
wouldn't leak in.

**What are you most proud of from this module?**
Not the fix itself, but the honesty of the submission. Instead of checking every box
and pretending a red repo was green, I documented exactly which failures pre-existed,
proved my change removed one failure and added none, and kept the diff small enough
that a reviewer could verify it in under a minute. Learning to make a clean, defensible,
tightly-scoped contribution to a codebase I didn't write is the thing I'll actually
carry forward.
