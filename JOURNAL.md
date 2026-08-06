# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint in `api/routes/health.py` tries to build a Redis client using `settings.redis_host` and `settings.redis_port`, but the `Settings` class in `core/config.py` only defines a single `redis_url` field — those two attributes don't exist. Every call to the health check therefore raises an `AttributeError` while checking Redis, which gets silently caught by a broad `except Exception` and reported as `"redis": "unhealthy"`. This makes the endpoint useless for its actual purpose: it always reports Redis as down, even when Redis is running fine, and hides the real bug (a code error, not an infrastructure problem) from anyone reading the health status. A successful fix builds the Redis client from `settings.redis_url` directly (e.g. `redis.Redis.from_url(...)`) so the health check accurately reflects Redis's real status, plus a test that exercises `/health` so this kind of attribute-name drift is caught automatically next time.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes (fit checklist):**
- Scope: touches exactly one file (`api/routes/health.py`) plus a new/updated test — small, well-bounded for a first contribution.
- Comfort: Tier 1 (`good first issue`) label, and I verified the root cause myself by reading `core/config.py` alongside `health.py` before claiming — it's a straightforward attribute mismatch, not a design question.
- Risk: low — the fix doesn't change the health check's contract (still returns the same JSON shape / status codes), just makes the Redis check work correctly.
- Learning value: touches Pydantic Settings, the `redis-py` client API, and error-swallowing anti-patterns (`except Exception` masking bugs), which felt like a good first exposure to this codebase's conventions.

**Progress update:** Fix implemented in `api/routes/health.py` (Redis client now built via `redis.Redis.from_url(settings.redis_url)`), with unit tests added in `tests/unit/test_health_check.py` covering both the healthy path and a real Redis ping failure. `ruff`, `black`, and `mypy` all pass on the changed files via the repo's pre-commit hooks. Commit: `fa4bd64` on this branch.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/YunzheOVE/pathreview/commit/41f4335

**Reproduction summary:**
Reproduced the bug in isolation by calling `redis.Redis(host=settings.redis_host, ...)` directly, which raised `AttributeError: 'Settings' object has no attribute 'redis_host'`. Then ran the pre-fix `health_check()` function against a stubbed DB session to observe the full user-facing symptom: the error gets silently caught and the endpoint reports `"redis": "unhealthy"` with a `503`, even though Redis itself was never actually contacted. Full transcript and root-cause explanation are in `REPRODUCTION.md`.

**PLAN.md link:** https://github.com/YunzheOVE/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** Not recorded — optional per instructions, skipped for this week.

**Blockers or open questions:**
None blocking. One dependency to keep in mind for Week 9: fixing this endpoint required type-annotating `health_check()`, which surfaced an unrelated pre-existing bug (issue #154, raw SQL string passed to `db.execute()`). I suppressed it with a scoped `# type: ignore` comment rather than fixing it, to keep this PR limited to #155 — noted in `PLAN.md` under Risks & unknowns in case #154 gets fixed independently and the suppression comment needs cleanup.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from `PLAN.md` are implemented: the Redis client in `api/routes/health.py` is now built via `redis.Redis.from_url(settings.redis_url, decode_responses=True)` instead of the non-existent `settings.redis_host`/`settings.redis_port`, the endpoint signature is type-annotated (`Annotated[AsyncSession, Depends(get_db)]`, `-> dict[str, Any]`), and two unit tests were added in `tests/unit/test_health_check.py` covering the healthy path and a real Redis ping failure.

I also ran a full self-review pass beyond just the changed files: `ruff check .`, `black --check .`, and `python -m pytest tests/unit` against the whole repo to see the baseline, not just my own files. On the changed files specifically, `ruff` and `black` pass cleanly and both new tests pass. Repo-wide, there are pre-existing failures unrelated to this change: 53 pre-existing unit test failures (e.g. `test_review_service.py` fails due to an unrelated `AttributeError: 'coroutine' object has no attribute 'first'` in `core/services/review_service.py`, nothing to do with Redis/health), 178 pre-existing `ruff` findings elsewhere in the repo, and `mypy` errors from missing third-party stubs (`PyPDF2`, `jose`, `passlib`, `rank_bm25`) plus a numpy stub incompatible with Python 3.13. None of these touch `api/routes/health.py` or `tests/unit/test_health_check.py`, and none existed because of my change — I confirmed by running the same commands against `main` before starting.

**Next steps:**
Get peer/mentor feedback on the open PR (#244) in the course Slack channel, incorporate any requested changes, and finalize the PR description so it accurately reflects the `from_url()` approach and documents the pre-existing failures above.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/244

**Branch:** `fix/155-health-check-redis-host`

**What you built:**
Fixed the `/health` endpoint's Redis check, which raised `AttributeError` on every request because `Settings` only defines `redis_url`, not `redis_host`/`redis_port`. The client is now built with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`, so `/health` correctly reports Redis's real status instead of always showing `"unhealthy"`.

**Tests added or updated:**
Added `tests/unit/test_health_check.py` with two tests: `test_redis_check_uses_redis_url_not_missing_attrs` (verifies the client is constructed from `settings.redis_url` via `from_url` rather than the missing host/port attributes) and `test_redis_check_reports_unhealthy_when_ping_fails` (verifies the endpoint reports `"redis": "unhealthy"` with a 503 when Redis ping genuinely fails, so real failures still surface correctly).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(On changed files: `ruff`, `black`, and `mypy` pass with no new errors, and both new tests pass. Repo-wide, 53 pre-existing test failures, 178 pre-existing `ruff` findings, and several pre-existing `mypy` stub errors exist on `main`/unrelated files — confirmed unaffected by this change; see Check-in 1 for detail.)*

**Draft PR feedback received from:** A cohort peer, via the course Slack review channel — confirmed the `redis.Redis.from_url()` approach was correct and the test coverage was sufficient; no changes requested to the reviewed code.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer comments have come in on PR #244.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
The actual code fix was trivial — one line, swap `redis.Redis(host=..., port=...)` for `redis.Redis.from_url(settings.redis_url)`. What took real time was everything *around* the fix: getting a stable local dev environment running on Windows inside a OneDrive-synced folder. `uvicorn --reload` was watching `.venv` and `node_modules` and triggering endless reload loops and port conflicts because OneDrive kept re-syncing files mid-reload; `npm` failed under Git Bash because Windows needs the `.cmd` shim explicitly; `seed_db.py` crashed on startup because Windows' default console codepage couldn't print a checkmark character. None of that had anything to do with the actual bug I was assigned, but it consumed more debugging time than the fix itself.

**What did you learn about working in a large codebase?**
The biggest shift was learning to separate "is this broken because of my change" from "was this already broken." Before this module I would have seen 53 failing tests and 178 lint errors after my change and assumed I'd broken something. Here, I had to actually run the same checks against `main` before touching anything, read the specific tracebacks (e.g. an unrelated `AttributeError: 'coroutine' object has no attribute 'first'` in `core/services/review_service.py`) to confirm they were pre-existing and unrelated to Redis/health, and then explicitly document that comparison rather than just claiming "tests pass." That kind of blast-radius thinking (proving your change is safe, not just that it works) is very different from working on a personal project where you're usually the only source of bugs.

**How did AI tools help — and where did they fall short?**
Where it helps: AI assistance was most useful for the mechanical, high-friction parts: diagnosing Windows-specific environment failures quickly by reading terminal output and cross-referencing the `Makefile`, writing the `AsyncMock`/`MagicMock` test scaffolding for the async DB session and Redis client (a pattern I hadn't used before), and systematically checking my PR/journal against the grading rubric line by line using the live GitHub API instead of just eyeballing it.

Where it fell short: it initially wrote a PR description that was subtly wrong about how the fix worked (describing manual host/port parsing when the actual code just calls `from_url()`). It's a good reminder that AI-generated descriptions of your own code still need a human fact-check against to avoid potential errors later on.

**What would you do differently if you started over?**
I'd set up the project outside of OneDrive from day one (e.g. in a plain `C:\dev\` folder) — nearly every environment issue I hit traced back to file-sync interference, and it would have saved a full session of debugging. I'd also avoid letting my personal `instructions.md` file get anywhere near the git index; it accidentally got tracked and included in a commit, which I had to clean up mid-module. Fix-wise, I'm satisfied with the scope I chose — a small, well-bounded Tier 1 issue was the right call for a first contribution.

**What are you most proud of from this module?**
Catching and documenting the unrelated pre-existing issue #154 (the raw SQL string bug that `mypy` surfaced once I added type annotations) without scope-creeping into fixing it. It would have been easy to either ignore the new type error or to "fix everything while I'm in here" — instead I suppressed it with a scoped `# type: ignore` comment, filed the reasoning in `PLAN.md` and `JOURNAL.md`, and kept the PR focused on exactly #155. That kind of discipline felt like the most "real open-source contributor" moment of the whole module.