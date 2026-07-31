# Module 3: Simulated Open Source Contribution

You've built AI features. You've practiced navigating and debugging unfamiliar codebases. Now you put it together, working through a complete, professional contribution on a multi-service AI application.

🎯 What you're working toward: A submitted pull request on pathreview, a production-grade AI application, following real contribution standards. This is the same workflow you use IRL — except here, the codebase is controlled and the issues are curated for you.

The Four Phases (Weeks 7-10)
1. Issue Selection (Week 7)
Browse the pathreview issue tracker and choose an issue that's the right fit for your skill level. Use the tier labels and the "Is this right for me?" checklist to guide your decision. Claim your issue publicly — comment on the issue and add it to the cohort ledger — so the cohort can see who's working on what. Claims aren't exclusive; more than one student may work the same issue.

Deliverable: Issue link + problem summary statement + forked repo with setup commits

2. Issue Reproduction and Solution Planning (Week 7-8)
Get the project running locally, reproduce the issue, and write a structured plan for your fix. You'll document your approach in a markdown planning file in your fork and record a short walkthrough video showing the issue and your intended solution.

Deliverable: Forked repo with 2+ starter commits, markdown plan, and a ≤2 min Loom walkthrough

3. Solution Building and PR Submission (Week 8-9)
Implement your fix iteratively using AI coding tools. Write or update tests, self-review against the project's contribution standards, and request feedback from a peer or mentor. Submit your pull request by the end of Week 9 — this is your graded deliverable for the module.

Deliverable: Submitted pull request following pathreview contribution standards

4. Iteration and Reflection (Week 10)
Respond to any reviewer feedback on your PR and document what you learned. Your grade is based on the PR you submitted in Week 9 — Week 10 is for engaging with feedback and wrapping up, not for rushing a submission. If no review comes in before the course ends, that's okay.

Deliverable: Reflection document + any documented reviewer responses


The Codebase: PathReview
What It Is
PathReview is an AI-powered portfolio review assistant — a multi-service Python + React application with a FastAPI backend, RAG pipeline, multi-tool agent, safety layer, and a React/TypeScript frontend. It uses Docker, database migrations, a CI pipeline, and pre-commit hooks.

Choosing Your Issue
The issue tracker has 66 curated open issues, organized into three tiers. Pick based on your comfort level — there's no extra credit for choosing harder issues, and starting with a well-scoped Tier 1 issue is a smart move if you're newer to contributing to large codebases.

Tier 1: Scoped to a single file or config. Good first contribution.
Tier 2: Requires understanding how modules connect.
Tier 3: Architectural or AI system changes. Significant scope.
Contribution Standards
PathReview uses the same standards you'd find in a real open source project. Your branch naming, commit messages, code style, and PR description all need to follow the project's contributing guide before you open a PR.

Run make check (linter + formatter + type checker) and make test-unit before opening your PR. Incomplete PRs will be sent back.

How You're Graded
Implementation Quality: 40%
Contribution Standards: 25%
Process Documentation: 20%
Issue Selection and Planning: 15%
Your PR submission at the end of Week 9 is the graded deliverable. Grades are based on your submitted documentation — the PR itself, bi-weekly check-ins, and your reflection — not code reviewed directly. (The Week 8 walkthrough video is recommended for early feedback but isn't graded.)


What to Submit
Week 7: Issue link, problem summary, forked repo with setup commits
Week 8: Forked repo with reproduced issue, markdown plan, Loom walkthrough (≤2 min, recommended)
Week 9: Submitted pull request + two bi-weekly check-ins
Week 10: Reflection document + any documented reviewer responses

Module Resources
PathReview Repository
Issue tracker: All 66 curated open issues, filterable by tier
SETUP.md — local environment guide: Platform-specific setup instructions
CONTRIBUTING.md — branch naming and commit conventions: Contribution standards, branch naming, and PR process
Week 7 — Issue Selection
Is this issue right for me? — checklist: Use this before committing to avoid scope surprises
Guide — reading and navigating large codebases: How to orient in an unfamiliar multi-module project
Week 8 — Reproduction and Planning
Examples — strong vs weak solution plans: Annotated examples of what a complete PLAN.md looks like
Week 9 — Solution Building and PR Submission
Checklist — pre-submission self-review: Run through this before marking your PR ready for review
Guide — writing effective tests for your changes: How to identify what to test and match existing test patterns
Examples — strong PR descriptions: Annotated examples of well-written PR descriptions
Week 10 — Iteration and Reflection
Guide — responding professionally to code review feedback: How to engage with maintainer comments constructively

--- 
# =========================================================================================
# WEEK 7 - Issue Selection
# =========================================================================================

> Week 7 — Issue Selection & Planning Your Contribution

The first six weeks were about building skills. The last four are about using all of them.

In Module 3, you're making a simulated open source contribution to PathReview — an AI-powered portfolio review tool designed for early-career developers, which means it's designed for people like you. The codebase is large, the issues are real, and the contribution cycle mirrors what you'd do contributing to an actual open source project. There's no starter template. There's no scaffolding. You pick your issue, you set up your environment, and you figure it out.

This week is about starting right. The most common mistake developers make when joining a new codebase is moving too fast — picking an issue that sounds manageable, skimming the relevant code, and writing a solution that technically works but doesn't fit the existing patterns, doesn't follow the project's conventions, and requires three rounds of revision to get merged. This week is explicitly about not doing that.

You'll orient yourself in PathReview before you touch a single line of code. You'll select an issue that's appropriately scoped for the time you have, claim it publicly, and get your local environment running with your first setup commits. The full written solution plan comes next week — this week is about understanding the problem well enough to explain it in your own words, and documenting the scope reasoning behind your choice.

The skills you're using this week — codebase navigation, issue analysis, spec-first thinking — are everything from Weeks 5 and 6 applied to a new context.

Why this matters: Issue selection and solution planning are underrated professional skills. Senior developers know that a well-scoped issue and a clear plan before implementation is worth more than twice as many hours spent coding in the wrong direction. In real open source communities and professional settings alike, contributors who demonstrate that they understand the codebase before proposing changes earn maintainer trust quickly — and that trust is what gets your work merged. The habit of writing a plan before writing code is also what separates developers who can work independently from those who need constant direction.

Learning Objectives

By the end of this week, you will be able to:

Configure a complex development environment for a multi-service application independently
Evaluate and select an appropriately scoped issue based on the codebase's structure and conventions
Navigate an unfamiliar production codebase to understand the context around a specific issue
Work through the issue-fit checklist and document the scope reasoning behind your selection
What you're building this week: A selected and claimed issue, a configured local development environment, and a JOURNAL.md problem summary that demonstrates you understand the problem before you've started solving it.

> PathReview: Choose Your Issue

This week you set yourself up for everything that follows. Your job is to find an issue in the pathreview repository that you can realistically solve, understand the problem well enough to explain it, and get your local development environment running. A good issue choice now saves you a lot of pain in Weeks 8 and 9.

📖 Resources
Module 3 Overview: Four-week arc, issue tiers, contribution standards, and grading breakdown
pathreview issue tracker: Browse all 66 curated open issues, filtered by tier level
SETUP.md — local environment guide: Platform-specific setup instructions
CONTRIBUTING.md — branch naming and commit conventions: Contribution standards, branch naming, and PR process
Is this issue right for me? — checklist: Use this before committing to an issue to avoid scope surprises
Guide — reading and navigating large codebases: How to orient yourself in an unfamiliar multi-module project
What to Do This Week

Fork the repo and get it running locally. Fork pathreview on GitHub, then clone your fork (not the original repo) and follow the setup guide in docs/SETUP.md:

git clone https://github.com/<your-username>/pathreview.git
cd pathreview
git remote add upstream https://github.com/ascherj/pathreview.git
Then run make setup followed by make run and confirm the app loads at localhost:5173 before moving on. The README points to the original repo — always clone from your fork's URL so you can push your own branch.


Browse the issue tracker and choose an issue. Go to the pathreview issue tracker and filter by tier label. Start with Tier 1 if this is your first time contributing to a large codebase. Use the "Is this right for me?" checklist (linked in resources below) before committing.


Claim your issue and add it to the ledger. Comment on the issue to let others know you're working on it. Then add your issue to the cohort issue ledger so your peer and instructor can track who is working on what — enter your name, GitHub username, and issue # on your section's tab, and the rest fills in automatically.


Create a branch and push your setup commits. Create a branch following the naming convention in docs/CONTRIBUTING.md and push at least one commit to show your environment is set up. A small config change or an initial JOURNAL.md commit is fine.

Branch naming — what is the issue ID?
The format from CONTRIBUTING.md is <type>/<issue-number>-<short-description>, for example: fix/124-resume-parser-index-error.

The issue number here is the GitHub issue number (like 124, visible in the URL and under the issue title). Each issue in the tracker has this number — look at the issue's URL or the number below the title.


Create your JOURNAL.md and submit. Create a JOURNAL.md file in the root of your fork, on your working branch (the branch you created above — that's where all your Module 3 work lives), and fill in the Week 7 section using the template below. Then submit your branch URL — not a bare repo link.

Submit the branch URL, not just the repo URL. Your link must include /tree/<your-branch>, e.g. https://github.com/<you>/pathreview/tree/fix/123-short-description. A plain repo link points the grader at your fork's main branch, which is just the untouched project — none of your JOURNAL.md or issue work lives there, so your submission will look empty. You'll submit this same branch URL each week of Module 3.
JOURNAL.md Template: Week 7
Create a file called JOURNAL.md in the root of your fork, committed to your working branch. You'll add a new section each week — this file is your running record of progress throughout Module 3.

---

## Week 7 — Issue selection

**Issue link:** [paste link here]

**Issue title:** [paste issue title here]

**Tier:** [ ] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

**Branch name:** [paste branch name here]

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
Replace all bracketed placeholders with your own content before submitting. Incomplete fields will affect your score.

Deliverables Checklist
Issue link and title in JOURNAL.md: Direct link to the GitHub issue you've chosen and claimed
Problem summary in JOURNAL.md: 3–5 sentences in your own words — what the issue is (not a copy-paste of the title), what's currently broken or missing, and what a successful fix would accomplish
"Is this right for me?" checklist reasoning in JOURNAL.md: Work through the checklist and note your scope reasoning in your selection notes
Fork with at least one setup commit: Branch follows the naming convention in CONTRIBUTING.md
Cohort issue ledger entry: Your issue is recorded so the cohort can see who is working on what
Branch URL submitted via course portal: Link to your working branch (ending in /tree/<your-branch>, not a bare repo link) submitted via the course portal by the deadline
If you complete your PR before Week 10: This module spans four weeks, but some issues (especially Tier 1) can be resolved in less time. If you submit a clean PR by the end of Week 9, consider starting a second issue. Choose one from a different tier than your first — it extends your practice, and it's a great thing to talk about in your Week 10 reflection. (A second issue isn't separately graded; your Week 9 PR remains the graded deliverable.)
🗺️ How It's Graded
A detailed breakdown of graded features and points can be found on the course grading page.

---

# =========================================================================================
# WEEK 8 — Issue recreation
# =========================================================================================

> Week 8 — Issue Reproduction & Solution Planning

You understand the problem. Now you prove it — and plan the fix.

This week you move from reading about your issue to demonstrating it: reproduce the broken behavior in your local environment, then write a structured PLAN.md that lays out exactly how you'll fix it — the files you'll change, the sub-tasks in order, the risks and edge cases you can already see. The plan is your deliverable for the week, and it's what makes next week's implementation go fast instead of sideways.

Reproduction comes first for a reason: until you can make the bug happen on your machine, you don't actually know what's broken — you know what the issue says is broken, which is not always the same thing. And plans written before reproduction are always somewhat wrong — the codebase does something you didn't expect, the approach you imagined doesn't fit the existing patterns. Finding those gaps now, on paper, is far cheaper than finding them mid-implementation.

You'll be using AI tools throughout — for navigating the codebase, explaining unfamiliar patterns, pressure-testing your approach. The discipline that matters here is what you bring to that collaboration: reading the real code before trusting a summary of it, and writing a plan specific enough that you could hand it to someone else and they'd build the same thing.

You're also encouraged to record a short walkthrough video (≤2 minutes) showing the reproduced issue and your planned fix. It's recommended rather than graded — the point is the early feedback it earns you from instructors and mentors before you start building.

Why this matters: The ability to make measurable progress on an unfamiliar codebase — without someone telling you what to do next — is one of the most valuable things you can demonstrate to an engineering team. This week is practice for exactly that. Every internship and new job starts with a period where you're working in a codebase you don't fully understand, trying to ship something real. The developers who thrive in that situation are the ones who can plan, start, adapt when the plan changes, and communicate their progress clearly. That's what this week is building.

Learning Objectives

By the end of this week, you will be able to:

Reproduce a reported issue in a local environment and document the steps that trigger it
Write a solution plan that names specific files, concrete sub-tasks, and real risks and edge cases
Trace the code paths involved in an issue well enough to predict what a change will affect
Communicate a planned approach clearly enough that someone else could evaluate or execute it
What you're building this week: Reproduction commits in your fork, a completed PLAN.md using the planning framework, and (recommended) a ≤2-minute walkthrough video for early feedback.

> PathReview: Reproduce the Issue and Plan Your Fix

This week you move from understanding the problem to proving you can reproduce it and articulating how you'll solve it. By the end of the week you should have a working local reproduction of your issue and a structured PLAN.md in your fork. You're also encouraged to record a short walkthrough video — it's recommended, but it isn't part of your grade, and it's something you can share in Slack or bring to office hours if you'd like early feedback.

📖 Resources
Guide — reading and navigating large codebases: How to trace a bug through an unfamiliar multi-module project
Examples — strong vs weak solution plans: Annotated examples showing what a complete PLAN.md looks like
Loom — free screen recording: Use this to record your 2-minute walkthrough video
What to Do This Week

Reproduce the issue locally. Trigger the bug or gap described in your issue in your local environment. If the issue is a bug, confirm you can reliably reproduce it. If it's a feature gap or documentation issue, confirm you understand exactly what's missing and where. Use AI tools, the codebase docs, and Slack to help you navigate if you get stuck.


Commit your reproduction. Push a commit that documents the reproduced issue. This could be a comment in the relevant file, a failing test, or a note in your JOURNAL.md showing the reproduction steps. The goal is to show the issue is real and you know exactly where it lives.


Write your solution plan. Create a PLAN.md file in your fork and write out your approach using the planning framework below. Break your solution into concrete steps, identify which files you'll touch, and note any risks or unknowns. Research with AI tools, mentors, and the codebase before finalizing your plan.


Record a walkthrough video (recommended, not graded). Record a short video (≤2 minutes) showing the reproduced issue in your local environment and walking through your planned solution. This doesn't need to be polished! It's a technical walkthrough you can share in Slack or bring to office hours to ask instructors and mentors for early feedback before you start building. It's strongly recommended, but it isn't part of your grade — your reproduction commits and PLAN.md are what's assessed.


Update your JOURNAL.md and submit: Add a Week 8 section to your JOURNAL.md (on your working branch, alongside your Week 7 entry) using the template below. Submit your branch URL via the course portal — the same /tree/<your-branch> link you used in Week 7, not a bare repo link (a plain repo link points the grader at main, where none of your work lives).

JOURNAL.md Template: Week 8
Add this section below your Week 7 entry in JOURNAL.md. Do not replace your previous entry!

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
Your PLAN.md file should live in the root of your fork alongside JOURNAL.md. See the planning framework below for what it should contain.

PLAN.md Planning Framework
Create PLAN.md in the root of your fork. Use this structure to break down your solution before you write any code.

## Solution plan

**Issue:** [issue title and link]

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

### Risks & unknowns
What could go wrong? What are you still unsure about?

### Edge cases
What inputs or states should your fix handle gracefully?
You'll update this file as your understanding evolves in Week 9. It's a living document, not a contract.

Deliverables Checklist
Reproduction commit: At least one commit documenting the reproduced issue in your fork
PLAN.md in your fork: Completed using the planning framework above — all six sections filled in, with specific files named, at least 3 concrete sub-tasks, specific risks tied to real files or investigation paths, and concrete edge cases
Week 8 section added to JOURNAL.md: Includes your reproduction commit link and PLAN.md link (and your walkthrough video link if you recorded one)
Walkthrough video (recommended, not graded): A short ≤2-minute video linked in your JOURNAL.md — encouraged (share it in Slack or bring it to office hours if you'd like early feedback), but not part of your grade
Branch URL submitted via course portal: Link to your working branch (ending in /tree/<your-branch>, not a bare repo link) submitted via the course portal by the deadline
🗺️ How It's Graded
A detailed breakdown of graded features and points can be found on the course grading page.

---

# =========================================================================================
# WEEK 9 - Solution Building & PR Submission
# =========================================================================================

> Week 9 — Implementation & PR Submission

This is the week you build, close the gap between "working" and "done," and submit your pull request — the primary graded deliverable of the module.

By now your implementation handles the core case. This week is about making it production-quality: handling the edge cases, following the project's test patterns, writing documentation that explains what you built and why, and verifying that your changes don't break anything unrelated. Those aren't finishing touches — they're the difference between code that works for you and code that works for the maintainers who will review it, the users who will depend on it, and the contributors who will maintain it after you.

This is also the week to honestly assess whether your implementation is actually complete. "It works on my machine" is not the same as "it passes CI." "The happy path works" is not the same as "edge cases are handled." The bar for a real open source pull request is higher than just technically correct — it has to be readable, tested, and documented to the project's standards.

If you hit a genuine blocker this week, the answer isn't to push through with a workaround. Scope appropriately, document what you learned, and be honest in your check-ins about what's done and what isn't. That's what real contributors do.

You'll write two check-in entries in your JOURNAL.md this week — one mid-week on your progress, and one at submission with your PR link — and submit your pull request by the end of the week.

Why this matters: Knowing when code is done — actually done, not just running — is a professional skill. The gap between a working proof of concept and a submittable contribution includes edge case coverage, test writing, documentation, and a honest self-review against the project's standards. These steps are what make contributions maintainable over time and what make maintainers willing to accept work from contributors they don't know personally. Developing the judgment to evaluate your own work honestly, and the discipline to bring it to standard before submitting, is what separates developers who ship reliably from developers who ship occasionally.

Learning Objectives

By the end of this week, you will be able to:

Identify and handle edge cases in an implementation that extend beyond the happy path
Write tests for your changes that follow the existing test patterns in a codebase
Write documentation that explains what you built, why you made the decisions you did, and how to test it
Submit a pull request that meets the project's contribution standards for code, tests, and documentation
What you're building this week: A complete, tested, documented implementation — submitted as your pull request by the end of the week — with both check-ins capturing where you are and how you got there.

> PathReview: Build Your Solution and Submit Your PR

This is the most demanding week of Module 3. You'll implement your fix, write tests, get a peer or mentor to review your draft, and submit a pull request to pathreview. Your submitted PR is the primary graded deliverable for the entire module, so give yourself enough time to get it right.

Don't wait until the due date to open your PR! Open a PR early in the week so you can get feedback before you finalize.
📖 Resources
CONTRIBUTING.md — contribution standards: Branch naming, commit conventions, code style, and PR process
Checklist — pre-submission self-review: Run through this before marking your PR as ready for review
Guide — writing effective tests for your changes: How to identify what to test and match existing test patterns
Examples — strong PR descriptions: Annotated examples of well-written PR descriptions
What to Do This Week

Implement your fix iteratively. Work from your PLAN.md, tackling one sub-task at a time. Use AI coding tools to explore the codebase, generate and debug code, and understand existing patterns — but review all AI-generated output against the project's conventions before committing. Commit frequently so your progress is visible.


Write or update tests. Every code change needs relevant tests. Run make test-unit as you go. If you're unsure what to test, look at the existing test files for the module you're touching in tests/unit/ — match the patterns you see there.


Self-review against contribution standards. Before opening your PR, run make check to catch linting, formatting, and type errors. Read through docs/CONTRIBUTING.md and verify your branch name, commit messages, and docstrings all follow the project conventions.

Pre-existing failures in make check or make test-unit
The codebase may already have type errors or failing tests that are unrelated to your issue — especially if you're working on a CI or tooling issue. If you hit this:

Run make check and make test-unit and note which failures exist before you start.
After your changes, run both commands again and confirm your changes did not introduce any new failures.
In your PR description, document any pre-existing failures you observed and explicitly state your changes do not affect them.
Then check the self-review boxes in your Check-in 2 — in a codebase with documented pre-existing failures, "passes" means your changes introduce no new failures.
The requirement is that your contribution doesn't make things worse — not that you fix the entire codebase before merging.


Request peer or mentor feedback on a draft PR. Open a draft PR early in the week and ask a classmate or mentor to review it before you finalize. Use the feedback to catch issues you missed. Mark the PR as ready for review only once you've addressed any feedback you agree with.

(Note: peer review happens in Slack. Your instructor will confirm which channel to use.)


Submit your bi-weekly check-ins. Add two check-in entries to your JOURNAL.md this week — one mid-week (Wednesday) and one at submission (Sunday). See the check-in format below.

(Note: check-in cadence may vary by cohort. Follow your instructor's guidance if it differs from the Wednesday/Sunday schedule above.)


Finalize and submit your PR. Fill in the PR template completely, confirm make check and make test-unit both pass, and submit by the deadline. Then update your JOURNAL.md (on your working branch) with the PR link and submit your branch URL via the course portal — the same /tree/<your-branch> link from Weeks 7–8, not a bare repo link. The grader opens that link, reads your JOURNAL.md, and follows the PR link in Check-in 2 to grade your PR; a plain repo link lands on main, where there's no JOURNAL.md to read.

JOURNAL.md Template: Week 9
Add this section below your Week 8 entry in JOURNAL.md. Fill in both check-ins — the first by Wednesday, the second by Sunday alongside your PR link.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]

**Next steps:**
[What are you working on for the rest of the week?]

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
The grader reaches your PR by opening your submitted branch URL, reading JOURNAL.md, and following the PR link in Check-in 2 — so make sure you submit the /tree/<your-branch> URL (not a bare repo link) and that Check-in 2 points to a submitted (not draft) PR by the deadline.

Deliverables Checklist
Submitted pull request on pathreview: Not a draft — marked as ready for review, PR template fully filled in
Tests written or updated: Relevant unit tests present and passing — documented in Check-in 2
make check and make test-unit pass: Confirmed before opening the PR — noted in Check-in 2
Both check-ins in JOURNAL.md: Check-in 1 by Wednesday, Check-in 2 by Sunday with PR link
Branch URL submitted via course portal: Link to your working branch (ending in /tree/<your-branch>, not a bare repo link) submitted via the course portal by the deadline
🗺️ How It's Graded
A detailed breakdown of graded features and points can be found on the course grading page.

---

# =========================================================================================
# WEEK 10 — Iteration and Reflection
# =========================================================================================

> Week 10 — Iteration & Reflection

This is what all of it has been building toward.

Your pull request went in last week — this week you participate in the review. If feedback comes back, some of it will be quick fixes. Some of it will require you to think carefully about whether the reviewer is right, and how to make a good argument if you disagree. And if no feedback arrives before the course ends, that's okay too — note it and move on; your grade doesn't depend on it. Engaging with the review cycle professionally is the final skill this course teaches.

The reflection you write this week is not a formality. It's the place where you articulate what you actually learned — not "I learned how to fine-tune a model" in the abstract, but specifically: what you chose to build, why you chose it, what went wrong and how you responded, what you would do differently with the full context you have now. That reflection is also evidence of the kind of thinking that makes a developer genuinely useful on a team.

At the end of this week, you'll have a portfolio of four production AI projects, two professional debugging and collaboration write-ups, and one documented open source contribution with a real commit history and real review responses. That's a portfolio that means something — because you can explain every piece of it.

Why this matters: The final loop — submit, receive feedback, iterate, resubmit — is how real software ships. It's also the most common place where early-career developers stall: waiting too long to submit, taking review feedback personally, not knowing how to respond professionally to pushback. Completing this cycle, even in a simulated environment, builds the muscle memory for doing it under real conditions. And the reflection habit — articulating what you built, what you'd change, and why decisions were made — is what turns project work into genuine professional growth. Interviewers ask about projects not just to hear what you built, but to hear how you think. This week teaches you how to answer that question well.

Learning Objectives

By the end of this week, you will be able to:

Respond to code review feedback in writing — addressing changes, asking clarifying questions, and pushing back professionally where appropriate
Document reviewer feedback and your responses as part of a professional contribution record
Reflect on a multi-week technical project with specificity: what decisions were made, what went wrong, and what you'd change
What you're building this week: Documented responses to any review feedback on your open pull request, and a reflection that demonstrates you understand not just what you built, but why the decisions you made were the right ones — or what you'd change if you were starting over.

> PathReview: Respond, Reflect, and Wrap Up

Your PR is submitted. This week is about engaging with any feedback that comes in, documenting what you learned, and closing out the module. Your grade for Week 10 is based on your reflection — not on whether your PR gets merged or reviewed.

Your grade is already largely set. The bulk of your Module 3 grade came from your Week 9 PR submission. Week 10 is worth 10 pts and is assessed entirely on your reflection and any documented reviewer responses, not on the outcome of your PR.
📖 Resources
Guide — responding professionally to code review feedback: How to engage with maintainer comments constructively
What to Do This Week

Check your PR for reviewer feedback. Check your open PR for any comments from reviewers or maintainers. If feedback has come in, respond professionally and make any changes you think are warranted. Document what you received and how you responded in your JOURNAL.md. If no feedback has arrived by the end of the week, that's okay — note it and move on.


Write your reflection. Add a Week 10 section to your JOURNAL.md using the template below. The reflection is the main deliverable this week, so write it with care. This is your chance to consolidate what you learned across the full four-week contribution cycle.


Submit your branch URL via the course portal. Submit your branch URL one final time by the due date — the same /tree/<your-branch> link from Weeks 7–9, not a bare repo link. The grader navigates to your JOURNAL.md on that branch to read your Week 10 entry and review your complete contribution record across all four weeks; a plain repo link lands on main, where there's no JOURNAL.md.

JOURNAL.md Template: Week 10
Add this section below your Week 9 entry in JOURNAL.md. This is the final entry in your journal.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [ ] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
Reflections are graded on depth and specificity, not positivity. Write honestly about what was hard and what you'd change.

Deliverables Checklist
Reviewer feedback documented in JOURNAL.md: What you received and how you responded — or a note that no review came in
Reflection completed in JOURNAL.md: All five reflection prompts answered with specificity
Branch URL submitted via course portal: Link to your working branch (ending in /tree/<your-branch>, not a bare repo link) submitted via the course portal by the deadline
🗺️ How It's Graded
A detailed breakdown of graded features and points can be found on the course grading page.

---

# =========================================================================================
# Module 3: PathReview Grading Guide
# =========================================================================================
Week 7: Issue Selection
Total Points: 10pts

Required Features
2pts	Issue Link
2	A live link to a specific pathreview GitHub issue is included in JOURNAL.md. The link resolves to an individual issue page — not the issue tracker homepage.
3pts	Issue Fit and Selection Reasoning
1	The issue tier is acknowledged — the student references the tier label (Tier 1, 2, or 3) and it aligns with their stated skill level or comfort with the codebase.
2	The summary or selection notes show the student reasoned about scope fit — not just "I picked one that looked interesting." A Tier 3 selection with a clear rationale earns full credit.
3pts	Problem Summary Demonstrates Understanding
1	The summary describes what the issue is in plain language — not a copy-paste of the issue title.
1	The summary describes what behavior is currently broken or missing.
1	The summary describes what a successful fix would accomplish.
2pts	Forked Repo with Setup Commits
2	At least one student-authored setup commit is visible in the repository's commit history (for example, the commit that adds JOURNAL.md, or a small configuration change), beyond the original pathreview commit history.
Week 8: Reproduction and Planning
Total Points: 10pts

Required Features
2pts	Starter Commits
1	At least one commit documents the reproduced issue — the message or content indicates the student confirmed the issue exists in their local environment.
1	At least one commit introduces PLAN.md. These can be separate commits or two distinct commits — what matters is that both actions are represented.
8pts	PLAN.md — Content and Specificity
1	PLAN.md identifies what needs to change — the student names, in their own words, the specific feature, component, or bug they intend to fix (e.g. "the resume parser bug"). Describing what a correct implementation would do differently strengthens the plan but is not required for this point; a contentless restatement with no identifiable target ("fix the bug", "make it work") earns 0.
1	PLAN.md names specific parts of the codebase likely involved — files, modules, or components by name, not just "I'll look at the relevant code."
2	PLAN.md breaks the fix into actionable sub-tasks — the plan reads like something a person could follow step by step, not a restatement of the issue. Scored by the count of distinct sub-tasks that name a real action: 3 or more earns the full 2 points; exactly 2 (even if thin or lacking step-by-step detail) earns 1 point; one or zero, or a pure restatement of the issue ("make it work"), earns 0. A thin two-task plan is partial credit, not a restatement.
2	PLAN.md documents the fix's inputs and outputs and names specific risks or unknowns — what the fix takes in and produces (signatures, data, or behavior that change), and specific risks or unknowns each tied to a concrete file, function, or investigation path.
2	PLAN.md lists concrete edge cases — at least two specific input or state scenarios the fix must handle gracefully.
Week 9: PR Submission
Total Points: 20pts

Required Features
3pts	PR Submitted and Ready for Review
3	The PR link in JOURNAL.md Check-in 2 is live and points to an open pull request on pathreview.
5pts	PR Template Fully and Substantively Filled In
2	The PR description explains what the fix does and how it addresses the issue — a reader who hasn't seen the code can understand what changed and why.
2	The PR description names the issue it closes (by number or link) and includes specific instructions for how to manually verify or test the change — not just "run the tests," but actionable steps a reviewer could follow.
1	Every required section of the PR template (Summary, Issue, Changes, Testing, Notes for Reviewers) contains substantive content — no required section is left empty or at placeholder text.
4pts	Contribution Standards Documented as Followed
2	Both self-review checkboxes in JOURNAL.md Check-in 2 are checked: make check passes and make test-unit passes.
2	The branch name recorded in the **Branch:** field of JOURNAL.md Check-in 2 follows pathreview's naming convention (e.g., fix/123-short-description).
4pts	Tests Documented
2	Check-in 2 names the specific test file(s) that were created or modified.
2	Check-in 2 describes what the tests cover — specific enough that a reader can understand what behavior is being tested. "I wrote tests for the fix" is not sufficient; "Added tests in test_rag_pipeline.py covering the case where no relevant chunks are retrieved" earns full credit.
4pts	Both JOURNAL.md Check-Ins Present and Substantive
2	Check-in 1 (mid-week) is present with substantive content: current progress names specific sub-tasks completed from PLAN.md, next steps describe what remains, and blockers are noted or explicitly marked as none.
2	Check-in 2 (end of week) is present with substantive content: the PR link is included, a 1–3 sentence description of what was built is provided, the tests field is filled in, and both self-review checkboxes are present.
Week 10: Reflection
Total Points: 10pts

Required Features
2pts	Reviewer Feedback Documented
1	The checkbox for whether reviewer feedback was received is checked (either Yes or No).
1	If Yes: the student summarizes what the reviewer commented on and describes how they responded or plan to respond. If No: the student notes that no review arrived. Both outcomes earn full credit — this criterion assesses documentation, not whether review came in.
5pts	All Five Reflection Prompts Answered
5	All five prompts are answered with at least 2–3 sentences each. No prompt is left blank or at placeholder text. The five prompts: (1) What was harder than you expected? (2) What did you learn about working in a large codebase? (3) How did AI tools help — and where did they fall short? (4) What would you do differently if you started over? (5) What are you most proud of from this module?
3pts	Reflection Demonstrates Specificity
3	At least 3 of the 5 prompts include concrete details tied to the student's actual experience — referencing their specific issue, a named file or component, a particular moment in the process, a real AI interaction, or a concrete decision they made. The response could only have been written by this student about this project.
