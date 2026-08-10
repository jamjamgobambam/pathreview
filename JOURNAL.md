## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers #146

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber currently detects and redacts US phone numbers written with dashes (for example, `555-123-4567`), but it fails to recognize the common parenthesized format `(555) 123-4567`. As a result, these phone numbers are left unredacted and are not reported by the detection logic. The issue affects the phone number matching logic in the PII scrubber, and a successful fix will ensure both formats are detected and redacted consistently while allowing the existing tests to pass.


**Branch name:** `fix/146-parenthesized-phone-redaction`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger






## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Kr1shna304/pathreview/commit/c74b86a903bca441acd64f2fdd050de49129105f

**Reproduction summary:**
Reproduced the issue by running the existing PII scrubber unit tests in `tests/unit/test_pii_scrubber.py`. The tests confirmed that phone formats such as `(555) 123-4567` and `+1 555 123 4567` are not detected by `PIIScrubber.detect()` and are not replaced by `[REDACTED]` in `PIIScrubber.scrub()`, while other supported formats like `555-123-4567` and `555.123.4567` continue to work.

**PLAN.md link:** https://github.com/Kr1shna304/pathreview/blob/fix/146-parenthesized-phone-redaction/PLAN.md

**Walkthrough video (recommended):** https://drive.google.com/file/d/1Iac2YRsVF7IFfWeLPvEOG8TDyjpD6Y_s/view?usp=drive_link

**Blockers or open questions:**
Pre-commit hooks currently report existing ruff and mypy issues unrelated to the phone number reproduction.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I analyzed the existing regex patterns from Subtask 1 to identify why certain phone number formats were not being detected. After identifying the missing cases, I updated the phone_us pattern to support those formats and validated that the detection logic worked as expected. Before making changes, I also ran make check and discovered that two test functions were incomplete. I reviewed those tests and noted the additional work needed before completing the implementation.

**Next steps:**
Implement the remaining PLAN.md subtasks (Subtasks 3 and 4), complete the two incomplete test functions, add any required test cases for the updated phone number pattern, run the full test suite and validation checks, and verify that the changes do not introduce any regressions.

**Blockers:**
None

---

### Check-in 2 (end of week)

**PR link:** [\[link to your submitted pull request\]](https://github.com/ascherj/pathreview/pull/605)

**Branch:** fix/146-parenthesized-phone-redaction

**What you built:**
Updated the PII scrubber to correctly detect and redact additional valid US phone number formats by modifying the phone_us regex pattern in pii_scrubber.py. I also adjusted the street address regex to resolve formatting issues and made minor code quality improvements, including fixing annotations, replacing an unused loop variable with _, and addressing formatting issues required for CI.

**Tests added or updated:**
Updated tests/unit/test_pii_scrubber.py by extending the existing test_detect_no_false_positives and test_address_variations tests to verify the updated phone number and address pattern behavior. I also added missing return type annotations in the test file to satisfy type-checking requirements.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
Yet to receive 

**How you responded:**
None

---

### Reflection

**What was harder than you expected?**
The first challenge was reproducing the issue. I initially thought I could simply install the project and go step by step, but personal system configuration issues made the setup more difficult than expected. I faced some challenges with Docker and getting everything running correctly. While investigating the issue and reviewing the existing test cases, I also discovered some problems that were outside the scope of the original issue. We separated those into different issues instead of trying to solve everything at once.


**What did you learn about working in a large codebase?**
When we build our own projects from scratch, we usually know the structure and understand where different pieces of code are located. However, in a large existing codebase, that understanding is not automatically there. Documentation and organization make a big difference in how quickly someone can understand and work with the code. I learned that real-world codebases are not always perfect, and before fixing a bug, we need to understand both the specific issue and the overall structure around it. Taking an organized approach makes it much easier to investigate, learn, and solve problems.

**How did AI tools help — and where did they fall short?**
AI was useful for understanding what particular functions were doing, how different parts of the code were connected, and which functions called each other. It also helped me understand functions at a high level without having to read every line of code, identify existing code patterns, write code based on specifications, create test cases, and work through some deployment-related code.
However, AI is only effective when we provide clear and specific context. It is not practical to simply ask it to understand an entire codebase, and sometimes it can miss important details. I also learned that AI should not make technical decisions for us. It can help us reason through the possible outcomes of a decision, but the final decision should come from our own understanding and judgment. 

**What would you do differently if you started over?**
I intentionally selected a relatively simple issue because I was still getting familiar with the codebase and wanted to start with an issue involving fewer file changes. Now that I have gained more experience with the project, I can better assess an issue before deciding how to approach it. I would first understand the scope, review the related code and tests, and do some initial testing to validate the problem before deciding on the implementation approach.

**What are you most proud of from this module?**
I am most proud of how much I learned about the overall codebase. I developed a high-level understanding of the project structure, including the tests, core functionality, RAG components, frontend, ingestion, safety, and other major areas. I then focused on the assigned issue, reproduced and investigated the problem, identified the underlying mistake, discovered additional issues and unwritten test cases, and ultimately resolved the core issue and submitted the PR.
This experience pushed me beyond simply writing code. I learned how to navigate an unfamiliar real-world codebase, investigate an issue systematically, understand existing patterns, validate a solution, and contribute through the complete development workflow. It made me feel that I was moving beyond being someone who just writes code and becoming a more well-rounded developer.