## Solution plan

**Issue:** Bias detector patterns are too narrow to match common phrasings
https://github.com/ascherj/pathreview/issues/151

### Understand
so basically the bias detector uses regex to catch biased language, but the patterns are written super specific, like they only match if someone uses the exact same words the dev originally typed. like it needs the word "is" in a sentence or it needs "developer" singular instead of "developers" plural, stuff like that. so the actual problem isnt that the regex is broken, its that its way too picky about exact wording. it should be catching the same biased idea even if someone phrases it a little different, but right now it just doesnt.

### Map
- `safety/bias_detector.py` this is the only file i actually need to touch, it has the two pattern lists (DISMISSIVE_PATTERNS and DEMOGRAPHIC_PATTERNS)
- `tests/unit/test_bias_detector.py` not touching this file but im using the 9 failing tests as my checklist for what needs to pass once im done

### Plan
1. fix DISMISSIVE_PATTERNS so it accepts more verb variations (cant/cannot/wont/lack/missing) not just "lack|missing", so stuff like "cant write production code" gets caught
2. get rid of the required "is" in the first pattern so "education lacks fundamentals" matches without needing "is" stuck in there
3. fix DEMOGRAPHIC_PATTERNS to accept plural words too (developers, programmers, people) since right now its only singular (developer, programmer, person)
4. widen the poor/rich background pattern so "developers from poor backgrounds" matches, not just "person from poor"
5. add something to catch phrases like "attendance/background means inadequate training" since nothing catches that right now at all
6. after every change run pytest tests/unit/test_bias_detector.py -v again to make sure i didnt break any of the 23 tests that already pass while im fixing the 9 that fail

### Inputs & outputs
input is just a string of feedback text. output doesnt change, still returns (bool, string) like before, is it biased and why. im only changing what makes it return True, not changing the shape of what it gives back

### Risks & unknowns
- if i make the regex too loose i could start flagging stuff that isnt actually biased, like the positive bootcamp mention test or the clean feedback test that currently pass fine. need to double check those still work after i change stuff
- not sure if using .* like the existing immigrant/international pattern is totally safe to copy everywhere else, since it could accidentally match across a whole sentence and catch weird word combos i didnt mean to catch
- some tests check the actual reason string too (like it checks "demographic" is somewhere in the reason), so i gotta make sure i dont accidentally mix up which pattern list gives which reason message

### Edge cases
- empty string and just whitespace should still return False, already works, just dont wanna break it
- has to stay case insensitive, already works via re.IGNORECASE
- if someone mentions bootcamp/age/whatever in a positive or neutral way it needs to stay False, gotta be careful i dont make my patterns so broad they start flagging good feedback too