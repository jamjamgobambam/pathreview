## Solution plan

**Issue:** #151: Bias detector patterns are too narrow to match common phrasings 

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

This issue is caused by the regex patterns creating a strict template to match against all phrases fed into testing. We expect the bias_detector to use common words to match against phrases to determine whether the entire statement is dismissive or 

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

I expect to touch the following files.
- Files included
   -  `safety/bias_detector.py`
    - `tests/unit/test_bias_detector.py`

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Create two categories for classification -> Subject + Dismissive. Subject denotes who/what is being judged (online course, bootcamp, immigrant, etc..) Dismissive denotes the negative judgement (can't, not, struggle, lack, etc..). 
2. The idea is to match at least 6 words within the phrase to determine whether it is biased. Replacing regex character matching with re.fullmatch helps to create a more robust way of properly assessing negative semantic meaning
3. Then I included a negation guard to make sure less false negatives are applied to the output. 

### Inputs & outputs
What does your fix take as input? What should it produce or change?

This fix allows the same inputs, but just adjusts the parameters for bias detection

### Risks & unknowns
What could go wrong? What are you still unsure about?

If a different type of phrase is entered through the bias detector that doesn't have any of the matching dismissive or subject values, it could still cause errors. 
### Edge cases
What inputs or states should your fix handle gracefully?

I added a normalizer to make all inputs clean. This way if there is a hyphen between words like self-taught, all iterations of the spelling will be treated the same.

****
