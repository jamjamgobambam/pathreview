# Solution plan

**Issue:** [README scorer test fixture is too short for its own word-count assertion — #156](https://github.com/ascherj/pathreview/issues/156)

### Understand

`tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals`
fails with `assert 51 > 100`.

- **Expected (by the test):** a "comprehensive" README — `word_count > 100` and
  `word_count_category == "comprehensive"`.
- **Actual:** the inline fixture is only ~51 words, so the scorer returns
  `word_count == 51` and `category == "minimal"`.

**Root cause:** a test-data mismatch, *not* a scorer bug. The scorer counts and
categorizes correctly. The binding constraint is the category threshold: per
`_score_readme` (`agent/tools/readme_scorer.py:70-75`),
`< 100 = minimal`, `100–499 = adequate`, `≥ 500 = comprehensive`. To satisfy
both assertions the fixture must contain **≥ 500 words**, not merely > 100.

### Map

Files involved:

- `tests/unit/test_readme_scorer.py` — **the only file I'll touch.** The fixture
  string and assertions live in `test_readme_with_all_quality_signals`
  (fixture lines 19–49, assertions lines 53–63).
- `agent/tools/readme_scorer.py` — reference only (defines the thresholds and
  scoring). **Not modified** — the logic is correct.

### Plan

1. Rewrite the `readme` fixture in `test_readme_with_all_quality_signals` into a
   genuine ≥ 500-word README (target ~550 for margin), expanding the existing
   sections with real prose.
2. Preserve every quality signal the assertions check: Installation section,
   Usage section, badges (`![...](...)`), a demo link (`try it` / `demo`), and a
   Tech Stack section.
3. Leave all assertions unchanged — they now correctly describe the fixture.
4. Run the single test, then the whole module, then the unit suite, to confirm
   the fix and check for regressions.

### Inputs & outputs

- **Input:** the fixture is a hard-coded README string passed to
  `scorer.execute({"readme_content": readme})`. No external/runtime input.
- **Output / change:** the test's assertions pass. Expected scorer result for
  the new fixture: `has_readme=True`, `word_count > 500`,
  `word_count_category == "comprehensive"`, all section flags `True`, and
  `overall_score == 1.0` (all 6 boolean signals + word bonus maxed at 1.0),
  which satisfies `overall_score > 0.7`.

### Risks & unknowns

- **Low risk** — change is confined to test data; no production code, deps,
  migrations, or API surface affected.
- Word counting is `len(content.split())` (whitespace split), so code fences,
  list dashes, and punctuation all count as tokens. I'll pad to a comfortable
  margin (~550+) so 500 isn't borderline.
- Unknown: whether `make lint`/pre-commit imposes line-length limits on the long
  string literal — will format the fixture to satisfy black/ruff if flagged.

### Edge cases

- The fixture must stay **well above** 500 words so trivial edits don't drop it
  back into `adequate`.
- All regex-detected signals must remain intact after rewriting (a demo phrase,
  at least one `![badge](url)`, and headings matching the install/usage/tech
  patterns) so no sibling assertion breaks.
- No behavior change for the other tests — verify the full module stays green,
  not just the target test.
