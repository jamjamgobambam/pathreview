## Solution plan

**Issue:** [#106 — Shared test fixture for a sample user profile is missing from `tests/fixtures/`](https://github.com/ascherj/pathreview/issues/106)

### Understand

**Root cause:** `tests/fixtures/sample_profiles/basic_profile.json` was deleted and never restored. No `tests/fixtures/` directory exists in the repo at all. As a result, any integration test that loads a realistic sample profile from that path either crashes with `FileNotFoundError` or has to construct inline test data — causing fixture data to drift across test files.

**Expected:** A single shared JSON fixture at `tests/fixtures/sample_profiles/basic_profile.json` and a corresponding `sample_profile` pytest fixture in `tests/conftest.py` that every test can import, so profile data has one source of truth.

**Actual:** The directory and file are absent; `tests/conftest.py` has no `sample_profile` fixture; unit tests that need a profile (e.g. `test_review_service.py`) each build their own minimal `Mock()` objects with inconsistent fields.

### Map

Files I expect to touch:

| File | Change |
|------|--------|
| `tests/fixtures/sample_profiles/basic_profile.json` | **Create** — the missing fixture |
| `tests/conftest.py` | **Edit** — add `sample_profile` fixture that loads and returns the JSON |
| `tests/integration/test_shared_profile_fixture.py` | **Already created** — reproduction test; will pass after fix |
| `tests/unit/test_review_service.py` | **Edit** — replace local `mock_profile` fixture with the shared one |

### Plan

1. **Create the fixture directory and JSON file**
   - `mkdir -p tests/fixtures/sample_profiles/`
   - Write `basic_profile.json` with realistic data matching the `Profile` model fields: `id`, `user_id`, `github_username`, `resume_filename`, `resume_text`, `portfolio_url`, and a `repos` array with two sample repositories.

2. **Add a `sample_profile` fixture in `tests/conftest.py`**
   - Open and parse `basic_profile.json` relative to the fixture file's path.
   - Return the dict so tests can use it directly (no database needed for unit tests).

3. **Update `test_review_service.py` to use the shared fixture**
   - Remove the local `mock_profile` fixture.
   - Replace usages with the new `sample_profile` fixture from `conftest.py`, so the test drives off consistent data.

4. **Verify the reproduction tests now pass**
   - Run `pytest tests/integration/test_shared_profile_fixture.py -v` and confirm 3 passed, 0 failed.

5. **Run the full test suite to check for regressions**
   - `pytest tests/unit/ -v` — confirm no existing tests break.

### Inputs & outputs

**Input:** Nothing external — the fix is self-contained file creation and fixture wiring.

**Output / change:**
- `tests/fixtures/sample_profiles/basic_profile.json` exists with valid JSON.
- `conftest.py` exposes a `sample_profile` dict fixture any test can request.
- `test_shared_profile_fixture.py` goes from 1 failed / 2 skipped → 3 passed.
- `test_review_service.py` uses the shared fixture instead of its own `Mock()`.

### Risks & unknowns

- **Schema drift:** The JSON fixture must stay in sync with `core/models/profile.py`. If the `Profile` model adds or removes fields in the future, the fixture will need updating. Mitigation: the reproduction tests assert the expected fields; a schema mismatch will surface immediately.
- **UUID format:** The `Profile.id` and `user_id` columns use `UUID(as_uuid=False)` (stored as strings). The fixture JSON should store UUIDs as strings (e.g. `"11111111-1111-1111-1111-111111111111"`) so they round-trip cleanly.
- **`repos` field is not in the ORM model:** The `Profile` DB model has no `repos` column; repos live elsewhere (e.g. `IngestedSource`). The fixture JSON can include a `repos` array as supplemental test data, but the `conftest.py` fixture should make it clear this is not a direct DB mapping.

### Edge cases

- **Fixture file unreadable / malformed JSON** — the `conftest.py` fixture should let the `json.JSONDecodeError` propagate (fail loudly, not silently skip).
- **Tests that need a `Profile` ORM object, not a dict** — the shared fixture returns a plain dict; tests that need a real `Profile` instance should construct one from the dict using `Profile(**data)` or continue to use mocks for pure unit tests.
- **Empty or null optional fields** — `github_username`, `portfolio_url`, `resume_filename`, and `resume_text` are all nullable in the model; the fixture should populate all of them so tests can also cover the non-null paths.
