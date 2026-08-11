## Week 7 — Issue selection

**_Issue link:_** https://github.com/ascherj/pathreview/issues/152

**_Issue title:_** Faithfulness checker can never mark short claims as supported

**_Tier:_** [X] Tier 1 [ ] Tier 2 [ ] Tier 3

**_Problem summary:_**
Short, accurate claims get scored 0.0 by the faithfulness evaluator. The problem is in `_is_supported()`: it only counts a claim as supported if it shares at least two non-stopword tokens with the context chunks. Short claims often have just one. So feedback like "the candidate knows Python" has a single matching token, falls under the threshold, and gets flagged as unsupported even though it's true. The fix has to score these one-token claims correctly without weakening the check for longer, multi-token claims.

**_Branch name:_** fix/152-short-claims-faithfulness

**_Setup confirmation:_** [X] App runs locally at localhost:5173

**_Cohort ledger:_** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ocabezas95/pathreview/commit/6f60da3e705d350cee6fc50ab66c1e8bf4fa267c

**Reproduction summary:** Reproduced short claims faithfulness scoring issues locally by running `pytest tests/unit/test_faithfulness_checker.py`. Observed assertions failing where `FaithfulnessChecker.check()` returned `0.0` or raised a `TypeError` on short claims/chunks, failing to parse single/short sentence claims correctly.

**PLAN.md link:** https://github.com/ocabezas95/pathreview/blob/fix/152-short-claims-faithfulness/PLAN.md

**Walkthrough video (recommended):** None

**Blockers or open questions:** None

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** I have fully implemented the fix for Issue #152. I updated `faithfulness_checker.py` to handle `None` context chunks safely and refactored `_extract_claims` and `_is_supported` to correctly parse and score short claims. All `PLAN.md` sub-tasks are complete, and `make test-unit` (including a new short claim test) and `make check` pass successfully.

**Next steps:** Open a draft PR on GitHub to get feedback, refine if necessary, and then submit the final Pull Request by the Sunday deadline.

**Blockers:** None at this time!

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/377

**Branch:** `fix/152-short-claims-faithfulness`

**What you built:** I fixed an issue where short claims were being incorrectly discarded and evaluated as 0.0. I updated the context string concatenation to safely handle `None` values and refactored the claim extraction and overlap logic to scale down required token matches for short sentences.

**Tests added or updated:** Added `test_short_claims_retained_and_evaluated` to `tests/unit/test_faithfulness_checker.py` to ensure concise claims are preserved and scored correctly.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
N/A (Summer 2026 cohort — no reviewer feedback assigned)

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Balancing the claim extraction logic so that it splits sentences effectively without creating false positives or breaking short valid phrases was trickier than expected. Handling subtle edge cases—such as `None` values in `context_text` causing unexpected `TypeError`s during evaluation also required careful safe-checking that wasn't immediately obvious when first inspecting the issue.

**What did you learn about working in a large codebase?**
Working in an established codebase means adhering strictly to existing conventions and testing practices. Bypassing existing environment issues (like pre-existing `mypy` type hint warnings) while ensuring that all 23 unit tests passed and writing targeted new test cases taught me how to isolate my changes without breaking surrounding infrastructure.

**How did AI tools help — and where did they fall short?**
AI tools were very helpful for quickly pinpointing where the short claim length constraint was failing in `_is_supported` and generating initial regex patterns for splitting conjunctions. However, they fell short when dealing with dynamic token overlap logic and edge cases like `None` safe-checking, which required hands-on debugging and precise logical structuring.

**What would you do differently if you started over?**
If starting over, I would write unit tests for edge cases (like short 1-token claims and `None` handling) _before_ attempting the fix, following a stricter Test-Driven Development (TDD) workflow to verify the failure modes earlier in the process.

**What are you most proud of from this module?**
I am most proud of creating a comprehensive fix that solved both the primary short claim faithfulness scoring bug and underlying null handling, backed by a clean PR with unit tests verifying full test suite compliance.
