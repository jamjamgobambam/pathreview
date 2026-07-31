## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x ] No — still awaiting review

**Summary of feedback:**
No Feedback 

**How you responded:**
No Feedback 

---

### Reflection

**What was harder than you expected?**
- Finding the regex patterns that could catch a wide net of potential biased outputs but not too flexible
- Determining the scope of coverage. Even though I was tempted to try to cover as many cases as possible, for time and simplicity sake, I limited to ensuring that the regex pattern could cover the test cases as well as the original intent of the previous regex patterns.

**What did you learn about working in a large codebase?**
- I learned about git conventions that ensured for every update to the remote branch, the type of changes made will be understood
- Also learned about how some codebases may require linter check to ensure that code formatting follows as is
- I learned about how issues are made and how to create a PR

**How did AI tools help — and where did they fall short?**
- During brainstorming my approach, AI was helpful in reviewing and giving feedback on my approaches including the tradeoffs. For instance, event though regex patterns were limited, they are much simpler to implement and run rather than having another model which  may be more computation heavy and expensive. 
- AI was helpful in terms of troubleshooting when I was struggling to push my updates to my remote working branch, it gave me a git line to run that bypasses the linter (only used it temporarily before fixing the issue)
- Also, AI helped simplify my new regex pattern for detecting dismissive outputs (e.g. The person is too old / young to code etc). I modeled it for the regex pattern detecting biased demographic based output. 



**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

I would change the implementation to try a more advance bias catcher method by using Huggyface to make the bias detector smarter and less rigid. 

Others that stayed the same: 
- The issue was scoped perfectly based on my experience and commitment ability
- Planning w/ AI (Claude) feedback went well together.
- Process of understanding the issue, brainstorming, and designing the solution went well.


**What are you most proud of from this module?**
- Being able to learn more regex pattern to help the program improve it's output quality

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Replaced all the old regex patterns with new ones that improved the passing rate of the test cases by 25%. (31/32 test cases passed).

**Next steps:**
- trying to reach 100% percentage test case pass by focusing on the current failing test case
- implement hugging face appraoch and compare performance

**Blockers:**
- long regex patterns interfer with the limit on line length but breaking into new lines will affect the performance so have to bypass the format checker.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/289

**Branch:** fix/151/narrow-bias-detector 

**What you built:**
A more flexible regex pattern that detects more biased outputs. All the original patterns for Demographic and Dismissive patterns were replaced with new ones.
The bias detection layer is now more robust.

**Tests added or updated:**
Verified changes were valid by running test_bias_detector.py and passing all test cases.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** N/A


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/stephanyTF/pathreview/commits/fix/151/narrow-bias-detector/?since=2026-07-16&until=2026-07-16 

**Reproduction summary:**
In the terminal, I ran .venv/Scripts/python -c "from safety.bias_detector import BiasDetector; print(BiasDetector.detect_bias('The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education'))". 

From there I saw that the test case failed in the output, as the bias detector didn't catched the bias. 

**PLAN.md link:** (https://github.com/stephanyTF/pathreview/blob/fix/151/narrow-bias-detector/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
N/A

## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/151)

**Issue title:** Bias detector patterns are too narrow to match common phrasings


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
 The issue is that the regex patterns in the bias_detector.py file only match near-exact phrasings, so it misses more natural wordings of the same biased language that the system outputs. An example is when the system is not supposed to assume that bootcamp experience are invaluable, the bias detection fails to pick that sentiment in this: "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education" because the regex is strict on the order and specifity of the flag words. Hence bias prevention is weak without a more robust bias detector.

**Branch name:** fix/151/narrow-bias-detector

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** (Skipped for TF)
