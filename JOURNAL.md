# JOURNAL

PathReview contribution. Issue: **D-08 — Add a safety event count to the health
check endpoint.** Working branch: `feat/d08-health-safety-event-count`.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/eokoned1/pathreview/commit/9fa2929

**Reproduction summary:**
Added a failing unit test,
`tests/unit/test_health_safety_events.py::test_health_reports_recorded_safety_events`.
It records 3 safety events through `SafetyMonitor` (proving the count data is
available via `get_event_count`), then calls the real `/health` endpoint and
asserts the reported count matches. It fails with
`AssertionError: health endpoint reports 0 safety events, but 3 were recorded`
(`assert 0 == 3`) — confirming `api/routes/health.py` hardcodes
`safety_events_last_hour = 0` and never queries `SafetyMonitor`.

**PLAN.md link:** https://github.com/eokoned1/pathreview/blob/feat/d08-health-safety-event-count/PLAN.md

**Walkthrough video (recommended):** <!-- optional Loom link -->

**Blockers or open questions:**
- The Redis block in `health.py` reads `settings.redis_host` / `settings.redis_port`,
  but `core/config.py` only defines `redis_url` — so Redis access there already
  raises `AttributeError`. My fix needs a working Redis client (parse `redis_url`
  or reuse a shared one) or the count will silently stay `0`. Want to confirm the
  intended way to get a client.
- "Last hour" is currently a misnomer: `get_event_count` doesn't enforce
  `window_hours` and relies on a 24h key expiry. Deciding whether to implement
  true hourly bucketing (touches `log_event` and every event producer) or
  document the limitation and file a follow-up.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Established a pre-change baseline of the repo (`make test-unit`: 53 pre-existing
unrelated failures; `ruff`: 182 errors; `black`: 53 files; `mypy`: bails early on
stub/numpy issues). Implemented the two core sub-tasks from PLAN.md: added
`SafetyMonitor.get_total_event_count()` (sums per-type counts across
`VALID_EVENT_TYPES`, degrading to 0 on Redis errors) and wired `/health` to it
via `redis.from_url(settings.redis_url)` instead of the hardcoded `0`.

**Next steps:**
Finish the test coverage (endpoint wiring + no-events + Redis-unavailable), re-run
the suite to confirm no new failures, and open a draft PR for feedback.

**Blockers:**
Decided to keep the pre-existing `settings.redis_host` gap in `health.py` out of
scope (it affects the Redis dependency line, not the safety count) and document
it in the PR instead of expanding the change.

---

### Check-in 2 (end of week)

**PR link:** <!-- PR_URL_PLACEHOLDER -->

**Branch:** `feat/d08-health-safety-event-count`

**What you built:**
`/health` now reports the real `safety_events_last_hour` instead of a hardcoded
`0`. A new `SafetyMonitor.get_total_event_count()` sums recorded safety events
across all event types from Redis, and the endpoint calls it inside a guarded
block so a Redis outage degrades the count to `0` rather than failing the health
check.

**Tests added or updated:**
`tests/unit/test_health_safety_events.py` — converted the Week 8 reproduction
test to assert the corrected behavior, and added coverage for
`get_total_event_count` (sum across types; zero when empty) and the endpoint
wiring (reports the recorded count; zero with no events; degrades to zero when
Redis is unavailable). All 5 pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

*("Passes" per the documented pre-existing-failures guidance: my change
introduces **no new** failures. Verified by diffing the failing-test set before
and after — unit failures went 54 → 53 (my reproduction test now passes, zero
new failures); `mypy` error count on the touched files is unchanged (14 → 14);
`ruff`/`black` on my added code are clean, and the remaining warnings on the
touched files — unsorted imports, unused `timedelta`/`timestamp`, `Depends`
default, and a `black` trailing-comma on `VALID_EVENT_TYPES` — are all
pre-existing, not introduced by this change.)*

**Draft PR feedback received from:** none yet — draft opened for peer/mentor review

---

### Note on issue selection

I first surveyed the tier-1 bug issues in `scripts/issues_manifest.json`
(A-01, B-01, B-02, C-01, D-01, E-01, E-02, E-03, F-02) and found they are
**already implemented/handled on `main`** — e.g. the resume parser has no
`sections['experience'][0]` access, `github_tool` null-guards the description,
`GET /reviews/{id}` already returns 404. D-08 is genuinely unfinished: the
`safety_events_last_hour` field is present but stubbed to `0`, which makes it a
real, reproducible gap to close.
