## Solution plan

**Issue:** rompt injection defense doesn't sanitize newline characters in user-supplied resume text https://github.com/ascherj/pathreview/issues/64 

### Understand
This behavior arises as a result of a failure to extract forbidden characters in a string. In `safety/prompt_defense.py` there is a function called "sanitize" which takes in a string and returns the sanitized text, this function fails to strip escape sequences, such as `\n---\n` and `\nSystem:`

### Map
I expect it to touch the `safety/prompt_defense.py` file, as well as all of the tests that connect to this file

### Plan
- First I identify the existing behaviors of the sanitizer function
- Secondly, I add the blocked sequences to a list, which defines which substrings I block
- Lastly, I remove all these strings from the input

### Inputs & outputs
Input: Unclean String

Output: Sanitized Strings


### Risks & unknowns
The major risk factor here is that it could potentiall modify the input string in unintended ways, such as removing the letter "n" in certain words and sequences. I will have to find a way of gracefully handing that 

### Edge cases
It should handle:
- Empty Strings
- Large Strings (Maybe have a cap)
- Only the forbidden characters (Return empty string)
- Already clean string (don't do anything)