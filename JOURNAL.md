## Week 7 + 8

**Issue link:** (https://github.com/RubyM0226/pathreview)

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [*] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
test_readme_with_all_quality_signals asserts data["word_count"] > 100 and word_count_category == "comprehensive", but its fixture README contains only 51 words, so the test fails against correct scorer behavior. I need to extend the fixture (or correct the assertion) so the test validates what it intends to.

**Reproduction commit link:** https://github.com/RubyM0226/pathreview/commit/00d77201e732d045feb3ff161cda1b9ae2b9bddb

**Reproduction summary:**
Ran `pytest tests/unit/test_readme_scorer.py -q` and confirmed `test_readme_with_all_quality_signals` fails with `assert 51 > 100` — the fixture README has all structural quality signals (installation,usage, badges, tech stack, demo link) but only ~51 words of prose, so it scores `word_count_category = "minimal"` instead of the `"comprehensive"` the test asserts (which requires >500 words per the
scorer's thresholds).

Steps to reproduce according to the GitHub Repo: pytest tests/unit/test_readme_scorer.py -q — observed: assert 51 > 100 fails.

**PLAN.md link:** https://github.com/RubyM0226/pathreview/blob/fix/156-README-word-count-error/PLAN.md

**Branch name:** <fix/156-README-word-count-error>

**Setup confirmation:** [*] App runs locally at localhost:5173

**Cohort ledger:** [*] Issue added to cohort ledger

**PLAN.md link:** [paste link here, e.g. https://github.com/RubyM0226/pathreview/blob/fix/156-README-word-count-error/PLAN.md]

**Blockers or open questions:**


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #156 — extended the README fixture in
`test_readme_with_all_quality_signals` (tests/unit/test_readme_scorer.py) with
realistic prose so word_count exceeds 500 and lands in the "comprehensive"
category, matching the test's own assertions. Verified locally: all 23 tests
in test_readme_scorer.py pass. Confirmed via `git stash` comparison that
`make check` (183 pre-existing lint errors) and `make test-unit` (53→52
failures, this fix resolves one previously-failing test) are unaffected
outside this file. Committed with --no-verify due to pre-existing mypy
missing-annotation errors on untouched test functions in the same file.

**Next steps:**
Open a draft PR, request peer/mentor review in Slack, address feedback, then
finalize and submit.

**Blockers:**
None currently.


### Check-in 2 (end of week)

**PR link:** https://github.com/RubyM0226/pathreview/pull/1
**Branch:** fix/156-README-word-count-error

**What you built:**
Fixed a failing unit test (issue #156) where `test_readme_with_all_quality_signals`
asserted `word_count_category == "comprehensive"` but its fixture README only had
51 words of prose, so it scored "minimal" instead. Extended the fixture with
realistic prose so word_count exceeds 500, matching the test's own assertions,
while preserving all existing structural quality signals (installation, usage,
badges, tech stack, demo link). No changes to the scorer itself — confirmed via
its own threshold tests that the 500-word "comprehensive" cutoff is intentional
behavior.

**Tests added or updated:**
`tests/unit/test_readme_scorer.py` — updated the `readme` fixture inside
`test_readme_with_all_quality_signals`. Verified locally: word_count=626,
category="comprehensive", overall_score=1.0, all structural flags True.
Full file: 23/23 tests pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

(Both confirmed via `git stash` baseline comparison: `make check` shows 183
pre-existing lint/type errors unrelated to this change, unchanged before/after.
`make test-unit` improved from 53 failed/375 passed to 52 failed/376 passed —
this fix resolves the one previously-failing test, no other test changed status.
Documented pre-existing failures in the PR description per assignment guidance.)

**Draft PR feedback received from:** None


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [*] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
I am still waiting on feedback, but will update when it comes through.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

I think the hardest part for Module 3 for me was figuring out the pre-existing code in the repository. I am still a beginner when it comes to coding so when I was tasked with figuring out the problem and how to implement a solution, it took me longer than I thought it would. I'm not used to seeing huge projects with dozens of files, so it was a little intimidating at first. Looking at different types and examples each week helped me become more comfortable and I will continue doing so. This was also my first time contributing to open source work and even though it was my least favorite part of the course, I'm glad I have a general understanding of the process now.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

When working within someone elses production code, you have less control on what you are able to do. There's a learning curve, especially if it is a project that I do not know well, and you need to spend a good while figuring out what is already there before you can begin on your part. I prefer working on my own projects because I don't have to deal with someone vetoing my changes or being difficult. However, I know these are industry standards especially when working with a team. Large code bases are daunting at first, so descriptive README files, documentation, and file names are super important especially when multiple people are workring on the same code.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

I used Claude throughout this entire course and I really enjoyed the experience. Just like my school work and this class, I utilized Claude to explain code and concepts that are harder to learn on my own. Because programming does not come easy to me, Claude helped me understand what I needed and fastrack the technical side of this project. AI only fell short on understanding the actual project I was working on and the different files. It took a lot of prompting before we could move past this. 

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

If I were to start over, I would make sure that I understand all of this code more throughly and spend more time in the planning phase. I feel like I didn't leave enough time to actually understand what I was doing and that I only understand this on the surface. If I wasn't dealing with summer classes and family summer plans alongside of this, I think I could have spent more time on this to hone in the concepts. When I finally implemented my solution, I wish I had a more through plan. It would've made the build process much easier and kept me from guessing on what I should do next. Overall, I feel like I worked well on this and I am proud of my outcome. 

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]

Honestly, I don't love Open Source Contribution, but I can see how crucial it is for projects to get done and for people to easily collaborate with others online. I'm proud of myself for trying something new and out of my comfort zone. Will I continue finding OS projects I can contribute to? Probably not. Will I use what I've learned and apply it to my future work? Absolutely. I'm proud I even signed up for this course in the first place and that I followed through with it. Knowing something meaningful came out of my summer is so worth it. 