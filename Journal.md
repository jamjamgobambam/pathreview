## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/154#issuecomment-5039403002]

**Issue title:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that the database health check or probe within the ap/routes/health.py route is passing a raw SQL string plainly rather than explicitely marking the expression or string using sqlalchemy.text() so SQLAlchemy can correctly interact with the expression. Since SQLAlchemy doesn't expect a raw string, it raises an ArgumentError instead. As a result, the /health endpoint is incorrectly reported as unnavailable even though the connection is working properly or is reachable. A successful fix would wrap the string with the sqlalchemy.text() call within the api/routes/health.py file at the "SELECT 1" portion would allow the Get /health api endpoint call using curl to be successful and return the appropriate health records.

**Branch name:** [fix/154-DB-Probe-SQL-Input-Error]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection_Reasoning**
I've never contributed to an opensource project and many of the formalities are new to me so I wanted to choose a issue that was self-contained. It's also my first time navigating such a large codebase so I wanted to choose a tier 1 problem since they only affect a small number of files, therefore, it gives me the chance to slowly ease open source contribution. I found that the issue was well defined and I could accurately predict the affected files or where to start looking, I've also handled past debugging issue much like this on so I feel especially confident with this nature of issue. In addition to this, I don't have much time these following weeks so I wanted to choose a problem that was more adjusted with my expected work output.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/ascherj/pathreview/commit/af8dc3124ef7bf5db6ce9f784760c8f0adc86b3a)

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
Using the established testing client offered by fastapi and pytest, we are able to run the test file under tests/integration/test_get_health.py listed under test_health_endpoint. This test simply calls the get health endpoint and verifies whether it is successful or produces an error upon contacting or establishing a connection with it. This can also be replicated by running the app by using make run, and using gitbash to run the curl http://localhost:8000/health command which will return with the error description.

**PLAN.md link:** (https://github.com/ascherj/pathreview/commit/2c5e3233325e113df8a1969205af1595b0aff47f)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I imported and integrated the text() wrapper offered by SQLAlchemy during update 2.xx for raw SQL text within the health.py file within the route folder. After doing so, I 
had to run the text I implemented and I sadly learned that the assertion within the test_get_health.py file in the test/integration folder was failing, following the 
procedure I detailing slightly in the Plan.md, I investigated the cause of this error to determine the cause of it to evaluate whether the cause of it was from the solution I implemented.
Doing so, I learned that this was an error or situation caused by a separate bug that is highlighted in issue 43.

**Next steps:**
[What are you working on for the rest of the week?]
Ask for clarification from TA's or the slack tech help channel whether I should fix the error and confirm if the error is in fact already existing or present.

**Blockers:**
[Anything slowing you down? Or leave blank.]
I must wait for clarification from a TA or the tech help channel to know whether I should try to implement a fix that is blocking the get_health probe from passing or if I should narrow the 
scope of the test I implemented to specifically target the error caused by SQLAlchemy. This would be the most likely situation given that the cause of the error is already documented as a seperate
issue but I still wanted to be entirely sure that I can continue with my work.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/888

**Branch:** fix/154-DB-Probe-SQL-Input-Error

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
I simply updated or altered the api/routes/health.py file to import the text() wrapper from the SQLAlchemy library and integrate it within the db.execute to wrap the "Select 1" SQL command so it can be 
successfully executed. SQLAlchemy update 2.xx enforces that all raw SQL commands must be wrapped by their text() wrapper to ensure maintainability for the database.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
To ensure that this change corrected the error this fix is targeting, I also implemented a test within test/integration/test_get_health.py that asserts that the response from the get_health route does not return a status of 503 that is more commonly attributed to SQLAlchemy errors. I updated this test case after encountering issue #54 which made it impossible to receive a successful status of 200 without implementing a fix for it, I then needed to change the scope of this test from asserting that it returns 200 to only checking that it doesn't return a status of 503.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** ["none"]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in, but I will eagerly await any input and use all the skills taught in this course to professionally address their concerns.

**How you responded:**
There was no feedback to respond to, but when I do receive it I will respond in a professional way that utilizes every insight or skill taught throughout this course.
---


### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

Starting this project, I wasn't expecting the setup to be this technically involved, in the sense that I utilized most of the insights taught throughout this course. These topics range from Git/Git hub knowledge to coordinate documentation when addressing a fix, troubleshooting when docket containers weren't loading correctly, or utilizing a specific approach with AI to understand a codebase when encountering it for the first time.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

I learned the very important skill of opening my programming perspective to eventually hone on problem or fix entirely. Being able to understand a large codebase with the goal of understanding the different mechanisms interconnected with a specific issue is a wonderful skill that I wouldn't have developed without this simulated codebase. Prior to this experience, I would avoid public codebases or PR contributions because I was afraid of approaching larger codebases since they were too daunting. I also learned the importance of documentation when submitting PRs or when interacting with public codebases, documenting design decisions or testing methods is incredibly important since it aids in trying to understand a codebase to develop a bug fix for any collaborator in the future. Prior to this class, I wouldn't document anything since I figured that the programming spoke for itself. This would always hurt me in the future since I would always return to the project to add a fix or expand the project, but I would quickly give up because I struggled so much in trying to  understand my code after a long hiatus.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

I lack the broad programming knowledge to understand the vast variety of programming disciplines or libraries utilized in larger codebases like this one. With AI, I was able to quickly learn about a variety of functions or libraries without having to sift through pages and pages of documentation like I'm accustomed to. Particularly, I asked it why a TEXT wrapper was needed in SQLAlchemy if it had allowed raw SQL string in the previous version. Claude would inform me by collecting insights across reddit or stack overflow to explain the importance of wrapping the sql string with a TEXT wrapper. With this insight, I utilized the TEXT wrapper instead of downgrading the SQLAlchemy import which would break several other functions in the process. Along the same strain of using AI to inform me of a topic to assist me with decision making, it fell short when addressing the many import or setup challenges I came across. When I was first setting up the project, I asked AI for any insights or potential fixes when my Ubuntu distro wasn't mounting correctly with Docker or when Redis wasn't downloading correctly when running Make Setup. I asked AI for help, but it was largely lackluster so I had to research some fixes and experiment many times. This is expected, because there aren't that many documented instances of this issue occurring so there's nothing AI can base their judgment or help on.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
Regarding my issue selection, I wouldn't change anything about it because I believe I chose the right issue when considering the limited amount of time I had to implement a fix. In another circumstance, I would've definitely tried a issue with a higher difficulty if I had a bit more time. If I could start over, I would definitely change how I planned my implementation by committing some more time into trying to understand the larger codebase. Particularly, since after implementing my fix I wrote a test case that was too broad for the issue I was tackling. I later on had to adjust the scope of the test case, but I could've avoided it if I had accustomed myself a tiny bit more with the larger codebase environment. As a result, this would've altered my process because I wouldn't've had to narrow my test case later on in the timeline.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I'm most proud of my commitment to documenting my interaction with the codebase since I used to view this as a waste of time. It took a lot to overcome my previous biases of ignoring documentation when it didn't have a direct payoff I could see. Another aspect I'm proud of myself for is my tenacity in utilizing GitHub or git to interact with this project, it's a very daunting or scary tool to use since it can have such a big impact on the larger programming project but I feel like I overcame it because of  this opportunity.
