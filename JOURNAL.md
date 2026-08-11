## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/89](https://github.com/ascherj/pathreview/issues/89)

**Issue title:** API reference doc is missing the `POST /profiles` request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API reference documentation in `docs/API.md` currently documents the response schemas for endpoints but does not provide details on the expected request bodies. Specifically, the request body schemas for `POST /profiles` and `POST /reviews` are missing. A successful fix will add comprehensive schemas for both endpoints to `docs/API.md`, detailing the field names, types, descriptions, and providing example JSON payloads. This affects the API documentation layer, making it complete and user-friendly for API integration.

**Selection reasoning:**
I chose this Tier 1 issue to start with because it provides a guided entry point to inspect the FastAPI schemas (`ProfileCreate` and `ReviewCreate`) and route handlers. It is a scoped fit that allows me to build confidence with the codebase layout and project setup steps before tackling deeper logic changes.

**Branch name:** docs/89-api-request-schemas

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/Natkuma01/pathreview/commit/558a2259393087c0f771103317c799848642090c](https://github.com/Natkuma01/pathreview/commit/558a2259393087c0f771103317c799848642090c)

**Reproduction summary:**
We compared the API code to `docs/API.md`. The documentation did not show the request schemas for profile and review endpoints.

**PLAN.md link:** [https://github.com/Natkuma01/pathreview/blob/docs/api-request-schemas/PLAN.md](https://github.com/Natkuma01/pathreview/blob/docs/api-request-schemas/PLAN.md)

**Walkthrough video (recommended):** [Omitted]

**Blockers or questions:**
None.

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
We checked the routes in `api/routes/profiles.py` and `api/routes/reviews.py`. We identified the missing request body schemas. We added documentation tables and payload examples for `POST /profiles` and `POST /reviews` to `docs/API.md`.

**Next steps:**
We will write unit tests to validate the schemas. We will also run our test suite to ensure everything remains stable.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/581

**Branch:** docs/89-api-request-schemas

**What you built:**
We documented the request body schemas for both profile and review creation in `docs/API.md`. We also wrote unit tests to validate these schemas.

**Tests added or updated:**
We created a new test file `tests/unit/test_api_schemas.py`. It tests validation constraints for `ProfileCreate` and `ReviewCreate` models.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in by the end of the week, so I'm moving forward with my reflection!

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Figuring out exactly where to put the tests for the schemas in the existing test structure was a bit tricky. I had to understand how the project organizes unit tests versus integration tests. Ultimately, I had to make sure my new file `test_api_schemas.py` fit perfectly into their established directory conventions.

**What did you learn about working in a large codebase?**
I learned that reading existing code and matching its style is absolutely critical. When updating the API docs in `docs/API.md`, I had to make sure my new tables and examples looked exactly like the surrounding documentation. This ensures that the documentation feels cohesive and doesn't stick out as a separate addition.

**How did AI tools help — and where did they fall short?**
AI tools were incredibly helpful for generating the exact markdown tables for the schemas and stubbing out the initial unit tests. However, they fell short when it came to understanding the nuances of the exact file structure and where things should be placed. I still had to manually review the project layout to ensure my tests went into the right directory under `tests/unit/`.

**What would you do differently if you started over?**
If I started over, I would probably spend more time initially looking at how other similar API endpoints were documented. I rushed a bit before jumping straight into writing the schemas for `POST /profiles`. Taking that extra time upfront would have definitely saved me some back-and-forth on formatting and structure later on.

**What are you most proud of from this module?**
I'm really proud of successfully adding comprehensive tests alongside the documentation. It felt great to go beyond just updating the `docs/API.md` file. By writing unit tests to validate the `ProfileCreate` and `ReviewCreate` models, I helped ensure they will stay accurate in the future!
