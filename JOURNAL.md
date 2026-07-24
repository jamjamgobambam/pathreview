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

**Reproduction commit link:** TBD

**Reproduction summary:**
I reproduced Issue #157 by running `pytest tests/unit/test_relevance_scorer.py -q`. The test suite reported `1 failed, 18 passed`, with `test_query_with_partial_overlap` failing because the scorer returned `1.0` while the assertion expected a score between `0.3` and `0.9`. The fixture contains all four query terms—`Python`, `Django`, `web`, and `framework`—so it represents full overlap rather than the intended partial overlap.

**PLAN.md link:** TBD

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
None at this stage.
