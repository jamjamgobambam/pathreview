## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/72

**Issue title:** Add a bias audit report that runs over a sample of stored reviews

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
PathReview has a bias detector, but there is not yet an offline audit report that checks how that detector performs across a sample of stored reviews. This means the project has limited visibility into where the detector may create false positives or false negatives, especially when review text includes demographic signals. A successful fix would add a script that samples stored reviews, runs them through the bias detector with clear logging, and produces a report summarizing the results. The work should mainly affect `scripts/audit_bias.py` and `safety/bias_detector.py`.

**Branch name:** feat/72-bias-audit-report

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/antunishdPursuit/pathreview/commit/fc3d948dca0a39e1a8e9d5c88395f226fa9165bc

**Reproduction summary:**
I reproduced issue #72 as a missing-feature gap. The expected offline audit script, `scripts/audit_bias.py`, does not exist, while the reusable bias detection logic exists in `safety/bias_detector.py` through `BiasDetector.detect_bias(text)`.

**PLAN.md link:** https://github.com/antunishdPursuit/pathreview/blob/feat/72-bias-audit-report/PLAN.md

**Walkthrough video (recommended):** https://www.loom.com/share/a48973d934254ea8b9481bd80d1d820e

**Blockers or open questions:**
I still need to confirm which stored review source should be sampled and how the report should label false positives and false negatives when there is no existing ground-truth dataset.

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** I implemented the offline bias audit for Issue #72. The script samples up to 100 completed stored reviews, combines each review's content and suggestions, runs the existing bias detector, logs each result, and generates an editable JSON report. The same script can be edited by a human to add human labels and then calculate false-positive and false-negative rates by demographic signal. I also added three unit tests that passed.

**Next steps:** Run the remaining repository checks, document unrelated existing failures, push the branch, open a draft pull request against the upstream repo, and complete Check-in 2 with the final PR information.

**Blockers:** The local database contains only five eligible completed reviews, so the audit cannot demonstrate a full 100-review sample. The full unit suite currently reports 53 failures in unrelated test files, while all three tests for the audit workflow pass.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/763

**Branch:** `feat/72-bias-audit-report`

**What you built:** I built an offline bias audit that samples completed stored reviews, runs their combined content and suggestions through the existing bias detector, and generates an editable JSON report. After human labels are added, the same script can calculate false-positive and false-negative rates by demographic signal and generate an evaluated report.

**Tests added or updated:** I added `tests/unit/test_audit_bias.py` with three tests covering review-text extraction, labeled report evaluation and temporary-file cleanup, and invalid demographic signal rejection. All three audit tests pass. The full unit suite reported 378 passed and 53 failures in unrelated test files.

**Self-review confirmation:**
[x] `make check` introduces no new failures in the changed files. Focused Ruff, Black, and mypy checks pass. The repository-wide lint step stops on 182 unrelated existing errors.
[x] `make test-unit` introduces no new audit failures. All three audit tests pass, while the repository-wide suite has 53 failures in unrelated test files.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No

**Summary of feedback:** No reviewer feedback was provided during Summer 2026.

**How you responded:**

---

### Reflection

**What was harder than you expected?**

The hardest part was making sure the AI stayed focused on Issue #72. Sometimes it tried to fix unrelated problems or expand the solution by adding more tests and changes than the issue required, so I had to keep bringing it back to the approved scope. It was also difficult to decide how to test the bias audit when the database contained only five eligible reviews instead of the requested sample of 100, and I ultimately decided to use the available reviews rather than invent data.

**What did you learn about working in a large codebase?**

Working in a large codebase taught me how important it is to understand where files and functions belong before changing anything. For Issue #72, I had to determine that the new audit belonged in `scripts/audit_bias.py`, understand how it would load reviews, and reuse the existing `BiasDetector` without modifying it because our task was to evaluate the detector. I also learned to keep track of the files I touched and how they interacted so that a narrow change would not affect unrelated behavior.

**How did AI tools help — and where did they fall short?**

AI tools helped me research the codebase, understand existing functions, write parts of the audit script, and develop tests. They fell short when the requirements were unclear, and they sometimes tried to fix unrelated problems, add more tests, or expand the solution beyond the issue. I still had to decide whether to use only the five stored reviews, whether creating additional data was appropriate, and how human labels should be added before calculating false-positive and false-negative rates.

**What would you do differently if you started over?**

If I started over, I would read the issue and nearby code more deeply before implementing anything, and I would ask the maintainers more specific questions when the requirements were unclear. This could have clarified whether the sample of 100 was a strict requirement, how ground-truth labels should be established, and what report format they expected. I might also choose a more challenging issue that would expand my abilities while still keeping the implementation narrowly focused.

**What are you most proud of from this module?**

I am most proud that I completed the assignments and applied lessons from earlier AI 201 projects to the final pull request. For Issue #72, I built a flow that loads stored reviews, generates an editable JSON report for human labels, and processes the updated report to calculate the final metrics without modifying `BiasDetector` or inventing data. I am also proud that the course helped me make better architecture decisions, explain the code more clearly in interviews, and apply what I learned during a hackathon.

