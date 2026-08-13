## Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on Settings — https://github.com/ascherj/pathreview/issues/155

### Understand
Root cause, and expected vs actual behavior. The
probe reads attributes Settings never defines, Python raises AttributeError at
call time rather than startup, and the broad except turns a code bug into a
false "Redis is down" report. Expected: /health reports Redis healthy when Redis
is reachable. Actual: always unhealthy.

### Map

- `api/routes/health.py` — the Redis probe inside `health_check()` builds a client from `settings.redis_host` and `settings.redis_port`. The `except Exception` closing that block swallows the resulting `AttributeError`.
- `core/config.py` — line 12 defines `redis_url: str = Field(default="redis://localhost:6379/0")`. No `redis_host` or `redis_port` field exists.
- `tests/unit/test_health.py` — new file. No health test existed in `tests/unit/`.
- `tests/conftest.py` — inspected for reusable fixtures. Only sample-text fixtures exist; no client or DB fixture, so tests call `health_check()` directly with a mocked session.

### Plan

1. Replace the `redis.Redis(host=..., port=..., db=0, ...)` construction with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`.
2. Verify manually: `make run`, then `curl http://localhost:8000/health`, and confirm the `redis` key changes from `unhealthy` to `healthy`.
3. Add `tests/unit/test_health.py` covering the probe, matching the class/fixture/docstring patterns in `tests/unit/test_review_service.py`.
4. Capture `make test-unit` and `make check` baselines before changing anything, and compare after, to confirm no new failures.
5. Open a PR against `ascherj/pathreview:main` documenting the before/after and any pre-existing failures.

### Inputs & outputs

[What the probe takes in (settings.redis_url) and what changes (the
`dependencies.redis` value in the response, and the overall status/HTTP code).]

### Risks & unknowns

[Real candidates you actually hit: `from_url` parses the db index out of the URL
so dropping `db=0` must not change behavior; the broad `except Exception` still
masks future bugs and narrowing it is a scope decision; the repo has pre-existing
`make check` and `make test-unit` failures that make "passing" ambiguous;
postgres also reports unhealthy from an unrelated SQLAlchemy 2.0 cause.]

### Edge cases

[What the fix should handle: Redis genuinely down (should still report unhealthy,
not crash); a malformed or missing redis_url; the default value when no env var
is set.]
