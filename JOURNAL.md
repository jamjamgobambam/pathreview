## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159#issue-4884927126

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

I chose a Tier 1 because this is my first time contributing to open source, so I wanted to practice going through the motions of the entire process without too many bumps on the road. I will like to try a second issue pending time.

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that the test isn't passing for tests that test for presence of logs in caplog like in test_empty_chunks_list_return_empty in test_batch_processor.py.
We know that it's that issue because because in this example, the second assert is failing, which isolates the issue to lack of logs present in caplog.
So, even though the process functions correctly returns an empty list when there are no chunks,
and the empty list event is caputured (log seen in stderr), caplog isn't receiving the log.

The file I will look at will be tests/conftest.py because that's where test setup is configured,
and since both structlog and the business logic are working, it wouldn't make sense to check the running code.

A successful fix would mean that the caplog related tests pass.

**Branch name:** fix/159/structlog-output-not-captured

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/4cd813b86a3479a449fa372a5e759cbd07d2f8ac

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I first did a control -F project wide to see if the caplog issue existed anywhere else, but confirmed it was just in test_empty_chunks_list_returns_empty in tests/test_batch_processor.

1. Ran the test
2. Confirmed the test failed for the assert checking caplog for the log

**PLAN.md link:** https://github.com/ninaony/pathreview/blob/fix/159/structlog-output-not-captured/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have not completed anything so far, so nothing has been finished yet.

**Next steps:**
I sitll have to finish the rst of my PLAN.md

- Understanding how logger works
- Looking at what the codebase has already built in terms of the logger
- Implementing the fix
- Completing the PR

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** [Pull request link](https://github.com/ascherj/pathreview/pull/943)

**Branch:** `fix-159-structlog-output-not-captured`

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
I added a call to `core/logging/py/configure_logging` in `tests/conftest.py`just like it's done in `scripts/seed_dv.py` so that the structlog configuration that hands the log to a stdlib handler would work. Essentially, without that configuration, structlog handles logs itself and default to writing to stderr. Caplog, which is what the test used watches stdlib, so I basically just switched on the stdlib configuration of structlog, which happened to already exist in the codebase.

**Tests added or updated:**
`test_batch_processor` previously failed and now was fixed

Added `test_logging_config` to test if the fix would apply suite-wide and not just for `test_batch_processor` module. I added two tests, one to test it the same way the codebase + test did and one using the actual function call that the codebase defined.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

Make check:
Previously had 180 errors, then I re-ran it after my fix and saw that that there was 181 error. This had to do with my comment that I included to mark where the bug was. When I removed it, there was still a traling space so I had to remove that. Now it's back to 180.

Make test-unit:
Previously had 53 failed, 375 passed, 1 warning, but then it became 52 failed, 376 passed, 2 warnings. The one more test passing and one less test failing is indicative of my fix. The additinal warning I was confused about, but I checked with Claude, and it said that it had nothing to do with my fix. One of the warnings was related to async which may not have fired at the time I had initially ran that command.

This became 52 failed, 378 passed, and 2 warnings after I added my two tests.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No review

**How you responded:**

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
I was originally going to try a tier 2 because I wanted to push myself, but ended up trying a tier 1 since this was my first time contributing to open source. I thought it was going to be a smooth, easy ride but it really wasn't. Like even though my fix literally ended up being only one line of code, I had to learn so much about loggers, so I could understand what the actual issue was. I wanted to learn where exactly in the pipeline the issue occured, and that required doing a deep dive on how various libraries worked and what configurations existed, etc.

In addition, I'm stil getting used to git commands, especially doing it all in the comomand line which feels really tedious. A lot of the organization related tasks like the commit naming conventions and the PLAN.md/JOURNAL.md files also require a lot of thinking. So I guess I underestimated how much pre-work is required before you actually code. While I did want to just code more, I'm glad I had to learn to pause and understand.

**What did you learn about working in a large codebase?**
If I wasn't prompted to really scan the codebase and understand what exists, I think my insticts owuld have led me to build something from scratch like one does when working on their own project. For my case, the fix really became simple once I understood the codebase well.

I'm also learning more about industry standard when it comes to organizing files in larger codebases. Like to me `main.py` seems like it would be in `/core`, but it was in `/api`. I defnitely want to get better at organizing in this way especially if I plan on creating open source repos.

**How did AI tools help — and where did they fall short?**
Claude helped me reall trace through all the relevant modules I had to go through. It was so helpful in helping me navigate the codebase and really understand every method call or library that was used. It also helped me go into depth with my logging understanding. Lastly, it helped a lot with the git commands in the command line when I got confused how to reword my commit messages.

For where it fell short, I like to learn with analogies, and so I would bring something up sometimes Claude would just discard the hwole thing unless it fit perfectly or sometimes it would even just misinterpret what I was saying. Luckily, I was able to push back, but also I wouldn't say it was the worse thing all the time because it pushed me to articulate my thoughts more clearly.

**What would you do differently if you started over?**
I think I'd do better with readjusting my plan as I go or even just using it. I kind of treated it as its own isolated document, when really it was the key to helping me stay organized and on track. I feel like I definitely went on some tangents that I didn't need to when I was learning about loggers. Though, I'm glad I did it, I'm not sure I needed to go that in depth for the project. Thus, I'd want to get better at making sure I know what exactly what I need or the acrtual goal of the current step I'm at, so that provides better guardrails around the work I'm doing.

**What are you most proud of from this module?**
I'm honestly so happy about the tests I added, and the fact that I even noticed the method not being used. I can't lie, Claude did provide a beautiful assist when it helped me identify the configuration function, but I was the one that noticed that the rest of the codebase never called it. And then the fact that I decided to test the bare structlog and the codebase's method was so satisfying.

One of my biggest worries when contributing is not thinking outside the box enough with tests but somehow still only focusing on the atomic issue. Like it always feels like there could technically be something missing, so how do you know what to include or not, but this felt like a pretty solid attempt.
