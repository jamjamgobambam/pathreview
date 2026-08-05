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

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/phan228/pathreview/commit/2145085

**Reproduction summary:**
I called the detector directly with a common biased phrasing that falls outside its rigid regex templates — `python -c "from safety.bias_detector import BiasDetector; print(BiasDetector.detect_bias('Bootcamp grads just aren\'t as capable as real CS majors.'))"` — and it returned `(False, '')`, confirming the narrow patterns let clearly biased statements slip through as false negatives.

**PLAN.md link:** https://github.com/phan228/pathreview/blob/fix/151-bias-detector-patterns/PLAN.md

**Blockers or open questions:** None

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Core fix is implemented in `safety/bias_detector.py`. Done from PLAN.md:
restructured the pattern data into per-category subject/predicate/reason groups
(education, age, origin, and the new gender category); replaced the rigid
full-sentence regexes with a subject × dismissive-predicate co-occurrence match
within an 8-word window (either order); expanded the vocabulary; and added the
artifact guard so critique of a work item ("bootcamp project … lacks tests")
isn't misread as bias about the person. Added tests for the 8 reproduced
phrasings, a gender case, and the artifact near-miss — all 42 bias tests pass,
and ruff/black/mypy are clean on the changed files.

**Next steps:**
Open the PR against `ascherj/pathreview` linking issue #151, do a final
self-review, and fill in Check-in 2.

**Blockers:**
The repo has pre-existing, unrelated failures (`make test-unit`: 44 failures in
skill_extractor/tech_detector/structural_chunker; `make check`: ~179 lint errors
repo-wide) that exist on the base branch independent of this change. They make
the repo-wide gates red even though the changed files pass on their own.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/868

**Branch:** `fix/151-bias-detector-patterns`

**What you built:**
Broadened the bias detector so it flags common paraphrasings of biased feedback,
not just near-verbatim templates. It now matches when a demographic/educational
*subject* co-occurs with a *dismissive predicate* within a small word window (in
either order), which catches false negatives while leaving neutral and positive
mentions unflagged; it also adds a previously-missing gender bias category.

**Tests added or updated:**
`tests/unit/test_bias_detector.py` — added a parametrized test for the 8
reproduced phrasings, a gender-bias detection test, and an artifact near-miss
test (critique of a "bootcamp project" must not be flagged as bias about the
person). All existing positive/neutral tests remain green as false-positive
guards.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Note: both boxes are left unchecked because `make check` and `make test-unit`
> fail repo-wide due to pre-existing issues unrelated to this change (see
> Check-in 1 blockers). The files changed in this PR pass ruff, black, and mypy,
> and all 42 tests in `tests/unit/test_bias_detector.py` pass.

