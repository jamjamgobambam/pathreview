## Solution plan

**Issue:** [#106 — Shared test fixture for a sample user profile is missing from `tests/fixtures/`](https://github.com/ascherj/pathreview/issues/106)

---

### Understand

**Root cause:** The directory `tests/fixtures/sample_profiles/` and the file
`basic_profile.json` inside it were deleted from the repository. Nothing else
in the codebase was changed — the fixture itself is the only missing piece.

**Expected behaviour:** `basic_profile.json` exists and contains a realistic
sample portfolio (a GitHub username, a text resume, and data for two
repositories). The integration tests and the eval runner (`scripts/run_evals.py`)
can load the file and use it as benchmark input.

**Actual behaviour:** The directory does not exist. Every test that depends on
the file is decorated with `pytest.mark.skipif(not FIXTURE_PATH.exists(), ...)`,
so all 11 tests in `tests/integration/test_sample_profile_fixture.py` silently
skip instead of executing.

---

### Map

Files involved:

| File | Role |
|------|------|
| `tests/fixtures/sample_profiles/basic_profile.json` | **The file to create** — the missing fixture |
| `tests/integration/test_sample_profile_fixture.py` | Integration tests that skip without the fixture (added in reproduction commit) |
| `scripts/run_evals.py` | References `tests/fixtures/sample_profiles/` as the benchmark portfolio directory |
| `agent/orchestrator.py` | Defines the `profile_data` dict contract the fixture must satisfy |

No other files need to change.

---

### Plan

1. **Create the fixture directory.**
   Make `tests/fixtures/sample_profiles/` (the directory itself does not exist
   in the repo).

2. **Determine the required JSON schema.**
   Inspect `agent/orchestrator.py → Orchestrator._build_plan()` to confirm
   which keys are read from `profile_data`:
   - `github_username` (string)
   - `resume_text` (string)
   - `projects` (list of dicts, each with `github_repo`, `name`, `description`,
     `readme_content`)
   - Optional: `files`, `repo_metadata`

3. **Write `basic_profile.json` with valid sample data.**
   The file must contain:
   - A realistic GitHub username (e.g. `"janedoe"`)
   - A multi-section resume text (Experience, Education, Skills)
   - Exactly two repository entries, each with all required fields

4. **Verify the integration tests un-skip and pass.**
   Run `pytest tests/integration/test_sample_profile_fixture.py -v` and confirm
   all 11 tests that were previously skipping now execute and pass.

5. **Verify the eval runner accepts the fixture.**
   Run `python scripts/run_evals.py` and confirm it no longer fails to find
   the benchmark portfolios directory.

---

### Inputs & outputs

**Input:** None — `basic_profile.json` is a static file with no runtime inputs.

**Output / what changes:**
- A new file at `tests/fixtures/sample_profiles/basic_profile.json` containing
  a JSON object that satisfies the `Orchestrator._build_plan` input contract.
- All 11 skipped integration tests in
  `tests/integration/test_sample_profile_fixture.py` begin executing and pass.
- `scripts/run_evals.py` can load benchmark portfolios without error.

**Signatures / behaviour that change:**
- No function or class signatures change.
- `FIXTURE_PATH.exists()` in the test module evaluates to `True` instead of
  `False`, causing `pytestmark.skipif` to stop skipping.

---

### Risks & unknowns

- **Unknown: exact schema version expected by eval runner.**
  `scripts/run_evals.py` references the directory in a comment but the load
  logic is marked `TODO`. Risk: if the eval runner is implemented before this
  PR merges, its expected schema may differ from the orchestrator schema I
  used. Mitigation: keep keys consistent with `Orchestrator._build_plan` and
  add `readme_content` per project since the orchestrator's `readme_scorer`
  step needs it.

- **Unknown: whether optional fields (`files`, `repo_metadata`) are required
  by any downstream test.**
  The current integration tests do not assert those keys. Risk: a future test
  added against this fixture might fail if those keys are absent. Mitigation:
  include `repo_metadata` as an empty dict `{}` so the orchestrator's
  skill-extractor step receives a valid (empty) value.

- **Risk: fixture staleness as the schema evolves.**
  If `Orchestrator._build_plan` gains new required keys in a later PR, the
  fixture will silently become incomplete. Mitigation: the integration tests
  validate each key explicitly, so any schema drift will surface as a test
  failure rather than a silent skip.

---

### Edge cases

1. **`github_username` is present but `projects` is an empty list.**
   The orchestrator skips the `github_tool` step cleanly (the `for project in
   profile_data.get("projects", [])` loop simply doesn't execute). The fixture
   must have two projects to satisfy `test_fixture_has_exactly_two_repositories`,
   but this edge case confirms the orchestrator won't crash on an empty list.

2. **`resume_text` is an empty string or whitespace-only.**
   `Orchestrator._build_plan` gates the `skill_extractor` step on
   `profile_data.get("resume_text")`, which is falsy for an empty string. The
   integration test `test_resume_text_feeds_skill_extractor_step` would fail,
   catching this regression before merge.

3. **`basic_profile.json` is valid JSON but missing a required top-level key.**
   The `TestBasicProfileFixtureStructure` tests assert each required key
   individually, so a partially-complete fixture fails fast with a clear error
   message rather than an obscure `KeyError` deep in the pipeline.

4. **The fixture file contains Unicode characters in resume or README text.**
   `open(FIXTURE_PATH, encoding="utf-8")` is used in the test fixture loader,
   so non-ASCII characters (accented names, em-dashes) are handled correctly
   as long as the JSON file itself is saved as UTF-8.
