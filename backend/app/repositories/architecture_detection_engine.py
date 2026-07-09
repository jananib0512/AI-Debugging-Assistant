import ast
import re
import uuid
from collections import defaultdict
from pathlib import Path

from app.detection.detector import EXTENSION_LANGUAGE_MAP
from app.repositories.syntax_detection_engine import IGNORED_DIRS, SUPPORTED_LANGUAGES


class ArchitectureDetectionEngine:

    def analyze(self, workspace_path: Path | None = None) -> dict:
        if not workspace_path or not workspace_path.exists():
            return self._empty_result()

        language_map = self._detect_languages(workspace_path)
        scanned_languages = list(language_map.keys())
        all_results: list[dict] = []
        total_errors = 0
        files_with_errors = 0
        critical = high = medium = low = 0

        import_graph: dict[str, list[str]] = {}

        for lang, patterns in language_map.items():
            for pattern in patterns:
                for file_path in workspace_path.rglob(pattern):
                    if self._is_ignored(file_path):
                        continue
                    rel = str(file_path.relative_to(workspace))
                    imports = self._extract_imports(file_path)
                    import_graph[rel] = imports

        for lang, patterns in language_map.items():
            for pattern in patterns:
                for file_path in workspace_path.rglob(pattern):
                    if self._is_ignored(file_path):
                        continue
                    result = self._analyze_file(file_path, lang, workspace_path, import_graph)
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

        circular = self._detect_circular_imports(import_graph, workspace_path)
        for circ in circular:
            total_errors += 1
            files_with_errors += 1
            critical += 1
            all_results.append(self._circular_result(circ, workspace_path))

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
            matches = list(workspace_path.rglob(f"*{ext}"))
            actual = [m for m in matches if not self._is_ignored(m)]
            if actual:
                found.setdefault(lang, []).append(f"*{ext}")
        return found

    def _is_ignored(self, path: Path) -> bool:
        return any(part in IGNORED_DIRS for part in path.parts)

    def _extract_imports(self, file_path: Path) -> list[str]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []
        imports: list[str] = []
        for line in content.split("\n"):
            m = re.match(r'^\s*import\s+(\S+)', line)
            if m:
                imports.append(m.group(1).split(".")[0])
                continue
            m = re.match(r'^\s*from\s+(\S+)\s+import', line)
            if m:
                parts = m.group(1).split(".")[0]
                imports.append(parts)
                continue
            m = re.match(r'^\s*(?:const|let|var)\s+\w+\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]', line)
            if m:
                pkg = m.group(1).split("/")[0]
                if pkg.startswith("@"):
                    parts = m.group(1).split("/")
                    pkg = f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]
                if not pkg.startswith("."):
                    imports.append(pkg)
                continue
            m = re.match(r'^\s*import\s+(?:\{[^}]*\}\s+from\s+)?[\'"]([^\'"]+)[\'"]', line)
            if m:
                pkg = m.group(1).split("/")[0]
                if pkg.startswith("@"):
                    parts = m.group(1).split("/")
                    pkg = f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]
                if not pkg.startswith("."):
                    imports.append(pkg)
        return list(set(imports))

    def _detect_circular_imports(self, graph: dict[str, list[str]], workspace: Path) -> list[list[str]]:
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in graph:
                    continue
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    cycle = path[path.index(neighbor):] + [neighbor]
                    if len(cycle) > 1:
                        cycles.append(cycle)
            rec_stack.discard(node)

        for node in graph:
            if node not in visited:
                dfs(node, [node])

        seen = set()
        unique: list[list[str]] = []
        for c in cycles:
            key = tuple(sorted(c))
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique[:10]

    def _circular_result(self, cycle: list[str], workspace: Path) -> dict:
        return {
            "file_path": cycle[0],
            "language": "Python",
            "errors": [{
                "bug_title": "Circular Dependency",
                "description": f"Circular import chain detected: {' → '.join(cycle)}. This can cause import errors and initialization problems.",
                "severity": "Critical",
                "confidence": 95,
                "language": "",
                "affected_file": cycle[0],
                "line_number": 1,
                "column_number": 1,
                "code_snippet": " → ".join(cycle),
                "ai_explanation": f"Circular dependencies occur when modules import each other directly or transitively. This creates a cycle in the dependency graph: {' → '.join(cycle)}. Python raises ImportError or produces partially-initialized modules.",
                "suggested_fix": "Refactor shared code into a common module that both files can import without creating a cycle. Use lazy imports (inside functions) if immediate refactoring is not possible.",
                "error_type": "circular_dependency",
                "function_name": "",
                "architecture_category": "circular_dependency",
                "impact_scope": "Multiple modules across the project",
            }],
            "error_count": 1,
            "health_score": 60.0,
        }

    def _analyze_file(self, file_path: Path, language: str, workspace: Path, import_graph: dict) -> dict:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            rel = str(file_path.relative_to(workspace))
            return {
                "file_path": rel,
                "language": language,
                "errors": [], "error_count": 0, "health_score": 100.0,
            }
        rel = str(file_path.relative_to(workspace))
        lines = content.split("\n")
        errors: list[dict] = []
        imports_here = import_graph.get(rel, [])

        if language == "Python":
            errors = self._analyze_python(content, rel, lines, imports_here)
        elif language in ("JavaScript", "TypeScript"):
            errors = self._analyze_jsts(content, rel, lines)
        elif language in ("Java", "C#", "C++", "Go", "PHP", "Ruby"):
            errors = self._analyze_generic(content, rel, lines)

        errors = self._deduplicate(errors)
        health = self._calc_health(errors)
        return {
            "file_path": rel,
            "language": language,
            "errors": errors,
            "error_count": len(errors),
            "health_score": health,
        }

    # ── Python AST Analysis ──

    def _analyze_python(self, content: str, rel: str, lines: list[str], imports: list[str]) -> list[dict]:
        errors: list[dict] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return errors

        self._check_god_class(tree, rel, lines, errors)
        self._check_god_function(tree, rel, lines, errors)
        self._check_deep_inheritance(tree, rel, lines, errors)
        self._check_tight_coupling(rel, imports, errors, lines)
        self._check_complex_conditionals(tree, rel, lines, errors)
        self._check_logic_duplication(tree, rel, lines, errors)
        self._check_mixed_concerns(tree, rel, lines, errors)
        self._check_business_logic_layer(tree, rel, lines, errors)
        self._check_missing_validation(tree, rel, lines, errors)
        self._check_improper_globals(tree, rel, lines, errors)
        self._check_exception_antipattern(tree, rel, lines, errors)
        self._check_dead_code_path(tree, rel, lines, errors)
        return errors

    def _check_god_class(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                if len(methods) > 15:
                    errors.append(self._make_error(
                        "God Class",
                        f"Class '{node.name}' has {len(methods)} methods. Classes with too many methods violate Single Responsibility Principle.",
                        "Medium", 80, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"The class '{node.name}' contains {len(methods)} methods, suggesting it handles too many responsibilities. This makes the class hard to maintain, test, and extend.",
                        f"Split '{node.name}' into smaller, focused classes. Each class should have a single responsibility. Extract related groups of methods into separate service/repository classes.",
                        "god_class", "", f"Class has {len(methods)} methods — consider splitting.",
                    ))
                    break

    def _check_god_function(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                issues = []
                if len(node.args.args) > 7:
                    issues.append(f"has {len(node.args.args)} parameters")
                body_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if body_lines > 80:
                    issues.append(f"spans {body_lines} lines")
                if len(issues) >= 2:
                    errors.append(self._make_error(
                        "God Function",
                        f"Function '{node.name}()' has multiple complexity factors: {', '.join(issues)}.",
                        "Medium", 80, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"The function '{node.name}()' has {len(node.args.args)} parameters and spans {max(body_lines, 0)} lines. Large functions with many parameters are hard to understand, test, and maintain.",
                        f"Break '{node.name}()' into smaller functions. Use data classes/dataclasses to group related parameters. Extract distinct logic blocks into named helper functions.",
                        "god_function", node.name, f"Function has {', '.join(issues)}.",
                    ))
                    continue
                if len(node.args.args) > 7:
                    errors.append(self._make_error(
                        "Excessive Parameters",
                        f"Function '{node.name}()' has {len(node.args.args)} parameters, making it hard to use and test.",
                        "Medium", 75, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Functions with more than 5-7 parameters are confusing to call and indicate the function may be doing too much.",
                        f"Group related parameters into a single data class, or split the function into smaller functions with fewer parameters.",
                        "excessive_params", node.name, f"{len(node.args.args)} parameters.",
                    ))
                if body_lines > 80:
                    errors.append(self._make_error(
                        "Overly Long Function",
                        f"Function '{node.name}()' spans {body_lines} lines. Long functions are hard to understand and maintain.",
                        "Medium", 75, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Functions longer than ~50 lines typically do too many things. {node.name}() spans {body_lines} lines.",
                        f"Extract distinct blocks of logic into helper functions. Each function should do one thing well.",
                        "long_function", node.name, f"{body_lines} lines.",
                    ))

    def _check_deep_inheritance(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [b for b in node.bases if isinstance(b, ast.Name)]
                if len(bases) > 0:
                    inheritance_depth = 1
                    current = node
                    for _ in range(10):
                        parent_bases = [b for b in current.bases if isinstance(b, ast.Name)]
                        if not parent_bases:
                            break
                        current = None
                        for walk_node in ast.walk(tree):
                            if isinstance(walk_node, ast.ClassDef) and walk_node.name == parent_bases[0].id:
                                current = walk_node
                                break
                        if current is None:
                            break
                        inheritance_depth += 1
                    if inheritance_depth >= 4:
                        errors.append(self._make_error(
                            "Deep Inheritance Hierarchy",
                            f"Class '{node.name}' has {inheritance_depth} levels of inheritance. Deep hierarchies make code hard to understand and modify.",
                            "Medium", 70, rel, node.lineno, node.col_offset or 0,
                            self._snippet(lines, node.lineno),
                            f"Inheritance depth of {inheritance_depth} levels means understanding behavior requires tracing through {inheritance_depth} classes. Deep hierarchies are fragile and hard to modify.",
                            f"Prefer composition over inheritance. Use interfaces/protocols and dependency injection instead of deep class hierarchies.",
                            "deep_inheritance", "", f"{inheritance_depth} levels of inheritance.",
                        ))
                        break

    def _check_tight_coupling(self, rel: str, imports: list[str], errors: list[dict], lines: list[str]) -> None:
        if len(imports) > 12:
            errors.append(self._make_error(
                "Tight Coupling",
                f"File imports from {len(imports)} different modules. High coupling makes the code hard to maintain and test.",
                "Medium", 70, rel, 1, 1,
                lines[0][:120] if lines else "",
                f"Importing from {len(imports)} modules creates high coupling. Changes in any of those modules may require changes in this file.",
                f"Reduce coupling by introducing mediator patterns, dependency injection, or consolidating related imports into facade modules.",
                "tight_coupling", "",
                f"{len(imports)} module dependencies — high coupling.",
            ))

    def _check_complex_conditionals(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                depth = self._if_depth(node, 0)
                if depth >= 4:
                    func = self._find_parent_func(tree, node) or ""
                    errors.append(self._make_error(
                        "Complex Conditional Logic",
                        f"If-else nesting depth of {depth} at line {node.lineno}. Deep conditionals are hard to understand and test.",
                        "High", 85, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Deeply nested conditionals (depth {depth}) create complex code paths that are difficult to reason about, test, and modify without introducing bugs.",
                        f"Use early returns / guard clauses, extract conditions into named functions, use polymorphism, or replace with strategy pattern / lookup tables.",
                        "complex_conditional", func,
                        f"If-else nesting depth: {depth}.",
                    ))
                    break

    def _check_logic_duplication(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        function_bodies: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_text = ast.unparse(node.body) if node.body else ""
                if body_text:
                    for other_name, other_body in function_bodies.items():
                        if other_name != node.name and body_text == other_body:
                            errors.append(self._make_error(
                                "Logic Duplication",
                                f"Function '{node.name}()' has identical code body to '{other_name}()'. Duplicated logic violates DRY principle.",
                                "Medium", 80, rel, node.lineno, node.col_offset or 0,
                                self._snippet(lines, node.lineno),
                                f"Two functions '{node.name}' and '{other_name}' have identical implementations. This duplicates bug fixes and makes maintenance harder.",
                                f"Replace duplicated functions with a single shared function. If the functions have different signatures, create a common helper and call it from both.",
                                "logic_duplication", node.name,
                                f"Duplicated from '{other_name}'.",
                            ))
                            break
                    function_bodies[node.name] = body_text

    def _check_mixed_concerns(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                has_io = False
                has_computation = False
                has_db = False
                has_business = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        cname = ""
                        if isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Name):
                            cname = f"{child.func.value.id}.{child.func.attr}"
                        elif isinstance(child.func, ast.Name):
                            cname = child.func.id
                        if cname in ("open", "read", "write", "save"):
                            has_io = True
                        if cname in ("filter", "all", "query", "session.query", "db.query"):
                            has_db = True
                        if cname in ("commit", "rollback", "transaction"):
                            has_db = True
                has_business = len(node.body) > 3
                concerns = sum([has_io, has_db, has_business])
                if concerns >= 2 and (has_db or has_io):
                    errors.append(self._make_error(
                        "Mixed Concerns",
                        f"Function '{node.name}()' mixes business logic with {'I/O' if has_io else ''}{' and ' if has_io and has_db else ''}{'database access' if has_db else ''}. This violates separation of concerns.",
                        "Medium", 70, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Mixing {'I/O operations' if has_io else ''}{' and ' if has_io and has_db else ''}{'database queries' if has_db else ''} with business logic in '{node.name}()' violates the Single Responsibility Principle and makes the function hard to test.",
                        f"Separate the function into distinct layers: move {'I/O to a repository/IO layer' if has_io else ''}{' and ' if has_io and has_db else ''}{'database operations to a repository' if has_db else ''} and keep business logic in a service layer.",
                        "mixed_concerns", node.name,
                        "Violates separation of concerns.",
                    ))
                    break

    def _check_business_logic_layer(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        is_controller = any(kw in rel.lower() for kw in ["view", "template", "controller", "handler", "route"])
        if not is_controller:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ("query", "filter", "all", "raw_sql", "execute"):
                    errors.append(self._make_error(
                        "Business Logic in Wrong Layer",
                        f"Database query '{node.func.attr}' found at line {node.lineno} in a controller/view file. Business logic should be in service/repository layers.",
                        "High", 85, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Placing database queries directly in controller/view files makes the code hard to test, reuse, and maintain. Business logic and data access belong in service/repository layers.",
                        f"Move the database query to a dedicated repository or service class. Controllers should only handle request/response concerns.",
                        "business_logic_layer", "", "Database query in controller layer.",
                    ))
                    break

    def _check_missing_validation(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_handler = any(kw in node.name.lower() for kw in ["handler", "handle", "endpoint", "post", "put", "patch", "create", "update", "save"])
                if not is_handler:
                    continue
                has_validation = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        cname = ""
                        if isinstance(child.func, ast.Attribute):
                            cname = f"{child.func.attr}"
                        elif isinstance(child.func, ast.Name):
                            cname = child.func.id
                        if cname in ("validate", "is_valid", "validate_data", "check", "assert", "raise"):
                            has_validation = True
                            break
                if not has_validation:
                    errors.append(self._make_error(
                        "Missing Input Validation",
                        f"Handler function '{node.name}()' at line {node.lineno} has no visible input validation. Missing validation can lead to security vulnerabilities and runtime errors.",
                        "High", 80, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Handler '{node.name}()' processes input without visible validation. This can lead to injection attacks, data corruption, and unexpected errors.",
                        f"Add input validation using Pydantic models, form validation libraries, or explicit type/range checks at the start of the function. Validate all external input before processing.",
                        "missing_validation", node.name,
                        "No input validation in handler.",
                    ))
                    break

    def _check_improper_globals(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                for name in node.names:
                    parent = self._find_parent_func(tree, node) or ""
                    errors.append(self._make_error(
                        "Improper Use of Global State",
                        f"Global variable '{name}' used in function '{parent}' at line {node.lineno}. Mutable global state makes code unpredictable and hard to debug.",
                        "High", 85, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Using global variables for state management introduces hidden dependencies between functions. Changes to '{name}' can affect any part of the program, making debugging difficult.",
                        f"Replace global state with dependency injection, class-level state, or pass values as function parameters. Use context managers for shared resources.",
                        "improper_global", parent,
                        f"Global '{name}' used for state.",
                    ))
                    break

    def _check_exception_antipattern(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "Exception"):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Raise):
                            if isinstance(child.exc, ast.Call) and isinstance(child.exc.func, ast.Name):
                                if child.exc.func.id in ("Exception", "RuntimeError"):
                                    parent = self._find_parent_func(tree, node) or ""
                                    errors.append(self._make_error(
                                        "Exception Antipattern",
                                        f"Catching broad Exception and re-raising generic exception at line {child.lineno}. This loses error context and complicates debugging.",
                                        "Medium", 75, rel, child.lineno, child.col_offset or 0,
                                        self._snippet(lines, child.lineno or node.lineno),
                                        f"Catching a broad exception and re-raising as a generic type discards the original error type and stack trace, making it harder to diagnose issues.",
                                        f"Catch specific exception types, re-raise the original exception (without creating a new one), or include the original error as a cause (raise ... from original_error).",
                                        "exception_antipattern", parent,
                                        "Loses original error context.",
                                    ))
                                    break

    def _check_dead_code_path(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for stmt in node.body:
                    if isinstance(stmt, (ast.Return, ast.Raise)):
                        stmt_idx = node.body.index(stmt)
                        following = node.body[stmt_idx + 1:]
                        if following:
                            after = following[0]
                            if not isinstance(after, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                errors.append(self._make_error(
                                    "Dead Code Path",
                                    f"Unreachable code after '{stmt.__class__.__name__.lower()}' at line {after.lineno} in function '{node.name}()'. Dead code increases confusion and maintenance cost.",
                                    "Medium", 80, rel, after.lineno, after.col_offset or 0,
                                    self._snippet(lines, after.lineno),
                                    f"Code after a return or raise statement is unreachable. This code may be leftover from refactoring and can mislead developers.",
                                    f"Remove the unreachable code block. If it needs to execute, restructure the logic so the return/raise happens after all intended code runs.",
                                    "dead_code", node.name,
                                    "Unreachable code after return/raise.",
                                ))
                                break
                    if isinstance(stmt, ast.Return) or isinstance(stmt, ast.Raise):
                        pass

    # ── JS/TS Analysis ──

    def _analyze_jsts(self, content: str, rel: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        self._check_god_class_jsts(lines, rel, errors)
        self._check_god_function_jsts(lines, rel, errors)
        self._check_complex_conditionals_jsts(lines, rel, errors)
        self._check_tight_coupling_jsts(lines, rel, errors)
        self._check_missing_validation_jsts(lines, rel, errors)
        self._check_mixed_concerns_jsts(lines, rel, errors)
        return errors

    def _check_god_class_jsts(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        methods_found = 0
        class_name = ""
        class_line = 0
        brace_depth = 0
        in_class = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'(class|interface)\s+\w+', stripped):
                in_class = True
                class_name = stripped.split()[1] if stripped.split() else ""
                class_line = i
                methods_found = 0
                brace_depth = stripped.count("{") - stripped.count("}")
            elif in_class:
                brace_depth += stripped.count("{") - stripped.count("}")
                if re.match(r'\s*(async\s+)?\w+\s*\(', stripped) or re.match(r'\s*(public|private|protected)\s+\w+\s*\(', stripped):
                    methods_found += 1
                if brace_depth <= 0:
                    if methods_found > 15:
                        errors.append(self._make_error(
                            "God Class",
                            f"Class '{class_name}' has {methods_found} methods. Classes with too many methods violate Single Responsibility Principle.",
                            "Medium", 80, rel, class_line, 1,
                            lines[class_line - 1][:120] if class_line <= len(lines) else "",
                            f"Class '{class_name}' contains {methods_found} methods, indicating it handles too many responsibilities.",
                            f"Split '{class_name}' into smaller, focused classes following Single Responsibility Principle.",
                            "god_class", "",
                            f"Class has {methods_found} methods.",
                        ))
                    in_class = False

    def _check_god_function_jsts(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            m = re.search(r'(?:function|def)\s+(\w+)\s*\(([^)]*)\)', line)
            if not m:
                m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)', line)
            if not m:
                m = re.search(r'(\w+)\s*:\s*(?:async\s*)?(?:function\s*)?\(([^)]*)\)', line)
            if m:
                func_name = m.group(1)
                params = m.group(2).split(",") if m.group(2).strip() else []
                if len(params) > 7:
                    errors.append(self._make_error(
                        "Excessive Parameters",
                        f"Function '{func_name}' has {len(params)} parameters, making it hard to use and test.",
                        "Medium", 75, rel, i, line.find("(") + 1 if "(" in line else 1,
                        line[:120],
                        f"Functions with more than 5-7 parameters are confusing to call and indicate the function may be doing too much.",
                        f"Group related parameters into a configuration object or use destructuring with defaults.",
                        "excessive_params", func_name,
                        f"{len(params)} parameters.",
                    ))

    def _check_complex_conditionals_jsts(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        depth = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'(if|else if|elif)\s*[\(]', stripped):
                depth += 1
            if depth >= 4:
                errors.append(self._make_error(
                    "Complex Conditional Logic",
                    f"If-else nesting depth of {depth} at line {i}. Deep conditionals are hard to understand and test.",
                    "High", 85, rel, i, line.find("(") + 1 if "(" in line else 1,
                    line[:120],
                    f"Deeply nested conditionals create complex code paths that are difficult to reason about and test.",
                    f"Use early returns, guard clauses, extract conditions into named functions, or use switch/pattern matching.",
                    "complex_conditional", "",
                    f"Conditional depth: {depth}.",
                ))
                break
            if re.match(r'\s*\}', stripped):
                depth = max(0, depth - 1)

    def _check_tight_coupling_jsts(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        imports = set()
        for line in lines:
            m = re.match(r'^\s*import\s+(?:\{[^}]*\}\s+from\s+)?[\'"]([^\'"]+)[\'"]', line)
            if m:
                pkg = m.group(1).split("/")[0]
                if pkg.startswith("@"):
                    parts = m.group(1).split("/")
                    pkg = f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]
                if not pkg.startswith("."):
                    imports.add(pkg)
            m = re.match(r'^\s*(?:const|let|var)\s+\w+\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]', line)
            if m:
                pkg = m.group(1).split("/")[0]
                if pkg.startswith("@"):
                    parts = m.group(1).split("/")
                    pkg = f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]
                if not pkg.startswith("."):
                    imports.add(pkg)
        if len(imports) > 15:
            errors.append(self._make_error(
                "Tight Coupling",
                f"File imports from {len(imports)} different modules/packages. High coupling makes the code hard to maintain and test.",
                "Medium", 70, rel, 1, 1,
                lines[0][:120] if lines else "",
                f"Importing from {len(imports)} modules creates high coupling. Changes in any module may require changes in this file.",
                f"Reduce coupling by introducing facade modules, barrel exports, or dependency injection patterns.",
                "tight_coupling", "",
                f"{len(imports)} dependencies — high coupling.",
            ))

    def _check_missing_validation_jsts(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'(app|router|route)\.(post|put|patch|delete)\s*\(', line, re.IGNORECASE):
                handler_lines = lines[i:i + 30]
                handler_text = "\n".join(handler_lines)
                if not re.search(r'validate|isValid|check|sanitize|z\.|yup|joi|express-validator', handler_text, re.IGNORECASE):
                    errors.append(self._make_error(
                        "Missing Input Validation",
                        f"Route handler at line {i} has no visible input validation. Missing validation can lead to security vulnerabilities.",
                        "High", 80, rel, i, line.find("(") + 1 if "(" in line else 1,
                        line[:120],
                        f"Route handlers without input validation are vulnerable to injection attacks and data corruption.",
                        f"Add validation middleware (e.g., express-validator, zod, joi, yup) or validate inputs explicitly at the start of the handler.",
                        "missing_validation", "",
                        "No input validation in route handler.",
                    ))
                    break

    def _check_mixed_concerns_jsts(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        has_fs = False
        has_http = False
        has_db = False
        for line in lines:
            if re.search(r'(readFileSync|writeFileSync|fs\.|FileReader)', line):
                has_fs = True
            if re.search(r'(fetch|axios\.|http\.|https\.|request\()', line):
                has_http = True
            if re.search(r'(query|find|findAll|findOne|insert|update|delete|save|repository\.)', line):
                has_db = True
        concerns = sum([has_fs, has_http, has_db])
        if concerns >= 2:
            errors.append(self._make_error(
                "Mixed Concerns",
                f"File combines {'I/O, ' if has_fs else ''}{'HTTP, ' if has_http else ''}{'database' if has_db else ''} concerns. Mixing responsibilities violates separation of concerns.",
                "Medium", 65, rel, 1, 1, lines[0][:120] if lines else "",
                "Files that mix I/O, HTTP, and database concerns are hard to maintain, test, and understand.",
                "Separate concerns into dedicated layers: API clients in services, I/O in utilities, database in repositories.",
                "mixed_concerns", "", "Combines multiple architectural concerns.",
            ))

    # ── Generic Analysis ──

    def _analyze_generic(self, content: str, rel: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        self._check_complex_conditionals_generic(lines, rel, errors)
        self._check_god_class_generic(lines, rel, errors)
        self._check_tight_coupling_generic(lines, rel, errors)
        return errors

    def _check_complex_conditionals_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        depth = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'(if|else if|elif)\s*[\(]', stripped, re.IGNORECASE):
                depth += 1
            if depth >= 5:
                errors.append(self._make_error(
                    "Complex Conditional Logic",
                    f"If-else nesting depth of {depth} at line {i}. Deep conditionals are hard to understand.",
                    "High", 80, rel, i, line.find("(") + 1 if "(" in line else 1,
                    line[:120],
                    f"Deeply nested conditionals create complex code paths.",
                    f"Use guard clauses, early returns, or switch statements to simplify.",
                    "complex_conditional", "",
                    f"Conditional depth: {depth}.",
                ))
                break
            if re.match(r'\s*\}', stripped):
                depth = max(0, depth - 1)

    def _check_god_class_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        class_count = 0
        method_count = 0
        class_name = ""
        in_class = False
        brace_count = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'(class|interface)\s+\w+', stripped, re.IGNORECASE):
                if in_class and method_count > 15:
                    errors.append(self._make_error(
                        "God Class",
                        f"Class '{class_name}' has {method_count} methods. Too many methods violate single responsibility.",
                        "Medium", 75, rel, i, 1, line[:120],
                        "Class with many methods handles too many responsibilities.",
                        "Split into smaller focused classes.",
                        "god_class", "",
                        f"{method_count} methods.",
                    ))
                class_name = stripped.split()[1] if len(stripped.split()) > 1 else ""
                method_count = 0
                in_class = True
                brace_count = stripped.count("{") - stripped.count("}")
            elif in_class:
                brace_count += stripped.count("{") - stripped.count("}")
                if re.match(r'\s*(public|private|protected|def|function)\s+\w+\s*\(', stripped, re.IGNORECASE):
                    method_count += 1
                if brace_count <= 0 and not stripped.startswith("}"):
                    in_class = False
        if in_class and method_count > 15:
            errors.append(self._make_error(
                "God Class",
                f"Class '{class_name}' has {method_count} methods.",
                "Medium", 75, rel, len(lines), 1,
                lines[-1][:120] if lines else "",
                "Class with many methods handles too many responsibilities.",
                "Split into smaller focused classes.",
                "god_class", "",
                f"{method_count} methods.",
            ))

    def _check_tight_coupling_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        imports = 0
        for line in lines:
            if re.match(r'^\s*(import|use|include|require)\s', line.strip(), re.IGNORECASE):
                imports += 1
        if imports > 20:
            errors.append(self._make_error(
                "Tight Coupling",
                f"File has {imports} import/include statements. High coupling makes code hard to maintain.",
                "Medium", 65, rel, 1, 1, lines[0][:120] if lines else "",
                f"Importing from {imports} modules creates high coupling.",
                "Reduce coupling by consolidating related imports into facades.",
                "tight_coupling", "",
                f"{imports} import statements.",
            ))

    # ── Helpers ──

    def _if_depth(self, node: ast.If, current: int) -> int:
        max_depth = current + 1
        for child in ast.walk(node):
            if isinstance(child, ast.If) and child is not node:
                inner = self._if_depth(child, current + 1)
                if inner > max_depth:
                    max_depth = inner
        return max_depth

    def _find_parent_func(self, tree: ast.Module, target: ast.AST) -> str | None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if child is target:
                        return node.name
        return None

    def _make_error(self, title: str, desc: str, severity: str, confidence: int,
                    rel: str, line: int, col: int, snippet: str,
                    explanation: str, fix: str, error_type: str,
                    func_name: str, impact_scope: str) -> dict:
        return {
            "bug_title": title,
            "description": desc,
            "severity": severity,
            "confidence": confidence,
            "language": "",
            "affected_file": rel,
            "line_number": line,
            "column_number": col,
            "code_snippet": snippet,
            "ai_explanation": explanation,
            "suggested_fix": fix,
            "error_type": error_type,
            "function_name": func_name,
            "architecture_category": error_type,
            "impact_scope": impact_scope,
        }

    def _snippet(self, lines: list[str], line_num: int, ctx: int = 1) -> str:
        start = max(0, line_num - 1 - ctx)
        end = min(len(lines), line_num + ctx)
        return "\n".join(
            f"{'>' if i == line_num - 1 else ' '} {lines[i]}"
            for i in range(start, end)
        )

    def _deduplicate(self, errors: list[dict]) -> list[dict]:
        seen = set()
        unique: list[dict] = []
        for e in errors:
            key = (e["bug_title"], e["line_number"], e["affected_file"])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    def _calc_health(self, errors: list[dict]) -> float:
        penalty = 0.0
        for e in errors:
            s = e["severity"]
            if s == "Critical":
                penalty += 15
            elif s == "High":
                penalty += 10
            elif s == "Medium":
                penalty += 5
            else:
                penalty += 2
        return max(0.0, 100.0 - penalty)

    def _empty_result(self) -> dict:
        return {
            "session_id": uuid.uuid4().hex,
            "status": "unavailable",
            "total_errors": 0, "total_files_scanned": 0, "files_with_errors": 0,
            "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0,
            "results": [], "scanned_languages": [],
        }
