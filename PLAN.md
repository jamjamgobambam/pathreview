## Solution plan

**Issue:** Relevance scorer "partial overlap" test fixture actually has full query overlap
(https://github.com/ascherj/pathreview/issues/157)

### Understand
The root cause is bad test fixture data, not a bug in the scorer itself.
`test_query_with_partial_overlap` in `tests/unit/test_relevance_scorer.py`
asserts that a partially-matching query should score between 0.3 and 0.9.
But the fixture query ("Python Django web framework") has all 4 of its
terms present in the fixture chunk ("Django is a Python web framework for
rapid development") — so it's actually a full-overlap case. Expected
behavior: the fixture should represent a genuine partial match (some but
not all query terms present in the chunk). Actual behavior: the scorer
correctly returns 1.0 for full overlap, which fails the test's 0.3–0.9
assertion — the scorer logic is working as intended.

### Map
- `tests/unit/test_relevance_scorer.py` — contains the failing test
  `test_query_with_partial_overlap` and its fixture data (query + chunks);
  this is the only file I expect to modify.
- `rag/evaluator/relevance_scorer.py` — contains `RelevanceScorer.score()`,
  the method under test; I will read this to confirm scoring logic but do
  not expect to change it.

### Plan
1. Read `RelevanceScorer.score()` in `rag/evaluator/relevance_scorer.py`
   to confirm exactly how term overlap is calculated (e.g. simple keyword
   match vs. weighted scoring), so my new fixture produces a predictable
   score.
2. Rewrite the fixture chunk text in `test_query_with_partial_overlap` so
   only 2-3 of the 4 query terms ("Python", "Django", "web", "framework")
   appear in the chunk, instead of all 4.
3. Manually calculate/estimate the expected score under the scorer's logic
   to confirm it should land inside 0.3–0.9 before running the test.
4. Run `pytest tests/unit/test_relevance_scorer.py -q` to confirm the
   target test passes and no other test in the file regresses (should stay
   19/19 passing).
5. Update the test's docstring/comment if needed so the fixture's intent
   ("partial overlap") is clearly documented for future readers.

### Inputs & outputs
- **Input:** the fixture's `query` string and `chunks` list (specifically
  the `"text"` field of each chunk dict) passed into `scorer.score(query,
  chunks)`.
- **Output:** a float score; currently `1.0`, should change to a value
  strictly between `0.3` and `0.9` after the fixture fix.
- No changes to function signatures, return types, or any non-test files.

### Risks & unknowns
- **Risk:** I don't yet know if `RelevanceScorer.score()` uses simple
  substring/keyword matching or something more complex like TF-IDF or
  embedding similarity — if it's not simple overlap counting, my fixture
  edit might not land in the 0.3–0.9 range as expected. I'll verify this
  by reading `relevance_scorer.py` before editing the fixture (Plan step 1).
- **Risk:** removing a term from the chunk text might unintentionally
  affect sentence structure/grammar in a way that looks like a typo rather
  than a deliberate partial-match case — I'll keep the chunk text
  grammatically natural.
- **Unknown:** whether there's a shared fixture/conftest.py file that other
  tests also depend on — I'll check `tests/unit/conftest.py` (if it exists)
  to confirm this fixture is local to this one test and won't break others.

### Edge cases
- **Zero overlap:** if I accidentally remove too many terms and the chunk
  shares no words with the query, the score could drop to 0.0, falling
  outside the 0.3–0.9 target range — I need to leave enough overlap to
  stay in range, not just any overlap.
- **Case sensitivity:** need to confirm whether the scorer lowercases terms
  before comparing (e.g. "Python" vs "python") so my edited fixture doesn't
  accidentally create a false partial-match due to casing rather than
  genuine word absence.
- **Whitespace/punctuation:** need to make sure the fixture chunk still
  reads as a normal sentence (not just space-separated keywords) so it
  reflects a realistic chunk of document text.