## Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on `Settings` ([issue text provided as #155](https://github.com/ascherj/pathreview/issues/155))

### Understand
The root cause is a configuration mismatch in the health route. `api/routes/health.py` builds a Redis client with `settings.redis_host` and `settings.redis_port`, but `core/config.py` only defines `redis_url`. Expected behavior: if PostgreSQL, Redis, and the vector DB are available, `GET /health` should return a healthy response. Actual behavior on Wednesday, July 29, 2026: the Redis probe hits a missing settings attribute, marks Redis unhealthy, and the endpoint raises `HTTPException 503`.

### Map
Files and modules involved:
- `api/routes/health.py`
- `core/config.py`
- `tests/unit/test_health.py`
- `JOURNAL.md`
- `PLAN.md`

Expected code-touch files for the fix:
- `api/routes/health.py`
- `tests/unit/test_health.py`

Possible supporting file if the chosen fix needs config changes:
- `core/config.py`

### Plan
1. Add or update a regression test that describes the intended healthy path when Redis is configured through the existing settings model.
2. Replace the Redis probe in `api/routes/health.py` so it uses the real configuration path from `Settings` instead of missing `redis_host` and `redis_port` fields.
3. Verify the endpoint still reports PostgreSQL and vector DB status the same way, and only returns `503` for actual dependency failures.
4. Run targeted backend tests and a local `/health` check against the dev stack to confirm the fix.

### Inputs & outputs
Inputs:
- `settings.redis_url`
- Database dependency from `get_db`
- Redis connectivity check (`ping`)
- Existing vector DB URL setting

Outputs:
- A correct `/health` response payload
- `200 OK` when dependencies are healthy
- `503 Service Unavailable` only when a real dependency check fails

### Risks & unknowns
- I need to confirm whether the preferred fix is `redis.from_url(...)` or parsing `redis_url` into host and port values before constructing the client.
- The local notes currently disagree on issue number: Week 7 references `#156`, but the issue text provided this week says `#155`.
- There is no existing health-route test coverage, so I need to be careful not to lock the test too tightly to one implementation detail.

### Edge cases
- Missing or malformed `redis_url`
- Redis URLs that include authentication, non-default ports, or database indices
- Redis genuinely being down versus the configuration object being wrong
- `vector_db_url` being unset, which currently reports `unavailable` rather than failing the whole endpoint
