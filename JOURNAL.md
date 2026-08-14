# Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker` in the RAG evaluator (`rag/evaluator/faithfulness_checker.py`)
is supposed to score how well generated feedback is supported by the retrieved context
chunks. When one of those chunks has a `text` key whose value is `None`, the `check()`
method crashes with a `TypeError` instead of returning a score, because
`chunk.get("text", "")` only substitutes the default when the key is *missing* — not
when it is present with a `None` value — so `" ".join(...)` receives a `None`. Any
evaluation run that includes such a chunk breaks entirely rather than degrading
gracefully. A successful fix treats `None` text as an empty string so `check()` skips
the empty chunk and still returns a normal 0.0–1.0 faithfulness score, which is exactly
what the existing `test_none_context_chunk_text` unit test expects.

**Selection notes ("Is this right for me?"):**
This Tier 1 issue has a clear reproduction, a localized root cause in one evaluator,
and an existing regression test that defines success. It fits my scope because the fix
requires no API, schema, dependency, or architectural changes—only safe handling of a
nullable dictionary value. I can verify it by running the focused faithfulness checker
test and confirming `check()` returns a score instead of raising `TypeError`.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/wzltmp/pathreview/commit/a4420c8

**Reproduction summary:**
I reproduced the issue against the `main` version of `rag/evaluator/faithfulness_checker.py`
by running `FaithfulnessChecker().check("Knows Python.", [{"text": None}])`. The observed
failure was `TypeError: sequence item 0: expected str instance, NoneType found` from the
`" ".join(...)` call that receives `None` from `chunk.get("text", "")`.

**PLAN.md link:** https://github.com/wzltmp/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
No current blockers. Before opening the PR, I still need to run the full required checks:
`make check` and `make test-unit`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
PLAN.md steps 1–4 are done. The fix is implemented in
`rag/evaluator/faithfulness_checker.py`: `check()` now builds `context_text` with
`chunk.get("text") or ""` instead of `chunk.get("text", "")`, so a chunk with an explicit
`"text": None` falls back to `""` exactly as a missing key already did. The existing
`test_none_context_chunk_text` now passes, and `test_missing_text_key_in_chunk` is
unaffected. I also audited the branch against `docs/CONTRIBUTING.md`: branch name matches
`<type>/<issue-number>-<short-description>`, all commits are Conventional Commits with the
`rag` scope, and there are no merge commits.

**Next steps:**
PLAN.md step 5 — establish validation evidence. This repo has many pre-existing `make
check` and `make test-unit` failures, so I need to measure ruff, mypy, and pytest against
a clean `upstream/main` checkout *before* and *after* my change to prove I introduce no
new ones. I also want to strengthen test coverage: the existing regression test only
asserts a bounded float for a lone `None` chunk, so it would still pass if the crash were
"fixed" by discarding the whole context. Then rebase onto `upstream/main`, self-review the
full diff, and open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/548

**Branch:** `fix/153-faithfulness-checker-none-text`

**What you built:**
`FaithfulnessChecker.check()` crashed with `TypeError` whenever a retrieved context chunk
had `"text": None`, because `dict.get()` only substitutes its default when the key is
*absent*, not when it is present and `None` — so `" ".join(...)` received a `None`. The
fix coerces a `None` chunk text to `""` before joining, so the malformed chunk is skipped
and `check()` returns a normal 0.0–1.0 score instead of taking down the whole evaluation
run. I also updated the `check()` docstring to document the nullable-text behavior.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — added
`test_none_chunk_text_does_not_discard_valid_chunks`, which passes a `None` chunk
*alongside* a valid chunk and asserts the valid one is still scored (`score > 0.5`). This
covers a gap the existing `test_none_context_chunk_text` could not catch: that test only
asserts a bounded float for a lone `None` chunk, so it would still pass if the crash were
avoided by throwing away the entire context. I verified the new test is a genuine
regression test by reverting the one-line fix and confirming it fails, then restoring it.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both boxes use the documented meaning for a codebase with pre-existing failures: my
changes introduce **no new failures**. Measured against a clean `upstream/main` worktree
before and after:

| Check | `main` (baseline) | This branch | Delta |
|---|---|---|---|
| `make test-unit` | 53 failed / 375 passed | 52 failed / 377 passed | −1 failure, 0 new |
| `ruff` | 182 errors | 181 errors | −1, 0 new |
| `mypy` (`make typecheck` scope) | 5 errors | 5 errors | identical output |

I diffed the sorted lists of `FAILED` test IDs between `main` and this branch: the only
difference is `test_none_context_chunk_text` flipping from failing to passing. Nothing
that passed on `main` fails here. The 3 still-failing tests in
`test_faithfulness_checker.py` are pre-existing `_is_supported()` scoring-threshold bugs,
a separate concern I deliberately kept out of scope. All of this is documented in the PR's
Notes for Reviewers section.

**Draft PR feedback received from:** none — opened directly as ready for review. Peer
review requested in the cohort Slack channel; I will address any feedback in follow-up
commits on this branch.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
As of August 14, 2026, [PR #548](https://github.com/ascherj/pathreview/pull/548) is open
and marked as requiring review, with no reviews or comments. Reviewer feedback is not
provided in Summer 2026, so no review came in by the end of the week.

**How you responded:**

---

### Reflection

**What was harder than you expected?**

The code change was only one expression, but proving that it was safe was much harder
than writing it. I chose issue #153 because it had a narrow failure: `dict.get("text",
"")` returns `None` when the key exists with that value, and `" ".join(...)` then raises
a `TypeError`. Changing it to `chunk.get("text") or ""` stopped the crash. The existing
`test_none_context_chunk_text` also turned green, but it only checked that the result was
a bounded float. It would still pass if the implementation silently discarded all
context and always returned `0.0`.

I had to define the intended behavior more precisely and add
`test_none_chunk_text_does_not_discard_valid_chunks`, which combines a `None` chunk with
valid context and asserts that the valid text is still scored. I then reverted the fix,
confirmed that this test failed, and restored it. The other unexpected difficulty was
validation in a repository whose default branch already had 53 failing unit tests, 182
ruff errors, and 5 mypy errors. I used a clean `upstream/main` worktree and compared
sorted failure IDs, not just totals, to show that my branch introduced no regressions.

**What did you learn about working in a large codebase?**

I learned that contributing to someone else's codebase is as much about respecting its
boundaries as changing its code. I needed to follow the repository's branch and commit
conventions, understand the evaluator's existing behavior, and separate my failures from
the baseline before making any claim about validation. I also found that project tooling
can disagree with itself: the pre-commit mypy hook checks staged tests, while `make
typecheck` excludes them, so touching a test exposes about 25 pre-existing
`no-untyped-def` errors. I ran the individual checks manually and compared the same hook
against `upstream/main` rather than hiding or "fixing" unrelated failures.

The most important scope decision was leaving three failing `_is_supported()` tests
alone. They belong to issue #152 and were already failing on `main`. Fixing them while I
was in the file would have mixed two bugs in one review and risked overlapping another
contributor. In my own project I might clean up everything nearby; in a shared project,
a focused change with explicit evidence is easier to review and safer to merge.

**How did AI tools help — and where did they fall short?**

AI tools helped me trace the failure to the difference between a missing dictionary key
and an explicit `None`, find the nearby tests, enumerate edge cases, and turn raw command
output into a baseline-versus-branch comparison. They were also useful for reviewing the
written explanation from a maintainer's perspective: what behavior changed, why the new
test mattered, and which failures were unrelated.

They did not remove the need to verify anything. A plausible answer was available as soon
as the existing test passed, but that answer did not prove valid chunks were preserved.
I had to inspect the assertion, strengthen it, and deliberately revert the production
change to prove the regression test could fail. AI-assisted edge-case analysis also
stopped too early at falsy values; only later did I notice that a truthy non-string value
such as `{"text": 123}` still raises the same `TypeError`. That case was outside the
reported issue, so I did not expand this PR, but it showed me that generated suggestions
are hypotheses to test, not evidence.

**What would you do differently if you started over?**

I would write the journal entries when the work happens instead of reconstructing both
Week 9 check-ins near the deadline. I would also open a draft PR earlier so a peer could
challenge the behavior and test before I marked it ready for review. Technically, I would
start with the stronger behavioral test—`None` beside a valid chunk—then make it pass,
and I would establish the repository's baseline before running the full suite on my
branch. Finally, I would examine the whole input contract up front, including truthy
non-string values, even if I ultimately documented them as out of scope.

**What are you most proud of from this module?**

I am most proud of not stopping at the one-line fix. The additional regression test
captures the behavior users need: one malformed context chunk must not erase the useful
chunks around it. Confirming that the test failed when I reverted the fix made it real
evidence rather than a green checkbox. I am also proud that I handled a noisy codebase
without either claiming the suite was clean or widening the PR to repair unrelated
problems. The final contribution is small, but its scope, test, validation record, and PR
explanation make it something a maintainer can evaluate with confidence.
