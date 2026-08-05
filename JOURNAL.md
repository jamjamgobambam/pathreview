## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/82

**Issue title:** Concurrent review requests for the same profile can produce inconsistent results

**Tier:** [x] Tier 3

**Problem summary:**
When two review requests for the same profile are submitted at nearly the same time,
`create_review()` has no check for an existing in-flight review before starting a new
one. Each request independently triggers `process_review()`, which re-runs the full
ingestion pipeline and writes its own `IngestedSource` and `Review` rows with no
coordination between the two runs. In practice this produces duplicate ingested data
for one profile and two competing review results with no clear "correct" outcome for
the client to read. A successful fix adds a guard — a per-profile lock, a DB-level
constraint, or a rejection of the second request — so that only one review can be
in progress for a given profile at a time. This affects `api/routes/reviews.py` and
`core/services/review_service.py`.

Scope-fit checklist — Is this right for me?

This issue sits at the right difficulty for where I am right now — hard enough that I have to make a real design decision instead of applying a mechanical patch, but bounded enough (two files, one traceable root cause) that I can actually finish it and reproduce it with confidence rather than getting lost in an open-ended problem. The full reasoning behind that verdict is below.

How I located the relevant files: The issue lists api/routes/reviews.py and core/services/review_service.py as relevant files. I didn't take that at face value — I read both files in full before committing to the issue, and traced the actual code path: POST /reviews in reviews.py calls create_review(), which hands off to process_review() in review_service.py. Neither function checks for an existing in-flight review before starting a new one, which is the actual root cause, not just a description of one.

What's the root cause, concretely? create_review() has no guard against two requests for the same profile_id running concurrently. Each call independently triggers process_review(), which re-runs _run_ingestion_pipeline() — so two overlapping requests produce duplicate IngestedSource rows and two competing Review records with no coordination between them.

**Branch name:** fix/82-concurrent-review-race

**Setup confirmation:** [x] App runs locally at localhost:5173
*(needs `docker compose up -d db`, `alembic upgrade head`, backend + frontend running — confirm once you've done this)*

**Cohort ledger:** [x] Issue added to cohort ledger
*(comment on #82 claiming it, then add it to whatever ledger/sheet your course uses)*

## Week 8 — Reproduction & solution planning

**Reproduction summary:** Added a test that fires two concurrent `create_review()` calls for the same `profile_id` via `asyncio.gather`; without a guard in `create_review()`, both calls independently ran `process_review()` / `_run_ingestion_pipeline()`, producing two `IngestedSource` rows and two `Review` rows for one profile instead of one.

**Blockers or open questions:**
Still deciding between an in-process lock vs. a DB-level constraint for serializing reviews — depends on whether the app runs multiple worker processes in this environment. Need to check for other call sites of `process_review()` besides the `POST /reviews` route before finalizing the fix.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the concurrency guard from PLAN.md: `create_review()` in
`core/services/review_service.py` now relies on a DB-level partial unique
index (`uq_reviews_profile_active`, one active review per `profile_id`)
and raises `ReviewAlreadyInProgressError` when a concurrent insert
violates it. Added a new Alembic migration for the index. Updated
`api/routes/reviews.py` to catch that error and return 409 with the
existing review's id. Rewrote `tests/unit/test_concurrent_review_race.py`
to verify the fix (previously it only reproduced the bug) — all 3 tests
pass: same-profile rejection, different-profiles non-blocking, and
guard release once a review leaves the active state.

**Next steps:**
Cleaning up a stray duplicate test file before final self-review, then
running `make check`/`make test-unit` against a clean tree and diffing
against my pre-fix baseline to confirm no new failures. Opening a draft
PR for feedback once that's confirmed.

**Blockers:**
None currently — ran into an early Alembic/Docker setup issue (missing
`script.py.mako`, Docker daemon not running) but both resolved.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/779

**Branch:** `fix/82-concurrent-review-race`

**What you built:**
Added a DB-level partial unique index enforcing at most one active
(`pending`/`processing`) review per profile. `create_review()` catches
the resulting `IntegrityError` on a conflicting concurrent insert and
raises `ReviewAlreadyInProgressError`; the API layer turns that into a
409 response carrying the existing review's id, instead of silently
allowing two independent reviews (and duplicate ingestion) to run for
the same profile.

**Tests added or updated:**
`tests/unit/test_concurrent_review_race.py` — rewritten from a bug
reproduction into fix verification. Covers: (1) two concurrent
`create_review()` calls for the same profile produce exactly one
success and one `ReviewAlreadyInProgressError`, (2) concurrent calls for
different profiles both succeed independently, (3) a profile's guard
releases once its review leaves the active state, allowing a new one.
Uses a fake session + fake shared table to simulate the real unique
index without a live Postgres connection.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
*(Confirm both against a clean tree — see note above about the stray
duplicate test file — before checking these off. `test-unit`: 53
pre-existing failures observed both before and after this change, none
in files this fix touches. `check`: [FILL IN after re-running clean —
document the pre-existing lint failure count here, e.g. "N pre-existing
ruff errors across unrelated files, confirmed identical before/after."])


## Week 10 — Reflection


### Reflection

**What was harder than you expected?**
Getting the environment actually running was a bigger time sink than
the fix itself. I hit three separate blockers before I could even
generate a migration: Alembic failing with a missing `script.py.mako`
template file (had to restore it or copy it from the installed
package), Docker Desktop not actually running when `docker compose up
-d` failed against the socket, and only after both of those could I
get to the real work. None of that was a "hard problem" in the
interesting sense — it was just friction — but it ate a
disproportionate amount of the week compared to writing the actual
guard logic.

The part of the actual fix that was harder than expected was my own
test. My first version of the concurrency reproduction test used one
shared fake DB session object for both "concurrent" calls, and it
passed for the wrong reason — the shared session's `commit()` couldn't
tell which call's object was which, so it silently let both through
instead of catching a real conflict. I only caught this because the
test's behavior didn't change the way I expected after I'd already
fixed the underlying bug — if I hadn't dug into *why*, I could have
shipped a fix with a test that wasn't actually testing anything. That
was a good lesson in not trusting a passing test just because it's
green.

**What did you learn about working in a large codebase?**
The issue as filed ("add a per-profile lock") undersold how many
constraints the existing code already imposed on the solution space.
`process_review()` commits three separate times across its lifecycle
(status→processing, post-ingestion, completion) specifically so that
`GET /reviews/{id}/status` can poll and see progress mid-flight. That
ruled out an approach I initially considered — a transaction-scoped
Postgres advisory lock held for the whole pipeline — because collapsing
those three commits into one long transaction to support the lock
would have quietly broken the polling endpoint. I wouldn't have known
that constraint existed without actually reading `process_review()` in
full before choosing a design. A DB-level partial unique index needed
zero changes to that function, which made it the safer choice for a
codebase I didn't write and don't fully understand every edge case of.

I also learned that "pre-existing failures" isn't something to just
assert — it's something to prove. I ran `make test-unit` and `make
check` before touching anything, then diffed the exact `FAILED` list
before and after my change rather than eyeballing whether the counts
looked similar. That caught something real: one `make check` run
looked at first like more pre-existing noise, but turned out to
include two actual bugs I'd introduced — a missing `raise ... from exc`
on my new `IntegrityError` handler, and an except-block that had landed
in the wrong route function during editing. Without the diff, I might
have logged those as "pre-existing" in my PR description, which would
have been wrong and would have hidden my own bug from a reviewer.

**How did AI tools help — and where did they fall short?**
AI assistance was strongest for exactly the kind of work where "does
this fit the existing code" mattered more than "is this correct in
general" — reading `process_review()`'s actual commit structure before
proposing a fix, rather than defaulting to the first textbook answer
(advisory lock) that would have quietly broken something. It was also
useful for the tedious-but-important self-review discipline: diffing
failure lists rather than trusting a glance, catching that my fake
test session was sharing state incorrectly, and picking the new lines
out of a wall of ruff/mypy output.

Where it fell short, or where I had to be the check on it rather than
the other way around: I found an existing open PR for the same issue
number on the upstream repo from another student, submitted with a
completely different design — a Postgres advisory lock. It would have
been easy to treat that as "the answer" and copy the approach
uncritically. Instead I used it as a prompt to think about *why* that
approach might not fit this specific codebase's commit structure, which
is what actually led to the partial-unique-index design instead. The
tool also can't verify things outside its reach — I still had to be the
one who actually ran `docker compose up -d`, actually confirmed Docker
Desktop was running, actually ran `\d reviews` against the real
database to confirm the index landed. No amount of AI-assisted
debugging replaces actually running the thing.

**What would you do differently if you started over?**
I'd read `process_review()`'s full commit structure *before* writing my
Week 8 PLAN.md, not after starting Week 9 implementation. My original
plan listed a transaction-scoped lock as one of a few options without
flagging that it was actually incompatible with the existing polling
behavior — I only discovered that constraint later, which meant some
of my Week 8 planning time went toward an option I ended up ruling out
for reasons I could have known from the start. I'd also set up and
confirm the full local environment (Docker running, Alembic template
file present) during Week 7 initial setup, rather than discovering both
were broken in the middle of Week 9 when I actually needed to generate
a migration.

**What are you most proud of from this module?**
Catching my own test bug. It would have been easy to see three green
checkmarks after the first version of
`test_concurrent_review_race.py` and move on — the assertions read
correctly, the test ran, it passed. Instead, changing the fix and
watching the test's behavior not change how I expected made me stop
and actually trace *why*, which surfaced a real flaw in how I'd
modeled concurrency (one shared fake session instead of separate
sessions against a shared table). That's the kind of failure that's
invisible from the outside — a reviewer looking at a green CI run
would have no way to know the test wasn't testing what it claimed to
— and I only caught it by not fully trusting my own first pass.
>>>>>>> 0ef82c3 (fix(api): reject concurrent reviews for the same profile via DB constraint)
