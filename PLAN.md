## Solution plan

**Issue:** README scorer test fixture is too short for its own word-count assertion — https://github.com/ascherj/pathreview/issues/156

### Understand

The root cause is a mismatch between a test's input and the behavior it asserts,
not a defect in the scorer. `TestReadmeScorer.test_readme_with_all_quality_signals`
feeds `ReadmeScorer` an inline fixture README of ~51 words, then asserts
`word_count > 100` (and, further down, the "comprehensive" category). The scorer
correctly reports `word_count=51` and `category=minimal` (confirmed in the
captured log: `readme_scored category=minimal score=0.871... word_count=51`), so
the assertion fails with `assert 51 > 100` at `tests/unit/test_readme_scorer.py:56`.

- **Expected:** a README exhibiting all quality signals scores as
  `"comprehensive"` with `word_count > 100`.
- **Actual:** the fixture is too short to reach that threshold, so the test fails
  against correct scorer output.

The fix is to make the test honest about its intent by extending the fixture past
the 100-word threshold — _not_ by weakening the assertion. The test is named for
"all quality signals," so it must genuinely reach the comprehensive band;
loosening the assertion would silently drop coverage of that branch.

### Map

- `tests/unit/test_readme_scorer.py` — contains `TestReadmeScorer.test_readme_with_all_quality_signals`
  and the inline triple-quoted fixture README (the `readme` variable). The fixture
  is local to the method, not shared, so editing it is self-contained.
  **Primary edit site (the fixture string).**
- `agent/tools/readme_scorer.py` — the `ReadmeScorer` class. **Read only, do not
  edit.** Needed to confirm how `word_count` is computed and the exact category
  boundaries (`minimal` → `comprehensive`).

### Plan

1. Read `ReadmeScorer` in `agent/tools/readme_scorer.py` to confirm how words are
   counted (raw whitespace split vs. markdown/code stripped) and the threshold
   that maps to `"comprehensive"` (strict `>` vs `>=`, and whether any tier sits
   above comprehensive).
2. Rewrite the inline `readme` fixture to a realistic comprehensive README
   (target ~150 words) that adds real prose while preserving every existing
   quality signal already in the fixture: the `# Project Name` heading, the
   Installation and Usage code blocks, the Features and Tech Stack lists, the two
   badges, and the Live Demo link.
3. Confirm the rewritten fixture still satisfies every other assertion in the
   test (`result.success`, `has_readme`, the `"comprehensive"` category check, and
   any signal-presence assertions after line 56).
4. Run `pytest tests/unit/test_readme_scorer.py -q` to confirm green, then run the
   full unit suite to confirm no regression.

### Inputs & outputs

- **Input:** the inline `readme` fixture string passed to
  `scorer.execute({"readme_content": readme})`.
- **Output/change:** the scorer result for that fixture reports `word_count > 100`
  and the `"comprehensive"` category, while every other asserted field remains
  satisfied. No production code changes.

### Risks & unknowns

- The test asserts more than word count (success, `has_readme`, category, and
  signal checks below line 56). A careless rewrite could drop a heading, code
  fence, badge, or link and break a sibling assertion — the extension must add
  prose only, not remove existing structure.
- Word-count computation is not yet confirmed: if the scorer strips markdown/code
  before counting, padding with code blocks or bullet lists won't raise the count
  (the current 51-word result over a fixture with many lines suggests only prose
  words count). Confirm in `readme_scorer.py` before writing the fixture.
- Category boundaries not yet confirmed: if a tier exists above "comprehensive,"
  overshooting could push the fixture out of the target band. Aim comfortably
  past 100 but verify the upper bound.

### Edge cases

- Boundary behavior at exactly 100 vs 101 words (strict `>` vs `>=`).
- Markdown/code syntax in the fixture — do fenced blocks, badge image syntax, or
  link syntax count as words?
- Whitespace-only or indented lines (the fixture is indented inside the method)
  not inflating or deflating the count unexpectedly.
