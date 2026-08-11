## Solution plan

**Issue:** [Add a `has_tests` boolean to the repo analysis output (#50)](https://github.com/ascherj/pathreview/issues/50)

### Understand
`TechDetector` never had test-detection logic added — expected output includes `has_tests: bool` (true for a `tests/`/`test/` dir, `pytest.ini`, or `test_*.py`); actual output has no such field, confirmed by a failing test ([2914f8f](https://github.com/Kunalkrk/pathreview/commit/2914f8ffb18b380721c2edc256d9f0c967b426e0)).

### Map
- `agent/tools/tech_detector.py` — add detection here.
- `tests/unit/test_tech_detector.py` — has a failing test to fix, plus a negative case to add.
- `ingestion/parsers/repo_analyzer.py` — has its own unrelated `has_tests`; reference only.

### Plan
1. Add `_detect_has_tests(filtered_files)` checking for test dir/`pytest.ini`/`test_*.py`.
2. Wire it into `_detect_tech()` and the empty-files early return.
3. Confirm `test_has_tests_detection` passes; add a negative-case test.
4. Run `make check && make test-unit`.

### Inputs & outputs
Input: same `files: list[str]` already passed in. Output: one new `has_tests: bool` key, no other fields change.

### Risks & unknowns
- Naive substring match would false-positive on `latest.py`/`contest.js` — need path/filename-aware matching.
- Open question: issue only lists Python markers; should JS/TS conventions (`__tests__/`, `spec/`) count too?
- Unrelated pre-existing bug: `_should_skip_file` misses root-level `node_modules/`/`build/` paths.
- `TechDetector` isn't wired into the live review pipeline yet, so this is only verifiable via unit tests for now.

### Edge cases
- Empty file list → `has_tests: False`, no crash.
- Mixed-case paths still detected.
- Test-like filenames outside a real test path (`latest.py`) must not be flagged.
- Test files under vendor/build paths already filtered via `_should_skip_file`.
