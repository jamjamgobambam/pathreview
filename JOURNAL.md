## Week 7 — Issue selection

**Issue link:** \
 https://github.com/ascherj/pathreview/issues/88


**Issue title:** \
POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** Tier 1 was chosen to complete as a first open source contribution.

**Problem summary:** \
<!-- [In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.] -->
Issue #88 deals with the return of reviews when a profile has no added documentation such as github repo, or resume to provide feedback on. A test to administer to make the system does not crash with any ingested documentation is currently missing. By providing a test for the review output would ensure a successful fix of the system not crash. 

**Branch name:** \
test/88-post-review-endpoint

**Setup confirmation:** Yes App runs locally at localhost:5173

**Cohort ledger:** Yes Issue added to cohort ledger


**Is This Issue Right for me?:**\
- I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
- I've located the relevant files and confirmed they exist in the codebase.
- I can describe a concrete before-and-after: what the user sees before the fix and what they see after.
- I've found and read the specific code the issue references (not just the file — the function or section).
- I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
- I've found the test file for my module and read at least one test end-to-end.
- I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
- This issue has no open blockers or dependencies on other unresolved issues.