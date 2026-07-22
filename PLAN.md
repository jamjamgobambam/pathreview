## Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on Settings — [#155](https://github.com/ascherj/pathreview/issues/155)

### Understand
The `/health` endpoint's Redis probe constructs a `redis.Redis` client using
`settings.redis_host` and `settings.redis_port`. Neither field exists on the
`Settings` model — only a combined `redis_url` field does. This causes an
`AttributeError` every time the Redis check runs, which the surrounding
`except Exception` block silently catches and reports as `"unhealthy"`.
Expected behavior: the health check should correctly report Redis's real
status. Actual behavior: it always reports "unhealthy," regardless of whether
Redis is actually reachable, because the code never even gets far enough to
attempt a real connection.

### Map
- `api/routes/health.py` — contains the buggy Redis client construction; the
  main file to fix
- `core/config.py` — defines the `Settings` model and the existing
  `redis_url` field; read-only reference, no changes needed here
- `tests/unit/test_health.py` — new test file to add coverage (didn't exist
  before this issue)

### Plan
1. Reproduce the bug locally by calling `GET /health` and confirming the
   `AttributeError` / "unhealthy" Redis status.
2. Replace the manual `host=`/`port=` client construction with
   `redis.Redis.from_url(settings.redis_url, decode_responses=True)`.
3. Add unit tests: one confirming Redis reports "healthy" via a mocked
   successful connection, one confirming a genuine connection failure is
   still correctly reported as "unhealthy" (so we don't just paper over
   errors).
4. Run `ruff`, `black`, and `mypy` locally to satisfy the project's
   pre-commit hooks, fixing any type-annotation gaps introduced by touching
   this file.
5. Commit with a Conventional Commits message referencing the issue, and
   push for review.

### Inputs & outputs
**Input:** the existing `settings.redis_url` connection string
(`redis://localhost:6379/0` by default).
**Output:** the `/health` endpoint correctly reports `"redis": "healthy"`
when Redis is reachable, and `"redis": "unhealthy"` only on a genuine
connection failure — not on every request due to a config bug.

### Risks & unknowns
- `redis.Redis.from_url()` needs to correctly parse the DB index (`/0`) at
  the end of the URL — confirmed this works via manual testing against the
  local Docker Redis container.
- Touching `health.py` surfaced unrelated pre-existing type issues that
  `mypy` flagged once `db` was properly typed (e.g. the raw `"SELECT 1"`
  string not wrapped in `text()`, which is really issue #154). Risk of
  scope creep — mitigated by using a scoped `# type: ignore` comment rather
  than fixing that unrelated bug here.
- Since #155 was a heavily-claimed "good first issue," there was a risk of
  duplicate/conflicting PRs already open against the same lines — checked
  the issue's linked PRs before starting to avoid wasted work.

### Edge cases
- Redis genuinely unreachable (e.g. container stopped) — should still
  report `"unhealthy"` and return a 503, not silently succeed.
- Malformed or missing `redis_url` in `.env` — `from_url()` will raise on
  a clearly invalid string, which is caught by the existing `except
  Exception` block and correctly reported as unhealthy.
- Redis reachable but wrong DB index — out of scope for this fix, since
  the URL's DB index is inherited as-is from settings.