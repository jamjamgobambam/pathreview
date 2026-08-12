## Week 7 — Issue selection

**Issue link:** https://github.com/<org>/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** Tier 1

**Problem summary:**
The `_is_supported()` method in `rag/evaluator/faithfulness_checker.py` determines
whether a generated claim is backed by the retrieved context by requiring at least
two overlapping non-stopword tokens between the claim and the context. This
threshold breaks down for short factual claims. A sentence like "The candidate
knows Python" only shares one meaningful token with a supporting context like "python expert," 
so it gets marked unsupported even though it's accurate. As a result, any feedback made up of short, well-supported claims
scores 0.0, which misrepresents genuinely faithful output as unfaithful. The fix will involves adjusting the overlap threshold to scale with claim length.
This affects the `rag` module's evaluation layer, `FaithfulnessChecker`, and existing unit tests already capture the expected behavior once fixed.

**Branch name:** fix/152-faithfulness-checker-short-claims

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger


**Checklist reasoning:**

*Part 1 — Understanding:* The issue is that `_is_supported()` in the faithfulness
checker requires 2+ overlapping non-stopword tokens between a claim and its
context, but short claims often only share 1 actually meaningful token with a fully supporting context, so they always score as unsupported. It should be a short, accurate claim like "Knows Python" backed by context
like "python expert" should score as supported.

*Part 2 — Tier fit:* Tagged Tier 1. This is my first time tackling an issue in a large codebase

*Parts 3 and 4:* I believe it will take me around 3 hours to debug given the failing tests

## Week 8 - Reproduction of Issue

## Week 8 — Reproduction & solution planning

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/landon517/pathreview/commit/a3f670ecac2b9bfebc9413ceb58d987cb55704ab)

**Reproduction summary:**
Ran the failing tests and the repro script from issue #152; confirmed the
faithfulness checker returns 0.0 for claims that should be fully supported,
because `_is_supported()`'s hardcoded overlap threshold of 2 tokens can't be
met by short claims.

**PLAN.md link:** 

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Also noticed `test_none_context_chunk_text` fails with a TypeError — appears
unrelated to #152 (crashes on None context text rather than a scoring issue),
treating as out of scope for this fix.


## Week 9 — Solution building & PR submission
 
### Check-in 1
 
**Current progress:**
Sub-tasks 1–4 from `PLAN.md` are done. I reproduced the bug locally and confirmed
the failing tests all trace back to the same root cause rather than separate
defects. I read `_is_supported()` in full and enumerated its three tunable pieces
— the hardcoded stopword literal, the `.split()` tokenization, and the `>= 2`
threshold constant — and grepped for callers to confirm `_is_supported()` is only
used from `check()` within `faithfulness_checker.py`, so changing its behaviour
doesn't ripple into other evaluators.
 
I settled the design question from sub-task 3 in favour of a scaled absolute
threshold over a ratio: claims with ≤ 2 meaningful tokens must match all of them,
claims with 3+ keep the original `>= 2` rule. A ratio would have changed scoring
for every claim length rather than only the short-claim case in the issue.
 
While reproducing I confirmed the tokenization wrinkle I flagged in `PLAN.md` was
real — plain `.split()` leaves trailing punctuation attached, so `"python."` never
matched the context token `"python"`. Fixed that with a `\b\w+\b` regex in the same
change, since the threshold fix alone wouldn't have resolved the reported example.
 
**Next steps:**
Sub-task 5 — finish the regression tests, run the full test file, and check for
regressions in longer-claim cases. Then `make check`, self-review against
`docs/CONTRIBUTING.md`, and open the draft PR for feedback.
 
**Blockers:**
Two tests in this file fail on `main` for reasons unrelated to #152 and I need to
document them rather than fix them. `test_none_context_chunk_text` is issue #153 —
a `TypeError` in `check()` when a chunk has `text: None` — which is a separate
defect and out of scope here. `test_partial_support_returns_middle_score` looks
unfixable from `_is_supported()` at all; confirming that before I write it up.
 
---
 
### Check-in 2 
 
**PR link:** https://github.com/ascherj/pathreview/pull/970

**Branch:** `fix/152-faithfulness-checker-short-claims`
 
**What you built:**
Replaced the hardcoded 2-token overlap threshold in
`FaithfulnessChecker._is_supported()` with one that scales to claim length —
claims with 2 or fewer meaningful tokens must have all of them appear in the
context, while longer claims keep the original `>= 2` rule. Also switched
tokenization from `str.split()` to a `\b\w+\b` regex so trailing punctuation no
longer blocks a match, and added an explicit guard returning `False` for claims
made up entirely of stopwords. Short, fully-supported claims now score as
supported instead of being forced to 0.0 by their length.
 
**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — five tests added.
`test_short_claim_single_token_overlap_scores_supported` is the regression test
for the exact case in #152. `test_short_claim_no_overlap_stays_unsupported` guards
against the fix over-loosening the checker. `test_zero_meaningful_token_claim`
covers a stopword-only claim. `test_check_end_to_end_with_short_claims` exercises
the full `check()` path with a mix of short and normal claims.
`test_extract_claims_drops_very_short_claims` documents the pre-existing
`len(claim) > 10` filter in `_extract_claims()`, which drops claims like
`"Knows SQL"` before they reach `_is_supported()` — relevant context for anyone
reading the issue later. Three previously-failing tests named in the issue now
pass: `test_short_claim_single_token_overlap_scores_supported`,
`test_multiple_context_chunks`, and `test_multiple_claims_varying_support`.
 
**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
 
*Both in the sense the assignment defines for a codebase with documented
pre-existing failures: my changes introduce no new failures. Two tests in
`tests/unit/test_faithfulness_checker.py` failed on `main` before this branch and
still fail after it, both documented in the PR description.
`test_none_context_chunk_text` is issue #153, a separate `TypeError` in `check()`
when a context chunk has `text: None`, deliberately left out of scope to keep this
PR to one issue. `test_partial_support_returns_middle_score` cannot pass under any
change confined to `_is_supported()`: its feedback is a single sentence, so
`check()` sees exactly one claim and can only return 0.0 or 1.0, while the test
asserts a score strictly between 0.2 and 0.8. Making it pass would require graded
per-claim scoring, and even that doesn't resolve it cleanly — its claim is
numerically identical to the one in `test_feedback_with_no_support_in_context`
under token overlap (6 meaningful tokens, 1 overlapping, 7-token context) while the
two tests require different score bands, so separating them needs term weighting or
semantic similarity rather than token counts. That's a redesign of the scoring
layer, outside the scope of #152.*
 



## Week 10 — Iteration & reflection
 
### Reviewer feedback
 
**Feedback received:** [x] No — still awaiting review
 
**Summary of feedback:**
No reviewer or maintainer comments came in on the PR before the end of the week.
  
---
 
### Reflection
 
**What was harder than you expected?**
 
Deciding what not to fix. I went in assuming the hard part would be writing the
patch.
 
The clearest example was `test_partial_support_returns_middle_score`, which I had
listed in `PLAN.md` as one of the failing tests related to 152. I assumed my fix
would make it pass. It didn't, and once I worked through why, it turned out it
couldn't. Its input feedback is a single sentence, so `_extract_claims()` returns
one claim, and since `check()` computes `supported / len(claims)` over a
boolean, the only reachable scores are 0.0 and 1.0 while the test asserts a value
strictly between 0.2 and 0.8. No change confined to `_is_supported()` can satisfy
it. I spent real time trying graded-scoring designs before noticing that the claim
in that test is numerically identical to the one in
`test_feedback_with_no_support_in_context` under token overlap, six meaningful
tokens, one overlapping, seven-token context, while the two tests demand different
score bands. Separating them needs term weighting or semantic similarity, not a
better threshold.
 
Working that out and then choosing to write it up rather than fix it felt wrong
at first. 
 
The same thing happened with 153. It's a `TypeError` in the same file, in the
method directly calling the one I was fixing, and it's a one-line change,
`chunk.get("text", "")` returns `None` when the key exists with a `None` value.
Everything about it invited me to just fix it while I was in there. Keeping the PR
to one issue was a deliberate choice I had to keep re-making.
 
**What did you learn about working in a large codebase?**
 
That "the tests pass" doesn't mean what it means on a personal project. When I ran
`make test-unit` on this repo I got 51 failures across files I'd never opened. I first had to
establish a *baseline*: capture the failure list on `main`, capture it on my branch,
and diff them, so I could demonstrate that my two remaining failures predated me
and that nothing new appeared. The standard isn't "everything is green," it's
"you didn't make it worse," and proving the second one is its own piece of work.
 
The other thing I didn't anticipate was how much the tooling enforces conventions
that the code itself doesn't follow. I added five tests to
`tests/unit/test_faithfulness_checker.py` and pre-commit refused the commit with 30
mypy errors and a ruff `F841` — almost all of them in tests written long before I
touched the file, which had never been type-annotated. Pre-commit only checks files
you've changed, so touching one file made me responsible for its entire backlog.
I hadn't considered that the cost of a change includes the accumulated debt of
whatever you happen to touch.
 
**How did AI tools help — and where did they fall short?**
 
Most useful for orientation and for pressure-testing my reasoning. Getting oriented
in `rag/evaluator/` and understanding what `_is_supported()` was actually doing went
much faster. It was also good at generating the first draft of the
regression tests and at articulating the design tradeoff. Where it fell short: it
can't tell you whether something is *true of your repo*. It confidently described
what my test results would be, and the actual numbers were different. 
I had 51 repo-wide failures, not the handful predicted. Anything
grounded in the real state of the codebase had to come from
running the commands myself. The turning point on the
`test_partial_support_returns_middle_score` question only came from reconstructing
the module and running it, not from reasoning about it.
 
It was also least useful on the parts that weren't code. I didn't know how to open
a pull request, and that's not a knowledge gap AI closed for me quickly. It's a
sequence of specific actions in a specific UI, where knowing that the base repository
dropdown has to say `ascherj/pathreview` and not my own fork matters more than
anything about the patch. I lost more time to workflow mechanics than to the bug.
 
**What would you do differently if you started over?**
 
Learn the submission mechanics in Week 7, not Week 9. I lost the full 20 points on
last week's deliverable, and it wasn't because the fix was wrong — the fix was
committed and pushed. It was because I didn't have `JOURNAL.md` check-ins written
and I didn't understand that the PR was accessible by way of link.
The engineering was the part I was most worried about and the part that went
fine. The process was the part I messed up on.
 
I'd also run `make test-unit` and `make check` on `main` on day one and write the
output down. I ran them for the first time when I was ready to commit, which meant
I couldn't immediately tell which failures were mine. Ten minutes of baseline
capture at the start would have saved an hour of uncertainty at the end.
  
**What are you most proud of from this module?**
 
I'm most proud of managing this codebase and figuring out what exactly this issue is
revolving around and how to go about solving it. 
I got a lot of experience in engineering a solution. Writing unit tests also requires a deep
understanding of the possibilities, which required great focus. 
