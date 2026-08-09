# Solution Plan: README Scorer Test Fixture Issue #156

## Problem

The README scorer test `test_readme_with_all_quality_signals` fails because the fixture README is too short.

The test expec
- `word_count > 100`
- `word_count_category == "comprehensive"`

but the fixture currently contains approximately 51 words.

## Reproduction

Command:

```bash
pytest tests/unit/test_readme_scorer.py -q

Observed:

assert 51 > 100
Root Cause

The scorer behavior is correct. The test fixture does not accurately represent the scenario being tested.

The fixture includes README quality signals such as:

installation instructions
usage examples
features
technology stack
links/images

However, it lacks enough descriptive content to reach the comprehensive word-count threshold.

Implementation Plan
# Solution plan

**Issue:** README scorer test fixture is too short for its own word-count assertion (#156)

Issue link: https://github.com/ascherj/pathreview/issues/156

## Understand

The issue is caused by a mismatch between the test fixture and the expected behavior.

The test `test_readme_with_all_quality_signals` expects a README that represents a comprehensive project README. It asserts:

- `word_count > 100`
- `word_count_category == "comprehensive"`

However, the current fixture only contains approximately 51 words. The README scorer correctly categorizes the fixture as minimal, causing the test to fail.

The expected behavior is for the fixture to contain enough realistic README content to satisfy the comprehensive quality signals being tested.

## Map

Files involved:

- `tests/unit/test_readme_scorer.py`
  - Contains the failing test:
    - `TestReadmeScorer.test_readme_with_all_quality_signals`

- `agent/tools/readme_scorer.py`
  - Contains the README scoring logic being tested.

- `PLAN.md`
  - Documents the solution approach.

- `JOURNAL.md`
  - Documents reproduction steps and progress.

## Plan

1. Update the README fixture inside `tests/unit/test_readme_scorer.py`.
   - Add realistic project description text.
   - Increase fixture length beyond 100 words.

2. Preserve existing README quality signals.
   - Keep installation instructions.
   - Keep usage examples.
   - Keep features, tech stack, badges, and links.

3. Run the README scorer unit test.
   - Verify the fixture produces the expected comprehensive category.

4. Run broader project validation.
   - Run `make check`.
   - Run `make test-unit`.

## Inputs & outputs

### Input

The README scorer receives:

```python
{
    "readme_content": "<README markdown content>"
}
 
Output

The scorer returns analysis data including:

README existence
word count
quality category
scoring information

The fix should only change the test fixture input and should not modify scorer behavior.

Risks & unknowns
Adding content to the fixture could unintentionally affect other scoring metrics.
The exact threshold behavior of the scorer may depend on additional README signals.

Mitigation:

Only add descriptive README content.
Keep existing markdown structure unchanged.
Run the full unit test suite after changes.
Edge cases

The fixture should continue handling:

Short README files that should correctly score as minimal.
Comprehensive README files exceeding the word threshold.
README content containing markdown syntax such as code blocks, links, and images.
