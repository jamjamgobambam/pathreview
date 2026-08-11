# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker.check()` method builds its context string by pulling
`text` out of each chunk dict with `chunk.get("text", "")`, assuming that
missing keys are the only case it needs to guard against. But `.get()` only
falls back to the default when the key is absent — if a chunk explicitly has
`"text": None`, `.get()` returns `None`, and the subsequent `" ".join(...)`
call raises a `TypeError` because it can't join a `NoneType` into a string.
In practice this means any upstream chunk that legitimately has a null/empty
text field (rather than a missing one) crashes the faithfulness check instead
of being skipped or treated as empty. A correct fix should coerce `None`
values to an empty string (or filter the chunk out) before joining, so the
checker degrades gracefully instead of raising. This touches
`rag/evaluator/faithfulness_checker.py`, and there's already a failing test,
`test_none_context_chunk_text`, in `tests/unit/test_faithfulness_checker.py`
that should pass once the fix is in.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/adedotdev/pathreview/commit/966b683 (branch `fix/153-faithfulness-checker-none-text`)

**Reproduction summary:**
Ran the existing (failing) test `tests/unit/test_faithfulness_checker.py::test_none_context_chunk_text`, which calls `FaithfulnessChecker.check()` with a chunk `{"text": None}`. It raised `TypeError: sequence item 0: expected str instance, NoneType found` at `rag/evaluator/faithfulness_checker.py:39`, confirming `chunk.get("text", "")` returns `None` (not the default) when the key is present but explicitly `None`. Documented the reproduction with an inline comment at the crash site.

**PLAN.md link:** https://github.com/adedotdev/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** _not recorded yet_

**Blockers or open questions:**
The same `chunk.get("text", "")` pattern also exists in `review_generator.py`, `relevance_scorer.py`, and `hybrid.py` and likely has the same latent bug, but issue #153 only scopes the fix to `faithfulness_checker.py`. Also, 3 tests in `test_faithfulness_checker.py` fail today for reasons unrelated to this issue (claim-extraction/overlap-scoring logic) — need to confirm with a mentor whether that's separately tracked before I touch it in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md step 1: `faithfulness_checker.py` now builds
`context_text` with `chunk.get("text") or ""` instead of
`chunk.get("text", "")`, so a chunk with `"text": None` is treated the same as
a missing/empty one instead of crashing. `test_none_context_chunk_text` now
passes. Added `test_mixed_none_missing_and_valid_text_chunks` to cover a
`context_chunks` list with `None` text, a missing key, and valid text in the
same call (PLAN.md's "mixed" edge case) — it passes too.

Before changing anything I captured a baseline: `pytest tests/unit -m unit`
had 53 pre-existing failures unrelated to #153 (bias detector, PII scrubber,
resume parser, review service, etc. — none touch faithfulness/context
handling). After the fix, the suite has 52 failures — the exact same set
minus `test_none_context_chunk_text`, confirmed via diff. `ruff check` and
`black --check` on the two touched files show only pre-existing issues I
didn't introduce (an unsorted-import warning already in
`faithfulness_checker.py`, and an unused-variable warning in an untouched
test method) — my own added/changed lines are clean. `mypy` on
`faithfulness_checker.py` alone passes; a full-tree `mypy` run fails in this
environment due to missing third-party type stubs (`PyPDF2`, `jose`,
`passlib`, `rank_bm25`) and a numpy stub/Python-version mismatch, all
pre-existing and unrelated to this change.

**Next steps:**
Open a draft PR referencing #153, share it in Slack for early feedback, then
finalize once reviewed.

**Blockers:**
No `make` binary available in this Windows/Git Bash environment, so I ran the
underlying `pytest`/`ruff`/`black`/`mypy` commands directly from a local
`.venv` instead of `make check`/`make test-unit` — same commands the
Makefile wraps, just invoked without `make`.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/992

**Branch:** `fix/153-faithfulness-checker-none-text`

**What you built:**
`FaithfulnessChecker.check()` now coerces a chunk's `"text"` to `""` with
`chunk.get("text") or ""` instead of `chunk.get("text", "")`, so a chunk with
an explicit `"text": None` is treated the same as a missing or empty one
instead of raising `TypeError` when `" ".join(...)` hits a `None`.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — added
`test_mixed_none_missing_and_valid_text_chunks`, covering `None` text, a
missing key, and valid text in the same `context_chunks` list. The
pre-existing `test_none_context_chunk_text` now passes; it was the failing
test the issue was scoped around.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(run as the underlying `ruff`/`black`/`mypy`/`pytest` commands directly, no
`make` binary available on Windows — see Week 9 Check-in 1 blocker. Baseline
had 53 pre-existing unit-test failures unrelated to #153; after this change
there are 52, the same set minus `test_none_context_chunk_text`. `ruff` and
`black` on the touched files show only pre-existing issues I didn't
introduce. `mypy` passes on `faithfulness_checker.py`; a full-tree run fails
on pre-existing missing type stubs unrelated to this change.)_

**Draft PR feedback received from:** none yet

## Week 10 — Review response & reflection

### Review feedback

Checked PR #992 for activity: it's open, not a draft, 5 commits, and has 0
issue comments, 0 review comments, and 0 reviews. The repo also has no CI
checks configured (0 check runs on the head commit), so there's no automated
signal either. Nothing has come back to respond to. Per the course's own
framing, that's an acceptable outcome, not a gap — so I'm noting it here
rather than manufacturing a response to feedback that doesn't exist. If
something does come in before the course ends, I'll add a dated response
below this entry addressing it directly (fix it, ask a clarifying question,
or explain my reasoning if I disagree).

### Reflection

I picked issue #153 because it was small enough to actually finish end to
end in a few weeks but real enough to teach something: `.get(key, default)`
only substitutes the default when the key is *absent*, not when the value is
`None`. I'd used that pattern without thinking about it for years, so
reproducing the crash was also the moment I actually understood the bug in
my own code, not just this codebase's.

The fix itself — `chunk.get("text") or ""` — took five minutes once I
understood the root cause. Almost everything else took longer than the fix:

- **Scoping discipline.** Grepping for the same `chunk.get("text", "")`
  pattern turned up three more call sites (`review_generator.py`,
  `relevance_scorer.py`, `hybrid.py`) with the identical latent bug. My first
  instinct was to fix all of them while I was in there. I didn't, because the
  issue only named `faithfulness_checker.py`, and a PR that quietly grows
  past its issue is exactly the kind of thing a reviewer has to untangle
  later. I left a reviewer note instead. In hindsight I'd make that call
  again, but I'd file the follow-up issue immediately instead of just
  mentioning it in a PR comment — right now that context only lives in a PR
  description, which is a bad long-term home for it.
- **Separating my bug from the codebase's bugs.** The test suite had 53
  pre-existing failures before I touched anything, completely unrelated to
  #153 (bias detector, PII scrubber, resume parser, and three other tests in
  the very file I was editing). Without a baseline, it would have been easy
  to either falsely claim "all tests pass" or falsely panic that my one-line
  change broke 53 tests. Running the suite before *and* after and diffing
  the failure list was the only way to make an honest claim about what my
  change actually did. That's a habit I didn't have before this project and
  now think is close to mandatory for any change to an unfamiliar codebase.
- **A near-miss with the tools, not the code.** Early on, my shell's git
  root turned out to be resolving to my entire home directory instead of the
  project folder, with thousands of unrelated files staged — including
  browser cookies and a prior commit containing what looked like real
  secrets in a `.env` file. None of that was related to #153, and it would
  have been easy to just run the commit the task asked for without checking
  where I actually was. Catching it before committing anything was luck as
  much as diligence — I happened to check `git rev-parse --show-toplevel`
  out of habit. If I were starting over, checking that up front, before any
  git command, would be step zero, not an accident.
- **Correctness vs. clarity trade-off I'm still not 100% settled on.**
  `chunk.get("text") or ""` reads cleanly and passes every test, but it also
  coerces any falsy `"text"` value to `""`, not just `None` — which is fine
  today because `text` is always a string or `None` in practice, but it's a
  slightly looser fix than `chunk.get("text") if chunk.get("text") is not
  None else ""`. I chose the terser version for readability and flagged the
  trade-off explicitly in PLAN.md's risks section rather than silently
  picking one. If a reviewer pushes back and wants the explicit `is None`
  check, I think they'd have a fair point about precision even though I'd
  argue readability for a codebase where `text` fields are always strings.
  That's the kind of disagreement I'd rather have in a PR thread than avoid
  by guessing what a reviewer wants.

If I were starting this whole arc over with what I know now, the main thing
I'd change is doing the cross-codebase grep for the bug pattern during Week
8 planning instead of Week 9 implementation — it would have let me make the
scope decision, and file any follow-up issues, before writing PLAN.md rather
than as an afterthought once I was already mid-fix.
