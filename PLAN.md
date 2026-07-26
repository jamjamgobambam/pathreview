## Solution plan

**Issue:** README scorer test fixture is too short for its own word-count assertion
(https://github.com/ascherj/pathreview/issues/156)

### Understand
The test `test_readme_with_all_quality_signals` asserts a sample README fixture
scores `word_count > 100` and `word_count_category == "comprehensive"`. The scorer's
actual thresholds (`agent/tools/readme_scorer.py`, `_score_readme`) are: `<100` =
minimal, `<500` = adequate, `>=500` = comprehensive. The fixture README is only ~51
words, so it correctly scores as "minimal" per the scorer's real logic — the test's
expectation was simply written against the wrong threshold. Expected behavior: a
README with all quality signals (installation, usage, badges, demo link, tech stack)
AND 500+ words should score as "comprehensive." Actual behavior: the fixture has the
right sections but not enough words, so the test fails even though the scorer is
correct.

### Map
- `tests/unit/test_readme_scorer.py` — contains the failing test and its fixture
  README string; this is where the fixture needs to be extended and the assertion
  corrected.
- `agent/tools/readme_scorer.py` — the `_score_readme` static method; not being
  changed, but confirms the real 500-word threshold this fix must align with.

### Plan
1. Extend the fixture README in `test_readme_with_all_quality_signals` with
   realistic additional content (more detail in each existing section, plus
   an additional "Contributing" section) so it genuinely exceeds 500 words.
2. Update the assertion from `data["word_count"] > 100` to
   `data["word_count"] >= 500` to match the scorer's actual "comprehensive"
   boundary.
3. Run `pytest tests/unit/test_readme_scorer.py -q` to confirm all 23 tests pass.
4. Spot-check that the extended fixture still legitimately triggers every
   quality signal the test checks (installation, usage, badges, demo, tech stack)
   — since new content shouldn't accidentally break section-detection regexes.
5. Update JOURNAL.md and commit the fix as a clean, isolated commit.

### Inputs & outputs
Input: a README content string passed to `scorer.execute({"readme_content": ...})`.
Output: unchanged — still the same `ToolResult` data dict (`has_readme`,
`word_count`, `word_count_category`, section flags, `overall_score`). This fix
only changes the test's fixture data and assertion values, not the scorer's
logic or output shape.

### Risks & unknowns
- Adding filler-feeling text to hit the word count could accidentally break one
  of the regex-based section detections (e.g. if reworded text stops matching
  `install|setup|getting\s+started`) — mitigated by keeping each existing
  section's original trigger phrase intact and only adding surrounding prose.
- Unsure whether the maintainers would prefer the assertion say `>= 500` or
  a looser `> 400` with some buffer; I'll default to matching the scorer's
  exact boundary (`>= 500`) since that's what "comprehensive" actually requires.
- Need to confirm this doesn't affect `test_overall_score_calculation`, which
  multiplies a similar readme block by 3 — should be unrelated since it's a
  separate test with its own fixture, but worth re-running the full file to be sure.

### Edge cases
- Word count exactly at the boundary (500 words) — scorer uses `< 500` for
  "adequate," so 500 exactly should already be "comprehensive"; not something
  my fix needs to handle differently, just worth knowing the fixture should
  clearly exceed 500, not land exactly on it, to avoid off-by-one ambiguity.
- Fixture must still trigger all 5 quality signals simultaneously (not just
  word count) — verified by rereading each regex pattern before extending text.