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

    # This function extracts skills from text while allowing callers to omit the filename.
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

    # this function detects programming languages in the provided text.
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
        # Match Python-shaped imports without treating ES module imports with
        # braces or quoted module paths as Python evidence.
        if re.search(
            r"(?m)^\s*(?:import\s+[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*(?:\s+as\s+[A-Za-z_]\w*)?"
            r"|from\s+[A-Za-z_][\w.]*\s+import\s+[A-Za-z_*]\w*)\s*$",
            text,
        ):
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

        # JavaScript and TypeScript detection
        #  Collect JS and TS evidence separately so shared syntax does not make a
        # TypeScript source appear as both TypeScript and JavaScript.
        filename_lower = str(filename or "").lower()
        js_evidence = []
        ts_evidence = []
        js_decisive = False
        ts_decisive = False

        if re.search(r"\.jsx?$", filename_lower):
            js_evidence.append("JavaScript file extension (.js or .jsx)")
            js_decisive = True
        if re.search(r"\.tsx?$", filename_lower):
            ts_evidence.append("TypeScript file extension (.ts or .tsx)")
            ts_decisive = True

        # Boundary checks prevent extensions in strings such as "adjust" from
        # being mistaken for source filenames mentioned in documentation.
        if re.search(r"(?<![\w.])[\w./\\-]+\.jsx?(?![\w.])", text, re.IGNORECASE):
            js_evidence.append("JavaScript filename referenced in content")
            js_decisive = True
        if re.search(r"(?<![\w.])[\w./\\-]+\.tsx?(?![\w.])", text, re.IGNORECASE):
            ts_evidence.append("TypeScript filename referenced in content")
            ts_decisive = True

        if re.search(r"\b(?:javascript|ecmascript)\b", text, re.IGNORECASE):
            js_evidence.append("JavaScript language name found")
            js_decisive = True
        if re.search(r"\btypescript\b", text, re.IGNORECASE):
            ts_evidence.append("TypeScript language name found")
            ts_decisive = True

        # Syntax-only matches require corroboration below; this avoids treating
        # a lone shared keyword such as import, class, or async as JavaScript.
        if re.search(r"\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=", text):
            js_evidence.append("JavaScript variable declaration")
        if re.search(r"(?:\([^\n)]*\)|[A-Za-z_$][\w$]*)\s*=>", text):
            js_evidence.append("JavaScript arrow function")
        if re.search(r"\brequire\s*\(", text):
            js_evidence.append("CommonJS require call")
        if "package.json" in text_lower:
            js_evidence.append("package.json found")

        if re.search(r"\b(?:export\s+)?interface\s+[A-Za-z_$][\w$]*", text):
            ts_evidence.append("TypeScript interface declaration")
        if re.search(r"\btype\s+[A-Za-z_$][\w$]*(?:<[^>]+>)?\s*=", text):
            ts_evidence.append("TypeScript type alias")
        if re.search(r"\benum\s+[A-Za-z_$][\w$]*", text):
            ts_evidence.append("TypeScript enum declaration")
        if re.search(
            r"\b[A-Za-z_$][\w$]*\s*:\s*(?:string|number|boolean|unknown|never|any)(?:\[\])?\b",
            text,
        ):
            ts_evidence.append("TypeScript type annotation")

        # One decisive signal or two independent syntax signals are required.
        # TypeScript takes precedence because JavaScript syntax is valid in TS.
        if ts_decisive or len(ts_evidence) >= 2:
            skills_dict["TypeScript"] = SkillDetection(
                name="TypeScript",
                category="Language",
                confidence=min(0.95, 0.65 + len(ts_evidence) * 0.1),
                evidence=ts_evidence,
            )
        elif js_decisive or len(js_evidence) >= 2:
            skills_dict["JavaScript"] = SkillDetection(
                name="JavaScript",
                category="Language",
                confidence=min(0.95, 0.65 + len(js_evidence) * 0.1),
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

    # Detect Docker syntax in addition to explicit DevOps technology names.
    def _detect_tools(self, text: str, skills_dict: dict) -> None:
        """Detect tools and DevOps technologies."""
        text_lower = text.lower()

        # Dockerfiles are recognizable from multiple line-oriented instructions,
        # even when the literal word "docker" never appears in the file.
        dockerfile_instructions = re.findall(
            r"(?im)^\s*(from|run|cmd|entrypoint|copy|add|workdir|expose|arg|env|user|volume)\b",
            text,
        )
        docker_evidence = []
        if len(set(instruction.lower() for instruction in dockerfile_instructions)) >= 2:
            docker_evidence.append("Dockerfile instruction pattern")

        # Compose detection needs a services block plus two supporting keys;
        # requiring combined structure avoids false positives from generic YAML.
        has_services = bool(re.search(r"(?im)^\s*services\s*:\s*(?:#.*)?$", text))
        compose_keys = {
            match.lower()
            for match in re.findall(
                r"(?im)^\s+(build|image|ports|volumes|networks|depends_on|environment)\s*:",
                text,
            )
        }
        has_compose_version = bool(
            re.search(r"(?im)^\s*version\s*:\s*['\"]?\d+(?:\.\d+)?['\"]?\s*$", text)
        )
        if has_services and (len(compose_keys) >= 2 or (compose_keys and has_compose_version)):
            docker_evidence.append("Docker Compose services and configuration keys")

        if docker_evidence and "docker" not in text_lower:
            skills_dict["Docker"] = SkillDetection(
                name="Docker",
                category="Tool",
                confidence=min(0.95, 0.85 + len(docker_evidence) * 0.05),
                evidence=docker_evidence,
            )

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
