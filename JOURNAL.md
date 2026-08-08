## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [✅] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The faithfulness checker scores a generated claim as "supported" only if at least 2 non-stopword tokens overlap between the claim and its retrieved context. This threshold doesn't scale down for short claims: a claim like "Knows Python." has only one meaningful token to begin with, so it can never reach the 2-token minimum even when the context fully supports it. As a result, reviews made up of short, accurate claims are incorrectly scored as unsupported, dragging the overall faithfulness score toward 0.0. The bug lives in `_is_supported()` in `rag/evaluator/faithfulness_checker.py`, and is covered by three failing tests already in the repo: `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, and `test_multiple_claims_varying_support`.

**Selection notes:**
Worked through the "Is this right for me?" checklist before claiming this issue.

- Scope: single-function fix in `_is_supported()`, well-contained, no architectural changes needed
- Familiarity: reviewed a related bug in the same file (#153) beforehand, so I understand the surrounding code and file structure
- Claimed status: confirmed via the Development sidebar that no branches or PRs are linked to #152, unlike several other tier-1 issues I checked first (#150, #153, #154 all had competing PRs already open)
- Test coverage: three related tests already exist in the repo, giving a clear, verifiable definition of "done"

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/JTasnim/pathreview/commit/f2530bb8a574aafa728cafaeedbe5f5efab6dfa4

**Reproduction summary:**

Ran `FaithfulnessChecker().check('Knows Python. Knows SQL.', [{'text': 'python expert'}, {'text': 'sql expert'}])`
locally and observed `0.0` despite both claims being fully supported. Confirmed the three tests
named in the issue (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
`test_multiple_claims_varying_support`) fail on main, while 18 other tests in the same file pass.


**PLAN.md link:** https://github.com/JTasnim/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Walkthrough video (recommended):** https://drive.google.com/file/d/1JWR5fG4MkvQQiAxwH1anCI2cP5upQr3Z/view?usp=sharing

**Blockers or open questions:**
Still deciding the exact scaling rule for the overlap threshold (e.g. ratio vs. fixed floor) —
will validate against the full existing test suite before finalizing in Week 9.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `_is_supported()` — the required token overlap now scales
with the claim's own meaningful token count (floor of 1) instead of using a fixed
threshold of 2. While testing against the three named tests, found two related
issues that also needed fixing to get all three passing: punctuation attached to
tokens (e.g. "Python,") blocked otherwise-identical matches, and `_extract_claims()`
treated compound sentences joined by "and" as one all-or-nothing claim instead of
independently-scored claims. Fixed both alongside the main threshold change.

Added `test_single_meaningful_token_claim_is_supported`, covering the exact
single-token case from the issue. Ran the full test file before and after:
baseline was `4 failed, 18 passed`; after the fix, `22 passed, 1 failed`
(`test_none_context_chunk_text` — confirmed pre-existing, belongs to issue #153,
unrelated code path in `check()`, not `_is_supported()`).

Ran `make check` across the full codebase and confirmed via `git stash` comparison
that this change introduces no new lint errors — only two pre-existing findings in
the touched files (import order in `faithfulness_checker.py`, an unused variable
in a test that already didn't assert a value).

**Next steps:**
Finalize the PR description (root cause explanation, before/after reproduction
steps, Notes for Reviewers covering both the #153 and lint findings). Run the
full pre-submission checklist, open a draft PR, and share it in the cohort
Slack channel for peer/mentor feedback before marking it ready for review.

**Blockers:**
None currently. Still deciding whether to mention the `test_minimum_overlap_required`
comment discrepancy (documents the old fixed-threshold rule) directly in the PR
description or leave it as a passing observation — will resolve before opening
the PR.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/469

**Branch:** fix/152-faithfulness-short-claims

**What you built:**
Scaled the required token overlap in `_is_supported()` to the claim's own
meaningful token length instead of a fixed threshold of 2, so short claims
(e.g. "Knows Python.") can be marked supported when they're actually
well-matched by context. Also fixed punctuation stripping in tokenization and
compound-sentence splitting in `_extract_claims()`, both of which surfaced
while verifying the three tests named in the issue.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — added
`test_single_meaningful_token_claim_is_supported`, covering the exact
single-token case from the issue. Full suite: 22 passed, 1 pre-existing
failure (`test_none_context_chunk_text`, issue #153, unrelated code path,
confirmed via `git stash` baseline comparison before/after this change).

**Self-review confirmation:** [✅] make check passes [✅] make test-unit passes

**Draft PR feedback received from:** none — shared in cohort Slack[#ai201-community-su26], no
response received by submission deadline


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No review came in. Shared the draft PR in the cohort Slack channel in Week 9 for peer
feedback as well; no response received by the Week 10 deadline.

**How you responded:**
N/A — no feedback received to respond to.

---

### Reflection

**What was harder than you expected?**
Getting all three tests named in the issue to actually pass. My first fix — scaling
the overlap threshold to claim length — looked correct and got 2 of 3 target tests
passing immediately. I assumed the third just needed a different ratio and spent
time tuning the formula before realizing the test couldn't pass under *any*
threshold value: it required a single claim to score a *partial* result, which is
mathematically impossible when one sentence produces exactly one claim. The real
fix required splitting compound sentences in `_extract_claims()`, a function the
issue never named. I was debugging the wrong hypothesis for longer than I'd like
to admit before I actually computed the numbers by hand for each failing case
instead of guessing at threshold values.

**What did you learn about working in a large codebase?**
That a bug's stated scope and its actual scope aren't always the same thing. The
issue named one function (`_is_supported()`), but the tests it referenced revealed
that a proper fix touched two functions and needed a documented judgment call
about scope (which I included explicitly in my PR's Notes for Reviewers, rather
than quietly expanding the diff). I also learned to distrust my own confidence —
running `make check` and the full test suite before *and* after a change, and
diffing the two, caught things that just reading my own code wouldn't have. And
practically: rebasing onto upstream late in the process, keeping local
environment fixes (a numpy pin for Docker) permanently unstaged so they never
leak into commits, and splitting docs commits from code commits all mattered more
than I expected going in.

**How did AI tools help — and where did they fall short?**
AI was most useful for fast iteration — tracing a function line by line, computing
token overlaps for specific test cases to test a hypothesis quickly, and drafting
PR descriptions and commit messages against the project's actual conventions
once I gave it the real CONTRIBUTING.md. Where it fell short: it couldn't replace
actually running the code. My first "fix" looked reasonable on paper, but only
running it against the full test suite revealed it was wrong for a subtle
mathematical reason (a single-claim sentence can't produce a partial score). AI
could help me reason about *why* once I had the real numbers in front of me, but
generating and running the actual evidence was still on me.

**What would you do differently if you started over?**
Run the full test suite immediately after my *first* attempted fix, rather than
checking only the three named tests first. If I'd seen the full picture (22 tests,
not 3) from the start, I likely would have caught the compound-claim problem in
one pass instead of two. I'd also write the punctuation-tokenization edge case
into my plan earlier — I found it almost by accident while tracing the function
manually, and it turned out to be load-bearing for one of the three tests, not
just a nice-to-have observation.

**What are you most proud of from this module?**
Not shipping my first fix. It passed 2 of 3 tests and would have been easy to
declare "close enough," but I kept testing until I understood *why* the third
one failed, rather than adjusting numbers until it happened to pass. That
distinction — between a fix that passes tests by coincidence and one you can
actually explain — feels like the most transferable thing I took from this
module.