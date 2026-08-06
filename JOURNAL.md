# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands

**Tier:** ☑ Tier 1 ☐ Tier 2 ☐ Tier 3

**Problem summary:**

The API documentation currently explains the available endpoints but 
doesn't provide example `curl` commands that developers can copy and 
run. This makes it harder for new contributors to quickly verify that 
the API is working after setting up the project locally. The missing 
examples are located in `docs/API.md` and affect developer onboarding 
rather than application functionality. A successful fix will add clear 
curl examples for the documented endpoints so users can test the API 
more easily.

**"Is this right for me?" checklist reasoning:**

I selected this issue because it is a Tier 1 documentation task with a 
clearly defined scope. It only requires updating the API documentation 
without changing application logic, making it a good first contribution 
to the project. I reviewed the existing documentation and confirmed the 
missing examples before choosing this issue.

**Branch name:** `docs/117-api-curl-examples`

**Setup confirmation:** ☑ App runs locally at `http://localhost:5173`

**Cohort ledger:** ☐ Issue added to cohort ledger (will update after 
adding my information)

## Selection reasoning

### Part 1 — Understanding the Issue

- I can explain the issue: The API documentation lists endpoints but 
does not show example curl commands. The goal is to improve docs/API.md 
by adding runnable examples.
- Affected area: This issue affects the documentation layer. The 
referenced file is docs/API.md.
- Definition of done: Developers should be able to copy the curl 
commands from the documentation and use them to test API endpoints.

### Part 2 — Tier Fit

- Tier: Tier 1
- Reason: This is a small documentation change limited to one file and 
does not require changes to application logic.
- This scope is appropriate for my first open-source contribution.

### Part 3 — Codebase Readiness

- I located the affected file: docs/API.md.
- I reviewed the existing API documentation structure and understand 
where examples should be added.
- I will verify examples against the available endpoints and local API 
setup.

### Part 4 — Scope and Time

- I reviewed issue comments and confirmed other contributors are working 
on similar tasks, but claims are non-exclusive.
- Estimated effort: 2–3 hours, which fits within Weeks 8–9.
- No blockers or dependencies were listed on the issue.

### Verdict

This issue is a good fit because it is a focused Tier 1 documentation 
improvement with clear acceptance criteria.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
(To be added after committing)
https://github.com/Williyam30/pathreview/commit/a83fd91

**Reproduction summary:**

I opened docs/API.md and confirmed that each API endpoint is described 
only with text. There are no example curl commands demonstrating how to 
call the endpoints, making it difficult for new developers to verify the 
API is working locally.

I compared the documentation in docs/API.md with the implementation in 
the API route files. I found that while the endpoints are listed, the 
documentation does not explain the correct request formats. For example, 
/auth/login uses OAuth2PasswordRequestForm, which requires 
application/x-www-form-urlencoded data instead of JSON, and profile 
creation accepts form data rather than a simple JSON body. Without 
runnable curl examples, developers are likely to send incorrect requests 
when testing the API.

**PLAN.md link:**
(To be added after PLAN.md is committed)
https://github.com/Williyam30/pathreview/blob/docs/117-api-curl-examples/PLAN.md

**Walkthrough video (recommended):**
Not recorded for now but will do a final video after all.

**Blockers or open questions:**
Need to verify request bodies for authentication and profile creation 
before writing examples.


---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I implemented the main documentation update from my PLAN.md by adding 
runnable curl examples to `docs/API.md`. I added examples for all API 
endpoints including health checks, authentication, profiles, and 
reviews. During implementation, I verified request formats from the 
FastAPI route files, including JSON payloads for registration and 
reviews, form-encoded login requests using OAuth2PasswordRequestForm, 
and multipart form data for profile creation with resume uploads.

**Next steps:**

I will review the updated documentation for accuracy, run the required 
project checks, and prepare a pull request. I will also verify that the 
curl examples work correctly with the local API server and complete the 
final JOURNAL.md submission update with the PR link.

**Blockers:**

None.

### Pull Request

**PR link:**
https://github.com/ascherj/pathreview/pull/595

**PR status:**
Open

**Validation notes:**
- `make test-unit` fails due to existing unrelated failures.
- `make check` fails due to existing lint issues unrelated to 
documentation changes.


### Check-in 2 (end of week)

**PR link:**
https://github.com/ascherj/pathreview/pull/595

**Branch:**
`docs/117-api-curl-examples`

**What you built:**
I updated the API documentation by adding copy-paste curl examples for 
the documented endpoints, including health checks, authentication, 
profile, and review endpoints. The goal was to make it easier for 
developers to test the API locally and understand the required request 
formats.

**Tests added or updated:**
No tests were added or updated because this was a documentation-only 
contribution. No application code was modified.

**Self-review confirmation:**
[ ] make check passes (fails due to documented pre-existing lint issues 
unrelated to this documentation change)
[ ] make test-unit passes (fails due to documented pre-existing failures 
in security, RAG, parsing, and detection modules)

**Draft PR feedback received from:**
none

**Additional notes:**
I was unable to attend the final review calls due to an emergency 
situation, so I did not receive peer review feedback before submitting 
the PR. The PR was still completed, validated, and submitted with 
documented test and lint results.



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer or maintainer feedback was received before the course 
deadline. The pull request remains open and is awaiting review.

**How you responded:**

No response was required because no review comments were received.

---

### Reflection

**What was harder than you expected?**

The most challenging part was understanding a large existing codebase 
before making even a small documentation change. Although my task only 
involved adding curl examples to the API documentation, I still needed 
to inspect the authentication routes, profile endpoints, request 
formats, and existing documentation structure to make sure every example 
matched the actual implementation. Learning how an unfamiliar project is 
organized took much more time than writing the documentation itself.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing project is very different 
from building my own projects. Instead of deciding everything myself, I 
had to follow the repository's structure, coding standards, branch 
naming conventions, commit message style, and contribution process. I 
also learned the importance of reading documentation first and verifying 
how features actually work before making changes.

**How did AI tools help — and where did they fall short?**

AI was very helpful for understanding unfamiliar files, explaining how 
different API endpoints worked, and helping me prepare documentation and 
my pull request. However, AI could not replace manually verifying the 
repository or checking whether examples matched the implementation. I 
still needed to review the code, confirm request formats, run project 
commands, and ensure the documentation was accurate.

**What would you do differently if you started over?**

If I started over, I would claim an issue and open a draft pull request 
earlier. I would also spend more time exploring the repository before 
beginning implementation so I could understand how different parts of 
the project fit together. This would make the implementation process 
smoother and leave more time for review and feedback.

**What are you most proud of from this module?**

I am most proud that I completed my first open-source contribution from 
start to finish. I successfully selected an issue, investigated the 
project, planned the solution, updated the documentation, submitted a 
pull request, and documented the entire development process using 
professional Git and GitHub workflows.
