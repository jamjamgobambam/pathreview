# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `docs/API.md` reference lists every HTTP endpoint the service exposes
(health, auth, profiles, reviews) but only names the route and method — there
are no runnable examples. A developer who has just finished `make setup` has
no fast way to confirm the API is actually responding, and has to either open
the Swagger UI or reverse-engineer request bodies from the route handlers.
A successful fix adds copy-pasteable `curl` invocations for each endpoint,
including sample request bodies where relevant and a representative response,
so first-time contributors can smoke-test the API in seconds.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes ("Is this right for me?")

- **Scope:** single file (`docs/API.md`), docs-only, no code paths touched.
- **Skills fit:** requires reading route handlers to get request/response
  shapes right — good exercise in navigating an unfamiliar backend without
  the risk of breaking runtime behavior.
- **Effort:** matches the 2–3 hour estimate on the issue; realistic for a
  first contribution.
- **Blast radius:** zero — documentation change, reversible, no migrations,
  no dependencies added.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/olusheki/pathreview/commit/d81b354

**Reproduction summary:**
Opened `docs/API.md` at the tip of `main` and confirmed the documentation
gap: every endpoint is listed by method and path, but none include a runnable
`curl` invocation, request body shape, auth header, or sample response — so a
developer who just ran `make setup` has no copy-pasteable way to verify the
API is responding without falling back to Swagger at `/docs`.

**PLAN.md link:** https://github.com/olusheki/pathreview/blob/docs/117-api-curl-examples/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five PLAN.md sub-tasks are done. Read the pydantic schemas and route
handlers to lock down request/response shapes, rewrote `docs/API.md` with
inline `curl` examples under every endpoint, added a token-export snippet at
the top, and surfaced three inaccuracies the old docs had (login is
form-encoded, profile create is multipart, `PUT /profiles/{id}` and
`GET /reviews/{id}/status` were undocumented).

**Next steps:**
Add a guard test that fails if any endpoint listed in `API.md` loses its
curl example, run `make check` / `make test-unit`, open a draft PR for peer
review, then mark ready.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/NNN

**Branch:** docs/117-api-curl-examples

**What you built:**
Added runnable `curl` invocations under every endpoint in `docs/API.md` so
first-time contributors can smoke-test the API after `make setup` without
digging through Swagger. Corrected three inaccuracies (login form-encoding,
profile multipart upload, two undocumented endpoints) discovered while
verifying request shapes against the route handlers.

**Tests added or updated:**
`tests/unit/test_api_docs.py` — one `pytest.mark.unit` test that parses
`docs/API.md`, extracts every endpoint header, and asserts each has a fenced
`bash` block containing `curl`. Fails loudly if a future endpoint is added
to the doc without an example.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Pre-existing note: this environment has no `.venv` yet (setup was skipped on
this machine), so `make check` / `make test-unit` were verified by running
the guard check standalone with the stdlib. All 11 endpoints in `API.md`
have curl examples; documented in the PR description so the reviewer can
re-run in a full env.

**Draft PR feedback received from:** none (mock submission)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback arrived. Per the Su26 note, reviewer feedback isn't a
feature this cohort, and this submission was a mock PR (never opened against
`ascherj/pathreview`), so there was no upstream reviewer to respond.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Reading enough of the codebase to write *correct* docs was the real work; the
`curl` examples themselves were trivial. The old `API.md` looked innocuous,
but three of the endpoints it described were wrong in ways I only caught by
opening the route files: `POST /auth/login` uses `OAuth2PasswordRequestForm`
(form-encoded, `username` holds the email — not JSON), `POST /profiles` is
multipart with a file upload, and two endpoints (`PUT /profiles/{id}`,
`GET /reviews/{id}/status`) weren't documented at all. "Docs task" doesn't
mean "shallow task" when the existing docs aren't trustworthy.

**What did you learn about working in a large codebase?**
Conventions do more than docs. `CONTRIBUTING.md` pinned the branch name
format, the commit style, and the PR template — following those made every
step (naming, committing, opening) a mechanical choice instead of a design
question. The other lesson: pydantic schemas are the source of truth. When
you need to know the shape of a request, don't read prose about it, read the
model. Prose lies (or drifts); the model is what the server actually
enforces.

**How did AI tools help — and where did they fall short?**
AI was strongest at navigation and boilerplate: locating the right files,
summarising route/schema pairs, and drafting the PR body, JOURNAL entries,
and PLAN.md from a rough spec. Where it fell short was judgment — deciding
whether the three "extras" I found (form-encoding fix, multipart fix, two
undocumented endpoints) belonged in a #117 PR or a follow-up was a scope
call that needed me. AI will happily expand scope if you don't push back;
"the fewest files that solve the ticket" is a discipline you have to bring.

**What would you do differently if you started over?**
Open the draft PR after the first commit, not after everything is polished.
The Week 9 instructions push for early drafts precisely because a PR title
and body force you to articulate the change before the diff is
irreversible-feeling — I'd get that pressure on day one instead of day five.

**What are you most proud of from this module?**
The guard test in `tests/unit/test_api_docs.py`. It's ~20 lines of stdlib,
no fixtures, no imports from the project, and it makes the #117 fix
self-enforcing: the next contributor who adds an endpoint to `API.md`
without a `curl` example will see the test fail before their PR merges.
Small, cheap, and it prevents the exact regression this issue existed for.

