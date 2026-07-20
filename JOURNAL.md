## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Scope-fit reasoning:**
Using the "Is this right for me?" checklist: the issue is scoped to a single
file (`bias_detector.py`), the fix is behavioral rather than architectural
(extending pattern matching, not redesigning a system), and there's an
existing test suite (9 failing tests) that defines exactly what "done"
looks like — which removes a lot of ambiguity for a first issue in an
unfamiliar codebase. It's labeled `tier-1` and doesn't touch other services
(no auth, no DB schema changes), so the blast radius if I get something
wrong is small. I chose it over other Tier 1 options specifically because
the failing tests give me a concrete, checkable definition of success
rather than open-ended judgment calls about what "good enough" means.

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

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
