## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker` class (in `rag/evaluator/faithfulness_checker.py`)
checks whether a claim is supported by a piece of context by requiring at
least 2 non-stopword tokens to overlap between them. This breaks down for
short factual claims — e.g. "Knows Python." only shares one meaningful token
("Python") with a fully supporting context like "python expert," so it's
always scored as unsupported even though it's correct. As a result, feedback
made up of short, valid claims can score 0.0 faithfulness, which is
misleading. A successful fix would adjust the overlap threshold or scoring
logic so that short claims can be correctly marked as supported, fixing the
related failing tests (`test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, `test_multiple_claims_varying_support`) in
`tests/unit/test_faithfulness_checker.py`.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [ ] App runs locally at localhost:5173
*(Note: backend starts but crashes on a Postgres connection error during
startup — DB isn't reachable. Frontend also blocked initially by npm not
being installed, since resolved. Still working through the Postgres piece.)*

**Cohort ledger:** [ ] Issue added to cohort ledger















## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/clem0g/pathreview/commit/b12000e

**Reproduction summary:**
Ran the reproduction snippet from the issue against
FaithfulnessChecker.check() -- confirmed a faithfulness score of 0.0 for
two short claims ("Knows Python.", "Knows SQL.") that are both fully
supported by their matching context chunks. Also noticed only 1 claim was
counted instead of 2, tracing to a separate length-filter issue in
_extract_claims() that drops sentences under 10 characters -- noted in
PLAN.md as a related but out-of-scope finding.

**PLAN.md link:** https://github.com/clem0g/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
Need to decide whether the scaled overlap threshold should count raw
tokens or non-stopword tokens only, and whether the _extract_claims()
length-filter bug is in scope for this issue or should be filed
separately.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in _is_supported() / added _support_score() and
_tokenize() in rag/evaluator/faithfulness_checker.py, per steps 1-2 of
PLAN.md. Replaced the hardcoded ">=2 overlap" boolean check with a
continuous overlap-ratio score (square-rooted), which also fixes
punctuation not being stripped from tokens. Confirmed via repro_152.py
that the reported bug is fixed, and confirmed via pytest that all 22
existing tests in test_faithfulness_checker.py pass, including the three
tests named in the issue that previously required this fix.

**Next steps:**
Run make check and make test-unit for full self-review, confirm no new
failures introduced (49 pre-existing failures observed, all in unrelated
modules), open a draft PR for peer/mentor feedback, then finalize and
submit by Sunday.

**Blockers:**
None currently -- the codebase has pre-existing lint errors and test
failures unrelated to this issue, documented in the PR description rather
than blocking this work.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/944

**Branch:** fix/152-faithfulness-short-claims

**What you built:**
Fixed FaithfulnessChecker._is_supported() so short claims (e.g. a single
distinctive term) can be correctly marked as supported. Replaced the
hardcoded "2+ overlapping tokens" boolean check with a continuous
_support_score() based on the fraction of a claim's meaningful tokens
found in context, and fixed punctuation not being stripped from tokens.

**Tests added or updated:**
No new test file added -- all fixes verified against the existing
tests/unit/test_faithfulness_checker.py, all 22 of which pass, including
the three tests named in issue #152. Added repro_152.py as a standalone
reproduction/regression script (not part of the pytest suite).

**Self-review confirmation:** [x] make check passes (for faithfulness_checker.py; 
pre-existing unrelated lint errors documented in PR description)
[x] make test-unit passes (for test_faithfulness_checker.py; 49 pre-existing
unrelated failures documented in PR description)

**Draft PR feedback received from:** [pending -- update once received]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No -- still awaiting review

**Summary of feedback:**
No reviewer feedback came in on PR #944. I also posted in Slack for
peer/mentor feedback ahead of finalizing, but did not receive a response
before the Week 9 deadline. Per the Su26 note, maintainer review is not a
feature this term.

**How you responded:**
N/A -- no feedback received. Proceeded with self-review (make check,
make test-unit) as the basis for marking the PR ready for review.

---

### Reflection

**What was harder than you expected?**
Environment setup ate more time than the actual bug fix. I hit npm not
being installed, then a Postgres connection refusal at backend startup
that I never fully resolved -- I ended up working around it since the
faithfulness checker module didn't actually need the full app stack
running to test. I also lost time to small terminal mistakes that had
nothing to do with the logic of the fix: a branch name with spaces in it
that git tried to parse as separate arguments, and a case-sensitive
filename mismatch (journal.md vs JOURNAL.md) that made an entire commit
go through empty without me noticing until I checked git show --stat.
None of that was hard in a "hard problem" sense, but it was a real
reminder that a big share of real development time goes to environment
and tooling friction, not writing code.

**What did you learn about working in a large codebase?**
My first fix attempt was wrong, and it took running the actual test suite
to find out. I initially just scaled the "require 2 overlapping tokens"
threshold down based on the claim's own length, but that didn't hold up
against the real test cases -- "Knows Python" still failed because it has
2 meaningful tokens even though only 1 of them appears in context. I only
caught this by tracing through the actual existing test file, not by
reasoning about the bug in isolation. That was the biggest lesson: in a
codebase with existing tests, the tests define correct behavior more
precisely than the issue description does, and you have to run them, not
just read them, to know if you're actually done. I also learned that
"passing" doesn't mean "the whole test suite is green" -- make test-unit
showed 49 pre-existing failures completely unrelated to my change, and
the actual bar was "did I introduce any new failures," not "is everything
passing."

**How did AI tools help — and where did they fall short?**
AI was most useful for quickly writing boilerplate (the reproduction
script, the PLAN.md structure, the PR description) and for helping me
understand git/terminal errors I didn't recognize, like the branch-name
parsing failure or the pre-commit hook segfault. Where it fell short: my
first proposed fix was plausible-sounding but wrong, because it was
reasoned from the issue description and one example rather than the
actual test suite. It only got corrected once I ran the real tests and
fed the failures back in. That's a pattern I want to remember -- AI
suggestions on logic fixes need to be verified against real test runs, not
accepted because the explanation sounds right.

**What would you do differently if you started over?**
I'd read the actual source file in full before writing PLAN.md, rather
than filling in "[confirm]" placeholders based on the issue description
alone -- I ended up doing this anyway once I had the real file, but doing
it earlier would have saved a revision pass. I'd also try to resolve the
Postgres setup issue directly instead of routing around it, since I never
confirmed whether it would have mattered for a different issue that
actually touched the API/DB layer.

**What are you most proud of from this module?**
Catching my own wrong fix. The first version looked reasonable and even
matched my mental model of the bug, but running the real test suite
proved it incomplete, and I was able to diagnose exactly why (claim token
count vs. actual context overlap) and land a version that passed all 22
tests instead of just patching it until the one repro case worked.
