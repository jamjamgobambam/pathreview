## Solution plan
**Issue:**
    Title: Skill extractor fails to detect JavaScript and TypeScript
    Link: https://github.com/ascherj/pathreview/issues/148 

### Understand
The extract_skills() function should detect text that clearly describes JavaScript work, such as: "Wrote index.js using const arrow functions and async/await callbacks." However, it currently returns no detections for this example.

It should also return "TypeScript" for samples that mention .tsx or .ts files and explicitly use the word TypeScript, such as: "Built app.tsx and types.ts with strict TypeScript interfaces." Instead, it currently returns only "React".

Inside extract_skills(), several helper functions are called to identify languages, frameworks, databases, and tools. In _detect_languages(), JavaScript and TypeScript evidence is collected together in js_evidence. The final language is chosen based only on whether the optional filename argument contains .ts; otherwise, the detection is labeled as JavaScript.

The .tsx extension appears only in REACT_INDICATORS. In _detect_react(), the input text is searched for .tsx, so a sentence containing a .tsx filename can produce a React detection. However, _detect_languages() does not recognize .tsx as TypeScript evidence.

The .ts and .js extension checks in _detect_languages() also look only at the optional filename argument. They do not search for filenames mentioned inside the input text. Because the reproduction examples pass filenames such as index.js, app.tsx, and types.ts as part of the text rather than through the filename argument, those extensions are not used as JavaScript or TypeScript evidence.

The issue description also states that extract_skills() should detect TypeScript when the word "TypeScript" appears in the input. However, the JavaScript and TypeScript section of _detect_languages() does not check for the literal word "TypeScript".

Finally, the JavaScript and TypeScript detection logic relies on a limited pattern that searches only for import or require. While require is a useful JavaScript indicator, import is not unique to JavaScript because Python also uses it. The current logic also misses stronger JavaScript clues in the reproduction example, such as const, arrow functions, and the .js filename mentioned in the text.

### Map
Files I expect to touch:
- ingestion/parsers/skill_extractor.py - Contains the SkillExtractor class and the extract_skills() function which are responsible for detecting skills. Inside this file, I expect to investigate the _detect_languages() function, where the JavaScript and TypeScript langauge detection is implemented. Similarly, I will investigate the _detect_react() function, which does the React language detection and is currently detecting React for some TypeScript inputs.
- tests/unit/test_skill_extractor.py - Contains test_javascript_detection and test_text_with_typescript_files tests that were indicated as failing related tests in the issue description. I will use these tests to verify my fix. I will also run the entire test file to make sure my fix doesn't introduce side effects/regressions. If I notice a lack of coverage on important JavaScript/TypeScript scenarios, I will add additional tests.

### Plan
1. Continue researching the differences between JavaScript and TypeScript, including their syntax, keywords, file extensions, and common code patterns. Use this research to determine which language features extract_skills() should recognize and which features are unique enough to distinguish the two languages.
2. Compare the GitHub issue description with the existing failing tests in tests/unit/test_skill_extractor.py to make sure I understand all of the JavaScript and TypeScript cases the extractor is expected to handle.
3. Continue tracing the JavaScript and TypeScript detection logic in ingestion/parsers/skill_extractor.py to determine why some language features are not being recognized and identify the best place to implement the fix.
4. Update the JavaScript and TypeScript detection logic so that it correctly recognizes the expected language features while preserving the existing behavior for other languages, frameworks, and technologies.
5. Rerun tests/unit/test_skill_extractor.py to verify that the JavaScript and TypeScript tests pass and that the previously passing tests continue to pass. If I identify important JavaScript or TypeScript scenarios that are not covered by the current tests, I will add targeted regression tests.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
**Function I'm changing**
_detect_languages(
        self,
        text: str,
        filename: Optional[str],
        skills_dict: dict,
    ) -> None:

**Inputs**
- text: The text to be analyzed for programming language evidence.
- filename (optional): optional filename whose file extention can be analyzed for additional evidence.
- skills_dict: dictionary that stores detected skills and confidence scores.

**Expected Change**
The fix should allow _detect_languages() to recognize JavaScript and TypeScript evidence found in the input text, rather than relying only on the optional filename argument or the limited import|require pattern.

**Output**
The function will continue to return None. Instead, it should update skills_dict with the correct language and confidence score.

### Risks & unknowns
- JavaScript and TypeScript share many language features, so changing the detection logic may make it more difficult to distinguish between the two without introducing false positives.
- It is not yet clear whether JavaScript and TypeScript detection should rely primarily on filenames, language keywords, code syntax, or a combination of these signals. I will need to determine which approach best matches the expected behavior described in the issue.
- Changes to the JavaScript and TypeScript detection logic could unintentionally affect detection for other technologies, such as React, since some indicators (for example, .tsx) are associated with multiple technologies.
- The existing tests reproduce the reported issue, but it is unclear whether they cover all important JavaScript and TypeScript cases. After implementing a fix, I may need to add regression tests for additional scenarios to help prevent similar issues in the future.

### Edge cases
- filename is None, so file-extension checks cannot be used.
- The text contains evidence for more than one programming language.
- The text contains language features that are shared by multiple languages (for - example, import, async, or await).
- The text references filenames such as .js, .ts, or .tsx instead of providing them through the filename argument.