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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in _is_supported() / added _support_score() and
_tokenize() in rag/evaluator/faithfulness_checker.py, per steps 1-2 of
PLAN.md. Replaced the hardcoded ">=2 overlap" boolean check with a
continuous overlap-ratio score (square-rooted), which also fixes
punctuation not being stripped from tokens. Confirmed via repro_152.py
that the reported bug is fixed, and confirmed via pytest that all 22
existing tests in test_faithfulness_checker.py pass, including the three
tests named in the issue that previously required this fix.

**Next steps:**
Run make check and make test-unit for full self-review, confirm no new
failures introduced (49 pre-existing failures observed, all in unrelated
modules), open a draft PR for peer/mentor feedback, then finalize and
submit by Sunday.

**Blockers:**
None currently -- the codebase has pre-existing lint errors and test
failures unrelated to this issue, documented in the PR description rather
than blocking this work.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/944

**Branch:** fix/152-faithfulness-short-claims

**What you built:**
Fixed FaithfulnessChecker._is_supported() so short claims (e.g. a single
distinctive term) can be correctly marked as supported. Replaced the
hardcoded "2+ overlapping tokens" boolean check with a continuous
_support_score() based on the fraction of a claim's meaningful tokens
found in context, and fixed punctuation not being stripped from tokens.

**Tests added or updated:**
No new test file added -- all fixes verified against the existing
tests/unit/test_faithfulness_checker.py, all 22 of which pass, including
the three tests named in issue #152. Added repro_152.py as a standalone
reproduction/regression script (not part of the pytest suite).

**Self-review confirmation:** [x] make check passes (for faithfulness_checker.py; 
pre-existing unrelated lint errors documented in PR description)
[x] make test-unit passes (for test_faithfulness_checker.py; 49 pre-existing
unrelated failures documented in PR description)

**Draft PR feedback received from:** [pending -- update once received]
