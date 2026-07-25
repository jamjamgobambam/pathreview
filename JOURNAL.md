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

**Reproduction commit link:** https://github.com/olusheki/pathreview/commit/f7b4e23

**Reproduction summary:**
Opened `docs/API.md` at the tip of `main` and confirmed the documentation
gap: every endpoint is listed by method and path, but none include a runnable
`curl` invocation, request body shape, auth header, or sample response — so a
developer who just ran `make setup` has no copy-pasteable way to verify the
API is responding without falling back to Swagger at `/docs`.

**PLAN.md link:** https://github.com/olusheki/pathreview/blob/docs/117-api-curl-examples/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**

