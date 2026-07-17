## Solution plan

**Issue:** [ Bias detector patterns are too narrow to match common phrasings #151](https://github.com/ascherj/pathreview/issues/151) 

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- The root cause is that the regex patterns in the DISMISSIVE_PATTERNS and DEMOGRAPHIC_PATTERNS in the bias_detector.py file are too rigid in its order of flag words
  that makes the bias detector miss sentences with biased language.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

### Risks & unknowns
What could go wrong? What are you still unsure about?

### Edge cases
What inputs or states should your fix handle gracefully?
