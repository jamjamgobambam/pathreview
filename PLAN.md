## Solution plan

**Issue:** [Shared test fixture for a sample user profile is missing from `tests/fixtures/`](https://github.com/ascherj/pathreview/issues/106)

### Understand
* **Root cause:** The test fixture file `tests/fixtures/sample_profiles/basic_profile.json` is not in the repository, which blocks/skips multiple integration tests and RAG pipeline evaluations that depend on a realistic user profile structure.
* **Expected behavior:** A JSON file should exist at the expected path with a realistic sample portfolio structure that can be successfully ingested and parsed by the RAG pipeline.
* **Actual behavior:** The file was missing, causing a `FileNotFoundError` when evaluation scripts or test runners attempted to access it.

### Map
* **Files involved:**
  * `tests/fixtures/sample_profiles/basic_profile.json` (The missing shared test fixture)
  * `tests/unit/test_fixtures.py` (Unit test verifying the existence and structure of the fixture)

### Plan
1. **Identify Schema Requirements:** Inspect schema definitions in `api/schemas/profile.py`, model fields in `core/models/profile.py` and `core/models/ingested_source.py`, and parser code in `ingestion/parsers/` to determine the fields and structure expected from a user profile.
2. **Recreate the JSON Fixture:** Define a valid JSON profile with:
   * `github_username`: A mock username (e.g. `janedoe`).
   * `resume`: Realistic Markdown-formatted resume text containing standard sections (Experience, Education, Skills, Projects).
   * `repositories`: A list of at least two repos, each containing `name`, `description`, `language`, `readme_content`, `file_structure`, and `pushed_at`.
3. **Verify via Tests:** Unit test in `tests/unit/test_fixtures.py` to assert the file's existence and validate its structure.
4. **Integration Testing:** Run the test suite (`pytest`) to confirm that the fixture resolves any loading issues and does not break existing test cases.

### Inputs & outputs
* **Input:** None (a static text/JSON fixture file is generated).
* **Output:** A valid `basic_profile.json` fixture that can be parsed and used by ingestion tests and RAG scripts, and a test suite verifying its validity.

### Risks & unknowns
* **Data Schema Updates:** If the underlying parser structures (e.g., `resume_parser.py` or `repo_analyzer.py`) expect additional nested keys in the future, the static fixture might need updates to remain valid.
* **Git Line Endings:** Text formatting differences (LF vs CRLF) on Windows systems during git commits could cause checksum or parse changes. Explicitly specifying `encoding="utf-8"` prevents character set issues.

### Edge cases
* **Missing repositories or empty values:** The RAG pipeline and parsers must handle profiles with zero/empty repositories or resumes gracefully (though this fixture specifically tests the populated, happy path).
* **Empty Markdown structures:** The mock resume text should contain clear section headers (e.g., `Experience:`, `Education:`) to ensure parser regexes match successfully.
