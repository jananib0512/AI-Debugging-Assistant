import ast
import json
import re
import uuid
import configparser
from pathlib import Path
from datetime import datetime, timezone

from app.detection.detector import EXTENSION_LANGUAGE_MAP

IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    ".env", "dist", "build", ".next", "target", "vendor",
    "bower_components", ".svn", "coverage", ".tox", "eggs",
}

SUPPORTED_LANGUAGES = {"Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "PHP", "Ruby"}

LANG_FILE_PATTERNS: dict[str, list[str]] = {
    "Python": ["*.py"],
    "JavaScript": ["*.js", "*.jsx", "*.mjs"],
    "TypeScript": ["*.ts", "*.tsx"],
    "Java": ["*.java"],
    "C#": ["*.cs"],
    "C++": ["*.cpp", "*.cxx", "*.cc", "*.hpp", "*.hxx"],
    "Go": ["*.go"],
    "PHP": ["*.php"],
    "Ruby": ["*.rb"],
}


class SyntaxDetectionEngine:

    def analyze(self, workspace_path: Path | None = None) -> dict:
        if not workspace_path or not workspace_path.exists():
            return {
                "session_id": uuid.uuid4().hex,
                "status": "unavailable",
                "total_errors": 0,
                "total_files_scanned": 0,
                "files_with_errors": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "results": [],
                "scanned_languages": [],
            }

        language_map = self._detect_languages(workspace_path)
        scanned_languages = list(language_map.keys())
        all_results: list[dict] = []
        total_errors = 0
        files_with_errors = 0
        critical = 0
        high = 0
        medium = 0
        low = 0

        for lang, pattern_list in language_map.items():
            for pattern in pattern_list:
                for file_path in workspace_path.rglob(pattern):
                    if self._is_ignored(file_path):
                        continue
                    result = self._analyze_file(file_path, lang, workspace_path)
                    all_results.append(result)
                    file_error_count = result["error_count"]
                    if file_error_count > 0:
                        files_with_errors += 1
                    total_errors += file_error_count
                    for e in result["errors"]:
                        s = e["severity"]
                        if s == "Critical":
                            critical += 1
                        elif s == "High":
                            high += 1
                        elif s == "Medium":
                            medium += 1
                        else:
                            low += 1

        return {
            "session_id": uuid.uuid4().hex,
            "status": "completed",
            "total_errors": total_errors,
            "total_files_scanned": len(all_results),
            "files_with_errors": files_with_errors,
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "results": all_results,
            "scanned_languages": scanned_languages,
        }

    def _detect_languages(self, workspace_path: Path) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        for ext, lang in EXTENSION_LANGUAGE_MAP.items():
            if lang not in SUPPORTED_LANGUAGES:
                continue
            pattern = f"*{ext}"
            matches = list(workspace_path.rglob(pattern))
            matches = [m for m in matches if not self._is_ignored(m)]
            if matches:
                if lang not in found:
                    found[lang] = []
                found[lang].append(pattern)
        for lang, patterns in LANG_FILE_PATTERNS.items():
            if lang not in found:
                for pattern in patterns:
                    matches = list(workspace_path.rglob(pattern))
                    matches = [m for m in matches if not self._is_ignored(m)]
                    if matches:
                        if lang not in found:
                            found[lang] = []
                        found[lang].append(pattern)
                        break
        return found

    def _is_ignored(self, path: Path) -> bool:
        for part in path.parts:
            if part in IGNORED_DIRS:
                return True
        return False

    def _analyze_file(self, file_path: Path, language: str, workspace: Path) -> dict:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {
                "file_path": str(file_path.relative_to(workspace)),
                "language": language,
                "errors": [self._make_error(
                    bug_title="Unreadable File",
                    description=f"Cannot read file: {file_path.name}. The file may be binary or corrupted.",
                    severity="High", confidence=95, language=language,
                    file_path=str(file_path.relative_to(workspace)),
                    line=1, col=1, snippet="",
                    explanation="The file could not be read as text. It may be a binary file or contain invalid encoding.",
                    fix="Ensure the file is a valid text file with UTF-8 encoding.",
                    error_type="io",
                )],
                "error_count": 1,
                "health_score": 0.0,
            }

        errors: list[dict] = []

        if language == "Python":
            errors = self._check_python(file_path, content, language, workspace)
        elif language in ("JavaScript", "TypeScript"):
            errors = self._check_js_ts(file_path, content, language)
        elif language in ("Java", "C#", "C++", "Go"):
            errors = self._check_brace_language(file_path, content, language)
        elif language == "PHP":
            errors = self._check_php(file_path, content)
        elif language == "Ruby":
            errors = self._check_ruby(file_path, content)

        errors += self._check_common(file_path, content, language, workspace)
        errors = self._deduplicate(errors)
        error_count = len(errors)
        health_score = max(0, 100 - (error_count * 5))
        return {
            "file_path": str(file_path.relative_to(workspace)),
            "language": language,
            "errors": errors,
            "error_count": error_count,
            "health_score": min(100, health_score),
        }

    def _check_python(self, file_path: Path, content: str, language: str, workspace: Path) -> list[dict]:
        errors: list[dict] = []
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            line = e.lineno or 1
            col = e.offset or 1
            msg = str(e)
            snippet = self._get_snippet(content, line)
            errors.append(self._make_error(
                bug_title="Python Syntax Error",
                description=f"Python parser detected a syntax error: {msg}",
                severity="Critical", confidence=98, language=language,
                file_path=str(file_path.relative_to(workspace)),
                line=line, col=col, snippet=snippet,
                explanation=f"The Python interpreter could not parse this file due to a syntax error at line {line}, column {col}. Error: {msg}",
                fix="Review the indicated line and fix the syntax. Common issues include missing colons, mismatched parentheses, or invalid indentation.",
                error_type="syntax",
            ))
            return errors

        lines = content.split("\n")
        for i, node in enumerate(ast.walk(tree)):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._check_python_import(node, content, file_path, language, workspace, errors)

        self._check_indentation(lines, file_path, language, errors)

        return errors

    def _check_python_import(self, node: ast.AST, content: str, file_path: Path, language: str, workspace: Path, errors: list[dict]) -> None:
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                self._try_resolve_import(parts[0], file_path, workspace, alias.lineno or 1, language, errors)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                parts = node.module.split(".")
                self._try_resolve_import(parts[0], file_path, workspace, node.lineno or 1, language, errors)

    def _try_resolve_import(self, module_name: str, file_path: Path, workspace: Path, line: int, language: str, errors: list[dict]) -> None:
        if module_name in ("os", "sys", "re", "json", "math", "datetime", "collections", "typing",
                          "pathlib", "functools", "itertools", "random", "uuid", "hashlib",
                          "copy", "enum", "string", "abc", "io", "base64", "datetime", "decimal",
                          "inspect", "logging", "socket", "subprocess", "tempfile", "threading",
                          "time", "traceback", "types", "warnings", "weakref", "builtins",
                          "__future__", "unittest", "pytest", "numpy", "pandas", "requests",
                          "flask", "django", "fastapi", "sqlalchemy", "pydantic", "click",
                          "jinja2", "werkzeug", "starlette", "uvicorn", "gunicorn"):
            return
        if not (workspace / "venv").exists() and not (workspace / ".venv").exists():
            if module_name.startswith("_"):
                return
            local_match = list(workspace.rglob(f"{module_name}.py")) + list(workspace.rglob(f"{module_name}/__init__.py"))
            if not local_match and module_name not in ("typing", "abc", "enum"):
                errors.append(self._make_error(
                    bug_title="Potential Missing Import",
                    description=f"Import '{module_name}' may be unresolved at line {line}.",
                    severity="Medium", confidence=60, language=language,
                    file_path=str(file_path.relative_to(workspace)),
                    line=line, col=1,
                    snippet=self._get_snippet_for_line(file_path, line),
                    explanation=f"The module '{module_name}' is imported at line {line} but could not be found locally or as a known built-in/third-party package.",
                    fix=f"Ensure '{module_name}' is installed or that the import path is correct.",
                    error_type="import",
                ))

    def _check_indentation(self, lines: list[str], file_path: Path, language: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if not line.strip() or line.strip().startswith("#"):
                continue
            stripped = line.rstrip("\n")
            if stripped != line.rstrip() and line.rstrip() and not line.endswith("\n"):
                continue
            leading = len(line) - len(line.lstrip())
            if leading > 0 and leading % 4 != 0 and leading % 2 != 0:
                snippet = line.strip()[:80]
                errors.append(self._make_error(
                    bug_title="Inconsistent Indentation",
                    description=f"Indent of {leading} spaces at line {i} is not a multiple of 2 or 4.",
                    severity="Medium", confidence=85, language=language,
                    file_path=str(file_path.relative_to(file_path.parent)),
                    line=i, col=1, snippet=snippet,
                    explanation="Python expects consistent indentation (usually 4 spaces per level).",
                    fix="Use consistent indentation: 4 spaces per level.",
                    error_type="indentation",
                ))

    def _check_js_ts(self, file_path: Path, content: str, language: str) -> list[dict]:
        errors: list[dict] = []
        lines = content.split("\n")

        stack: list[tuple[str, int]] = []
        pairs = {"{": "}", "(": ")", "[": "]", "\"": "\"", "'": "'", "`": "`"}
        opening = set(pairs.keys())
        closing = set(pairs.values())

        in_string = False
        string_char = None
        for i, line in enumerate(lines, 1):
            j = 0
            while j < len(line):
                ch = line[j]
                if in_string:
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == string_char:
                        in_string = False
                        string_char = None
                    j += 1
                    continue
                if ch in ("\"", "'", "`"):
                    in_string = True
                    string_char = ch
                    j += 1
                    continue
                if ch in opening and ch in ("{", "(", "["):
                    stack.append((ch, i))
                elif ch in closing:
                    if not stack:
                        errors.append(self._make_js_ts_error(
                            f"Unexpected closing bracket '{ch}'", i, j + 1,
                            f"Found '{ch}' with no matching opening bracket.", language, file_path,
                            self._get_snippet(content, i),
                            "syntax",
                        ))
                    else:
                        expected = pairs[stack[-1][0]]
                        if ch != expected:
                            open_line = stack[-1][1]
                            errors.append(self._make_js_ts_error(
                                f"Mismatched bracket: expected '{expected}' but found '{ch}'",
                                i, j + 1,
                                f"Bracket '{expected}' opened at line {open_line}, but '{ch}' closes at line {i}.",
                                language, file_path, self._get_snippet(content, i), "syntax",
                            ))
                        stack.pop()
                j += 1

        for ch, line_no in stack:
            errors.append(self._make_js_ts_error(
                f"Unclosed bracket '{ch}' opened at line {line_no}",
                line_no, 1,
                f"The bracket '{ch}' opened at line {line_no} is never closed.",
                language, file_path, self._get_snippet(content, line_no), "syntax",
            ))

        self._check_regex_patterns(content, lines, language, file_path, errors)

        return errors

    def _check_regex_patterns(self, content: str, lines: list[str], language: str, file_path: Path, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if language == "JavaScript":
                func_pattern = re.compile(r"(?:function\s+\w+\s*\(|const\s+\w+\s*=\s*(?:async\s*)?\(|let\s+\w+\s*=\s*(?:async\s*)?\()")
                if not func_pattern.search(stripped) and "=>" in stripped:
                    if stripped.count("(") != stripped.count(")") or stripped.count("{") != stripped.count("}"):
                        errors.append(self._make_js_ts_error(
                            "Invalid Arrow Function", i, 1,
                            "Arrow function at this line may have mismatched parentheses or braces.",
                            language, file_path, stripped[:80], "syntax",
                        ))

            if "import" in stripped or "require" in stripped or "#include" in stripped:
                if ";" not in line.rstrip("\n") and not stripped.endswith(";"):
                    errors.append(self._make_js_ts_error(
                        "Missing Semicolon", i, len(stripped),
                        "Import or require statement may be missing a terminating semicolon.",
                        language, file_path, stripped[:80], "syntax",
                    ))

    def _check_brace_language(self, file_path: Path, content: str, language: str) -> list[dict]:
        errors: list[dict] = []
        lines = content.split("\n")
        stack: list[tuple[str, int]] = []
        pairs = {"{": "}", "(": ")", "[": "]"}
        opening = set(pairs.keys())
        closing = set(pairs.values())
        in_string = False
        string_char = None

        for i, line in enumerate(lines, 1):
            j = 0
            while j < len(line):
                ch = line[j]
                if ch in ("\"", "'") and (j == 0 or line[j - 1] != "\\"):
                    if in_string:
                        if ch == string_char:
                            in_string = False
                            string_char = None
                    else:
                        in_string = True
                        string_char = ch
                    j += 1
                    continue
                if in_string:
                    j += 1
                    continue
                if ch in opening:
                    stack.append((ch, i))
                elif ch in closing:
                    if not stack:
                        errors.append(self._make_js_ts_error(
                            f"Unexpected closing bracket '{ch}'", i, j + 1,
                            f"Found '{ch}' with no matching opening bracket.", language, file_path,
                            self._get_snippet(content, i), "syntax",
                        ))
                    else:
                        expected = pairs[stack[-1][0]]
                        if ch != expected:
                            open_line = stack[-1][1]
                            errors.append(self._make_js_ts_error(
                                f"Mismatched bracket: expected '{expected}' found '{ch}'",
                                i, j + 1,
                                f"Bracket '{expected}' at line {open_line}, but '{ch}' at line {i}.",
                                language, file_path, self._get_snippet(content, i), "syntax",
                            ))
                        stack.pop()
                j += 1

        for ch, line_no in stack:
            errors.append(self._make_js_ts_error(
                f"Unclosed bracket '{ch}'", line_no, 1,
                f"The bracket '{ch}' at line {line_no} is never closed.", language, file_path,
                self._get_snippet(content, line_no), "syntax",
            ))

        return errors

    def _check_php(self, file_path: Path, content: str) -> list[dict]:
        errors: list[dict] = []
        if not content.strip().startswith("<?") and not content.strip().startswith("<?php"):
            errors.append(self._make_js_ts_error(
                "Missing PHP Opening Tag", 1, 1,
                "PHP files should start with <?php or <?.",
                "PHP", file_path, content[:50], "syntax",
            ))
        errors += self._check_brace_language(file_path, content, "PHP")
        return errors

    def _check_ruby(self, file_path: Path, content: str) -> list[dict]:
        errors: list[dict] = []
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("=begin"):
                continue
            if stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith("module "):
                if not stripped.endswith(";") and not stripped.endswith("\n") and not stripped.rstrip().endswith("\n"):
                    pass
            if stripped.startswith("if ") or stripped.startswith("unless ") or stripped.startswith("while ") or stripped.startswith("until ") or stripped.startswith("for "):
                if "do" not in stripped and not stripped.endswith("then") and not line.rstrip().endswith(";"):
                    pass
            if "end" not in content:
                errors.append(self._make_js_ts_error(
                    "Missing 'end' Keyword", i, 1,
                    "Ruby blocks must be closed with 'end', but no 'end' was found in this file.",
                    "Ruby", file_path, stripped[:80], "syntax",
                ))
                break
        errors += self._check_brace_language(file_path, content, "Ruby")
        return errors

    def _check_common(self, file_path: Path, content: str, language: str, workspace: Path) -> list[dict]:
        errors: list[dict] = []
        lines = content.split("\n")
        name = file_path.name

        if name in ("package.json", "composer.json", "tsconfig.json", ".prettierrc", ".eslintrc.json",
                    "manifest.json", "bower.json", "component.json"):
            errors += self._check_json(file_path, content, language, workspace)
        elif name.endswith((".yaml", ".yml")) and name not in (".gitignore",):
            errors += self._check_yaml(file_path, content, language, workspace)
        elif name.endswith(".toml"):
            errors += self._check_toml(file_path, content, language, workspace)
        elif name.endswith((".ini", ".cfg")):
            errors += self._check_ini(file_path, content, language, workspace)
        elif name.endswith(".xml"):
            errors += self._check_implicit_xml(file_path, content, language, workspace)

        self._check_missing_quotes(lines, file_path, language, errors)
        self._check_broken_imports(lines, file_path, language, errors)

        return errors

    def _check_json(self, file_path: Path, content: str, language: str, workspace: Path) -> list[dict]:
        errors: list[dict] = []
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            snippet = self._get_snippet(content, e.lineno or 1)
            errors.append(self._make_error(
                bug_title="Broken JSON Configuration",
                description=f"Failed to parse {file_path.name}: {e.msg}",
                severity="High", confidence=98, language=language,
                file_path=str(file_path.relative_to(workspace)),
                line=e.lineno or 1, col=e.colno or 1, snippet=snippet,
                explanation=f"The JSON configuration file '{file_path.name}' contains a syntax error at line {e.lineno}, column {e.colno}: {e.msg}.",
                fix="Fix the JSON syntax by validating with a JSON linter. Common issues include trailing commas, missing quotes, or extra brackets.",
                error_type="config",
            ))
        return errors

    def _check_yaml(self, file_path: Path, content: str, language: str, workspace: Path) -> list[dict]:
        errors: list[dict] = []
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if not line.strip() or line.strip().startswith("#"):
                continue
            if ":" in line:
                key_part = line.split(":", 1)[0]
                if key_part.count("'") % 2 != 0 or key_part.count('"') % 2 != 0:
                    errors.append(self._make_error(
                        bug_title="Broken YAML Configuration",
                        description=f"Possible YAML syntax issue at line {i}.",
                        severity="Medium", confidence=70, language=language,
                        file_path=str(file_path.relative_to(workspace)),
                        line=i, col=1, snippet=line.strip()[:80],
                        explanation=f"YAML file '{file_path.name}' may have a syntax issue at line {i}.",
                        fix="Check YAML indentation and quoting.",
                        error_type="config",
                    ))
                    break
        return errors

    def _check_toml(self, file_path: Path, content: str, language: str, workspace: Path) -> list[dict]:
        errors: list[dict] = []
        import tomllib as toml_parser
        try:
            toml_parser.loads(content)
        except Exception as e:
            errors.append(self._make_error(
                bug_title="Broken TOML Configuration",
                description=f"Failed to parse {file_path.name}: {e}",
                severity="High", confidence=95, language=language,
                file_path=str(file_path.relative_to(workspace)),
                line=1, col=1, snippet="",
                explanation=f"The TOML configuration file '{file_path.name}' could not be parsed.",
                fix="Check the TOML syntax for errors.",
                error_type="config",
            ))
        return errors

    def _check_ini(self, file_path: Path, content: str, language: str, workspace: Path) -> list[dict]:
        errors: list[dict] = []
        try:
            config = configparser.ConfigParser()
            config.read_string(content)
        except configparser.Error as e:
            errors.append(self._make_error(
                bug_title="Broken INI Configuration",
                description=f"Failed to parse {file_path.name}: {e}",
                severity="High", confidence=95, language=language,
                file_path=str(file_path.relative_to(workspace)),
                line=1, col=1, snippet="",
                explanation=f"The INI configuration file '{file_path.name}' could not be parsed.",
                fix="Check the INI file syntax. Ensure sections use [brackets] and key=value pairs.",
                error_type="config",
            ))
        return errors

    def _check_implicit_xml(self, file_path: Path, content: str, language: str, workspace: Path) -> list[dict]:
        errors: list[dict] = []
        if content.strip() and not content.strip().startswith("<"):
            return errors
        open_tags: list[str] = []
        tag_pattern = re.compile(r"<(\/?)(\w+)[^>]*>")
        for match in tag_pattern.finditer(content):
            is_close = match.group(1) == "/"
            tag_name = match.group(2)
            if tag_name.lower() in ("br", "hr", "img", "input", "meta", "link", "!doctype", "?xml"):
                continue
            if not is_close:
                open_tags.append(tag_name)
            else:
                if open_tags and open_tags[-1] == tag_name:
                    open_tags.pop()
                elif open_tags:
                    errors.append(self._make_error(
                        bug_title="Mismatched XML Tag",
                        description=f"Expected closing </{open_tags[-1]}> but found </{tag_name}>.",
                        severity="High", confidence=90, language=language,
                        file_path=str(file_path.relative_to(workspace)),
                        line=1, col=match.start() + 1,
                        snippet=content[max(0, match.start() - 20):match.end() + 20],
                        explanation=f"XML tags are not properly nested: <{open_tags[-1]}> was opened but </{tag_name}> was found.",
                        fix="Ensure XML tags are properly closed in the correct order.",
                        error_type="syntax",
                    ))
                    open_tags.pop()
        for tag in open_tags:
            errors.append(self._make_error(
                bug_title="Unclosed XML Tag",
                description=f"Tag <{tag}> is opened but never closed.",
                severity="Medium", confidence=85, language=language,
                file_path=str(file_path.relative_to(workspace)),
                line=1, col=1, snippet="",
                explanation=f"The XML tag <{tag}> was opened but never properly closed.",
                fix=f"Add a closing </{tag}> tag.",
                error_type="syntax",
            ))
        return errors

    def _check_missing_quotes(self, lines: list[str], file_path: Path, language: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//", "/*", "*", "<!--")):
                continue
            for q in ('"', "'"):
                count = stripped.count(q)
                if count > 0 and count % 2 != 0:
                    snippet = stripped[:80]
                    errors.append(self._make_error(
                        bug_title="Unmatched Quote",
                        description=f"Unmatched {q} at line {i}.",
                        severity="High", confidence=90, language=language,
                        file_path=str(file_path.relative_to(file_path.parent)),
                        line=i, col=stripped.find(q) + 1, snippet=snippet,
                        explanation=f"A {q} character at line {i} does not have a matching closing quote. This will cause a syntax error.",
                        fix=f"Ensure all {q} quotes are properly closed on this line.",
                        error_type="syntax",
                    ))
                    break

    def _check_broken_imports(self, lines: list[str], file_path: Path, language: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "import " in stripped or "from " in stripped:
                if ";" in language in ("Java", "C#", "C++", "Go", "PHP"):
                    if not line.rstrip("\n").rstrip().endswith(";"):
                        errors.append(self._make_error(
                            bug_title="Missing Semicolon",
                            description=f"Import statement at line {i} is missing a semicolon.",
                            severity="Medium", confidence=85, language=language,
                            file_path=str(file_path.relative_to(file_path.parent)),
                            line=i, col=len(stripped), snippet=stripped[:80],
                            explanation="In many languages, import/require/include statements must end with a semicolon.",
                            fix="Add a semicolon at the end of the import statement.",
                            error_type="syntax",
                        ))

    def _make_error(self, **kwargs) -> dict:
        return {
            "bug_title": kwargs["bug_title"],
            "description": kwargs["description"],
            "severity": kwargs["severity"],
            "confidence": kwargs["confidence"],
            "language": kwargs["language"],
            "affected_file": kwargs["file_path"],
            "line_number": kwargs["line"],
            "column_number": kwargs["col"],
            "code_snippet": kwargs["snippet"],
            "ai_explanation": kwargs["explanation"],
            "suggested_fix": kwargs["fix"],
            "error_type": kwargs["error_type"],
        }

    def _make_js_ts_error(self, title: str, line: int, col: int, explanation: str, language: str, file_path: Path, snippet: str, error_type: str) -> dict:
        return self._make_error(
            bug_title=title, description=explanation,
            severity="High", confidence=85, language=language,
            file_path=str(file_path.relative_to(file_path.parent)),
            line=line, col=col, snippet=snippet,
            explanation=explanation,
            fix="Review the indicated line and fix the bracket, quote, or syntax issue.",
            error_type=error_type,
        )

    def _get_snippet(self, content: str, line_num: int, context: int = 2) -> str:
        lines = content.split("\n")
        start = max(0, line_num - 1 - context)
        end = min(len(lines), line_num + context)
        snippet_lines = []
        for i in range(start, end):
            prefix = ">" if i == line_num - 1 else " "
            snippet_lines.append(f"{prefix} {lines[i]}")
        return "\n".join(snippet_lines)

    def _get_snippet_for_line(self, file_path: Path, line_num: int) -> str:
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").split("\n")
            if 1 <= line_num <= len(lines):
                return lines[line_num - 1][:80]
        except Exception:
            pass
        return ""

    def _deduplicate(self, errors: list[dict]) -> list[dict]:
        seen = set()
        unique: list[dict] = []
        for e in errors:
            key = (e["bug_title"], e["line_number"], e["column_number"])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique
