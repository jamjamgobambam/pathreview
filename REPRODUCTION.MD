# Reproduction — Issue #148

## Steps to reproduce

Ran the existing test suite for the affected file:

\`\`\`bash
pytest tests/unit/test_skill_extractor.py -v
\`\`\`

**Result:** 5 failed, 13 passed.

Failing tests matching the issue:
- `test_javascript_detection` — `extract_skills()` returns `[]` for JS text using `const`/`require('fs')` with no filename given.
- `test_text_with_typescript_files` — returns no TypeScript detection for text using `export interface`/`export class`.
- `test_devops_tool_detection` — returns no Docker detection for a Dockerfile snippet (`FROM`, `RUN`, `EXPOSE`) that never contains the literal word "docker".
- `test_docker_compose_detection` — same issue for docker-compose YAML syntax.

Also observed (out of scope for this fix): `test_database_technology_detection` fails with an `UnboundLocalError` due to a pre-existing typo in the test file itself (`skill_names` referenced before assignment) — unrelated to the skill_extractor.py bug, not part of this fix.

## Manual repro (from the issue)

\`\`\`python
from ingestion.parsers.skill_extractor import SkillExtractor
e = SkillExtractor()
print(e.extract_skills('Wrote index.js using const arrow functions and async/await callbacks'))
# observed: []
print([d.name for d in e.extract_skills('Built app.tsx and types.ts with strict TypeScript interfaces')])
# observed: ['React']