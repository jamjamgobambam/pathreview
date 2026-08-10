## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The test `test_query_with_partial_overlap` is intended to verify how the relevance scorer handles a partial match between a query and a retrieved chunk. However, the current chunk contains every word from the query, so the scorer correctly calculates a full-overlap score of `1.0`. The test then fails because its assertion expects the score to be below `0.9`. A successful fix would change the test data so that only some query terms overlap, while leaving the correctly functioning relevance scorer unchanged.

**Issue-selection reasoning:**

- **Understanding:** I can explain the problem and expected behavior without referring back to the issue. The test data represents full overlap even though the test is intended to represent partial overlap.
- **Affected code:** I located and read `test_query_with_partial_overlap` in `tests/unit/test_relevance_scorer.py`. I also reviewed the `score` and `_tokenize` methods in `rag/evaluator/relevance_scorer.py`.
- **Definition of done:** Before the fix, all four query terms match and the scorer returns `1.0`, causing the partial-overlap assertion to fail. After the fix, only some query terms should match, producing a score between `0.3` and `0.9`, and the test should pass.
- **Tier fit:** This is a Tier 1 issue and is appropriate for my first contribution to this codebase because the expected change is localized to a test fixture and does not require changes across multiple modules.
- **Codebase readiness:** I read the relevant test from start to finish and reviewed the scorer implementation to understand how the overlap score is calculated.
- **Testing:** I ran `pytest tests/unit/test_relevance_scorer.py -q` and reproduced the reported failure. The result was 1 failed and 18 passed, with the failing assertion showing that the score was `1.0`.
- **Rough plan:** I will update the test fixture so the query and chunk have genuine partial overlap, rerun the relevance scorer tests, and confirm that the production scorer code does not need to be changed.
- **Claims:** I checked the issue activity and cohort ledger and understand that claims are non-exclusive. I am comfortable continuing with this issue even though other contributors may also be working on it.
- **Time and scope:** The change is limited and should be achievable well before the Week 9 deadline.
- **Dependencies:** I did not find any stated unresolved blocker or dependency that must be completed before this issue can be fixed.

**Branch name:** fix/157-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Reproduce Issue #157](https://github.com/viswanathv4320/pathreview/commit/207c316)

**Reproduction summary:**
I reproduced Issue #157 by running `pytest tests/unit/test_relevance_scorer.py -q`. The test suite reported `1 failed, 18 passed`, with `test_query_with_partial_overlap` failing because the scorer returned `1.0` while the assertion expected a score between `0.3` and `0.9`.

The original fixture contains all four query terms—`Python`, `Django`, `web`, and `framework`—so it represents complete overlap rather than the intended partial overlap. This confirmed that the issue is located in the test fixture, not in the relevance scorer implementation.

**PLAN.md link:** [Solution plan](https://github.com/viswanathv4320/pathreview/blob/fix/157-partial-overlap-fixture/PLAN.md)

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the planned fix for Issue #157 by updating the fixture in `test_query_with_partial_overlap` so that the chunk contains only partial overlap with the query. The production relevance scorer code remains unchanged. The targeted test passes, and all 19 tests in `tests/unit/test_relevance_scorer.py` pass.

**Next steps:**
I will review the final diff, open the pull request against the upstream repository, and complete Check-in 2 with the final PR link.

**Blockers:**
The repository currently has pre-existing lint and unit-test failures unrelated to Issue #157. I confirmed that `main` has 182 lint errors and 53 failing unit tests. My branch has the same 182 lint errors and 52 failing unit tests because the intended relevance scorer test now passes.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/519

**Branch:** `fix/157-partial-overlap-fixture`

**What you built:**
Updated the `test_query_with_partial_overlap` fixture so that it represents genuine partial keyword overlap instead of full overlap. This fixes the failing test without changing the production relevance scorer implementation.

**Tests added or updated:**
Updated `tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap`. The targeted test passes, and all 19 relevance scorer unit tests pass.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
The broader checks still contain pre-existing repository failures. My branch has the same 182 lint errors as `main` and 52 failing unit tests compared with 53 on `main`; the difference is the relevance scorer test fixed by this PR.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**

The code change itself was simple. The harder part was confirming that the problem was in the test fixture rather than in the relevance scorer. I had to reproduce the failure, inspect the test and scorer logic, and compare my branch with `main` to confirm that other test failures were pre-existing.

**What did you learn about working in a large codebase?**

I learned that understanding context is important before changing code. I had to locate the relevant files, understand the expected behavior, reproduce the issue, and keep the change limited to the actual problem. I also learned that existing repositories may already have failing tests, so changes should be validated against the baseline.

**How did AI tools help — and where did they fall short?**

AI tools helped me understand unfamiliar code, interpret test results, plan debugging steps, and work through the Git and pull request workflow. However, I still had to verify the behavior by reading the code, reproducing the issue, running tests, and confirming that the proposed change was correct.

**What would you do differently if you started over?**

I would check the relevant test, implementation, and baseline test results earlier. This would help identify the root cause faster and separate pre-existing repository issues from problems introduced by my branch.

**What are you most proud of from this module?**

I am most proud of completing the full contribution workflow on an existing codebase: selecting an issue, reproducing it, planning the fix, making a focused change, testing it, documenting the work, and submitting a pull request.