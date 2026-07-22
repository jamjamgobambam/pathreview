# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG evaluator's `FaithfulnessChecker` scores generated feedback by splitting it
into claims and checking whether each claim is backed by the retrieved context.
Two bugs in `rag/evaluator/faithfulness_checker.py` combine to make short,
factual claims unscoreable: `_extract_claims` discards any claim of 10
characters or fewer before it's even evaluated (e.g. "Knows SQL"), and
`_is_supported` requires a fixed minimum of two overlapping non-stopword
tokens between claim and context — a bar a one- or two-word claim can never
clear even when its single substantive word is fully present in the context.
The result is that short, clearly-supported claims are scored as unsupported,
dragging the faithfulness score down for reasons unrelated to actual
factual accuracy. A correct fix scores short claims on the strength of their
key terms rather than an absolute token count, so a claim like "Knows Python"
is recognized as supported when the context contains "Python".

**"Is this issue right for me?" checklist reasoning:**

*Part 1 — Understanding the Issue*
- [x] I can explain the problem and expected behavior in 2–3 sentences without reading the issue. `_is_supported` requires ≥2 overlapping non-stopword tokens between a claim and its context, and `_extract_claims` drops any claim ≤10 characters — together these mean a short claim like "Knows Python" can never be marked supported even when the context fully backs it (e.g. "python expert"), because it has at most one or two meaningful words to overlap.
- [x] I've located the relevant files and confirmed they exist in the codebase. `rag/evaluator/faithfulness_checker.py` (the two methods named above) and its test file `tests/unit/test_faithfulness_checker.py`, both confirmed present via the `rag` label on the issue.
- [x] I can describe a concrete before-and-after. Before: `checker.check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}])` returns `0.0`. After: it returns `1.0`, and the three tests named in the issue (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) pass.

*Part 2 — Tier Fit*
- [x] The tier is a realistic match. Issue is labeled `tier-1` on the tracker, and the fix is genuinely self-contained — one source file, one test file, no cross-module or API changes. This is my first issue this module, so Tier 1 is the right starting point rather than reaching for Tier 2/3 to "prove" something.

*Part 3 — Codebase Readiness*
- [x] I've found and read the specific code the issue references. Read both `_extract_claims` and `_is_supported` in full, not just skimmed the file.
- [x] I understand the surrounding code well enough to change it safely. Traced the call path (`check()` → `_extract_claims()` → `_is_supported()` per claim → `supported / len(claims)`) and confirmed via `git stash` diffing that no other module depends on the internal scoring mechanics beyond the returned float.
- [x] I've read the test file and at least one test end-to-end. Read all 23 existing tests in `test_faithfulness_checker.py`, matched their fixture/assertion style when adding `test_short_claims_can_be_supported`.

*Part 4 — Scope and Time*
- [x] Checked for other claimants. No comments, no assignees, and no linked PRs on the issue itself as of claiming it — confirm the cohort ledger's own Claims count yourself, since that's private to the course and not something I can check.
- [ ] Estimated the time and I'm confident I can finish before the Week 9 deadline. This is a personal judgment call on your workload — worth confirming for yourself, though the actual scope turned out to fit comfortably in a single focused session (well under the 3–6 hour Tier 1 estimate): a ~30-line logic change plus test updates.
- [x] No open blockers or dependencies. Issue has no "blocked by" reference and no linked unresolved issues.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/BharathChalla/pathreview/commit/a805d72

**Reproduction summary:**
Reproduced by instantiating `FaithfulnessChecker` directly and running the
issue's own example: `checker.check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}])`.
On `main` this returns `0.0` instead of the expected `1.0` — confirmed both
that `_extract_claims` was dropping "Knows SQL" (9 characters, under the old
10-character floor) and that `_is_supported` was rejecting "Knows Python"
for having only 1 overlapping non-stopword token against a 2-token minimum.
The linked commit's new regression test (`test_short_claims_can_be_supported`)
encodes this exact reproduction case, and the three tests the issue names
(`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
`test_multiple_claims_varying_support`) were failing on `main` for the same
root cause before the fix.

**PLAN.md link:** https://github.com/BharathChalla/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
None going into Week 9 — the fix, tests, and PR (#262) are already up given
how the reproduction and root-cause investigation played out this week. One
open judgment call noted in PLAN.md's Risks section: the new comma/"and"
claim-splitting could over-fragment feedback that uses "and" in a
non-listing sense (e.g. "fast and reliable"); flagged as a known limitation
rather than solved.
