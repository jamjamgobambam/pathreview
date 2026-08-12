## Solution plan

**Issue:** #106 — Shared test fixture for a sample user profile is missing from `tests/fixtures/`
https://github.com/ascherj/pathreview/issues/106

### Understand
The repo is missing the entire `tests/fixtures/` directory. The fixture it should contain,
`tests/fixtures/sample_profiles/basic_profile.json`, doesn't exist and has no history in
`git log --all -- tests/fixtures`, so it was either never committed or removed before this
history began. `scripts/run_evals.py` still has a TODO comment (line 8) pointing at
`tests/fixtures/sample_profiles/` as the source of "benchmark portfolios," and the issue itself
is defined in `scripts/issues_manifest.json` (lines 1612-1620), which names this exact path.

There are no active integration tests currently referencing `basic_profile.json`,
`sample_profiles`, or `fixtures` anywhere in `tests/` — this is a from-scratch restoration, not
a case of matching an existing consumer's expectations exactly.

`tests/conftest.py` currently defines two fixtures, `sample_resume_text()` (lines 6-22) and
`sample_readme_text()` (lines 25-42), both plain inline strings. They set the project's style
for fake data: `sample_resume_text` uses name, role, contact line, experience, education, and
skills sections; `sample_readme_text` uses title, summary, features, and tech stack sections.
`basic_profile.json` should read as a natural extension of that same style, but as a JSON file
with a profile plus two repo objects instead of a single Python string.

Rather than inventing an arbitrary shape, the fixture should mirror what the ingestion/schema
layer actually expects, so it's realistic and immediately useful if a future test wires it up:
- `api/schemas/profile.py`: `ProfileCreate`/`ProfileUpdate` use `github_username` and
  `portfolio_url`; `ProfileResponse` adds `id`, `user_id`, `created_at`, `resume_filename`.
- `core/models/profile.py` (`Profile`, lines 19-56): stored fields are `github_username`,
  `resume_filename`, `resume_text`, `portfolio_url` (lines 30-33).
- `ingestion/pipeline.py`: `ingest_resume()` (55-124) takes resume `content`/`filename` and
  parses `resume_text`; `ingest_readme()` (126-199) takes a repo's README content;
  `ingest_repo_metadata()` (201-260) takes a full repo metadata dict and passes it to
  `RepoAnalyzer.parse()`.
- `ingestion/parsers/resume_parser.py`: `SECTION_HEADERS` (9-23) detects sections like
  `Summary`, `Technical Skills`, `Projects`, `Experience`, `Education` — the fixture's
  `resume_text` should use these headings so it looks like real parser input.
- `ingestion/parsers/repo_analyzer.py`: `RepoAnalyzer.parse()` (29-48) reads GitHub-shaped repo
  fields directly — `stargazers_count`, `forks_count`, `open_issues_count`, `readme_content`,
  `language`, `pushed_at`, plus `name`, `description`, `html_url`. Tech-stack detection (133-184)
  keys off `language` and config files like `package.json`, `requirements.txt`, `Dockerfile`.
- `ingestion/parsers/readme_parser.py`: expects markdown headings (`#`, `##`) in
  `readme_content`.

**Root cause:** The fixture file (and its parent folder) simply doesn't exist in the repo.
This is missing test data, not a code bug — no production code needs to change.

### Map
Files to touch:
- `tests/fixtures/sample_profiles/basic_profile.json` (new file) — the restored fixture, one
  realistic fake portfolio with top-level profile fields, resume content, and two GitHub-style
  repo objects.
- `tests/conftest.py` — add a `sample_profile_data` fixture that loads the JSON file, so tests
  can request it the same way they request `sample_resume_text` today.
- `tests/unit/test_fixtures.py` (new, already stubbed in working tree) — a basic test proving
  the fixture loads, has the expected profile fields, and has exactly two repo entries.

Files inspected but not changed (read for field/shape reference only):
- `scripts/run_evals.py` — only has a TODO comment referencing the path; implementing the eval
  runner itself is out of scope for this issue.
- `scripts/issues_manifest.json` (lines 1612-1620) — issue definition/source of truth for scope.
- `api/schemas/profile.py`, `core/models/profile.py` — field names for the profile portion.
- `ingestion/pipeline.py`, `ingestion/parsers/resume_parser.py`,
  `ingestion/parsers/repo_analyzer.py`, `ingestion/parsers/readme_parser.py` — shape reference
  so the repo objects and text bodies look like real parser input, not arbitrary strings.
- `core/models/ingested_source.py` — confirms there's no `Repo` model; repos are represented as
  ingested-source rows at the DB layer, but the fixture should still mirror GitHub API shape
  since that's what `RepoAnalyzer.parse()` and `ingest_repo_metadata()` actually consume.

### Plan
1. Create the directory `tests/fixtures/sample_profiles/`.
2. Write `basic_profile.json` with:
   - Top-level profile fields: `github_username`, `resume_filename`, `resume_text`,
     `portfolio_url`.
   - `resume_text` written with clear section headings (`Summary`, `Technical Skills`,
     `Experience`, `Education`) so it exercises `ResumeParser._detect_sections()` realistically,
     following the tone of `sample_resume_text` in conftest.py.
   - A `repos` list of exactly two entries, each shaped like GitHub repo metadata so it can
     feed `RepoAnalyzer.parse()` directly: `name`, `description`, `html_url`, `language`,
     `stargazers_count`, `forks_count`, `open_issues_count`, `pushed_at`, and `readme_content`
     (markdown with `#`/`##` headings, following the tone of `sample_readme_text`).
3. Add a `sample_profile_data` fixture to `tests/conftest.py` that opens the JSON file (path
   relative to the fixture file via `Path(__file__).parent`) and returns the parsed dict,
   following the docstring style of the existing fixtures.
4. Fill in `tests/unit/test_fixtures.py` (already present as an empty/stub file) with a test
   that requests `sample_profile_data` and asserts the expected top-level keys exist and
   `len(repos) == 2` — proof the fixture is wired up correctly, not just sitting on disk unused.
5. Run `make test-unit` to confirm the new test passes and nothing else breaks.
6. Run `make check` (lint/format/types) to confirm the new JSON and Python files are clean.

### Inputs & outputs
**New fixture file:** `tests/fixtures/sample_profiles/basic_profile.json`

```json
{
  "github_username": "janedoe",
  "resume_filename": "jane_doe_resume.pdf",
  "resume_text": "Jane Doe\nSoftware Engineer\n\nSummary\n...\n\nTechnical Skills\n...\n\nExperience\n...\n\nEducation\n...",
  "portfolio_url": "https://janedoe.dev",
  "repos": [
    {
      "name": "weather-app",
      "description": "A weather forecasting app built with React and the OpenWeatherMap API.",
      "html_url": "https://github.com/janedoe/weather-app",
      "language": "TypeScript",
      "stargazers_count": 12,
      "forks_count": 3,
      "open_issues_count": 1,
      "pushed_at": "2026-05-10T14:22:00Z",
      "readme_content": "# Weather App\n\n## Features\n...\n\n## Tech Stack\n..."
    },
    {
      "name": "task-tracker-api",
      "description": "A REST API for managing tasks, built with FastAPI and PostgreSQL.",
      "html_url": "https://github.com/janedoe/task-tracker-api",
      "language": "Python",
      "stargazers_count": 5,
      "forks_count": 1,
      "open_issues_count": 0,
      "pushed_at": "2026-04-02T09:10:00Z",
      "readme_content": "# Task Tracker API\n\n## Features\n...\n\n## Tech Stack\n..."
    }
  ]
}
```

**New fixture function (`tests/conftest.py`):**
- Input: none (reads from disk)
- Output: the parsed dict above, available to any test via `sample_profile_data` parameter

**Test I'll write (`tests/unit/test_fixtures.py`):**
```python
def test_sample_profile_data_has_expected_shape(sample_profile_data):
    """sample_profile_data fixture should load with expected top-level keys."""
    assert sample_profile_data["github_username"]
    assert sample_profile_data["resume_text"]
    assert len(sample_profile_data["repos"]) == 2
    for repo in sample_profile_data["repos"]:
        assert repo["name"]
        assert repo["readme_content"]
```

### Risks & unknowns
1. **No existing consumer to match exactly.** I confirmed via search that nothing in `tests/`
   currently references this file, so there's no schema to match byte-for-byte. I'm shaping the
   fixture to mirror what `RepoAnalyzer.parse()` and `ResumeParser` actually read (GitHub-style
   repo metadata, section-headed resume text) rather than an arbitrary shape, so it stays useful
   if/when a real test wires it up.
2. **Repo shape choice: GitHub API-style, not `IngestedSource`-style.** `IngestedSource` doesn't
   have `name`/`description`/`language`/etc. — those live on GitHub's API response shape, which
   is what `ingest_repo_metadata()` and `RepoAnalyzer.parse()` consume before mapping into DB
   rows. I chose to model the fixture after the API/parser input shape since that's the layer
   this fixture would actually feed in a future test.
3. **Decision: include the conftest fixture, not just the JSON file.** The issue implies the
   fixture should be consumable via pytest, not just sit on disk. A JSON file with no wiring
   would be dead weight. Adding `sample_profile_data` to `tests/conftest.py` plus a test proving
   it loads keeps this in scope while making the restored fixture actually usable.

### Edge cases
- Fixture file is valid JSON but a test imports it expecting a `list` at the top level instead
  of a `dict` — not applicable here since I'm defining the shape myself, but I'll keep the
  fixture function's return type explicit (`dict`) so misuse fails fast with a clear type error.
- `resume_text`/`readme_content` containing special characters (quotes, newlines) — need to
  make sure the JSON is valid (I'll validate with `python -m json.tool` before committing).
- Two repos is a hard requirement per the issue text — I will not add a third "for realism," to
  keep the fixture matching exactly what's asked.
- `readme_content` must use real markdown headings (`#`, `##`) rather than plain text, since
  `ReadmeParser._extract_heading_hierarchy()` and `_detect_ci()`/`_detect_tests()` in
  `RepoAnalyzer` key off structural markers — flat text would make the fixture look
  unrealistic if ever run through the real parsers.
