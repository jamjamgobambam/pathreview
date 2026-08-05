## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings #151

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

I picked this issue because: 

1. The solution looks appropriate and feasible for my skillset:
- It is a 'Tier 1' issue, which is the guidance for someone like me who is making their first open source contribution
- I've double-check from a global project search that class and method defined in `bias_detector.py` is limited to just that file and it's unit tests `test_bias_detector.py` -- so limited complexity and blast radius for any fix
- The identified code is in Python, which I'm comfortable with 

2. I've confirmed that it is a live issue by rerunning `test_bias_detector.py`. As reported, 9 unit tests are failing. 

3. It does not have a PR that fixes it, so I'm not duplicating or wasting effort.


**Problem summary:**

The method checks reviews for two types of bias -- dismissive assessments (e.g., "bootcamp graduates lack rigor") or demographic stereotypes (e.g, "young developers can't handle complex systems") -- and returns `is_biased == True` if bias is detected.    

However the regex patterns for `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` in `bias_detector.py` are too strict and miss other common phrasings that mean the same thing (e.g, "the candidate only attended a bootcamp, so this project lacks sufficient rigor"), resulting in some biased statements being marked as `is_biased == False`. 

My hypothesized solution is to make the regex less restrictive to catch a broader range of similar phrasing, so that those are properly assessed as `is_biased == True`. The known unknown is that I'm not familiar with regex so I don't know how effective the fix would be or how much effort is required. 

An alternative solution is to use LLM as a classifier, although the effort to implement and test this would likely elevate it to a higher issue tier. 

**Branch name:** fix/151-bias-detector-patterns

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 

https://github.com/chungmengcheong/pathreview/commit/2ac590662e70251df38bef162ed06975af6ed95b


**Reproduction summary:**

I added an additional unit test `test_dismissive_bootcamp_language_rephrased_detected` to verify that the bug reporter's rephrasing ("The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education.") is incorrectly passing the bias test. 

The new unit test and another 9 tests cited by bug reporter are failing as reported, i.e., incorrectly classifying biased test as `False`. See output of running of `.venv/bin/pytest tests/unit/test_bias_detector.py -v` below:

```

====================================================== short test summary info ======================================================
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_dismissive_bootcamp_language_detected - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_dismissive_bootcamp_language_rephrased_detected - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_bootcamp_lacks_rigor_detected - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_demographic_assumption_age_detected - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_coding_bootcamp_variant - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_developer_vs_programmer_distinction - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_multiple_bias_indicators - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_negative_educational_claim - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_rich_poor_assumption - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_assumption_vs_observation - assert False is True
=================================================== 10 failed, 23 passed in 0.17s ===================================================
```

**PLAN.md link:** [link to PLAN.md in your fork]

https://github.com/chungmengcheong/pathreview/blob/fix/151-bias-detector-patterns/PLAN.md


**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

No video

**Blockers or open questions:**

No blockers or open questions


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Per the plan, I have:

1. Refactored the regex patterns to generalize the concept of `SOURCE`, `PERSON`, `NEG_QUALITY` and `DESIRED_PROPERTY` to capture their synoymns and plurals, 

```
    SOURCE = r"(?:(?:coding\s+)?bootcamp|self-taught|online\s+(course)?)"
    PERSON = r"(?:graduates?|developers?|programmers?|person|people)"
    NEG_QUALITY = r"(?:insufficient|inadequate|lack|lacking|lacks)"
    DESIRED_PROPERTY = r"(?:code|rigor|fundamentals|proper\s+training|preparation)"
```

and then standardize their usage across all the regex expressions so that the overall set of expressions are simplified and more easily maintainable, e.g., 

```
        rf"(?:{SOURCE})\s+(?:education|training)\s+(?:is\s+)?{NEG_QUALITY}",
        rf"(?:{SOURCE})\s+attendance\s+means\s+({NEG_QUALITY})\s+{DESIRED_PROPERTY}",
```

2. Added a new pattern to connect those concepts within a sentence boundary, so that they don't have to be immediately next to each other to trigger a bias flag, i.e.:
```
        rf"(?:{SOURCE})\b"
        r"(?:[^.]){0,40}?\b(?:so|because|since|thus|therefore|which\s+means)\b(?:[^.]){0,30}?\b"
        rf"{NEG_QUALITY}\s+"
        rf"(?:the\s+)?{DESIRED_PROPERTY}\b",
```

3. Added a new unit test `test_dismissive_bootcamp_language_rephrased_detected` to verify that the alternative rephrasing reported in #151 is correctly flagged as bias. 


**Next steps:**

The refactoring are passing the unit tests and have addressed the issue. 

However, regex patterns are still deterministic pattern matching and more limited compared to a natural language classifier. I'll create a future enhancement request to refactor this module to an AI classifier if there is sufficient need. 

**Blockers:**

None

---

### Check-in 2 (end of week)

**PR link:** 

https://github.com/ascherj/pathreview/pull/378

**Branch:** 

`fix/151-bias-detector-patterns`

**What you built:**

- Refactored the regex patterns to generalize the concept of SOURCE, PERSON, NEG_QUALITY and DESIRED_PROPERTY to capture their synoymns and plurals, and then standardize their usage across all the regex expressions so that the overall set of expressions are simplified and more easily maintainable.
- Added a new pattern to connect those concepts within a sentence boundary, so that they don't have to be immediately next to each other to trigger a bias flag.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

- Added test_dismissive_bootcamp_language_rephrased_detected(self) in tests/unit/test_bias_detector.py to test that bias is detected for natural language rephrasings.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** 

@LeslieCodePath


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [X] Yes  [ ] No — still awaiting review

**Summary of feedback:**

@LeslieCodePath left three inline comments on `safety/bias_detector.py`: 
- two of the shared regex constants (`SOURCE`'s `online\s+(course)?` and `DESIRED_PROPERTY`'s `(proper\s+)?training`) used capturing groups whose output was never read, adding unnecessary overhead  
- the 30/40-character gap in my "connector" pattern (e.g., "bootcamp... so... lacks rigor") wasn't bounded by sentence punctuation, so it could span across unrelated sentences instead of staying within one dismissive claim; 
- a question on whether `re.DOTALL` was needed if the input could span multiple lines. They also left an encouraging general note that "regex is a bit of black magic" and that even once familiar with it, you can't judge how effective a pattern is until you test it.

**How you responded:**

- I fixed the two missed capturing groups to non-capturing groups. 
- For the sentence-boundary issue, I replaced the ad hoc `[^.]` gap with a shared `GAP` constant that excludes `.`, `!`, `?`, and newlines, so the pattern can no longer bridge across a real sentence or line break 
- For the `DOTALL` question, I checked the reasoning with Claude Code first: `DOTALL` only changes what `.` matches and wouldn't affect this pattern's boundary behavior, and enabling it to let `.*` cross newlines would have reopened the same false-positive risk the reviewer had just flagged — so I responded in the PR thread with that reasoning instead of applying the suggestion as-is.

---

### Reflection

**What was harder than you expected?**

Getting the regex patterns to actually work correctly took far longer than I expected. I now know what the PR reviewer meant by "even once you're very familiar w/ regex, it'll still be unclear... until you test it," :)

I was clumsy with the mechanics of doing the git workflow, and doing so correctly and professionally took nearly as much care as the code itself, specifically on making sure that:
- every clone, branch, commit, and pull request step was free of mistakes
- content at each step (commit messages, PR description, feedback responses) met the expected level of detail and style

**What did you learn about working in a large codebase?**

The biggest lesson was around "fitting in" to the existing codebase. I had to take time upfront to internalize the codebase's existing mental model, coding patterns, and style guidelines, especially when they differed from how I'd naturally approach something. 

I ended up refactoring the initial regex patterns in `bias_detector.py` to pull out and generalize SOURCE, PERSON, NEG_QUALITY and DESIRED_PROPERTY because I thought that made the code more readable and maintainable in the future. However that took up considerably more time for something that I didn't have to do in order to address the reported issue and make the code pass the failing unit tests. This was a trivial situation, but it has now made me more aware that I need to make a judgment call on whether to do a 'quick patch' or a more substantive refactoring when working on future issues.  

**How did AI tools help — and where did they fall short?**

For learning concepts, I used ChatGPT to learn regex from scratch and to decipher the intent behind the existing patterns in `bias_detector.py`. 

For the mechanics, I used Claude Code to double-check my work, decipher error and output messages from the command line, and walk me step-by-step through Docker and git CLI setup. 

The AI tools were also helpful in reasoning through a reviewer's suggestion rather than applying it blindly. I asked Claude whether `re.DOTALL` was needed for multi-line input, and it explained that `DOTALL` wouldn't fix the boundary issue and would reopen a false-positive risk already raised in review, which let me respond to the reviewer with an explanation rather than a guess.

**What would you do differently if you started over?**

If I were optimizing purely for time, I would have picked a different bug. The solution was clear after I had identified the issue (I needed to "loosen" the regex patterns), but I found regex to be difficult to build an intuition for and getting the patterns right was finicky work. 

**What are you most proud of from this module?**

I spent time scanning through parts of the codebase unrelated to my bug, and I'm proud that I understood both conceptually and mechanically much more of it than I expected going in. I feel more confident that I have a working sense of the patterns behind a modern AI application.