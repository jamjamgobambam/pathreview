## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker` class (in `rag/evaluator/faithfulness_checker.py`)
checks whether a claim is supported by a piece of context by requiring at
least 2 non-stopword tokens to overlap between them. This breaks down for
short factual claims — e.g. "Knows Python." only shares one meaningful token
("Python") with a fully supporting context like "python expert," so it's
always scored as unsupported even though it's correct. As a result, feedback
made up of short, valid claims can score 0.0 faithfulness, which is
misleading. A successful fix would adjust the overlap threshold or scoring
logic so that short claims can be correctly marked as supported, fixing the
related failing tests (`test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, `test_multiple_claims_varying_support`) in
`tests/unit/test_faithfulness_checker.py`.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [ ] App runs locally at localhost:5173
*(Note: backend starts but crashes on a Postgres connection error during
startup — DB isn't reachable. Frontend also blocked initially by npm not
being installed, since resolved. Still working through the Postgres piece.)*

**Cohort ledger:** [ ] Issue added to cohort ledger















## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/clem0g/pathreview/commit/b12000e

**Reproduction summary:**
Ran the reproduction snippet from the issue against
FaithfulnessChecker.check() -- confirmed a faithfulness score of 0.0 for
two short claims ("Knows Python.", "Knows SQL.") that are both fully
supported by their matching context chunks. Also noticed only 1 claim was
counted instead of 2, tracing to a separate length-filter issue in
_extract_claims() that drops sentences under 10 characters -- noted in
PLAN.md as a related but out-of-scope finding.

**PLAN.md link:** https://github.com/clem0g/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
Need to decide whether the scaled overlap threshold should count raw
tokens or non-stopword tokens only, and whether the _extract_claims()
length-filter bug is in scope for this issue or should be filed
separately.
