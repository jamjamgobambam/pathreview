# Solution plan

**Issue:** [#156 — README scorer test fixture is too short for its own word-count assertion](https://github.com/ascherj/pathreview/issues/156)

### Understand

`test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py` is
meant to prove that a rich, well-documented README is scored as
`"comprehensive"`. It asserts `word_count > 100` and
`word_count_category == "comprehensive"`.

- **Expected:** the sample README fixture is long enough that the scorer reports
  a high word count and the `"comprehensive"` category.
- **Actual:** the fixture only contains ~51 words, so the scorer (correctly)
  reports `word_count = 51` and category `"minimal"`, and the test fails with
  `assert 51 > 100`.

**Root cause:** the bug is in the *test* — the fixture is too short for the
assertions written against it — not in the scoring logic. The scorer's
thresholds are correct and deliberate: `< 100` → `minimal`, `100–499` →
`adequate`, `500+` → `comprehensive` (`agent/tools/readme_scorer.py:70-75`). To
legitimately reach `"comprehensive"` the fixture must exceed **500** words, not
just 100.

### Map

| File | Role in the fix |
|---|---|
| `tests/unit/test_readme_scorer.py` | **Primary edit.** Fixture + assertions in `test_readme_with_all_quality_signals`. |
| `agent/tools/readme_scorer.py` | **Reference only.** Defines the word-count thresholds and scoring; read to confirm expected behavior — not expected to change. |
| `pyproject.toml` / `.pre-commit-config.yaml` | **Possible edit.** May need to resolve the pre-commit `mypy` blocker (see Risks). |

### Plan

1. **Choose the fix direction.** The test's docstring and intent ("all quality
   signals returns high score") say the fixture *should* be comprehensive, so
   extend the fixture rather than weaken the assertions. Extend the sample
   README past 500 words while keeping every quality signal it already
   exercises: installation, usage, badges, demo link, and tech-stack sections.
2. **Rewrite the fixture** so `content.split()` yields 500+ words and the
   category becomes `"comprehensive"`; keep the section keywords and badge/demo
   markup so the other assertions (`has_installation_section`, `has_badges`,
   `has_demo_link`, `has_tech_stack_section`, `overall_score > 0.7`) still hold.
3. **Clear the pre-commit `mypy` blocker** so the change is committable with
   hooks active (the file currently fails `disallow_untyped_defs`). Decide
   between annotating the test functions vs. excluding `tests/` in mypy config.
4. **Verify:** run `pytest tests/unit/test_readme_scorer.py -q` (all pass) and
   `pre-commit run --files tests/unit/test_readme_scorer.py` (ruff/black/mypy
   clean).
5. **Ship:** update JOURNAL.md, push the branch, open a PR against upstream.

### Inputs & outputs

- **Input:** the `readme` fixture string inside
  `test_readme_with_all_quality_signals`.
- **Output:** a longer fixture (500+ words, all signals intact) and assertions
  that pass against the scorer's real, unchanged behavior. **No change to
  `readme_scorer.py`'s logic or public output** — this is a test-only fix.

### Risks & unknowns

- **Pre-commit `mypy` wall (biggest risk).** `disallow_untyped_defs = true` and
  `tests/` is not excluded, so mypy checks the *entire* file and flags all ~24
  untyped test functions on any edit. The fix commit cannot pass hooks until
  this is resolved — either add annotations (`scorer: ReadmeScorer`, `-> None`)
  to the functions in the file, or add `tests/` to mypy's `exclude`. Unsure
  which the maintainer prefers; annotating is more in the project's spirit but
  enlarges the diff.
- **Fix direction.** Extending the fixture assumes the test intent is
  "comprehensive." If the maintainer instead wants the assertions corrected to
  match a shorter README, the fix flips. Worth confirming on the issue.
- **Word-count mechanics.** The scorer counts via `content.split()`, so
  indentation, code fences, and punctuation all count as tokens. Need to verify
  the rewritten fixture reliably clears 500 words after Python strips the
  triple-quoted indentation.

### Edge cases

- Triple-quoted-string indentation inflating/deflating the split-based word
  count.
- Badge regex (`!\[.*?\]\(.*?\)`) and demo/tech-stack keywords must remain
  present after the rewrite.
- `overall_score > 0.7` must still hold once the fixture changes.
- Don't regress the sibling threshold tests (`minimal` / `adequate` /
  `comprehensive`) that pin the 100/500 boundaries.
