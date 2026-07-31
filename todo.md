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
