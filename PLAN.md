## Solution plan

**Issue:** [#106 — Shared test fixture for a sample user profile is missing from `tests/fixtures/`](https://github.com/ascherj/pathreview/issues/106)

### Understand

The issue states that "multiple integration tests were skipped" because they
depend on `tests/fixtures/sample_profiles/basic_profile.json`, "which was
deleted," and asks to restore it with a realistic portfolio (GitHub username,
resume, two repos).

Investigation showed the premise is a seeded/synthetic practice issue rather
than a real regression:

- `tests/fixtures/` did not exist anywhere in the working tree.
- The fixture path appears in **no** commit in history: both
  `git log --all --diff-filter=D -- 'tests/fixtures/*'` and a full-history
  `git grep` for `basic_profile` / `sample_profiles` returned nothing except
  documentation/comment references (`JOURNAL.md`, `scripts/issues_manifest.json`
  entry `G-01`, and a `# TODO` comment in `scripts/run_evals.py:8`).
- `tests/integration/` contained only an empty `__init__.py` — there were **no
  integration tests at all**, so nothing was actually being skipped. Running
  `pytest tests/ -rs` reported zero skips.

Conclusion: this is **net-new authoring**, not restoration. The fixture never
existed, so the "expected shape" must be derived from the current models, not
recovered from git.

Prior art: PR #134 (open, unmerged, author `sravanibhamidipaty`) attempted a
**different** approach — it added a Python `sample_user_profile` fixture to
`tests/conftest.py` plus a self-validating test, and never created the JSON
file the issue names. That is a scope mismatch with the literal issue text and
is likely why it stalled. This plan deliberately delivers the JSON fixture the
issue actually asks for.

### Map

Relevant files and what each contributes to the fixture's shape:

- `core/models/profile.py` — `Profile` (SQLAlchemy). Authoritative columns:
  `github_username` (`String(255)`, nullable), `resume_filename`
  (`String(255)`), `resume_text` (`Text`), `portfolio_url` (`String(500)`),
  plus `id`/`user_id`/timestamps. Relationships: `ingested_sources`
  (one-to-many), `reviews`, `user`.
- `core/models/ingested_source.py` — `IngestedSource`. A repo is one row with
  `source_type="repo"` (enum documented as `resume|readme|repo|web`),
  `source_url`, `filename`, `content_hash`, `chunk_count`. **The `Profile` row
  has no "repos" column — repos are child `IngestedSource` rows.**
- `core/models/__init__.py` — imports all four models (`User`, `Profile`,
  `IngestedSource`, `Review`); importing from the package (not the submodule)
  registers the full mapper registry so the string-based `User` relationship on
  `Profile` resolves.
- `scripts/seed_db.py` — tone reference for `github_username` /
  `portfolio_url` values; notably sets **no** `resume_text` and **no**
  `IngestedSource` repos, so a "resume + two repos" profile is new ground.
- `tests/conftest.py` — `sample_resume_text` fixture; style reference for the
  resume prose (Jane Doe / `github.com/janedoe`).
- `.github/workflows/ci.yml:79` — CI runs `pytest tests/integration -v` by
  path (no `-m` filter), so a test placed there runs in CI.
- `Makefile` (`test-integration`) — runs `pytest tests/integration -m integration`,
  so the `@pytest.mark.integration` marker keeps it runnable via `make` too.

### Plan

1. **Create the fixture** `tests/fixtures/sample_profiles/basic_profile.json`
   with only real model columns: top-level `github_username`,
   `resume_filename`, `resume_text`, `portfolio_url` (Profile), and a `repos`
   array of two objects each with `source_type`, `source_url`, `filename`
   (IngestedSource). No invented fields. Values follow `seed_db.py` tone and
   `conftest.py` resume style for coherence (`janedoe` / `janedoe.dev` /
   Jane Doe resume; repos `weather-app` and `portfolio-tracker`).
2. **Create the integration test**
   `tests/integration/test_profile_fixture_loading.py` that (a) loads the JSON
   from disk via a `Path`-based fixture, (b) constructs a real `Profile` and
   two real `IngestedSource` objects from it, and (c) asserts the relationship
   graph: `len(profile.ingested_sources) == 2`, every source is
   `source_type="repo"`, each `source.profile is profile`, and the two
   `source_url`s match. Import via `from core.models import ...` so the mapper
   registry is fully configured. Mark `@pytest.mark.integration`.
3. **Verify locally** — run the new test file (`pytest
   tests/integration/test_profile_fixture_loading.py -v`), then the full suite
   (`pytest tests/`) to confirm no regression, and the pre-commit hooks
   (ruff/black/mypy) pass.
4. **Commit and push** on branch `fix/106-restore-sample-profile-fixture`, then
   update `JOURNAL.md` (Week 8) and this `PLAN.md`.

### Inputs & outputs

**Inputs**
- `tests/fixtures/sample_profiles/basic_profile.json` — read at test time by
  `basic_profile_data` (JSON → `dict[str, Any]`).

**Outputs (produced/asserted by the test)**
- A transient `Profile` ORM object with `github_username == "janedoe"`,
  populated `resume_filename` / `resume_text` (contains "Jane Doe"), and an
  `https://` `portfolio_url`.
- Two transient `IngestedSource` objects auto-linked into
  `profile.ingested_sources` via `back_populates`, each `source_type="repo"`
  with URLs `https://github.com/janedoe/weather-app` and
  `.../portfolio-tracker`.
- No files written, no DB rows persisted — the test is pure in-memory object
  graph construction.

### Risks & unknowns

- **Mapper-registry resolution.** `Profile`'s `user` relationship targets
  `"User"` by string. Importing only `core.models.profile` can leave `User`
  unregistered and fail mapper configuration on first attribute access.
  Mitigation: import from `core.models` (the package `__init__` imports all
  four models). Verified by the passing test.
- **`back_populates` on unsaved objects.** The design relies on SQLAlchemy
  populating `profile.ingested_sources` from setting `IngestedSource(profile=...)`
  without a session/flush. This is real SQLAlchemy behavior but is the load-
  bearing assumption of the whole test — confirmed green in
  `tests/integration/test_profile_fixture_loading.py`.
- **`integration` marker vs. Docker.** `pyproject.toml` documents the marker as
  "require Docker services." This test needs none. Risk: a future CI change
  that deselects with `-m "not integration"` would hide it. Current CI
  (`.github/workflows/ci.yml:79`) selects by path, so it runs today; noted for
  reviewers.
- **Postgres-specific column types.** `Profile.id` uses
  `sqlalchemy.dialects.postgresql.UUID`. The test intentionally avoids any real
  DB engine, so this never has to bind to a dialect; a future "persist and
  query back" test would need a real Postgres (Docker) and is out of scope.
- **Import-time engine creation.** `core/database.py` builds an async engine at
  import from `settings.database_url`. `create_async_engine` does not open a
  connection, so import succeeds offline; confirmed by the test collecting and
  running with no DB available.

### Edge cases

- **Fixture file missing / renamed.** `test_fixture_file_exists` asserts
  `FIXTURE_PATH.exists()` with the path in the message, so a future deletion
  fails loudly at that test rather than with an opaque `FileNotFoundError`
  buried in another assertion — directly guarding against the exact scenario
  #106 describes.
- **Wrong repo count.** The issue specifies exactly two repos;
  `test_repos_map_to_two_ingested_sources` asserts `len(...) == 2`, so adding
  or dropping a repo in the JSON breaks the test deliberately.
- **`source_type` typo.** Every source is asserted `== "repo"`, catching a
  fixture edit that sets e.g. `"readme"` or a typo like `"repos"`.
- **Broken back-link.** `src.profile is profile` (identity, not equality)
  catches a regression where the relationship is configured such that the child
  no longer references its parent.
- **Encoding.** The resume text is opened with `encoding="utf-8"`, so the
  fixture stays portable if non-ASCII content is added later (relevant on the
  Windows dev environment where the default encoding is not UTF-8).
