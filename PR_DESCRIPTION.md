Fix #148: Detect JavaScript and TypeScript in skill extractor

## Summary
`extract_skills()` detected no languages for plain-text JavaScript descriptions, and only detected React (never TypeScript) for TypeScript descriptions. Root cause: JS/TS detection in `_detect_languages()` was almost entirely dependent on a `filename` argument that's often not available, the one text-based check required whitespace after `import`/`require` (missing `require('fs')`), and export/arrow-function/async-await syntax were never checked at all. TypeScript had no content-based signal whatsoever.

Closes #148

## Changes
- Rewrote JavaScript evidence checks in `_detect_languages()` to check real syntax: `require(...)`, `import ... from ...`, `export` statements, arrow functions, `async`/`await`, plus literal "javascript"/`.js`/`.jsx` mentions
- Added an independent TypeScript evidence check: `interface` declarations, type annotations, literal "typescript" mention, `.ts`/`.tsx` mentioned in text
- JavaScript and TypeScript are now detected independently, not mutually exclusive
- Added 4 tests covering the issue's two examples, a plain-English false-positive guard, and a `.tsx` file test expecting both React and TypeScript

## Testing
 Unit tests pass — all 4 new tests for issue Skill extractor fails to detect JavaScript and TypeScript #148 pass
 Full test file — 3 pre-existing tests fail (test_database_technology_detection,
test_devops_tool_detection, test_docker_compose_detection); the latter two are
Docker/DevOps gaps outside this fix's JS/TS scope
 Integration tests — not run, unit-level fix
 Lint/typecheck — not run (make unavailable on Windows)
 New/updated tests cover the changes

## Notes for Reviewers
Branch name is left over from an earlier issue (#130) I initially worked on before switching to #148 — the diff reflects #148 only.