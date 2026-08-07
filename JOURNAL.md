## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the POST /profiles request body schema

**Tier:** Tier 1 

**Problem summary:**
The API reference currently lists the available endpoints for creating profiles and requesting reviews, but it does not document the expected request body for either POST /profiles or POST /reviews. As a result, developers cannot determine what fields are required, what each field represents, or what a valid request should look like without inspecting the implementation. The issue affects docs/API.md. A successful fix would add the missing request body schemas, including field descriptions and example values, so the documentation provides complete guidance for both endpoints.

**Is This Issue Right for Me? Checklist Reasoning:**

I was able to explain the issue in my own words and identify a clear before-and-after outcome. Currently, docs/API.md lists the two POST endpoints without explaining the data they accept. Once the issue is complete, developers should be able to use the documentation to understand and construct valid requests for both endpoints.

I confirmed that the primary file affected is docs/API.md, and I reviewed its current Profiles and Reviews sections. I will also inspect the corresponding API routes and request models to make sure the documented fields, types, required values, and examples match the actual implementation.

This issue is labeled Tier 1, which is a realistic fit because the final change is localized to the API documentation and should not require changes across multiple application modules. Although I need to review the route and schema definitions for accuracy, the expected implementation should remain limited to one documentation file.

The issue does not appear to require a new automated test because it changes documentation rather than application behavior. Instead, I can verify the work by comparing the documented schemas against the existing request models and checking that the Markdown is readable and complete. I understand the surrounding API structure well enough to outline the work: locate the request models for POST /profiles and POST /reviews, identify their accepted fields, and add field descriptions and example request bodies to docs/API.md.

I checked the issue scope and estimated effort of two to three hours, which is realistic within the Week 8–9 timeline. I also confirmed that the issue does not list any unresolved blockers or dependencies. Based on its limited scope, clear definition of done, and Tier 1 classification, I believe this issue is an appropriate choice for me.

**Branch name:** docs/89-add-api-request-schemas

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [42baabc](https://github.com/ascherj/pathreview/commit/42baabcb02244b357f149dfab9430496cdb55896)

**Reproduction summary:**
I opened `docs/API.md` and confirmed that the `POST /profiles` and `POST /reviews` entries each contain only a single descriptive line with no request body schema, field list, or example. I then inspected `api/routes/profiles.py`, `api/routes/reviews.py`, `api/schemas/profile.py`, and `api/schemas/review.py` to identify the actual accepted fields and types. The gap is concrete: a developer reading the docs has no way to construct a valid request for either endpoint without reading the source code.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Blockers or open questions:**
`POST /profiles` uses `multipart/form-data` rather than a JSON body because it accepts a file upload. I need to confirm the best Markdown format for documenting a multipart form request (field table vs. code block) so the docs stay consistent with the existing style in `docs/API.md`.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The file API.md has been updated with the reqest body schemas of POST /profile and POST /review endpoints. I also created unit tests to verify the presence of these documentation changes. 

**Next steps:**
I will work on putting out a PR for these changes and closing the issue.

**Blockers:**
N/A

---

### Check-in 2 (end of week)

**PR link:** [[link to your submitted pull request](https://github.com/ascherj/pathreview/pull/1004)]

**Branch:** docs/89-add-api-request-schemas

**What you built:**
Added request body schemas for `POST /profiles` and `POST /reviews` to `docs/API.md`. Each entry now documents the content type, a field table with name, type, required/optional status, and constraints, and an example `curl` request. `POST /profiles` uses `multipart/form-data` with three optional fields (`github_username`, `portfolio_url`, `resume_file`); `POST /reviews` uses `application/json` with one required field (`profile_id`, UUID).

**Tests added or updated:**
`tests/unit/test_api_docs.py` — new file with 6 unit tests that assert each documented content type and field name is present in `docs/API.md`. Tests use `@pytest.mark.unit` and run as part of `make test-unit`.

**Self-review confirmation:** [ ] make check passes  [x] make test-unit passes (53 pre-existing failures unrelated to this change; 6 new tests pass)

**Draft PR feedback received from:** None

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in.

**How you responded:** N/A

---

### Reflection

**What was harder than you expected?**
I was surprised by how distributed the relevant information was across the codebase. Although the issue itself requested a documentation update to a single file, resolving it accurately required tracing the documented endpoints back through their routes and request schemas to understand their actual behavior. In particular, discovering that POST /profiles accepts multipart/form-data rather than a JSON body reinforced that I could not make assumptions based solely on the existing API documentation. The final change was relatively small, but the investigation required to make that change confidently was more involved than I expected.

**What did you learn about working in a large codebase?**
I learned that contributing to an unfamiliar codebase requires spending more time understanding existing decisions before making your own. In my own projects, I usually already know where functionality lives and why it was implemented a certain way. Here, I had to trace relationships between the documentation, routes, and request schemas before I could confidently determine what needed to change. I also learned how useful AI tools can be for navigating this process. Claude helped me locate relevant source code and understand how different parts of the repository were connected, which saved time during the issue discovery and reproduction phase without replacing the need for me to verify its findings against the codebase.

**How did AI tools help — and where did they fall short?**
AI was most useful for helping me gather my bearings in an unfamiliar codebase and for turning what I discovered into a structured execution plan. It helped me identify files worth investigating, understand relationships between different parts of the repository, and organize the steps needed to complete the issue.

At the same time, I frequently had to intervene when the agent missed relevant context or suggested intermediate steps that did not align with the established plan. This reinforced that effective AI collaboration still requires active judgment from the user. I found that the collaboration was most productive when I remained inquisitive about unexpected output, verified suggestions against the source code, and treated the plan as something I was responsible for maintaining rather than something the agent could execute unquestioned. AI helped accelerate my reasoning, but I still needed to provide the context and oversight that kept the work grounded in responsible development.

**What would you do differently if you started over?**
For my first open-source contribution, I would not change much about the issue I selected or the process I followed. Choosing a relatively contained documentation issue gave me room to focus on skills beyond implementation, such as navigating an unfamiliar repository, reproducing an issue, planning a solution, validating my changes, and preparing a contribution for review.

For my next contribution, however, I would like to choose a slightly more involved issue. Now that I have gone through the full contribution cycle once, I want to challenge the skills I established here and see how my approach to investigation, planning, AI collaboration, and implementation needs to evolve as the scope and complexity of an issue increase.


**What are you most proud of from this module?**
I am most proud of strengthening the muscle of AI + human collaboration in a way that I can see myself replicating in future open-source contributions and unfamiliar codebases. Rather than relying on AI simply to produce an answer or implementation, I became more intentional about using it to navigate, investigate, and plan while keeping myself responsible for validating its output and directing the overall process.

More broadly, completing this contribution cycle proved to me that I can enter an unfamiliar codebase, identify what I need to understand, and iteratively build enough context to make a meaningful contribution. That process is something I feel much more confident carrying into larger and more complex contributions in the future.