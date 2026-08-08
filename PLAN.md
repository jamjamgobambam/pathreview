# Plan

## Solution plan

**Issue:** [157 - Relevance scorer “partial overlap” test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?

The issue is that that `test_query_with_partial_overlap` test fails incorrectly in `tests/unit/test_relevance_scorer.py`. The root cause is a query (`"Python Django web framework"`) that contains all the tokens that are in the chunk text (`"Django is a Python web framework for rapid development"`). This causes the `RelevanceScorer` to correctly return a score of `1.0` - however, this isn't what the test should be doing. Instead, (as per its name) it should test for _partial_ overlap - not full. Because the current code for this test checks for _full_ overlap, the test fails.

### Map

Which files, functions, or modules are involved?
List the specific files you expect to touch.

The only file that needs to be modified is `tests/unit/test_relevance_scorer.py`. This is the file containing the buggy test code leading to a test failure. I will also take a look at `rag/evaluator/relevance_scorer.py`, which defines the `RelevanceScorer` class that the test uses. This file certainly doesn't need to be modified, but at least reading it will give me better context of what the `RelevanceScorer` does and how the corrected test should be written.

### Plan

What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Reproduce the issue via the steps in [JOURNAL.md](./JOURNAL.md#week-8--reproduction--solution-planning). Observe that the `test_query_with_partial_overlap` test fails - focus on this method.
2. Run all the tests and observe how many fail. Remember this for later.
3. Read the entire test file to get familiar with it. Read `rag/evaluator/relevance_scorer.py` for context of how the score is calculated and what sorts of queries are expected.
4. Change the `query` in the test to include at least a few words that aren't in the chunk text, such as `Python development framework details`.
5. Run the test file to see if the change correctly allows every test to pass.
6. Assess any collateral damage: a test file usually doesn't get imported to other modules, but just to be safe, perform a repo-wide search on the file name without the extension (`relevance_scorer`). Run all the tests like in the beginning. This time, confirm that exactly 1 less test failed than before, ensuring the fix only impacted the test that issue deals with.

### Inputs & outputs

What does your fix take as input? What should it produce or change?

**Method I'm changing:** `test_query_with_partial_overlap(self, scorer)`

**Inputs**: The test already takes the fixture `scorer` (a plain `RelevanceScorer` object).

**Outputs**: None. Performing assertions with the side-effect of producing test results in the terminal.

**Modification I'll make:**

```py
    def test_query_with_partial_overlap(self, scorer):
        """Test query with partial overlap returns score between 0 and 1."""
        query = "Python Django web framework details"     # MODIFIED
        chunks = [
            {
                "text": "Django is a Python web framework for rapid development"
            },
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert 0.3 < score < 0.9  # Partial overlap should be in middle range
```

### Risks & unknowns

What could go wrong? What are you still unsure about?

- **Inadequate query change**: Perhaps adding just one word (`"details"`) may not be enough to push the score into the 0.3-0.9 range. However, this can be solved by understanding how the score is calculated, mentally running the calculation on the updated query, and running the test file to confirm.
- **Partial overlap range**: How was the partial overlap range decided to be from 0.3 and 0.9? Can this be changed? I will err on the side of not touching it.
- **Handling edge cases**: Is this test supposed to test the comfortable partial overlap range only or also edge cases (such as close the 0.3 or 0.9 boundary)?
- **Stop word importance**: The `RelevanceScorer` doesn't seem to filter out stop words (like `the`, 'a', `of`, etc.) when calculating the score. Should relevance scoring still take into account stop words - despite this possibly being suboptimal for the end algorithm?
- **Breaking other tests**: If I'm not careful, I may end up breaking other tests (or even functionality) when modifying this test. I will have to be deliberate with my change and make sure to check the test pass rate and overall app behavior before and after the fix.

### Edge cases

What inputs or states should your fix handle gracefully?

- **Score falling exactly on a boundary**: There is a chance that, after I change the query, the number of matching words over the total number in the query ends up being exactly 0.3 or 0.9 - exactly on the boundary of partial overlap. The current test excludes these values in the range, but floating point errors may nudge the score over the boundary in either direction.
- **Unrepresentative test**: If I don't design the query to match what the codebase generally expects of queries (e.g. using typos, extraneous non-ASCII symbols, etc.), the test may still pass but not be testing anything useful. The simple assertion may succeed without a practical query being tested, which wouldn't be useful.
