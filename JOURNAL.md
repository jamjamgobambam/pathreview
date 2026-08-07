# Week 7 — Issue Selection

---

## Issue 1

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** 1

### Problem Summary

Inside the `create_review_endpoint` route, the profile ID and user ID are passed into `create_review`, but the application never verifies that the authenticated user actually owns the profile. This allows users to create reviews for themselves, resulting in invalid self-reviews. The fix is to verify profile ownership before creating the review, preventing self-reported reviews and eliminating redundant logic.

**Branch name:** `fix/163-review-creation-does-not-verify-profile-ownership`

**Setup confirmation:** [✅] App runs locally at `localhost:5173`

**Cohort ledger:** [✅] Issue added to cohort ledger

### Reviewer Feedback

**Received reviewer feedback:** [ ] Yes [✅] No

I did not receive reviewer feedback before submitting this assignment.

---

## Issue 2

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** 3

### Problem Summary

When the agent loops through reviews inside `orchestrator.run()`, it appends each completed review to `result` but does not save the state after each iteration. If the application crashes before the loop finishes, all in-progress work is lost. At first, I planned to create a new `CrashedReview(Base)` model to store progress. After spending more time reading the codebase, I discovered that `SessionStore` already existed and was designed for this purpose. The correct solution was simply to persist the session after each completed review by updating `SessionStore`.

**Branch name:** `fix/47-agent-state-isnt-persisted-across-restarts`

**Setup confirmation:** [✅] App runs locally at `localhost:5173`

**Cohort ledger:** [✅] Issue added to cohort ledger

### AI Usage

I used Gemini to help confirm whether I was looking in the correct part of the codebase. It helped point me toward the relevant files, but it did not generate the implementation or solve the issue for me. Initially, I was convinced I needed to create a separate `CrashedReview` model that stores reviews during loop then deletes when done, but after reading the existing code more carefully, I realized `SessionStore` already handled the functionality I needed. The experience reminded me that AI can help with navigation, but understanding the existing code is still essential.

### Reviewer Feedback

**Received reviewer feedback:** [ ] Yes [✅] No

I did not receive reviewer feedback before submitting this assignment.

---

# Reflection

### 1. What was harder than you expected?

The hardest part was Issue #47 because I initially approached the problem with the wrong assumption. I spent several hours planning to create a new `CrashedReview` model before realizing that the existing `SessionStore` already solved the persistence problem. Looking back, the challenge wasn't writing the code, it was understanding how the existing system worked.

### 2. What did you learn about working in a large codebase?

I learned that reading and understanding the existing codebase is often more important than immediately writing new code. My first instinct was to build a new solution, but the project already contained the functionality I needed. Taking more time to follow the flow of the application would have saved me several hours.

### 3. How did AI tools help—and where did they fall short?

Gemini was useful for helping me locate the general area of the project that I needed to investigate. However, it did not solve the issue or identify the existing `SessionStore` implementation for me. I still had to read the code myself, understand how it worked, and decide on the correct implementation.

### 4. What would you do differently if you started over?

If I started over, I would spend more time reading through the existing files before designing my own solution. I would trace the application's execution path and look for existing models or services before assuming something new needed to be created. That approach would have made the debugging process much faster.

### 5. What are you most proud of from this module?

I'm most proud that I stayed persistent even when I was stuck for several hours. Instead of giving up, I continued investigating until I understood how the codebase worked and found the correct solution. Solving Issue #47 taught me the value of patience and careful reading when working in unfamiliar projects.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ONESO-goat/a201-pathreview/tree/fix/146-scrubber-fails-to-redact-parenthesized-us-phone-numbers

**Reproduction summary:**

I just created a test string hoarding data that matches the listed formats that should be redated after scrub.

**PLAN.md link:** https://github.com/ONESO-goat/a201-pathreview/blob/fix/146-scrubber-fails-to-redact-parenthesized-us-phone-numbers/PLAN.md

**Blockers or open questions:**
N/A


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the core sub-tasks from PLAN.md: configured structlog for testing environments and refactored test_empty_chunks_list_returns_empty in tests/unit/test_batch_processor.py.

**Next steps:**
Get the work reviewed and verify test suites pass locally.


**Blockers:**
N/A

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/461

**Branch:** 159-structlog-output-is-not-captured

**What you built:**

Migrated the original logging logic from the package `logging` towards the package `structlog`. Added custom fixtures to bridge structlog outputs with pytest's caplog mechanism.

**Tests added or updated:**

- `unit/conftest.py`
* Added the function `_test_loggings` that test text, while `logger = logging` handles the error messages.
* Added the function `_test_structlogs` that test text, while `logger = structlog` handles the error messages.

Created

```python
class TestConfigs:
    """Test suite for validating fixtures and log outputs."""
    
    def test_text(self, caplog):
        ...
```

To test the functions created.

After testing in `/unit/conftest.py`, move back to `/unit/test_batch_processor.py` to test out the new knowledge on loggings in python.

There, with the help of Gemini I added:

```python
  @pytest.fixture(name="caplog")
    def fixture_log_output(self):
        """Since we are using structlog, we should be using this"""
        return LogCapture()
    
    @pytest.fixture(autouse=True)
    def fixture_configure_structlog(self, caplog):
        # redirects all output from structlog logger to pytest fixture wrapper
        structlog.configure(processors=[caplog])
```

* `fixture_log_output()` is a pytest fixture of structlog logs, similar to caplog of logging.

* `fixture_configure_structlog` makes sure that when a log is captured, it sends it to the pytest fixture_log_output fixture.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [] Yes  [X] No — still awaiting review

**Summary of feedback:**
I haven't received a review yet.

**How you responded:**
Thought "Where in the world is my review?" and checked the repository pull request notifications multiple times.

### Reflection

**What was harder than you expected?** 

The harder part was forcing myself to sit down and read someone else's raw code line-by-line without leaning on an AI to summarize everything for me. Breaking that instant-gratification habit and manually parsing another developer's logic structure proved to be a genuinely challenging mental hurdle. It was an interesting and necessary process, but definitely required a lot more sustained focus than I anticipated.

**What did you learn about working in a large codebase?**

I learned to actively search for the core "nutshell" components rather than getting bogged down in individual implementation files right away. This includes reading high-level documentation, examining the core data models, and checking function naming conventions first. Doing this helps grasp the architectural intent of the code quickly, rather than jumping straight into debugging a specific problem blindly.

**How did AI tools help — and where did they fall short?**

I primarily used AI to aid with debugging complex error traces or to quickly remind me of specific Git commands. Where AI fell short was in helping me understand the unique, domain-specific logic of the repository's existing codebase, which required human reading. I relied on it the most during a tedious rebase conflict, as I was fairly new to handling merge conflicts and it wasn't the simple "add, commit, push" workflow I was used to.

**What would you do differently if you started over?**

If I started over, I would rely much less on quick AI prompts and instead dive straight into official documentation and targeted Google searches to understand the underlying core concepts. Taking the extra time to read the primary documentation would have built a stronger mental model of Git rebasing and code architecture from day one. It would have saved me a lot of trial-and-error guessing in the terminal.

**What are you most proud of from this module?**

I am most proud of successfully navigating the end-to-end process of preparing, committing, and uploading my code while managing my first major branch rebase. Overcoming the anxiety of potentially breaking the build and learning how to safely push my contributions gave me a huge confidence boost. It made me feel like a much more capable software developer ready for collaborative environments.

