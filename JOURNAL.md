# Week 7: Issue Selection

## Selected Issue

**Title:** README scorer test fixture is too short for its own word-count assertion

**Issue:** https://github.com/ascherj/pathreview/issues/156

## Issue Tier

This issue is labeled **Tier 1**. I selected a Tier 1 issue because I am still learning the pathreview codebase and wanted an issue with a clear and manageable scope. It matches my current experience with Python and unit testing while allowing me to become familiar with the project structure.

## Why I Selected This Issue

I chose this issue because it focuses on a single unit test instead of requiring changes throughout the application. The issue is well-defined, making it easier to understand the expected behavior before implementing a fix. Working on this issue will also help me improve my skills in reading existing tests and understanding how they verify application behavior.

## Problem Summary

The issue is about a unit test that uses a sample README which is too short for the expectations in the test. The test is supposed to represent a high-quality README, but the sample content does not contain enough words to satisfy the word-count requirement.

Because of this mismatch, the test can fail even when the README scoring logic is working correctly.

A successful fix would make the sample README and the test expectations agree with each other so that the test accurately verifies the README scorer without producing incorrect failures.


## Is This Right for Me?

- [x] The issue is labeled Tier 1.
- [x] The scope is small and focused on a single unit test.
- [x] I understand what is currently broken after reading the issue and locating the test.
- [x] The issue matches my current Python and testing experience.
- [x] I can complete the work without needing to understand the entire codebase.

I chose this issue because it is small, well defined, and appropriate for my current skill level. It gives me the opportunity to practice reading unit tests and understanding existing code before working on larger or more complex issues.