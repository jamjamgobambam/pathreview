# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer "partial overlap" test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
So this issue is basically a broken unit test in
tests/unit/test_relevance_scorer.py. The test (test_query_with_partial_overlap)
is supposed to check that a query that only partly matches a chunk gets a score
somewhere in the middle, but the test data was set up wrong. The query is
"Python Django web framework" and the chunk it gets tested against actually has
all four of those words in it, so it's really a full match, not a partial one.
The scorer does the right thing and gives it a 1.0, but the test expects
something under 0.9, so it fails even though nothing is actually wrong with the
code. To fix it I just need to change the sample chunk so it only has some of
the query words instead of all of them — then it's actually testing partial
overlap like it's meant to, and the test passes.

**Branch name:** fix/157-relevance-scorer-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this issue right for me?" — checklist reasoning
I think this one's a good fit for me since it's pretty small and doesn't feel
overwhelming for a first issue. The change is only in one test file, and I
don't even have to touch the actual scorer code because the scorer already
works correctly. I was able to reproduce the failure by running
`pytest tests/unit/test_relevance_scorer.py -q` and watching it fail with
"assert 1.0 < 0.9". Once I looked at it, it made sense why — all four of the
query words show up in the chunk, so the overlap is complete. The main thing
I'll have to watch out for is picking new test data that actually gives a
partial score in the 0.3–0.9 range, and making sure I don't break any of the
other tests in the file.

## Week 8 - Issue Reproduction & Solution Planning

**Reproduction:**
I set up the Python side of the project locally (a `.venv` with the dev dependencies from
`pyproject.toml` — no Docker needed since this test only imports the scorer) and reproduced the
bug by running:

```
pytest tests/unit/test_relevance_scorer.py -q
```

It came back `1 failed, 18 passed`. The failing test is `test_query_with_partial_overlap`, and it
fails with:

```
assert 0.3 < score < 0.9
E   assert 1.0 < 0.9
[info] relevance_scored  avg_score=1.0 chunks_count=1 query_len=4
```

So I confirmed exactly what the issue said: the query has 4 words and the sample chunk contains all
4 of them, so the scorer returns 1.0, which is outside the 0.3–0.9 range the test expects. The
scorer is doing the right thing — the test's data is what's wrong.

**Solution plan:**
I wrote up the full plan in [PLAN.md](PLAN.md). The short version: the fix is to change the sample
chunk in that one test so it only contains *some* of the query words (drop "Django"), which makes
it a real partial-overlap case and gives a score of 0.75 (inside 0.3–0.9). The only file that
changes is `tests/unit/test_relevance_scorer.py` — the scorer itself stays the same because it's
already correct. The main risk I noted is not touching the tokenizer, since a few other tests in
the file depend on how it currently works.