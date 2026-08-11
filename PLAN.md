## Solution plan

**Issue:** [#106 — Restore deleted `basic_profile.json` fixture](https://github.com/ascherj/pathreview/issues/106)

### Understand

The project expects a sample portfolio JSON file at
`tests/fixtures/sample_profiles/basic_profile.json`, but that file was missing
from the checkout. The issue describes it as baseline portfolio data for tests:
a GitHub username, resume text, and two repositories.

The missing file is the root cause. I searched the current checkout and found
no integration test that loads this fixture, so the exact schema cannot be
proven by running a test. I recovered the original file from a recoverable Git
object, restored it at the required path, and verified that it is valid JSON.

### Map

- `tests/fixtures/sample_profiles/basic_profile.json` — The missing sample
  portfolio fixture. This is the file restored by the fix.
- `scripts/issues_manifest.json` — Contains the issue description and was used
  as evidence for the fixture's intended purpose. It does not need changing.
- `core/models/profile.py` and `core/services/review_service.py` — Related
  profile/review code that shows the application works with GitHub usernames
  and resume text. These files do not load this test fixture.
- `tests/integration/` — The expected location for integration tests, but the
  current checkout contains no test that reads this fixture.
- `PLAN.md` and `JOURNAL.md` — Course documentation for this investigation.

### Plan

1. Confirm the required fixture path and use the issue description plus nearby
   profile/review code to understand its likely purpose.
2. Search for fixture loaders and tests to identify the required key names and
   data types.
3. Restore `basic_profile.json` with a GitHub username, resume text, and two
   repository objects. Use the recovered original when available rather than
   guessing at the exact structure.
4. Validate that the file is valid JSON and run the relevant available tests.
   Document any missing tests or unrelated failures rather than claiming they
   passed.
5. Record the reproduction, evidence, and remaining unknowns in `JOURNAL.md`.

### Inputs & outputs

**Input:** A missing fixture file at
`tests/fixtures/sample_profiles/basic_profile.json`.

**Output:** A valid JSON profile fixture with this structure:

```json
{
  "github_username": "janedoe",
  "resume_text": "# Jane Doe\\n\\n## Skills\\nPython, FastAPI, React, PostgreSQL",
  "repositories": [
    {
      "name": "portfolio-api",
      "url": "https://github.com/janedoe/portfolio-api"
    },
    {
      "name": "task-dashboard",
      "url": "https://github.com/janedoe/task-dashboard"
    }
  ]
}
```

### Risks & unknowns

- The integration tests that originally loaded this fixture are not present in
  the current checkout, so their exact expectations cannot be verified here.
- The production application does not upload or load this fixture directly; it
  is test data rather than a user-facing JSON input.
- The full unit test suite has unrelated existing failures, so a passing suite
  cannot be used as proof that this fixture fix worked.

### Edge cases

- The file path and folder name must exactly be
  `tests/fixtures/sample_profiles/basic_profile.json`.
- The file must contain valid JSON; malformed JSON would prevent a test loader
  from reading it.
- The fixture must include two repository entries, as required by the issue.
- The fixture should contain sample/public data only, not private personal
  information.
