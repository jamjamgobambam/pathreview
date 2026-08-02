## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bias detector's regex patterns are too rigid and only match exact phrases, so they miss when the same bias is expressed in different ways. For example, it fails to catch natural variations like "The candidate only attended a bootcamp, so this project lacks rigor" or age-based assumptions phrased differently. The solution is to broaden the patterns to catch more variations of the same biased language.

**Branch name:** fix/151-broaden-bias-detector-patterns

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Selection notes:** 
I chose this issue because it has a clear title and description, which makes me fully understand what needs to be done and what files and functions were affected. It is a Tier 1 issue because it's my first open source contribution. The issue is not claimed and it's definitely realistic to complete within 2 weeks.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/mariiaonokhina/pathreview/commit/946592cf7f728cde8525c2c64ca8276c1900993b

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
There are 2 ways to reproduce this issue. First, I created a file called `test.py` (wasn't commited in the PR) and pasted the following code from the issue description:

```python
from safety.bias_detector import BiasDetector
print(BiasDetector.detect_bias('The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education'))
# observed: (False, '')  (expected: flagged as dismissive educational-background language)
```

When I ran the file, it returned that there is no bias (False), which is wrong.

Also, I ran `pytest tests/unit/test_bias_detector.py -v` and it showed that 9 tests are failing in the bias detector.

**PLAN.md link:** https://github.com/mariiaonokhina/pathreview/blob/fix/151-broaden-bias-detector-patterns/PLAN.md 

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I’ve reproduced the issue locally and started updating the bias detector patterns in the safety module. The first pass of the regex changes is in place for dismissive educational-background language, and I’m validating those cases against the existing bias detector tests.

**Next steps:**
I’m continuing to refine the patterns so they also catch the age and background-based assumptions from the issue without accidentally flagging neutral or positive feedback. After that, I’ll re-run the unit tests and do a final self-review.

**Blockers:**
I’m still checking the balance between broader matching and avoiding false positives, since the regexes need to be flexible enough to catch natural phrasing without over-matching "okay" descriptions.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/304 

**Branch:** fix/151-broaden-bias-detector-patterns

**What you built:**
I broadened the bias detector's regex patterns so it catches dismissive language about bootcamps, self-taught backgrounds, and online courses, as well as age- and background-based assumptions, even when those ideas are phrased differently. The change keeps neutral and positive mentions from being flagged while making the detector more accurate for the biased examples in the issue.

**Tests added or updated:**
I used and validated the existing unit tests in tests/unit/test_bias_detector.py. Those tests cover dismissive educational-language cases, demographic assumptions, positive/neutral mentions, and the detector's return value behavior.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Note** `make check` and `make test-unit` still show existing unrelated failures elsewhere in the repository. This change did not introduce any new failures

**Draft PR feedback received from:** N/A

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

N/A - no review.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

N/a

---

### Reflection

**What was harder than you expected?**

Understanding how the existing code fit together was harder than I expected. I thought I could move faster, but the project had more moving parts than I first realized and even the setup took a long time.

**What did you learn about working in a large codebase?**

I learned that working in a large codebase is very different from building something from scratch. In a personal project, you already know how all the parts connect and making a mistake is not critical. In a large codebase, small changes can affect other parts of the app, so you have to be careful and thoughtful. It is also important to understand the existing patterns before making changes.

**How did AI tools help — and where did they fall short?**

AI helped me move faster when I was stuck or trying to understand unfamiliar code. It was useful for getting to know the codebase and getting ideas on how to solve the issue I was working on. But it still needed a lot of review. I had to check the details myself and make sure the solution actually fit the project, as well as that it doesn't break any existing structure.

**What would you do differently if you started over?**

To be honest, I would spend more time reading the code and understanding the flow before I started changing things. I would also break the work into smaller steps and test earlier.

**What are you most proud of from this module?**

I am proud that I was able to work through a confusing codebase and complete a change that fit the project. I am also proud because this is my first open-source contribution and it opens the road for many of them to come later (because it won't feel as intimidating anymore).
