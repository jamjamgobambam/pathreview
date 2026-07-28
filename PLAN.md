## Solution plan

**Issue:** #106 — Shared test fixture for a sample user profile is missing from `tests/fixtures/`
https://github.com/ascherj/pathreview/issues/106

### Understand
The repo is missing the entire `tests/fixtures/` directory. The fixture it should contain,
`tests/fixtures/sample_profiles/basic_profile.json`, doesn't exist and has no history in
`git log --all -- tests/fixtures`, so it was either never committed or removed before this
history began. `scripts/run_evals.py` still has a TODO comment (line 8) pointing at
`tests/fixtures/sample_profiles/` as the source of "benchmark portfolios," so the path is a
real, expected convention — just never fulfilled.

Right now `tests/conftest.py` only defines two fixtures, `sample_resume_text` and
`sample_readme_text`, both plain inline strings (no file loading anywhere in the test suite
yet). The `Profile` model (`core/models/profile.py`) has fields `github_username`,
`resume_filename`, `resume_text`, and `portfolio_url`. There's no `Repo`/`repository` model —
repos are represented as `IngestedSource` rows with `source_type="repo"`, `filename`, and
`source_url` (`core/models/ingested_source.py`). So "a realistic sample portfolio (GitHub
username, resume, two repos)" maps to: one profile-shaped object plus a list of two
repo-shaped objects with a name, description, URL, and README-style text.

**Root cause:** The fixture file (and its parent folder) simply doesn't exist in the repo.
This is missing test data, not a code bug — no production code needs to change.

### Map
Files I expect to touch:
- `tests/fixtures/sample_profiles/basic_profile.json` (new file) — the restored fixture
  itself.
- `tests/conftest.py` — add a `sample_profile_data` fixture that loads the JSON file, so
  tests can request it the same way they request `sample_resume_text` today.
- `tests/unit/test_conftest_fixtures.py` or similar (new, small test) — a basic test proving
  the fixture loads and has the expected keys, so this isn't dead weight sitting unused.

Files I looked at but won't touch:
- `scripts/run_evals.py` — only has a TODO comment referencing the path; implementing the
  eval runner itself is out of scope for this issue.
- `core/models/profile.py`, `core/models/ingested_source.py` — read for field names only, no
  model changes needed.

### Plan
1. Create the directory `tests/fixtures/sample_profiles/`.
2. Write `basic_profile.json` with a realistic profile: `github_username`, `resume_filename`,
   `resume_text` (short realistic resume, following the tone of `sample_resume_text` in
   conftest.py), `portfolio_url`, and a `repos` list of exactly two entries, each with `name`,
   `description`, `url`, and `readme_text`.
3. Add a `sample_profile_data` fixture to `tests/conftest.py` that opens the JSON file
   (path relative to the fixture file via `Path(__file__).parent`) and returns the parsed
   dict, following the docstring style of the existing fixtures.
4. Write one small unit test that requests `sample_profile_data` and asserts the expected
   top-level keys exist and `len(repos) == 2` — proof the fixture is wired up correctly, not
   just sitting on disk unused.
5. Run `make test-unit` to confirm the new test passes and nothing else breaks.
6. Run `make check` (lint/format/types) to confirm the new JSON and Python files are clean.

### Inputs & outputs
**New fixture file:** `tests/fixtures/sample_profiles/basic_profile.json`

```json
{
  "github_username": "janedoe",
  "resume_filename": "jane_doe_resume.pdf",
  "resume_text": "Jane Doe\nSoftware Engineer\n...",
  "portfolio_url": "https://janedoe.dev",
  "repos": [
    {
      "name": "weather-app",
      "description": "A weather forecasting app built with React and OpenWeatherMap API.",
      "url": "https://github.com/janedoe/weather-app",
      "readme_text": "# Weather App\n..."
    },
    {
      "name": "task-tracker-api",
      "description": "A REST API for managing tasks, built with FastAPI and PostgreSQL.",
      "url": "https://github.com/janedoe/task-tracker-api",
      "readme_text": "# Task Tracker API\n..."
    }
  ]
}
```

**New fixture function (`tests/conftest.py`):**
- Input: none (reads from disk)
- Output: the parsed dict above, available to any test via `sample_profile_data` parameter

**Test I'll write:**
```python
def test_sample_profile_data_has_expected_shape(sample_profile_data):
    """sample_profile_data fixture should load with expected top-level keys."""
    assert sample_profile_data["github_username"]
    assert sample_profile_data["resume_text"]
    assert len(sample_profile_data["repos"]) == 2
```

### Risks & unknowns
1. **I'm guessing the exact JSON shape.** Nothing in the current codebase consumes this file,
   so there's no existing schema to match exactly. I'm basing the shape on the `Profile`
   model's fields plus the "GitHub username, resume, two repos" wording from the issue. If a
   reviewer expects different field names, I'll adjust.
2. **Should repos be modeled after `IngestedSource` fields instead?** I chose `name`/
   `description`/`url`/`readme_text` because that's what a "repo" conceptually needs for RAG
   ingestion, but `IngestedSource` doesn't have a `name` or `description` field — those live
   on GitHub's API response shape, not in our DB model. I'll note this mismatch in my PR
   description rather than guess further.
3. **Decision: include the conftest fixture, not just the JSON file.** The issue text says
   the fixture is needed so "tests that depend on reusable sample profile data" can use it —
   that implies it should be consumable via pytest, not just sit on disk. A JSON file with no
   wiring would be dead weight and likely bounce back in review asking how it's meant to be
   used. Adding `sample_profile_data` to `tests/conftest.py` (a few lines, following the
   existing pattern) plus a test proving it loads keeps this in Tier-1 scope while making the
   restored fixture actually usable.

### Edge cases
- Fixture file is valid JSON but a test imports it expecting a `list` at the top level
  instead of a `dict` — not applicable here since I'm defining the shape myself, but I'll
  keep the fixture function's return type explicit (`dict`) so misuse fails fast with a clear
  type error.
- `resume_text` containing special characters (quotes, newlines) — need to make sure the
  JSON is valid (I'll validate with `python -m json.tool` before committing).
- Two repos is a hard requirement per the issue text — I will not add a third "for realism,"
  to keep the fixture matching exactly what's asked.
