## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` API endpoint currently reports basic service status but has no visibility into safety system activity. Operators who want to check on safety monitoring have to leave the health check and go query a separate dashboard, which is slow and easy to skip. This issue asks for a new `safety_events_last_hour` field to be added to the health check response, pulling that count from the safety monitoring logic. The fix mainly touches `api/routes/health.py` (the endpoint itself) and `safety/monitoring.py` (where safety event data is tracked). Once done, anyone hitting `/health` will immediately see recent safety event activity alongside normal service status.

**Branch name:** fix/68-health-check-safety-event-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Reproduction — Issue #68

Ran the following to confirm the bug:

    .venv/bin/python -c "
    import redis
    from safety.monitoring import SafetyMonitor

    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    monitor = SafetyMonitor(r)
    monitor.log_event('content_filtered', {'reason': 'manual repro test'})
    print('Stored count in Redis:', monitor.get_event_count('content_filtered'))
    "

Output: `Stored count in Redis: 2`

Then immediately: `curl http://localhost:8000/health`

Output: `"safety_events_last_hour":0`

**Confirmed:** a real safety event exists in Redis (count = 2), but `/health` still
reports `0`. This confirms `safety_events_last_hour` in `api/routes/health.py` is
hardcoded and never wired up to `SafetyMonitor`.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Ahmadkarim7/pathreview/commit/ff9e3af

**Reproduction summary:**
Logged a safety event directly via SafetyMonitor.log_event(), confirmed Redis stored
the count (2), then immediately hit /health and found safety_events_last_hour still
returned 0 — proving the field is hardcoded in api/routes/health.py and was never
wired up to SafetyMonitor.

**PLAN.md link:** https://github.com/Ahmadkarim7/pathreview/blob/fix/68-health-check-safety-event-count/PLAN.md

**Walkthrough video (recommended):** (skipped)

**Blockers or open questions:**
Confirming with mentor whether another contributor (RadRebelSam) already has this
issue in progress, since they commented on #68 with a nearly identical branch name.
Also noted in PLAN.md: a fully accurate hourly count needs a bigger Redis storage
change (sorted sets vs. flat counters) than the issue's 2–4hr estimate suggests.
Unrelated to this issue but observed during testing: /health's postgres and redis
dependency checks are currently broken (SQLAlchemy text() issue and a missing
settings.redis_host attribute) — flagging in case it's relevant, but not touching
it since it's out of scope for #68.


## Week 9 — Implementation, tests, and PR

**PR link:** https://github.com/ascherj/pathreview/pull/674

**Branch name:** fix/68-health-check-safety-event-count

**Summary of changes:**
Implemented the fix in three commits following PLAN.md:

1. Redesigned the Redis storage in safety/monitoring.py. The old incr/expire
   counter never enforced window_hours (the docstring admitted it), so I switched
   to a sorted set per event type (safety:events:{event_type}:zset) with the
   event timestamp as the score. get_event_count() now prunes entries older than
   the window with ZREMRANGEBYSCORE and counts with ZCARD, so "last hour" is
   actually the last hour. Added get_total_event_count(window_hours=1) that sums
   across all 5 VALID_EVENT_TYPES.
2. Wired /health to real data. Created core/redis_client.py (shared Redis client
   built from settings.redis_url, mirroring the get_db pattern in core/database.py)
   and api/deps.py (a get_safety_monitor dependency). Replaced the hardcoded
   safety_events_last_hour = 0 in api/routes/health.py with a real call, keeping
   the existing try/except so Redis failures degrade to 0 instead of failing the
   endpoint. One catch mypy saved me from: my first version used redis.asyncio,
   but SafetyMonitor calls Redis synchronously — the async client would have
   silently returned 0 forever. Switched the shared client to sync redis.
3. Added tests/unit/test_health.py — 5 tests using an in-memory FakeRedis and
   FastAPI dependency overrides. Getting these to run took real debugging: the
   app's startup event calls init_db() against real Postgres, which broke
   TestClient across multiple tests (event-loop reuse), so I monkeypatch init_db
   to a no-op. I also had to patch the missing settings.redis_host/redis_port
   attributes (the pre-existing bug I flagged in Week 8) because that broken
   check flips /health to 503, which wraps the response in {"detail": ...} and
   breaks assertions.

**Tests touched:**
tests/unit/test_health.py (new). Covers: recent events counted, no events
returns 0, events older than 1 hour excluded (the actual windowing bug), multiple
event types summed, and Redis-down falls back to 0. All 5 pass.

**Self-review:**
- make test-unit: my 5 tests pass. The suite has 53 pre-existing failures in
  unrelated modules (bias detector, PII scrubber, resume parser, review service,
  etc.). Verified they're pre-existing by running the suite with my changes
  stashed (git stash) — same 53 failures, so my changes add zero new failures.
- Pre-commit hooks (ruff, black, mypy) pass on both implementation commits. The
  test commit was made with --no-verify: mypy follows test_health.py's import of
  api.main into pre-existing untyped modules (36 errors, none in files this PR
  touches). test_health.py itself is fully annotated and mypy-clean. Documented
  in the PR description.
- Pre-existing /health bugs (raw-SQL postgres check, missing settings.redis_host)
  left untouched as out of scope, worked around in test fixtures only.
- Migration note in PR: the storage format change means events logged under the
  old safety:events:{event_type} counter keys won't be counted after this change.
  I didn't find any other code reading the old key format.

**Feedback:**
Mentor confirmed earlier this week that overlap with RadRebelSam on #68 is fine
for this course repo, so I proceeded. I've requested a review on the draft PR via
Slack but have not received feedback back yet as of this entry — will incorporate
any review comments before marking the PR ready for review.


## Week 10 — Iteration & reflection
 
### Reviewer feedback
 
**Feedback received:** [ ] Yes  [x] No — still awaiting review
 
**Summary of feedback:**
No review has come in yet. I requested a review on the draft PR via Slack back in
Week 9 and haven't heard back as of this entry.
 
**How you responded:**
N/A — nothing to respond to yet. If feedback comes in after this entry, I'll
incorporate it and note the changes, but the PR is currently sitting as-is.
 
---
 
### Reflection
 
**What was harder than you expected?**
Python was the harder part for me overall — I'm not very familiar with the
language, so things that probably would've been quick for someone with a Python
background (the Redis sorted-set rewrite in `safety/monitoring.py`, wiring up
FastAPI's dependency injection in `api/deps.py`, getting the sync-vs-async Redis
client distinction right) took real time and trial and error. The mypy catch on
the async client silently returning 0 forever is a good example — I wouldn't have
caught that on my own without leaning on the tooling.
 
**What did you learn about working in a large codebase?**
The biggest difference from building my own project is how much of the work is
scoping what *not* to touch. I found two real pre-existing bugs in `/health` (the
broken Postgres check and the missing `settings.redis_host` attribute) while
testing my fix, and the instinct is to just fix them since I'm already in there.
But they were out of scope for #68, so I flagged them in the journal and PR
description and worked around them in test fixtures instead. I also had to deal
with someone else potentially working the same issue (RadRebelSam's nearly
identical branch), which isn't something that comes up when you're the only one
touching your own repo — it added a whole coordination step (checking with a
mentor) that had nothing to do with the code itself.
 
**How did AI tools help — and where did they fall short?**
AI tools were most useful for translating what I understood conceptually
(windowed counts, sorted sets vs. flat counters) into working Python syntax,
especially early on when I wasn't confident in the language. Where they fell
short was catching the subtler bugs — the sync/async Redis client issue was
something mypy caught, not something I'd have thought to ask an AI tool to check
for, since on the surface the async version looked like it should work fine.
 
**What would you do differently if you started over?**
I'd pick an issue that touched the RAG system, model tuning, or the multi-agent
tooling instead of the health check endpoint. The safety/health work was a good
intro issue for getting comfortable with the codebase and with Python, but it
didn't get me into the parts of PathReview I'm actually most curious about. If I
started over, I'd probably spend more time in Week 7 scanning the issue list
specifically for something in `rag/` or `agent/`, even if it meant a steeper
learning curve.
 
**What are you most proud of from this module?**
Getting through the Python unfamiliarity and still landing a real fix — not just
a patch, but an actual redesign of the storage logic (counter → sorted set) that
fixed a bug I found through testing (the windowing was never enforced) rather
than just the bug the issue described. I came out of this wanting to keep doing
open source contributions regularly, maybe about once a week, which wasn't
something I expected going in.