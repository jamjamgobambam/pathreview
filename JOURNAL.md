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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback has come in on PR #1015 as of this entry. Per the course's Su26 note, reviewer feedback isn't part of this cycle, so there's nothing further to document here.

**How you responded:**
N/A — no feedback received.

---

### Reflection

**What was harder than you expected?**
The pre-existing state of the repo, not the actual bug. The fix itself — scaling the overlap threshold instead of using a flat cutoff — took less time than expected once I'd pinned down the root cause. What actually slowed me down was that the moment I touched `test_faithfulness_checker.py`, pre-commit hooks surfaced 26+ mypy errors and a ruff unused-variable error that had nothing to do with my change — the whole file had apparently never passed those hooks before. I had to add type annotations across every test function in the file and complete two pre-existing tests that asserted nothing, just to get my own change to commit cleanly. I hadn't anticipated that fixing one bug would mean cleaning up unrelated debt just to get through the door.

**What did you learn about working in a large codebase?**
The biggest shift was realizing I couldn't trust "my tests pass" in isolation — I had to explicitly diff the full failure list before and after my change (using `git stash` to compare) to prove I hadn't broken anything else, because the suite already had dozens of unrelated pre-existing failures scattered across the codebase. In my own projects I'd just run the tests and call it done; here, "passing" only meant something once I'd separated my change's effect from the codebase's existing rot. I also learned that pre-commit hooks apply to the whole file you touch, not just your diff — so a small, well-scoped fix can pull in unrelated cleanup work whether you plan for it or not.

**How did AI tools help — and where did they fall short?**
AI was most useful early on: reading the actual source for several candidate issues in parallel and reporting back real difficulty (not just what the issue title implied) helped me pick a problem that was genuinely medium difficulty instead of over- or under-shooting it. It was also fast at pinpointing the exact line responsible for the bug and building a concrete before/after repro I could run myself. Where it fell short was on the first attempt at the actual fix — the first scaling formula it proposed looked reasonable on paper but, when we ran the full test suite instead of just the new test, it turned out to make longer claims stricter than before and broke a previously-passing test. That only surfaced because we actually executed the change against the whole file's tests rather than trusting the formula's logic by inspection. It reinforced that AI-generated code needs to be run and verified, not just reasoned about.

**What would you do differently if you started over?**
I'd pick a different issue. #152 was a reasonable "medium" pick on its own, but it turned out to be entangled with two other known bugs in the same file (#153's `None`-crash and a separate `_extract_claims()` comma-splitting bug), which made it harder to cleanly tell "is this failure mine or pre-existing?" every time I ran the tests. An issue more isolated from other in-flight bugs in the same file would have let me verify my own change faster and with more confidence, instead of having to cross-check against a noisy baseline every time.

**What are you most proud of from this module?**
Diagnosing the root cause precisely. Rather than stopping at "short claims sometimes fail," I traced it to the exact line (`len(meaningful_overlap) >= 2`) and built a minimal, concrete example — "Good communicator" vs. a paraphrased context — that showed exactly one token short of the threshold. Having that precise a repro made both the fix and the PR description much easier to write, because there was no ambiguity about what "fixed" actually meant.
