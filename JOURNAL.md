# PathReview Contribution Journal

> My running record of progress through Module 3. I add a new section each week.
> All Module 3 work lives on my working branch `fix/155-health-check-redis-host`.

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint is meant to report whether the app's dependencies
(like Redis) are reachable, but it reads a `redis_host` attribute off the
settings object that was never defined on the `Settings` model. Because that
field doesn't exist, every call to `/health` throws an `AttributeError` and the
endpoint fails instead of returning a status — so readiness/liveness monitoring
can't actually tell whether the service is healthy. The root cause is a mismatch
between `api/routes/health.py`, which expects `settings.redis_host`, and
`core/config.py`, which only exposes Redis through a `REDIS_URL`. A successful
fix makes `/health` respond without crashing by pointing the Redis probe at the
configuration that actually exists (rather than a phantom field), and adds a
unit test so this regression can't slip back in.

**Branch name:** `fix/155-health-check-redis-host`

**Setup confirmation:** [ ] App runs locally at localhost:5173
<!-- Frontend confirmed serving at http://localhost:5173/ (HTTP 200). Full stack
     pending local Docker/Colima install for the Postgres/Redis/Chroma backing
     services; this box gets checked once the backend is up. -->

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — selection notes

- **Scope is small and bounded.** The bug lives in one route (`api/routes/health.py`)
  plus one config file (`core/config.py`) — roughly one focused change, not a
  cross-cutting refactor. Good size for my first contribution to a large codebase.
- **I understand the area.** It's plain FastAPI + a Pydantic-style settings object;
  no deep RAG/agent internals required to be confident in the fix.
- **Clear, reproducible failure.** The issue gives an exact repro (`GET /health` →
  `AttributeError` on `redis_host`), so I can verify "before" and "after".
- **Testable success condition.** "`/health` returns a valid payload without
  raising" is easy to assert, so I can add a real unit test.
- **No special access needed.** Runs entirely against the local mock/dev stack —
  no external API keys or paid services.
- **Tier fit:** labeled `tier-1` / `good first issue`, matching where I should start.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Jeremy-Tian/pathreview/commit/bdc826cb98c408554fe24d0144a4a7e1cc28e48f

**Reproduction summary:**
I added a failing unit test ([tests/unit/test_health_redis_config.py](tests/unit/test_health_redis_config.py))
that mounts the real `/health` route with a healthy Redis stub (`ping()` → `True`)
and a working DB, then asserts Redis is reported `healthy`. It fails: `/health`
returns **HTTP 503** with `redis: "unhealthy"`, and the logs show
`redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"`.
Root cause confirmed — `api/routes/health.py` reads `settings.redis_host` /
`settings.redis_port`, but `core/config.py`'s `Settings` only defines `redis_url`.
Note: the `AttributeError` is *caught* by the probe's `try/except`, so the endpoint
doesn't hard-crash — it just reports Redis unhealthy and 503s **even when Redis is
up** (a refinement of my Week 7 description).

**PLAN.md link:** https://github.com/Jeremy-Tian/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** _(not recorded yet)_

**Blockers or open questions:**
- Local `.venv` is broken (Intel-arch wheels vs. this arm64 Mac), so I reproduced
  in a clean Python 3.11 venv. Need the project venv rebuilt to run the full suite
  and `pre-commit` (these commits used `--no-verify` to bypass the missing hook).
- Fix approach to confirm in Week 9: probe from the existing `redis_url` via
  `redis.Redis.from_url(...)` (my preference — single source of truth) vs. adding
  explicit `redis_host` / `redis_port` fields to `Settings`.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the #155 fix using the preferred approach from PLAN.md — `api/routes/health.py`
now builds the Redis client via `redis.Redis.from_url(settings.redis_url, decode_responses=True)`
instead of the nonexistent `settings.redis_host` / `settings.redis_port`. Confirmed
(via grep) that no other module reads those fields, so the change is safe and localized.
My Week 8 reproduction test now passes, and I added a companion test asserting a
genuinely-unreachable Redis still reports `unhealthy` / 503.

**Next steps:**
Open a draft PR and request peer review in Slack; finalize wording and self-review
against `make check` / `make test-unit`.

**Blockers:**
Local `.venv` is broken (x86_64 wheels on this arm64 Mac), so I couldn't run the
project's `make` targets directly. I reproduced an equivalent clean Python 3.11 venv
to run the unit suite, `ruff`, and `black` on my changes. Need the project venv
rebuilt to run `make check` / `make test-unit` natively (tracked for follow-up).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/427

**Branch:** `fix/155-health-check-redis-host`

**What you built:**
`GET /health` now probes Redis using the configured `redis_url` via
`redis.Redis.from_url(...)`, the single source of truth already on `Settings`.
This removes the `AttributeError` on the phantom `settings.redis_host` field, so the
endpoint reports Redis health based on real reachability instead of always returning 503.

**Tests added or updated:**
- [tests/unit/test_health_redis_config.py](tests/unit/test_health_redis_config.py) —
  regression test for #155: asserts redis `healthy`/200 when reachable (the repro) and
  `unhealthy`/503 when unreachable (guards against a fix that skips the check).
- [tests/conftest.py](tests/conftest.py) — autouse fixture routing structlog into
  stdlib logging so `caplog`-based assertions work in the suite.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
<!-- Not run natively (broken local .venv). Verified in an equivalent clean venv:
     unit subset shows no new failures vs. baseline; ruff/black clean on changed files;
     the 4 ruff findings and other unit failures are pre-existing and unrelated (see PR). -->

**Draft PR feedback received from:** none yet (draft PR pending)

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback came in. My PR (https://github.com/ascherj/pathreview/pull/427)
is open with 0 comments, 0 review comments, and 0 reviews as of the submission
deadline. (Per the Summer 2026 course note, peer review isn't a feature this term,
so this is expected.)

**How you responded:**
No changes were required since no feedback arrived. I re-read the PR one last time
against `docs/CONTRIBUTING.md` — branch name (`fix/<issue#>-<desc>`), Conventional
Commit messages with the `api` scope, and Google-style docstrings on the new test
functions — and confirmed it still reflects the final state of the branch.

---

### Reflection

**What was harder than you expected?**
The environment, by a wide margin — not the bug. My machine had no Docker, no
Homebrew, and a `.venv` that was silently broken (it held x86_64 wheels but I'm on
an arm64 Mac, so every import of `pydantic_core` died with an "incompatible
architecture" error). I couldn't even *run* a test until I'd installed Homebrew and
Python 3.11 and stood up a clean venv from scratch. The second surprise was the bug
itself being subtler than the issue described: the issue (and my own Week 7 note)
said `/health` "throws an AttributeError and the endpoint fails," but the error is
actually *caught* by the probe's `try/except`. The real symptom is a permanent
false-negative — `/health` returns 503 with Redis "unhealthy" even when Redis is
perfectly reachable. Getting that distinction right changed how I wrote the
reproduction.

**What did you learn about working in a large codebase?**
The hardest skill wasn't writing the fix — it was telling *my* breakage apart from
the codebase's existing breakage. When I added the `conftest.py` structlog fix, the
unit suite showed 51 failures; I only trusted that number after diffing the failing
test IDs **with vs. without** my change and proving the delta was exactly the tests
I intended to fix. The suite already had ~46 pre-existing failures and several
modules that don't even collect without optional deps. In my own projects "the tests
pass" is binary; here "passes" means "introduces no *new* failures," and you have to
establish a baseline before you can claim that. I also felt the pull of contribution
hygiene — resisting the urge to fix the 4 unrelated `ruff` findings in the file I was
already editing, and keeping commits small, scoped, and conventionally named.

**How did AI tools help — and where did they fall short?**
Most useful: locating the exact config/route mismatch fast, scaffolding the FastAPI
`TestClient` reproduction, and explaining the structlog→stdlib→`caplog` routing,
which I'd never wired up before. Where it fell short — twice, both instructive.
First, it initially surfaced the *wrong* issue (a resume-parser bug) as "the issue
to work on" before I confirmed against my branch and journal that my real issue was
#155; I had to verify, not trust. Second, the first structlog fix it produced
(`render_to_log_kwargs`) looked completely reasonable and passed the one test I
checked — but it silently broke six `test_prompt_templates` tests, because the app
logs with a `name` key that collides with a reserved `LogRecord` attribute and
raises `KeyError`. Only running the *whole* suite and diffing the baseline caught it.
The lesson: AI is good at plausible; verification is still mine to own.

**What would you do differently if you started over?**
Fix the environment first, before touching any code — I lost real time discovering
the broken venv mid-reproduction instead of validating `make test-unit` on day one.
I'd also keep the unrelated `conftest.py` structlog fix on its own branch/PR from the
start instead of folding it into the #155 PR (I flagged it for the reviewer, but it'd
have been cleaner to separate it). And I'd write the reproduction test to be
fix-agnostic from the beginning — my first version stubbed Redis by constructor args,
so when I switched the fix to `redis.Redis.from_url(...)` I had to go back and update
the stub. Testing behavior at the endpoint boundary, not the construction details,
would have avoided that.

**What are you most proud of?**
Catching my own regression. It would have been easy to see the target test go green,
call the structlog fix done, and ship six new failures into the PR. Instead I diffed
the full suite against a baseline and found the `KeyError` collision before it left my
machine. Being skeptical of a fix that *looked* finished — and proving it with data
rather than assuming — is the habit I most want to keep.
