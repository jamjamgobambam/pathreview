# Week 7 — Issue selection

**Issue link:** Link: https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1 &nbsp;&nbsp; [ ] Tier 2 &nbsp;&nbsp; [ ] Tier 3

**Problem summary:**

> [In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
> the title), what is currently broken or missing, and what a successful fix
> would accomplish. Naming the part of the codebase it affects is helpful context.]

In the system, the bias detector isn't able to detect phrases that contain bias
without using the near-exact phrases such as "bootcamp graduates lacks rigors".
When phrases with similar meaning are provided, the system fails to detect the
bias, such as "The candidate only attended a bootcamp, so this project lacks the
rigor of a formal CS education". This issue is related to the `detect_bias`
function in the `bias_detector.py` in the `safety` directory. 9 test cases in
`tests/unit/test_bias_detector.py` failed as well.

**Branch name:** `fix/151-bias-detector-patterns-too-narrow-to-match-common-phrasings`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Work Progress**
Was able to reproduce the issue by running the following command: 
(.venv) cxu@MacBookAir pathreview % python3 -c "                                                                               
from safety.bias_detector import BiasDetector
print(BiasDetector.detect_bias('The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education'))
"
(False, '')
- not much risks because - Looks like only the test_bias_detector and the actual bias_detector will be impacted - no other files will be impacted

Test Cases:
Phrases with similar meaning don't get detected, it has to be nearly the exact phrase

(.venv) cxu@MacBookAir pathreview % cd /Users/cxu/PycharmProjects/AI_Projects/pathreview
./.venv/bin/python -m pytest tests/unit/test_bias_detector.py -v

The 9 failing tests, grouped by what breaks
Test	Input	Why the current regex misses it
test_dismissive_bootcamp_language_detected	"bootcamp graduates can't write production code"	patterns only allow lack/missing, not can't
test_coding_bootcamp_variant	"coding bootcamp graduates can't write..."	same — no can't verb
test_developer_vs_programmer_distinction	"bootcamp developers can't...", "bootcamp programmers lack..."	developers not in the subject group; programmers not listed at all
test_bootcamp_lacks_rigor_detected	"bootcamp education lacks fundamentals"	pattern requires is insufficient/lacks — the word is is mandatory
test_negative_educational_claim	"self-taught developers are not equal to university graduates"	pattern requires self-taught IS not equal — no room for developers ... are
test_assumption_vs_observation	"bootcamp attendance means inadequate training"	no pattern for means inadequate
test_demographic_assumption_age_detected	"young developers can't..."	developer is singular-only; also reason must contain "demographic"
test_rich_poor_assumption	"developers from poor backgrounds can't afford..."	pattern is person from poor, doesn't allow developers from poor
test_multiple_bias_indicators	combines the above	fails because its parts fail

Solution Plan:
Change the design a little bit
It's doing the exact pettern check to to see if the word sequence contains any keywords in the pattern phrase, not an efficient approach to do it
- Switch design decision - I'd create a list of subjects and negative words from the failing tests so that by using the two lists, it helps to detect a subject signal with a negative predicate. 

First List: Subjects - Ex. bootcamp, self-taught, online courses, etc.
second List: Negative Predicates - Ex. cannot, lack/missing/insufficient, etc.

Then use the failed tests as guardrails so they don't create false positives - meaning make sure the nagative phrase do get flagged


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [JOURNAL.md](JOURNAL.md)

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I was able to reproduce the issue running the following command: python3 -c "from safety.bias_detector import BiasDetector
print(BiasDetector.detect_bias('The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education'))". I noticed when the phrase "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education" is passed into the function, the bias detector is not able to detect the bias, and return "False" as the result. Only when an explicit exact phrase is passed into the function, such as "bootcamp graduates lack rigor", then the bias detector is able to detect the bias by returning a warning with a reason "Dismissive language about educational background".

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** [Walkthrough_Video](pathreview/video1318638326.mp4)

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I've created a plan to fix the issue. I haven't started implementing the steps in the plan yet.

**Next steps:**
For the rest of the week, I'm working to implement the steps in the plan and create test cases for the added code/implementation.

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:**
`fix/151-bias-detector-patterns-too-narrow-to-match-common-phrasings`

**What you built:**

I changed the implementation design so that, instead of performing an exact keyword-pattern check in the text, it uses a combination of educational subjects, demographic subjects, and negative predicates to detect whether the text is biased while not triggering false alerts when the text contains parts of the keywords but does not contain bias or judgments.


**Tests added or updated:**

I added five more test cases to `test/test_bias_detector.py`:

- `test_co_occurrence_does_not_depend_on_word_order`: Tests whether the bias detector can detect bias without the exact word order—for example, when a negative predicate appears before the educational subject.
- `test_single_signal_without_co_occurrence_not_flagged`: Tests that text containing only a subject or only a negative predicate is not flagged as biased, preventing false positives.
- `test_demographic_category_takes_precedence_when_both_match`: Tests that, when both subject categories (educational and demographic subjects) appear, the demographic category takes precedence in bias detection.
- `test_detected_bias_emits_monitoring_warning`: Tests that the bias detector emits monitoring-event warnings when it detects bias.
- `test_unbiased_feedback_does_not_emit_monitoring_warning`: Tests that the bias detector does not trigger an alert when it does not detect bias in the text.


**Self-review confirmation:** [x] `make check` passes  [x] `make test-unit` passes

I was able to verify that the failures I encountered when I ran `make check` and `make test-unit` were not related to my fix by running the following commands:

```bash
.venv/bin/ruff check safety/bias_detector.py tests/unit/test_bias_detector.py
.venv/bin/black --check safety/bias_detector.py tests/unit/test_bias_detector.py
.venv/bin/mypy safety/bias_detector.py
.venv/bin/pytest -q tests/unit/test_bias_detector.py
```


**Draft PR feedback received from:**

Slack


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review; no feedback for Summer 2026

**Summary of feedback:**

[What did reviewers comment on? Or note that no review came in.]

N/A

**How you responded:**

[What changes did you make, or what did you reply? If no feedback,
leave blank.]

N/A

---

### Reflection

**What was harder than you expected?**

[Be specific — what part of the process, codebase, or workflow
surprised you?]

The setup process surprised me. When we were setting up the project, I didn't expect installing Docker, PostgreSQL, and the required software to take so much time or be so complex.

**What did you learn about working in a large codebase?**

[What's different about contributing to someone else's production code
vs. building your own project?]

What is different about contributing to someone else's production code compared with building your own project is that, when building your own project, you understand how it is built. When you modify the project or fix errors, if your changes cause other errors, you can modify them and add notes for your own reference. However, when contributing to someone else's codebase, you need to be very careful because some features may have been created by other developers who had specific intentions when they built them in certain ways. You don't want to modify the codebase and trigger other errors. Therefore, clear communication and creating a structured, clear PR are important.

**How did AI tools help — and where did they fall short?**

[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

AI assistance was helpful in understanding how the feature is used and how it relates to or interacts with other files. It also helped generate test cases. At the same time, some AI-generated test cases introduced new errors related to logs. I had to examine and correct the test cases myself to ensure they worked properly.

**What would you do differently if you started over?**

[Issue selection, planning, implementation, or process — anything
you'd change?]

I should have tested the application before making my implementation change because, when I ran the application, it returned many errors related to other features. Even though I was able to verify after my fix that the returned errors were not related to my implementation, testing beforehand would have helped me make a more accurate comparison—for example, how many errors existed before my fix versus after it.

I should probably have chosen a more difficult issue because my issue is Tier 1 and only affects a few files. I would like to challenge myself more.

**What are you most proud of from this module?**

[One thing — it doesn't have to be the PR itself.]

I'm proud that I was able to work in an unfamiliar codebase, identify an issue, reproduce it, and develop a plan to fix it.
