import ast
import uuid
import re
from pathlib import Path
from collections import Counter

from app.detection.detector import EXTENSION_LANGUAGE_MAP
from app.repositories.syntax_detection_engine import IGNORED_DIRS, SUPPORTED_LANGUAGES

PYTHON_LIKE = {"Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "PHP", "Ruby"}
BRACKET_LANGS = {"JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "PHP"}


class StaticCodeAnalysisEngine:

    def analyze(self, workspace_path: Path | None = None) -> dict:
        if not workspace_path or not workspace_path.exists():
            return {
                "session_id": uuid.uuid4().hex,
                "status": "unavailable",
                "total_errors": 0, "total_files_scanned": 0, "files_with_errors": 0,
                "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0,
                "results": [], "scanned_languages": [],
            }

        language_map = self._detect_languages(workspace_path)
        scanned_languages = list(language_map.keys())
        all_results: list[dict] = []
        total_errors = 0
        files_with_errors = 0
        critical = high = medium = low = 0

        for lang, pattern_list in language_map.items():
            for pattern in pattern_list:
                for file_path in workspace_path.rglob(pattern):
                    if self._is_ignored(file_path):
                        continue
                    result = self._analyze_file(file_path, lang, workspace_path)
                    all_results.append(result)
                    fc = result["error_count"]
                    if fc > 0:
                        files_with_errors += 1
                    total_errors += fc
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

        summary_parts = [f"Static analysis completed. {total_errors} code quality issues detected."]
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
            matches = [m for m in workspace_path.rglob(f"*{ext}") if not self._is_ignored(m)]
            if matches:
                found.setdefault(lang, []).append(f"*{ext}")
        return found

    def _is_ignored(self, path: Path) -> bool:
        return any(part in IGNORED_DIRS for part in path.parts)

    def _analyze_file(self, file_path: Path, language: str, workspace: Path) -> dict:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {
                "file_path": str(file_path.relative_to(workspace)),
                "language": language,
                "errors": [], "error_count": 0, "health_score": 100.0,
            }

        errors: list[dict] = []
        rel = str(file_path.relative_to(workspace))
        lines = content.split("\n")

        if language == "Python":
            errors = self._analyze_python(file_path, content, rel, lines)
        elif language in ("JavaScript", "TypeScript"):
            errors = self._analyze_js_ts(content, rel, language, lines)
        elif language in BRACKET_LANGS:
            errors = self._analyze_generic(content, rel, language, lines)

        errors = self._deduplicate(errors)
        ec = len(errors)
        return {
            "file_path": rel,
            "language": language,
            "errors": errors,
            "error_count": ec,
            "health_score": max(0, min(100, 100 - ec * 3)),
        }

    # ── Python (AST-based deep analysis) ──

    def _analyze_python(self, file_path: Path, content: str, rel: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return errors

        self._check_unused_imports(tree, rel, lines, errors)
        self._check_unused_variables(tree, rel, lines, errors)
        self._check_unused_functions(tree, rel, errors)
        self._check_unused_classes(tree, rel, errors)
        self._check_dead_code(tree, rel, lines, errors)
        self._check_empty_excepts(tree, rel, errors)
        self._check_long_functions(tree, rel, lines, errors)
        self._check_large_classes(tree, rel, lines, errors)
        self._check_deep_nesting(tree, rel, lines, errors)
        self._check_magic_numbers(tree, rel, lines, errors)
        self._check_high_complexity(tree, rel, errors)
        self._check_missing_error_handling(tree, rel, lines, errors)
        self._check_naming_conventions(tree, rel, errors)
        self._check_duplicate_code(lines, rel, errors)
        self._check_infinite_loops(tree, rel, errors)
        self._check_repeated_logic(tree, rel, errors)

        return errors

    def _check_unused_imports(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        imported: dict[str, tuple[int, int]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported[name] = (node.lineno or 1, node.col_offset or 1)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported[name] = (node.lineno or 1, node.col_offset or 1)

        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                if isinstance(node.value, ast.Name):
                    used.add(node.value.id)

        for name, (line, col) in imported.items():
            if name not in used and name not in {"os", "sys", "__future__", "typing"}:
                errors.append(self._make_error(
                    "Unused Import", f"The import '{name}' at line {line} is never used in this file.",
                    "Medium", 90, rel, line, col, self._snippet(lines, line),
                    f"The import statement for '{name}' is unnecessary and can be removed to improve code clarity.",
                    f"Remove 'import {name}' or use it in the file.", "static", name,
                ))

    def _check_unused_variables(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        assignments: dict[str, tuple[int, int]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        assignments[target.id] = (node.lineno or 1, node.col_offset or 1)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
                    assignments[node.target.id] = (node.lineno or 1, node.col_offset or 1)

        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)

        builtins = {"True", "False", "None", "self", "cls", "__name__", "__file__", "__doc__"}
        for name, (line, col) in assignments.items():
            if name not in used and name not in builtins and not name.startswith("_"):
                errors.append(self._make_error(
                    "Unused Variable", f"The variable '{name}' at line {line} is assigned but never used.",
                    "Low", 85, rel, line, col, self._snippet(lines, line),
                    f"The variable '{name}' is assigned on line {line} but never referenced anywhere in the file.",
                    f"Remove the unused variable '{name}' or use it in your code.", "static", "",
                ))

    def _check_unused_functions(self, tree: ast.Module, rel: str, errors: list[dict]) -> None:
        defined: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                defined[node.name] = node.lineno or 1

        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.add(node.func.id)

        builtin_funcs = {"print", "len", "range", "int", "str", "float", "list", "dict", "set",
                         "type", "isinstance", "hasattr", "getattr", "setattr", "open", "map",
                         "filter", "zip", "enumerate", "sorted", "reversed", "min", "max", "sum",
                         "abs", "round", "input", "format", "staticmethod", "classmethod", "property"}
        for name, line in defined.items():
            if name not in called and name not in builtin_funcs:
                errors.append(self._make_error(
                    "Unused Function", f"The function '{name}' defined at line {line} is never called.",
                    "Medium", 80, rel, line, 1, "",
                    f"The function '{name}' is defined but never referenced elsewhere in the project.",
                    f"Remove the unused function '{name}' if it is not needed, or add a call to it.", "static", name,
                ))

    def _check_unused_classes(self, tree: ast.Module, rel: str, errors: list[dict]) -> None:
        defined: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                defined[node.name] = node.lineno or 1

        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                used.add(node.func.id)

        for name, line in defined.items():
            if name not in used:
                errors.append(self._make_error(
                    "Unused Class", f"The class '{name}' defined at line {line} is never instantiated or referenced.",
                    "Medium", 80, rel, line, 1, "",
                    f"The class '{name}' is defined but never used anywhere in the project.",
                    f"Remove the unused class '{name}' if it is not needed.", "static", name,
                ))

    def _check_dead_code(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._scan_dead_code_in_body(node.body, rel, lines, errors)

    def _scan_dead_code_in_body(self, body: list[ast.stmt], rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, stmt in enumerate(body):
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                for j in range(i + 1, len(body)):
                    if not isinstance(body[j], (ast.FunctionDef, ast.ClassDef, ast.Pass)):
                        err_line = body[j].lineno or 1
                        errors.append(self._make_error(
                            "Dead Code", f"Unreachable code detected at line {err_line} after a return/raise statement.",
                            "High", 90, rel, err_line, 1, self._snippet(lines, err_line),
                            f"Code at line {err_line} will never execute because it follows an unconditional return or raise statement.",
                            "Remove the dead code or restructure the logic so it can be reached.", "static", "",
                        ))
                        break
                break

    def _check_empty_excepts(self, tree: ast.Module, rel: str, errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if all(isinstance(s, ast.Pass) for s in node.body):
                    line = node.lineno or 1
                    errors.append(self._make_error(
                        "Empty Exception Block", f"Empty except block at line {line} silently swallows exceptions.",
                        "High", 95, rel, line, 1, "",
                        "An empty except block catches all exceptions but does nothing, making debugging difficult.",
                        "Add proper error handling (logging, re-raising, or recovery logic) to the except block.", "static", "",
                    ))

    def _check_long_functions(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno or 1
                end = node.end_lineno or start
                length = end - start
                if length > 50:
                    errors.append(self._make_error(
                        "Long Function", f"Function '{node.name}' at line {start} has {length} lines.",
                        "Medium", 80, rel, start, 1, "",
                        f"The function '{node.name}' spans {length} lines. Long functions are harder to understand and maintain.",
                        f"Consider refactoring '{node.name}' into smaller helper functions.", "static", node.name,
                    ))

    def _check_large_classes(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                start = node.lineno or 1
                end = node.end_lineno or start
                length = end - start
                if length > 200:
                    errors.append(self._make_error(
                        "Large Class", f"Class '{node.name}' at line {start} has {length} lines.",
                        "Medium", 75, rel, start, 1, "",
                        f"The class '{node.name}' spans {length} lines. Large classes violate the Single Responsibility Principle.",
                        f"Consider splitting '{node.name}' into smaller, focused classes.", "static", node.name,
                    ))

    def _check_deep_nesting(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.If, ast.For, ast.While,
                                 ast.Try, ast.With)):
                depth = self._nesting_depth(node)
                if depth >= 5:
                    line = node.lineno or 1
                    errors.append(self._make_error(
                        "Deep Nesting", f"Deep nesting detected at line {line} ({depth} levels).",
                        "Medium", 75, rel, line, 1, self._snippet(lines, line),
                        f"Nesting depth of {depth} levels makes code hard to read and maintain.",
                        "Refactor to reduce nesting by using early returns, guard clauses, or extracting helper functions.", "static", "",
                    ))
                    break

    def _nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With,
                                  ast.AsyncFor, ast.AsyncWith)):
                child_depth = self._nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                child_depth = self._nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth

    def _check_magic_numbers(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if isinstance(node.value, int) and node.value in (0, 1, -1):
                    continue
                if isinstance(node.value, float):
                    continue
                parent = getattr(node, "parent", None)
                line = node.lineno or 1
                col = node.col_offset or 1
                errors.append(self._make_error(
                    "Magic Number", f"Magic number '{node.value}' at line {line} should be a named constant.",
                    "Low", 70, rel, line, col, self._snippet_for_line(lines, line),
                    f"Hardcoded numeric literal '{node.value}' at line {line} reduces code readability and maintainability.",
                    f"Replace '{node.value}' with a named constant (e.g., MAX_RETRIES = {node.value}).", "static", "",
                ))
                break

    def _check_high_complexity(self, tree: ast.Module, rel: str, errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                          ast.AsyncFor, ast.BoolOp)):
                        complexity += 1
                if complexity > 10:
                    line = node.lineno or 1
                    errors.append(self._make_error(
                        "High Cyclomatic Complexity",
                        f"Function '{node.name}' at line {line} has complexity of {complexity}.",
                        "High", 85, rel, line, 1, "",
                        f"Cyclomatic complexity of {complexity} indicates the function has too many branching paths and is hard to test.",
                        f"Refactor '{node.name}' into smaller functions, each with a single responsibility.", "static", node.name,
                    ))

    def _check_missing_error_handling(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ("open", "read", "write", "connect", "send", "recv"):
                    line = node.lineno or 1
                    parent = getattr(node, "parent", None)
                    if not any(isinstance(p, ast.Try) for p in self._parents(tree, node)):
                        errors.append(self._make_error(
                            "Missing Error Handling",
                            f"Call to '{node.func.attr}' at line {line} is not wrapped in try/except.",
                            "High", 80, rel, line, 1, self._snippet_for_line(lines, line),
                            f"The '{node.func.attr}()' call at line {line} may raise an exception that is not handled.",
                            f"Wrap the call in a try/except block to handle potential failures gracefully.", "static", "",
                        ))

    def _parents(self, tree: ast.Module, target: ast.AST) -> list[ast.AST]:
        result: list[ast.AST] = []
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child is target:
                    result.append(node)
        return result

    def _check_naming_conventions(self, tree: ast.Module, rel: str, errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    if not re.match(r"^[a-z_][a-z0-9_]*$", node.name):
                        line = node.lineno or 1
                        errors.append(self._make_error(
                            "Invalid Naming Convention",
                            f"Function '{node.name}' at line {line} doesn't follow snake_case.",
                            "Low", 80, rel, line, 1, "",
                            f"The function name '{node.name}' does not follow Python's snake_case naming convention.",
                            f"Rename '{node.name}' to use snake_case (e.g., '{self._to_snake(node.name)}').", "static", node.name,
                        ))
            elif isinstance(node, ast.ClassDef):
                if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                    line = node.lineno or 1
                    errors.append(self._make_error(
                        "Invalid Naming Convention",
                        f"Class '{node.name}' at line {line} doesn't follow PascalCase.",
                        "Low", 80, rel, line, 1, "",
                        f"The class name '{node.name}' does not follow Python's PascalCase convention.",
                        f"Rename '{node.name}' to use PascalCase (e.g., '{node.name.title()}').", "static", node.name,
                    ))

    def _to_snake(self, name: str) -> str:
        s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
        return s.lower()

    def _check_duplicate_code(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        block_lines: list[str] = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", "//", "/*", "*")):
                block_lines.append(stripped)
        line_counter = Counter(block_lines)
        dupes = [(line, count) for line, count in line_counter.most_common(5) if count >= 3 and len(line) > 20]
        for line_text, count in dupes:
            occurrences = [i + 1 for i, l in enumerate(block_lines) if l == line_text]
            if occurrences:
                errors.append(self._make_error(
                    "Duplicate Code",
                    f"Line '{line_text[:50]}...' appears {count} times across the file.",
                    "Medium", 75, rel, occurrences[0], 1, line_text[:80],
                    f"The same line of code appears {count} times in this file, indicating code duplication.",
                    "Extract the duplicated code into a reusable function or variable.", "static", "",
                ))
                break

    def _check_infinite_loops(self, tree: ast.Module, rel: str, errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_break = any(
                        isinstance(n, ast.Break) for n in ast.walk(node)
                    )
                    if not has_break:
                        line = node.lineno or 1
                        errors.append(self._make_error(
                            "Infinite Loop Risk",
                            f"Infinite loop detected at line {line} — 'while True' without a break.",
                            "Critical", 95, rel, line, 1, "",
                            "A 'while True' loop without any break statement will run indefinitely, potentially freezing the application.",
                            "Add a break condition or a return statement inside the loop.", "static", "",
                        ))

    def _check_repeated_logic(self, tree: ast.Module, rel: str, errors: list[dict]) -> None:
        func_bodies: list[tuple[str, int, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_str = ast.dump(node)
                func_bodies.append((node.name, node.lineno or 1, body_str))

        for i, (name1, line1, body1) in enumerate(func_bodies):
            for j, (name2, line2, body2) in enumerate(func_bodies):
                if j > i and self._similarity(body1, body2) > 0.85:
                    errors.append(self._make_error(
                        "Repeated Logic",
                        f"Function '{name1}' (line {line1}) and '{name2}' (line {line2}) have similar implementations.",
                        "Medium", 70, rel, line1, 1, "",
                        f"Functions '{name1}' and '{name2}' share very similar code, indicating duplicated logic.",
                        f"Consolidate the shared logic into a single reusable function.", "static", name1,
                    ))
                    break
            if any(e.get("bug_title") == "Repeated Logic" for e in errors):
                break

    def _similarity(self, s1: str, s2: str) -> float:
        if not s1 or not s2:
            return 0.0
        longer, shorter = (s1, s2) if len(s1) > len(s2) else (s2, s1)
        if len(longer) < 50:
            return 0.0
        match_len = sum(1 for a, b in zip(longer, shorter) if a == b)
        return match_len / len(longer)

    # ── JavaScript / TypeScript ──

    def _analyze_js_ts(self, content: str, rel: str, language: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        self._check_js_ts_unused(lines, rel, errors)
        self._check_js_ts_long_funcs(lines, rel, errors)
        self._check_dead_code_brkt(lines, rel, errors)
        self._check_duplicate_code(lines, rel, errors)
        self._check_magic_numbers_brkt(lines, rel, errors)
        self._check_deep_nesting_brkt(lines, rel, errors)
        self._check_empty_catch(lines, rel, errors)
        self._check_console_log(lines, rel, errors)
        return errors

    def _check_js_ts_unused(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        func_defs: list[tuple[str, int]] = []
        var_defs: list[tuple[str, int]] = []
        func_calls: set[str] = set()
        var_refs: set[str] = set()

        for i, line in enumerate(lines, 1):
            f_match = re.search(r"(?:function|const|let|var)\s+(\w+)", line)
            if f_match and "function" in line:
                func_defs.append((f_match.group(1), i))
            elif f_match and f_match.group(1) and "=" in line:
                var_defs.append((f_match.group(1), i))
            call_match = re.findall(r"(\w+)\s*\(", line)
            for c in call_match:
                if c not in ("if", "for", "while", "switch", "catch", "function", "typeof"):
                    func_calls.add(c)
            ref_match = re.findall(r"\b(\w+)\b", line)
            for r in ref_match:
                if r not in ("function", "const", "let", "var", "return", "if", "else",
                             "for", "while", "do", "switch", "case", "break", "continue",
                             "new", "this", "typeof", "instanceof", "void", "delete",
                             "import", "export", "from", "class", "extends", "static",
                             "get", "set", "async", "await", "yield", "true", "false",
                             "null", "undefined"):
                    var_refs.add(r)

        for name, line in func_defs:
            if name not in func_calls:
                errors.append(self._make_error(
                    "Unused Function", f"Function '{name}' at line {line} is defined but never called.",
                    "Medium", 75, rel, line, 1, self._snippet_for_line(lines, line),
                    f"The function '{name}' is defined but never invoked anywhere in the file.",
                    f"Remove the unused function or add a call to it.", "static", name,
                ))
                break

        for name, line in var_defs:
            if name not in var_refs and not name.startswith("_"):
                errors.append(self._make_error(
                    "Unused Variable", f"Variable '{name}' at line {line} is declared but never used.",
                    "Low", 80, rel, line, 1, self._snippet_for_line(lines, line),
                    f"The variable '{name}' is declared but never referenced anywhere in the file.",
                    f"Remove the unused variable declaration.", "static", "",
                ))
                break

    def _check_js_ts_long_funcs(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        in_func = False
        func_start = 0
        func_name = ""
        brace_count = 0
        for i, line in enumerate(lines, 1):
            f_match = re.match(r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()", line)
            if f_match and not in_func:
                in_func = True
                func_start = i
                func_name = f_match.group(1) or f_match.group(2) or ""
                brace_count = line.count("{") - line.count("}")
                continue
            if in_func:
                brace_count += line.count("{") - line.count("}")
                if brace_count <= 0:
                    length = i - func_start
                    if length > 50:
                        errors.append(self._make_error(
                            "Long Function", f"Function '{func_name}' at line {func_start} spans {length} lines.",
                            "Medium", 75, rel, func_start, 1, "",
                            f"The function spans {length} lines. Long functions are harder to understand.",
                            "Refactor into smaller helper functions.", "static", func_name,
                        ))
                    in_func = False

    def _check_dead_code_brkt(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped in ("return;", "return", "break;", "break", "continue;", "continue", "throw"):
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith(("}", ")", ";", "//", "/*", "*")):
                        errors.append(self._make_error(
                            "Dead Code", f"Unreachable code at line {j + 1} after return/break.",
                            "High", 85, rel, j + 1, 1, self._snippet_for_line(lines, j + 1),
                            "Code after an unconditional return or break statement will never execute.",
                            "Remove the dead code or restructure the logic.", "static", "",
                        ))
                        break
                break

    def _check_magic_numbers_brkt(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            nums = re.findall(r"(?<![.\w])(\d{2,})(?![.\w])", line)
            if nums and "=" in line and not line.strip().startswith(("//", "/*", "*")):
                errors.append(self._make_error(
                    "Magic Number", f"Hardcoded number '{nums[0]}' at line {i} should be a named constant.",
                    "Low", 65, rel, i, line.find(nums[0]) + 1, self._snippet_for_line(lines, i),
                    f"Hardcoded numeric literal '{nums[0]}' reduces code readability.",
                    f"Replace with a named constant.", "static", "",
                ))
                break

    def _check_deep_nesting_brkt(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            indent = len(line) - len(line.lstrip())
            if indent > 40:
                errors.append(self._make_error(
                    "Deep Nesting", f"Deep nesting at line {i} (indentation level {indent // 2}).",
                    "Medium", 70, rel, i, 1, self._snippet_for_line(lines, i),
                    "Excessive nesting depth makes code difficult to read and maintain.",
                    "Refactor to reduce nesting with early returns or guard clauses.", "static", "",
                ))
                break

    def _check_empty_catch(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines):
            if "catch" in line and "{" in line:
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].strip() in ("{}", "{ }", "{  }"):
                        errors.append(self._make_error(
                            "Empty Exception Block",
                            f"Empty catch block at line {i + 1} silently swallows errors.",
                            "High", 90, rel, i + 1, 1, "",
                            "An empty catch block silently swallows exceptions, making debugging difficult.",
                            "Add error handling (logging or recovery logic) to the catch block.", "static", "",
                        ))
                        break
                break

    def _check_console_log(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if "console.log" in line or "console.debug" in line:
                errors.append(self._make_error(
                    "Debug Log Left in Code",
                    f"Console log statement at line {i} should be removed before production.",
                    "Low", 90, rel, i, line.find("console") + 1, self._snippet_for_line(lines, i),
                    "Debug logging statements left in production code can expose sensitive information and clutter output.",
                    "Remove or comment out the console.log statement.", "static", "",
                ))
                break

    # ── Generic (Java, C#, C++, Go, PHP) ──

    def _analyze_generic(self, content: str, rel: str, language: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        self._check_dead_code_brkt(lines, rel, errors)
        self._check_duplicate_code(lines, rel, errors)
        self._check_magic_numbers_brkt(lines, rel, errors)
        self._check_deep_nesting_brkt(lines, rel, errors)
        self._check_empty_catch(lines, rel, errors)
        return errors

    # ── Helpers ──

    def _make_error(self, title: str, desc: str, severity: str, confidence: int,
                    rel: str, line: int, col: int, snippet: str,
                    explanation: str, fix: str, error_type: str, func_name: str) -> dict:
        return {
            "bug_title": title, "description": desc, "severity": severity,
            "confidence": confidence, "language": "", "affected_file": rel,
            "line_number": line, "column_number": col, "code_snippet": snippet,
            "ai_explanation": explanation, "suggested_fix": fix,
            "error_type": error_type, "function_name": func_name,
        }

    def _snippet(self, lines: list[str], line_num: int, ctx: int = 1) -> str:
        start = max(0, line_num - 1 - ctx)
        end = min(len(lines), line_num + ctx)
        return "\n".join(f"{'>' if i == line_num - 1 else ' '} {lines[i]}" for i in range(start, end))

    def _snippet_for_line(self, lines: list[str], line_num: int) -> str:
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1][:80]
        return ""

    def _deduplicate(self, errors: list[dict]) -> list[dict]:
        seen = set()
        unique: list[dict] = []
        for e in errors:
            key = (e["bug_title"], e["line_number"], e["affected_file"])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique
