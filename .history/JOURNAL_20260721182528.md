## Week 7 — Issue selection

**Issue link:** [(https://github.com/ascherj/pathreview/issues/64)]

**Issue title:** [Prompt injection defense doesn't sanitize newline characters in user-supplied resume text]

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: I'm working on issue #64, a teir 2 bug. The bug allows newline sequences to remove the original system prompt and add new instructions. Resolving this issue would prevent adversarial users from inserting new commands and ensure the resume is parsed as data. As this is located in the safety/prompt_defense, it would also preserve the integrity and authority of the original system prompt.]

**Branch name:** [(https://github.com/Ungadeu/pathreview/tree/fix/64-prompt-injection-defense)]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger