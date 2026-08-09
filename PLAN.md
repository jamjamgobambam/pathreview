## Solution plan

**Issue:** #147 https://github.com/ascherj/pathreview/issues/147

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- In the resume parser, there is a method that detects each new section of a resume (i.e. experience, skills, education). However, the parser does not detect new sections when there is whitespace or extra spaces before the section header. The resume parser should return each section separately but it will skip the ones with whitespace. 

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
- test_resume_parser.py, resume_parser.py are the main files I will work in

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
- I will first go through the failed test cases to figure out what exactly is breaking
- I will go through resume_parser.py and focus on the regex which seems to be the issue 
- I will create new sample inputs to test my fix

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- input and output will not change 

### Risks & unknowns
What could go wrong? What are you still unsure about?
- I am still unsure about how the entire input resume is broken down through regex. 

### Edge cases
What inputs or states should your fix handle gracefully?
- Non-traditional resume structures/styles might affect the way the parser detects sections 