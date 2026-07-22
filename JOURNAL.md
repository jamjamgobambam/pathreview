# Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `BiasDetector` in `safety/bias_detector.py` relies on a small set of rigid
regular expressions that only fire on very specific word sequences — e.g. it
catches "bootcamp education is insufficient" but misses common paraphrases like
"bootcamp grads usually aren't as capable" or "someone with only a self-taught
background probably isn't ready." Because the patterns demand near-exact
phrasing and fixed word order, most real-world biased statements about
educational background, age, and demographic identity pass through undetected
(false negatives), defeating the safety guardrail's purpose. A successful fix
broadens the detection patterns to match common phrasings and sentence
structures for the same underlying bias, while keeping them specific enough not
to over-flag legitimate neutral or positive mentions. The change is contained to
the `DISMISSIVE_PATTERNS` / `DEMOGRAPHIC_PATTERNS` lists (and their tests), so
it's a focused, low-blast-radius Tier 1 fix.

**Branch name:** `fix/151-bias-detector-patterns`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
