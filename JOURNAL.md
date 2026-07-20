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

### Note on issue selection

I first surveyed the tier-1 bug issues in `scripts/issues_manifest.json`
(A-01, B-01, B-02, C-01, D-01, E-01, E-02, E-03, F-02) and found they are
**already implemented/handled on `main`** — e.g. the resume parser has no
`sections['experience'][0]` access, `github_tool` null-guards the description,
`GET /reviews/{id}` already returns 404. D-08 is genuinely unfinished: the
`safety_events_last_hour` field is present but stubbed to `0`, which makes it a
real, reproducible gap to close.
