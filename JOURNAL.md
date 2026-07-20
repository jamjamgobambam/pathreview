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
**Selection reasoning ("Is this issue right for me?" checklist):**
1. **Is it actually open?** Yes — I checked and #157 has no merged fix yet.
   (There's an open, unmerged PR #164 from another student attempting it,
   but multiple people are allowed to work the same issue in this course,
   so this doesn't disqualify it.)
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