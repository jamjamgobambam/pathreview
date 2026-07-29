# Solution Plan — Issue #156

**Issue:** README scorer test fixture is too short for its own word-count assertion
**Link:** https://github.com/ascherj/pathreview/issues/156
**Branch:** `test/156-readme-scorer-fixture-word-count`
**Tier:** 1

---

## 1. Problem statement

`tests/unit/test_readme_scorer.py::test_readme_with_all_quality_signals` is
meant to verify that a rich, high-quality README scores well and is classified
as `"comprehensive"`. It asserts:

- `data["word_count"] > 100` (line 56)
- `data["word_count_category"] == "comprehensive"` (line 57)

But the fixture README in that test contains only ~51 words, so the test fails
against a correctly-behaving scorer (`assert 51 > 100`). The bug is in the
**test's fixture**, not in the production code.

## 2. Root-cause analysis (from reading the code)

`agent/tools/readme_scorer.py` categorizes word count as:

| Words        | Category        |
|--------------|-----------------|
| `< 100`      | `minimal`       |
| `100–499`    | `adequate`      |
| `>= 500`     | `comprehensive` |

(See `readme_scorer.py:70-75`.) `word_count = len(content.split())`.

**Key insight — the naive fix is insufficient.** The issue text says "extend
the fixture past 100 words," but that alone only satisfies line 56. To also
satisfy `word_count_category == "comprehensive"` (line 57), the fixture must
reach **≥ 500 words**. A fixture of, say, 150 words would flip line 56 green
but leave line 57 red (category would be `"adequate"`). The two assertions
together require a fixture of **at least 500 words**.

The other assertions in the test must keep passing, so the enlarged fixture
must still contain the signal markers the scorer looks for
(`readme_scorer.py:79-97`):

- Installation: `install | setup | getting started`
- Usage: `usage | how to use | quickstart | example`
- Badges: markdown image syntax `![...](...)`
- Demo: `demo | live demo | try it | see it | live link`
- Tech stack: `tech stack | technologies | built with | technology | stack`
- `overall_score > 0.7` — with all 6 boolean signals true and `word_count ≥ 500`
  (bonus `min(wc/500, 1.0) = 1.0`), the score is `7/7 = 1.0`, comfortably above.

## 3. Chosen approach

**Extend the fixture README to ≥ 500 real words while preserving every quality
signal**, rather than weakening the assertions.

Rationale: the test's *intent* is to exercise the "comprehensive, all-signals"
path. Correcting the assertions downward (e.g. asserting `adequate`/`minimal`)
would make the test pass but stop testing what it was written to test, and
would duplicate the existing `test_word_count_category_adequate` /
`test_word_count_category_minimal` cases. Extending the fixture keeps the
test meaningful.

### Alternatives considered

- **Correct the assertion instead of the fixture** (assert `word_count < 100`
  and `category == "minimal"`). Rejected: destroys the test's purpose and
  overlaps existing minimal/adequate tests.
- **Extend fixture to only ~150 words.** Rejected: fails line 57 because 150
  words → `"adequate"`, not `"comprehensive"`.
- **Lower the `comprehensive` threshold in the scorer** to match the fixture.
  Rejected: this is a test bug, not a spec bug; changing production behavior
  would break `test_word_count_category_comprehensive` (which expects `>500`).

## 4. Concrete steps

1. In `test_readme_with_all_quality_signals`, replace the fixture README string
   with a longer, realistic README of **≥ 500 words** (target ~520–550 for
   headroom).
2. Preserve all existing signal sections: `## Installation` (with code block),
   `## Usage` (with code block), `## Features`, `## Tech Stack`, two badge
   image lines, and a `## Live Demo` link — exactly the markers already
   asserted on lines 58–62.
3. Pad the word count with genuine README prose (e.g. an Overview,
   Configuration, Architecture, Contributing, and FAQ section) so the content
   reads like a real comprehensive README, not filler.
4. Run the single test, then the full scorer suite, then lint/format/typecheck.
5. Commit on the working branch using Conventional Commits and push.

## 5. Files I'll touch

| File | Change |
|------|--------|
| `tests/unit/test_readme_scorer.py` | Enlarge the fixture in `test_readme_with_all_quality_signals` only. No other tests change. |

No production code changes. No new files.

## 6. Testing & validation

```bash
# Targeted
pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -q
# Full scorer suite (guard against regressions in the other 22 tests)
pytest tests/unit/test_readme_scorer.py -q
# Repo standards
make check        # ruff + black + mypy
make test-unit
```

Expected after fix: `23 passed`. Confirm the scorer logs
`category=comprehensive` and `word_count >= 500` for the new fixture.

## 7. Risks & unknowns

- **Word-count miscount:** `split()` counts whitespace-separated tokens;
  indentation/markdown punctuation attached to words still counts as one token.
  Mitigation: verify the actual `word_count` from the test output / a quick
  `len(readme.split())` check rather than eyeballing.
- **Accidentally dropping a signal:** a rewrite could omit a keyword and flip
  `has_*` to false. Mitigation: keep the existing section headers verbatim and
  re-run the full file.
- **Line-length lint (E501):** long fixture lines could trip `ruff`. The README
  is a triple-quoted block of short lines, so this should be fine, but
  `make lint` will confirm.
- **Unknown:** whether maintainers prefer "extend fixture" vs "correct
  assertion." The issue explicitly offers both; this plan picks the
  intent-preserving option and documents why. Open to switching if review
  feedback disagrees.

## 8. Rollback

Single-file, test-only change on an isolated branch. Rollback = revert the one
commit (`git revert <sha>`) or `git checkout main -- tests/unit/test_readme_scorer.py`.
No data, migrations, or production behavior affected.
