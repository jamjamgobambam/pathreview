## Solution plan

**Issue:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`
— https://github.com/ascherj/pathreview/issues/106

### Understand
The repo has no `tests/fixtures/` directory and no shared sample-profile fixture.
`tests/conftest.py` provides only two text fixtures (`sample_resume_text`,
`sample_readme_text`), so any test needing a full portfolio profile — GitHub
username, resume, and repos together — has to build one inline.

Expected: a reusable `tests/fixtures/sample_profiles/basic_profile.json` holding a
realistic sample portfolio, loadable by tests through a shared pytest fixture.
Actual: the file and directory do not exist.

Reproduction note: the issue says integration tests were "skipped" because of the
missing fixture, but `grep -rn "basic_profile" tests/` and
`grep -rn "sample_profiles" tests/` both return nothing, and `tests/integration/`
contains only `__init__.py`. So there are no skipped tests to un-skip — this is a
missing-asset gap, not a failing test. My fix therefore has to supply both the
fixture and a consumer for it, or it would add a file nothing references.

### Map
Files I expect to touch:
- `tests/fixtures/sample_profiles/basic_profile.json` (new — the fixture data)
- `tests/conftest.py` (new `sample_user_profile` fixture that loads the JSON)
- `tests/unit/test_sample_profile_fixture.py` (new — verifies it loads and matches
  the model's field names)

Files I read to determine the fixture's shape:
- `core/models/profile.py` — authoritative fields: `id`, `user_id`,
  `github_username`, `resume_filename`, `resume_text`, `portfolio_url`,
  `created_at`, `updated_at`. All four content fields are `nullable=True`.
- `api/schemas/profile.py` — `ProfileCreate`/`ProfileUpdate` accept only
  `github_username` (≤255) and `portfolio_url` (≤500). `ProfileResponse` returns
  `resume_filename` but never `resume_text`.
- `core/services/review_service.py::_run_ingestion_pipeline` — repos are not a
  Profile column. GitHub data is written to `IngestedSource.raw_data` as a JSON
  string with `source_type: "github"`, keyed off `profile.github_username`.
- `agent/tools/github_tool.py` — consumes `github_username` + `repo_name`, so each
  repo entry needs a `name` field usable as `repo_name`.

Fixture shape this implies: a `profile` object mirroring the model's columns, plus a
sibling `repos` list of two entries (`name`, `description`, `language`,
`readme_text`, `url`), so the repos can be fed to `github_tool` or serialized into
an `IngestedSource.raw_data` payload without restructuring.

### Risks & unknowns
- **Schema vs. model mismatch.** `resume_text` exists on `Profile` but appears in no
  Pydantic schema. I'm including it in the fixture because parser tests need real
  resume content, but I'll note in the PR that it's model-only, in case a reviewer
  expects the fixture to mirror `ProfileResponse` instead.
- **Repo shape is inferred, not specified.** `IngestedSource.raw_data` is a free-form
  JSON string, so no schema constrains a repo entry. I'm choosing a shape that
  matches what `github_tool.py` consumes; a reviewer may prefer a different one.
- **Pre-existing failures.** The suite reports 53 failures across bias detector,
  resume parser, review service, PII scrubber and others. These are seeded bugs for
  unrelated issues. I must not touch them, and I need to show my change leaves the
  count unchanged.
- **Orphaned-file risk.** Nothing currently references the fixture, so shipping only
  the JSON would add a file nothing uses. Adding a conftest loader plus one test is
  what makes the contribution reviewable.
- **Path resolution.** Loading via a relative path breaks when pytest runs from
  outside the repo root; I'll resolve from `Path(__file__).parent`.

### Edge cases
- All four content fields are nullable, so tests must not assume they're populated.
  The basic fixture fills them all; I'll note that a `minimal_profile.json` covering
  the all-null case is a natural follow-up rather than scope for this PR.
- Field length limits: `github_username` ≤255 and `portfolio_url` ≤500 — the sample
  values must stay well inside both so the fixture can be used to construct a real
  `ProfileCreate` without validation errors.
- `id` and `user_id` are UUID columns, so the fixture must use valid UUID strings,
  not placeholders like `"user-1"`.
- Timestamps must be ISO-8601 strings that survive a JSON round-trip into
  `datetime`.
- Malformed or missing JSON should fail once, in the loader, with a clear message.
- Unicode and multi-line resume text must survive the round-trip.