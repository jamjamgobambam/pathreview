## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/148)

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is located in the `extract_skills()` function within `ingestion/parsers/skill_extractor.py`. The function takes a text string as input for analysis. Currently, it fails to identify JavaScript-related work, and it fails to properly recognize TypeScript keywords or associated file extensions (.tsx/.ts). In the case of TypeScript, it incorrectly attributes the skills only to `React` rather than identifying the language itself. Essentially, the language detection for the JavaScript/TypeScript family is broken. 
I exectuted the tests and found that five tests are failing 
```bash
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_text_with_typescript_files - assert False
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_database_technology_detection - UnboundLocalError: cannot access local variable 'skill_names' where it is not associated with a value
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_devops_tool_detection - assert False
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_javascript_detection - assert False
```

A successful fix would restore the ability of the SkillExtractor to accurately parse and categorize JS/TS-related content. Specifically, it would accomplish the following:

- **Comprehensive Detection:** Enable the function to recognize and return "JavaScript" as a detected skill when the input text mentions JS-related terminology or file extensions (e.g., index.js).

-  **Correct TypeScript Attribution:** Ensure that TypeScript keywords and files (e.g., .tsx, .ts) are correctly identified as "TypeScript" rather than defaulting only to "React.

- **Unit Tests:** The fix must successfully pass the specified unit test cases: `test_javascript_detection`, `test_text_with_typescript_files`, `test_devops_tool_detection`, and `test_docker_compose_detection`.

**Is this issue right for me:**  

- **Part 1 — Understanding the Issue**  
    As described in the problem summary section, I can explain the issue in my own words, locate the relevant files and functions affected, and clearly explain the expected outcome once the issue is fixed.

- **Part 2 — Tier Fit**  
    This is a localized issue that primarily affects the `skill_extractor.py` file. I chose a `Tier 1` issue because I have limited exposure to contributing to open-source projects, and this is the first AI-related codebase I have contributed to. The scope of the issue is a bug fix, and I am confident that my skill level and understanding of the subject are sufficient to resolve this issue.

- **Part 3 — Codebase Readiness**  
    I have found the specific parts of the codebase that cause the mentioned test cases to fail. I also looked into the test cases that pass. By comparing these tests, I have found the missing pieces of code that cause the test cases to fail. I believe at this point, I have sufficient contextual codebase knowledge to write a rough plan for fixing the issue.

-   **Part 4 — Scope and Time**  
    I checked the issue description and other related comments of this issue on the issue tracker. At the time of writing, several students are working on this issue. With my schedule, it might take me one to two weeks to complete, depending on the limited time available to me; however, I am confident I can make a PR before the deadline with relevant documentation. This issue has no open blockers or dependencies on other unresolved issues. It references only a PR that has failed to merge.

Therefore, with the above-mentioned reasoning, I decided to choose `issue #148` to be fixed.  

**Branch name:** fix/148-skill-extractor-fails

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit links:** 
- https://github.com/dineshigdd/pathreview/commit/d1bb46fb9fa2dfe219dda68c08766a321520b802
- https://github.com/dineshigdd/pathreview/commit/0518faa6cb423a0b71275b076e679baa46c1a8f8  

**Reproduction summary:**
Before reprodicing bugs, I analyzed the `extract_skills()` in `skill_extractor.py` that detects JavaScript/TypeScript.

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
In the above code, is `if re.search(r"\b(import|require)\s+", text):` the only code-level check that can trigger JavaScript detection? Therefore, any pattern that is not detected by the regex `\b(import|require)\s+` will not be counted as JavaScript. The following section shows four cases --with some edge cases-- in which JavaScript is not detected.


**Bug Reproduction Script:**
```bash
python3 <<'PY'

from ingestion.parsers.skill_extractor import SkillExtractor

# Comprehensive Bug Reproduction Suite for JavaScript/TypeScript Detection
# This suite covers both standard JavaScript patterns and edge cases where 
# the current heuristics (file extensions, package.json, import/require regex) fail.

test_cases = [
    {
        "name": "Standard ES6 Modern Syntax (No extension, no import/require)",
        "code": """
        const calculateTotal = (items) => {
            let subtotal = 0;
            var taxRate = 0.05;
            return subtotal * taxRate;
        };
        """
    },
    {
        "name": "Traditional Function Declaration with Console Logging",
        "code": """
        function displayWelcomeMessage(username) {
            console.log("Welcome back, " + username);
        }
        """
    },
    {
        "name": "ES6 Class Definition without Module Imports",
        "code": """
        class ShoppingCart {
            constructor() {
                this.items = [];
            }
            addItem(item) {
                this.items.push(item);
            }
        }
        """
    },
    {
        "name": "Asynchronous Function Using Promise/Fetch Patterns",
        "code": """
        async function fetchData(url) {
            let response = await fetch(url);
            let data = await response.json();
            return data;
        }
        """
    }
]

e = SkillExtractor()

print("=== Running Skill Extractor Bug Reproduction Suite ===\n")
for index, test in enumerate(test_cases, start=1):
    detected_skills = e.extract_skills(test["code"])
    skill_names = [d.name for d in detected_skills]
    
    print(f"Test Case {index}: {test['name']}")
    print("Code Snippet:")
    print(test["code"].strip())
    print(f"Detected Skills: {skill_names}")
    print("-" * 50)

PY
```  

*Output*  

```bash
=== Running Skill Extractor Bug Reproduction Suite ===

Test Case 1: Standard ES6 Modern Syntax (No extension, no import/require)
Code Snippet:
const calculateTotal = (items) => {
            let subtotal = 0;
            var taxRate = 0.05;
            return subtotal * taxRate;
        };
Detected Skills: []
--------------------------------------------------
Test Case 2: Traditional Function Declaration with Console Logging
Code Snippet:
function displayWelcomeMessage(username) {
            console.log("Welcome back, " + username);
        }
Detected Skills: []
--------------------------------------------------
Test Case 3: ES6 Class Definition without Module Imports
Code Snippet:
class ShoppingCart {
            constructor() {
                this.items = [];
            }
            addItem(item) {
                this.items.push(item);
            }
        }
Detected Skills: []
--------------------------------------------------
Test Case 4: Asynchronous Function Using Promise/Fetch Patterns
Code Snippet:
async function fetchData(url) {
            let response = await fetch(url);
            let data = await response.json();
            return data;
        }
Detected Skills: []
--------------------------------------------------

```   

The `issue #148` also states that the `extract_skills()` function fails the test_devops_tool_detection() test case, which includes keywords for setting up `Docker` and `Docker Compose`.
I have reproduced this bug as follows:
 
```bash
python3 <<'PY'

from ingestion.parsers.skill_extractor import SkillExtractor

docker_false_negative_cases = [
    {
        "name": "Dockerfile",
        "snippet": """
FROM python:3.9
RUN pip install requirements.txt
EXPOSE 8000
""",
        "expected_bug": (
            "Should detect Docker from Dockerfile directives "
            "(FROM, RUN, EXPOSE) but does not because "
            "the word 'docker' never appears."
        ),
    },
    {
        "name": "Docker Compose",
        "snippet": """
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
""",
        "expected_bug": (
            "Should detect Docker from docker-compose syntax "
            "(services, build, ports) but does not because "
            "the word 'docker' never appears."
        ),
    },
]

e = SkillExtractor()

print("=== Running Docker False Negative Reproduction Suite ===\n")

for index, test in enumerate(docker_false_negative_cases, start=1):
    skills_dict = {}
    e._detect_tools(test["snippet"], skills_dict)

    print(f"Test Case {index}: {test['name']}")
    print(f"Detected Skills: {list(skills_dict.keys())}")
    print(f"Expected Bug: {test['expected_bug']}")
    print("-" * 60)

PY

```

*Output*

```bash
=== Running Docker False Negative Reproduction Suite ===

Test Case 1: Dockerfile
Detected Skills: []
Expected Bug: Should detect Docker from Dockerfile directives (FROM, RUN, EXPOSE) but does not because the word 'docker' never appears.
------------------------------------------------------------
Test Case 2: Docker Compose
Detected Skills: []
Expected Bug: Should detect Docker from docker-compose syntax (services, build, ports) but does not because the word 'docker' never appears.

```

The following section shows the plan to fix the issue by detecting JavaScript/TypeScript for the optimal possible solution.

**PLAN.md link:** [My plan to fix issue #148](./PLAN.md)

**Walkthrough video (recommended):** [Issue #148 : bug reproduction and planning](https://www.loom.com/share/7b5502a57ead43c2b4d9db79e6441d73)

**Blockers or open questions:** --

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have successfully implemented both JavaScript/TypeScript and Docker/Docker Compose detection for this issue.
    - **JavaScript/TypeScript:** Improved the regular expression within `_detect_languages()` in `skill_extractor.py` and added corresponding unit tests in `test_skill_extractor.py`.  
    - **Docker/Docker Compose:** Refactored the detection logic by introducing a new helper function, `_detect_docker()`, and integrating it into `_detect_tools()`. Verified these changes using comprehensive test cases in `test_skill_extractor.py`

**Next steps:**
I will review the new code and run all added tests to ensure my modifications haven't introduced any errors. Finally, I will finalize the documentation and prepare the pull request (PR).

**Blockers:**
When committing changes to the test files, `mypy` flagged missing type annotations in both existing and newly added test functions. While these new test cases strictly follow the project guideline of **The Core Rule: Match the Existing Pattern**, `mypy` enforced stricter type-checking. Following guidance from class, this was resolved by using the `--no-verify` flag during the commit.


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/647

**Branch:** `fix/148-skill-extractor-fails`

**What you built:**
I updated `_detect_languages()` in `skill_extractor.py` by expanding its regular expressions — introducing JavaScript/TypeScript keyword patterns (JS_TS_KEYWORD_PATTERNS), TypeScript syntax patterns (TS_SYNTAX_PATTERNS), and a JavaScript arrow-function pattern (JS_ARROW_PATTERN). This improves the JavaScript/TypeScript detection in `extract_skills()`, which invokes `_detect_languages()`.

I also added a new function, `_detect_docker()`, in `skill_extractor.py`. It detects Dockerfile instructions and docker-compose syntax, and is invoked inside `_detect_tools()`. Because of it, `extract_skills()` — which calls `_detect_tools()` — can now recognise Docker and Docker Compose even when the literal word "docker" is absent.

**Tests added or updated:**
The tests added for JavaScript/TypeScript detection:  
    | Test case | Description |
    | :--- | :--- |
    | `test_javascript_es6_import_detection` | Detects ES6 `import ... from` syntax as JavaScript |
    | `test_javascript_arrow_function_detection` | Detects arrow functions and variable declarations |
    | `test_javascript_function_class_export_detection` | Detects `function/class/export` syntax as JavaScript |
    | `test_plain_text_not_detected_as_javascript` | Ignores prose containing JS-like words to prevent false positives |
    | `test_unsupported_language_not_detected_as_javascript` | Ignores Go source code to prevent misdetection as JavaScript/TypeScript |
    | `test_missing_filename_returns_list` | Handles missing filenames with non-code text by returning a list without error |
    | `test_empty_filename_does_not_crash` | Handles empty filename strings gracefully |
    | `test_python_shared_keywords_not_detected_as_javascript` | Avoids collisions by keeping Python code using import/class/async/await strictly as Python |
    | `test_malformed_snippet_does_not_crash` | Handles truncated or incomplete code by returning a list without raising an error |
    | `test_minimal_valid_snippet_still_detected` | Guards against false negatives by successfully detecting tiny valid JS declarations |
   
The tests added for Docker and Docker compose detection:  
    | Test case | Description |
    | :--- | :--- |
    | `test_dockerfile_copy_cmd_detection` | Detects a Dockerfile using COPY and CMD as Docker |
    | `test_multistage_dockerfile_detection` | Detects a multi-stage Dockerfile as Docker |
    | `test_compose_services_image_detection` | Detects a compose file using services + image |
    | `test_compose_volumes_detection` | Detects a compose file declaring volumes |
    | `test_non_docker_yaml_not_detected` | Ignores generic YAML with no services or Dockerfile |
    | `test_pip_install_alone_not_detected_as_docker` | Ignores a bare pip install line to prevent misdetection |
    | `test_partial_docker_config_does_not_crash` | Handles incomplete configs by returning a list without crashing |
    | `test_docker_detected_in_large_multiblock_text` | Detects a Dockerfile embedded within large text blocks |
    | `test_docker_detected_regardless_of_filename` | Identifies Docker based on its body regardless of the filename |
    | `test_docker_keywords_in_shell_script_not_detected` | Ignores lowercase `from/copy/run` keywords inside a shell script |
       

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**  No review came in

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The most difficult part of the process was setting up the local development environment. The reason for this was partly because I did not read the correct documentation related to setup and pre-existing conditions on my local machine.

The biggest mistake I made in setting up the local development environment was not reading the correct documents. I initially started setting up by following the "What to Do This Week" section in the Week 7 `Show (Project) section` and using AI tools such as `Gemini`, and completely missed the `SETUP.md`. Consequently, it took me a long time to set up the local environment, and I had a lot of compatibility issues because I did not install Docker. Eventually, I found out my mistake and followed the `SETUP.md`. From that point onward, setting up became a smooth process.

I was doing all the project work in Windows and used Git Bash as the terminal. This works well for a small codebase. However, this project had a large and complex codebase. With some support from AI, I decided to install the project in Linux (WSL) as it is a useful experience for future projects as well. As a result, I had to install some of the prerequisites needed for this project, such as Docker and Docker Compose, and update other requirements such as Node and Python.

Other than setting up the local environment, I also found it somewhat challenging initially to understand the architecture (project structure) of the codebase. But with the resources available in the Student Hub, I overcame this challenge by first trying to gain a high-level understanding of the project structure and then navigating from the front end to the back end in detail for the specific part of the project related to the `issue #148` I tried to address.

**What did you learn about working in a large codebase?**
I think building your own project is surprisingly easier than understanding someone else's codebase. When building your own project, you know the ins and outs of the project from the beginning and you are gradually aware of how a simple project grows into a large, complex project layer by layer.

On the other hand, contributing to someone else's codebase is synonymous with dropping a traveler into a thick jungle with a compass and a map. A traveler has to use their knowledge of reading maps and compasses to navigate the thick jungle. So as a developer, with knowledge in software engineering and with the assistance of documents such as `README.md`, `CONTRIBUTING.md`, and `SETUP.md`, a developer has to find their way to the section of the codebase to address the issue they are concerned with, rather than getting lost in the details and depth of the codebase and researching unnecessary sections that are not related to the issue.

**How did AI tools help — and where did they fall short?**
*How I use AI tools*  
- Implementation phase  
    AI tools were most useful in the implementation stage when I expanded the functionality of `_detect_languages()` for JavaScript and TypeScript detection and when I added the new function `_detect_docker` for Docker and Docker Compose detection in `skill_extractor.py`. The code generated based on the `PLAN.md` was initially not as I expected and did not detect JavaScript or TypeScript. Therefore, I revised my prompt and instructed the AI to use all the keywords in `JS_TS_KEYWORDS` and regular expressions to cover the test cases that I had planned.

- Planning phase  
    While I primarily came up with the steps myself in the planning phase, I had some assistance from AI in planning and developing test cases in `test_skill_extractor.py` . In bug reproduction, I used AI mainly to come up with the Python code after analyzing the `issue #148` thoroughly and informing the AI of the type of bug reproduction I expected.

*Beyond AI*  
- Understanding the codebase and issue  
    While AI is immensely helpful, in understanding the codebase, issue, and planning, I used AI minimally. I found through my experience in this course that AI produces useful solutions when the prompt is more specific. Vague prompts produce broad solutions that are not very useful. Therefore, I tried to have a good understanding of the codebase and especially about the issue I tried to address without using AI, and then used AI only for validating my understanding.

- Creativity in the planning phase  
    When developing `Map` and `Plan` to create a solution for this issue, I came up with the high-level idea. As I had an in-depth understanding of the issue, I was able to come up with a fairly reasonable solution. 

    When identifying limitations, unknowns, and edge cases, I came up with the high-level idea. However, I did use AI partially in refining my ideas.

- Reviewing the AI code  
    I manually reviewed and tested all the code generated by AI. This helped me instruct the AI to refine some of the code it generated, as I mentioned before with the JavaScript/TypeScript logic implementation.

**What would you do differently if you started over?**
- Issue selection  
    I chose a beginner-friendly issue(`issue #148`). While I am satisfied with my issue selection, I would probably choose an issue related to AI if I started over. The reason for this is that I could have applied the concepts I learned in previous modules to the open-source contribution.

- Refining test cases  
    I would use AI to refine my test cases more. I used AI to come up with test cases, but if I were to start this issue or any other issue over again, I would carefully review the test cases to refine them. I had overlapping test cases in this project; I would combine those and minimize redundant test cases, with or without using AI tools.

- Planning and scope  
    When planning the solution for the issue, I focused more on improving the regular expressions and did not put much effort into identifying other JavaScript- and TypeScript-related file extensions, such as `JSX` or `TSX`. Therefore, I would address these extensions if I started over.


**What are you most proud of from this module?**
I am proud that I used AI as a tool without blindly accepting its outcomes for the most part. I tried to understand the codebase and the issue with minimal use of AI. I think this part is critical as it provides an opportunity for real learning about the codebase and the issue to address. This understanding helped me to address the issue effectively, and I am proud of that achievement. I am confident that I can address more challenging issues later in open-source contributions.