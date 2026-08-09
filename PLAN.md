## Solution plan

**Issue:** Fixture too short: `test_readme_with_all_quality_signals` asserts `comprehensive` but README has ~51 words
(https://github.com/ascherj/pathreview/issues/156)

### Understand

The unit test `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py`
embeds a sample README that is only 51 words long, then asserts two things a 51-word README can
never satisfy:

- `data["word_count"] > 100`
- `data["word_count_category"] == "comprehensive"`

The scorer in `agent/tools/readme_scorer.py` categorizes word counts (lines 70-75) as:
`< 100` = `minimal`, `100-499` = `adequate`, `>= 500` = `comprehensive`. So a README must have
**at least 500 words** to be `comprehensive`.

- **Expected:** a high-quality README fixture is scored `comprehensive` and the test passes.
- **Actual:** the fixture is 51 words, so it scores `minimal`, and the first count assertion
  fails with `assert 51 > 100`.

The scorer logic is correct. The defect is in the test fixture data, not the production code.

### Map

Files involved:

- `tests/unit/test_readme_scorer.py` — **the file I will change.** Specifically the `readme`
  fixture string inside `test_readme_with_all_quality_signals` (lines ~19-50).
- `agent/tools/readme_scorer.py` — **reference only, not changing.** It defines the word-count
  thresholds (lines 70-75) and the signal-detection regexes (lines 79-97) that the fixture must
  satisfy.

To make the test pass, the rewritten fixture must satisfy every assertion in the test body
(lines 54-64):

- `word_count > 100` and `word_count_category == "comprehensive"` (so `>= 500` words)
- `has_installation_section` (regex matches `install` / `setup` / `getting started`)
- `has_usage_section` (`usage` / `how to use` / `quickstart` / `example`)
- `has_badges` (image syntax `![...](...)`)
- `has_demo_link` (`demo` / `live demo` / `try it` / `see it` / `live link`)
- `has_tech_stack_section` (`tech stack` / `technologies` / `built with` / `technology` / `stack`)
- `overall_score > 0.7`

### Plan

1. Rewrite the `readme` fixture in `test_readme_with_all_quality_signals` into a realistic,
   well-structured README of **at least 500 words** (target ~550-600 for a safe margin) so the
   category becomes `comprehensive`.
2. Ensure the expanded fixture still contains every quality signal the test checks: an
   Installation section, a Usage section, at least one image badge `![alt](url)`, a demo/live
   link phrase, and a Tech Stack section.
3. Keep the fixture as clean, plausible README prose (the stray notes/gibberish that had been
   pasted into the fixture have already been reverted).
4. Run `.venv/bin/python -m pytest tests/unit/test_readme_scorer.py -v` and confirm this test
   plus the rest of the `readme_scorer` suite pass.
5. Run `make check` (ruff, black, mypy) so the change clears the project's pre-commit gates
   before opening the PR.

### Inputs & outputs

- **Input:** the multi-line `readme` string passed to `scorer.execute({"readme_content": readme})`.
- **Output / effect:** after the change, `scorer.execute` returns `word_count >= 500`,
  `word_count_category == "comprehensive"`, all five signal booleans `True`, and
  `overall_score > 0.7`, so the test passes. No production code changes; no other tests change.

### Risks & unknowns

- **Word-count semantics:** the scorer counts with `content.split()` (readme_scorer.py:67), a
  plain whitespace split. Code fences, badge/link syntax, and punctuation all count as "words,"
  so I must target the `str.split()` count, not a prose word count, and verify by running the
  test rather than estimating.
- **Threshold margin:** land comfortably above 500 (~550+) so a small future edit does not drop
  the fixture back under `comprehensive`.
- **Broad regexes:** the signal patterns match substrings (e.g. `stack`, `example`, `setup`), so
  the main risk while rewriting is accidentally *removing* a required signal, not failing to
  match one. I will re-check all five signals after editing.
- **Blast radius:** confirm no other test relies on the exact old fixture text. A grep shows the
  fixture is local to this one test function, so the risk is low.

### Edge cases

- **Boundary counts:** 100 is not `> 100`, and 500 is the first `comprehensive` value (`>= 500`).
  I will stay clearly above both boundaries.
- **Badge must be an image:** keep `![alt](url)` image syntax, since a plain `[text](url)` link
  will not match the badge regex.
- **Demo link needs an explicit phrase:** include a "Live Demo" / "try it" phrase, because a bare
  URL alone does not match the demo regex.
- **Score stays above threshold:** adding more signals and words only raises `overall_score`, so
  keeping all signals present keeps `overall_score > 0.7`.
