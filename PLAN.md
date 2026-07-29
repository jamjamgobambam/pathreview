## Solution plan

**Issue:** README scorer test fixture is too short for its own word-count assertion — https://github.com/ascherj/pathreview/issues/156

### Understand
`test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py` asserts that its fixture README has `word_count > 100` and `word_count_category == "comprehensive"`. The fixture is only 51 words. In `agent/tools/readme_scorer.py`, `word_count_category` is `"minimal"` below 100 words, `"adequate"` from 100–499, and `"comprehensive"` only at 500+. Running the test confirms this: the scorer correctly computes `word_count=51`, `category="minimal"`, `score=0.87`, and the test fails with `assert 51 > 100`. The root cause is the test fixture, not the scorer — the scorer is behaving exactly as designed. The fixture was written to demonstrate "all quality signals" (installation, usage, badges, demo link, tech stack) but was never actually padded out to comprehensive-length content, so its own length assertion was never satisfiable.

### Map
- `tests/unit/test_readme_scorer.py` — contains the broken fixture and assertions (lines ~17–63, specifically lines 56–57). This is the only file that needs to be modified.
- `agent/tools/readme_scorer.py` — not changed, but this is where the category thresholds (`< 100` minimal, `< 500` adequate, else comprehensive, lines ~69–75) and `overall_score` calculation live; used as the source of truth for what the fixture should assert.
- No other tests depend on this fixture, so the change should remain isolated to this test file.

### Plan
1. Extend the README fixture in `test_readme_with_all_quality_signals` so its word count genuinely exceeds 500, while preserving every quality signal the test checks for (installation section, usage section, badges, demo link, tech stack section) so the other assertions still hold.
2. Re-run `pytest tests/unit/test_readme_scorer.py -q` and confirm `word_count > 500`, `word_count_category == "comprehensive"`, and `overall_score > 0.7` all pass together.
3. Sanity-check the other word-count-category tests (`test_word_count_category_minimal`, `_adequate`, `_comprehensive`) still pass unaffected, since they use separate fixtures.
4. Add a short comment above the fixture explaining that it is intentionally longer than 500 words so it satisfies the "comprehensive" threshold and isn't accidentally shortened in the future.
5. Run the full unit test suite (make test-unit) to confirm there are no regressions elsewhere.

### Inputs & outputs
**Input:** the existing test file, the fixed word-count thresholds in `readme_scorer.py` (treated as fixed/correct, not touched).
**Output:** an updated fixture string in `test_readme_with_all_quality_signals` whose word count is genuinely >500, and a passing test suite with no regressions elsewhere.

### Risks & unknowns
- Padding the fixture with filler text risks accidentally breaking the section-detection assertions (`has_installation_section`, `has_usage_section`, `has_tech_stack_section`, `has_badges`, `has_demo_link`) if filler text is inserted inside a detected section in a way that confuses the regex/keyword matching in `readme_scorer.py`. Need to add filler as clearly separate prose, not inside code blocks or section headers.
- Unsure whether `overall_score > 0.7` will still hold once word count changes — score is an average across multiple components including `min(word_count / 500, 1.0)`, so pushing word count to exactly 500+ should raise, not lower, the score, but I want to verify this numerically rather than assume.
- Alternative fix (loosen the assertions instead of extending the fixture) was considered but rejected: it would weaken the test's original intent of validating a genuinely comprehensive README, so extending the fixture is the more faithful fix.

### Edge cases
- Word count should end up comfortably above 500 (not borderline at 500–510) to avoid failures caused by small differences in how words are counted.
- Filler content added must not accidentally introduce/remove keywords the scorer checks for (e.g., adding the word "setup" or "example" elsewhere could flip `has_installation_section`/`has_usage_section` in unintended ways).
- Confirm behavior is unchanged for the two boundary tests already in the suite (`test_word_count_category_adequate` at 200 words, `test_word_count_category_comprehensive` at 700 words) since they use independent fixtures and shouldn't be affected by this change.
