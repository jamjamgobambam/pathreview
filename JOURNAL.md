# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The partial-overlap unit test for the relevance scorer currently uses a query and chunk that share every query term. Because the scorer measures how many query keywords appear in the retrieved text, it correctly returns a full score of 1.0, while the test incorrectly expects a score below 0.9. The problem is confined to the fixture in `tests/unit/test_relevance_scorer.py`, rather than the scoring implementation in `rag/evaluator/relevance_scorer.py`. A successful fix will make the fixture contain only some of the query terms so the test accurately exercises partial keyword overlap.

**Selection reasoning:**
This issue is appropriate for my first contribution because it is a clearly defined Tier 1 problem limited to one test fixture. The issue supplies a direct reproduction command, and the existing scorer implementation makes the expected behavior straightforward to verify. It does not require database changes, external API access, or changes across multiple application layers. I also confirmed that the issue was open, unassigned, had no comments, and had no competing claim when I selected it.

**Branch name:** test/157-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/DhivyaSriLingala/pathreview/commit/66d88ee

**Reproduction summary:**
I ran the targeted `test_query_with_partial_overlap` test and reproduced the failure consistently. The relevance scorer returned `1.0` because all four query tokens occur in the fixture text, causing the test's expected middle-range assertion to fail.

**PLAN.md link:** https://github.com/DhivyaSriLingala/pathreview/blob/test/157-partial-overlap-fixture/PLAN.md

**Walkthrough video (recommended):** Not recorded; this optional item is not graded.

**Blockers or open questions:**
No current blockers. The evidence indicates that the test fixture should change while the production relevance-scoring implementation remains unchanged.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed every implementation sub-task from `PLAN.md` and opened draft PR
[#343](https://github.com/ascherj/pathreview/pull/343). The partial-overlap
fixture now shares exactly two of the query's four unique tokens, producing a
deterministic score of `0.5`; the targeted test passes, and all 19 relevance
scorer tests pass.

**Next steps:**
I will request peer or mentor feedback on the draft PR, address any actionable
feedback, mark the PR ready for review, and complete Check-in 2 with the final
validation results.

**Blockers:**
Peer or mentor review is pending. Repository-wide validation has 182
pre-existing lint errors and 52 pre-existing unit-test failures after this
fix; the contribution introduced no new failures and removed the issue #157
failure from the baseline of 53.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/343

**Branch:** `test/157-partial-overlap-fixture`

**What you built:**
I corrected the partial-overlap test fixture so it contains exactly two of the
query's four unique tokens and produces the intended relevance score of `0.5`.
The production relevance-scoring code did not need to change because it was
already calculating the overlap correctly.

**Tests added or updated:**
I updated `tests/unit/test_relevance_scorer.py`. The targeted partial-overlap
test passes, all 19 relevance-scorer tests pass, and the repository-wide unit
test comparison improved from 53 failures and 375 passes to 52 failures and
376 passes without introducing any new failures.

**Self-review confirmation:** [x] `make check` baseline compared: no new failures  [x] `make test-unit` baseline compared: no new failures

The repository-wide commands still report documented pre-existing failures:
182 Ruff errors and 52 unrelated unit-test failures. Per the assignment's
baseline rule, these confirmations record that my contribution introduced no
new failures; they do not claim that the repository-wide commands were fully
green.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes (automated Copilot review)  [ ] No

**Summary of feedback:**
GitHub Copilot identified misleading present-tense wording in
`REPRODUCTION.md`, a platform-specific reproduction command, and self-review
checkboxes in `JOURNAL.md` that implied the repository-wide checks were fully
green. This automated review does not count as the required human peer or
mentor review, which is still pending.

**How you responded:**
I updated `REPRODUCTION.md` to identify the pre-fix upstream baseline, use a
platform-neutral `pytest` command, and describe the old fixture behavior in
the past tense. I also reworded the self-review confirmation to state that the
before-and-after baselines had no new failures rather than claiming fully
passing repository-wide checks.

---

### Reflection

**What was harder than you expected?**
Separating a bad test fixture from a production-code defect was harder than I
expected. The failing assertion initially made the scorer look incorrect, but
tracing its set-intersection calculation showed that the original chunk
contained all four query terms and therefore deserved a score of `1.0`. It
was also challenging to distinguish my result from the repository's existing
52 unit-test failures and 182 lint errors, which required before-and-after
baseline comparisons instead of relying on a single green command.

**What did you learn about working in a large codebase?**
I learned that a narrow issue should lead to a narrow change, supported by
evidence from the implementation and nearby tests. In someone else's
codebase, changing production behavior just to satisfy one failing test can
create regressions, so I first reproduced the failure, read the scoring logic,
calculated the expected token overlap, and changed only the fixture. I also
learned that contribution work includes following branch and commit
conventions, documenting known baseline failures, and making the PR easy for
a maintainer to evaluate.

**How did AI tools help — and where did they fall short?**
AI tools helped me navigate the repository, interpret the relevance formula,
compare baseline and post-change test results, and draft clear journal and PR
documentation. They were especially useful for turning test output into a
focused investigation and checking that the final diff stayed within scope.
However, AI could not replace my judgment about whether the test or production
code was wrong, and it could not resolve the project's unrelated failures or
obtain human review. I still had to verify the token math, inspect the actual
code, run the tests, and decide which suggested changes belonged in this PR.

**What would you do differently if you started over?**
I would capture the repository-wide test and lint baseline immediately after
setup and before beginning issue work. That would make it faster to prove that
later failures were pre-existing. I would also ask my instructor about the
correct Slack review channel earlier and complete both Week 9 check-ins as
soon as each milestone was reached instead of filling in the final check-in
later.

**What are you most proud of from this module?**
I am most proud that I resisted expanding a one-line fixture problem into an
unnecessary production-code change. I reproduced the issue, explained the
root cause with a concrete `2 / 4 = 0.5` expectation, made a minimal fix, and
used focused plus repository-wide validation to show that the contribution
removed the intended failure without making the existing baseline worse.
