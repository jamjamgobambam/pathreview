## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer "partial overlap" test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bug is in `tests/unit/test_relevance_scorer.py`, in the test
`test_query_with_partial_overlap`. The test is meant to check that when a
query only partially matches a chunk of text, the relevance scorer returns a
score in the middle range (0.3–0.9). But the fixture data doesn't actually
create a partial-overlap scenario: the query "Python Django web framework"
has all four of its terms present in the chunk text ("Django is a Python web
framework for rapid development"), so it's really a full-overlap case. The
scorer correctly returns 1.0 for full coverage, which makes the test's
assertion (`0.3 < score < 0.9`) fail — not because the scorer logic is wrong,
but because the fixture doesn't test what it claims to. A successful fix
means rewriting the fixture (either the chunk or the query) so the overlap
is genuinely partial, without changing any logic in
`rag/evaluator/relevance_scorer.py`.

**Selection reasoning ("Is this issue right for me?" checklist):**
1. **Is it actually open?** Yes — I checked and #157 has no merged fix yet.
   (Multiple people are allowed to work the same issue in this course,
   so other claim comments doesn't disqualify my selection.)
2. **Is the scope clear?** Yes — the problem is specific and reproducible.
   Running `pytest tests/unit/test_relevance_scorer.py -q` reliably
   reproduces the exact failure (`assert 1.0 < 0.9`), so there's no
   ambiguity about what's broken.
3. **Is it the right size?** Yes — this is a one-file, one-fixture change
   in `tests/unit/test_relevance_scorer.py`. No changes needed to
   `relevance_scorer.py` or any other service.
4. **Is the maintainer active?** N/A for this course context — this is a
   simulated/curated repo for the assignment, not a live upstream project
   waiting on maintainer review.
5. **Does it match where I am?** Yes — this only requires understanding
   Python test fixtures and basic string/keyword overlap logic, both of
   which I'm comfortable with. No unfamiliar language features or
   frameworks involved, so it's a good low-risk first issue.

**Branch name:** fix/157-relevance-scorer-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger



## Week 8 — Reproduction

**Reproduction steps:**
Ran the following command locally to confirm the issue exists in my environment:
`pytest tests/unit/test_relevance_scorer.py -q`

**Observed output:**
```..F................                                                                      [100%]
=========================================== FAILURES ===========================================
_____________________ TestRelevanceScorer.test_query_with_partial_overlap ______________________

self = <tests.unit.test_relevance_scorer.TestRelevanceScorer object at 0x10797a650>
scorer = <rag.evaluator.relevance_scorer.RelevanceScorer object at 0x1079ea710>

    def test_query_with_partial_overlap(self, scorer):
        """Test query with partial overlap returns score between 0 and 1."""
        query = "Python Django web framework"
        chunks = [
            {
                "text": "Django is a Python web framework for rapid development"
            },
        ]
    
        score = scorer.score(query, chunks)
    
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
>       assert 0.3 < score < 0.9  # Partial overlap should be in middle range
        ^^^^^^^^^^^^^^^^^^^^^^^^
E       assert 1.0 < 0.9

tests/unit/test_relevance_scorer.py:60: AssertionError
------------------------------------- Captured stdout call -------------------------------------
2026-07-21 20:24:24 [info     ] relevance_scored               avg_score=1.0 chunks_count=1 query_len=4
=================================== short test summary info ====================================
FAILED tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap - assert 1.0 < 0.9
1 failed, 18 passed in 0.32s
```

**Confirmation:** This confirms the bug described in issue #157 — the fixture
query and chunk text overlap on all 4 terms ("Python", "Django", "web",
"framework"), producing a full-overlap score of `1.0` instead of a genuine
partial-overlap score, causing the test's `0.3 < score < 0.9` assertion to
fail. The scorer itself behaves correctly; the fixture data is the problem.