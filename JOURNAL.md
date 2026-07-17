# Week 7: Issue Selection

## Selected Issue

**Issue:** https://github.com/ascherj/pathreview/issues/156

## Issue Tier

This issue is labeled **Tier 1**. I selected a Tier 1 issue because I am still learning the pathreview codebase and wanted an issue with a clear and manageable scope. It matches my current experience with Python and unit testing while allowing me to become familiar with the project structure.

## Why I Selected This Issue

I chose this issue because it focuses on a single unit test instead of requiring changes throughout the application. The issue is well-defined, making it easier to understand the expected behavior before implementing a fix. Working on this issue will also help me improve my skills in reading existing tests and understanding how they verify application behavior.

## Problem Summary

The issue is about a unit test that uses a sample README which is too short for the expectations in the test. The test is supposed to represent a high-quality README, but the sample content does not contain enough words to satisfy the word-count requirement.

Because of this mismatch, the test can fail even when the README scoring logic is working correctly.

A successful fix would make the sample README and the test expectations agree with each other so that the test accurately verifies the README scorer without producing incorrect failures.