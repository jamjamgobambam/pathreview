## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/90

**Issue title:** Add integration tests for authentication edge cases

**Tier:** [ ] Tier 1  [✅] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, tests for auth middleware check if a token is valid or not. However, these tests do not include edge cases like expired tokens, malformed tokens, tokens assigned with a different secret, and missing `Authorization` headers, all of which follow a valid token format but aren't tokens that can be used. This PR adds those edge cases into the unit tests to ensure the bad tokens can be caught instead of silently ignored. 

**Branch name:** feat/90-auth-edge-cases-tests

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]