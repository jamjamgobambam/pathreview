# Contribution Journal

## Week 7 — Issue selection

**Issue:** [#155 — Health check references `settings.redis_host`, which does not exist](https://github.com/ascherj/pathreview/issues/155) (Tier 1, `bug`, `api`, `good first issue`)

**Problem summary:**
PathReview's `/health` endpoint is permanently broken: it reports HTTP 503 regardless of actual
system state. The Redis probe reads `settings.redis_host` and `settings.redis_port`, which are
not defined on the `Settings` model — the config exposes Redis as a single `redis_url`. The
resulting `AttributeError` is swallowed by a broad exception handler, so Redis is always marked
unhealthy and the endpoint always escalates to 503. The fix is to construct the client from the
field that exists, via `redis.Redis.from_url(settings.redis_url)`, and to add unit-test coverage
for the endpoint, which currently has none.

**Setup:** Forked [ascherj/pathreview](https://github.com/ascherj/pathreview) to
[salman-khan03/pathreview](https://github.com/salman-khan03/pathreview). Set up a local Python
virtual environment and installed dev dependencies (`pip install -e ".[dev]"`) to run the unit
suite and linters without Docker.

**Branch:** [`fix/155-health-check-redis-config`](https://github.com/salman-khan03/pathreview/tree/fix/155-health-check-redis-config)

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [`685f1ad` — test(api): add regression test reproducing #155 health check crash](https://github.com/salman-khan03/pathreview/commit/685f1ad)

**Reproduction summary:**
Wrote `tests/unit/test_health.py` against the unmodified endpoint and ran it before making any
fix. 3 of 5 tests failed, and the endpoint's own log captured the exact bug:
`redis_health_check_failed  error="'Settings' object has no attribute 'redis_host'"`. This
confirmed the Redis probe never reaches `ping()` and the endpoint always returns 503.

**PLAN.md link:** [PLAN.md](https://github.com/salman-khan03/pathreview/blob/fix/155-health-check-redis-config/PLAN.md)

**Walkthrough video (recommended):** _Not yet recorded._

**Blockers or open questions:**
- The upstream repo's committed `scripts/issues_manifest.json` (130 seed issues) does not match
  the live issue tracker on `ascherj/pathreview` — the manifest's issues are already fixed on
  `main`. Worked from the real, numbered tracker instead (issue #155) once I confirmed this.
- Have not run `make test-integration` (requires Docker services), so the fix is verified at the
  unit level (mocked Redis client) but not against a live Redis instance.
