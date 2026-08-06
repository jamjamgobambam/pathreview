# PathReview Development Journal

**Name:** Christian A Gomez Diaz
**GitHub Username:** Christian101GTZ

---

# Week 7 — Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

### Problem Summary

The skill extractor currently does not recognize JavaScript and TypeScript when they appear in a resume or profile document. As a result, these programming languages are missing from the extracted skills even though they are valid technologies. This affects the ingestion pipeline because the application may produce incomplete skill data. A successful fix will update the skill extraction logic and related tests so JavaScript and TypeScript are detected correctly. This ensures resumes containing these technologies are analyzed more accurately.

### Issue Selection Notes

I selected this issue because it is focused on a single part of the ingestion pipeline and has a clear expected outcome. The problem is well defined: JavaScript and TypeScript should be recognized as valid skills during extraction. It is an appropriate first contribution because the scope is manageable while still requiring me to understand and modify production code and its related tests. Based on the issue checklist, I believe I can complete it without needing to understand the entire codebase.

**Branch name:** `fix/148-skill-extractor-javascript-typescript`

**Setup confirmation:** [x] App runs locally at `localhost:5173`

**Cohort ledger:** [x] Issue added to cohort ledger 

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Christian101GTZ/pathreview/commit/81ff1ad

**Reproduction summary:**

I reproduced Issue #148 by running the existing TypeScript unit test:

`pytest tests/unit/test_skill_extractor.py::TestSkillExtractor::test_text_with_typescript_files -v`

The test failed because the extractor did not return TypeScript for text containing TypeScript-specific syntax. I also compared extraction with and without a `.ts` filename. Without a filename, the extractor incorrectly returned Python. With `example.ts`, it returned both Python and TypeScript.

**PLAN.md link:** https://github.com/Christian101GTZ/pathreview/blob/fix/148-skill-extractor-javascript-typescript/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**

The Python type-annotation pattern matches `str` inside the TypeScript type `string`, creating a false Python result. I still need to determine the safest detection patterns for distinguishing JavaScript, TypeScript, and Python without introducing false positives. 

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Reviewed the existing SkillExtractor implementation and its unit tests. I identified that JavaScript and TypeScript detection relied mainly on filenames and import statements, so code snippets without filenames were not detected correctly. I began implementing syntax-based detection for both languages.

**Next steps:**
Finish the implementation, run the relevant tests and project checks, commit the changes, open a pull request, and request feedback.

**Blockers:**
The repository contains several pre-existing unit-test failures unrelated to Issue #148. I documented the baseline failures so I could verify that my changes did not introduce additional failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/546

**Branch:** `fix/148-skill-extractor-javascript-typescript`

**What you built:**
Improved the SkillExtractor so it can identify JavaScript and TypeScript from code syntax instead of relying only on file extensions. The updated logic recognizes JavaScript patterns such as `require()`, `console.log()`, and variable declarations, along with TypeScript patterns such as interfaces, type annotations, type aliases, `implements`, and generic `Promise` types.

**Tests added or updated:**
I used the existing tests in `tests/unit/test_skill_extractor.py`. The JavaScript and TypeScript detection tests now pass. The full skill-extractor test file produced 15 passing tests and 3 unrelated pre-existing failures involving database and Docker detection.

**Self-review confirmation:** [x] make check introduces no new failures  [x] make test-unit introduces no new failures

**Draft PR feedback received from:** none

---
## Week 10 — Iteration & Reflection

### Reviewer Feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer or maintainer feedback had been posted on PR #546 when I completed this journal entry. The pull request is still open and has not been reviewed or merged.

**How you responded:**

No response was needed because I did not receive any feedback. However, I reviewed my pull request again and found a bug I had missed.

In Week 8, I noticed that the Python type pattern matched `str` inside the TypeScript type `string`, but I never fixed it. When I tested this code:

```typescript
export interface User { id: string; }
```

the extractor still returned both TypeScript and Python.

I pushed a follow-up commit (`0dab550`) that added a word boundary to the Python pattern. The TypeScript example now returns only TypeScript, while Python code such as `url: str` is still detected correctly.

The test results stayed at 15 passing and 3 failing, so my fix did not create any new failures.

---

### Reflection

**What was harder than you expected?**

Finding the correct file took longer than writing the actual fix. There was a `skill_extractor.py` file inside `ingestion/parsers/`, another one inside `agent/tools/`, and also a `tech_detector.py` file. The issue did not explain which file controlled the behavior.

I had to read `tests/unit/test_skill_extractor.py` and look at its imports. That showed me that the tests used the extractor inside `ingestion/parsers/`, so I knew that was the correct file to change.

Another difficult part was writing detection patterns without causing false positives. It would have been easy to detect TypeScript by only looking for the word `interface`, but regular documents can also contain that word.

The Python false positive was a good example. The existing regular expression looked correct, but it matched `str` inside the word `string`. I only found the problem because I ran the extractor myself and checked the actual output instead of assuming the tests covered everything.

**What did you learn about working in a large codebase?**

I learned that existing tests can be some of the best documentation in a repository. They showed me which module was being used, what output was expected, and which existing behaviors I needed to avoid breaking.

I also learned that working in a shared codebase involves more than making the code function. The repository used Ruff, Black, and MyPy during the pre-commit process. The formatting tools changed enough lines that my commit showed 111 insertions and 38 deletions, even though the actual logic change was much smaller.

When I tried adding tests, MyPy reported 21 errors. Only two were related to my work. The repository requires typed functions in `pyproject.toml`, but its normal `make check` command does not run MyPy on the tests folder. Pre-commit does check any staged test files, which exposed older errors that were already there.

I decided not to fix all of those unrelated errors because they were outside the scope of Issue #148. I learned that knowing what not to change is also important.

I also noticed that one of the three failing tests appears to contain its own bug. `test_database_technology_detection` uses `skill_names` before it has been created. This helped confirm that the three failing tests were not caused by my changes.

**How did AI tools help — and where did they fall short?**

AI helped me understand code and regular expressions more quickly. It explained what patterns such as `\b`, `\s*`, and alternation groups were doing. This helped me understand why `: string` was incorrectly matching the Python type `str`.

It also helped me search through the repository without including unnecessary folders such as `.git`, `node_modules`, and `.venv`. It was also useful for explaining Git commands before I ran them.

However, AI could not make every decision for me. It could not know which `skill_extractor.py` file was the correct one until I checked the test imports myself.

It also suggested some changes that may have been technically correct but were not appropriate for this pull request, such as fixing unrelated tests or adding type annotations to many existing functions. I had to keep the work focused on Issue #148.

AI could suggest possible detection patterns, but it could not guarantee that they would avoid false positives. I still had to run the extractor, examine the results, and decide whether the behavior was correct.

**What would you do differently if you started over?**

I would read the test file earlier. Many of the things that confused me during Weeks 7 and 8 were explained inside `tests/unit/test_skill_extractor.py`.

I would also follow up on every blocker I write down. My Week 8 journal mentioned the Python false positive, but I still opened the pull request without fixing it. I only noticed it again because I reviewed my journal at the end of the module. I should have treated the blockers in my journal like a checklist.

I would also run the formatting tools before making larger changes. That would help separate automatic formatting changes from the actual code I wrote.

Finally, I would try to keep `JOURNAL.md` and `PLAN.md` out of the pull request branch. PR #546 currently includes those course files along with the real code changes, which makes the pull request look larger than the actual fix.

**What are you most proud of from this module?**

I am most proud that I found and fixed a bug in my own pull request after it was already open.

It would have been easy to consider the project finished once I submitted the pull request, especially because my grade did not depend on it being reviewed or merged. However, the extractor was still incorrectly labeling TypeScript as Python, and I had already written about that problem in my journal.

I went back, found the cause, updated the regular expression, tested both TypeScript and Python examples, and pushed a follow-up commit. That felt more like a real open-source contribution than simply opening the pull request.
