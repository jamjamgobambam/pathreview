## Solution plan

**Issue:** Skill extractor fails to detect JavaScript and TypeScript (https://github.com/ascherj/pathreview/issues/148)

### Understand
The root cause of this issue is that the skill extraction logic in the ingestion pipeline does not recognize "JavaScript" and "TypeScript" as valid technical skills. The expected behavior is that when a user's resume contains these languages, they are successfully parsed and added to the extracted skills list. The actual behavior is that they are silently ignored and dropped from the final output.

### Map
The specific file involved in this extraction logic is `ingestion/parsers/skill_extractor.py`. I will need to update the data structure (likely a list, set, or dictionary of allowed keywords) or the regex pattern within this file to include both languages.

### Plan
1. Locate the exact list or regex pattern inside `ingestion/parsers/skill_extractor.py` that dictates which skills are successfully matched.
2. Append "JavaScript" and "TypeScript" to the allowed skills list, ensuring they match the existing string format conventions.
3. Locate the corresponding unit test file (likely inside `tests/ingestion/`) and add a test case passing a dummy resume containing these languages.
4. Run `make test-unit` to confirm the extractor now successfully flags these skills without breaking existing matches.

### Inputs & outputs
* **Input:** Raw resume text strings fed into the ingestion pipeline (e.g., "Proficient in Python, JavaScript, and HTML").
* **Output:** A standardized array/list of extracted skill strings (e.g., `["Python", "JavaScript", "HTML"]`).

### Risks & unknowns
* **Risk:** If the extraction uses naive regex matching, adding "JavaScript" might accidentally interfere with matches for "Java" if word boundaries (`\b`) are not strictly enforced in the pattern. I need to investigate how the current string matching isolates whole words.

### Edge cases
1. **Case Insensitivity:** The fix must gracefully handle variations in capitalization (e.g., "javascript", "Javascript", "typeScript").
2. **Punctuation/Formatting:** The fix must successfully extract the languages even if they are immediately followed by commas, periods, or parentheses (e.g., "JavaScript," or "(TypeScript)").