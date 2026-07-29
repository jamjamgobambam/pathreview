# Solution plan

**Issue:** [README scorer test fixture is too short for its own word-count assertion](https://github.com/ascherj/pathreview/issues/156)

### Understand

The unit test `test_readme_with_all_quality_signals` in
`tests/unit/test_readme_scorer.py` asserts that a high-quality README produces
`word_count > 100` and `word_count_category == "comprehensive"`. But the README
string it feeds the scorer is only **51 words**, so both assertions fail against
correct scorer behavior.

- **Expected:** a comprehensive, richly-detailed README fixture that the scorer
  counts as >100 words and categorizes as `comprehensive`.
- **Actual:** the fixture is 51 words, which the scorer correctly counts and
  categorizes as `minimal`, so the test fails with `assert 51 > 100`.

The root cause is **in the test, not the production code**. The scoring logic in
`agent/tools/readme_scorer.py` (`_score_readme`) is correct:
`word_count = len(content.split())`, and the category thresholds are
`< 100 → minimal`, `< 500 → adequate`, `>= 500 → comprehensive`. Because
`comprehensive` requires **≥500 words**, the fixture must reach 500+ words to
satisfy *both* assertions simultaneously.

### Map

Files / functions involved:

- **`tests/unit/test_readme_scorer.py`** — `TestReadmeScorer.test_readme_with_all_quality_signals`.
  The inline `readme` fixture string is the only thing that changes. **(File I will touch.)**
- **`agent/tools/readme_scorer.py`** — `ReadmeScorer._score_readme` (read-only
  reference for thresholds; **not modified**).

### Plan

1. **Confirm the target thresholds.** Verify `comprehensive` requires ≥500 words
   and that the other assertions (`has_installation_section`, `has_usage_section`,
   `has_badges`, `has_demo_link`, `has_tech_stack_section`, `overall_score > 0.7`)
   depend on section markers already present in the fixture.
2. **Extend the fixture README** to ≥500 whitespace-split tokens while keeping
   every existing section marker (Installation, Usage, Features, Tech Stack,
   badges, Live Demo) so all `has_*` signals stay `True`. Add realistic prose
   under the existing headings rather than filler.
3. **Verify word count deterministically.** Run
   `python -c "print(len(open(...).read()... ))"`-style check or a quick REPL to
   confirm the new fixture yields ≥500 words with margin (target ~550) so it can't
   drift back under the boundary.
4. **Run the test** — `pytest tests/unit/test_readme_scorer.py -q` — and confirm
   the previously-failing test passes and no sibling test regresses.
5. **Run the full unit suite** (`make test-unit`) to confirm no collateral damage.

### Inputs & outputs

- **Input:** the inline `readme` multi-line string passed to
  `scorer.execute({"readme_content": readme})`.
- **Output / change:** an extended README fixture (≥500 words). After the change
  the scorer returns `word_count >= 500` and `word_count_category ==
  "comprehensive"`, so the test's existing assertions pass. No production code,
  API, or runtime behavior changes.

### Risks & unknowns

- **Boundary drift:** `comprehensive` is `>= 500`; landing at exactly 499 words
  would silently re-break the test. Mitigation: target ~550 words with margin and
  assert the count during development.
- **Breaking sibling signals:** rewording headings could drop a keyword the
  regexes in `readme_scorer.py` look for (e.g., renaming "Installation" would
  flip `has_installation_section` to `False`). Mitigation: preserve the exact
  section keywords; only add body text.
- **Assertion-vs-fixture ambiguity:** the issue allows "extend the fixture *or*
  correct the assertion." I'm choosing to extend the fixture because the test's
  intent is clearly to validate a *comprehensive* README; weakening the assertion
  to match a tiny fixture would test less than intended. Open question: confirm
  with the maintainer via PR description that extending is the preferred direction.
- **Indentation/tokenization:** the fixture is triple-quoted with leading
  indentation; `split()` counts all whitespace-separated tokens including markdown
  symbols, so the effective word count differs slightly from prose word count —
  I'll measure the actual `len(content.split())`, not eyeball it.

### Edge cases

- **Exactly 500 words** → must be `comprehensive` (`>= 500`); tests should land
  comfortably above, not on, the boundary.
- **All section markers still match** after editing (installation, usage, badges,
  demo, tech stack) so `overall_score` stays `> 0.7`.
- **Other tests unaffected:** `test_readme_with_no_content` (empty → `minimal`,
  score 0.0) and `test_readme_with_only_title` (title only → `minimal`) use their
  own fixtures and must remain green.
- **Markdown-heavy content:** code fences, list markers, and image syntax count
  as tokens — the fixture must reach the threshold in real `split()` tokens, not
  just visible prose.
