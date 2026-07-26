## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The skill extraction logic in the ingestion pipeline does not reliably recognize JavaScript and TypeScript skills from resume or project text. In particular, ingestion/parsers/skill_extractor.py misses common indicators such as JavaScript and TypeScript filenames, require() calls, TypeScript interfaces, typed parameters, and other language-specific syntax. As a result, relevant skills may be omitted even when the submitted text clearly demonstrates experience with those languages. A successful fix would expand the detection logic so these common patterns are recognized while avoiding incorrect language classifications.

**Is This Issue Right for Me?**

***Can I explain what this issue is asking for in my own words?***
The the skill detection logic (code) in the ingestion pipeline does not properly detect 
TypeScript or JavaScript. The skill detection code needs to recognize TypeScript and JavaScript. TypeScript samples have to also not be detected only as 'React', but as TypeScript (especially for just pure TypeScript samples).

***Do I understand which part of the app is affected?***
This affects the ingestion part of the app

***Do I understand what "done" looks like?***
As stated above, the skill detection logic should detect JavaScript text as JavaScript. TypeScript text should also be detected as TypeScript and not only as React, especially if it is a pure TypeScript sample.

**Branch name:** fix/148-skill-extractor-js-ts-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
Ran the 4 failing tests with `python3 -m pytest tests/unit/test_skill_extractor.py -vv -s` and confirmed `extract_skills()` misses the JS/TS/Docker family: JavaScript text (`const`, `require('fs')`) returns `[]`; TypeScript returns no TypeScript — the issue's `.tsx`/`.ts` example returns only `['React']`, while the `test_text_with_typescript_files` interface sample returns `['Python']` (a false match on `: string`); a Dockerfile snippet returns only `['Python']` (matched on "requirements.txt"); and Docker Compose YAML returns `[]`.

The failing tests are the following:
test_javascript_detection
test_text_with_typescript_files
test_devops_tool_detection
test_docker_compose_detection

***Observed test output***
To capture the actual detections, I temporarily added print() statements to the four failing tests (not committed) and ran python3 -m pytest tests/unit/test_skill_extractor.py -vv -s.

```
test_text_with_typescript_files
  Input:  export interface User { id: string; name: string; }
          export class UserService { async getUser(id: string): Promise<User> {} }
  Got skills:   ['Python']
  Full details: [('Python', 0.7, ['Python type annotations'])]
  -> FAILED (expected TypeScript)

test_devops_tool_detection
  Input:  FROM python:3.9
          RUN pip install requirements.txt
          EXPOSE 8000
  Got skills:   ['Python']
  Full details: [('Python', 0.7, ['requirements.txt found'])]
  -> FAILED (expected Docker)

test_javascript_detection
  Input:  const fs = require('fs');
          const data = fs.readFileSync('file.txt');
          console.log(data);
  Got skills:   []
  Full details: []
  -> FAILED (expected JavaScript)

test_docker_compose_detection
  Input:  version: '3.8'
          services:
            web:
              build: .
              ports: ["8000:8000"]
  Got skills:   []
  Full details: []
  -> FAILED (expected Docker)
```

Summary: 4 failed, 14 passed (18 collected).

Results:
test_javascript_detection      -> Got skills: []
test_text_with_typescript_files -> Got skills: ['Python']
test_devops_tool_detection     -> Got skills: ['Python']
test_docker_compose_detection  -> Got skills: []


***Root causes***
the JS/TS `import|require` regex requires trailing whitespace so `require('fs')` never matches, the defined `JS_TS_KEYWORDS` are never checked, file extensions are only read from the `filename` arg (not the text), and `_detect_tools()` only matches the literal word "docker" — which never appears in Dockerfile or Compose syntax.

**PLAN.md link:** 
https://github.com/karencalpo/pathreview/blob/fix/148-skill-extractor-js-ts-detection/PLAN.md

**Walkthrough video (recommended):** Not included.

**Blockers or open questions:**
Issue #148 spans 4 failing tests (JavaScript, TypeScript, DevOps/Docker, Docker Compose). Open questions across all four:
- **JS vs. TS disambiguation:** when text has both `.ts`/`.tsx` files and JS syntax, should it report both JavaScript and TypeScript, or just TypeScript? Need to avoid the current behavior where TS samples collapse to only "React".
- **Keyword false positives:** relying on generic JS keywords (`const`, `let`, `function`) risks matching non-code prose — need to tune confidence so a single keyword doesn't over-trigger.
- **Docker Compose classification:** report as a separate "Docker Compose" skill or fold into "Docker"? Currently planning to fold into "Docker".
- **Dockerfile keyword safety:** matching `FROM`/`RUN`/`EXPOSE` could false-positive on unrelated prose — considering requiring 2+ keywords or line-start anchoring to keep confidence honest.