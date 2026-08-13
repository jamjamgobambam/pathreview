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
🗺️ How It's Graded
A detailed breakdown of graded features and points can be found on the course grading page.