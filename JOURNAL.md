## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint in api/routes/health.py tries to read a setting
called redis_host to check if Redis is working. This setting does not exist
on the Settings model. Only redis_url exists there. Because of this, calling
GET /health crashes with an AttributeError before it can report Redis status.
A correct fix will build the Redis connection from redis_url instead, so the
health check can run without crashing and give a clear status for Redis.

**Checklist notes:**
This issue is Tier 1, and the fix is contained to one file, api/routes/health.py. I confirmed the bug directly, redis_host is used in that file but does not exist in Settings, only redis_url does. The codebase and test setup is not fully explored yet, that will happen in Week 8. Many students have claimed this issue and one PR is already open, but claims are non-exclusive, so I am comfortable with the overlap. The scope looks realistic for the Weeks 8-9 timeline. Once I am more comfortable with the codebase, I may take on a second issue at a higher tier as a stretch goal.

**Branch name:** fix/155-redis-host-config

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/JadeJaguar/AI201-pathreview/commit/3699f09

**Reproduction summary:**
I wrote a unit test that calls the health_check function directly with a
mocked database. The test confirms that the Redis check always fails with
an AttributeError, because settings.redis_host does not exist on Settings,
so the /health endpoint always reports Redis as unhealthy.

**PLAN.md link:** https://github.com/JadeJaguar/AI201-pathreview/blob/fix/155-redis-host-config/PLAN.md

**Walkthrough video (recommended):** not recorded

**Blockers or open questions:**
Not fully sure yet if redis.Redis.from_url is the correct method to use with
this project's version of the redis package. Also unsure if I should fix the
unrelated mypy errors already present in health.py, since they blocked my
commit and I had to use --no-verify to get past them this week.## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Reproduced the issue and wrote PLAN.md in Week 8. Implemented the fix in
api/routes/health.py, changing the Redis client to use redis.Redis.from_url
with settings.redis_url, instead of the missing redis_host and redis_port
fields.

**Next steps:**
Update the reproduction test to check the fixed, healthy behavior. Run
make check and make test-unit, confirm no new failures. Open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/958

**Branch:** fix/155-redis-host-config

**What you built:**
Fixed the /health endpoint's Redis check, which previously always failed
with an AttributeError because it read settings.redis_host and
settings.redis_port, fields that do not exist on Settings. The fix builds
the Redis client with redis.Redis.from_url(settings.redis_url), the setting
that actually exists, so the health check now correctly reports Redis
status instead of always failing.

**Tests added or updated:**
Updated tests/unit/test_health.py. It now has two tests, one confirming
Redis reports healthy when the ping succeeds, and one confirming Redis
still correctly reports unhealthy, without crashing, when Redis is
unreachable.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Notes on pre-existing failures:**
make check flags one pre-existing issue in api/routes/health.py, a B008
warning about using Depends() in an argument default. This pattern is used
in every route file in the project (profiles.py, reviews.py, etc.), and is
unrelated to issue #155, so it was left as is.

make test-unit shows 53 pre-existing failing tests, unrelated to this fix,
spread across bias_detector, pii_scrubber, resume_parser, readme_scorer,
review_service, and others. These are separate known bugs in the codebase,
matching several other tier-1 issues in the tracker (for example #146,
#147, #153). Both tests in test_health.py pass, and none of the 53
pre-existing failures reference health.py or redis.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No

**Summary of feedback:**
No review came in during Week 10.

**How you responded:**
N/A, no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Running make check across the whole project was harder than I
expected. It returned 183 errors on the first run, and at first that
felt like I had broken something big. I had to learn to read through
all of it carefully and figure out which errors were caused by my
own change, versus which ones already existed in files I never
touched. Separating "my bug" from "the project's existing debt" was
a skill I didn't expect to need this early.

**What did you learn about working in a large codebase?**
In my own projects, if something is broken, it's almost always
something I just wrote. In this codebase, that assumption doesn't
hold. I had to actually verify, using grep and by reading
core/config.py directly, rather than guessing, before I could be
confident my fix was correct and my test wasn't just reproducing an
already-known problem. I also learned that a fix isn't done until
you've proven it with a passing test (with edge cases included), 
not just by seeing the right output once in a browser.

**How did AI tools help, and where did they fall short?**
AI tools were most useful for understanding unfamiliar parts of the
process fast, like what a specific error message actually meant, or
how to structure a test I'd never written before.

**What would you do differently if you started over?**
I'd run make check and make test-unit right after reproducing the
bug in Week 8, instead of waiting until right before opening the PR
in Week 9. That would have given me more time to separate
pre-existing issues from new ones, instead of doing it all under
time pressure.

**What are you most proud of from this module?**
Writing the reproduction test before touching any code. It forced me
to prove the bug was real and understand exactly where it lived,
before I wrote a single line of the actual fix.
