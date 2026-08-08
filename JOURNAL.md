\## Week 7 — Issue selection



\*\*Issue link:\*\* https://github.com/ascherj/pathreview/issues/156



\*\*Issue title:\*\* README scorer test fixture is too short for its own word-count assertion



\*\*Tier:\*\* \[X] Tier 1  \[ ] Tier 2  \[ ] Tier 3



\*\*Selection reasoning:\*\*

Picked a Tier 1 problem since it is the skill level that seems adequate for me. It deals with seemingly one component, the readme\_scorer.py and the given logic. A higher tier would likely be more involvement of files that rely on one another, which appears far more difficult than I might be able to manage at the moment. This is also a very realistic example where one would have to search for the cause of a "perfect" test file failing and the cause not being the actual behavior but another asserted aspect.



\*\*Problem summary:\*\*

The test\_readme\_with\_all\_quality\_signals in the tests for the readme\_scorer.py has it set that the word count of the README would be over 100 words in length \[line: assert data\["word\_count"] > 100], but the current fixture README only has 52 and the test is failing even though its behavior being tested beside that works. Basically the README test is failing the README because it has smaller word count than assumed and not because the README is incorrect in any other fashion. A successful fix would allow for the README scorer to work properly as long as the README is not empty.



\*\*Branch name:\*\* fix/156-readme-scorer-fixture



\*\*Setup confirmation:\*\* \[X] App runs locally at localhost:5173



\*\*Cohort ledger:\*\* \[X] Issue added to cohort ledger







\## Week 8 — Reproduction \& solution planning



\*\*Reproduction commit link:\*\* https://github.com/Cristina-Adame/pathreview/commit/af2b33ae77174ed0458f0b4933df1de57c2088bd 



\*\*Reproduction summary:\*\*

Ran the command "pytest tests/unit/test\_readme\_scorer.py -q" on my branch and saw the failure:

```

FAILED tests/unit/test\_readme\_scorer.py::TestReadmeScorer::test\_readme\_with\_all\_quality\_signals - assert 51 > 100



```

Confirms that the README has 51 words but the assertion expects more than 100, causing it to fail. This is failing even though the other README requirements/assertions are met.



\*\*PLAN.md link:\*\* https://github.com/Cristina-Adame/pathreview/blob/fix/156-readme-scorer-fixture/PLAN.md



\*\*Walkthrough video (recommended):\*\* N/A



\*\*Blockers or open questions:\*\*



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the expanded string README fixture to >500 words. All 23 unit test pass now.

**Next steps:**
Opening the draft PR, getting feedback, and marking as ready for review.

**Blockers:** none


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/739

**Branch:** fix/156-readme-scorer-fixture

**What you built:**
Expanded the README string fixture in 'test_readme_with_all_quality_signals' to
exceed 500 words by adding sections. This fixes the problem by expanding the README string fixture to >500 words to match the comprehensive assertion of >500 and the word count assertion of >100.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
'tests/unit/test_readme_scorer.py' by expanding the README string fixture in 'test_readme_with_all_quality_signals'. Fixes 2 assertions: "word\_count"] > 100 and word_count_category == "comprehensive".

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Hardest part was likely just selecting a problem and then trying to navigate to the appropriate files within the codebase. Knowing where to look and understanding how the files
related to each other took more time than the actual fix.

**What did you learn about working in a large codebase?**
Learned that there is a lot to think about when trying to make a branch or push a fix. More tedious and more to consider rather than your own individual work. In a personal codebase the design can change often but it is not polite to go around changing the intended design of someone else's codebase.

**How did AI tools help — and where did they fall short?**
The selection of the problem was greatly influenced by Claude. Claude asked questions to gauge my skill level and suggested problems accordingly. Going beyond Claude was to consider which type of fix would be best for the specific problem. If expanding the fixture or changing the assertion.

**What would you do differently if you started over?**
If starting over, I likely would have picked a more challenging issue to do for the project. This issue was very straightforward and had a simple fix. It is not a true example of what working on code in real life could be like.

**What are you most proud of from this module?**
Probably that I got more acquainted with Git and GitHub. I didn't have much experience coming in and this forced me to do different things with branches and commits that I had never done before. I now have a better intuition when navigating through those tools.
