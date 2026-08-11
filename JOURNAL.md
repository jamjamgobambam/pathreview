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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments on PR #992 as of this entry — 0 issue
comments, 0 review comments, 0 reviews. (Su26 note: reviewer feedback isn't
enabled as a feature this term, so this was expected rather than a stalled
PR.) The repo also has no CI configured, so there was no automated signal to
respond to either.

**How you responded:**
N/A — nothing came in to respond to. If that changes before the course ends,
I'll add a dated follow-up here addressing it directly.

---

### Reflection

**What was harder than you expected?**
The fix itself was one line — `chunk.get("text") or ""` instead of
`chunk.get("text", "")` — and took about five minutes once I understood
`.get(key, default)` only substitutes the default when the key is *absent*,
not when the value is `None`. Almost everything else took longer than the
fix. Distinguishing "tests that are failing because of my change" from
"tests that were already broken" was harder than expected — the suite had 53
pre-existing failures completely unrelated to #153, including 3 in the exact
file I was editing, so I had to run the full suite before and after my
change and diff the failure lists rather than trust a single "N tests
failed" number. I also hit a real environment problem I didn't anticipate:
my shell's git repository root turned out to be resolving to my entire home
directory instead of the project folder, with thousands of unrelated files
staged for commit — including browser cookies and a previous commit that
already contained what looked like real secrets in a `.env` file. None of
that was related to #153, but if I hadn't checked `git rev-parse
--show-toplevel` before committing anything, I could have easily committed
or pushed something I shouldn't have while just trying to knock out the
week's checklist.

**What did you learn about working in a large codebase?**
You can't assume a clean baseline. In a codebase you own, a failing test
usually means you broke something; in a large, unfamiliar codebase, it might
mean nothing to do with you at all, and claiming "all tests pass" without
checking first is actually dishonest. I also learned that the same bug
pattern tends to repeat — grepping for `chunk.get("text", "")` turned up
three more call sites (`review_generator.py`, `relevance_scorer.py`,
`hybrid.py`) with what looks like the identical latent crash. Finding that
was tempting to "fix while I was in there," but the issue only named
`faithfulness_checker.py`, and a PR that quietly grows past its issue is
exactly the kind of thing a reviewer has to untangle later. Staying scoped
to what the issue actually asked for, and leaving a note instead of silently
expanding the diff, felt like the more professional call even though it
meant leaving known bugs unfixed.

**How did AI tools help — and where did they fall short?**
I used Claude Code throughout — to grep the codebase for the sibling bug
pattern, run the reproduction and the before/after test-suite diff, draft
PLAN.md and the JOURNAL.md entries, and catch things I might have missed,
like the stray unrelated typo that had crept into `hybrid.py` on my branch
and the home-directory git-root problem. That verification loop (baseline,
change, re-verify, diff the failures) is something I'd have been more likely
to skip doing carefully by hand under time pressure. Where it fell short:
it has no `gh` CLI or GitHub credentials in my environment, so it couldn't
actually open the PR — I had to do that step myself. It also isn't a
substitute for knowing what a reviewer would actually want; it flagged the
`or ""` vs. explicit `is None` trade-off as a judgment call rather than
silently picking one, but I still had to decide which one I'd defend. And
concretely, this Week 10 entry itself is a good example of where it fell
short: the first draft used the wrong section headings and swapped the
required five-question reflection format for its own free-form version,
because it was working from an earlier paraphrase of the assignment instead
of the actual template text. I only caught that by re-checking the draft
against the real assignment description, which is exactly the kind of
verification step I now think is necessary any time I'm using AI output for
something that gets graded.

**What would you do differently if you started over?**
Two things. First, I'd run the cross-codebase grep for the bug pattern
during Week 8 planning instead of discovering it mid-implementation in Week
9 — it would have let me decide the scope, and file a follow-up issue for
the sibling bugs, before writing PLAN.md instead of as an afterthought.
Second, I'd check the actual assignment text/checklist against my
deliverables before considering a week "done," not just at the end when
something prompts a re-check — Week 10's reflection format is proof that
working from memory of instructions given several messages ago, instead of
the source text, produces drift.

**What are you most proud of from this module?**
The before/after baseline-diff verification on the test suite. It would have
been easy to either claim "tests pass" without checking, or panic at 53
failing tests that had nothing to do with my change. Instead I captured the
exact failing-test list before touching anything, made the fix, re-ran the
suite, and diffed the two lists to show precisely one test changed status —
the one the issue was about. That's a small habit, but it's the difference
between a claim I can actually defend to a reviewer and one I'm just hoping
is true.
