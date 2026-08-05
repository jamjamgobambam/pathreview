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

    # Content signals for JavaScript, as (pattern, evidence) pairs. These are
    # matched against the raw text so a snippet is recognised even when no
    # filename is available. Patterns are deliberately anchored (word
    # boundaries, a required operator or paren) to keep prose from matching.
    JS_SIGNALS = (
        (r"\brequire\s*\(", "CommonJS require() call"),
        (r"\bimport\b[^;\n]*\bfrom\s*['\"]", "ES6 import statement"),
        (
            r"\bexport\s+(default|const|let|var|function|class|interface|type|enum|\{)",
            "ES6 export statement",
        ),
        (r"\b(const|let)\s+\w+\s*=", "const/let declaration"),
        (r"(\w|\))\s*=>", "Arrow function"),
        (r"\bfunction\s*\w*\s*\(", "function declaration"),
        (r"\bconsole\.(log|error|warn|info)\s*\(", "console logging"),
    )

    # Signals that only appear in TypeScript, never in plain JavaScript.
    # Structural patterns require their opening brace or `=` so that Python's
    # `from enum import Enum` and similar prose do not match.
    TS_SIGNALS = (
        (r"\binterface\s+\w+\s*(\{|extends\b)", "TypeScript interface declaration"),
        (r"\btype\s+\w+\s*=", "TypeScript type alias"),
        (r"\benum\s+\w+\s*\{", "TypeScript enum declaration"),
        (r":\s*(string|number|boolean|any|unknown|never|void)\b", "TypeScript type annotation"),
        (r":\s*Promise\s*<", "TypeScript Promise return type"),
        (r"\bas\s+(string|number|boolean|const)\b", "TypeScript type assertion"),
    )

    # Dockerfile instructions other than FROM. Matched case-sensitively at the
    # start of a line, and only trusted in pairs, so prose is not misread.
    DOCKERFILE_DIRECTIVES = (
        "RUN",
        "CMD",
        "EXPOSE",
        "ENTRYPOINT",
        "COPY",
        "ADD",
        "WORKDIR",
        "ENV",
        "VOLUME",
        "ARG",
        "LABEL",
        "USER",
    )

    # Keys that identify a docker-compose service block.
    COMPOSE_SERVICE_KEYS = (
        "image",
        "build",
        "ports",
        "volumes",
        "networks",
        "depends_on",
        "container_name",
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
        #
        # Detection is content-driven so that a raw snippet with no filename is
        # still recognised. TypeScript is a superset of JavaScript, so any
        # TypeScript signal wins and the text is reported once, as TypeScript,
        # with the JavaScript evidence folded in.
        filename_lower = str(filename or "").lower()

        js_evidence = []
        if filename_lower.endswith((".js", ".jsx", ".mjs", ".cjs")):
            js_evidence.append("JavaScript file extension")
        if filename_lower.endswith("package.json") or "package.json" in text_lower:
            js_evidence.append("package.json found")
        js_evidence.extend(self._match_signals(text, self.JS_SIGNALS))

        ts_evidence = []
        if filename_lower.endswith((".ts", ".tsx", ".mts", ".cts")):
            ts_evidence.append("TypeScript file extension")
        ts_evidence.extend(self._match_signals(text, self.TS_SIGNALS))

        if ts_evidence:
            combined_evidence = ts_evidence + js_evidence
            skills_dict["TypeScript"] = SkillDetection(
                name="TypeScript",
                category="Language",
                confidence=min(0.95, 0.6 + len(combined_evidence) * 0.1),
                evidence=combined_evidence,
            )
        elif js_evidence:
            skills_dict["JavaScript"] = SkillDetection(
                name="JavaScript",
                category="Language",
                confidence=min(0.95, 0.6 + len(js_evidence) * 0.1),
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

        for ext, (lang, confidence) in extension_langs.items():
            if ext in filename_lower:
                skills_dict[lang] = SkillDetection(
                    name=lang,
                    category="Language",
                    confidence=confidence,
                    evidence=[f"{lang} file extension"],
                )

    @staticmethod
    def _match_signals(text: str, signals: tuple[tuple[str, str], ...]) -> list[str]:
        """Collect the evidence for every signal whose pattern matches the text.

        Args:
            text: The source text to search.
            signals: Pairs of (regular expression, human-readable evidence).

        Returns:
            The evidence string for each signal that matched, in declaration order.
        """
        return [evidence for pattern, evidence in signals if re.search(pattern, text)]

    def _detect_docker_content(self, text: str) -> list[str]:
        """Detect Docker from Dockerfile or Compose structure rather than by name.

        Dockerfiles and docker-compose files almost never contain the literal
        string "docker", so they are recognised from their directives instead.

        Args:
            text: The source text to analyse.

        Returns:
            Evidence strings describing what matched, or an empty list if the
            text does not look like a Dockerfile or a Compose file.
        """
        evidence = []

        # FROM is the mandatory first instruction of every Dockerfile, so an
        # uppercase line-leading FROM stands on its own. Other directives are
        # ambiguous individually, so at least two must co-occur.
        if re.search(r"^[ \t]*FROM[ \t]+\S+", text, re.MULTILINE):
            evidence.append("Dockerfile FROM instruction")

        matched = [
            directive
            for directive in self.DOCKERFILE_DIRECTIVES
            if re.search(rf"^[ \t]*{directive}[ \t]+\S", text, re.MULTILINE)
        ]
        if len(matched) >= 2:
            evidence.append(f"Dockerfile directives ({', '.join(matched)})")

        # A compose file needs a services block plus at least one service key.
        if re.search(r"^[ \t]*services:", text, re.MULTILINE):
            keys = "|".join(self.COMPOSE_SERVICE_KEYS)
            if re.search(rf"^[ \t]*({keys}):", text, re.MULTILINE):
                evidence.append("docker-compose services definition")

        return evidence

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

        # The loop above is a substring match on the tool name, which misses
        # Dockerfiles and compose files because they do not spell out "docker".
        docker_evidence = self._detect_docker_content(text)
        if docker_evidence:
            existing = skills_dict.get("Docker")
            if existing is None:
                skills_dict["Docker"] = SkillDetection(
                    name="Docker",
                    category="Tool",
                    confidence=self.TOOLS["docker"],
                    evidence=docker_evidence,
                )
            else:
                existing.evidence.extend(docker_evidence)
