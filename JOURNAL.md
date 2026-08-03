## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for `core/services/review_service.py` is below 40%

**Tier:** [] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review service is the core workflow for creating and processing portfolio reviews, but its important execution paths are not covered by unit tests. The missing coverage leaves the success path, partial failure path, and full failure path effectively unverified, which makes regressions harder to detect. A successful fix would add focused tests around the service logic in `core/services/review_service.py` so the behavior is exercised and documented.

**Branch name:** test/109-review-service-coverage

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Oreo236/pathreview/commit/91a3dc7c07b5918d45a14ebe66b816d2288966a6

**Reproduction summary:**
I reproduced the issue by running the review-service unit tests with coverage reporting. The current test run fails and does not provide meaningful coverage for the review workflow, confirming that the service’s main execution paths are not being exercised.

**PLAN.md link:** https://github.com/Oreo236/pathreview/blob/test/109-review-service-coverage/PLAN.md

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
None at the moment; the next step is to add focused tests around the success and failure branches in the review workflow.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reproduced the issue by running the review-service tests and confirmed that the main workflow branches were not being exercised well. I also created a plan in [PLAN.md](PLAN.md) and started adding focused tests for the review workflow.

**Next steps:**
I’m finishing the targeted unit tests for the review-service success and failure branches and verifying them with pytest.

**Blockers:**
None at the moment.

---

### Check-in 2 (end of week)

**PR link:** Not submitted yet

**Branch:** `test/109-review-service-coverage`

**What you built:**
I added targeted unit tests for the review-service workflow in [tests/unit/test_review_service.py](tests/unit/test_review_service.py). The new tests cover review creation, review lookup, safety-check failure, missing-profile failure, and missing-review early exit.

**Tests added or updated:**
Updated [tests/unit/test_review_service.py](tests/unit/test_review_service.py) to cover the main review-service execution paths.

**Self-review confirmation:** [x] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback

**How you responded:**
No changes were needed in response to reviewer feedback.

---

### Reflection

**What was harder than you expected?**
The hardest part was understanding the service’s intent. It required more careful reading than I expected, especially when the code was working but the edge cases were not clearly documented.

**What did you learn about working in a large codebase?**
Working in a larger codebase taught me that contribution is about more than making a change that passes locally. It is also about reading surrounding patterns, respecting existing conventions, and making sure a change fits the expectations of the project rather than just solving the immediate problem in an isolated way.

**How did AI tools help — and where did they fall short?**
AI tools were helpful for quickly suggesting test cases, explaining unfamiliar functions, and helping me think through the service’s likely success and failure paths. They were less reliable when it came to judging whether a test reflected the intended product behavior rather than just the current implementation, so I had to verify the logic by reading the relevant code and aligning the tests with the service’s actual contract.

**What would you do differently if you started over?**
If I started over, I would map the important execution paths of the service more explicitly before writing tests, so I could focus on the highest-value branches first. I would also spend more time capturing the reasoning behind each test case in my notes and PR description so the purpose of the coverage work is easier for others to understand.

**What are you most proud of from this module?**
I am most proud of creating, understanding, fixing some of the previous test and my new test. It was a very fun journey.