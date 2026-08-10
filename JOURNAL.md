## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the POST /profiles request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API reference doc (docs/API.md) lists the POST /profiles endpoint but only gives a one-line description with no request body details. Looking at the actual route in api/routes/profiles.py, the endpoint accepts three optional fields — github_username, portfolio_url, and resume_file — sent as multipart/form-data rather than JSON, since resume_file is a file upload. None of that is documented, so a developer reading the API reference has no way to know what to actually send without opening the code or the Swagger UI themselves. The fix is to update the POST /profiles entry in API.md to list each field, its type, whether it's optional, and the multipart/form-data content type.

**Branch name:** docs/89-profiles-request-body-schema

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger



**Selection notes:**
I initially looked at #97, #87, and #101. #87 was Tier 3 (new webhook infrastructure) 
and #97 turned out to be Tier 3 as well, despite reading like a smaller frontend fix — 
its label was the deciding factor. #101 was Tier 2. Since this is my first open source 
contribution, the checklist says to stick with Tier 1, so I went back to the tracker 
filtered by tier-1 and found #89. It's confined to one doc file, has a clear before/after 
(missing schema vs. documented schema), and I confirmed the actual request body by reading 
api/routes/profiles.py before claiming it.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AliceInWonderland61/pathreview/commit/96ebed43cdd8394b1fa270aef3e6911a2f470a7a

**Reproduction summary:**
Confirmed `docs/API.md` documents no request body schema for `POST /profiles`
by reading `api/routes/profiles.py` — the endpoint actually expects
`multipart/form-data` with three optional fields, one of which is a file
upload with its own validation. Committed a note in `docs/API.md` marking
exactly what's missing.

**PLAN.md link:** https://github.com/AliceInWonderland61/pathreview/blob/docs/89-profiles-request-body-schema/PLAN.md


**Blockers or open questions:**
Issue #89 mentions both POST /profiles and POST /reviews, but I scoped this
to /profiles only, matching the issue title — flagged in PLAN.md's Risks
section.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md — updated the `POST /profiles` entry in
`docs/API.md` with the full request schema: content type
(`multipart/form-data`), a field table (github_username, portfolio_url,
resume_file with types and required/optional status), an example curl
request, and the 422 error case for invalid resume file types. Ran
`make check` and `make test-unit` before and after my change to confirm
I introduced no new failures.

**Next steps:**
Open a draft PR and get feedback from a peer or mentor in Slack before
marking it ready for review.

**Blockers:**
None at them moment. 


### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/830

**Branch:** docs/89-profiles-request-body-schema

**What you built:**
Added the missing request body schema for POST /profiles to docs/API.md —
content type (multipart/form-data), a field table (github_username,
portfolio_url, resume_file with types and required/optional status), an
example curl request, and the 422 error case for invalid resume file types.

**Tests added or updated:**
None — docs-only change, no testable code. Ran `make check` and
`make test-unit` before and after to confirm no new failures (182
pre-existing lint errors, 53 pre-existing test failures, both unrelated to
this change).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** no one answered, but that's on me I asked a bit too late


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
Reviewer praised the completeness of the PR template and the specificity
of my Testing section notes on pre-existing failures. Suggested
improvements: make the PR title more specific, expand the Summary section
to explain why the schema matters for developers/users, explicitly write
"N/A — <reason>" in empty sections instead of leaving them blank, and —
for future issues — reach out to the issue creator if the title and
description scope mismatch, rather than silently picking one
interpretation.

**How you responded:**
Replied on the PR thanking the reviewer, then updated the title to
"docs: add POST /profiles body schema to API reference", expanded the
Summary section to explain the practical impact of the missing schema on
developers, and updated Screenshots/Demo to an explicit
"N/A — documentation-only change, no UI or visual output to demo."
Acknowledged the scope-mismatch suggestion for future issues.


**What was harder than you expected?**
Reading the output of `make check` and `make test-unit` for the first time
was more overwhelming than I expected — 182 lint errors and 53 test
failures looked like I had broken something, even though I'd only edited
a markdown file. I had to learn to actually scan the output for whether
any of it touched files I'd changed, rather than assuming a wall of red
text meant I'd done something wrong.

**What did you learn about working in a large codebase?**
Documentation can somewhat drift from the actual code without anyone noticing. For example, the docs/API.md never mentioned that POST /profiles used multipart/form-data
instead of JSON. I had to read the route handler
directly rather than trusting the schema file (I assumed this would be the right place to check but it wasn't). I also learned that a codebase can carry pre-existing, unrelated failures (182 lint errors, 53 test failures) that aren't your
responsibility to fix, just not add onto it. 

**How did AI tools help — and where did they fall short?**
Claude was really helpful for pulling the actual repo code so I didn't
have to dig through GitHub manually, and for turning my messy notes into
the actual PLAN.md/PR format the grader wanted. It was also good for
walking me through git stuff step by step when I got confused (like
auth issues when pushing, or figuring out branch tracking). Where it
fell short is it can't actually do the investigation for me — I still
had to be the one to read the route code, decide what the real request
shape was, and figure out how to scope the issue myself. It also
couldn't tell me whether make check's errors were mine or not, I had to
actually look and compare line by line.

**What would you do differently if you started over?**
I'd actually read CONTRIBUTING.md before making my very first commit
instead of finding out about the branch naming and commit message rules
partway through Week 9 — my early commits weren't quite right because I
just didn't know the convention yet. Also, when I got feedback that the
issue mentioned two endpoints but I only did one, the reviewer pointed
out I should've just asked the issue creator to clarify instead of
guessing and picking one myself. I'll actually do that next time instead
of assuming my interpretation is right.

**What are you most proud of from this module?**
Honestly just finishing. Nothing too elaborate, I'm just happy I was able
to get through the whole thing and actually navigate all the instructions
without giving up somewhere in the middle.