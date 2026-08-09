## Solution plan

**Issue:** README scorer test fixture is too short for its own word-count assertion (#156)
https://github.com/ascherj/pathreview/issues/156

### Understand
`test_readme_with_all_quality_signals` asserts `word_count_category == "comprehensive"`,
which per `_score_readme()`'s thresholds requires `word_count > 500`. The current fixture
has all structural quality signals (installation, usage, badges, tech stack, demo link)
but only ~51 whitespace-tokens of actual content, so it scores "minimal" instead. Other
tests (`test_word_count_category_minimal/_adequate/_comprehensive`) independently confirm
the 100/500 thresholds are intentional scorer behavior — the fixture, not the scorer, is
what needs to change.

### Map
- `tests/unit/test_readme_scorer.py` — extend the `readme` fixture string inside
  `test_readme_with_all_quality_signals` (lines ~24-46)
- No changes expected to `agent/tools/readme_scorer.py`

### Plan
1. Rewrite the fixture's prose sections (project description, features, usage
   explanation) with realistic, substantive paragraphs instead of one-line stubs
2. Verify token count exceeds 500 by running the scorer against the new fixture locally
   (e.g. a quick `len(readme.split())` check) before running the full test
3. Confirm all structural assertions still pass: `has_installation_section`,
   `has_usage_section`, `has_badges`, `has_demo_link`, `has_tech_stack_section`
4. Confirm `overall_score > 0.7` still holds given the `min(word_count/500, 1.0)`
   bonus term in the score formula
5. Re-run `pytest tests/unit/test_readme_scorer.py -q` to confirm the full file passes,
   then `make test-unit` to confirm nothing else regressed

### Inputs & outputs
Input: the `readme_content` string in the test fixture. Output: `ReadmeScorer.execute()`'s
result dict — specifically `word_count` and `word_count_category` need to land in the
"comprehensive" range while all other fields stay `True`/high as before.

### Risks & unknowns
- Padding the fixture with filler text could feel artificial rather than like a real
  README — want the added prose to read naturally, not like `"word " * 500`
  (`test_score_scales_with_word_count` shows they're comfortable with repeated-phrase
  padding elsewhere, so this is a style choice, not a strict blocker)
- Need to recompute word count exactly, since markdown syntax (`##`, `` ``` ``, `![]()`)
  all count as tokens too — easy to misjudge the target length by eyeballing it
- Should double check `overall_score > 0.7` isn't a near-miss after edits, since it's an
  averaged score across 7 components

### Edge cases
- Fixture must stay just over 500 tokens, not exactly at the boundary (500 itself is
  `"adequate"` per `word_count < 500` in the scorer, so 501+ is required)
- Adding prose shouldn't accidentally remove any of the existing keyword matches
  (e.g. rewording "Installation" section could break the regex match if the heading
  itself changes)