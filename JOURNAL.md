## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
<!--In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.] -->
This issue lies within the safety directory in pii_scrubber.py. Currently a number like "750-345-5346" will go through and not be detected as PII. A fix would have the parentheses scrubbed from the number and it detected as PII so that a user's information is properly funneled into the proper protective/safety channels. After fixing that mathcing issue, a few failing tests must pass before this issue is considered complete.

**Branch name:** fix/146-pii-scrubber-fails-parenthesized-phone-number-redaction

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Is this right for me?**

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** N/A - mypy and ruff specifies test constraints I have not been able to meet.

**Reproduction summary:**
I used the reproduction code given on the issue's page. I observed the scrub() function failing to scrub a phone number with parentheses around a set of its numbers and the detect() function failing to detect the same phone number as PII.

**PLAN.md link:** [PLAN.md](https://github.com/IGS1I/guided-PathReview/blob/fix/146-pii-scrubber-fails-parenthesized-phone-number-redaction/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
I am still unsure how to properly recreate the PII phone number issue within the launched app since the login credentials do not work.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Nothing completed so far. Having issues getting account user and passowrd to work for the pathreview app.

**Next steps:**
Skip the authenitcation issue, implment my fix and test with unit test (test/unit/test_pii_scrubber.py)

**Blockers:**
Laziness and other work I have set up.

### Check-in 2 (end of week)

**PR link:** [PR-915](https://github.com/ascherj/pathreview/pull/915)

**Branch:** fix/146-pii-scrubber-parenthesized-phone-number-redaction

---

**What you built:**
The update was for the PII_PATTERNS dictionary in pii_scrubber.py. The dictionary holds the parameters/conditions for PIIs. "\b" looks for characters and does not account for non-characters like parentheses '()', so the fix to recognize parentheses phone numbers with PII_Scrubber.detect() and hide parentheses phone numbers with PII_Scrubber.scrub() was to add `(?<!\d)` at the front of the phone_us entry in PII_PATTERNS.

A seperate addition was `\b` at the end of the street address entry of PII_PATTERNS since another test, regarding street addresses, in the unit test for the PII_Scrubber was failing.

**Tests added or updated:**
No unit tests added, used the default tests that interact with the pii_scrubber.

However, added tests/security/debug_pii.py script to test scrub() and detect().

**Self-review confirmation:** [x] python pytest tests/unit/test_pii_scrubber.py -v passes

~~[ ] make check passes  [] make test-unit passes~~

**Draft PR feedback received from:** [stephanyTF](https://github.com/ascherj/pathreview/pull/915#issuecomment-5195409304) on GitHub and Stephany Lam on Slack

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
Reviewer thought my section descriptions were great and that my addition of screenshots of my code were nice. She also found a lot that I could change:

- Focus on singular issue, despite easy adjacent fixes
- Detail ALL changes made
- Specify all test cases passed and added
- `Fixes issue [#146]` is redudnant since `Closes #146` already have in Issue section
- Elaborate on purpose and function of tests

**How you responded:**
Thank you @stephanyTF !

Thank you Stephany. I noted some of the changes that you mentioned as well as I reviewed other PRs from my peers. I agree that I should have added more specificity for tests. I understand as well that widening the issue's scope to the street address failure is not a necessary thing and should be brought up with the maintainers rather than my own discretion. I will take your notes into my future open-source and PR work. 🙏🏾

I did not make any changes to my PR since the due date has alredy passed.

---

### Reflection

**What was harder than you expected?**
I was surprised that the application did not work properly. The user credentials generated did not work to log into the path review app. I also did not expect `make check` and `make test-unit` to be mandatory since they will always fail massively since the whole codebase is riddled with failures, despite any fix created for any singular issue.

**What did you learn about working in a large codebase?**
Time has to be made to understand another's work. This can be time consuming, possibly as time consuming as building things yourself depending on how large the codebase is and how clear the author(s) made the function and variable names.

**How did AI tools help — and where did they fall short?**
AI tools helped me with taming ruff and black linting rules when I went to push my changes, as well as how to properly recreate the issue and test for its claim. I used GitHub Copilot mainly since it is integrated into VsCode pretty well. They tried solving the issue in safety/pii_scrubber.py and I had to stop its thinking so I can do the work myself.

**What would you do differently if you started over?**
I would have reached out to the Slack channel more. The app did not work so I could not see the issue visually, something that may have helped others with their issues.

**What are you most proud of from this module?**
I am not proud of any of my work per se, but I am glad I got to work with some of the issues that arose as I tried to make changes. I ran into linting issues with ruff and black formatters that are set to run when pushing commits/making changes to the codebase. The base files suprisingly did not follow the rules, which allowed me time to read output messages/files and figure out how to easily fix the chanegs specified by formatters. It is the reason the on the source of this file, there is another line after this paragraph, that each .md file starts with a `#` then `##` and so one, and that each title has newlines before and after itself. Was cool to see that the issue had such a simple solution in PII_PATTERNS dictionary in safety/pii_scrubber.py.
