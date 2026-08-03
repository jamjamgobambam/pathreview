
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
### Check-in 2

**Current progress:**
Implemented the fix for issue #151 in `safety/bias_detector.py` — replaced
the exact-phrase regex approach with clause-level matching: a clause is
flagged only when it contains both a protected-category term (educational
background, age, or socioeconomic/national background) and a dismissive
or negative-capability term. This directly addresses the root cause traced
in PLAN.md (patterns anchored to singular nouns, specific verbs like
"is"/"lack", and rigid connective phrases like "person from").

Also fixed one regression caught during testing: the original
`(?:equal|comparable)` negative pattern only matched "not equal/comparable
to" and missed "never equal/comparable to" — added "never" as an
alternative.

**Testing:**
- `pytest tests/unit/test_bias_detector.py -v` — 32/32 passing (all 9
  originally-failing tests now pass; all 23 originally-passing tests
  still pass, confirming no regressions)
- `make check` — passing (ruff, black, mypy all clean)
- `make test-unit` — passing

**Manual verification:**
Re-ran the original repro from issue #151:
> "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education"

Previously returned `(False, '')`. Now correctly returns
`(True, "Dismissive language about educational background")`.

**PR status:**
Opened as draft: https://github.com/arshadshiju/pathreview/pull/152
Branch: `fix/151-bias-detector-pattern-matching`
Commit: `fdb1cd7`

**Next steps:**
Get peer feedback on the draft PR, address any review comments, then mark
ready for final review.

**Blockers:**
None currently.
