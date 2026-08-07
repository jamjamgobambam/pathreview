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
        js_evidence = []
        has_js = ".js" in str(filename or "").lower()
        has_ts = ".ts" in str(filename or "").lower()
        if has_js:
            js_evidence.append("JavaScript file extension (.js)")
        if has_ts:
            js_evidence.append("TypeScript file extension (.ts)")

        # Scan the text body for in-text file extension mentions
        # (e.g. "index.js", "app.tsx"). Requires a word character before the
        # dot so plain words ending in ".js" (e.g. "ASAP.js") are less likely
        # to false-match, and a trailing word boundary so ".js" does not
        # swallow ".jsx".
        intext_exts = {m.group(1).lower() for m in re.finditer(r"\w+\.(js|jsx|ts|tsx)\b", text)}
        js_intext = {ext for ext in intext_exts if ext in ("js", "jsx")}
        ts_intext = {ext for ext in intext_exts if ext in ("ts", "tsx")}
        if js_intext:
            has_js = True
            js_evidence.append(
                "JavaScript file extension in text ("
                + ", ".join(sorted("." + e for e in js_intext))
                + ")"
            )
        if ts_intext:
            has_ts = True
            js_evidence.append(
                "TypeScript file extension in text ("
                + ", ".join(sorted("." + e for e in ts_intext))
                + ")"
            )

        # Language name mentioned literally in the text (case-insensitive).
        if "javascript" in text_lower:
            has_js = True
            js_evidence.append("'JavaScript' mentioned in text")
        if "typescript" in text_lower:
            has_ts = True
            js_evidence.append("'TypeScript' mentioned in text")

        # JS/ES6/CommonJS imports only. A bare `import <name>` also matches
        # Python, so require JS-specific forms: `require(`, `import ... from`,
        # `import {`, or a side-effect `import '...'`.
        if re.search(
            r"\brequire\s*\(|\bimport\b[^\n]*\bfrom\b|\bimport\s*\{|\bimport\s*['\"]",
            text,
        ):
            js_evidence.append("CommonJS or ES6 imports")
        if "package.json" in text_lower:
            js_evidence.append("package.json found")

        # JS-specific keyword detection. Exclude keywords that also appear in
        # Python (import, async, await, class) to avoid false positives on
        # Python code. Require >= 2 unique JS-only keywords before treating
        # keyword evidence as a JS/TS signal.
        js_only_keywords = self.JS_TS_KEYWORDS - self.PYTHON_KEYWORDS
        found_js_keywords = {
            kw for kw in js_only_keywords if re.search(rf"\b{re.escape(kw)}\b", text)
        }
        if len(found_js_keywords) >= 2:
            js_evidence.append("JavaScript keywords (" + ", ".join(sorted(found_js_keywords)) + ")")

        # TypeScript-specific syntax. These constructs (interface/type/enum
        # declarations and typed annotations like ": string") do not appear in
        # plain JavaScript or Python, so they are strong TypeScript signals.
        ts_signals = []
        if re.search(r"\binterface\s+\w+", text):
            ts_signals.append("interface declaration")
        if re.search(r"\btype\s+\w+\s*=", text):
            ts_signals.append("type alias")
        if re.search(r"\benum\s+\w+", text):
            ts_signals.append("enum declaration")
        if re.search(r":\s*(string|number|boolean)\b", text):
            ts_signals.append("TypeScript type annotations")
        if ts_signals:
            has_ts = True
            js_evidence.append("TypeScript syntax (" + ", ".join(ts_signals) + ")")

        if js_evidence:
            confidence = min(0.95, 0.6 + len(js_evidence) * 0.1)
            lang = "TypeScript" if has_ts else "JavaScript"
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

        # Docker detection from file contents that never mention "docker".
        # Dockerfile instructions and docker-compose keys are matched at the
        # start of a line (case-insensitive, ignoring leading indentation).
        docker_evidence = []
        if re.search(
            r"(?im)^\s*(FROM|RUN|CMD|EXPOSE|ENTRYPOINT|COPY|WORKDIR)\s+",
            text,
        ):
            docker_evidence.append("Dockerfile instructions")
        if re.search(
            r"(?im)^\s*(version|services|build|ports|image)\s*:",
            text,
        ):
            docker_evidence.append("docker-compose keys")

        if docker_evidence and "Docker" not in skills_dict:
            skills_dict["Docker"] = SkillDetection(
                name="Docker",
                category="Tool",
                confidence=0.85,
                evidence=docker_evidence,
            )
