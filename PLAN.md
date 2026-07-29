## Solution plan
**Issue:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Issue link:** [Shared test fixture for a sample user profile is missing from tests/fixtures/](https://github.com/ascherj/pathreview/issues/106)

### Understand
The root cause is that integration tests expect a shared fixture at `tests/fixtures/sample_profiles/basic_profile.json`, but that file was deleted. Expected behavior is that tests can load a realistic sample portfolio from that path. Actual behavior is that those tests are skipped or cannot run because the fixture is missing.

### Map
Expected file to touch:
- `tests/fixtures/sample_profiles/basic_profile.json`
  - This missing JSON fixture is the actual issue target. It should contain one realistic fake portfolio with top-level profile fields, resume content, and two repository objects.
  - The issue specifically names this path in `scripts/issues_manifest.json` lines 1612-1620.

Files to inspect before editing:
- `tests/conftest.py`
  - Lines 6-22 define `sample_resume_text()`, which shows the project’s existing style for fake resume data: name, role, contact line, experience, education, and skills.
  - Lines 25-42 define `sample_readme_text()`, which shows the existing style for fake README content: title, summary, features, and tech stack.
  - These fixtures are useful examples for making `basic_profile.json` consistent with the rest of the test data.

- integration tests that reference `basic_profile.json`
  - I searched for `basic_profile`, `sample_profiles`, and `fixtures`.
  - There are no active integration test files currently referencing `basic_profile.json` in `tests/`.
  - The relevant reference is in `scripts/run_evals.py` line 8, where the TODO says benchmark portfolios should load from `tests/fixtures/sample_profiles/`.
  - The issue definition itself is in `scripts/issues_manifest.json` lines 1612-1620.

- `api/schemas/profile.py`
  - `ProfileCreate` on lines 7-9 accepts `github_username` and `portfolio_url`, so the fixture should include those.
  - `ProfileUpdate` on lines 12-14 uses the same editable profile fields.
  - `ProfileResponse` on lines 17-23 returns `id`, `user_id`, `github_username`, `portfolio_url`, `created_at`, and `resume_filename`. The fixture probably does not need database IDs unless a test expects them, but it should include `resume_filename` if it represents a complete profile.

- `core/models/profile.py`
  - `Profile` is defined on lines 19-56.
  - Lines 30-33 show the stored profile fields that matter for the fixture: `github_username`, `resume_filename`, `resume_text`, and `portfolio_url`.
  - Lines 42-48 show relationships to users, ingested sources, and reviews, but this issue should not require changing those models.

- `ingestion/pipeline.py`
  - `IngestionPipeline.__init__()` lines 30-53 wires together `ResumeParser`, `ReadmeParser`, and `RepoAnalyzer`.
  - `ingest_resume()` lines 55-124 accepts `profile_id`, resume `content`, and `filename`; it parses resume text on line 88 and attaches filename/source metadata on lines 92-98. This supports including `resume_text` and `resume_filename` in the fixture.
  - `ingest_readme()` lines 126-199 accepts `repo_name` and README content; it parses README content on line 159. This supports including `readme_content` inside each repo object.
  - `ingest_repo_metadata()` lines 201-260 accepts a repository metadata dictionary; it reads `repo_data.get("name")` on line 216 and passes the whole repo object into `RepoAnalyzer.parse()` on line 233. This supports making each repo object look like GitHub metadata.

- `ingestion/parsers/resume_parser.py`
  - `SECTION_HEADERS` lines 9-23 list sections the parser detects, including `experience`, `education`, `skills`, `projects`, `summary`, and `technical skills`.
  - `ResumeParser.parse()` lines 29-47 accepts either bytes or string content.
  - `_parse_markdown()` lines 80-97 handles string resumes and returns metadata including detected sections.
  - `_detect_sections()` lines 127-146 detects section headings, so the fixture resume should use clear headings like `Summary`, `Technical Skills`, `Projects`, `Experience`, and `Education`.

- `ingestion/parsers/repo_analyzer.py`
  - `RepoAnalyzer.parse()` lines 29-48 accepts a dict, JSON string, or JSON bytes.
  - Lines 50-68 read repo fields: `stargazers_count`, `forks_count`, `open_issues_count`, `readme_content`, `language`, and `pushed_at`.
  - Lines 73-86 build the searchable repo summary using `name`, `description`, `language`, metrics, tech stack, and `html_url`.
  - Lines 90-103 return metadata including `repo_name`, `repo_url`, `primary_language`, test/README/CI booleans, and tech stack.
  - `_detect_ci()` lines 111-119 checks `file_structure` for `.github/workflows` and other CI config.
  - `_detect_tests()` lines 121-131 checks `file_structure` for test folders/files.
  - `_detect_tech_stack()` lines 133-184 checks `language`, file extensions, and config files like `package.json`, `requirements.txt`, `dockerfile`, `tsconfig.json`, and `vite.config`.

- `ingestion/parsers/readme_parser.py`
  - `ReadmeParser.parse()` lines 9-45 accepts README markdown as string or bytes.
  - Lines 27-39 extract README metadata such as heading count, word count, code blocks, and badges.
  - `_extract_heading_hierarchy()` lines 47-64 detects markdown headings, so each repo’s `readme_content` should include normal markdown headings like `# Project Name`, `## Tech Stack`, and `## Features`.


### Plan
1. Search the test suite for references to `basic_profile.json`, `sample_profiles`, or profile fixture loading.
2. Identify the JSON structure expected by the tests or nearby schemas.
3. Recreate `tests/fixtures/sample_profiles/basic_profile.json` with realistic sample data:
   - GitHub username
   - resume information or resume text
   - two repository entries
4. Keep the fixture deterministic and free of real personal data.
5. Run the affected tests, or at least run fixture-loading tests if the full integration suite needs external services.

### Inputs & outputs
Input: a missing fixture path expected by integration tests.
Output: a restored JSON fixture containing a realistic but fake sample portfolio that tests can load consistently.


### Risks & unknowns
The main risk is choosing a JSON shape that looks reasonable but does not match what the skipped integration tests expect. Another unknown is whether the integration tests require Docker services, API keys, or seeded database state to run fully.

Since no active integration test currently references the fixture, the exact consumer is partially unknown. The best move is to align the JSON with the schema/model/parser expectations above.

### Edge cases
What inputs or states should your fix handle gracefully?
The fixture should avoid real PII, should include enough resume and repo detail for parser/retrieval tests, and should use stable fake data so tests do not depend on live GitHub responses.

I will consider missing or incomplete data when shaping the fixture, but I do not plan to add new app behavior for incomplete profiles unless the existing tests require it. Since this issue is about a deleted fixture, the fix should stay focused on restoring complete sample data rather than changing parser or validation logic.