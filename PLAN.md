## Solution plan

**Issue:** [README scorer test fixture is too short for its own word-count assertion #156](https://github.com/ascherj/pathreview/issues/156)

### Understand

`ReadmeScorer._score_readme` (in [agent/tools/readme_scorer.py](agent/tools/readme_scorer.py)) categorizes README content by word count:

- `< 100` words → `"minimal"`
- `< 500` words → `"adequate"`
- `>= 500` words → `"comprehensive"`

The test `test_readme_with_all_quality_signals` in [tests/unit/test_readme_scorer.py](tests/unit/test_readme_scorer.py) is meant to exercise a "gold standard" README that hits every quality signal (installation, usage, badges, demo link, tech stack) and expects a high overall score. But its fixture string is only **51 words**, while the assertions expect:

```python
assert data["word_count"] > 100
assert data["word_count_category"] == "comprehensive"
```

Since `"comprehensive"` requires `word_count >= 500`, and the fixture doesn't even clear the 100-word bar, the test fails deterministically: `assert 51 > 100`. The scorer logic itself is correct and consistent with the other word-count tests (`test_word_count_category_minimal/adequate/comprehensive` all pass) — this is purely a test-fixture/assertion mismatch, not a scoring bug.

**Expected behavior:** the fixture representing a comprehensive, all-signals README should actually contain >= 500 words so its assertions are internally consistent and the test reflects a realistic "great README."

**Actual behavior:** the fixture is short (51 words), so the test fails even though `ReadmeScorer` behaves correctly.

### Map

Files expected to be touched:

- [tests/unit/test_readme_scorer.py](tests/unit/test_readme_scorer.py) — `test_readme_with_all_quality_signals` (lines ~17-72): expand the fixture content so it naturally reaches >= 500 words while keeping all existing quality-signal markers (`## Installation`, `## Usage`, `## Tech Stack`, badges, demo link) intact.
- No changes expected in [agent/tools/readme_scorer.py](agent/tools/readme_scorer.py) — the scoring logic already matches its own documented thresholds and passes every other test in the suite.
- [JOURNAL.md](JOURNAL.md) — Week 8 entry (this reproduction).

### Plan

1. Confirm reproduction (done): ran `pytest tests/unit/test_readme_scorer.py -k all_quality_signals -q`, observed `assert 51 > 100`, and verified the scorer's thresholds are consistent with the other passing word-count tests.
2. Expand the `readme` fixture string in `test_readme_with_all_quality_signals` with additional realistic prose (e.g. longer descriptions under each existing section, an added "Configuration" or "Contributing" section) until word count is comfortably >= 500, without removing any of the existing signal markers the test already checks for (installation, usage, badges, demo link, tech stack).
3. Re-run the full `tests/unit/test_readme_scorer.py` suite locally to confirm the target test passes and no other test in the file regresses (particularly `test_overall_score_calculation`, which reuses similar patterns).
4. Re-run `make check` (ruff + black + mypy) and `make test-unit` for the whole repo to catch any unrelated regressions before opening the PR.
5. Update the PR description referencing issue #156, following the strong-PR-description examples and `docs/CONTRIBUTING.md` conventional-commit format (`test(agent): ...`).

### Inputs & outputs

- **Input:** the `readme` fixture string literal inside `test_readme_with_all_quality_signals`; no external inputs or runtime config are involved since this is a pure unit test over a hardcoded string.
- **Output:** an updated fixture whose real word count is >= 500, so `scorer.execute({"readme_content": readme})` returns `word_count_category == "comprehensive"` and `word_count > 100` truthfully, and the test passes without weakening any assertion.

### Risks & unknowns

- **Risk:** padding the fixture with filler text could accidentally break one of the regex-based signal checks (e.g. `has_installation_section`, `has_tech_stack_section` in [agent/tools/readme_scorer.py:79-97](agent/tools/readme_scorer.py)) if added prose happens to interfere with section header matching — mitigated by keeping the existing `## Installation` / `## Usage` / `## Tech Stack` headers untouched and only adding body text.
- **Risk:** the added word count could push `overall_score` in [agent/tools/readme_scorer.py:99-109](agent/tools/readme_scorer.py) close to 1.0, but the test only asserts `overall_score > 0.7`, so there's headroom — should double check this doesn't collide with any upper-bound assertion elsewhere in the file.
- **Unknown:** whether the maintainers would prefer the alternative fix mentioned in the issue (loosening the assertion to match the current 51-word fixture, e.g. asserting `"adequate"`/`> 50` instead) rather than growing the fixture. I'm planning to expand the fixture rather than weaken the assertion, since the test's name and intent (`test_readme_with_all_quality_signals`) implies it should model a genuinely comprehensive README — I'll flag this choice explicitly in the PR description so a reviewer can redirect me if they'd rather see the assertion changed instead.
- **Unknown:** whether any other test file or fixture in the repo reuses this same README string (a quick grep found no reuse, but worth reconfirming before editing).

### Edge cases

- Fixture must still parse as `has_readme is True` (non-empty after `.strip()`).
- Word count must land clearly inside the `"comprehensive"` band (`>= 500`), not just barely over 100, so the fix isn't fragile to minor future edits of the fixture.
- All other per-signal assertions in the same test (`has_installation_section`, `has_usage_section`, `has_badges`, `has_demo_link`, `has_tech_stack_section`) must remain `True` after the fixture is expanded.
- `overall_score > 0.7` must still hold — since `word_count` bonus is `min(word_count / 500, 1.0)`, reaching exactly 500 words maximizes that component, which only helps satisfy this assertion.
- No other currently-passing test in `test_readme_scorer.py` should regress (run the full file, not just the one test, after the change).
