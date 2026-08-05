## Solution plan

**Issue:** [#106 — Shared test fixture for a sample user profile is missing from `tests/fixtures/`](https://github.com/ascherj/pathreview/issues/106)

### Understand

The repository is missing `tests/fixtures/sample_profiles/basic_profile.json`, even though issue #106 and the benchmark runner's TODO in `scripts/run_evals.py` identify that directory as the source of reusable sample portfolios. I reproduced the gap locally: the expected path does not exist, and reading it raises `FileNotFoundError`. This prevents any test or evaluation flow that expects the shared profile from loading consistent portfolio data.

The fix should restore a valid, deterministic JSON document at the exact requested path. It should represent one fictional GitHub user, a realistic resume, and exactly two distinct repositories so consumers can exercise a complete portfolio without network calls or ad hoc mocks. The current repository does not enforce a benchmark JSON schema yet, so the validation test added with the fixture will make the chosen contract explicit.

### Map

Files and code paths involved:

- `tests/fixtures/sample_profiles/basic_profile.json` — create the missing shared portfolio fixture with the GitHub username, resume data, and two repositories required by the issue.
- `tests/unit/test_basic_profile_fixture.py` — create a focused test that loads the JSON, verifies its required structure, and produces clear failures if the fixture is missing or malformed.
- `scripts/run_evals.py` — existing future consumer; its `main()` TODO names `tests/fixtures/sample_profiles/` as the benchmark input directory. I will use this path as the source of truth without expanding the issue into implementing the evaluation runner.
- `core/models/profile.py` — reference for the existing profile concepts and field names, especially `github_username`, `resume_filename`, and `resume_text`.
- `api/schemas/profile.py` — reference for the public profile representation and username constraints.
- `tests/conftest.py` — reference for the tone and content of the existing fictional resume and README fixtures; it will remain unchanged unless implementation work reveals a direct reuse opportunity.

### Plan

1. Define the smallest explicit JSON contract that satisfies issue #106 and matches the concepts already present in `core/models/profile.py`: a non-empty `github_username`, a `resume` object with `filename` and `text`, and a `repositories` array containing exactly two objects.
2. Create `tests/fixtures/sample_profiles/basic_profile.json` with fictional, deterministic data. Give both repositories unique names and URLs plus non-empty descriptions, primary languages, and README text so downstream tests have meaningful content to analyze.
3. Add `tests/unit/test_basic_profile_fixture.py`. Resolve the fixture path from `Path(__file__)` rather than the process working directory, load it with `json.loads()`, and assert the required keys, value types, non-blank strings, exactly two repositories, and unique repository names.
4. Validate the artifact directly with `python -m json.tool tests/fixtures/sample_profiles/basic_profile.json`, then run the focused test with `pytest tests/unit/test_basic_profile_fixture.py`.
5. Run `make test-unit` and `make check` to catch regressions, formatting problems, or type errors. If a later implementation of `scripts/run_evals.py` establishes a different schema, update the fixture and focused test together rather than adding a second incompatible profile format.

### Inputs & outputs

The fix is a data artifact rather than a production function change.

- **Input path:** `tests/fixtures/sample_profiles/basic_profile.json`
- **Input format:** UTF-8 JSON object
- **Required top-level data:**
  - `github_username: str`
  - `resume: {"filename": str, "text": str}`
  - `repositories: list[dict]`
- **Required repository data:** each of the two entries will contain non-empty `name`, `url`, `description`, `primary_language`, and `readme` strings.
- **Output on success:** `json.loads()` returns a reusable dictionary describing one complete sample portfolio. Tests and future evaluation code can consume it without GitHub access, file uploads, database records, or generated values.
- **Validation behavior:** `test_basic_profile_fixture_has_expected_shape() -> None` passes only when the file exists, parses successfully, contains the required fields, and has exactly two distinct repositories. Missing or invalid data produces a focused assertion or JSON decoding failure that points back to the fixture.

No API response, database schema, or runtime user behavior should change as part of this issue.

### Risks & unknowns

1. **The exact benchmark JSON schema is not implemented.** `scripts/run_evals.py` only contains a TODO, so it does not yet define whether resume and repository data should be nested or flat. I will use a minimal documented structure based on issue #106 and `core/models/profile.py`, and keep the schema assertion in `tests/unit/test_basic_profile_fixture.py` so future changes happen in one visible place.
2. **The repository has two fixture conventions.** Existing text fixtures live in `tests/conftest.py`, while issue #106 explicitly requires a JSON file under `tests/fixtures/sample_profiles/`. I will follow the issue's exact path and leave the Python fixtures intact, avoiding an unrelated migration or duplicate pytest fixture.
3. **A validation test could become too coupled to sample wording.** In `tests/unit/test_basic_profile_fixture.py`, I will validate structure, types, counts, and non-blank content rather than exact prose. This keeps the data editable while preserving the contract.
4. **Relative paths can work locally but fail under a different test working directory.** The new test will derive the repository-relative fixture path from its own file location instead of assuming pytest was launched from the project root.
5. **Realistic data could accidentally include real personal information.** `basic_profile.json` will use clearly fictional names, usernames, URLs, and resume details while still providing representative technical content.

### Edge cases

- The fixture file is absent, renamed, or placed in the wrong directory: the focused test should fail at the exact expected path.
- The file contains malformed JSON, a trailing comma, or invalid escaping in multiline resume/README content: `json.loads()` and `python -m json.tool` should fail clearly.
- `github_username`, resume text, or a repository field is empty or whitespace-only: the validation test should reject it.
- `repositories` is missing, is not a list, contains fewer or more than two entries, or repeats the same repository name: the validation test should reject it.
- A repository has valid metadata but no README content: the validation test should reject it because the evaluation pipeline needs analyzable project text.
- Resume and README strings contain punctuation or line breaks: the JSON must preserve them as valid strings and load without data loss.
