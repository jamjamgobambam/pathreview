# Week 7 – Issue Selection

**Issue link:**
https://github.com/ascherj/pathreview/issues/18

**Issue title:**
Add end-to-end ingestion test with a sample resume fixture

**Tier:**
Tier 2

**Selection reasoning:**
I selected this Tier 2 issue because I have previous experience contributing to larger codebases through CodePath projects, and I want to continue improving my testing and debugging skills. The issue has a clear description, identifies the relevant files, and has a well-defined scope, making it a realistic project to complete within the module timeline.

**Problem summary:**
This issue requests an end-to-end integration test for the resume ingestion pipeline. While the project already includes unit tests for individual parsers, there is no test that verifies the complete workflow from uploading a resume through processing and storing the resulting data. A successful solution will add an integration test using a sample resume fixture so the entire ingestion pipeline can be validated automatically.

## "Is this right for me?" checklist reasoning

I understand the goal of this issue and can explain what needs to be implemented in my own words. The issue description identifies the relevant file (`tests/integration/test_ingestion_pipeline.py`), which provides a clear starting point for exploring the codebase. Since I have prior experience contributing to large repositories, I am comfortable working on a Tier 2 issue. The issue has a defined scope, no listed blockers, and I believe it is realistic to complete before the Week 9 deadline.

**Branch name:**
docs/18-week7-journal

**Setup confirmation:**
- [x] App runs locally at localhost:5173

**Cohort ledger:**
- [x] Issue added to cohort ledger

---

# Week 8

## Reproducing Issue #18

I set up the project locally and verified the current resume ingestion functionality. I explored the existing resume parser, ingestion pipeline, chunking strategy, and embedding workflow to understand how the application processes resumes.

I also confirmed that the repository contains unit tests for the resume parser but does not include an end-to-end integration test for the complete ingestion pipeline. This matches the goal of Issue #18.

### PLAN.md

I created a `PLAN.md` document outlining my approach to solving the issue. The plan includes:

- Files to investigate and modify
- Implementation steps
- Potential risks
- Edge cases
- Testing strategy

PLAN.md:
https://github.com/baabass1/pathreview/blob/docs/18-week7-journal/PLAN.md

---

# Week 9

## Implementation

This week I implemented the solution for Issue #18 by adding an end-to-end integration test for the resume ingestion pipeline.

### Changes made

- Created a sample resume fixture:
  - `tests/fixtures/sample_resumes/sample_resume.md`
- Created an integration test:
  - `tests/integration/test_ingestion_pipeline.py`
- Verified the complete resume ingestion workflow from parsing through embedding generation and vector database storage using mocked dependencies.

### Testing

I tested the implementation by running:

```bash
.venv/bin/pytest tests/integration/test_ingestion_pipeline.py -v
```

The integration test completed successfully.

**Result:**

- 1 test collected
- 1 test passed

### Challenges

The biggest challenge was understanding how the ingestion pipeline connected multiple components, including the resume parser, chunking strategy, embedding provider, and vector database. I explored each part of the pipeline before implementing the integration test.

During the commit process, the repository's pre-commit hooks reported existing `mypy` errors in project files that were unrelated to my implementation. After verifying that my integration test passed successfully and confirming that the remaining errors came from existing project files, I committed and pushed my implementation to my branch.

### What I learned

This assignment helped me better understand the difference between unit tests and integration tests. Unit tests verify individual components, while integration tests verify that multiple components work together correctly throughout an entire workflow. I also gained more experience using mocks to isolate external dependencies while testing the overall behavior of the application.

---

## Week 9 – Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I completed the implementation of the end-to-end resume ingestion integration test. I added a sample resume fixture in `tests/fixtures/sample_resumes/sample_resume.md` and created `tests/integration/test_ingestion_pipeline.py` to verify the complete ingestion workflow. I also confirmed that the integration test passes successfully.

**Next steps:**

Open a pull request, complete the PR template, update this journal with the PR link, and submit the branch URL through the course portal.

**Blockers:**

None.

---

### Check-in 2 (end of week)

**PR link:**

https://github.com/ascherj/pathreview/pull/963

**Branch:**

docs/18-week7-journal

**What you built:**

I added an end-to-end integration test for the resume ingestion pipeline using a sample resume fixture. The test verifies the complete workflow from resume parsing through chunking, embedding generation, vector database storage, and ingestion recording using mocked external dependencies.

**Tests added or updated:**

Added `tests/integration/test_ingestion_pipeline.py` to verify the complete resume ingestion pipeline using the sample fixture located in `tests/fixtures/sample_resumes/sample_resume.md`. The test confirms that resume parsing, chunking, embedding generation, vector database storage, and ingestion recording all execute successfully.

**Self-review confirmation:**

- [x] make check passes (no new failures introduced)
- [x] make test-unit passes

**Draft PR feedback received from:**

None.

---

# Week 10 – Iteration & Reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No – still awaiting review

**Summary of feedback:**

At the time I completed this journal entry, my pull request had not received any reviewer feedback. The pull request remains open, so there were no review comments or requested changes to document.

**How you responded:**

N/A

---

### Reflection

**What was harder than you expected?**

The hardest part was understanding how the resume ingestion pipeline connected multiple components instead of writing the test itself. I spent time tracing how the resume parser, chunking strategy, embedding generation, and vector database interacted before I felt confident adding the integration test. I also had to determine which external dependencies should be mocked so the test focused on verifying the pipeline rather than external services.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing production codebase requires much more reading than writing code. Before making changes, I explored the existing parser, ingestion pipeline, and test structure to follow the project's conventions. I also learned that understanding the repository's organization and existing patterns makes implementing new features much easier and helps produce code that fits naturally with the rest of the project.

**How did AI tools help — and where did they fall short?**

AI was most helpful for explaining unfamiliar parts of the codebase, identifying where related functionality was implemented, and helping me understand the overall ingestion workflow. However, AI could not determine whether its suggestions matched the repository's actual architecture or testing patterns. I still needed to read the existing code, verify file locations, understand the project's design, and make implementation decisions based on the repository itself.

**What would you do differently if you started over?**

If I started over, I would spend more time exploring the repository before writing any code. Understanding the relationships between the parser, ingestion pipeline, embeddings, and vector database earlier would have made planning the integration test more straightforward. I would also review the existing test suite in greater detail before beginning implementation.

**What are you most proud of from this module?**

I am most proud that I completed an end-to-end contribution that followed a professional open source workflow from issue selection through planning, implementation, testing, pull request creation, and documentation. This project gave me practical experience working in someone else's codebase rather than only building projects from scratch. It also improved my confidence in reading unfamiliar code and contributing changes that follow an existing project's structure.
