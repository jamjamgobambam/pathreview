# Solution plan

**Issue:** README scorer test fixture is too short for its own word-count assertion — https://github.com/ascherj/pathreview/issues/156

## Understand

The failing test is `TestReadmeScorer::test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py`. The root cause is that the README fixture inside the test produces `word_count=51`, but the test asserts that `data["word_count"] > 100` and expects the README to be categorized as comprehensive.

Expected behavior: the fixture should represent a realistic comprehensive README and should satisfy the assertions being tested.

Actual behavior: the fixture is too short, so the scorer reports `category=minimal` and `word_count=51`, causing the test to fail.

## Map

Files expected to touch:

- `tests/unit/test_readme_scorer.py` — update the README fixture used by `TestReadmeScorer::test_readme_with_all_quality_signals`
- `PLAN.md` — document the Week 8 solution plan
- `JOURNAL.md` — document Week 8 reproduction and planning progress
- `REPRODUCTION.md` — document the reproduced failure

Main test involved:

- `TestReadmeScorer::test_readme_with_all_quality_signals`

Related behavior:

- The README scorer receives `readme_content`
- It calculates a `word_count`
- It assigns a README quality category
- The test expects this fixture to trigger the comprehensive path

## Plan

1. Re-run `python -m pytest tests/unit/test_readme_scorer.py -q` to confirm the current failure.
2. Edit the README fixture in `tests/unit/test_readme_scorer.py` so it contains more than 100 meaningful words while keeping the existing installation, usage, features, tech stack, badges, and live demo signals.
3. Avoid changing production scorer logic unless the updated fixture still reveals a scorer inconsistency.
4. Re-run the README scorer unit tests and confirm the failing test passes.
5. Before opening the Week 9 PR, run `make check` and `make test-unit`.

## Inputs & outputs

Input: the README fixture string passed into `scorer.execute({"readme_content": readme})` inside `tests/unit/test_readme_scorer.py`.

Output: a corrected test fixture that produces a word count above 100 and matches the intended comprehensive README scenario.

The intended fix should change test data only. The scorer should still return `success=True`, `has_readme=True`, a calculated `word_count`, and the appropriate category based on the README content.

## Risks & unknowns

- Risk in `tests/unit/test_readme_scorer.py`: expanding the fixture could accidentally remove one of the existing quality signals.
- Risk in the scorer behavior: the comprehensive category may depend on more than word count, so the fixture must preserve all quality sections.
- Unknown: whether maintainers prefer expanding the fixture or changing the assertion to match a shorter README.
- Unknown: whether nearby tests rely on the same scoring thresholds and reveal another mismatch after this fixture is corrected.

## Edge cases

- A README under 100 words should not be treated as comprehensive just because it has headings.
- A README over 100 words should not be treated as comprehensive if it lacks key quality signals.
- Markdown code fences, bullet lists, badges, and links should not break word-count behavior.
- The updated fixture should use meaningful README content rather than repeated filler text.
