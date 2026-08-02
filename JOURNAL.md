# Project journal

## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The checker requires two matching non-stopword terms, so a short claim such as
`Knows Python` cannot be supported even when Python appears in the retrieved context.
The work is centered on `rag/evaluator/faithfulness_checker.py` and its unit tests. I
also included the related `text=None` failure from #153 at this checker's input
boundary, without claiming the separate suite-level path is fixed.

**Branch name:** `fix/152-faithfulness-short-claims`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Is this right for me?

- This is a Tier 1 change isolated to one evaluator and its tests.
- The issue provides a concrete input and expected score that can be reproduced first.
- Existing faithfulness tests provide a clear before-and-after target.
- General natural-language inference remains outside the scope of this lexical
  checker.

## Week 8 - Reproduction and solution planning

**Planning record commit:**
[d907e28](https://github.com/ahmedtaha100/pathreview/commit/d907e28083e80d84f5d5a9a308dd373eac4e7281)

**Failing reproduction commit:**
[1eb292b](https://github.com/ahmedtaha100/pathreview/commit/1eb292b3d11455a0f1995010d7334d637507450c)

**Reproduction summary:**
The exact `Knows Python. Knows SQL.` example returned `0.0` despite both facts being
present. Passing `{"text": None}` directly to `FaithfulnessChecker.check()` also
raised `TypeError`. At the reproduction commit, the two focused regression tests fail
for those reasons before the implementation is applied.

**PLAN.md:**
[Solution plan](https://github.com/ahmedtaha100/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md)

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The checker compares terms rather than meaning, so negation and entity attribution
remain known limitations. The repository also has unrelated baseline check failures,
which require a same-environment comparison.

**Working branch:**
[fix/152-faithfulness-short-claims](https://github.com/ahmedtaha100/pathreview/tree/fix/152-faithfulness-short-claims)

## Week 9 - Solution building and PR submission

### Check-in 1 (mid-week)

**Current progress:**
The exact #152 and checker-level #153 failures are reproduced. The implementation now
extracts narrowly reporter-led short claims, preserves the ordinary two-term support
rule, and skips malformed context text. Focused regression coverage is in place.

**Next steps:**
Run false-positive and technical-identifier probes, compare the complete unit failure
set with a fresh `main` worktree, finish the contribution checks, and make the PR
description match only the verified behavior.

**Blockers:**
The repository has unrelated unit, lint, formatting, and type-check failures on
`main`, so verification must use the course's documented no-new-failures process.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/211

**Branch:** `fix/152-faithfulness-short-claims`

**What you built:**
I updated the faithfulness checker so one-fact claims are scoreable only after a narrow
reporting verb such as `knows`. Ordinary claims keep the original two-term support
threshold, partial evidence receives proportional credit below that threshold, and
malformed context text is skipped without hiding valid sibling chunks.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` now covers the exact #152 reproduction, the
checker boundary from #153, supported and unrelated short claims, subject stripping,
the ten-claim cap, partial scores, punctuation, PascalCase dotted names, common
technical identifiers, and Unicode apostrophe and in-word hyphen variants. The
focused run passes all 55 collected cases with warnings treated as errors, reaching
100% checker coverage (86/86 statements and 28/28 branches).

The `make test-unit` equivalent reports `412 passed / 49 failed`, compared with
`375 passed / 53 failed` on a fresh same-environment `main`
worktree. The four original faithfulness failures now pass, and the remaining 49
failure node IDs are identical on both revisions.

**Self-review confirmation:** [x] `make check` passes*  [x] `make test-unit` passes*

\* GNU Make is unavailable in this Windows environment, so I ran each Makefile command
directly. Under the course's pre-existing-failure policy, these boxes mean the change
adds no failure: Ruff reports 180 existing errors versus 182 on `main`; Black
`--check` reports 50 files versus 52; and mypy reports the same 103 errors in 26 files
on both. Both changed Python files pass Ruff and Black, and the checker passes strict
mypy. Integration collection exits 5 with no tests on both revisions.

**Draft PR feedback received from:** none
