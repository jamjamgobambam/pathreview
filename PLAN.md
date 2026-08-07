## Solution plan

**Issue:** [#148 - Skill extractor fails to detect JavaScript and TypeScript](https://github.com/ascherj/pathreview/issues/148)


### Understand
This issue can be divided into two parts,but the root cause is similar

**1. Not detecting JavaScript/TypeScript**  
    **Root cause:**  
    The following code in `_detect_languages()` function in `SkillExtractor` class detects `JavaScript/TypeScript`
    ```python
    if ".js" in str(filename or "").lower():
                js_evidence.append("JavaScript file extension (.js)")
            if ".ts" in str(filename or "").lower():
                js_evidence.append("TypeScript file extension (.ts)")
            if re.search(r"\b(import|require)\s+", text):
                js_evidence.append("CommonJS or ES6 imports")
            if "package.json" in text_lower:
                js_evidence.append("package.json found")
    ```
    The root cause of this bug is that the regular expression `r"\b(import|require)\s"` only detects `JavaScript/TypeScript` code containing the `import` or `require` keyword followed by one or more whitespace characters. Therefore, it will detect, for example, `import React from 'react';` or `import { useState } from 'react';`, but not `const fs = require('fs');`. Additionally, it can produce false positives because `import` matches Python statements such as `import os` or `import sys`. This regular expression does not detect other keywords in `JS_TS_KEYWORDS`: `export`, `const`, `let`, `var`, `function`, `async`, `await`, and `class`. Another concern that could complicate detecting JavaScript/TypeScript is that the `JS_TS_KEYWORDS` set includes overlapping keywords (`import`, `class`, `async`, `await`) that are also present in the `PYTHON_KEYWORDS` set.


**2. Not detecting devops tools such as docker and docker compose**   
    **Root cause:**     
    The root cause for not detecting `docker` or `docker compose` is that the `_detect_tools()` function detects DevOps tools by matching keywords in the `TOOLS` set. As issue [#148](https://github.com/ascherj/pathreview/issues/148) states, `test_devops_tool_detection` and `test_docker_compose_detection` fail. The reason for this is because these test cases do not contain the keyword `docker` (which is used in the `TOOLS` set) in the `text` variable. The following code, `detect_tools()`, is responsible for this keyword matching.

    ```python
    for tool, confidence in self.TOOLS.items():
                if tool in text_lower:
                    display_name = tool.upper() if tool in ["ci/cd"] else tool.title()
    ```

### Map
**Files I expect to touch:**
- `ingestion/parsers/skill_extractor.py` - conditional statement `if re.search(r"\b(import|require)\s+", text)` , which attempt to detecgt JavaScript/TypeScript text using keywords, of `_detect_languages()` function. I will modify this regular expression to match more complex `JavaScript/TypeScript` code.

- I will add more keywords to `JS_TS_KEYWORDS` set so that logic for detecting `python` scripts will not connfuse `JavaScript/TypeScript` code

- `tests/unit/test_skill_extractor.py` - I will add test cases that covers Positive cases, Negative cases,false positives,false negatives,and TypeScript-specific syntax.

- In this issue resolution , I will focus on improving the logic to detect `docker` and `docker compose`. I will add special Docker detection logic using regex patterns in `_detect_tools` function. If it is neccessary I will implemnt this as separate function.

- I will also add more test cases in `test_skill_extractor.py` that covers Dockerfile,Multi-stage Dockerfile,Compose, Non-Docker YAML,and pip install requirements.txt.

### Plan
**For detecting JavaScript/TypeScript**
1. In `ingestion/parsers/skill_extractor.py`, identify the function and code within the `SkillExtractor` class that detects JavaScript/TypeScript.
2. Improve the regular expression that detects JavaScript/TypeScript in the code identified in Step 1.
3. Add test cases in `tests/unit/test_skill_extractor.py` to cover:
    - Positive cases (should detect JavaScript/TypeScript)
    - Negative cases (plain text, unsupported languages, empty/missing filenames)
    - False positives & cross-language collisions (Python code with shared keywords)
    - False negatives & malformed/incomplete code snippets
    - TypeScript-specific syntax (interfaces, type annotations)
    - Conflicting signals (mismatched filename extensions vs. code body)
    - Size extremes (very small snippets vs. large multi-block text)
4. Run each test case that I added in Step 3, as well as `test_mixed_language_text` in `tests/unit/test_skill_extractor.py`.


**For detecting Docker and Docker Compose**
1. In `ingestion/parsers/skill_extractor.py`, identify the function and the part of the code within the `SkillExtractor` class that detects Docker and Docker Compose.
2. Improve the regular expression that detects Docker and Docker Compose tools in the code identified in Step 1.
3. Add test cases in `tests/unit/test_skill_extractor.py` to cover:
    - Dockerfile (`FROM`, `RUN`, `EXPOSE`)
    - Dockerfile (`COPY`, `CMD`)
    - Multi-stage Dockerfile
    - Compose (`services`, `build`)
    - Compose (`services`, `image`)
    - Compose (`volumes`)
    - Non-Docker YAML (negative)
    - `pip install requirements.txt` alone (negative)
    - Partial or malformed configurations & size extremes (small snippets vs. large multi-block files)
    - Missing, empty, or neutral filenames providing no technology hints
    - Contextual keyword collisions (Docker-related keywords used in non-Docker contexts like shell scripts)

### Inputs & outputs
**Functions that I'm changing:**
- `_detect_languages(text: str, filename: Optional[str]) skills_dict: dict ) -> None:`
- `_detect_tools(text, detected_skills)`

**Existing happy path:**  
*Inputs*
- `text`: String variable that holds JavaScript, TypeScript, Docker, and Docker Compose texts.
- `filename`: String variable  An optional variable that contains the filenames of JavaScript or TypeScript files with the extension `.js` or `.ts`.
- `skills_dict`: A dictionary that stores detected skills.

*Output*
- Return Value: `None`  
Although this function returns `None`, it modifies the `skills_dict` dictionary passed to it. Specifically, it adds detected programming languages as `SkillDetection` objects, using the language name as the key and the corresponding `SkillDetection` instance as the value.

For example, if JavaScript code is detected, the function may add an entry such as:

```python
skills_dict["JavaScript"] = SkillDetection(...)
```

### Risks & unknowns
- **Cross-language keyword collision:** Broad regex patterns or shared syntax keywords (such as import, export, or class structures) risk misclassifying JavaScript or TypeScript code as Python skills. We need to ensure language parsers are scoped strictly by file extensions (e.g., .js, .ts, .py) or explicit context rather than generic keyword matching alone.
- ***Regex limitations for full language coverage:***
     JavaScript contains 38+ reserved keywords, and TypeScript adds numerous type-system-specific keywords. Attempting to catch every edge case or combination via regular expressions is impractical and risks high false-positive rates (particularly due to keyword overlap with Python, such as `import`, `class`, `async`, and `await`). We will focus on capturing the most common and critical patterns.
- ***Regex limitations for Docker and Docker Compose structures:*** Dockerfiles support complex multi-line syntax, flags, and build arguments, while Docker Compose files rely on nested YAML structures that can vary significantly. Using basic regular expressions to capture every valid configuration risks missing edge cases or misclassifying generic YAML files (false positives). Therefore , we will focus on detecting high-confidence indicators like common Dockerfile instructions (`FROM`, `RUN`, `CMD`) and Compose service keys.

### Edge cases
**For langauge detection** 
- No language indicators are present in the input text.
- The filename is missing, empty, or uses an unsupported extension.
- The input contains code from multiple programming languages.
- The input contains ambiguous syntax or keywords shared across languages.
- The filename and source code indicate different languages.
- The input contains malformed, incomplete, or non-executable code.
- The input contains only documentation, comments, or plain text.
- The input contains unsupported programming languages.
- The input is very small and contains limited evidence for language detection.
- The input is very large and contains multiple code blocks or language indicators.

**For Docker and Docker Compose detection**
- No Docker or Docker Compose indicators are present in the input text.
- The input contains only a partial Dockerfile or Docker Compose configuration.
- The input contains configuration syntax that resembles Docker Compose but belongs to another YAML-based tool.
- The input contains keywords commonly used in Docker configurations but in a non-Docker context.
- The input contains multiple technologies or configuration formats in the same text.
- The input contains malformed or incomplete Dockerfile or Docker Compose content.
- The input is very small and contains limited evidence for reliable detection.
- The input is very large and contains multiple configuration blocks.
- The filename is unavailable, empty, or provides no indication of the underlying technology.
- Docker-related evidence appears in the content without the literal word "Docker".