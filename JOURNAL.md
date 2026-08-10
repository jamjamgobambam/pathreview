## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview generates portfolio feedback with a RAG pipeline, and a faithfulness checker scores whether each claim in that feedback is actually backed by the retrieved source text. The check lives in rag/evaluator/faithfulness_checker.py, in the _is_supported() method. Right now that method only counts a claim as supported when at least two meaningful (non-stopword) words overlap between the claim and the context. Short factual claims like "Knows Python" share only one meaningful word with a fully supporting context, so they are always scored as unsupported, and feedback made of short correct claims comes back with a faithfulness score of 0.0. A successful fix lowers that threshold so short, genuinely supported claims are no longer penalized, while claims with no real support still score as unsupported, verified against the three failing tests in tests/unit/test_faithfulness_checker.py.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" reasoning:**
The scope is contained to one method in one file, with a clear definition of done since three existing tests pin down the expected behavior, so I am not guessing at acceptance criteria. It fits my background in LLM output evaluation from my TrendMate chatbot project, where I built the LLM integration and needed the model's output to stay grounded, so I understand why a faithfulness check exists and what a correct fix should preserve. While confirming the bug I also noticed a separate failure (test_none_context_chunk_text) caused by a None context chunk, but that belongs to issue #153, so I am keeping this contribution scoped to the threshold bug in #152.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/lisatran183/pathreview/commit/8fb7f214559be009bc76d886be262b5ddfc4e2d4

**Reproduction summary:**
Ran `pytest tests/unit/test_faithfulness_checker.py -v` locally on the
fix/152-faithfulness-short-claims branch. Confirmed all 3 target tests fail
as the issue describes:
- test_partial_support_returns_middle_score — assert 0.2 < 0.0
- test_multiple_context_chunks — assert 0.0 > 0.5
- test_multiple_claims_varying_support — assert 0.2 < 0.0
(A 4th test, test_none_context_chunk_text, also fails but with a TypeError —
that's the separate None-context bug already scoped to #153, not this issue.)

**PLAN.md link:** https://github.com/lisatran183/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Blockers or open questions:**
Still deciding whether the fix should scale the overlap threshold by claim length (risk: reintroduces false positives from generic shared words like "developer") or move to a continuous per-claim support score instead of a boolean, since some failing tests expect partial (0.2-0.8) scores rather than strict pass/fail.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
2 of 5 sub-tasks from PLAN.md are done and committed separately:
1. Stripped punctuation before tokenizing in _is_supported() — fixed a silent bug where "Python," never matched "python" in context
2. Added _support_score(), which scales the required word-overlap to a claim's own length instead of a flat "always need 2" rule, and updated check() to average these scores. All 3 target tests (test_partial_support_returns_middle_score, test_multiple_context_chunks, test_multiple_claims_varying_support) now pass, along with the other 19 pre-existing tests. Only test_none_context_chunk_text still fails, which is expected — that's #153's bug, not this one's.

**Next steps:**
Sub-task 5 from PLAN.md: add a dedicated regression test for the punctuation-stripping fix specifically, since none of the 22 existing tests isolate that case on its own. Then run make check across the full project (not just this file) and read through docs/CONTRIBUTING.md to confirm branch naming and commit conventions before opening a draft PR.

**Blockers:**
None right now, though the punctuation-fixing commit took a few tries to get past ruff's line-length rule on the docstring — resolved, just slower than expected.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/630

**Branch:** fix/152-faithfulness-short-claims

**What you built:**
Fixed the faithfulness checker's overlap threshold so short claims (1-2 content words) can score as supported instead of always scoring 0.0, while also fixing a punctuation-stripping bug found during reproduction that was silently breaking real word matches.

**Tests added or updated:**
tests/unit/test_faithfulness_checker.py —> added
test_punctuation_does_not_break_overlap_matching to specifically regression-test the punctuation fix. Full suite: 22 passed, 1 pre-existing failure (test_none_context_chunk_text, scoped to #153, unrelated to this PR).

**Self-review confirmation:** 
[x] make check passes (except one pre-existing mypy annotation issue in this file, predating this PR and documented in the PR description)  
[x] make test-unit passes

**Draft PR feedback received from:** none yet — requested in course Slack on the submission deadline, but marked ready for review without waiting on a response due to the submission deadline.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - still awaiting review

**Summary of feedback:**
No review came in. I also didn't wait for peer feedback before marking the PR ready for review, since the Week 9 deadline landed the same day I requested it in Slack.

**How you responded:**
[left blank, no feedback to respond to]

---

### Reflection

**What was harder than you expected?**
Understanding how the three methods actually worked together before I touched anything. `check()` calls `_extract_claims()` to split feedback
into claims, then calls `_is_supported()` on each one, then averages the results. It wasn't obvious at first that `_extract_claims()` had its own 
filter (anything under 10 characters gets dropped), which quietly removed one of the claims from the issue's own example. I had to actually print
out the claims list to see that, instead of assuming I understood the flow from reading the code alone.

**What did you learn about working in a large codebase?**
On my own projects, I only had to worry about breaking my own logic. Here, every change I made to `_is_supported()` or `check()` had to be checked
against 19+ tests I didn't write, covering behavior I didn't design. I couldn't just fix the 3 target tests and move on. I had to run the whole
suite every time and reason about whether a change that fixed one thing might quietly break a test like `test_feedback_with_no_support_in_context`,
which was testing a completely different scenario. That forced me to think about the code's existing contract with the rest of the system, not just
whether my fix worked in isolation.

**How did AI tools help — and where did they fall short?**
Claude helped me find a second bug in the issue I chose, one that wasn't mentioned in the original issue description at all: punctuation wasn't
being stripped before comparing words, so tokens like "Python," never matched "python" in the context. I probably wouldn't have caught that
just from reading the code.

*Where it fell short:* a few times Claude pointed me to the wrong test or gave a slightly wrong line number or character count, especially during
the back-and-forth fixing ruff's line-length and unused-variable errors. I had to actually open the file and check what was really there instead
of trusting the guess. It was a good reminder that I still needed to verify things myself rather than assume the suggestion was correct.

**What would you do differently if you started over?**
I'd write the regression test for the punctuation bug before implementing the threshold-scaling fix, not after. I found and fixed both bugs almost
back to back, which meant when the target tests started passing, I couldn't immediately tell which fix caused which improvement. If I'd
written the punctuation test first and watched it fail, then fixed punctuation and watched it pass, then moved on to the threshold problem,
each step would have had its own clear before/after instead of me having to reason backward about which change did what.

**What are you most proud of from this module?**
I'm proud that I actually felt like a real software engineer during this, even though that's not the career path I'm aiming for. There was a lot of
reading, a lot of making sure I actually understood the code before touching it, and constant checking that what I changed was actually
solving the issue without breaking anything else in the system. That carefulness, running the full test suite every time instead of just the
tests I cared about, checking pre-existing failures before assuming I caused something, is not something I expected to internalize this deeply
given my background is in data analytics, not software engineering.
