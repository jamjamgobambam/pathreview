## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text:None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`FaithfulnessChecker.check()` in `rag/evaluator/faithfulness_checker.py` scores generated
feedback by comparing it against the retrieved context chunks. To build the comparison text,
it does `chunk.get("text", "")` for each chunk, which only falls back to `""` when the `"text"`
key is missing entirely — if a chunk has `"text": None` (e.g. from a source that failed to
extract text during ingestion), `.get()` returns `None` instead of the default, and the
subsequent `" ".join(...)` raises a `TypeError` because it can't join a `None` into a string.
This crashes the entire evaluation run instead of just skipping or scoring around the bad
chunk. A successful fix replaces the `.get("text", "")` call with logic that coerces a `None`
value to an empty string (e.g. `chunk.get("text") or ""`), so the checker degrades gracefully
on malformed chunks instead of raising, and adds a regression test covering a chunk with an
explicit `None` text value.

**Scope check ("Is this right for me?"):**
This is a good first issue: it's isolated to one small method in one file with no cross-module
changes, the bug is fully understood (root cause is the `.get()` default-value gotcha, not a
mystery), it doesn't touch auth, migrations, or infra, and it's easy to verify with a unit test
that passes a chunk with `text: None` before/after the fix. It's scoped small enough to finish
well within Tier 1 expectations while still touching real application code (not just docs/tests).

**Branch name:** fix/153-faithfulness-checker-none-context

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/KritinRane/pathreview/commit/b30477f7ac6ef4e2f8f6b8fefc9296c54b37edf3

**Reproduction summary:**
Ran `.venv/bin/python scripts/repro_issue_153.py` (and the existing unit test
`tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text`),
passing a context chunk of `{"text": None}` to `FaithfulnessChecker.check()`.
Both crash with `TypeError: sequence item 0: expected str instance, NoneType found`
at the `" ".join([chunk.get("text", "") ...])` line in
`rag/evaluator/faithfulness_checker.py`, confirming the `.get(..., "")` default
does not cover an explicit `None` value.

**PLAN.md link:** https://github.com/KritinRane/pathreview/blob/fix/153-faithfulness-checker-none-context/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm no other module builds context with the same `.get("text", "")`
pattern, and decide whether to coerce truthy non-string `text` values (likely
out of scope for this issue).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: `rag/evaluator/faithfulness_checker.py`
now builds `context_text` with `chunk.get("text") or ""` instead of
`chunk.get("text", "")`, so a chunk with `"text": None` coerces to an empty
string instead of raising `TypeError` on `" ".join(...)`. Added a new
regression test, `test_none_context_chunk_text_matches_empty_string`, that
asserts a `None`-text chunk scores identically to an empty-string chunk. The
pre-existing `test_none_context_chunk_text` (previously failing) now passes.
All 4 sub-tasks from PLAN.md's "Plan" section are done: the one-line fix,
the added assertion, a full run of `test_faithfulness_checker.py` to confirm
no regressions, and re-running `scripts/repro_issue_153.py` (now prints
`faithfulness score: 0.0` instead of crashing).

Also resolved the "Upstream duplication" risk from PLAN.md: grepped `rag/`
for the same `.get("text", "")` pattern and found it in three other files.
Two (`review_generator.py`, `hybrid.py`) don't crash on `None`. One,
`relevance_scorer.py`, has the identical bug class (crashes with
`AttributeError` instead of `TypeError`) — documented in PLAN.md as a
follow-up to file separately, kept out of this PR to stay scoped to issue
#153.

Ran `make test-unit` and `make check` before and after the change to isolate
pre-existing failures: baseline was 53 failed / 375 passed unit tests and
182 lint errors; after the fix it's 52 failed / 377 passed (one
previously-failing test now passes, one new test added, no new failures)
and still 182 lint errors (no new lint issues introduced).

**Next steps:**
Open a draft PR for peer/mentor review, fill in the PR template, and get
feedback before marking it ready for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/574

**Branch:** `fix/153-faithfulness-checker-none-context`

**What you built:**
`FaithfulnessChecker.check()` crashed with a `TypeError` when a context
chunk had `"text": None` (e.g. from a source that failed text extraction
during ingestion), because `chunk.get("text", "")` only falls back to `""`
when the key is *absent*, not when it's present but `None`. Changed the
lookup to `chunk.get("text") or ""` so both a missing key and an explicit
`None`/falsy value coerce to `""`, letting the checker degrade gracefully
instead of aborting the whole evaluation run.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — the pre-existing
`test_none_context_chunk_text` (previously failing) now passes; added
`test_none_context_chunk_text_matches_empty_string`, which asserts a
`None`-text chunk scores identically to an empty-string chunk. Also fixed
an unused-variable lint error in an unrelated pre-existing test
(`test_common_words_filtered_in_overlap`) and added type annotations across
the file to satisfy the repo's `disallow_untyped_defs` mypy setting, which
the pre-commit hook enforces on `tests/` even though `make check`'s
`typecheck` target excludes that directory.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both commands were run before and after the change to isolate pre-existing
issues: baseline (on `main`) was 53 failed / 375 passed unit tests and 182
lint errors; after this fix it's 52 failed / 377 passed (the target test
now passes, one new test added, zero new failures) and 180 lint errors (2
fewer, from cleanup in the touched test file, zero new ones introduced).
The remaining 52 test failures and 180 lint errors are pre-existing and
unrelated to this change — verified with `git stash` diffs against `main`
before making any edits.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
PR #574 has no comments and no reviews as of this writing. Per the Su26
course note, reviewer feedback isn't a feature this term, so no maintainer
review was expected.

**How you responded:**
N/A — no feedback arrived to respond to.

---

### Reflection

**What was harder than you expected?**
The fix itself — swapping `chunk.get("text", "")` for `chunk.get("text") or
""` — was a one-line change. What took real time was everything around it:
confirming the bug's exact failure mode with a reproduction script before
touching code, grepping the rest of `rag/` for the same `.get(key, default)`
pattern to see how far the risk actually spread, and then deciding what
*not* to fix. Finding the identical bug class in `relevance_scorer.py` and
choosing to leave it out of this PR (documented as a follow-up instead) was
harder than writing the patch — it's easy to want to "fix it while I'm in
here," and staying inside the issue's scope took more discipline than the
code did.

**What did you learn about working in a large codebase?**
The pre-commit hook enforcing `disallow_untyped_defs` on `tests/` even
though `make check`'s `typecheck` target excludes that directory was the
clearest lesson: a codebase's stated checks (`make check`) and its actual
enforced checks (pre-commit hooks, CI) can diverge, and you only find that
divergence by trying to commit, not by reading the Makefile. I also learned
to treat pre-existing failures as a baseline to diff against rather than a
blocker — running `make test-unit`/`make check` on `main` first (53
failed / 182 lint errors) gave me a number to compare my branch against, so
I could prove my change added zero new failures instead of just eyeballing
the diff and hoping.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical, error-prone parts:
grepping for every other occurrence of the `.get(key, default)` pattern
across `rag/`, writing the regression test that mirrors the existing test
style, and adding type annotations across the touched test file to satisfy
mypy. It fell short on the judgment calls — deciding whether
`relevance_scorer.py`'s identical bug belonged in this PR or a separate
issue, and how much of the "upstream duplication" risk from PLAN.md was
actually worth investigating versus noting and moving on. Those scoping
decisions needed a human read of what the issue was actually asking for.

**What would you do differently if you started over?**
I'd file the `relevance_scorer.py` follow-up issue immediately after
finding it in Week 9 instead of just noting it in PLAN.md — right now it
only exists as a paragraph in this repo's docs, not as a trackable issue,
so it's easy for it to get lost.

**What are you most proud of from this module?**
Not the one-line fix — the repro script and the baseline
test/lint counts. Having `scripts/repro_issue_153.py` crash predictably
before the fix and print a real score after, plus a documented before/after
test count, meant the PR was verifiable by anyone reading it, not just
asserted as fixed.
