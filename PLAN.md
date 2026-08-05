## Solution plan

**Issue:** README scorer test fixture is too short for its own word-count
assertion — https://github.com/ascherj/pathreview/issues/156
(branch `test/156-readme-scorer-fixture-word-count`, Tier 1)

### Understand

**Root cause.** `tests/unit/test_readme_scorer.py::test_readme_with_all_quality_signals`
feeds the scorer a fixture README that is only ~51 words long, then asserts the
result is a long, `"comprehensive"` README. The production scorer is correct;
the test's fixture contradicts the test's own assertions.

**Expected vs. actual.**

- *Expected by the test:* `word_count > 100` **and** `word_count_category == "comprehensive"`.
- *Actual from correct scorer behavior:* `word_count == 51`, `word_count_category == "minimal"`.
- Result: `assert 51 > 100` fails.

**Key subtlety.** The scorer (`agent/tools/readme_scorer.py:70-75`) categorizes:
`< 100 → minimal`, `100–499 → adequate`, `>= 500 → comprehensive`. So merely
extending the fixture "past 100 words" (as the issue loosely suggests) satisfies
line 56 but **not** line 57 — 150 words would classify as `"adequate"`. To
satisfy both assertions the fixture must reach **≥ 500 words**. This is a
**test bug, not a production bug.**

### Map

| File | Involvement |
|------|-------------|
| `tests/unit/test_readme_scorer.py` | **The only file I will touch.** Enlarge the fixture inside `test_readme_with_all_quality_signals` (lines ~19-49). |
| `agent/tools/readme_scorer.py` | Reference only (not modified). Relevant logic: word-count categorization (`:70-75`), signal-detection regexes (`:79-97`), overall-score composition (`:99-109`). |

The enlarged fixture must keep the markers the scorer's regexes match so the
other assertions (lines 58-63) still pass:
- Installation: `install | setup | getting started`
- Usage: `usage | how to use | quickstart | example`
- Badges: `![...](...)` image syntax
- Demo: `demo | live demo | try it | see it | live link`
- Tech stack: `tech stack | technologies | built with | technology | stack`

### Plan

1. **Rewrite the fixture** in `test_readme_with_all_quality_signals` to a
   realistic README of **≥ 500 words** (target ~520-550 for headroom).
2. **Preserve every quality signal** — keep `## Installation` (code block),
   `## Usage` (code block), `## Features`, `## Tech Stack`, two badge lines,
   and a `## Live Demo` link verbatim.
3. **Pad with genuine prose** (Overview, Configuration, Architecture,
   Contributing, FAQ) so the content reads like a real comprehensive README,
   not repeated filler.
4. **Validate:** run the single test, then the full scorer file, then
   `make check` (ruff/black/mypy) and `make test-unit`.
5. **Commit & push** on the working branch using Conventional Commits.

### Inputs & outputs

- **Input to the fix:** the fixture README string passed to
  `scorer.execute({"readme_content": readme})`.
- **Output / what changes:** only the test fixture content. After the change
  the scorer returns `word_count >= 500`, `word_count_category == "comprehensive"`,
  all `has_*` signal flags `True`, and `overall_score` = `7/7 = 1.0` (six boolean
  signals + `min(word_count/500, 1.0)` bonus) — comfortably `> 0.7`.
- **Net effect:** `pytest tests/unit/test_readme_scorer.py` goes from
  `1 failed, 22 passed` to `23 passed`. No production behavior changes.

### Risks & unknowns

- **Word-count miscount:** `len(content.split())` counts whitespace-separated
  tokens; I'll verify the real count from test output rather than eyeballing.
- **Dropping a signal in the rewrite** would flip a `has_*` flag to false —
  mitigate by keeping section headers verbatim and re-running the whole file.
- **Lint (E501) on long lines** — the fixture is short-line markdown in a
  triple-quoted block, so it should pass; `make lint` confirms.
- **Unknown / maintainer preference:** the issue offers "extend fixture OR
  correct assertion." I chose extend-the-fixture to preserve the test's intent
  (and avoid overlap with the existing minimal/adequate tests); open to
  switching if review disagrees.

### Edge cases

- **Boundary at exactly 500 words:** `>= 500` is `comprehensive`, so target
  comfortably above 500 (not exactly 500) to avoid an off-by-one from
  recounting.
- **Case-insensitive / keyword-variant sections:** detection is
  case-insensitive and keyword-based, so headers like `## Getting Started` or
  `## Technologies` also satisfy signals — keep the plain canonical headers to
  avoid ambiguity.
- **No regression to sibling tests:** the dedicated `minimal` / `adequate` /
  `comprehensive` threshold tests (lines 89-117) must remain untouched and
  green — this change is scoped to a single test's fixture.
