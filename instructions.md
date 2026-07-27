PathReview: Choose Your Issue
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

Rubric
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

Week 8:
PathReview: Reproduce the Issue and Plan Your Fix
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