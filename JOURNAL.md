## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/129

**Issue title:** Add a database migration validation step to CI that checks all migrations can be applied cleanly #129

**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
The current issue is that CI doesn't validate database migrations at all, so a broken migration — or one that applies cleanly but leaves the schema out of sync with the SQLAlchemy models — can reach `main` with a passing build and only surface later at runtime. What I need to add is a validation step that runs when CI runs: it should apply the current migration and all prior ones from start to finish against a fresh database, then confirm the resulting schema matches what's defined in the models. A successful fix means either failure (a migration that won't apply or that drifts from the models) turns the build red on the pull request instead of slipping through. The files relevant to this are `.github/workflows/ci.yml` and `scripts/validate_migrations.sh`, which I'll work in to add the automated validation pipeline. 

**Problem Scope:** This problem is right for me because it is quite challenging and deals with cross-cutting concerns which I think I have the skillset for. Furthermore, I will have the time to commit to a PR of this difficulty and scale. With all of this in mind, I believe that a problem of this score is well within my skillset and a good fit for me to tackle. 

**Branch name:** `chore/129-migration-validation-ci`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Louis-Barbosa/pathreview/commit/6f6b982


**Reproduction summary:**
To reproduce the issue, I added migration `003`, which is deliberately broken (it renames `reviews.error_message`, drifting the schema away from the SQLAlchemy model). No CI job or script verifies migrations, so the broken migration passes with a green build and is allowed to reach main.


**PLAN.md link:** https://github.com/Louis-Barbosa/pathreview/blob/chore/129-migration-validation-ci/PLAN.md


**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
So far I have created and implemented the validation script: `scripts/validate_migrations.sh` which essentially uses `alembic upgrade head` to run every migration in order and then `alembic check` to compare the finished database against the code's models. I also included a `migrations` job in `.github/workflows/ci.yml` to run the script anytime a job starts a throwaway PostgreSQL database. This makes it so that the check will run automatically on every pull request.

**Next steps:**
For the rest of the week I am going to be testing to make sure that it functions properly and is not breaking any systems. This means that I will likely build a test script to ensure that it works and to provide proof in the PR that it is functional. Furthermore, I will remove any old broken migrations that I used to test how the system was broken. This is simply because I want my PR to be clean and leaving a broken migration can be confusing. 

**Blockers:**
N/A

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/181

**Branch:** `chore/129-migration-validation-ci`

**What you built:**
I built a CI migration-validation step. The file `scripts/validate_migrations.sh` applies every migration to a fresh, empty database (`alembic upgrade head`) and then confirms the resulting schema matches the SQLAlchemy models (`alembic check`), failing the build if a migration is broken or the schema has drifted. A new `migrations` job in `.github/workflows/ci.yml` runs the script against a throwaway PostgreSQL service on every pull request, essentially automating the check. While validating, the check surfaced a real pre-existing drift — migration `001` created a redundant `uq_users_email` unique constraint the models don't declare — which I fixed with a new migration `003`, then removed the deliberately-broken reproduction migration.

**Tests added or updated:**
I added `tests/unit/test_migrations.py` — static checks over the migration history (no database required): exactly one base revision, exactly one head, and every `down_revision` points to a known revision. These guard the single-linear-history invariant the CI job relies on (e.g. the multiple-heads case that would make `upgrade head` ambiguous). Verified the script itself end-to-end against a local Postgres container: it fails with the broken migration present and passes once the repo is clean.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**
No feedback was given.

---

### Reflection

**What was harder than you expected?**
What I found to be much harder than expected was understanding the how the internsection between the codebase and the workflow functioned. To be able to write the script that would verify the migrations I needed to understand how the codebase configuration was handling its drivers and variables. This was already challenging to understand but was necessary as understanding how to build the script was dependant on how well my codebase understanding was. 

**What did you learn about working in a large codebase?**
Working with a larger codebase is vastly different from just working on your own project. With your own project its much easier to firstly understand what is being built since you are building it presumably from scratch but also you are allowed to be more dynamic with what is added to the project since you are in complete control of its concept and direction. Working on someone else's production instead requires you to understand the workflow and the scripts that are being used. This means that it requires much more time to read and understand what exactly you are working with. Also, since it is not your project whatever you want to contribute is usually a problem already flagged so that it could be fixed or you are working within the confines of the owner's ideas. 

**How did AI tools help — and where did they fall short?**
I think that AI assistance was most useful in terms of understanding the pre-existing workflow and scripts. Esspecially since I primarily use claude code, it is able to go through all the files and give me a better explanation of how every file interacts than may be provided in the `README.md`. However, this doesn't mean that it replaces reading the files themselves and taking sometime to understand how certain scripts interact. Many times that are comments left by the codebase's owner that are worth reading yourself. I do think that is one instance where you may still want to use AI initially for the broad stroke ideas and then go in and read the files yourself. I also think for understanding things the SQLAlchemy or Alembic using other resources beyond AI was extremely crucial and helpful. 

**What would you do differently if you started over?**
If I were to start over, I think that I would focus differently in testing. I think that I could've produced a better tests script for the `scripts/validate_migrations.sh` since they currently only focus on structural invariants. Next time I would create a script that also focuses on capturing end-to-end verification in one repeatable step. I'd also like to improve upon my planning. I think I would've liked to have a more thorough `PLAN.md`. I just feel that by having a more thorough plan I could understand my goals and how I was planning to accomplish these goals. What I mean by this is that instead of just saying "Write `scripts/validate_migrations.sh`. It reads the `DATABASE_URL` from the environment and runs, in order: `alembic upgrade head` (applies all migrations, fails if one is broken), and `alembic check` (compares the schema to the models and fails if there's drift)" I will instead be more descriptive and say more specifically it will read `DATABASE_URL`. A more descriptive plan will simply be better since it will allow me to remember intricate details of the plan even if I step away from it for a few days. 

**What are you most proud of from this module?**
I think that I am most proud of my implementation. This is because a lot of the concepts and tools used in the workflow were unfamiliar to me and so I did have to take the time to learn them. Despite the challenge of learning these concepts, I was still able to develop a solid contribution that is fully functional. I am most proud of my ability to adapt to the challenges that I wasn't necissarly expecting with the workflow and being able to produce a good script. 
