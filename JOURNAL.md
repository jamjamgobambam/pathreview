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

**Reproduction commit link:** https://github.com/karencalpo/pathreview/commit/b981e36ff13dd04e4a8d48ad036d72cb5f07c78e

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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented separate JavaScript and TypeScript detection paths in
`SkillExtractor`. JavaScript detection now recognizes CommonJS/ES module syntax,
while TypeScript detection recognizes interfaces, type aliases, enums, generic
`Promise` types, and TypeScript type annotations. Added Docker detection based on
multiple line-anchored Dockerfile instructions and Docker Compose structure. The
four tests named in issue #148 now pass.

**Next steps:**
Remove temporary debugging output, review the diff for unrelated changes, run the
affected test file and project quality checks, and submit a draft PR for feedback.

**Blockers:**
The full unit suite still contains failures outside issue #148. I also fixed
`test_database_technology_detection` while investigating; reviewer input is
needed on whether that unrelated database fix should be removed from this PR and
submitted separately.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/410

**Branch:** `fix/148-skill-extractor-js-ts-detection`

**What you built:**
Improved JavaScript and TypeScript skill detection by recognizing CommonJS
calls, filenames mentioned in text, explicit TypeScript references, and common
TypeScript syntax. Added Docker detection based on multiple line-anchored
Dockerfile instructions and Docker Compose structure, with safeguards against
false positives.

**Tests added or updated:**
Updated `tests/unit/test_skill_extractor.py` with positive and negative
regression coverage for JavaScript, TypeScript, Dockerfile, and Docker Compose
detection. All 15 targeted tests pass; the complete test file retains one
unrelated failure for `psycopg2` PostgreSQL detection.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

*Note: The repository-wide commands retain unrelated existing failures. Ruff and mypy
pass for the changed implementation and test files, and all 15 targeted tests
pass.*

**Draft PR feedback received from:** Tanaka Mbavarira

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
My reviewer commented on my tests. They looked good and very comprehensive to him. He did mention that I had a 
piece of information that was not accurate in my `PLAN.md`. It said I did not include a fix that I had apparently 
included for a test (for `test_database_technology_detection`). I mentioned I did not include it in `test_skill_extractor.py` to keep scope tight, but I apparently still had it according to the file diff. My reviewer said my PR looked good otherwise.

**How you responded:**
I responded that he was correct to note that my `PLAN.md` was not accurate and needed to be updated. The fix I did 
not include fixes the `UnboundLocalError` that I was getting when running `test_database_technology_detection`. The test, however, still fails because `psycopg2` is not recognized as PostgreSQL. This is an issue unrelated to the one I worked on, but fails beacause `psycopg2` needs to be associated with PostgresSQL. I also told the reviewer I would update PLAN.md so that the information is accurate.

---

### Reflection

**What was harder than you expected?**
The hardest part was not adding the detection. It was making sure the detection
did not match the wrong thing.

I expected this issue to just need more patterns, like adding `require()` and
`interface` to the regexes. But when I ran the tests, TypeScript was being
detected as Python. The Python type annotation regex
`:\s*(int|str|float|bool|list|dict)` was matching the `str` inside TypeScript's
`: string`. It was a missing `\b`, and it was giving a confident but wrong
answer.

Docker had the same problem. `FROM`, `RUN`, and `COPY` are normal English words,
so matching them on their own would tag regular text as Docker. I ended up
requiring two different Dockerfile instructions plus one from a stronger set like
`COPY`, `EXPOSE`, or `WORKDIR`. The tests did not ask for this. The test only
checks that Docker is detected, not that it is not over-detected. I had to decide
where to draw that line myself, because the result includes a confidence score.

The other thing that surprised me was how much work went into keeping the scope
tight. The issue title sounded like one bug, but it was four failing tests with
four different causes. While reproducing, I also fixed an `UnboundLocalError` in
an unrelated database test, and that fix exposed a different problem where
`psycopg2` is not recognized as PostgreSQL. I had to leave that one broken on
purpose. My reviewer also caught that my `PLAN.md` said I had left the database
fix out when the diff still had it. Keeping the notes accurate took more
attention than I expected.

**What did you learn about working in a large codebase?**
The biggest difference is that I did not get to decide what "correct" meant. The
four tests I had to fix were already in `tests/unit/test_skill_extractor.py`
before I started. Someone else wrote them, and they defined what the function was
supposed to do. In my own projects I usually write the test after I decide how
something should work. Here it was the other way around, and I had to read the
tests carefully to figure out what was actually being asked for.

I also had to check who was using the code before I changed it. Changing how
`extract_skills()` behaves could have broken something else in the repo. I looked
and found the parser has no production callers, and only the test file imports
it, so I knew the change was safe. In my own project I would already know that.
Here I had to go and confirm it.

The project also decided the style, not me. `make check` runs ruff, black, and
mypy. Ruff has the `UP` rules turned on, so `Optional[str]` had to become
`str | None`, and mypy has `disallow_untyped_defs`, so I had to annotate
`detected_skills` as `dict[str, SkillDetection]`. Neither of those had anything
to do with issue #148. They were just the rules of the repo.

The last thing I learned is that a failing test suite is not always my fault.
When I first ran the tests there were failures I did not cause, like `psycopg2`
not being recognized as PostgreSQL. I had to work out which failures were mine
and which were already there, and then leave the ones that were not mine alone.

**How did AI tools help — and where did they fall short?**
The AI was good at explaining programming concepts I did not understand. It was
also good at explaining how portions of code work, especially the tests in
`test_skill_extractor.py` for the issue I worked on. Regex was the biggest
example. It helped me see why `\b(import|require)\s+` never matched
`require('fs')`, because that pattern needs whitespace after the keyword and
`require('fs')` has a parenthesis instead.

Where AI fell short, I felt, was in isolating what bugs belonged to the issue I
worked on and which ones did not. I ended up fixing issues that were not related
to the one I worked on. I added a `DATABASE_ALIASES` entry so `psycopg2` would be
detected as PostgreSQL, and then had to take it back out in a later commit
because it had nothing to do with issue #148. The AI could tell me a bug was
real, but it could not tell me whether the bug was mine to fix. That was a
judgment call about scope, and I had to make it myself and then explain it to my
reviewer.

**What would you do differently if you started over?**
If I were to start over, the main thing I would change is how I picked my issue.
I would read through every issue in the original repository before deciding on
one. I chose #148 because it dealt with technologies closest to what I use at
work every day. I figured that would make it easy enough for me to work on, and
it was also a Tier 1.

What I did not do was look at the failing tests before I committed to it. The
title only says JavaScript and TypeScript, but the issue was really four failing
tests, and two of them were about Docker and Docker Compose. That is not
something I would have guessed from the title. If I had opened
`test_skill_extractor.py` first, I would have seen the real size of the issue
before choosing it.

So if I did everything again, I would have looked at more issues instead of just
the first 10, and I would have judged them by what the tests actually asked for,
not just by whether the technology was familiar to me.

**What are you most proud of from this module?**
I am proud that I got to work on a fork of an open source project, even if it was
a simulated one. I got to learn the procedure for how to participate in making
changes and creating PRs that would potentially be merged into an open source
project.

The part I did not expect to value was having to reproduce the bug and write a
plan before writing any code. I made a commit that only documented the four
failing tests and what they actually returned, and I wrote `PLAN.md` before I
changed `skill_extractor.py`. That felt slow at the time, but it meant that when
my reviewer looked at the PR, I could explain why each change was there.

This is different from the PR process I experienced at work. Here I was writing
for someone who had never seen my code and did not know the issue, so the
reproduction and the plan had to do the explaining for me.