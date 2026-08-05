## Solution plan

**Issue:** #106 — Shared test fixture for a sample user profile is missing from `tests/fixtures/`

### Understand
The project is meant to keep one shared "sample portfolio" fixture at
`tests/fixtures/sample_profiles/basic_profile.json` that integration tests load
to drive the ingestion pipeline (resume + repositories) end to end. Reading the
repo rather than trusting the issue text turned up something important: the
fixture has **never existed** in git history (`git log --all --full-history --
'tests/fixtures/**'` returns 0 commits), my fork's `origin/main` is identical to
`upstream/main` (0 commits apart either way), and the only real code reference to
the path is a TODO comment in [scripts/run_evals.py:8](scripts/run_evals.py#L8).
There were also **no** integration tests consuming it — `tests/integration/` held
only an empty `__init__.py`.

So the issue's literal wording ("multiple integration tests were skipped because
[the fixture] was deleted") is seeded phrasing from
`scripts/issues_manifest.json`; the true state is *the fixture and its consuming
test are both absent*. The expected behavior after the fix: the fixture exists as
a realistic portfolio (a GitHub username, a resume, and two repositories), and the
integration test that loads it — already added in reproduction commit `f06165a` —
passes instead of erroring with `FileNotFoundError`.

**Root cause:** the fixture file
`tests/fixtures/sample_profiles/basic_profile.json` does not exist, so any code
that loads it fails at read time before the pipeline runs.

### Map
Files I expect to touch:
- `tests/fixtures/sample_profiles/basic_profile.json` — **NEW**, the fix. Must
  contain `github_username`, `resume_text`, `portfolio_url`, and a `repositories`
  list of exactly two entries shaped like the GitHub API dicts the analyzer reads.
- `tests/conftest.py` — **already added** in `f06165a`: `FIXTURES_DIR` helper and
  the `basic_profile` loader fixture (line ~52). No further change expected unless
  the loader needs adjusting.
- `tests/integration/test_sample_profile_fixture.py` — **already added** in
  `f06165a`: the consuming test. It turns green once the fixture exists; I may add
  assertions if the fixture reveals gaps.

Reference only (read, not edited):
- `ingestion/parsers/repo_analyzer.py` — `RepoAnalyzer.parse()` (lines ~50–105)
  defines exactly which repo fields are read: `name`, `description`, `language`,
  `stargazers_count`, `forks_count`, `open_issues_count`, `pushed_at`, `html_url`,
  `readme_content`.
- `ingestion/parsers/resume_parser.py` — `ResumeParser.parse()` /
  `_detect_sections()` decides which resume headers are recognized.
- `core/models/profile.py` — the `Profile` fields (`github_username`,
  `resume_text`, `portfolio_url`) the fixture mirrors.

### Plan
1. Re-read `RepoAnalyzer.parse()` and its helpers (`_detect_ci`, `_detect_tests`,
   `_detect_tech_stack`) in `ingestion/parsers/repo_analyzer.py` to lock the exact
   keys and confirm which fields make `has_ci` / `has_tests` / `tech_stack` come
   out realistic.
2. Re-read `ResumeParser._detect_sections()` to confirm the header strings it
   recognizes, so `resume_text` reliably yields Experience / Skills / Education.
3. Author `tests/fixtures/sample_profiles/basic_profile.json`:
   - `github_username` (e.g. `"janedoe"`), a realistic multi-section `resume_text`,
     and a `portfolio_url`;
   - `repositories`: exactly two, one Python-heavy and one JS/TS, each with the
     GitHub-API fields from step 1, including `readme_content` and an ISO-8601
     `pushed_at`.
4. Run `.venv/bin/python -m pytest tests/integration -m integration -v` and confirm
   the three tests go from error → pass (green).
5. Run `make test-unit` to confirm the additive `conftest.py` change causes no
   regressions in the 428 existing unit tests.
6. Run `make check` (ruff, black, mypy) so the branch is clean for the PR.
7. Open a PR against `upstream/main` using the PR template, linking issue #106.

### Inputs & outputs
**Consumer:** the `basic_profile` fixture in `tests/conftest.py`
(`json.loads(fixture_path.read_text())` → `dict`).

**Contract the fixture must satisfy:**
```json
{
  "github_username": "str",
  "resume_text": "str (multi-section)",
  "portfolio_url": "str",
  "repositories": [ { "...repo..." }, { "...repo..." } ]
}
```
**Each repo (subset `RepoAnalyzer` reads):**
```json
{
  "name": "str", "description": "str", "language": "str",
  "stargazers_count": 0, "forks_count": 0, "open_issues_count": 0,
  "pushed_at": "ISO-8601 str", "html_url": "str", "readme_content": "str"
}
```
**Test behavior** (spec already written in `f06165a`):
- Before fix: all 3 tests **error** (`FileNotFoundError`) at fixture load.
- After fix:
  - `test_fixture_has_required_portfolio_fields` → keys present, exactly 2 repos.
  - `test_repositories_parse_through_repo_analyzer` → `RepoAnalyzer.parse(repo)`
    returns a `ParseResult`; `metadata["repo_name"] == repo["name"]` and
    `metadata["primary_language"] == repo["language"]`.
  - `test_resume_parses_through_resume_parser` → `ResumeParser` detects an
    Experience or Skills section.

### Risks & unknowns
1. **`primary_language` assertion is exact.** `RepoAnalyzer.parse()` does
   `primary_language = repo_data.get("language", "Unknown")`
   ([repo_analyzer.py:58](ingestion/parsers/repo_analyzer.py#L58)), and my test
   asserts it equals `repo["language"]`. If I forget `language` on a repo, parse
   returns `"Unknown"` and the assertion breaks. Mitigation: always set an explicit
   `language` on both repos.
2. **Unconfirmed resume-section matching.** I have not yet read
   `_detect_sections()` closely, so I don't know if it matches `"Experience:"` vs
   `"Work Experience"` etc. Risk: a plausible-looking `resume_text` parses to zero
   detected sections and `test_resume_parses...` fails. Mitigation: model
   `resume_text` on the existing `sample_resume_text` fixture in
   [tests/conftest.py](tests/conftest.py), which is already known to parse.
3. **Scope ambiguity around `run_evals.py`.** Its TODO says "load benchmark
   *portfolios*" (plural), which could imply a directory of profiles rather than a
   single file. I'm scoping to exactly what issue #106 asks (one profile, two
   repos) and treating `run_evals.py` (a stub) as out of scope — noted so it can be
   revisited if a reviewer expects more.
4. **Pre-commit hooks are stricter than `make check`.** The `mypy` hook runs on
   changed files (not just `api/ core/ ...`), which already forced type
   annotations in `f06165a`. JSON isn't type-checked, but any further edit to
   `conftest.py` must keep the `dict[str, Any]` annotations to stay green.

### Edge cases
- **Repo with no `readme_content`:** `RepoAnalyzer` sets `has_readme=False` — valid,
  but at least one repo in the fixture should include `readme_content` so the
  `has_readme=True` path is exercised.
- **Repo missing `language`:** would default to `"Unknown"` and desync the
  assertion — explicitly avoided by always setting it (see Risk 1).
- **Resume with only an Education section:** the test accepts Experience *or*
  Skills, so `resume_text` must contain at least one of those two, not only
  Education.
- **Exactly two repos:** the test asserts `len(repositories) == 2`; a third entry
  would fail — the count is fixed per the issue.
- **Extra GitHub-API keys in a repo dict:** harmless — `RepoAnalyzer` reads via
  `.get()` and ignores unknown fields, so a fuller, more realistic repo object is
  safe.
