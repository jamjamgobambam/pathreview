## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/159]

**Issue title:** [structlog output is not captured by pytest caplog — log assertions fail suite-wide]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

tests fail since structlog doesnt propagate into the stblib logging system when testing. any test that uses caplog fails. we have to mod conftest.py or structlog so when testing using caplog will work as intended

**Branch name:** [test/159-configure-structlog-caplog]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

Claims are non-exclusive — more than one student may work on the same issue, and your grade comes from your own artifacts, never from being first. Still, check the issue comments and the Claims column in the Issue Catalog tab of the cohort ledger: a less-crowded issue of the same tier can mean smoother coaching and peer review.

[x]I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
Is the scope realistic for Weeks 8–9?

You have roughly two weeks to implement, test, and submit a PR. Tier 1 issues should take 3–6 hours of focused work. Tier 2 issues may take 8–12 hours. Tier 3 issues can take significantly longer.

Think about your week — other classes, work, other commitments. Is this achievable?

[x]I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
Are there any blockers or dependencies?

Some issues say "blocked by #X" or reference another issue that needs to be resolved first. Check the issue for any such dependencies.

[x]This issue has no open blockers or dependencies on other unresolved issues.