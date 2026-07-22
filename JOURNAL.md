## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue is about a bug in the agent workflow where state from one review can carry over into a later review for the same user. That stale session information can cause the next review to behave incorrectly or reuse context that should have been reset. A successful fix would ensure each new review starts with a clean agent session so the behavior is consistent and predictable.

**Branch name:** chore/43-week7-setup

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Selection notes:**
This issue is a good fit for a Week 7 submission because it is focused on project setup and contribution workflow rather than a large feature implementation. The scope is limited enough for a first contribution, and the work mainly involves documenting or clarifying setup expectations rather than changing core application behavior.
