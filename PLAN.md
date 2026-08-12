## Solution plan

**Issue:** Skill extractor fails to detect JavaScript and TypeScript — https://github.com/ascherj/pathreview/issues/148

### Understand
Confirmed root causes (three distinct issues under one title): (1) JavaScript detection relied almost entirely on filename extension plus a broken regex requiring whitespace after `require`/`import`, so `require('fs')` never matched and the `JS_TS_KEYWORDS` set was defined but never actually used. (2) TypeScript had no dedicated detection at all — `.tsx`/`.ts` files only matched the existing React pattern. (3) Docker/DevOps detection only matched the literal word "docker" in text, but real Dockerfile and docker-compose syntax never contains that word — confirmed this was in scope since the original issue explicitly listed `test_devops_tool_detection` and `test_docker_compose_detection` as related failing tests, not a separate problem.

### Map
Only one file needed changes: `ingestion/parsers/skill_extractor.py`. No test file changes were needed — the existing tests in `tests/unit/test_skill_extractor.py` already specified the correct expected behavior.

### Plan (as executed)
1. Read the pattern-matching logic and confirmed root cause via reproduction + failing test output
2. Rewrote JS detection to check for `require()` calls, ES6 `import...from`, `export` statements, `const`/`let`/`var`, and `console.log`
3. Added separate TypeScript detection (interfaces, type annotations, `Promise<T>`), so TypeScript no longer gets folded into JavaScript or React
4. Added a new `_detect_docker` method for structural Dockerfile/docker-compose detection, wired into `extract_skills`
5. Fixed a `mypy` type-annotation issue on `detected_skills` caught by the pre-commit hook

### Inputs & outputs
Input: free text (code snippets, commit messages, config file contents) plus an optional filename. Output: a list of `SkillDetection` objects — now correctly including JavaScript, TypeScript, and Docker where applicable, with no regressions to existing Python/React/framework/database detection.

### Risks & unknowns
Resolved: JS/TS pattern overlap handled by checking TypeScript-specific evidence first and only falling back to JavaScript if no TS signals are present. Resolved: `.tsx` files can still trigger both React and TypeScript, since they're stored as separate dict keys. Remaining, not in scope: `test_database_technology_detection` still fails due to a pre-existing, unrelated bug in the test file itself (references a variable before it's assigned) — documented in the PR, not fixed here.

### Edge cases
Mixed JS+TS text is handled (both evidence sets are collected; TypeScript takes priority when TS-specific signals exist). Docker detection is case-sensitive on purpose (`FROM`/`RUN`/`EXPOSE` uppercase) to avoid colliding with Python's lowercase `from`/`import`. Not yet handled: compound extensions like `.d.ts` or `.test.ts` aren't specially distinguished beyond a basic `.ts` substring check — potential follow-up.
