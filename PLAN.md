## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

### Understand
**What is the root cause of this issue? What behavior is expected vs. actual?**

Issue [#146](https://github.com/ascherj/pathreview/issues/146) entails a privacy risk with user's PII, specifically their phone numbers. Phone numbers are expected to be redacted, however in the PII scrubber only numbers without pantheses are addressed do if you enter your number as (555)-345-7349 it will show as-is, while entering 55-345-7349 will show as [Redacted]. Phone numbers are expected to be redacted/scrubbed.

### Map
**Which files, functions, or modules are involved?**
**List the specific files you expect to touch.**

safety/pii_scruber.py is the target file. Class PIIScrubber and its functions scrub() and detect() will need to be inspected. The regression test that I will be faithful to and use as a fail-to-pass test is test/unit/test_pii_scrubber.py

### Plan
**What are the steps to fix this issue?**
**Break it into 3–5 concrete sub-tasks.**

1) Find out how to log into PathReview platform since default credentials do not work.

2) Recreate issue

2) Read through pii_scrubber.py and its unit test

3) Run Unit test

4) Draft a solution

5) Test solution

6) Iteratively modify solution if issue remains

### Inputs & outputs
**What does your fix take as input? What should it produce or change?**

My fix is additive. I am modifying what the PII Scrubber considers to be PII, adding the consideration of pantheses in a user's phone number. When the unit test is ran, "[Redacted]" should be printed similar to a phone number without parentheses.

### Risks & unknowns
**What could go wrong? What are you still unsure about?**

Nothing. This issue is relatively small. After going through tests and running the PII Scrubber testing suite, I will know where to focus my efforts.

Though it is possible that my initial fix to the PIIScrubber object will cause a parsing issue. Maybe in modifying bounds for phone number PII ruins bounds for other types of PII.

### Edge cases
**What inputs or states should your fix handle gracefully?**

My fix should be able to **handle parentheses in any of the sets of numbers** that exist in a phone number, not just in the first three. This slightly widens the scope of the issue, but does not fully shift the focus of detecting a phone number with parentheses as PII and redacting it.