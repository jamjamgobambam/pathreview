## Week 7 — Issue selection

**Issue link:** [GitHub Issue Link](https://github.com/ascherj/pathreview/issues/149)

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`StructuralChunker` (the `_extract_sections` method in `ingestion/chunking/structural_chunker.py`) is a strategy for splitting documents into chunks based on Markdown headings, specifically designed to handle README-style documents. However, its collection logic relies on "first encountering a heading" before it begins recording body lines.

If the entire document contains no headings, the body lines will never be collected, and ultimately `chunk()` returns an empty list.

The problem is that this process generates no error messages or logs, resulting in such documents being silently excluded from the RAG index - users are completely unaware that their documents have "disappeared".

After the fix, headless documents should at least be retained as a single chunk (or fall back to `SemanticChunker`) rather than being discarded.

**Branch name:** fix/149-chunker-drops-no-heading-docs

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ShiriZhang/pathreview/commit/54ff4590b6f6ceb8d561a684f2dfa8f153c20c9e

**Reproduction summary:**
Ran `pytest tests/unit/test_structural_chunker.py -k test_document_with_no_headings -v` locally; the existing test fails with `assert 0 >= 1` because `StructuralChunker.chunk()` returns an empty list for a plain-text document with no Markdown headings, confirming the behavior described in issue #149.

**PLAN.md link:** https://github.com/ShiriZhang/pathreview/blob/fix/149-chunker-drops-no-heading-docs/PLAN.md

**Walkthrough video (recommended):** Not recorded this week

**Blockers or open questions:**
Still deciding between two fix strategies (treat headless doc as one section vs. fully delegate to SemanticChunker) — plan to check linked PRs #192/#162 for precedent before finalizing in Week 9. Also spent some time confirming a pre-commit failure was pre-existing project debt rather than a fork-sync issue (documented in PLAN.md's Risks & unknowns).


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md's option (a): `_extract_sections()` now treats a headless document as a single section instead of returning an empty list. Added 3 new unit tests covering a short headless doc, a long headless doc (verifying it sub-chunks via SemanticChunker), and a false-positive heading match (`#nospace`). All 18 tests in `test_structural_chunker.py` pass, and comparing against the pre-recorded baseline confirms no new failures were introduced elsewhere in the suite (53 → 52 failing, only `test_document_with_no_headings` flipped from fail to pass).

**Next steps:**
Open PR, request peer/mentor review in Slack, finalize JOURNAL Check-in 2.

**Blockers:**
Compressed the Wednesday/Sunday check-in schedule into a single day due to limited time before the deadline.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/629

**Branch:** `fix/149-chunker-drops-no-heading-docs`

**What you built:**
Fixed `StructuralChunker.chunk()` silently dropping documents with no Markdown headings. When `_extract_sections()` finds no headings at all, it now returns the whole document as a single section instead of an empty list, so it gets chunked (and sub-chunked via `SemanticChunker` if it's large) like any other document.

**Tests added or updated:**
`tests/unit/test_structural_chunker.py` — added `test_long_document_with_no_headings_gets_sub_chunked`, `test_hash_without_space_is_not_treated_as_heading`, and `test_headless_document_has_empty_heading_metadata`, covering the fix's sub-chunking path, a false-positive heading edge case, and the resulting metadata shape.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
*(Note: this codebase has pre-existing failures unrelated to #149 — 180 ruff errors and 53 failing tests at baseline. "Passes" here means no new failures were introduced; see PR description for the full before/after comparison.)*

**Draft PR feedback received from:** Claude Code


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No comments or reviews were received on PR #629 as of this week. Per the course's
Su26 note, reviewer feedback isn't a feature enabled this term.

**How you responded:**
N/A — no feedback received to respond to.

---

### Reflection

**What was harder than you expected?**
I expected the hard part of this issue to be the actual chunking logic — it
turned out to be a three-line fix. What actually slowed me down was the
tooling: every time I touched a file that had never been part of a commit
before (`structural_chunker.py`, then `semantic_chunker.py`, then
`test_structural_chunker.py`), `pre-commit` surfaced a fresh batch of
pre-existing ruff/mypy errors that had nothing to do with my change. I spent
more time figuring out "is this my problem or not" than writing the fix
itself. I also didn't expect `mypy` to check across the whole import graph —
I assumed I could scope a commit to one file and have hooks only judge that
file.

**What did you learn about working in a large codebase?**
The codebase doesn't start clean, and it's not your job to make it clean —
it's your job to not make it worse. I had to get comfortable drawing a line
around "what counts as issue #149" versus "things I noticed along the way,"
and defend that line in the PR description instead of either ignoring debt
silently or trying to fix everything I ran into. The edge case my reviewer
found during PR review (a heading-only document with no body falling into
the same fallback as a truly headless one) was a good example — I had to
decide whether that was actually in scope, and documenting the decision
felt more honest than pretending I hadn't seen it.

**How did AI tools help — and where did they fall short?**
AI was most useful for fast, precise diagnosis — reading a wall of
ruff/mypy/pytest output and telling me exactly which line was new versus
pre-existing, and explaining git concepts (stash vs. stage, merge vs.
rebase) in the moment I needed them instead of me guessing from
documentation. It fell short on anything that required a judgment call
that was actually mine to make: which fix strategy to implement, whether
to fix or document the edge case, and getting a real second opinion from a
classmate — Slack peer review is something no amount of AI assistance
substitutes for, and I ended up requesting it too late in the week to get
a real response.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` to record the baseline in Week 7
or 8, not Week 9 — I didn't realize the scale of pre-existing failures
until I was already trying to open a PR, and that reshaped how I had to
write the PR description under time pressure. I'd also post in Slack for
peer review on day one of Week 9 instead of after the implementation was
already done, so there was actually time for someone to respond.

**What are you most proud of from this module?**
Not assuming the fork-sync explanation was correct just because it sounded
plausible and came from a mentor — I checked it against a clean copy of
`upstream/main` before accepting it, and it turned out the real cause was
different. That felt like the most "real engineering" moment of the whole
module, more than the fix itself.
