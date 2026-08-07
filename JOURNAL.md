## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/89)

**Issue title:** API reference doc is missing the POST /profiles request body schema

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that there is documentation missing for the POST /profiles endpoint, specifically the request body schema. The bug was recreated via `localhost:8000/docs` as the schema was nowhere to be found. A successful fix would document the multipart form fields the endpoint actually accepts — `github_username`, `portfolio_url`, and `resume_file` — along with their types and constraints, since the endpoint uses `Form` and `File` parameters rather than a JSON body. The affected part of the codebase is in `docs/API.md`.

**Branch name:** docs/89-add-missing-request-body-schema

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Issue fit and selection reasoning:**
[X] "Is this right for me?" checklist reviewed

I know that Tier 1 is right for me because it's my first open source contribution. I know what fixes to make, and I know what done looks like based on the other examples of a complete API schema. There is a good number of people that also chose this issue, but I don't have a problem with that. Also, based on the hours I am able to commit for this project, 3–6 hours is sufficient especially since I have a lot of other stuff going on during these last few weeks. The only dependency is that I should check if the code for the POST /profiles endpoint is complete before writing the reference doc.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue](https://github.com/ayc325/pathreview/commit/8993fa22e63ba9aa98ea4a4d09facadd49aea3ba)

**Reproduction summary:**
I ran the app locally and opened the interactive API docs at `localhost:8000/docs`, then navigated to the `POST /profiles` endpoint. I observed that the endpoint's request body section did not list the expected schema (the `github_username`, `portfolio_url`, and `resume_file` multipart form fields), confirming that `docs/API.md` is missing this documentation and needs to be updated to match the actual `Form`/`File` parameters accepted by the endpoint.

**PLAN.md link:** [PLAN.md](https://github.com/ayc325/pathreview/blob/docs/89-add-missing-request-body-schema/PLAN.md)

**Walkthrough video (recommended):** Skipped — not part of the grade, and the reproduction commit + PLAN.md already capture what the video would have covered:

- Reproduced the missing schema by hitting `localhost:8000/docs` and confirming `POST /profiles` shows no request body schema.
- Walked through the planned fix: document the three actual fields (`github_username`, `portfolio_url`, `resume_file`) and their constraints in `docs/API.md`, based on `api/routes/profiles.py` and `api/schemas/profile.py`.
- Happy to do a live walkthrough in office hours instead if early feedback would help before I start building.

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1–3 from PLAN.md are done. I added the request body schema table for `POST /profiles` to `docs/API.md` (fields, types, required/optional, constraints), plus a note on the resume file type check and a known-bug note for the oversized-field `500` error I found while verifying against the live server. I also drafted a PR description in `PLAN.md`.

**Next steps:**
Sub-tasks 4 & 5 — add the example request/response to `docs/API.md`, then do a final verification pass (re-check the doc against Swagger UI and re-run `make test-unit`/`make check` to confirm no new failures) and lint the markdown before committing.

**Blockers:**
None so far.

---

### Check-in 2 (end of week)

**PR link:** [PR 426](https://github.com/ascherj/pathreview/pull/426)

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`] `docs/89-add-missing-request-body-schema`

**What you built:**
I added the missing request body documentation for `POST /profiles` to `docs/API.md` — a schema table covering all three fields (`github_username`, `portfolio_url`, `resume_file`), their types, optionality, and constraints, plus notes on the resume file-type validation and a known bug I found while verifying against the live server (oversized fields return a `500` instead of the expected `422`). I also added an example request/response so the doc is usable on its own.

**Tests added or updated:**
Added `tests/unit/test_openapi_schema.py` — a regression test that calls `app.openapi()` directly and asserts `POST /profiles`'s generated schema still exposes `github_username`, `portfolio_url`, and `resume_file`. It's meant to catch the schema silently drifting out of sync with `docs/API.md` if someone renames or removes a field later.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"] Dennis Lam 

-- 

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
Reviewer just said it looks good and that it was great that I pointed out a bug found from working on the issue for docs.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
I did not need to make any changes since I had already pointed out the bug in the PR summary.

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
It was harder than expected in terms of documentation. I thought that the documentation update would be just the README update, but it was actually an api schema documentation update that had to be reflected on the swagger ui. In short, the scope of the project was different than what I thought and it suprised me.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
I learned that it's ok not to know everything about the codebase. I just need to know how my portion of the project works in the grand scheme of the project. For this project, I utilized reading over the `API.md` and `ARCHITECTURE.md` in order to understand the general project and how the API specs documentation should be written. Since this specific issue was regarding the POST /profiles, I also did more of a deep dive into the `profile.py` file and focused less on the other files since I didn't need to know the other parts of the code as much to complete my issue.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
The AI Tools helped in terms of refining the API specs documentation that I had already written up by hand. Specifically, I took what I had, gave the AI my documentation, `API.md`, `ARCHITECTURE.md` and the grading rubric and had it fill in any lackluster portions of my api documentation.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
If I started over, I would not have chosen a documentation based issue. I would've chosen a bug issue. Documentation issues are hard to test besides just testing if the documentation is being displayed on the swagger ui. A bug issue has more clear right/wrong in terms of testing, so I would've gone for that. In addition, documentation based issues actually take a bit more understanding of the design of the project because there is no strict right/wrong test case that can be written for it.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I am most proud that I was able to complete the project because I was very busy these past few weeks. I am proud that I made it through and completed it and still managed to learn great git commit techniques, prompt engineering methods, and documentation.
