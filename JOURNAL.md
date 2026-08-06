# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker` in `rag/evaluator/faithfulness_checker.py` scores generated
feedback by splitting it into claims (sentences) and checking each claim for keyword
overlap with the retrieved context. The `_is_supported()` helper requires at least 2
non-stopword tokens to overlap between a claim and the context text before it counts
the claim as supported. Short factual claims like "Knows Python." contain only one
meaningful token ("python"), so even when the context fully backs the claim (e.g. a
chunk containing "python expert"), the overlap can never reach the threshold of 2 and
the claim is always marked unsupported. This silently zeroes out the faithfulness
score for any feedback made up of short, accurate sentences, which is exactly the
style of feedback this evaluator is meant to check, and it's also why several existing
unit tests (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
`test_multiple_claims_varying_support`) currently fail. A successful fix adjusts the
overlap threshold logic so it scales with claim length instead of using a fixed
minimum of 2, so short but genuinely supported claims score correctly.

**Scope reasoning ("Is this right for me?" checklist):**
- Reproduction is already given in the issue (a 3-line script) and reproduces against a
  single function, so I can confirm the bug before writing any code.
- The fix is isolated to one file (`rag/evaluator/faithfulness_checker.py`) and doesn't
  require touching the API, frontend, or any external service — low blast radius.
- There are already three named failing unit tests
  (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
  `test_multiple_claims_varying_support`) that define what "done" looks like, so I have
  a concrete, checkable success criterion rather than an open-ended judgment call.
- Tier-1 label matches this being my first issue in the codebase.
- Risk: I need to make sure the new overlap threshold doesn't just special-case short
  claims but stays consistent for longer ones too — worth checking the full test file,
  not just the three named tests, before opening a PR.

**Branch name:** fix/152-faithfulness-checker-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/grenver/pathreview/commit/6d9352dc92c32ea08ad0242cca4302afb160e031

**Reproduction summary:**
Ran the issue's exact repro script locally: `FaithfulnessChecker().check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}])` returns `0.0`. Tracing it further, I found the bug is actually two compounding issues in `faithfulness_checker.py` — `_extract_claims()`'s `len(s.strip()) > 10` filter silently drops "Knows SQL" before it's ever scored (only 1 of 2 claims gets extracted), and `_is_supported()`'s fixed `>= 2` token-overlap threshold means the one remaining claim ("Knows Python") can never be marked supported since it only has one meaningful token ("python"). Documented both with inline comments at the exact lines in the commit above; confirmed via `pytest tests/unit/test_faithfulness_checker.py` that this produces 4 failing tests (the 3 named in the issue, plus one unrelated pre-existing bug I flagged separately in PLAN.md).

**PLAN.md link:** https://github.com/grenver/pathreview/blob/fix/152-faithfulness-checker-short-claims/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
No blockers. Still deciding on the exact scaling formula for the overlap threshold (ratio-based vs. a sliding minimum) — noted as an open risk in PLAN.md and something I may bring to office hours before finalizing the implementation in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented both fixes from PLAN.md in `rag/evaluator/faithfulness_checker.py`: removed the `len() > 10` filter in `_extract_claims()`, and replaced the fixed `>= 2` overlap threshold in `_is_supported()` with one that scales to the claim's own meaningful-token count (1 for claims with <=2 meaningful tokens, 2 otherwise). Landed on the scaling formula I was undecided on in Week 8 — a sliding minimum rather than a pure ratio, since a ratio-based threshold made longer claims incorrectly *harder* to support than before. Along the way also found and fixed a real tokenization bug (`.split()` left punctuation attached to words, e.g. `"PostgreSQL,"` never matched `"PostgreSQL"` in context) and had to switch `check()` from a binary supported/unsupported count to a proportional per-claim score, since a couple of existing tests expect a "middle" score from feedback that's structurally a single claim — impossible with pure binary scoring. Added a regression test reproducing the issue's exact repro script. All 3 named tests pass; verified via diff against a stashed baseline that no other test in `tests/unit/` regressed.

**Next steps:**
Run `make check` and `make test-unit`, finalize the PR description (including documenting pre-existing failures per the module's guidance), and open the PR against upstream for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/352

**Branch:** `fix/152-faithfulness-checker-short-claims`

**What you built:**
Fixed two compounding bugs in `FaithfulnessChecker` that caused short, accurate feedback claims (e.g. "Knows Python.") to always score as unsupported: a length filter dropped them before scoring, and a fixed overlap threshold was unreachable for short claims. The overlap requirement now scales with claim length, and `check()` gives proportional credit per claim instead of a strict binary count.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — added `test_short_claims_fully_supported_score_1`, a regression test reproducing the issue's exact repro script. No other test files touched; the 3 previously-failing named tests (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) now pass unmodified.

**Self-review confirmation:** [x] make check passes (on changed files — see PR for pre-existing repo-wide failures) [x] make test-unit passes (zero new failures vs. stashed baseline)

**Draft PR feedback received from:** none yet — opened as draft for review

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No comments or reviews have landed on [PR #352](https://github.com/ascherj/pathreview/pull/352) as of the end of Week 10. Per the Su26 course note, reviewer feedback isn't a feature this term, so this is expected rather than a sign the PR is stalled.

**How you responded:**
N/A — nothing to respond to. If feedback arrives after this journal is submitted, I'll continue watching the PR and would document any follow-up here retroactively.

---

### Reflection

**What was harder than you expected?**
The issue as filed described a single bug — a token-overlap threshold that's unreachable for short claims. Reproducing it in Week 8 turned up a second, compounding bug (a `len() > 10` character filter in `_extract_claims()` that silently dropped short claims before they were ever scored), and implementing the fix in Week 9 turned up a third, unrelated tokenization bug where trailing punctuation on words like `"PostgreSQL,"` broke overlap matching entirely. None of these were visible from reading the issue text — each only showed up once I actually ran the repro script and read the function line by line. I underestimated how much of the work is confirming an issue is fully and correctly scoped before touching any code, rather than just implementing the fix the issue description implies.

**What did you learn about working in a large codebase?**
The existing test suite carried more of the design intent than the issue or the code comments did. `test_partial_support_returns_middle_score` is what told me `check()` needed to return a proportional score rather than a binary supported/unsupported count — that requirement wasn't stated anywhere except as an assertion in a test I wasn't asked to touch. I also learned to treat "did I break anything else" as a first-class step: diffing test results against a stashed baseline before opening the PR, and separating pre-existing repo-wide failures from ones my change introduced, mattered more here than in a solo project where I'd just trust a green test run.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical parts: tracing execution through `_extract_claims()` and `_is_supported()` to pinpoint exactly which line dropped each claim, and drafting the regression test once I knew what behavior it needed to lock in. It fell short on the actual design decision — whether the overlap threshold should scale as a ratio of claim length or as a sliding minimum. A ratio-based threshold looked cleaner in the abstract but, when I worked through concrete examples by hand, it made longer claims *harder* to support than the original fixed threshold, which is the opposite of what the fix was supposed to do. That tradeoff only became visible by reasoning about specific example claims myself, not from a general suggestion.

**What would you do differently if you started over?**
I'd run the full unit test file before writing any plan in Week 8, not just the named failing tests from the issue. I did eventually check the whole file before opening the PR, but doing it earlier would have surfaced the proportional-scoring requirement and the tokenization bug during planning instead of during implementation, which would have made the Week 9 PLAN-to-code step more predictable and less like debugging-while-building.

**What are you most proud of from this module?**
Catching the tokenization bug. It wasn't in the issue, wasn't required by any of the three named failing tests, and I could have shipped a passing fix without ever finding it — the three named tests happened to use words without trailing punctuation. Deciding to keep digging past "the named tests pass" and verify the fix against cases the issue didn't explicitly cover is the habit I most want to carry into the next codebase I contribute to.
