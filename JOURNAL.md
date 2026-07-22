# Module 3 Journal — LaxmiPrasanna Ravikanti

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
When you finish a review in PathReview you can see a summary of it, but only while
you are logged into your own account. There is currently no way to hand that summary
to someone else, such as a mentor or a peer, unless they also have an account and log
in. Issue #101 asks me to add a "Copy link" button on the review page that generates a
link anyone can open, even without logging in, showing a read-only version of the
summary. So that these public links do not live forever, the link should expire 30 days
after it is created. Making this work means changes across the stack: a new frontend
service to request the link, the button itself on the review page, and a new API route
that creates these public links and checks whether they have expired.

**Branch name:** feat/101-share-review-link

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
<!-- Action item: add your name, GitHub username (prasanna-4), and issue #101 to the
     Section 1A tab of the cohort ledger, then check this box. -->

### "Is this right for me?" — scope reasoning

- **Do I understand what is being asked?** Yes. The feature is easy to describe in one
  sentence, a button that copies a public, read-only, 30-day link to a review summary,
  and I can picture how a user would use it, which tells me the requirements are clear.
- **Is the scope manageable?** It is labeled Tier 2 with an estimate of 5 to 8 hours. It
  is bigger than a single-file bug fix because it spans three layers: the React frontend
  (`ReviewPage.tsx`), a new frontend service (`shareService.ts`, which does not exist
  yet and I will create), and the Python API (`api/routes/reviews.py`). The issue names
  all of these files, so I know where the work lives instead of having to hunt for it.
- **Do I have the skills?** I work as a frontend developer intern at Hyland Software,
  mostly in Angular, so I am comfortable with component-based frontend work, services,
  and state management. PathReview's frontend is React rather than Angular, so the
  concepts carry over but I will be learning React's specific patterns as I go, which is
  part of why I wanted a frontend issue.
- **What are the key decisions?** How to generate a share token, where to store it and
  its creation date, how to enforce the 30-day expiry, and how to serve the read-only
  view without requiring authentication.
- **Why I chose it:** I want to strengthen my frontend skills and land a real, merged
  open-source contribution. The Tier 1 frontend issues available were small polish or
  test tasks; I chose this Tier 2 feature instead because it is a complete, user-facing
  piece of work that better reflects the kind of frontend engineering I do and want to
  grow in. The parts I will watch most closely are the expiry logic and the no-login
  access path, since those are where edge cases are most likely to hide, so I will make
  sure I have tests around token creation and expiry before I consider it done.
