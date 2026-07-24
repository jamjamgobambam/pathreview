## Solution plan

**Issue:** [ Bias detector patterns are too narrow to match common phrasings #151](https://github.com/ascherj/pathreview/issues/151) 

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- The root cause is that the regex patterns in the DISMISSIVE_PATTERNS and DEMOGRAPHIC_PATTERNS in the bias_detector.py file are too rigid in its order of flag words
  that makes the bias detector miss sentences with biased language.
- An example of an expected behavior is the case the system generates this biased resonse: "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education'", the bias detector should flag it however it passes it undetected.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
- Regex patterns are in the bias_detector.py file.
- The function we're testing in prior file is detect_bias. 
- Relevant test cases are in the test_bias_detector.py

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. Lessen the rigidness and improve the coverage of the regex in the DISMISSIVE_PATTERNS and the DEMOGRAPHIC_PATTERNS located in the bias_detector.py.
2. Test the new patterns with a wide range of diverses test cases
3. Plan and implement another text scanner besides regex like Pre-Trained Sentiment Models (TextBlob) or an AI trained model (Hugging Face Transformers)  

### Inputs & outputs
What does your fix take as input? What should it produce or change?
The fix should take Pathreview's generated response to the user and it should return the correct bias lable for it.

### Risks & unknowns
What could go wrong? What are you still unsure about?
The two suggested implementations could fall short. The first in improving the regex pattern may be futile as regex can be very rules based so it may not cover all types of language cases. The second with implementing ai models to scan for intent may add increased complexity that could make result in heavier processing time. 

### Edge cases
What inputs or states should your fix handle gracefully?
- Language whose biased words can appear in any order in the sentence
- A wide variety of words that signal the same bias intent
- Biased language with euphemism (sounding positive or polite but is just cushioning something negative) 
