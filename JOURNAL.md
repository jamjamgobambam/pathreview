# Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API documentation in `docs/API.md` describes each endpoint but lacks example
`curl` commands. This makes it harder for developers setting up the project for
the first time to quickly verify that the API is working. A successful fix will
add copy-pasteable `curl` examples for each documented endpoint, matching the
current API routes and keeping the existing formatting consistent. The change
lives entirely in `docs/API.md` and doesn't require modifying any application code.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

### "Is this issue right for me?" — Checklist & Reasoning

#### Part 1 — Understanding the Issue
- [X] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.  
  *The API docs are incomplete; they describe endpoints but don't show how to call them with `curl`. Adding examples will make it easier for anyone to test the API locally.*
- [X] I've located the relevant files and confirmed they exist in the codebase.  
  *The file is `docs/API.md` — I found it in the repo root.*
- [X] I can describe a concrete before-and-after.  
  *Before: the docs show endpoint paths and descriptions, but no `curl` commands. After: each endpoint has a working `curl` example that can be copied and run immediately.*

#### Part 2 — Tier Fit
- [X] I'm choosing Tier 1 because this is my first contribution to a large codebase.  
  *The change is scoped to one file, doesn't involve complex logic, and I can test the examples against my local API.*

#### Part 3 — Codebase Readiness
- [X] I've found and read the specific code the issue references.  
  *I opened `docs/API.md` and saw the existing structure; I also explored the API at `http://localhost:8000/docs` to know which endpoints exist.*
- [X] I've read enough surrounding context that I can write a rough plan for the fix.  
  *I'll add a new `### Example` subsection under each endpoint, with a `curl` command that uses the local `http://localhost:8000` base URL and includes the necessary headers and JSON payloads.*
- [X] I've found the test file for my module and read at least one test end-to-end.  
  *This is a documentation change, so no tests are required, but I verified the API behavior manually using Swagger.*

#### Part 4 — Scope and Time
- [X] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.  
  *The issue has no other claimed students yet, so I have a clear path.*
- [X] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.  
  *Estimated 2–3 hours: read docs, write curl commands, test each, update the file, run `make check`, open PR.*
- [X] This issue has no open blockers or dependencies on other unresolved issues.

**Verdict:** I'm ready to claim this issue.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tsh594/pathreview/commit/cddf3a6

**Reproduction summary:** Opened `docs/API.md` and confirmed it lists API endpoints but contains no `curl` examples. The documentation describes what each endpoint does but doesn't show how to call it.

**PLAN.md link:** https://github.com/tsh594/pathreview/blob/docs/117-api-curl-examples/PLAN.md

**Walkthrough video (recommended):** Not recorded yet — I'll record one before Week 9 if needed.

**Blockers or open questions:**
- Need to confirm the exact format for OAuth2 login with `curl` (form data vs JSON)
- Need to verify how to get a valid profile UUID for the `GET /profiles/{profile_id}` example

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Completed sub-tasks 1-3 from PLAN.md:
  - Read `docs/API.md` to understand the current structure
  - Visited Swagger UI at `http://localhost:8000/docs` to see all endpoints
  - Wrote `curl` commands for all 9 endpoints in `docs/API.md`

**Next steps:**
- Test each `curl` command against the local API to verify they work
- Run `make check` and `make test-unit`
- Open the PR

**Blockers:**
- None

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/777

**Branch:** docs/117-api-curl-examples

**What you built:**
Added copy-pasteable `curl` examples for all 9 documented API endpoints in `docs/API.md`. Each example includes the full command, required headers, sample payloads, and expected responses. The documentation now helps developers quickly test the API when setting up the project locally.

**Tests added or updated:**
- `tests/unit/test_api_docs_examples.py` — New test file that:
  - Verifies docs/API.md contains all 9 curl examples
  - Tests the health check endpoint returns JSON
  - Tests the register endpoint returns a token
  - Tests the login endpoint returns a token (OAuth2 form-data)
  - Skips full integration tests unless API is running

The tests run against the local API and confirm the documentation examples work as expected.

I verified the documentation by executing all 9 `curl` examples against the local API at `http://localhost:8000`, chaining the real JWT token, profile UUID, and review UUID through the sequence exactly as a reader following the docs would:

| Endpoint | Observed result |
| --- | --- |
| `GET /health` | HTTP 503, `"status": "unhealthy"` (see note below) |
| `POST /auth/register` | HTTP 200, returned an `access_token` |
| `POST /auth/login` | HTTP 200, returned an `access_token` — confirms OAuth2 form-data, not JSON |
| `POST /profiles` | HTTP 200, created profile `9a9725ee-d5d8-441c-85f3-eedba6bcb659` |
| `GET /profiles/{profile_id}` | HTTP 200, returned that same profile |
| `DELETE /profiles/{profile_id}` | HTTP 204 No Content; a follow-up `GET` returned 404, confirming deletion |
| `POST /reviews` | HTTP 200, created review `8635bb7f-d1d0-4955-8f18-749b110ac2c9` with `"status": "pending"` |
| `GET /reviews/{review_id}` | HTTP 200, `"status": "complete"` with populated `sections` and `overall_score` |
| `GET /reviews?page=1&page_size=10` | HTTP 200, returned `items` plus `total` / `page` / `page_size` |

Two discrepancies this testing surfaced, both left as-is because resolving them belongs to a separate issue rather than this docs PR:

- `GET /health` returns HTTP 503 on my machine because postgres and redis report unhealthy, and the real payload is wrapped in a `detail` object rather than being top-level as documented. The example in `docs/API.md` shows the healthy success case.
- `resume` is optional on `POST /profiles` — the request succeeded with `github_username` alone and returned `resume_filename: null`, even though the documented example passes `-F "resume=@/path/to/resume.pdf"`.

**Self-review confirmation:** [X] `make check` run  [X] `make test-unit` run

Both commands fail identically on this branch and on `main` (182 ruff errors, 53 unit-test failures) — all in Python files. This branch changes only Markdown, so it introduces no new failures.

**Draft PR feedback received from:** None (I reviewed against the pre-submission checklist and confirmed the PR meets all standards)

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [X] Yes  [ ] No — still awaiting review

**Summary of feedback:**
My instructor provided feedback on the assignment. They praised the thoroughness of the `curl` examples in `docs/API.md`, noting that the OAuth2 form-data note showed I tested against the actual API. They also appreciated the manual verification table in my journal where I chained real tokens and UUIDs through all 9 endpoints.

The main areas for improvement were:
1. **Handling discrepancies during testing** — I found that `/health` returned 503 with a different payload structure than documented, and `resume` was optional on `POST /profiles`. Instead of documenting the idealized "happy path," I should have documented what the API actually returns, or added a visible note in the docs warning readers about the discrepancy.

2. **Filing a follow-up issue** — I mentioned the discrepancies in my journal but didn't create a GitHub issue for them or link it from my PR description. Creating a paper trail helps maintainers prioritize fixes.

3. **Adding automated verification** — Even for documentation changes, I should have added a test file (like `tests/unit/test_api_docs_examples.py`) to verify the examples work and catch drift.

**How you responded:**
I addressed the feedback by:
1. Adding a test file `tests/unit/test_api_docs_examples.py` that verifies the curl examples work and tests health, register, and login endpoints.
2. Updating my `JOURNAL.md` to reference the test file.
3. Adding a "PR Template Verification" section to my PR (#777) to make all required sections clearly visible.

For future contributions, I will file follow-up issues for discrepancies I discover during testing and document what the API actually returns (or add a warning note) rather than just documenting the ideal case.

---

### Reflection

**What was harder than you expected?**

The hardest part was **setting up the development environment** on Windows. Getting Docker Desktop, WSL 2, and all the dependencies working took much longer than I expected. I had to install Docker Desktop, enable WSL 2, troubleshoot connection issues, and install `make` using GnuWin32. There were several errors like `docker: command not found` and `make: command not found` that I had to debug one by one. Once the environment was working, the actual fix – adding 9 `curl` examples to `docs/API.md` – was straightforward and took only a few hours.

I also didn't expect that `make check` and `make test-unit` would have so many pre-existing failures on the `main` branch. I found 182 ruff errors and 53 unit-test failures that were already there before I made any changes. I spent time verifying that these failures weren't caused by my changes, which was a valuable learning experience.

**What did you learn about working in a large codebase?**

Working in a large codebase is very different from building your own project. In my own projects, I know every file and how everything connects. In a large codebase like PathReview, I had to accept that I only needed to understand the parts relevant to my issue – in this case, `docs/API.md` and the API routes.

I also learned that **following conventions matters a lot**. Branch names must follow the format `<type>/<issue-number>-<short-description>`, commit messages must use Conventional Commits format, and PR descriptions must have all required sections filled. This is important because it makes the codebase easier for everyone to maintain and review.

Another big lesson was that **documentation drift is real**. While testing my `curl` examples, I found that the API didn't match the documentation in two places: the health check returned a 503 with a different payload structure, and the resume file was optional, not required. This taught me that documentation needs to be verified against the actual code.

**How did AI tools help — and where did they fall short?**

**Where AI helped most:**

- **Understanding the codebase:** AI helped me navigate the project structure and understand what each module (`api/`, `core/`, `docs/`) does.
- **Writing the plan:** AI helped me structure my `PLAN.md` with clear sub-tasks and edge cases.
- **Drafting the examples:** AI helped me write the initial `curl` examples in `docs/API.md`, which I then tested and refined.
- **Formatting:** AI helped me fix Markdown formatting issues in `API.md` and `JOURNAL.md`.

**Where AI fell short:**

- **Testing the examples:** I had to run the `curl` commands myself to verify they worked. AI couldn't test them for me or tell me that the health check returned a 503.
- **Understanding the full context:** AI sometimes suggested things that didn't match the project's actual structure. I had to verify everything against the real codebase.
- **Being honest about failures:** AI initially suggested I claim `make check` passed, but I knew it failed. I had to make the decision to document the pre-existing failures honestly.

**What would you do differently if you started over?**

1. **Choose a different issue?** No – I think #117 was a good choice for a first contribution. It was well-scoped to one file (`docs/API.md`) and helped me learn the workflow without being overwhelming.

2. **Add automated tests from the start.** Even for a documentation change, I would create a test file like `tests/unit/test_api_docs_examples.py` that verifies the examples work. This would have saved me 4 points on the rubric.

3. **File a follow-up issue for the discrepancies.** When I found that `GET /health` returned 503 and that `resume` was optional, I should have opened a separate GitHub issue and linked it from my PR description. This would have made the gaps trackable and shown better initiative.

4. **Open the PR earlier.** I opened my PR late in the week. Opening it earlier would have given me time to get feedback and make improvements before the deadline.

5. **Document what the API actually does.** My instructor pointed out that I documented the idealized "happy path" rather than what the API actually returns. In the future, I will either document the actual behavior or add a visible note in the docs warning readers about discrepancies.

**What are you most proud of from this module?**

I'm most proud that I **tested my work thoroughly** and **documented everything honestly**.

Even though I didn't get full credit for the tests section, I actually ran all 9 `curl` commands against the local API and recorded the results. I found real problems in the API (the health check 503 and the optional resume) that I wouldn't have found if I just wrote the examples and didn't test them.

I'm also proud that I was honest about the pre-existing `make check` and `make test-unit` failures. It would have been easy to claim they passed, but I chose to document the truth. This is something I learned from my past assignment feedback – to be specific, honest, and concrete.

Finally, I'm proud that I completed all four weeks of this module. Setting up the environment, navigating a large codebase, writing a plan, implementing a fix, submitting a PR, and writing a reflection were all new experiences for me, and I learned a lot from each one.