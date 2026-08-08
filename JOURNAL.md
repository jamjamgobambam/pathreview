## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/119

**Issue title:** Add inline docstrings to all public methods in core/services/

**Tier:** [ ] Tier 1 [X] Tier 2 [ ] Tier 3

**Problem summary:**
The public methods in the files under core/services don't have docstrings to explain what they do, what arguments they take, what they return, and any errors they may raise. A successful fix would make these methods easier to understand for any person who will later maintain this code base or needs to change any files/functionality in core/services. This problem affects the services layer of the code, but this fix is more important for maintainability down the line. I picked this problem because when I'm coding individually I normally don't put much effort into documentation. I think that getting practice with adding documentation to methods is going to be helpful for me if I work on a team at my work in the future.

**Branch name:** docs/119-services-methods-missing-docstrings

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/SahilMulki/pathreview/commit/6ea4b55a3e3c5b249c81aa15fe9d7cd4fbb02461

**Reproduction summary:**
This issue is a documentation issue, so it can't be reproduced in any traditional sense. This issue relates to the lack of inline docstrings for any methods in profile_service.py and review_service.py.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
None

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
So far I've done the first two steps of my plan. The first step was to read and deeply understand each method in the files in core/services. The second step was to review other docstrings in the repo to make sure that ones I write will follow the expected style and conventions.

**Next steps:**
For the rest of the week I will work on actually writing the docstrings. Then once they are written I will write tests and make sure that all tests pass. Then I will create a pull request and submit.

**Blockers:** none

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/475

**Branch:** docs/119-services-methods-missing-docstrings

**What you built:**
I added complete inline docstrings to profile_service.py and review_service.py. These docstrings are the full Google-style docstrings with Args:, Returns:, and Raises:. These docstrings also document the behavior of the method.

**Tests added or updated:**
I added a test under tests/unit/test_service_docstrings.py. This test checks all functions in core/services to make sure they have docstrings with sufficient detail (includes Args:, Returns:, and Raises:).

**Self-review confirmation:** [X] make check passes [X] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
None

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
None

---

### Reflection

**What was harder than you expected?**
I was surprised by the importance of docstirngs. Usually in my own code I don't spend much time to think about adding docstrings or other forms of documentation. Through this project I've learned a lot about the importance of documentation for readability and maintainability of code. It was also surprising how difficult it can be to understand someone else's code when there isn't sufficient documentation. For example some functions in core/services that I had to write doctrings for like delete_profile or process_review were complex and required understanding of the entire project.

**What did you learn about working in a large codebase?**
When contributing to someone else's production code you have to try to match their style and conventions as best you can. This makes your code easier to understand in the context of the whole repo. When I'm building my own project I set my own style and conventions.

**How did AI tools help — and where did they fall short?**
AI assistant was most useful in help to proofread and edit my docstrings. I needed to go beyond what AI could give me in the sense that I had to write the docstrings myself according to the Google conventions for docstrings which was required by the problem spec on GitHub. I also used AI to help understand the functions like list_reviews and get_review so that my docstring were more accurate.

**What would you do differently if you started over?**
If I started over I think that I would spend more time at the start reading through the code base so that I could better understand the style and conventions of the docstrings expected. Doing this before I started reading and trying to understand the functions I needed to add docstrings to would have saved me time. That's because I would have known better what I need to be on the look out for when readin the functions because I know what the docstring needs to contain (ex. inputs, outputs, error cases, etc.).

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I'm most proud of learning more about the importance of documentation and how to write good documentation. I think that strong documentation in my work will make me a better programmer. I believe that writing accurate docstrings is an often overlooked part of programming.
