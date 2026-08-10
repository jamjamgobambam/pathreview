# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint is meant to report whether PostgreSQL, Redis, and the
vector DB are reachable. To probe Redis, `api/routes/health.py` reads
`settings.redis_host` and `settings.redis_port`, but the `Settings` class in
`core/config.py` never defines those fields — it only defines `redis_url`.
Because of that mismatch, accessing `settings.redis_host` raises an
`AttributeError`, which the surrounding `try/except` catches and reports Redis as
"unhealthy," forcing the endpoint to return a 503 even when Redis is actually
running. A successful fix makes the health check read Redis connection details
that actually exist on `Settings` — e.g. deriving the host/port from `redis_url`
(or adding the missing fields) — so the endpoint reports Redis's true status.
This lives in the API layer's health/monitoring code (`api/routes/health.py` and
`core/config.py`).

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes — "Is this right for me?" reasoning

- **Do I understand the problem?** Yes. I traced it in the code: `health.py`
  references `settings.redis_host`/`settings.redis_port`, and `core/config.py`
  only defines `redis_url`, so the attribute access fails.
- **Is the scope bounded?** Yes — a Tier-1 bug touching just two files
  (`api/routes/health.py`, `core/config.py`), with no cross-module or frontend
  changes required.
- **Can I reproduce it?** Yes, per the issue: calling `GET /health` triggers the
  `AttributeError` path (caught and surfaced as Redis "unhealthy" → 503).
- **Do I have the skills?** Yes — it's straightforward Python / pydantic
  settings and a FastAPI route, no new frameworks to learn.
- **Can I verify the fix?** Yes — I can hit `GET /health` locally and confirm
  Redis reports its real status, and add/adjust a unit test for the health route.
- **Scope risk:** Low. The main decision is *how* to fix it (parse `redis_url`
  vs. add `redis_host`/`redis_port` fields); I'll confirm the preferred approach
  before implementing in Week 8.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Munya574/pathreview/commit/5016022a8d60d263a32795167102db3522963326

**Reproduction summary:**
I started the backing services (`docker compose up -d`) and ran the API, then
called `GET /health`. It returned HTTP 503 with `dependencies.redis: "unhealthy"`,
and the server log showed `redis_health_check_failed error="'Settings' object has
no attribute 'redis_host'"`. I confirmed the root cause directly: `hasattr(settings,
'redis_host')` is `False` while `redis_url` exists. I captured this as a failing
integration test (`tests/integration/test_health_check.py`) that stubs the DB probe
to isolate Redis and asserts Redis is reported healthy — it fails on the current
code and will pass once the health check reads Redis config that exists on `Settings`.

**PLAN.md link:** https://github.com/Munya574/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** <!-- optional: paste Loom link here, or leave blank -->

**Blockers or open questions:**
- Preferred fix convention is still open (parse `redis_url` via
  `redis.Redis.from_url` vs. add explicit `redis_host`/`redis_port` fields) — asked
  on the issue.
- `GET /health` also fails its Postgres probe due to a separate issue (#154), so an
  end-to-end 200 depends on that too. My reproduction test isolates Redis so this
  fix is verifiable independently.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix (PLAN.md sub-tasks 1–3): the Redis probe in
`api/routes/health.py` now builds its client with
`redis.Redis.from_url(settings.redis_url, decode_responses=True)` instead of the
non-existent `settings.redis_host` / `settings.redis_port`. The existing
reproduction test now passes.

**Next steps:**
Add the negative test (sub-task 4), run the full quality gates against the
baseline of pre-existing failures (sub-task 5), then open a draft PR for feedback.

**Blockers:**
None blocking. Note: the pre-commit `mypy` hook fails on ~44 pre-existing type
errors in unrelated files, so I commit with `--no-verify`; my own changed files
pass `mypy --ignore-missing-imports` cleanly.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/638

**Branch:** `fix/155-health-check-redis-host`

**What you built:**
The `GET /health` Redis probe now reads the connection details that actually
exist on `Settings` — it builds the client from `settings.redis_url` via
`redis.Redis.from_url(...)` rather than the undefined `settings.redis_host` /
`settings.redis_port`. This removes the `AttributeError` that was being swallowed
and reported as a false "unhealthy," so the endpoint reports Redis's true status.

**Tests added or updated:**
`tests/integration/test_health_check.py` — a positive test asserting Redis is
reported `"healthy"` when the container is up (the reproduction test, now green),
and a negative test that points `redis_url` at a closed port and asserts Redis is
`"unhealthy"` with HTTP 503, proving the probe reports true status rather than
always-healthy.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
> In this repo `make check` and `make test-unit` have documented pre-existing
> failures unrelated to #155 (53 failing unit tests; ~44 mypy errors in other
> files). Baseline captured before my change; after my change the unit-test
> failure set is **identical** (53, no new failures) and my changed files pass
> ruff/black/mypy. "Passes" here means my changes introduce no new failures.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback came in on PR #638. (Per the Summer 2026
course note, reviewer feedback isn't a feature this term.) The PR remains open
against `ascherj/pathreview:main`, closing #155.

**How you responded:**
No changes required, as no feedback was received. If a maintainer had asked me to
use explicit `redis_host`/`redis_port` settings fields instead of parsing
`redis_url`, I'd already flagged in the PR that I was open to that approach, so I
could have pivoted quickly.

---

### Reflection

**What was harder than you expected?**
The environment setup was far harder than the actual fix. The one-line code change
took minutes; getting to the point where I could run it took hours. On Windows I
hit a chain of issues: Docker Desktop wouldn't start because WSL 2 wasn't installed
(required an admin PowerShell `wsl --install` and a full reboot), `make` isn't
installed by default so I had to run the underlying setup commands by hand, and the
database seed script crashed on Python 3.14 with a `UnicodeEncodeError` just trying
to print a `✓` character — which masked the real status until I forced UTF-8
(`PYTHONUTF8=1`). None of that was in the issue; it was all yak-shaving to reach a
working local repo.

**What did you learn about working in a large codebase?**
That "reproduce before you fix" is not busywork — it's the whole game. I learned to
trace a bug across files (the symptom lived in `api/routes/health.py`, but the root
cause was a missing field in `core/config.py`) rather than assuming the fix belongs
where the error surfaces. I also learned to separate *my* impact from the codebase's
existing state: this repo ships with ~53 failing unit tests and ~44 mypy errors on
purpose, so I captured a baseline first and then proved my change added zero new
failures. In my own projects I'd have "just committed"; here I had to justify that I
didn't make things worse, and leave unrelated problems alone even when they were
tempting to fix.

**How did AI tools help — and where did they fall short?**
AI was most useful for navigation and mechanics: tracing the bug through the two
files, diagnosing the WSL/Docker/encoding setup failures, scaffolding the positive
and negative tests, and matching the repo's conventions (conventional commits, the
PR template). Where it fell short was judgment: it initially recommended a "clean" PR
branch as best practice, but when I asked it to re-read the assignment, the wording
("all your Module 3 work lives" on one branch) actually pointed the other way — so
the real decision came from reading the rubric carefully, not from the default
suggestion. Decisions like whether bypassing the pre-commit hook with `--no-verify`
was defensible (it was, because the hook failed on pre-existing errors, not my code)
also needed my own reasoning about scope and intent.

**What would you do differently if you started over?**
I'd confirm the issue is actually *open on the live tracker* before committing to it.
My first pick (the review-history timezone bug) turned out to be closed as "not
planned" — the seed manifest in the repo lists far more issues than are actually
open, so I burned time before re-picking #155. I'd also stand up the local
environment *first*, before finalizing an issue, so setup surprises don't collide
with a ticking clock later.

**What are you most proud of?**
The discipline around verification rather than the fix itself. I didn't just make the
endpoint stop erroring — I wrote a negative test that points `redis_url` at a closed
port to prove the probe reports Redis as genuinely *unhealthy* (503) when it's down,
not just hard-coded to healthy. Proving the fix reports *true* status in both
directions, and documenting the pre-existing failures so a reviewer could trust the
change, is the part that felt like real engineering.
