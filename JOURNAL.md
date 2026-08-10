## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/128]

**Issue title:** [Add a dependency vulnerability scan to the CI pipeline]

**Tier:** [ ] Tier 1 [ ] Tier 2 [✓] Tier 3

**Problem summary:**
[My issue (#128) is to build an automated dependency security scan that will run when a pull request is targeted towards main and when code is pushed directly to main. What is currentely missing is a programmable function that will automate the calling of "pip audit" and "npm audit" to run the security scan on the codebase's Python and JavaScript dependences. A successful fix would look a github function that sends a fail message showing the high-priority vulnerabilities found in the codebase. The part of the codebase that it affects are the .github workflows where it starts, but will check over the entire codebase to find vulnerabilities.]

**Branch name:** [fix/128-add-a-dependency-vulnerability-scan-to-the-ci-pipeline]

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/chase-b04/pathreview/commit/b25442f3bc59edc077403949b71af8ac60ecd90d

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I reproduced this bug by first running cd frontend and then npm audit, this read npm vulnerabilities that the command can currentely find. Next, I went to the backend and ran -m pip install --quiet pip-audit and -m pip_audit in a test venv, which showed two PIP vulnerabilities currentely with the chromadb and ecdsa. What I observed are that there are real issues and vulnerabilities, but no actual workflow for improvements in CI, as shown with the ci.yml that has no security scanning steps

**PLAN.md link:** [[link to PLAN.md in your fork](https://github.com/chase-b04/pathreview/blob/fix/128-add-a-dependency-vulnerability-scan-to-the-ci-pipeline/PLAN.md)]

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
My current blockers are potentially needing to change too many unrelated files that will either get struck down by the PR reviewer, or if I only send in the relevantely changed files, then will it work in the main repo once pulled?

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
What I have implemented so far is the backend and frontend scans in the ci.yml file, adding a scan for both that will run every time the github action is called during pull request merges. The two commands I wrote for usability and testing are make audit-backend and make audit-frontend.

**Next steps:**
I will spend the rest of the week on testing and verifying that my program works and that it is ready for a success code review and pull request merge.

**Blockers:**
What's slowing me down is that when I run "make check," 53 errors appear, it used to be 172. I am working with Claude right now to figure this out in my setup and see whats wrong, as it seems to be a setup error and not a issue fix error.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/886

**Branch:** Fix/128 add a dependency vulnerability scan to the ci pipeline - #886

**What you built:**
Added a security-scan CI job that runs pip-audit and npm audit on every PR and push to main, fails the build on real vulnerability findings, and posts the results as a PR comment. The backend scan ignores two vulnerabilities that have no available fix upstream (documented in the Makefile), and the frontend scan only fails on high or critical severity so moderate/low findings do not make CI permanently red.

**Tests added or updated:**
No new automated tests were added for the scan itself. This repo has no existing pattern for unit testing GitHub Actions workflow files, everything in tests/unit/ tests Python classes and functions, not CI config. Instead I verified it by running make audit-backend and make audit-frontend locally against real dependencies, and the real verification will happen when the job actually runs on this PR (job passes/fails correctly, comment appears). Separately, I updated tests/unit/test_tech_detector.py to remove 7 unused variable assignments flagged by the linter. That was a lint cleanup, not new coverage.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

**Draft PR feedback received from:** None, I asked in the slack and got no responses.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes [] No — still awaiting review

**Summary of feedback:**
I recieved feedback from a CodePath Mentor during Thursday's meeting. The positive parts of my feedback include going beyond my scope in a good way, fixing a make run issue gating npm audit to high/critical so CI doesn't stay permanently red, documenting the ignore-list for unfixable CVEs with clear rationale, and framing scans that are expected to fail as a feature. The constructive feedback first was to make sure that TOREVIEWER.md wasn't deleted for the final draft, as I had deleted it for the final draft, but the mentor who reviewed my PR said to add it back. I also needed to confirm the PR-comment step actually fires in Actions since I couldn't test it locally.

**How you responded:**
How I responded was I added TOREVIEWER.md back to next commit that will go with my reflection for week 10's push, as well as double checkign the PR-comment step firing action. Otherwise, I took the positive feedback nicely and am excited to continue PRs at a similar level.

---

### Reflection

**What was harder than you expected?**
Proving the gap was harder than describing it. Adding a security scan that would run on npm audit sounded easy enough, but actually knowing the tools, github action usecases, and wiring of of my github actions to the entire program and npm and pip was a little more complicated than expected. I also had issues when it came to processing that trying to show code errors where actually a good thing and a feature of my program. Finally, and honestly my biggest issue, was just figuring out the Make File and the setup, as I had to change it around multiple times throughout the few weeks, and had to avoid submitting any setupchanges that werent mandatory in my fix.

**What did you learn about working in a large codebase?**
I learned to read the existing patterns before adding anything new. Before touching ci.yml, I had to understand how the other jobs were structured and how eval.yml already posts PR comments with actions/github-script, since my new job should follow that same convention instead of inventing its own style. I also had to be careful about scope. There were unrelated uncommitted changes sitting in the repo that had nothing to do with my issue, and I had to leave those alone rather than assume I could touch or commit them.

**How did AI tools help — and where did they fall short?**
AI was most useful for speed, such as locating the right workflow file, running and summarizing audit tool output, and structuring the plan into concrete sections. It fell short on boundaries around git. It committed changes on my behalf without asking first, which I had to correct and then undo. That was a good reminder that I need to stay the one deciding when something actually gets committed or pushed.

**What would you do differently if you started over?**
I would decide on a severity threshold and an ignore/allowlist strategy before writing any workflow YAML, since I found vulnerabilities that don't have fixes available yet. Without a plan for that upfront, the job would either be too noisy or too lenient. I'd also set expectations earlier about what I want an AI assistant to do versus what I want to do myself, especially around git actions.

**What are you most proud of from this module?**
Having real and measurable evidence for the issue instead of a hypothetical description. Being able to say "here are 11 real vulnerable packages and 2 real CVEs that CI currently misses" made the whole issue concrete.

---

# Section Notes

## Part 1 — Understanding the Issue

Can I explain what this issue is asking for in my own words?

- The problem is that there is no automated scan for security vulnerabilities in the continuous integration pipeline. The expected behavior is that in the CI pipeline, whenever a pull request targets main and when code is pushed directly to main, the program will call pip audit and npm audit to find security flaws in the codebase.

Do I understand which part of the app is affected?

- Yes, the part of the app that is affected is the ci.yml workflow in the .github folder. This issue is strictly devops.

Do I understand what "done" looks like?

- The before is that a developer can send pull requests with no certainty of it being secure, and users can interact with a vulnerable product. After, a developer gets a breakdown of vulnerability findings which they can use to fix the code, and the users will be working with a fully secure product.

## Part 2 — Tier Fit

Is the tier a realistic match for where I am right now?

- While not on my public profile, I have contributed numerous times to a large codebase in a work environment, from tasks like simple frontend implementation to full on RESTful API building. I have also worked on CI/CD pipelines before using a database, Docker, and GitHub Actions. I believe I have the experience to take on this Tier 3.

## Part 3 — Codebase Readiness

Can I find the relevant code?

- I have found the necessary code with relative ease in .github/workflows.

Do I understand the surrounding code well enough to change it safely?

- I have read the file and surrounding context (such as the other workflow, safety/security based code, and tests) and can write a rough plan for the fix.

Have I read the relevant test file?

- I have found the test file for my module and will need to make tests for my end-to-end.

## Part 4 — Scope and Time

How many others are already working on this issue?

- I have checked the issue comments and ledger's claims counts, there are 3 other students working on this issue, none of which are currentely in my session as of right now. I am comfortable with how many others are working on this issue.

Is the scope realistic for Weeks 8–9?

- While the PR says this should only be a 3-5 hour issue, with planning, testing, and documentation, it will take longer. That being said, 5 hours + the amount of time needed to do the extras is both very reasonable in a two week timeframe, as well as giving me enough cushion time in the case that I am working slow or am stuck.

Are there any blockers or dependencies?

- My issue does not claim to have any blockers or dependencies.
