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

    # Syntax that only appears in JavaScript or TypeScript. Any one of these is
    # enough to conclude the text belongs to the JS/TS family. Bare keywords are
    # deliberately not used on their own: JS_TS_KEYWORDS shares "import", "async",
    # "await", and "class" with Python, and words like "let" and "function" occur
    # in ordinary prose, so matching them alone reports JavaScript for Python code.
    JS_SYNTAX_PATTERNS = (
        r"require\s*\(",
        r"\bmodule\.exports\b",
        r"console\.(log|error|warn|info)\s*\(",
        r"=>",
        r"\bfrom\s+['\"]",
        r"\bfunction\s*\w*\s*\(",
        r"\b(const|let|var)\s+[\w${[][^\n]*=",
        r"\bexport\s+(default|const|function|class|interface|type|enum)\b",
    )

    # Signals that JS/TS text is specifically TypeScript. These are checked against
    # the text itself so TypeScript is detected even when no filename is supplied.
    TS_SYNTAX_PATTERNS = (
        r"\binterface\s+\w+\s*\{",
        r"\btype\s+\w+\s*=",
        r"\benum\s+\w+\s*\{",
        r":\s*(string|number|boolean|any|void|unknown|never)\b",
        r"\bPromise\s*<",
    )

    # Dockerfile instructions, matched case-sensitively at the start of a line so
    # ordinary prose ("graduated from", "run a script") is not mistaken for one.
    DOCKERFILE_INSTRUCTIONS = (
        "ADD",
        "ARG",
        "CMD",
        "COPY",
        "ENTRYPOINT",
        "ENV",
        "EXPOSE",
        "FROM",
        "HEALTHCHECK",
        "LABEL",
        "RUN",
        "VOLUME",
        "WORKDIR",
    )

    # Keys that identify a Docker Compose file when paired with "services:".
    COMPOSE_KEYS = (
        "image:",
        "build:",
        "ports:",
        "volumes:",
        "depends_on:",
        "environment:",
    )

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

        # Detect Docker from Dockerfile or Compose structure
        self._detect_docker(text, detected_skills)

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
        skills_dict: dict[str, SkillDetection],
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
        if re.search(r":\s*(int|str|float|bool|list|dict)\b", text):
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
        self._detect_js_ts(text, filename, skills_dict)

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

    def _detect_js_ts(
        self,
        text: str,
        filename: str | None,
        skills_dict: dict[str, SkillDetection],
    ) -> None:
        """
        Detect JavaScript and TypeScript from the text content itself.

        JavaScript is reported when the text contains syntax that Python does not
        share (for example ``require('fs')`` or an arrow function). TypeScript is
        reported when the text shows type-level syntax, references a ``.ts``/``.tsx``
        file, or names the language, so TypeScript is detected even when no filename
        is supplied. Both may be reported for the same text, since TypeScript
        projects normally contain JavaScript too.

        Args:
            text: The source text to analyze
            filename: Optional filename used as an additional extension signal
            skills_dict: Accumulated detections, mutated in place
        """
        filename_lower = str(filename or "").lower()
        text_lower = text.lower()

        js_evidence = []
        ts_evidence = []

        if filename_lower.endswith((".js", ".jsx", ".mjs", ".cjs")):
            js_evidence.append("JavaScript file extension")
        if re.search(r"\b[\w-]+\.(js|jsx|mjs|cjs)\b", text_lower):
            js_evidence.append("JavaScript file reference in content")
        if "package.json" in text_lower:
            js_evidence.append("package.json found")

        for pattern in self.JS_SYNTAX_PATTERNS:
            if re.search(pattern, text):
                js_evidence.append("JavaScript or TypeScript syntax found")
                break

        # JS_TS_KEYWORDS enriches the evidence list once the family is established,
        # but never decides detection on its own (see the note on the constant).
        if js_evidence:
            keywords_found = sorted(
                keyword for keyword in self.JS_TS_KEYWORDS if re.search(rf"\b{keyword}\b", text)
            )
            if keywords_found:
                js_evidence.append(f"Keywords found: {', '.join(keywords_found)}")

        if filename_lower.endswith((".ts", ".tsx")):
            ts_evidence.append("TypeScript file extension")
        if re.search(r"\b[\w-]+\.(ts|tsx)\b", text_lower):
            ts_evidence.append("TypeScript file reference in content")
        if "typescript" in text_lower:
            ts_evidence.append("TypeScript named in content")

        for pattern in self.TS_SYNTAX_PATTERNS:
            if re.search(pattern, text):
                ts_evidence.append("TypeScript type syntax found")
                break

        if js_evidence:
            skills_dict["JavaScript"] = SkillDetection(
                name="JavaScript",
                category="Language",
                confidence=min(0.95, 0.6 + len(js_evidence) * 0.1),
                evidence=js_evidence,
            )

        if ts_evidence:
            skills_dict["TypeScript"] = SkillDetection(
                name="TypeScript",
                category="Language",
                confidence=min(0.95, 0.6 + len(ts_evidence) * 0.1),
                evidence=ts_evidence,
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

    def _detect_docker(self, text: str, skills_dict: dict[str, SkillDetection]) -> None:
        """
        Detect Docker from file structure rather than the literal word "docker".

        A Dockerfile or a Compose file often never mentions Docker by name, so this
        looks for Dockerfile instructions at the start of a line and for Compose
        service definitions. Two or more distinct instructions are required so that
        an isolated capitalised word in prose is not treated as a Dockerfile.

        Args:
            text: The source text to analyze
            skills_dict: Accumulated detections, mutated in place
        """
        if "Docker" in skills_dict:
            return

        evidence = []

        instruction_pattern = r"^\s*({})\s+\S".format("|".join(self.DOCKERFILE_INSTRUCTIONS))
        instructions = {
            match.group(1) for match in re.finditer(instruction_pattern, text, re.MULTILINE)
        }
        if len(instructions) >= 2:
            evidence.append(f"Dockerfile instructions: {', '.join(sorted(instructions))}")

        has_services = re.search(r"^\s*services\s*:", text, re.MULTILINE) is not None
        has_service_key = any(
            re.search(rf"^\s*{re.escape(key)}", text, re.MULTILINE) for key in self.COMPOSE_KEYS
        )
        if has_services and has_service_key:
            evidence.append("Docker Compose service definitions found")

        if evidence:
            skills_dict["Docker"] = SkillDetection(
                name="Docker",
                category="Tool",
                confidence=self.TOOLS["docker"],
                evidence=evidence,
            )

    def _detect_tools(self, text: str, skills_dict: dict) -> None:
        """Detect tools and DevOps technologies."""
        text_lower = text.lower()

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
