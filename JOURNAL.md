## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG faithfulness checker currently requires at least two meaningful
non-stopword tokens to overlap between a claim and its supporting context.
Short factual claims may contain only one meaningful token, so claims such as
“Knows Python” are marked unsupported even when the context clearly supports
them. This affects the `_is_supported()` logic in the faithfulness checker and
causes multiple unit tests to fail. A successful fix will allow short,
supported claims to receive credit while still preventing unrelated claims
from being classified as supported.

**Selection notes — “Is this right for me?” checklist reasoning:**
This issue is labeled Tier 1 and provides a clear reproduction example, the
specific function involved, and the names of related failing tests. Its scope
appears limited to the RAG faithfulness checker and its unit tests, rather than
requiring changes throughout the entire application. I should be able to
reproduce the bug locally and verify the solution using automated tests. Before
implementing the fix, I will inspect how short claims, stopwords, and token
overlap are currently handled so that the change does not introduce overly
permissive matching.

**Branch name:** fix/152-short-claim-faithfulness

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Reproduce issue #152](https://github.com/monikamarr/pathreview/commit/9d62939)

**Reproduction summary:**
I reproduced issue #152 by testing the short claims “Knows Python” and
“Knows SQL” against context containing “python expert” and “sql expert.”
The checker returned `0.0` instead of the expected `1.0` and reported only
one extracted claim, confirming that short supported claims are not handled
correctly.

**PLAN.md link:** [Solution plan](https://github.com/monikamarr/pathreview/blob/fix/152-short-claim-faithfulness/PLAN.md)

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**
I still need to determine how short claims should be evaluated without allowing
generic one-word overlaps to create false positives. I also need to confirm why
only one of the two short claims was extracted and whether compound claims
should be split into separately scored claims.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the planned fix for issue #152. Short meaningful claims are now
preserved during extraction, short claims can be supported by one meaningful
overlapping token, and longer claims use a stricter proportional overlap rule.
I also added safe handling for context chunks whose `text` value is missing or
`None`. The targeted faithfulness checker test suite passes all 23 tests.

**Next steps:**
I will complete the pull request documentation, perform a final self-review,
mark the PR as ready for review, and submit the branch URL through the course
portal.

**Blockers:**
The repository has pre-existing repository-wide lint, type-checking, and unit
test failures outside the files changed for this issue. The modified production
file passes Black, Ruff, and mypy, and all targeted faithfulness checker tests
pass.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/255

**Branch:** `fix/152-short-claim-faithfulness`

**What you built:**
I updated the faithfulness checker so short factual claims can be recognized as
supported when they share a meaningful technical term with the retrieved
context. I also preserved short claims during extraction, added stricter
proportional matching for longer claims, and safely handled missing or `None`
context text.

**Tests added or updated:**
I updated `tests/unit/test_faithfulness_checker.py` with a regression test for
the reported short-claim scenario. The full targeted test file passes 23 out of
23 tests.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

The repository contains documented pre-existing failures in repository-wide
lint, type-checking, and unit tests. My changes introduce no new failures in the
modified module, and the targeted tests and checks pass.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback was received during the course period, so no
changes were made after opening the pull request.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**

The hardest part was understanding an unfamiliar codebase well enough to make a
small, targeted change with confidence. At first I assumed the issue would only
require changing one function, but after reproducing the bug I realized I also
needed to understand how claims were extracted, how they were scored, and how
the existing tests described the intended behavior. Learning how to investigate
the code before making changes took more time than the implementation itself.

**What did you learn about working in a large codebase?**

I learned that contributing to someone else's project is much more structured
than building my own. Before writing any code, I had to reproduce the issue,
create a solution plan, understand the existing tests, and keep the scope of my
changes limited to the assigned issue. I also learned that repository-wide
failures are common in active projects and that the goal is to avoid introducing
new problems rather than trying to fix unrelated parts of the codebase.

**How did AI tools help — and where did they fall short?**

AI was most helpful for understanding unfamiliar code, planning the
implementation, explaining the purpose of existing functions, and helping me
navigate Git, testing, and the pull request workflow. However, I still needed to
verify every suggestion by reading the existing implementation and running the
tests myself. AI could suggest possible fixes, but it could not determine the
project's intended behavior without comparing the code, issue description, and
existing tests.

**What would you do differently if you started over?**

I would spend more time reading the existing implementation and tests before
writing any code. Early on I focused on solving the bug immediately, but I later
realized that understanding the surrounding design made the implementation much
simpler and reduced unnecessary changes. I would also open the pull request
earlier so there would be more time for feedback.

**What are you most proud of from this module?**

I'm most proud that I completed the full open-source contribution workflow from
start to finish. Instead of only fixing a bug, I reproduced the issue, planned
the solution, added a regression test, implemented the fix, verified it with
tests, and submitted a pull request following the project's contribution
process.