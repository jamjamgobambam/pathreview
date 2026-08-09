## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
FaithfulnessChecker._is_supported() (rag/evaluator/faithfulness_checker.py) marks a claim as supported only if it shares at least two non-stop-word tokens with the retrieved context. Short claims like "Good indentation" have just two or three content words total, so nearly every token must match the context to hit the threshold. If there were any small thing to break it, like a plural, tense change, or synonym, it drops the overlap to one and fails the claim even when it's true. This fixed threshold makes it so short correct claims can structurally never clear. A fix should scale the required overlap to claim length rather than using a flat >= 2 cutoff.

**Branch name:** fix/152-faithfulness-short-claims-not-supported

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/gzam1028/pathreview/commit/a49fe21

**Reproduction summary:** Added a failing unit test in `tests/unit/test_faithfulness_checker.py` showing that `FaithfulnessChecker._is_supported()` requires at least two non-stop-word tokens to overlap between a claim and the context, regardless of how many content words the claim actually has. A short claim like "Good communicator" (2 meaningful tokens: "good", "communicator") is checked against the paraphrased context "Excellent communicator with clients and stakeholders" — only "communicator" overlaps (1 token, since "excellent" isn't "good"), so it's marked unsupported even though the claim is clearly true. The test asserts `supported is True` and currently fails with `assert False is True`, proving the bug is real and not just a misreading of the issue description.

**PLAN.md link:** https://github.com/gzam1028/pathreview/blob/fix/152-faithfulness-short-claims-not-supported/PLAN.md

**Blockers or open questions:**
The fix will require flipping the expected value of an existing test (`test_minimum_overlap_required`) since it currently documents the same buggy threshold behavior on purpose. Need to make sure that change is explained clearly in the PR so it doesn't look like an accidental regression. No blockers on the environment or reproduction itself.

## Week 9 — Solution building & PR submission

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1015

**Branch:** fix/152-faithfulness-short-claims-not-supported

**What you built:** `FaithfulnessChecker._is_supported()` (rag/evaluator/faithfulness_checker.py) now lowers the required token overlap to 1 for claims with 2 or fewer meaningful tokens, instead of always requiring 2 regardless of claim length. Longer claims still require the original 2-token floor, so vague or padded claims still need real evidence rather than a single lucky keyword match.

**Tests added or updated:** `tests/unit/test_faithfulness_checker.py` — flipped the reproduction test (`test_short_claim_with_partial_paraphrase_should_be_supported`) to pass, updated `test_minimum_overlap_required`'s expected value with an explanation for why it changed, and added three new edge-case tests: a single-meaningful-token claim that matches, one that doesn't, and a longer claim confirming the original 2-token floor still holds.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass for the files this PR touches. `make check`/`make test-unit` fail at the whole-repo level due to pre-existing, unrelated issues — documented in the PR description with a before/after comparison confirming this PR introduces no new failures.)

**Draft PR feedback received from:** none — opened directly as ready for review, no draft review cycle this time.
