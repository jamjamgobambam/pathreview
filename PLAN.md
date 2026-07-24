# PLAN.md

## Solution plan

**Issue:** #156 — README scorer test fixture is too short for its own word-count assertion
**Link:** [PASTE ISSUE LINK]

### Understand

The failing test is `test_readme_with_all_quality_signals` in
`tests/unit/test_readme_scorer.py` (lines 17–63). It builds an inline README
fixture (an indented triple-quoted string) and passes it to
`ReadmeScorer.execute(...)`, then makes two word-count assertions that the
fixture cannot satisfy:

- Line 56: `assert data["word_count"] > 100`
- Line 57: `assert data["word_count_category"] == "comprehensive"`

**Expected behavior (as the test author intended):** a README containing all
quality signals should score as a long, "comprehensive" document (word_count
> 100, and category `"comprehensive"`).

**Actual behavior (confirmed by running the test):** the fixture tokenizes to
**51 words**. `ReadmeScorer._score_readme` (`agent/tools/readme_scorer.py`,
lines 56–124) computes `word_count = len(content.split())` (line 67) and
categorizes it (lines 70–75):

```python
if word_count < 100:      word_count_category = "minimal"
elif word_count < 500:    word_count_category = "adequate"
else:                     word_count_category = "comprehensive"
```

So 51 words → category `"minimal"`. The test fails at line 56 with
`assert 51 > 100`. Line 57 is never reached, but with 51 words it would also
fail (`"comprehensive"` requires `word_count >= 500`, not just `> 100` — the
assertion and the fixture are inconsistent with each other on *two* counts).

**Root cause (confirmed):** the mismatch is in the **test fixture / test
expectations**, not in the scorer. The scorer behaves consistently — 22 of the
23 tests in the file pass, including the dedicated category tests
(`test_word_count_category_minimal/adequate/comprehensive` at lines 89–117),
which prove the thresholds work as intended. Only `test_readme_with_all_quality_signals`
asserts a word count its own fixture can't reach.

**Not yet decided (Week 9 decision):** *how* to reconcile them. There are two
candidate directions, and they are not equivalent:
1. Lengthen the fixture so it genuinely has > 500 words (satisfies both the
   `> 100` assertion *and* the `"comprehensive"` category assertion), or
2. Relax the assertions to match a realistic all-signals README (e.g. assert
   `> 40` words and category `"minimal"`/`"adequate"`), which changes what the
   test claims to verify.
   Direction 1 keeps the test's original intent ("comprehensive"); direction 2
   changes the test's meaning. I will confirm the intended semantics before
   choosing.

### Map

Files, functions, tests, and fixtures involved:

- **Test (fails):** `tests/unit/test_readme_scorer.py`
  - `TestReadmeScorer.test_readme_with_all_quality_signals` (lines 17–63) — the
    single failing test; owns the too-short inline fixture and the two
    conflicting word-count assertions (lines 56–57). **This is the file I will
    likely touch.**
  - Reference tests that already pass and define correct threshold behavior
    (do NOT need changing, but constrain the fix):
    `test_word_count_category_minimal` (89–97),
    `test_word_count_category_adequate` (99–107),
    `test_word_count_category_comprehensive` (109–117).
- **Scorer (source of truth for thresholds; likely NOT changed):**
  `agent/tools/readme_scorer.py`
  - `ReadmeScorer._score_readme` (56–124): `word_count` computation (67) and
    category thresholds (70–75). This defines "comprehensive" = `>= 500` words.
- **Fixture location:** the fixture is **inline inside the test method**
  (lines 19–49) — there is no separate fixture file under `tests/fixtures/`
  for this case, so any fixture change is local to this one test.

### Plan

1. Re-run the single failing test to capture a fresh, real failure line and
   the reported `word_count` (baseline evidence for the PR).
2. Confirm the intended semantics of "all quality signals present": decide
   whether such a README is meant to be `"comprehensive"` (>= 500 words) or
   whether the assertions were simply overstated relative to a normal README.
3. Choose the fix direction (fixture-lengthening vs. assertion-adjustment) and
   record the rationale — do NOT touch scorer logic in
   `agent/tools/readme_scorer.py`.
4. Implement the chosen change in `test_readme_with_all_quality_signals` only,
   keeping all other quality-signal assertions (installation, usage, badges,
   demo, tech stack, `overall_score > 0.7`) intact.
5. Run the full file `tests/unit/test_readme_scorer.py` and confirm
   `23 passed`, and run the broader unit suite (`tests/unit`) to confirm no
   regressions elsewhere.

### Inputs & outputs

- **Input:** `ReadmeScorer.execute({"readme_content": <README string>})`.
- **Relevant outputs today:** for the current fixture the scorer returns
  `word_count=51`, `word_count_category="minimal"`, and
  `overall_score≈0.87` (all quality-signal booleans already `True`).
- **What should change after the fix:** the test must stop making assertions
  the fixture cannot meet. After the fix, running
  `test_readme_with_all_quality_signals` passes because the fixture's word
  count and the asserted `word_count`/`word_count_category` are mutually
  consistent. **No change to scorer output for any given input** — only the
  test's fixture text and/or expectations change.

### Risks & unknowns

- **Weakening the assertion:** lowering the `> 100` / `"comprehensive"`
  expectations (direction 2) would make the test verify less than it claims
  ("all signals AND comprehensive length"). Risk of silently reducing coverage.
- **Over-reaching into scorer logic:** editing `_score_readme` thresholds in
  `agent/tools/readme_scorer.py` to "make the test pass" would break the three
  category tests (lines 89–117) and change product behavior. Out of scope for
  this issue.
- **Shared-fixture risk:** low — the fixture is inline in this one test, so a
  change here does not affect other tests. (Confirmed there is no shared
  README fixture file feeding this case.)
- **Unknown:** the original author's intent for "comprehensive" in this test —
  must be confirmed in Week 9 before choosing a direction.

### Edge cases

The fix (whichever direction) must keep these behaviors correct, mirroring the
existing passing tests so nothing regresses:

- **Empty README** (`""`): `has_readme=False`, `word_count=0`,
  category `"minimal"`, `overall_score=0.0`
  (`test_readme_with_no_content`, lines 65–74).
- **Whitespace-only README:** `has_readme=False`, `word_count=0`
  (`test_whitespace_only_readme`, lines 279–285).
- **Very short README** (title only, `# Project Title`): `word_count < 100`,
  category `"minimal"` (`test_readme_with_only_title`, lines 76–87).
- **Below threshold** (< 100 words): category `"minimal"`
  (`test_word_count_category_minimal`, lines 89–97).
- **Adequate band** (100–499 words): category `"adequate"`
  (`test_word_count_category_adequate`, lines 99–107).
- **At/above the comprehensive threshold** (>= 500 words): category
  `"comprehensive"` (`test_word_count_category_comprehensive`, lines 109–117).
- **All-quality-signals README** (the fixture under repair): quality-signal
  booleans stay `True` and `overall_score > 0.7`; only the word-count
  expectations become internally consistent.
