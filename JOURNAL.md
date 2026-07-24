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

**Reproduction commit link:** https://github.com/ascherj/pathreview/issues/146

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
N/A