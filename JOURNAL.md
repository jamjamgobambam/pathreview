# AI201 Module 3 – Open Source Contribution Journal

**Name:** Kevin Balbuena Montes  
**Course:** CodePath AI201  
**Module:** Module 3 – Open Source Contribution  
**Issue:** #71 – Prompt Injection Red-Team Test Suite  
**Repository:** PathReview  
**Branch:** `test/71-prompt-injection-red-team`

---

# Week 7

## Issue Selection

**Selected Issue:** [Issue #71 – Implement a Red-Team Test Suite for the Prompt Injection Defense](https://github.com/ascherj/pathreview/issues/71)

**Issue Tier:** Tier 3

For my open-source contribution, I selected Issue #71, which focuses on strengthening the project's protection against prompt injection attacks by creating an automated red-team test suite.

Prompt injection is a technique where a user attempts to manipulate an AI system into ignoring its original instructions or following malicious commands. Although the project already includes a `PromptDefense` class and several unit tests, it does not yet have a dedicated red-team test suite with a curated collection of realistic prompt injection attacks. The issue also requests adding reusable fixtures and ensuring these security tests run automatically in CI whenever the safety layer is modified.

A successful solution will create the missing security test suite, organize realistic prompt injection examples into reusable fixtures, verify that known attacks are detected or blocked by the safety layer, and integrate these tests into the project's automated testing workflow.

This issue is labeled **Tier 3**, meaning it is intended to be more challenging than a typical beginner contribution. I intentionally selected it because it closely aligns with my career interests in cybersecurity, AI security, and secure software engineering. While I expect to spend additional time understanding the existing codebase, I believe the challenge will help me improve my ability to analyze unfamiliar security code, design meaningful automated tests, and contribute to a real open-source project. My plan is to approach the work incrementally by first understanding the current implementation before adding new tests and fixtures.

---

## Repository Setup

During Week 7, I completed the initial setup required before beginning development.

I successfully:

- Forked the PathReview repository to my GitHub account.
- Cloned my fork to my local development environment.
- Added the original repository as the upstream remote.
- Verified my Git configuration.
- Installed and configured the required development tools.
- Created a dedicated feature branch named `test/71-prompt-injection-red-team`.
- Claimed Issue #71 on GitHub to let the maintainers know I would be working on it.

Completing these setup tasks prepared my development environment so I can begin investigating the project without modifying the main branch.

---

## Initial Investigation

Before writing any code, I explored the project structure to better understand how prompt injection protection is currently implemented.

I located the existing PromptDefense tests and reviewed the different types of attacks that are already being checked. These include role-switching attempts, template injection, instruction overrides, separator-based attacks, and sanitization behavior.

While reviewing the existing tests, I noticed that the project already has unit tests for individual detection methods. My next goal is to understand whether there are realistic prompt injection techniques that are not currently covered by automated testing.

Rather than immediately writing code, I want to first understand how the current implementation works and identify where additional security coverage is needed.

---

## What I Learned

This week helped me better understand the typical workflow for contributing to an open-source project.

Before making any code changes, contributors usually:

- Read the issue carefully.
- Set up the development environment.
- Create a separate feature branch.
- Investigate the existing implementation.
- Understand the current test coverage.
- Plan the solution before writing code.

I also learned that security testing is not only about finding vulnerabilities, but also about making sure legitimate user input is not incorrectly blocked by defensive rules.

---

## Goals for Week 8

During the next phase of this project, I plan to:

- Review the `PromptDefense` implementation.
- Understand how prompt injection detection currently works.
- Identify missing attack scenarios.
- Design a reusable prompt injection test suite.
- Create realistic prompt injection fixtures.
- Verify that the new tests integrate correctly with the existing testing framework.
- Begin implementing the solution for Issue #71.

---

## Reflection

This project is already different from my previous programming assignments because I am working with an existing codebase written by other developers instead of starting from scratch.

My goal is not only to complete the assignment, but also to learn how experienced software engineers investigate security problems, understand unfamiliar code, and contribute improvements through testing and collaboration.


## Week 8 — Reproduction & Solution Planning

**Reproduction commit link:**
https://github.com/Ataliosos/pathreview/commit/e4a6351

**Reproduction summary:**

I reproduced the feature gap described in Issue #71 by reviewing the existing prompt injection defense implementation and running the current unit tests. I inspected `safety/prompt_defense.py` and `tests/unit/test_prompt_defense.py`, which contain the current prompt injection detection logic and unit tests.

I also confirmed that the project does not contain the dedicated red-team security test suite (`tests/security/test_prompt_injection.py`) or the reusable prompt injection fixture directory (`tests/fixtures/injection_attempts/`) described in the issue. This confirms the missing functionality requested by Issue #71.

**PLAN.md link:**
https://github.com/Ataliosos/pathreview/blob/test/71-prompt-injection-red-team/PLAN.md

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**

While reproducing the issue, I observed that one existing unit test (`test_whitespace_variations_detected`) currently fails because the regular expression does not detect role names followed by spaces before the colon (for example, `System  :`). This appears to be separate from Issue #71, so I plan to keep my implementation focused on the requested red-team test suite.

## Week 9 – Pull Request Submission

### Check-in 1 (Mid-Week Progress)

**Current Progress:**

This week I completed the implementation of the red-team prompt injection security test suite for Issue #71. I created the new `tests/security/test_prompt_injection.py` file and organized reusable test data into the new `tests/fixtures/injection_attempts/` directory. The fixture directory now contains separate JSON files for known attacks, legitimate (benign) prompts, and documented prompt injection bypasses.

I also configured the test suite to load fixture data from JSON files instead of hardcoding every test case inside the Python file. This makes the tests easier to maintain and allows additional prompt injection examples to be added without modifying the test logic.

Finally, I created a dedicated GitHub Actions workflow (`.github/workflows/security.yml`) so the prompt injection security tests can run automatically during continuous integration.

**Next Steps:**

Before submitting my pull request, I still need to:

- Run Ruff and Black to verify formatting.
- Run the complete prompt injection security test suite.
- Review the code one final time.
- Push my completed commits to GitHub.
- Open a Pull Request against the upstream repository.

**Blockers:**

None.

---

### Check-in 2 (Final Submission)

**PR Link:**

`https://github.com/ascherj/pathreview/pull/926`

**Branch:**

`test/71-prompt-injection-red-team`

**What I Built:**

I implemented the red-team prompt injection testing framework requested in Issue #71. The contribution adds a dedicated security test suite, reusable JSON fixture files containing malicious and legitimate prompt examples, documented known prompt injection bypasses using `pytest.mark.xfail`, and a GitHub Actions workflow that automatically runs the security tests.

This work improves the project's security testing by making it easier to expand prompt injection coverage while helping prevent future regressions.

**Tests Added / Modified:**

Created:

- `tests/security/test_prompt_injection.py`

Added reusable fixtures:

- `tests/fixtures/injection_attempts/attacks.json`
- `tests/fixtures/injection_attempts/benign.json`
- `tests/fixtures/injection_attempts/known_bypasses.json`

Added CI workflow:

- `.github/workflows/security.yml`

The new tests verify:

- Known prompt injection attacks are detected correctly.
- Legitimate user prompts are not incorrectly classified as attacks.
- Previously identified prompt injection bypasses are documented using `pytest.mark.xfail`, allowing future improvements to be measured without breaking the test suite.
- Prompt injection test cases are loaded from reusable JSON fixtures rather than being hardcoded in the test file.

**Self-Review Confirmation:**

- [x] Equivalent of `make check` completed successfully by running:
  - `python -m ruff check tests/security/test_prompt_injection.py`
  - `python -m black --check tests/security/test_prompt_injection.py`

- [x] Equivalent of `make test-unit` completed successfully by running:
  - `python -m pytest tests/security/test_prompt_injection.py -v -m security`

**Draft PR Feedback Received From:**

None.