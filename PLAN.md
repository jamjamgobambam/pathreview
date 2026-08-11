# Solution Plan

## Issue

**Issue:** README scorer test fixture is too short for its own word-count assertion

**Issue link:** https://github.com/ascherj/pathreview/issues/156

---

## Understand

The failing unit test expected the README fixture to be classified as
"comprehensive." However, the fixture itself did not contain enough words to
meet the threshold defined by the README scorer. The production logic was
working correctly—the failure was caused by outdated test data rather than an
implementation bug.

---

## Map

Files involved:

- `tests/unit/test_readme_scorer.py`
- `agent/tools/readme_scorer.py` (used to verify the scoring thresholds)

The primary file to modify is:

- `tests/unit/test_readme_scorer.py`

---

## Plan

1. Reproduce the failing unit test locally.
2. Review the README scoring logic to confirm the expected word-count
   thresholds.
3. Update the README fixture so that it exceeds the "comprehensive" threshold
   while preserving the existing quality signals.
4. Run Ruff, Black, and the unit tests to verify the change.
5. Submit the fix through a pull request.

---

## Inputs & Outputs

### Input

The README fixture string used in
`test_readme_with_all_quality_signals`.

### Output

The README fixture satisfies the required word-count threshold and the unit
test passes without changing the production implementation.

---

## Risks & Unknowns

- Future changes to the README scoring thresholds could require updates to the
  fixture.
- The fixture should remain readable and avoid introducing formatting issues
  that cause Ruff or Black to fail.

---

## Edge Cases

- README content near the threshold boundary.
- README files with many headings but insufficient descriptive text.
- README files containing code blocks, images, and links in addition to
  documentation text.