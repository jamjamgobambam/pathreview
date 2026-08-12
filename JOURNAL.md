## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API.md file lists the endpoints (health, auth, profiles, reviews) but
doesn't give any example curl commands. So if you just finished setup and
want to check that the API works, you kinda have to open Swagger or dig
through the code. The fix is to add real curl examples people can paste in
after `make run`, including auth headers and sample bodies where needed.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Got the curl examples written for issue #117 — auth, profiles, reviews
(including polling), pagination, and cleanup. Docs are mostly in place.

**Next steps:**
Double-check the commands against the actual routes, run the project
checks, and get the PR ready to submit.

**Blockers:**
`make check` and `make test-unit` already fail in this repo. My change is
docs-only so I'm not touching those files, but it makes the checkboxes
awkward.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/354

**Branch:** `docs/117-api-curl-examples`

**What you built:**
Updated `docs/API.md` so it's actually usable. Added setup vars, how to
grab the token and IDs, examples for each public endpoint, notes on JSON
vs form vs multipart, review polling, and cleanup at the end.

**Tests added or updated:**
No app code changed. I checked the examples against the FastAPI route
files and ran `zsh -n` on the bash blocks so they at least parse.

**Self-review confirmation:** [x] `make check` introduces no new failures  [x] `make test-unit` introduces no new failures

`make check` still has 35 lint/type errors and `make test-unit` has 89
failures — all in other files, not from this docs change.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
Nothing on my PR yet (https://github.com/ascherj/pathreview/pull/354).
The course said Su26 doesn't really do reviewer feedback anyway, so I'm
not surprised. PR is still open with the #117 docs changes.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Honestly the local setup stressed me more than writing the docs. I got
the app running at localhost:5173 fine, but `/health` kept saying
Postgres and Redis were down even though they weren't — turns out the
health check code itself is buggy. Also `make check` / `make test-unit`
fail all over the place for stuff I didn't touch, so I couldn't just
rely on "all green." And I thought login would be JSON like register,
but it's form data with `username`/`password`. Had to read the route
files to figure that out.

**What did you learn about working in a large codebase?**
When it's your own project you already know how things work. Here I had
to go look at `api/routes` and the schemas because the old API.md was
too thin to trust. Stuff like which calls need a bearer token, or that
reviews come back pending and you have to poll, isn't obvious from a
one-line description. Also #117 had a ton of people claiming it, so I
learned that picking an issue isn't only about difficulty — if half the
class wants the same one, that matters too.

**How did AI tools help — and where did they fall short?**
AI helped a lot with the boring orientation stuff — reading SETUP,
branch naming, sketching a plan, and drafting curl once I knew the
shapes. Where it was less useful: when the repo was inconsistent (health
503 but app works, tests already broken, login not JSON). I still had to
open the Python files and try things myself. Also I didn't want the PR
to pretend tests passed when they didn't — that felt like something I
had to decide, not something to outsource.

**What would you do differently if you started over?**
I'd check how crowded the issue was before locking in. #117 was popular
and there are a bunch of similar PRs. I'd also try harder to run every
curl live while Docker was working, instead of falling back to
"compare against the route source" when Desktop wasn't available. And
I'd mention the `/health` 503 quirk earlier so nobody thinks their setup
is broken when it isn't.

**What are you most proud of from this module?**
That someone can open API.md and actually walk through the API in the
terminal now — get a token, hit the endpoints, poll a review, clean up —
without living in Swagger. Feels like a real improvement even though it
was "just docs." Keeping the journal updated each week also helped me
remember what I actually ran into instead of only remembering the PR
link.
