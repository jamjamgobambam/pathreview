# JOURNAL

## Week 7 Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the `POST /profiles` request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/API.md` lists the response shape for every endpoint but never documents what a client actually needs to send when creating a profile or requesting a review. This is confusing in practice because `POST /profiles` isn't a plain JSON request â€” it's `multipart/form-data`, since it accepts an optional resume file upload alongside `github_username` and `portfolio_url` fields, and that distinction wasn't documented anywhere. `POST /reviews` is simpler (JSON with just a `profile_id`), but it also had no documented request format. A successful fix adds field-level tables and example requests for both endpoints so a new API consumer doesn't have to read `api/routes/profiles.py` and `api/schemas/review.py` just to figure out how to call them.

**Branch name:** docs/89-post-profiles-schema

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 Reproduction & solution planning

**Reproduction commit link:** https://github.com/RithikaMathew/pathreview/commit/60fa346

**Reproduction summary:**
Ran the app locally and compared the auto-generated OpenAPI schema at `localhost:8000/docs` against the pre-fix version of `docs/API.md` (commit 888af31). Confirmed `POST /profiles` is multipart form data with an optional resume file, and `POST /reviews` is JSON with just `profile_id` â€” neither was documented before this fix.

**PLAN.md link:** https://github.com/RithikaMathew/pathreview/blob/docs/89-post-profiles-schema/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**


## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The API.md fix from Week 7 is complete - request schemas for POST /profiles and POST /reviews are documented with field tables and examples. Ran `make check` and `make test-unit` to confirm nothing broke.

**Next steps:**
Open a draft PR, get a quick peer review, then mark it ready for review.

**Blockers:**


### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/347

**Branch:** docs/89-post-profiles-schema

**What you built:**
Added request body schemas (field tables and example requests) for POST /profiles and POST /reviews to docs/API.md, which previously only documented response shapes for these endpoints.

**Tests added or updated:**
None - documentation-only change, no code paths affected. Verified make test-unit, make lint, and make typecheck all show only pre-existing failures unrelated to this change.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** Aayush

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - still awaiting review (reviewer feedback not enabled for Su26 per course note)

**Summary of feedback:**
No reviewer comments received. Aayush gave informal peer feedback on the draft PR before I marked it ready for review (documented in Week 9 Check-in 2).

**How you responded:**
N/A - no formal reviewer feedback to respond to this week.

---

### Reflection

**What was harder than you expected?**
The environment setup was the hardest part, not the actual documentation fix. I hit several separate issues in sequence: PowerShell not supporting bash heredoc syntax from the setup instructions, the Makefile's `run` target being written for bash and breaking under PowerShell, Docker Desktop not running, and then a port mismatch (the app expected 5432, but docker-compose actually maps Postgres to 5433). Each one looked like a new problem until I traced it back to its actual cause.

**What did I learn about working in a large codebase?**
I learned to isolate whether a failure is actually caused by my change or is a pre-existing issue in the codebase. When `make check` and `make test-unit` came back with dozens of failures, my first instinct was that I'd broken something - but none of the failing files were ones I'd touched, and the assignment's own guidance confirmed that's an acceptable, expected situation. I also learned to read actual source code (route handlers, pydantic schemas) instead of trusting what existing documentation claimed, since the docs were the very thing that was wrong.

**How did AI tools help - and where did they fall short?**
AI was most useful for reading through the codebase quickly - finding the right route and schema files, and translating cryptic errors (bcrypt warnings, mypy output, SQLAlchemy stack traces) into plain explanations of what was actually failing and why. It fell short anywhere that needed my own judgment or actual account-specific detail - like confirming who actually reviewed my draft PR, or deciding when a docker/network issue was actually resolved versus just quiet. I had to run commands myself and report back real output rather than assume AI's suggestions worked.

**What would I do differently if I started over?**
I would use Git Bash from the very start instead of PowerShell, since the project's own SETUP.md said to, and most of my early friction (heredocs, the Makefile) traced back to ignoring that. I'd also run `docker compose up -d` and confirm containers were healthy before attempting anything else, rather than discovering the DB connection issue reactively through a startup crash.

**What am I most proud of from this module?**
Getting the full local environment running end-to-end despite several unrelated blockers (shell mismatch, Docker not running, wrong port, bcrypt warning) - that took more troubleshooting than the actual doc fix itself, and I worked through each one methodically instead of giving up or reinstalling everything from scratch.
