## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/70

**Issue title:** Add rate limiting per IP address in addition to per user

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The project as is only limits user request based on their authenticated ID, but not by their origin IP address. The goal is to add in the IP limiter as an additional check within the rate limiter component as a secondary layer. If all things are implemented correctly, the project will automatically deny further requests from any users within the same IP if the limit has been reached.

**Branch name:** feat/70-rate-limit-per-ip

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Is this right for me?**: Yes
- Part 1: I understand the issue at hand, what the fix looks like, and knows where to pin point directly to add in the IP rate limiter.
- Part 2: Since I'm not a stranger to making pull requests, I can work with a Tier 2 issue involving communication between layers.
- Part 3: I managed to locate the appropriate code, where I think my changes will take place as well as the associated test file.
- Part 4: There are only 2 other people claiming this issue from other sessions, so I'm fine with it. I should have the time to do it within the upcoming weeks. This requested changes does not rely on anything else, so I can work on it right away.