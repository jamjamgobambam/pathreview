# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bias detector currently relies on regular-expression patterns that expect very specific sequences of words. Because the patterns are too restrictive, the detector misses natural sentences that express educational-background or age-related assumptions, even when the meaning is biased. This affects the bias-detection logic and causes several expected cases in `tests/unit/test_bias_detector.py` to fail. A successful fix will broaden the relevant patterns so they recognize the documented phrasings without incorrectly flagging unrelated language.

**Selection notes — “Is this right for me?” reasoning:**
This issue has a focused scope because it primarily involves the bias detector and its related unit tests. The issue includes examples of currently missed language and identifies the tests that document the expected behavior, giving me a clear way to reproduce and verify the problem. I have experience with Python, regular expressions, unit testing, and an AI-bias analysis project, so the technical area is appropriate for me. The main risk is making the patterns too broad and introducing false positives, so I will review the existing implementation carefully and run the complete bias-detector test suite after making changes.

**Branch name:** `fix/151-bias-detector-patterns`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Note Reproduction

**Issue:** Bias detector patterns are too narrow to match common phrasings
**Issue link:** `https://github.com/ascherj/pathreview/issues/151`
**Branch:** `fix/151-bias-detector-patterns`

### Reproduction

From the repository root, I ran:

```bash
source .venv/Scripts/activate
python -m pytest tests/unit/test_bias_detector.py -q
```

The test suite returned **9 failed and 23 passed**. In the failing cases, `BiasDetector.detect_bias()` returned `(False, "")` for statements containing dismissive educational language or demographic assumptions.

For example:

```python
BiasDetector.detect_bias(
    "bootcamp graduates can't write production code"
)
```

Observed:

```python
(False, "")
```

Expected:

```python
(True, "Dismissive language about educational background")
```

The issue appears in `safety/bias_detector.py`, where the patterns in `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` are too narrow to recognize common wording variations.

No production code was changed during reproduction.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** `https://github.com/zero3119/pathreview/commit/a7e29c920e1615e4b62be8b4935912ccfc045fb9`

**Reproduction summary:**

I reproduced Issue #151 by running `python -m pytest tests/unit/test_bias_detector.py -q`. Nine tests failed because the current regular expressions returned `(False, "")` for common phrasings of dismissive educational-background language and demographic assumptions.

**PLAN.md link:** `https://github.com/zero3119/pathreview/blob/fix/151-bias-detector-patterns/PLAN.md`

**Blockers or open questions:**

The main open question is how much flexibility to add between related regex terms without causing false positives for the positive, factual, and neutral examples in `tests/unit/test_bias_detector.py`.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed the local reproduction and solution-planning work for Issue #151. I confirmed that the focused bias-detector test suite produces 9 failing tests and 23 passing tests because `BiasDetector.detect_bias()` does not recognize several common forms of dismissive educational-background language and demographic assumptions. I have also identified `safety/bias_detector.py` and `tests/unit/test_bias_detector.py` as the primary files involved.

**Next steps:**
I will compare each failing test with the existing bias patterns, update the relevant patterns incrementally, and run the focused unit tests after each change. I will also add or verify negative test cases for neutral statements, run `make check` and `make test-unit`, open a draft pull request, and request peer or mentor feedback.

**Blockers:**
The main risk is expanding the patterns too broadly and causing neutral statements to be incorrectly flagged. I also need to verify whether overlapping matches are expected to return a particular bias explanation.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/736

**Branch:** `fix/151-bias-detector-patterns`

**What you built:**
I expanded the regular-expression patterns in `safety/bias_detector.py` so the bias detector recognizes more natural forms of dismissive educational-background language and demographic assumptions. The updated patterns support additional wording variations, contractions, plural subjects, and longer phrases while using bounded matching to reduce false positives.

**Tests added or updated:**
I added `tests/unit/test_bias_detector_issue_151.py`. The tests cover the longer bootcamp-dismissal wording from Issue #151, an age-related assumption expressed through contextual language, and a neutral bootcamp statement that must remain unflagged.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

`make check` reported pre-existing repository-wide lint failures in unrelated files. I documented those failures in the PR and verified that `safety/bias_detector.py` and `tests/unit/test_bias_detector_issue_151.py` do not introduce new linting, formatting, or type-checking failures.

**Draft PR feedback received from:** None


## Week 10 — Iteration & Reflection

### Reviewer Feedback

**Feedback received:** [ ] Yes  [x] No — review was not required

**Summary of feedback:**
No reviewer feedback was received because the summer course did not require a formal review.

**How you responded:**
No reviewer feedback was received because the summer course did not require a formal review.

---

### Reflection

**What was harder than you expected?**
Reading and understanding the codebase was harder than I expected. I had worked with other people’s code and legacy code before, but I had never needed to understand a codebase almost entirely from scratch. Usually, someone was available to help explain how everything worked. In this project, I was sometimes only given the name of a file and had to examine several other files to understand how they were connected. Even with the help of AI tools, it took time to understand the different files, functions, and relationships within the project.

**What did you learn about working in a large codebase?**
I learned that understanding the codebase is essential. Only reading isolated sections of code makes it difficult to understand the larger system and can make the development process slower. You do not need to understand every part of the codebase perfectly, but you should understand the section you are working on and how it connects to other components that may be affected by your changes.

**How did AI tools help — and where did they fall short?**
AI tools were especially helpful for summarizing code and explaining sections that I had difficulty understanding. They also helped me write certain parts of the implementation that would have taken me much longer to complete on my own. However, AI tools sometimes added, removed, or changed specific sections unnecessarily. Because of this, it was important to carefully review every suggestion and make corrections when necessary.

**What would you do differently if you started over?**
I would begin planning, commenting, and documenting my work earlier. At times, I started coding without creating a clear plan, which caused the work to become disorganized. Later in the module, I began planning before coding, and the process became much faster and easier. My comments and documentation also helped me remember what had already been completed and what still needed to be done whenever I stepped away from the computer and returned later.

**What are you most proud of from this module?**
I am most proud that I completed my first pull request. More specifically, I am proud of how much my commenting and documentation skills improved. I also learned a great deal about AI, but without improving my documentation skills, it would have been much more difficult to understand the project and successfully complete my contribution.
