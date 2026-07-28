## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health endpoint already advertises a `safety_events_last_hour` field, but it is currently hardcoded to zero. That means operators cannot tell whether the safety layer has been active recently, even though the app has monitoring hooks for safety events. A successful fix would make the health check report a real count instead of a placeholder so the endpoint reflects the actual safety system state.

**Selection notes:**
This fits the checklist for a first issue because it is small, isolated, and easy to verify. It stays inside the health/monitoring path rather than crossing into auth, ingestion, or the frontend, so the blast radius is low. I also avoided a stale tracker item where the current code already had the requested behavior.

**Branch name:** fix/68-health-check-safety-event-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/RadRebelSam/pathreview/commit/2269a0a9d9eb9ef623ba88b2ced13104fc3124cd

**Reproduction summary:**
I added two unit tests in `tests/unit/test_health_safety_events.py`. The first drives `SafetyMonitor.get_event_count` (via an in-memory Redis stand-in) and confirms it returns real, non-zero counts after events are logged. The second calls the `/health` endpoint with a mocked DB and observes that `safety_events_last_hour` comes back as `0` no matter what — proving the endpoint never consults the monitor and just returns the hardcoded placeholder. While reproducing, I also noticed the endpoint's Redis health check references `settings.redis_host`, which doesn't exist (config only defines `redis_url`) — an adjacent bug I've noted in PLAN.md but scoped out of this fix.

**PLAN.md link:** https://github.com/RadRebelSam/pathreview/blob/fix/68-health-check-safety-event-count/PLAN.md

**Blockers or open questions:**
The main open question is the "last hour" semantics: `get_event_count` ignores its `window_hours` argument and the Redis counters use a 24h TTL, so the count is cumulative rather than a true rolling hour. I need to confirm with the maintainer whether to relabel the field or implement hourly bucketed keys before Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix is implemented and committed (`fix(api): report real safety event count in /health`). All of PLAN.md steps 1–4 are done: `SafetyMonitor.get_total_event_count()` sums `get_event_count()` across `VALID_EVENT_TYPES`; `/health` now builds one Redis client and reports that total in `safety_events_last_hour`; the reproduction test flipped from "always 0" to "reports the aggregated count"; and the file grew from 2 tests to 8, covering the aggregation helper, an empty counter set, unknown/legacy keys, a Redis read failure, and a full Redis outage. Step 3 (the "last hour" window question from Week 8) is resolved as a scoping decision rather than an implementation: true rolling-window counts need bucketed Redis keys, which would change `log_event`'s write path for every safety module — too large for a tier-1 issue — so I documented exactly what the number means in the docstrings and will raise the window semantics as a follow-up in the PR.

One scope change from Week 8: I had planned to leave the broken `settings.redis_host`/`redis_port` lookup alone, but the endpoint could not build a Redis client at all because of it, so there was nothing to hand to `SafetyMonitor`. I switched that to `redis.from_url(settings.redis_url)` and reused the single client for both the redis dependency check and the safety count. It's a 3-line change my fix depends on, and it removes 3 pre-existing mypy errors in the file.

**Next steps:**
Open the draft PR, ask for peer review in Slack, address feedback, then mark it ready for review and fill in Check-in 2.

**Blockers:**
`make` isn't installed on my machine, so I run the Makefile targets directly out of `.venv/Scripts` (`ruff check .`, `black --check .`, `mypy api/ core/ ingestion/ rag/ agent/ safety/`, `pytest tests/unit -m unit`). Same commands, same results — noting it so the check-in matches what I actually ran.

The repo also has substantial pre-existing failures unrelated to #68, which I recorded before touching anything: 182 ruff errors, 52 files black would reformat, 103 mypy errors, and 53 failing unit tests. After my change the failing-test set is byte-for-byte identical (383 passed, up from 377 — the 6 new tests), ruff reports the same 7 findings in the files I touched, the only black deviation left in `safety/monitoring.py` is the pre-existing missing trailing comma, and mypy in `api/routes/health.py` went from 11 errors to 8. So my changes introduce no new failures. I'll document this in the PR description.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/341

**Branch:** `fix/68-health-check-safety-event-count`

**What you built:**
`/health` now reports a real `safety_events_last_hour` instead of a hardcoded `0`. I added `SafetyMonitor.get_total_event_count()`, which sums the existing per-type Redis counters across `VALID_EVENT_TYPES`, and wired the endpoint to it. The count is best-effort — a Redis failure leaves the field at `0` rather than breaking the health check — and I corrected the endpoint's Redis client construction (`settings.redis_host`/`redis_port`, which don't exist on `Settings`) to `redis.from_url(settings.redis_url)`, because without it no client existed to hand to the monitor.

**Tests added or updated:**
`tests/unit/test_health_safety_events.py`, from 2 reproduction tests to 8. They cover the aggregation helper (sums across types, empty counters, unknown/legacy keys ignored, Redis read error degrades to `0`) and the endpoint (reports the real aggregate, reports `0` when nothing has been logged, survives a full Redis outage while still marking the dependency unhealthy).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both in the "no new failures" sense the instructions describe — this repo has documented pre-existing failures (182 ruff, 52 black, 103 mypy, 53 unit tests). After my change: ruff 182 → 182, black 52 → 52, mypy 103 → 100, and the 53 failing tests are the same 53 test IDs with 6 additional passes. The baseline table is in the PR description.

**Draft PR feedback received from:** _pending — draft opened Tue, requesting review in Slack_
