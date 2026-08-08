# PathReview: Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG faithfulness evaluator (`rag/evaluator/faithfulness_checker.py`) scores
generated feedback by checking how many of its individual claims are actually
"supported" by the retrieved context chunks. The bug lives in `_is_supported()`,
which only counts a claim as supported when it shares at least two meaningful
(non-stopword) tokens with the context. Short but fully grounded claims such as
"Knows Python." share just one meaningful token with a context that plainly
supports them, so they are always marked unsupported and the overall score
collapses to 0.0. A successful fix makes the support check scale to the length of
the claim, so a genuinely covered one-keyword claim can still count as supported
while still rejecting claims the context does not actually back up, which
restores an accurate faithfulness score and makes the three related tests in
`tests/unit/test_faithfulness_checker.py` pass.

**Branch name:** fix/152-faithfulness-short-claim-support

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes: "Is this right for me?" reasoning

- **Scope is contained:** The fix is limited to a single function (`_is_supported()`)
  in one file (`rag/evaluator/faithfulness_checker.py`). No cross-module or
  database/API changes are required.
- **Clearly reproducible:** The issue provides an exact repro snippet and names the
  three failing unit tests (`test_partial_support_returns_middle_score`,
  `test_multiple_context_chunks`, `test_multiple_claims_varying_support`), so I have
  an objective definition of "done."
- **No heavy external dependencies:** The checker and its tests run purely in
  Python via `make test-unit`, so they do not need the LLM provider or the ChromaDB
  vector service, so a fully green vector DB isn't a blocker for this issue.
- **Right difficulty level:** It's a Tier 1 bug, but it's a real logic fix (not a
  test-fixture tweak or one-line crash guard), so it forces me to understand how a
  RAG system verifies that feedback is grounded in evidence, which is good learning value
  for a first contribution.
- **Risk / unknowns:** The main judgment call is choosing the right supported-ness
  rule (e.g. scaling required overlap to claim length) so that short valid claims
  pass without making unrelated claims pass too. I'll validate that balance against
  the full `test_faithfulness_checker.py` suite before opening a PR.

**Environment status:** `make setup` and `make run` succeed; frontend confirmed
returning HTTP 200 at http://localhost:5173/ with the backend on :8000. (Note: the
`chromadb/chroma:0.4.22` container currently crashes on NumPy 2.0; not required for
issue #152 and can be addressed separately.)

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/aryamanm24/pathreview/commit/ef14e1fdee20304b99cb82b03f78dbe6abde58c4

**Reproduction summary:**
I reproduced the bug two ways. Running the issue's own snippet,
`check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}])`
returns `0.0` and `_is_supported("Knows Python", "python expert")` returns
`False`, even though both short claims are fully backed by the context. Running
`pytest tests/unit/test_faithfulness_checker.py` confirms the three tests named
in the issue fail (`test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, `test_multiple_claims_varying_support`), and I
added `tests/unit/test_issue_152_reproduction.py` with two failing tests that
capture the exact scenario.

**PLAN.md link:** https://github.com/aryamanm24/pathreview/blob/fix/152-faithfulness-short-claim-support/PLAN.md

**Walkthrough video (recommended):** (not recorded)

**Blockers or open questions:**
The main open question is tuning a single support rule that satisfies both the
direct `_is_supported()` True/False tests and the `check()` mid-range score tests
at the same time. Separately, `test_none_context_chunk_text` also fails, but that
is the `text: None` crash tracked under issue #153, so I'm treating it as out of
scope for this #152 fix.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `rag/evaluator/faithfulness_checker.py`, working through
the PLAN.md sub-tasks: (1) added a `_tokenize()` helper that strips punctuation
so `"Python,"` matches `python`; (2) replaced the fixed `>= 2` overlap rule with
a graded `_support_score()` whose required matches scale with claim length; and
(3) made `check()` average the per-claim scores so partially grounded feedback
lands in the middle of the range. The three issue tests plus my reproduction
tests now pass.

**Next steps:**
Finish reconciling `_is_supported()` (kept as a `>= 0.5` threshold over the new
graded score), run the full `make check` / `make test-unit` to confirm no new
failures, open the PR, and request peer feedback.

**Blockers:**
None. `test_none_context_chunk_text` still fails, but that is issue #153 (a
separate `text: None` crash), not #152.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/526

**Branch:** `fix/152-faithfulness-short-claim-support`

**What you built:**
The faithfulness checker now grades each feedback claim by how much of it the
retrieved context supports, instead of requiring at least two overlapping words.
Tokenization strips punctuation, the support bar scales with claim length (a very
short claim needs just one meaningful match), and `check()` averages the per-claim
scores, so short and partially grounded feedback is scored fairly instead of 0.0.

**Tests added or updated:**
`tests/unit/test_issue_152_reproduction.py` has four regression tests covering the
issue snippet, a single-keyword short claim, a partially grounded claim scoring
mid-range, and comma-separated skills matching despite punctuation. The repo's
existing `tests/unit/test_faithfulness_checker.py` tests for this module now pass
unchanged.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

(Note on pre-existing failures: this repo ships many unrelated failing tests and
lint errors from other curated issues. Baseline before my change was 55 failing
unit tests; after my change it is 50, and the diff is exactly the 5 faithfulness
tests I fixed with no new failures. My changed files pass `ruff`, `black`, and
`mypy`. Per the assignment's guidance, "passes" here means my change introduces
no new failures.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review or comments arrived on PR #526 by the end of the week. As of this
entry the PR is still open with zero reviews and zero inline or conversation
comments. (Per the Summer 2026 cohort note, reviewer feedback is not provided
this term, so this is expected.)

**How you responded:**
There was nothing to respond to. If a review does come in later, I plan to read
every comment first, sort them into clear fixes vs. points that need discussion,
reply to each thread, and push follow-up commits rather than force-pushing over
the existing diff.

---

### Reflection

**What was harder than you expected?**
The hard part was not writing the fix but making one scoring rule satisfy two
sets of tests that pulled in opposite directions. The direct `_is_supported()`
tests wanted a clean True/False, while the `check()` tests wanted a single
partially grounded claim (like "The developer shows Python expertise and
Kubernetes knowledge") to land between 0.2 and 0.8, which a plain
supported/unsupported flag can never produce. I ended up working out the token
counts for the failing cases by hand, and that is how I found that a length
scaled threshold, `max(1, (len + 1) // 2)`, combined with averaging graded
per-claim scores, was what threaded both needles at once.

**What did you learn about working in a large codebase?**
The biggest shift was realizing the tests were the real specification. The issue
described the symptom, but the exact expected behavior lived in
`tests/unit/test_faithfulness_checker.py`, and reading those assertions is what
showed me the bug was actually three stacked problems: the `>= 2` overlap
threshold, punctuation-blind tokenization (so "Python," never matched "python"),
and binary per-claim scoring. I also learned to expect a messy baseline.
`make test-unit` reported 55 failing tests before I changed anything, so
"passing" meant "introduce no new failures," not a fully green suite. That is
very different from my own projects, where I control the whole state.

**How did AI tools help — and where did they fall short?**
AI was most useful for orienting quickly: tracing the only caller of `check()` in
`rag/evaluator/eval_suite.py` to confirm I would not break it, drafting PLAN.md
and the PR description, and running the suite iteratively while I tuned the logic.
Where it fell short was the precise threshold math. I could not just trust a
generated formula, because a plain overlap ratio gave 0.167 for the partial
support case and would have failed the 0.2 lower bound, so I had to reason
through the specific token overlaps myself. AI also had no knowledge of the 55
pre-existing failures, so establishing and documenting that baseline was on me.

**What would you do differently if you started over?**
I would open the PR as a draft earlier in the week instead of close to the
deadline, so there was more room for feedback even in a term where reviews are
rare. During issue selection I would also read the module's test file before
committing to the issue, because the interdependence between the
`_is_supported()` tests and the `check()` score-range tests was the real
difficulty, and I only fully saw it in Week 9. I would still choose #152 again;
it taught me more than a one-line crash fix would have.

**What are you most proud of from this module?**
I am most proud that the fix is principled rather than reverse-engineered from
the tests. The graded `_support_score()` with a length-aware threshold is a real
answer to "how well does the context support this claim," and it makes short
claims like "Knows Python" score correctly without letting unrelated claims slip
through. I am also proud of keeping the change honest and in scope: I left the
`test_none_context_chunk_text` crash alone because it belongs to issue #153, and
I documented the 55-to-50 failure baseline so a reviewer can trust exactly what
my change did and did not touch.
