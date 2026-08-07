# Project Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint in `api/routes/health.py` tries to build a Redis client from `settings.redis_host` and `settings.redis_port`, but the `Settings` model in `core/config.py` never defines those fields — it only has a `redis_url` string. Because of that, the Redis probe raises an `AttributeError` every time instead of actually checking whether Redis is up, so the health check always reports Redis as unhealthy even when it is running fine. A successful fix makes the health check build its Redis client from the existing `redis_url` setting (via `redis.Redis.from_url`), so the probe connects properly and reports the real Redis status.

**Selection notes — "Is This Issue Right for Me?" checklist:**

_Part 1 — Understanding the issue._ In my own words: the `/health` endpoint's Redis probe reads `settings.redis_host` and `settings.redis_port`, but the `Settings` model in `core/config.py` only defines `redis_url`, so the probe throws `AttributeError` and Redis always shows as unhealthy. The affected area matches the issue's `api` label: `api/routes/health.py` plus `core/config.py`, and I confirmed both files and the exact lines exist. Done looks like: before the fix, `GET /health` returns 503 with Redis marked "unhealthy" even when Redis is up; after the fix, the probe builds its client from `redis_url` and reports the real Redis status.

_Part 2 — Tier fit._ This is my first contribution to this codebase, so I'm choosing Tier 1 as recommended. The change is localized to one function in one file, which fits the Tier 1 definition.

_Part 3 — Codebase readiness._ I read the whole `health_check` handler, not just the broken line: it probes Postgres, Redis, and the vector DB, marks each dependency, and returns 503 if any is unhealthy — so I can predict my change only affects the Redis branch. My rough plan without looking anything up: replace the `redis.Redis(host=..., port=...)` construction with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`. There is no test file for the health route yet (nothing in `tests/unit/` covers it), so I read existing tests in `tests/unit/` to learn the fixture and assertion patterns, and my PR will add the first `/health` tests.

_Part 4 — Scope and time._ The issue has several other claims in the comments; claims are non-exclusive and I'm fine sharing it. As a Tier 1 fix (one function plus a new test file) and a large new repo, I estimate 3–5 hours including testing, which fits comfortably in the Weeks 8–9 window. The issue lists no blockers or dependencies on other issues.

**Branch name:** fix/155-health-check-redis-url

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/CCatherineeeee/pathreview/commit/215fc5316e53f1da5371e03654d1e995b862272d

**Reproduction summary:**
I brought the stack up locally (`docker compose up -d`, migrations, uvicorn) and called
`GET /health`, which returned 503 with `redis: "unhealthy"` on every request while
`docker compose exec redis redis-cli ping` answered `PONG` — proving Redis was fine and
the probe was lying. The uvicorn log gave the real cause:
`'Settings' object has no attribute 'redis_host'`, an `AttributeError` swallowed by the
handler's broad `except Exception` and misreported as a dependency outage.

**PLAN.md link:** https://github.com/CCatherineeeee/pathreview/blob/fix/155-health-check-redis-url/PLAN.md

**Walkthrough video (recommended):** _not recorded_

**Blockers or open questions:**
No blockers — the fix is validated and the path into Week 9 is clear. Two things I want a
maintainer's read on, both pre-existing and both scoped out of this PR into their own
issues: whether the Redis probe should carry a `socket_connect_timeout` (without one an
unreachable host hangs the endpoint), and whether the per-request client should be pooled
or closed. Separately, the Postgres probe in the same handler is broken independently of
#155, so `/health` will keep returning 503 after my fix lands — I need to make sure
reviewers read that as expected rather than as my change not working.

---

### Reproduction detail

**Status:** Reproduced and confirmed. The bug triggers on every request, not intermittently.

### Environment setup

Starting from a clean checkout (no `.env`, no `.venv`, Docker stopped):

```bash
cp .env.example .env
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
docker compose up -d
.venv/bin/alembic upgrade head        # applies migrations 001 and 002
.venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### Reproduction steps

```bash
curl -i http://127.0.0.1:8000/health
```

Observed — HTTP `503`, Redis reported as down:

```json
{
  "detail": {
    "status": "unhealthy",
    "dependencies": {
      "postgres": "unhealthy",
      "redis": "unhealthy",
      "vector_db": "healthy"
    },
    "safety_events_last_hour": 0,
    "timestamp": "2026-07-22T01:22:06.226408"
  }
}
```

Repeated 3 times, identical response each time.

### Proving it is a false alarm

Redis itself is healthy the whole time:

```bash
docker compose exec redis redis-cli ping
# PONG
```

So the endpoint claims Redis is down while Redis is answering. That contrast is the
core of the reproduction.

### Root cause confirmation

The HTTP response body gives no useful detail — it only says `"unhealthy"`. The real
cause appears only in the uvicorn server log:

```
redis_health_check_failed  error="'Settings' object has no attribute 'redis_host'"
```

Confirmed directly against the settings object:

```bash
.venv/bin/python -c "
from core.config import settings
print('has redis_host?', hasattr(settings, 'redis_host'))   # False
print('redis_url =', settings.redis_url)                    # redis://localhost:6379/0
"
```

`api/routes/health.py` (lines 44–49) builds its client from `settings.redis_host` and
`settings.redis_port`. `core/config.py` defines neither — it exposes only `redis_url`
(line 12). The attribute lookup raises `AttributeError` before any connection is
attempted, and the surrounding `except Exception` catches it and labels the dependency
"unhealthy".

**Takeaway for the PR:** the broad `except Exception` makes a coding error
indistinguishable from a real outage. A missing attribute and a dead Redis produce the
exact same output.

### Fix direction, validated

```bash
.venv/bin/python -c "
import redis
from core.config import settings
r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
print('ping ->', r.ping())   # True
"
```

Confirms `redis.Redis.from_url(settings.redis_url, ...)` connects against the running
container, so the planned one-line fix is sound.

### Out of scope — found while reproducing

Two other things surfaced. Neither is part of #155 and neither will be changed in this PR.

1. **Postgres check is also broken.** `health.py` line 31 calls
   `await db.execute("SELECT 1")` with a raw string, which SQLAlchemy 2.x rejects:
   `Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`.
   This matters for acceptance criteria: after fixing Redis, the `redis` key flips to
   `"healthy"`, but the endpoint still returns 503 because Postgres stays unhealthy.
   Worth filing separately.

2. **Vector DB check is vacuous.** It only tests whether the `vector_db_url` string is
   non-empty, so it reports `"healthy"` even when the Chroma container is stopped —
   which it was during part of this session.

### Next step

Add the first `/health` test file under `tests/unit/` (no test currently references the
health route), then apply the `from_url` fix.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1–4 of PLAN.md are complete.

1. _Fix the client construction_ — done. `api/routes/health.py` now calls
   `redis.Redis.from_url(settings.redis_url, decode_responses=True)` in place of the
   six-line `redis.Redis(host=..., port=...)` block that referenced two fields Settings
   never defines.
2. _Add `tests/unit/test_health.py`_ — done. 7 tests, the repo's first route tests.
3. _Verify end to end_ — done. Against live Docker the probe reports `healthy`, flips to
   `unhealthy` when I run `docker compose stop redis`, and returns to `healthy` on
   restart. Before the fix it reported `unhealthy` in all three states.
4. _Run the full gate_ — done, with pre-existing failures measured against a clean
   baseline (details below).

I also confirmed the tests actually catch the bug: reverting `health.py` to the pre-fix
version makes 2 of the 7 fail, so they are genuine regression guards rather than tests
that pass against broken code.

**Next steps:**
Sub-task 5 — open a draft PR, request peer review in the Slack channel my instructor
designates, address any feedback I agree with, then mark it ready for review. After that,
file the three follow-up issues for the out-of-scope problems found while reproducing
(the Postgres `text()` bug, no Redis connection timeout, no connection cleanup), and
complete Check-in 2 with the PR link.

**Blockers:**
None blocking. Two environment findings worth recording:

- `make` is not installed on my machine — running any target triggers an Xcode
  command-line-tools install prompt. I ran the underlying commands directly
  (`ruff check .`, `black --check .`, `mypy api/ core/ ...`, `pytest tests/unit -m unit`).
- The repo has substantial pre-existing failures. I measured a baseline from a clean
  worktree at the last commit before any of my code changes, then re-measured after:

  | Check                       | Before                | After                 | New failures |
  | --------------------------- | --------------------- | --------------------- | ------------ |
  | `ruff check .`              | 182 errors            | 182 errors            | 0            |
  | `black --check .`           | 52 to reformat        | 52 to reformat        | 0            |
  | `mypy api/ core/ ...`       | 5 errors              | 5 errors (identical)  | 0            |
  | `pytest tests/unit -m unit` | 53 failed, 375 passed | 53 failed, 382 passed | 0            |

  My two files are individually clean under ruff and black; my change adds 7 passing
  tests and introduces no new failures in any check.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/375

**Branch:** `fix/155-health-check-redis-url`

**What you built:**
The `/health` endpoint's Redis probe built its client from `settings.redis_host` and
`settings.redis_port`, neither of which exists on `Settings`, so the lookup raised
`AttributeError` before any connection was attempted and the handler's broad
`except Exception` reported that coding error as a dependency outage — Redis showed
unhealthy even while answering `PING`. The fix builds the client from
`settings.redis_url` (the field `Settings` actually defines) via `redis.Redis.from_url`,
so the probe connects and reports Redis's real status.

**Tests added or updated:**
`tests/unit/test_health.py` (new, 7 tests — the repo's first route tests). Covers the
Redis probe reporting healthy when reachable and unhealthy when the connection is
refused; a regression guard asserting the client is built from `settings.redis_url` and
that `decode_responses` is forwarded; a guard that `Settings` exposes `redis_url` and
neither `redis_host` nor `redis_port`; and three parametrized invalid-URL cases (empty,
scheme-less, wrong-scheme) confirming bad configuration is reported rather than crashing
the endpoint. The database dependency is stubbed so the Postgres probe stays healthy and
the assertions isolate Redis, keeping the tests offline and Docker-free.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review (Su26 note: formal
reviewer feedback is not provided this term)

**Summary of feedback:**
No formal review came in. PR #375 has one informal comment from a peer, AngelD2000
("LGTM"), but no line comments and no engagement with the two open questions I flagged in
the PR description (the missing `socket_connect_timeout` and whether the client should be
pooled or closed per request). Per the course note, this doesn't count as reviewer
feedback, so I'm treating the PR as unreviewed.

**How you responded:**
N/A — no feedback to respond to. The two open questions from the PR description remain
open; I filed the Postgres `text()` bug found during reproduction as its own issue rather
than folding it into this PR, since no reviewer weighed in either way.

---

### Reflection

**What was harder than you expected?**
Reproducing the bug convincingly was harder than fixing it. The fix is a one-line change,
but proving it was the *only* thing wrong took real work: I had to rule out that Redis
itself was down (it wasn't — `redis-cli ping` answered `PONG` while the endpoint reported
"unhealthy"), and then find that the real error was buried in the uvicorn log, not the
HTTP response, because `health.py`'s broad `except Exception` swallowed the `AttributeError`
and reported it identically to a real outage. Writing a reproduction that a reviewer could
trust without re-running everything themselves took longer than the code change itself.

**What did you learn about working in a large codebase?**
The biggest adjustment was scope discipline. While reproducing #155 I found two more real
bugs in the same function — the Postgres probe uses a raw SQL string that SQLAlchemy 2.x
rejects, and the vector DB check only verifies a config string is non-empty, not that the
service is reachable. In my own projects I'd have just fixed all three in one pass. Here I
had to leave them alone, note them for reviewers, and file them separately, because a PR
that touches three unrelated bugs is harder to review than three PRs that touch one each.
I also learned to measure a baseline before touching anything — the repo already had 53
failing unit tests and 182 ruff errors on `main`, and without recording that first I would
have had no way to prove my change added zero new failures.

**How did AI tools help — and where did they fall short?**
AI assistance (Claude, via this tool) was most useful for exploration and drafting: finding
every file that touched Redis, confirming the exact field mismatch between `health.py` and
`Settings`, writing the first draft of the test file and PR description, and working through
the "Is this right for me?" checklist against the actual code instead of in the abstract. It
fell short on judgment calls that needed my own decision: whether to fold the Postgres bug
into this PR or file it separately, and how much detail a reviewer actually needs in the PR
description versus what's just noise. With no formal review process this term, I couldn't
lean on a human reviewer to validate that judgment either — I had to be the one deciding
whether the PR description's open questions were resolved enough to consider the work done.

**What would you do differently if you started over?**
I'd write the PR description assuming no one will read it closely, since without a review
requirement this term there was no guarantee anyone would. I put two open questions (the
connect-timeout and pooling/cleanup behavior) in prose inside "Notes for Reviewers," and
in hindsight I should have filed those as their own follow-up issues immediately instead
of leaving them as unresolved questions in a PR that may never get a substantive read. I'd
also record my local environment quirks (no `make` installed, had to run
`ruff`/`black`/`mypy`/`pytest` directly) in Week 7 instead of discovering and writing about
them mid-Week-9, so future-me isn't rediscovering the same setup friction under deadline
pressure.

**What are you most proud of from this module?**
The regression tests actually testing something. Before finishing, I reverted `health.py`
to the pre-fix version and reran `tests/unit/test_health.py` — 2 of 7 tests failed against
the broken code. That's a small thing, but it's the difference between a test suite that
looks like coverage and one that would actually catch someone reintroducing this bug later.
