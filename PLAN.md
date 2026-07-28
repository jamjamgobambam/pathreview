# PLAN — Issue #156: README scorer test fixture too short for its own assertions

## Problem

`tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals`
fails. The test's inline `readme` fixture is a short README (~51 words), but the
test asserts the scorer reports a large, "comprehensive" README:

```
assert data["word_count"] > 100            # fails: actual word_count == 51
assert data["word_count_category"] == "comprehensive"
```

This is a **test-data defect, not a scorer defect**. The scorer in
`agent/tools/readme_scorer.py` correctly counts 51 words and correctly labels
that `minimal`. The fixture and the assertions simply disagree.

## Root cause

Two independent inconsistencies between the fixture and the assertions:

1. `word_count > 100` — the fixture only has ~51 words.
2. `word_count_category == "comprehensive"` — per `_score_readme`
   (`readme_scorer.py:70-75`), `comprehensive` requires **≥ 500 words**
   (`< 100 = minimal`, `100–499 = adequate`, `≥ 500 = comprehensive`).

So satisfying assertion (2) is the binding constraint: the fixture must contain
**≥ 500 words** to be genuinely "comprehensive." That automatically satisfies
`word_count > 100` as well.

## Approach

Enlarge the fixture README so it genuinely qualifies as comprehensive
(≥ 500 words) while preserving every quality signal the test checks. This keeps
the test's *intent* — validating a high-scoring, feature-complete README —
instead of watering the assertions down to match a weak fixture.

Signals that must remain present so the other assertions still pass:

- Installation section (`has_installation_section`)
- Usage section (`has_usage_section`)
- Badges (`has_badges`)
- Demo link (`has_demo_link`)
- Tech stack section (`has_tech_stack_section`)
- `overall_score > 0.7`

With all boolean signals present and word_count ≥ 500 (word bonus maxes at 1.0),
`overall_score` becomes `7/7 = 1.0`, comfortably above 0.7.

## Steps

1. Expand the `readme` string literal in `test_readme_with_all_quality_signals`
   to ≥ 500 words: flesh out the existing sections (Installation, Usage,
   Features, Tech Stack) with real prose paragraphs, keeping the badges and
   demo link intact.
2. Leave all assertions unchanged — they now describe the fixture correctly.
3. Run the single test, then the full `test_readme_scorer.py` module, then the
   unit suite, to confirm no regressions.

## Files to touch

- `tests/unit/test_readme_scorer.py` — enlarge the fixture in
  `test_readme_with_all_quality_signals` only. No other tests change.

Not touched:
- `agent/tools/readme_scorer.py` — scoring logic is correct; do not modify.

## Testing

```bash
.venv/bin/python -m pytest tests/unit/test_readme_scorer.py -v -m unit
```

Expect: the previously-failing test passes and all sibling tests stay green.

## Risks / unknowns

- **Low risk.** Change is confined to test data.
- Must count words carefully — `len(content.split())` splits on whitespace, so
  markdown punctuation, code fences, and list dashes all count as tokens. I'll
  target a comfortable margin (~550+ words) so the threshold isn't borderline.
- No dependency, migration, or API surface is affected.
