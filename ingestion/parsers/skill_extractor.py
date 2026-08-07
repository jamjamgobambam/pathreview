import re
from dataclasses import dataclass


@dataclass
class SkillDetection:
    """Result of detecting a skill."""

    name: str
    category: str
    confidence: float
    evidence: list[str]


class SkillExtractor:
    """Extract skills from source code and documentation."""

    PYTHON_KEYWORDS = {
        "import",
        "from",
        "def",
        "class",
        "async",
        "await",
        "yield",
        "lambda",
        "with",
    }

    JS_TS_KEYWORDS = {
        "import",
        "export",
        "require",
        "const",
        "let",
        "var",
        "function",
        "async",
        "await",
        "class",
    }

    # Each JS/TS keyword paired with the syntactic context that makes it a
    # reliable signal. Keywords shared with Python (import/class/async/await)
    # use JS-only framing, and words that also occur in plain English
    # ("let"/"function"/"require") only match inside real code, so neither
    # Python nor prose false-positives. Keys mirror JS_TS_KEYWORDS.
    JS_TS_KEYWORD_PATTERNS = {
        # ES6 `import X from '...'` (Python is `from x import y`, never
        # `import ... from`) or side-effect `import './x'` / `import '@scope/x'`.
        # The side-effect form is restricted to relative/scoped specifiers so
        # Go's `import "fmt"` / `import "net/http"` does not collide.
        "import": r"\bimport\b[^\n;]*\bfrom\s+['\"]|\bimport\s+['\"](?:\.{1,2}/|@[\w.-]+/)",
        "export": (
            r"\bexport\s+(?:default|const|let|var|function|class"
            r"|async|type|interface|enum|\{|\*)"
        ),
        "require": r"\brequire\s*\(\s*['\"]",
        "const": r"\bconst\s+[\w$]+\s*[:=]",
        "let": r"\blet\s+[\w$]+\s*[:=]",
        "var": r"\bvar\s+[\w$]+\s*[:=]",
        # function definition, incl. anonymous / generator, requires a body brace
        "function": r"\bfunction\b\s*\*?\s*[\w$]*\s*\([^)]*\)\s*\{",
        # `async function` / `async () =>` / `async x =>` (Python is `async def`).
        "async": r"\basync\s+function\b|\basync\s*\([^)]*\)\s*=>|\basync\s+[\w$]+\s*=>",
        # `const/let/var x = await ...` — JS-only because of the declaration.
        "await": r"\b(?:const|let|var)\s+[\w$]+\s*=\s*await\b",
        # JS class: `class X extends` or `class X {` (Python uses `class X:`).
        "class": r"\bclass\s+[\w$]+\s+extends\b|\bclass\s+[\w$]+\s*\{",
    }

    # TypeScript-only syntax. Primitive type names are the TS spellings
    # (string/number/boolean), distinct from Python's (str/int/bool), so
    # typed Python code does not match here.
    TS_SYNTAX_PATTERNS = (
        r"\binterface\s+[\w$]+\s*\{",  # interface declarations
        r"\btype\s+[\w$]+\s*=",  # type aliases
        r"\benum\s+[\w$]+\s*\{",  # enums
        # type annotation, anchored so prose like "status: number of items"
        # is not treated as a `: number` annotation.
        r":\s*(?:string|number|boolean|any|void|unknown|never)\s*(?:[;,)\]|&=>]|$)",
    )

    # Arrow functions are a strong standalone JS/TS signal.
    JS_ARROW_PATTERN = r"(?:\([^)]*\)|[\w$]+)\s*=>"

    REACT_INDICATORS = {
        "import React",
        "useState",
        "useEffect",
        "useContext",
        "useReducer",
        "useCallback",
        "useMemo",
        "useRef",
        "createContext",
        "ReactDOM.render",
        ".jsx",
        ".tsx",
    }

    FRAMEWORKS = {
        "django": ("Python", 0.95),
        "flask": ("Python", 0.95),
        "fastapi": ("Python", 0.95),
        "sqlalchemy": ("Python", 0.85),
        "numpy": ("Python", 0.85),
        "pandas": ("Python", 0.85),
        "scikit-learn": ("Python", 0.85),
        "tensorflow": ("Python", 0.85),
        "pytorch": ("Python", 0.85),
        "express": ("JavaScript", 0.95),
        "next.js": ("JavaScript", 0.95),
        "react": ("JavaScript", 0.95),
        "vue": ("JavaScript", 0.95),
        "angular": ("JavaScript", 0.95),
        "svelte": ("JavaScript", 0.85),
        "webpack": ("JavaScript", 0.85),
        "vite": ("JavaScript", 0.85),
        "rollup": ("JavaScript", 0.85),
        "jest": ("JavaScript", 0.80),
        "mocha": ("JavaScript", 0.80),
    }

    DATABASES = {
        "postgresql": 0.95,
        "mysql": 0.95,
        "mongodb": 0.95,
        "redis": 0.90,
        "elasticsearch": 0.90,
        "dynamodb": 0.90,
        "firebase": 0.85,
        "cassandra": 0.85,
        "oracle": 0.85,
    }

    TOOLS = {
        "docker": 0.95,
        "kubernetes": 0.95,
        "git": 0.90,
        "github": 0.90,
        "gitlab": 0.90,
        "aws": 0.90,
        "gcp": 0.90,
        "azure": 0.90,
        "ci/cd": 0.85,
        "jenkins": 0.85,
        "terraform": 0.85,
        "ansible": 0.85,
    }

    # Dockerfile instructions, matched uppercase at the start of a line so
    # Python's lowercase `from ... import` and prose do not collide.
    DOCKERFILE_INSTRUCTION_RE = re.compile(
        r"^\s*(FROM|RUN|CMD|COPY|ADD|EXPOSE|ENV|ENTRYPOINT|WORKDIR|VOLUME"
        r"|LABEL|ARG|USER|HEALTHCHECK|ONBUILD|STOPSIGNAL|SHELL|MAINTAINER)\b",
        re.MULTILINE,
    )
    # Every Dockerfile begins with a `FROM <image>` instruction.
    DOCKERFILE_FROM_RE = re.compile(r"^\s*FROM\s+\S+", re.MULTILINE)
    # docker-compose: a top-level `services:` mapping...
    COMPOSE_SERVICES_RE = re.compile(r"^\s*services:\s*(?:#.*)?$", re.MULTILINE)
    # ...plus at least one service-level key beneath it.
    COMPOSE_SERVICE_KEY_RE = re.compile(
        r"^\s*(build|image|ports|volumes|container_name|depends_on|networks"
        r"|environment|command|expose|restart):",
        re.MULTILINE,
    )

    def extract_skills(self, text: str, filename: str | None = None) -> list[SkillDetection]:
        """
        Extract skills from source code or documentation text.

        Args:
            text: The source text to analyze
            filename: Optional filename for extension-based detection

        Returns:
            List of detected skills with confidence scores
        """
        detected_skills: dict[str, SkillDetection] = {}

        # Detect languages first
        self._detect_languages(text, filename, detected_skills)

        # Detect frameworks and libraries
        self._detect_frameworks(text, detected_skills)

        # Detect React specifically
        self._detect_react(text, detected_skills)

        # Detect databases
        self._detect_databases(text, detected_skills)

        # Detect tools
        self._detect_tools(text, detected_skills)

        # Sort by confidence
        return sorted(
            detected_skills.values(),
            key=lambda x: x.confidence,
            reverse=True,
        )

    def _detect_languages(
        self,
        text: str,
        filename: str | None,
        skills_dict: dict,
    ) -> None:
        """Detect programming languages."""
        text_lower = text.lower()

        # Python detection
        python_evidence = []
        if ".py" in str(filename or "").lower():
            python_evidence.append("Python file extension (.py)")
        if re.search(r"\bimport\s+\w+", text):
            python_evidence.append("Python import statements")
        if re.search(r"\bdef\s+\w+\s*\(", text):
            python_evidence.append("Python function definitions")
        if re.search(r":\s*(int|str|float|bool|list|dict)", text):
            python_evidence.append("Python type annotations")
        if "requirements.txt" in text_lower:
            python_evidence.append("requirements.txt found")

        if python_evidence:
            skills_dict["Python"] = SkillDetection(
                name="Python",
                category="Language",
                confidence=min(0.95, 0.6 + len(python_evidence) * 0.1),
                evidence=python_evidence,
            )

        # JavaScript/TypeScript detection
        js_evidence = []
        if ".js" in str(filename or "").lower():
            js_evidence.append("JavaScript file extension (.js)")
        if ".ts" in str(filename or "").lower():
            js_evidence.append("TypeScript file extension (.ts)")
        matched_keywords = [
            keyword
            for keyword, pattern in self.JS_TS_KEYWORD_PATTERNS.items()
            if re.search(pattern, text)
        ]
        if matched_keywords:
            js_evidence.append("JS/TS keywords (" + ", ".join(sorted(matched_keywords)) + ")")
        if re.search(self.JS_ARROW_PATTERN, text):
            js_evidence.append("Arrow function syntax")

        ts_syntax = any(re.search(pattern, text) for pattern in self.TS_SYNTAX_PATTERNS)
        if ts_syntax:
            js_evidence.append("TypeScript-specific syntax")

        if "package.json" in text_lower:
            js_evidence.append("package.json found")

        if js_evidence:
            confidence = min(0.95, 0.6 + len(js_evidence) * 0.1)
            is_typescript = ".ts" in str(filename or "").lower() or ts_syntax
            lang = "TypeScript" if is_typescript else "JavaScript"
            skills_dict[lang] = SkillDetection(
                name=lang,
                category="Language",
                confidence=confidence,
                evidence=js_evidence,
            )

        # Other languages by extension
        extension_langs = {
            ".java": ("Java", 0.95),
            ".cpp": ("C++", 0.95),
            ".cs": ("C#", 0.95),
            ".go": ("Go", 0.95),
            ".rs": ("Rust", 0.95),
            ".rb": ("Ruby", 0.95),
            ".php": ("PHP", 0.95),
            ".swift": ("Swift", 0.95),
        }

        filename_lower = str(filename or "").lower()
        for ext, (lang, confidence) in extension_langs.items():
            if ext in filename_lower:
                skills_dict[lang] = SkillDetection(
                    name=lang,
                    category="Language",
                    confidence=confidence,
                    evidence=[f"{lang} file extension"],
                )

    def _detect_frameworks(self, text: str, skills_dict: dict) -> None:
        """Detect frameworks and libraries."""
        text_lower = text.lower()

        for framework, (category, confidence) in self.FRAMEWORKS.items():
            if framework in text_lower:
                display_name = framework.title()
                if display_name not in skills_dict:
                    skills_dict[display_name] = SkillDetection(
                        name=display_name,
                        category=category,
                        confidence=confidence,
                        evidence=[f"Found '{framework}' in content"],
                    )

    def _detect_react(self, text: str, skills_dict: dict) -> None:
        """Detect React specifically."""
        text_lower = text.lower()
        react_evidence = []

        for indicator in self.REACT_INDICATORS:
            if indicator.lower() in text_lower:
                react_evidence.append(indicator)

        if react_evidence:
            skills_dict["React"] = SkillDetection(
                name="React",
                category="Framework",
                confidence=min(0.99, 0.7 + len(react_evidence) * 0.05),
                evidence=react_evidence,
            )

    def _detect_databases(self, text: str, skills_dict: dict) -> None:
        """Detect databases."""
        text_lower = text.lower()

        for db, confidence in self.DATABASES.items():
            if db in text_lower:
                display_name = db.upper() if db in ["sql", "nosql"] else db.title()
                if display_name not in skills_dict:
                    skills_dict[display_name] = SkillDetection(
                        name=display_name,
                        category="Database",
                        confidence=confidence,
                        evidence=[f"Found '{db}' reference in content"],
                    )

    def _detect_tools(self, text: str, skills_dict: dict) -> None:
        """Detect tools and DevOps technologies."""
        text_lower = text.lower()

        # Structural Docker detection (Dockerfile / compose) runs first so its
        # richer evidence is not overwritten by the plain keyword scan below.
        self._detect_docker(text, skills_dict)

        for tool, confidence in self.TOOLS.items():
            if tool in text_lower:
                display_name = tool.upper() if tool in ["ci/cd"] else tool.title()
                if display_name not in skills_dict:
                    skills_dict[display_name] = SkillDetection(
                        name=display_name,
                        category="Tool",
                        confidence=confidence,
                        evidence=[f"Found '{tool}' reference in content"],
                    )

    def _detect_docker(self, text: str, skills_dict: dict) -> None:
        """Detect Docker and Docker Compose from Dockerfile / compose syntax.

        Recognises Dockerfiles even when the literal word "docker" is absent
        (a `FROM` instruction plus at least one other instruction), and
        docker-compose files (a top-level ``services:`` mapping plus a
        service-level key such as ``build:`` or ``image:``).
        """
        # Dockerfile: a real FROM plus at least two distinct instruction types.
        instructions = self.DOCKERFILE_INSTRUCTION_RE.findall(text)
        if self.DOCKERFILE_FROM_RE.search(text) and len(set(instructions)) >= 2:
            found = ", ".join(sorted(set(instructions)))
            skills_dict.setdefault(
                "Docker",
                SkillDetection(
                    name="Docker",
                    category="Tool",
                    confidence=0.95,
                    evidence=[f"Dockerfile instructions ({found})"],
                ),
            )

        # Docker Compose: top-level services mapping plus a service-level key.
        if self.COMPOSE_SERVICES_RE.search(text) and self.COMPOSE_SERVICE_KEY_RE.search(text):
            skills_dict.setdefault(
                "Docker Compose",
                SkillDetection(
                    name="Docker Compose",
                    category="Tool",
                    confidence=0.95,
                    evidence=["docker-compose services definition"],
                ),
            )
            # A compose file implies Docker itself.
            skills_dict.setdefault(
                "Docker",
                SkillDetection(
                    name="Docker",
                    category="Tool",
                    confidence=0.90,
                    evidence=["docker-compose configuration"],
                ),
            )
