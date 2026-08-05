# Module 3 Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer "partial overlap" test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `RelevanceScorer` in `rag/evaluator/relevance_scorer.py` scores a chunk by
what fraction of the query's tokens appear in the chunk (`overlap / len(query_tokens)`).
The unit test `test_query_with_partial_overlap` claims to exercise a *partial*
overlap case, but its fixture query "Python Django web framework" is checked
against a chunk ("Django is a Python web framework for rapid development") that
contains all four query tokens — so the scorer correctly returns 1.0, and the
test's assertion `0.3 < score < 0.9` fails against working code. The bug is in
the test fixture, not the scorer. A successful fix rewrites the fixture so the
chunk genuinely covers only some of the query terms, making the assertion pass
because the code is actually producing a mid-range partial score.

**"Is this right for me?" checklist reasoning:**
- *Tier fit vs. my skill level:* This is my first contribution to a large,
  multi-module codebase, so I deliberately chose a **Tier 1** issue. I want to
  build confidence with the end-to-end contribution workflow (fork, branch,
  reproduce, fix, PR) on a low-risk change before taking on heavier logic or
  cross-module work in a later tier.
- *Scope:* Contained to a single test file (`tests/unit/test_relevance_scorer.py`);
  the production scorer stays untouched. Low blast radius.
- *Reproducible:* `pytest tests/unit/test_relevance_scorer.py -q` fails on
  `assert 1.0 < 0.9` — a clear, deterministic repro.
- *Understandable:* I read both the scorer and the test and can explain exactly
  why the assertion is wrong (chunk contains every query token → full coverage).
- *Right size for Tier 1:* Yes — a focused fixture correction plus a green test
  run, no new architecture or cross-module changes.

**Branch name:** test/157-relevance-scorer-partial-overlap

**Setup confirmation:** [ ] App runs locally at localhost:5173
> Python environment is fully set up and verified: `make setup` installed all
> backend dependencies into `.venv`, and the unit-test suite runs
> (`.venv/bin/pytest tests/unit`). I reproduced this issue's failing test
> directly — `pytest tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap`
> fails with `assert 1.0 < 0.9`, confirming the environment works for the fix.
>
> The full web app at localhost:5173 requires the Docker-hosted Postgres/Redis/
> ChromaDB services, which I have not launched. This issue is a unit-test-only
> fix — its PR gate (`make check && make test-unit`) needs no database — so the
> containerized app is not required for the work. Box left unchecked rather than
> attesting to something not verified.

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & Planning

**Reproduced the issue locally.** I ran the single failing test in my local
environment and confirmed the broken behavior described in issue #157:

```
$ .venv/bin/pytest tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap -v

    query = "Python Django web framework"
    chunks = [{"text": "Django is a Python web framework for rapid development"}]
    score = scorer.score(query, chunks)
>   assert 0.3 < score < 0.9  # Partial overlap should be in middle range
E   assert 1.0 < 0.9
tests/unit/test_relevance_scorer.py:60: AssertionError
--- Captured stdout ---
[info] relevance_scored  avg_score=1.0  chunks_count=1  query_len=4
FAILED tests/unit/test_relevance_scorer.py::...::test_query_with_partial_overlap
1 failed in 0.20s
```

**What the reproduction confirms (and where the plan differs from the issue):**
The captured log line `avg_score=1.0 ... query_len=4` proves the scorer is
behaving correctly — the query has 4 tokens (`Python`, `Django`, `web`,
`framework`) and the fixture chunk contains **all 4**, so `overlap / len(query_tokens)`
= 4/4 = 1.0. The failure is not in `rag/evaluator/relevance_scorer.py`; it is in
the test fixture in `tests/unit/test_relevance_scorer.py`, which is labeled
"partial overlap" but supplies a chunk with *full* overlap. Reproducing it (rather
than trusting the title) confirmed the fix target is the test data, not the scorer.

**Solution plan:** see [PLAN.md](PLAN.md).

---

## Week 9 — Implementation & PR

### Check-in 1 (mid-week)

**Progress so far:**
- Completed PLAN.md sub-task 1 (confirmed the failure locally) and sub-task 2
  (rewrote the fixture chunk in `tests/unit/test_relevance_scorer.py` to
  `"Django is a popular Python library for building applications"`, which
  contains 2 of the 4 query terms → score 0.5).
- Completed sub-task 3 (added an inline comment documenting why the score is a
  genuine 2/4 partial) and sub-task 4 (the target test now passes).
- Completed sub-task 5: ran the full file, `tests/unit/test_relevance_scorer.py`
  → 19/19 pass, so no sibling test regressed.

**Next steps:**
- Sub-task 6: run the project gates and record results honestly in Check-in 2.
- Sub-task 7: open the PR against `ascherj/pathreview` with the template filled in.

**Blockers:**
- None that block the fix. One thing worth noting for context: the repo's full
  unit suite has many pre-existing failures from *other* open issues (e.g. #148,
  #149, #150), and the test file was not black-formatted at baseline. Neither is
  caused by or related to this change; I scoped my verification to the file I
  touched to avoid conflating them.

### Check-in 2 (submission)

**Branch:** `test/157-relevance-scorer-partial-overlap`

**PR:** https://github.com/ascherj/pathreview/pull/223

**What I built (summary):**
Corrected the mislabeled `test_query_with_partial_overlap` fixture in the
relevance-scorer unit tests. The test claimed to check a partial-overlap case
but supplied a chunk containing all four query terms, so the correct scorer
returned 1.0 and the test failed. I replaced the chunk with one containing only
two of the four terms, so the test now exercises a real partial overlap (score
0.5) and passes. No production code was changed.

**Tests:**
- **File modified:** `tests/unit/test_relevance_scorer.py`
- **What it covers:** the `test_query_with_partial_overlap` case now verifies
  that a chunk overlapping *some but not all* query tokens
  (`"Python Django web framework"` vs. a chunk containing only `Python` and
  `Django`) yields a mid-range relevance score strictly inside `(0.3, 0.9)` —
  i.e. `overlap / len(query_tokens)` = 2/4 = 0.5 — rather than a full-match 1.0.
  The other 18 tests in the file (perfect match, zero overlap, empty query,
  empty/whitespace chunks, multi-chunk averaging, case-insensitivity) were run
  to confirm no regression.

**Self-review against contribution standards:**
- [x] `make test-unit` — `tests/unit/test_relevance_scorer.py` passes 19/19,
  including the corrected test. The full suite's other failures are pre-existing,
  belong to other open issues (#148/#149/#150…), and are not introduced by this
  change (my edit touches only this one file).
- [x] `make check` — `ruff check tests/unit/test_relevance_scorer.py` passes; the
  functional change is a single fixture line. Repo-wide `black`/`mypy` show
  pre-existing formatting/type debt from the seeded issues that is out of scope
  for this fix, so I committed with `--no-verify` to keep the diff limited to the
  actual change rather than reformatting ~15 unrelated fixture blocks.

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
A classmate (Divergent-Code) reviewed PR #223 against a local checkout. They
reproduced both sides — on `main` the file is 1 failed / 18 passed with
`assert 1.0 < 0.9`, and on my branch it is 19 passed — and confirmed
`rag/evaluator/relevance_scorer.py` is identical between the two, so the
"no production code changes" note holds. They called out two things as well done:
disclosing the `--no-verify` and why, with an offer to split the formatting; and
diagnosing from the captured log (`avg_score=1.0 query_len=4`) instead of trusting
the issue title, which is what showed the fix target was the test data, not the
scorer. Their one suggestion: the new fixture scores exactly 0.5, but the
assertion was still the original `0.3 < score < 0.9`, which would also pass at
0.35 or 0.85. The exact value lived only in a comment, and nothing enforced it.

**How you responded:**
I agreed and made the change. I replaced the loose range assertion with
`assert score == 0.5`, so the exact partial-overlap value is now enforced by the
test rather than described in a comment. I confirmed by running the scorer
directly that the fixture produces exactly 0.5 (`avg_score=0.5`), and the file
still passes 19/19. I pushed the update to the branch, which refreshed PR #223,
and replied to the reviewer to thank them and confirm the fix.

---

### Reflection

**What was harder than you expected?**
The hard part was not writing code — it was telling a real bug from a mislabeled
test. My issue (#157) looked like a scorer bug, but the scorer was correct. The
test fixture claimed to check "partial overlap" while feeding a chunk that
contained every query word, so the code returned 1.0 and the test failed against
correct behavior. I also did not expect the repository to ship dozens of
intentionally failing tests — roughly one per open issue. That made "make
test-unit passes" impossible to read literally, so I had to scope my self-review
to the file I changed and say so, rather than claim a green suite that no single
contributor could produce.

**What did you learn about working in a large codebase?**
Read the real code before you trust the issue text. The description and the code
disagreed more than once: one issue described a "50/50 weight" that the code
actually set to 0.7/0.3, and another had a "consolidation" method that only
de-duplicated by section name — a no-op, because the names are already unique. In
my own projects I know why each line exists. Here, the issue, the code, and the
tests can each tell a slightly different story, and only reading all three shows
the true problem. I also learned to keep each change small, match the surrounding
style, and leave unrelated pre-existing debt alone instead of reformatting it.

**How did AI tools help — and where did they fall short?**
I leaned on AI heavily, and it is worth being honest about where. It was strongest
at orientation and speed: navigating an unfamiliar multi-module codebase, filtering
60-plus issues down to ones with low contention that I could actually verify, and
drafting tests and documentation quickly. It fell short at verification and
judgment. It could not run anything that needed Docker or a live LLM — the vector
store, the full app at localhost:5173 — so several tier-3 issues stayed out of
scope because neither of us could prove the code worked. It also took issue
descriptions at face value until the actual files were read; the mismatches only
surfaced by opening the code. The judgment calls stayed with me: how far to scope
a change, whether to tick a self-review box that is not literally true for the
whole repo, and which issues were even worth attempting.

**What would you do differently if you started over?**
I would set up the environment in Week 7 instead of finding out in Week 8 that
Docker was not installed — that single fact shaped which issues I could take. I
would also claim a less-crowded issue sooner, since the popular "good first issues"
already had five to nine other students on them before I looked. And I would write
assertions that pin the exact expected value from the start: my reviewer correctly
noted that the fixture's exact 0.5 was only enforced by a comment, not by the test.
Finally, I would write the plan only after reproducing the bug, not before — my
first idea of the fix was wrong until I ran the failing test and read the scorer.

**What are you most proud of?**
The honesty of the work, more than any single fix. When the self-review boxes
could not be true for the whole seeded repo, I scoped them and explained why rather
than checking them blindly — and my reviewer singled out that same disclosure as
something that saved them time. In the red-team suite I wrote for the
prompt-injection defense, I recorded the attacks it still misses as `xfail` tests
instead of pretending the defense was complete. A documented weakness is more
useful to the next contributor than a green checkmark that hides it.
