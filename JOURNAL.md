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


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:**
Set up a local Python 3.11 virtualenv (the project requires >=3.11; the
system default `python3` is 3.9) and captured a full baseline of `make check`
and `make test-unit` before making any changes. Baseline on this branch:
`make check` fails at the lint step with 182 pre-existing ruff errors (so
black and mypy never run; separately, black would reformat 52 files and mypy
reports 103 errors), and `make test-unit` reports 52 failed / 376 passed.
All of these are pre-existing on `main` and unrelated to issue #153.

Added one new test, `test_mixed_none_and_valid_context_chunk_text`, to
`tests/unit/test_faithfulness_checker.py`. It covers the realistic mixed
case the existing tests miss: a `context_chunks` list containing both a
`{"text": None}` chunk and a valid-text chunk. Beyond asserting no crash, it
asserts `score > 0.5` to prove the valid chunk's text still contributes
rather than being silently dropped. Verified the test genuinely guards the
regression — the pre-fix expression `chunk.get("text", "")` raises
`TypeError: sequence item 0: expected str instance, NoneType found` on this
input.

Re-ran both commands after the change: the set of failing tests is byte-for-byte
identical to the baseline (52 failed), with passed rising 376 → 377 from the new
test. Ruff still reports exactly 182 errors, so no new lint issues were
introduced. No new failures from this change.

**Next steps:** Open a draft PR, request peer review in Slack, finalize
PR description before deadline.

**Blockers:**
None blocking. Three tests in `test_faithfulness_checker.py`
(`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
`test_multiple_claims_varying_support`) fail at baseline, but for an unrelated
reason: `_is_supported` requires a 2-token non-stopword overlap, which short
claims can never meet. I checked the tracker and this is already filed as
issue #152, which names those exact three tests. Out of scope for #153, so I
left them untouched rather than overlapping with that issue.

---

### Check-in 2 (end of week)
**PR link:** https://github.com/ascherj/pathreview/pull/908 (open, ready for review)

**Branch:** fix/153-faithfulness-checker-none-text

**What you built:**
Fixed a `TypeError` crash in the RAG faithfulness checker that occurred when a
retrieved context chunk had `text: None`. The context-building expression used
`chunk.get("text", "")`, which only applies its default when the key is
missing — not when the key is present but `None` — so `" ".join()` received a
`None` and raised. Changed it to `chunk.get("text") or ""` so both the missing
key and the explicit `None` normalize to an empty string.

**Tests added or updated:**
Added `test_mixed_none_and_valid_context_chunk_text` to
`tests/unit/test_faithfulness_checker.py`, covering a mixed
`{"text": None}` + valid-text chunk list.

**Self-review confirmation:** [x] make check run and reviewed — no new errors
  [x] make test-unit run and reviewed — no new failures

  Both commands were run and their output compared against a baseline captured
  before any of my changes. Neither passes cleanly on this repo, and neither
  passes on `main` either — `make check` fails on 182 pre-existing ruff errors
  and `make test-unit` reports 52 pre-existing failures. That is expected: the
  repo has 67 open issues, and those failures *are* those issues. For example,
  #158 ("review_service unit tests misconfigure async mocks — 13 of 19 tests
  fail") accounts for the review_service failures, #151 the bias detector ones,
  #146 the PII scrubber ones, and #157/#156 the scorer fixtures. A fully green
  suite would mean every open issue was already fixed.

  What I verified is that my change is clean with respect to that baseline:

  | Command | Before | After |
  |---|---|---|
  | `make test-unit` | 52 failed, 376 passed | 52 failed, **377** passed |
  | `make lint` (ruff) | 182 errors | 182 errors |
  | `make typecheck` (mypy) | 103 errors / 26 files | 103 errors / 26 files |

  The failing-test set after my change is identical to the baseline set; the
  only delta is the passing count rising by one, from the test I added.

  Note also that the three faithfulness-checker failures are already tracked as
  issue #152, which names those exact three tests. They are a separate defect
  (the `_is_supported` two-token overlap threshold) from the `None` handling
  fixed here, so I left them for whoever picks up #152.

**Draft PR feedback received from:** [PLACEHOLDER]