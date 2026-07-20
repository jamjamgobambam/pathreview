## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bias detector module currently relies on regex patterns that only match
specific, near-exact phrasings of biased language, like "bootcamp graduates
lack rigor." It misses equivalent statements that express the same bias in
different words — for example, calling out someone's education informally or
making age-based assumptions about their ability to keep up with new tools.
Because the matching is too rigid, real instances of dismissive or
discriminatory language slip through undetected, which defeats the purpose
of a safety-layer component. Nine existing unit tests already define the
expected coverage and are currently failing, so a successful fix means
broadening the detection logic (likely moving from exact-phrase regex toward
more flexible pattern or keyword-based matching) until those tests pass
without introducing false positives on neutral text.

**Branch name:** fix/151-bias-detector-pattern-matching

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
