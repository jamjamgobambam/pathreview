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