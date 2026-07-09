import ast
import os
import re
import uuid
from pathlib import Path

from app.detection.detector import EXTENSION_LANGUAGE_MAP
from app.repositories.syntax_detection_engine import IGNORED_DIRS, SUPPORTED_LANGUAGES
from app.repositories.syntax_detection_engine import LANG_FILE_PATTERNS


class RuntimeDetectionEngine:

    def analyze(self, workspace_path: Path | None = None) -> dict:
        if not workspace_path or not workspace_path.exists():
            return self._empty_result()

        language_map = self._detect_languages(workspace_path)
        scanned_languages = list(language_map.keys())
        all_results: list[dict] = []
        total_errors = 0
        files_with_errors = 0
        critical = high = medium = low = 0

        for lang, patterns in language_map.items():
            for pattern in patterns:
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

    def _analyze_file(self, file_path: Path, language: str, workspace: Path) -> dict:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {
                "file_path": str(file_path.relative_to(workspace)),
                "language": language,
                "errors": [], "error_count": 0, "health_score": 100.0,
            }
        rel = str(file_path.relative_to(workspace))
        lines = content.split("\n")
        errors: list[dict] = []

        if language == "Python":
            errors = self._analyze_python(content, rel, lines)
        elif language in ("JavaScript", "TypeScript"):
            errors = self._analyze_jsts(content, rel, lines, language)
        elif language in ("Java", "C#", "C++", "Go", "PHP", "Ruby"):
            errors = self._analyze_generic(content, rel, lines, language)

        errors = self._deduplicate(errors)
        return {
            "file_path": rel,
            "language": language,
            "errors": errors,
            "error_count": len(errors),
            "health_score": max(0.0, 100.0 - len(errors) * 5.0),
        }

    # ── Python Analysis ──

    def _analyze_python(self, content: str, rel: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return errors

        self._check_infinite_recursion_py(tree, rel, lines, errors)
        self._check_infinite_loops_py(tree, rel, lines, errors)
        self._check_unhandled_exceptions_py(tree, rel, lines, errors)
        self._check_resource_leaks_py(tree, rel, lines, errors)
        self._check_null_ref_risks_py(tree, rel, lines, errors)
        self._check_bare_excepts_py(tree, rel, lines, errors)
        self._check_blocking_in_async_py(tree, rel, lines, errors)
        self._check_memory_leak_risks_py(tree, rel, lines, errors)
        self._check_thread_safety_py(tree, rel, lines, errors)
        self._check_timeout_risks_py(tree, rel, lines, errors)
        self._check_crash_points_py(tree, rel, lines, errors)
        return errors

    def _check_infinite_recursion_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                name = node.name
                calls_self = False
                has_return = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == name:
                        calls_self = True
                    elif isinstance(child, ast.Return):
                        has_return = True
                if calls_self and not has_return:
                    errors.append(self._make_error(
                        "Infinite Recursion Risk",
                        f"Function '{name}()' calls itself recursively but has no return statement as base case.",
                        "Critical", 85, rel, node.lineno, node.col_offset,
                        self._snippet(lines, node.lineno),
                        f"The function '{name}()' recursively calls itself without a return base case, which will cause a RecursionError at runtime.",
                        f"Add a proper base case with a return statement to stop the recursion.",
                        "runtime", name, "May cause RecursionError and stack overflow at runtime.",
                    ))

    def _check_infinite_loops_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.While, ast.For)):
                if isinstance(node, ast.While):
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        has_break = any(isinstance(c, ast.Break) for c in ast.walk(node))
                        if not has_break:
                            errors.append(self._make_error(
                                "Infinite Loop Risk",
                                f"'while True' at line {node.lineno} has no break statement and may run forever.",
                                "High", 90, rel, node.lineno, node.col_offset,
                                self._snippet(lines, node.lineno),
                                f"A 'while True' loop without a break statement will run indefinitely, potentially freezing the application.",
                                f"Add a break condition inside the loop or use a conditional while loop.",
                                "runtime", "", "May cause application freeze and unresponsive UI.",
                            ))

    def _check_unhandled_exceptions_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        dangerous = {"open", "eval", "exec", "compile", "json.loads", "int", "float", "input"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = f"{node.func.value.id}.{node.func.attr}" if isinstance(node.func.value, ast.Name) else ""
                if func_name in dangerous:
                    parent = self._find_parent_try(tree, node)
                    if parent is None:
                        errors.append(self._make_error(
                            "Unhandled Exception",
                            f"Call to '{func_name}()' at line {node.lineno} can raise an exception but is not wrapped in a try/except block.",
                            "High", 85, rel, node.lineno, node.col_offset,
                            self._snippet(lines, node.lineno),
                            f"The function '{func_name}()' can raise exceptions (e.g., ValueError, FileNotFoundError) at runtime but has no error handling.",
                            f"Wrap the call in a try/except block to handle potential exceptions gracefully.",
                            "runtime", "", f"Call to '{func_name}()' may crash if input is invalid.",
                        ))

    def _check_resource_leaks_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                parent = self._find_parent_try(tree, node)
                if parent is None:
                    errors.append(self._make_error(
                        "Resource Leak Risk",
                        f"File opened with open() at line {node.lineno} without using a context manager (with statement) or explicit close().",
                        "High", 85, rel, node.lineno, node.col_offset,
                        self._snippet(lines, node.lineno),
                        f"Opening a file without a context manager ('with open()') or explicit .close() call may cause file handle leaks.",
                        f"Use 'with open() as f:' to ensure the file is properly closed even if an error occurs.",
                        "runtime", "", "File handles may leak, causing 'too many open files' errors.",
                    ))

    def _check_null_ref_risks_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                returns_none = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is None:
                        returns_none = True
                    elif isinstance(child, ast.Return) and child.value is not None:
                        pass
                if node.name.startswith("get_") and returns_none:
                    errors.append(self._make_error(
                        "Possible Null Reference",
                        f"Function '{node.name}()' may return None but callers may not check for it.",
                        "Medium", 70, rel, node.lineno, node.col_offset,
                        self._snippet(lines, node.lineno),
                        f"The function '{node.name}()' can return None, which may lead to AttributeError if callers access attributes on the result without checking.",
                        f"Either raise an exception instead of returning None, or document the None return and add null checks at call sites.",
                        "runtime", node.name, "AttributeError when accessing methods on None result.",
                    ))

    def _check_bare_excepts_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                errors.append(self._make_error(
                    "Invalid Exception Handling",
                    f"Bare 'except:' at line {node.lineno} catches ALL exceptions, including SystemExit and KeyboardInterrupt.",
                    "High", 90, rel, node.lineno, node.col_offset or 0,
                    self._snippet(lines, node.lineno),
                    f"A bare 'except:' clause catches every exception type including SystemExit and KeyboardInterrupt, making debugging difficult and potentially masking critical errors.",
                    f"Replace with 'except Exception:' or catch specific exception types. Avoid bare except clauses.",
                    "runtime", "", "Masked errors and suppressed crash signals make debugging difficult.",
                ))

    def _check_blocking_in_async_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        async_funcs: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_funcs[node.name] = node.lineno

        blocking_calls = {"time.sleep", "requests.get", "requests.post",
                          "subprocess.run", "subprocess.call", "os.system"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    func_name = f"{node.func.value.id}.{node.func.attr}"
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                if func_name in blocking_calls:
                    parent_func = self._find_parent_func(tree, node)
                    if parent_func and parent_func in async_funcs:
                        errors.append(self._make_error(
                            "Blocking Operation in Async Code",
                            f"Blocking call '{func_name}()' at line {node.lineno} inside async function '{parent_func}()'.",
                            "High", 85, rel, node.lineno, node.col_offset or 0,
                            self._snippet(lines, node.lineno),
                            f"The blocking call '{func_name}()' inside an async function will block the event loop, negating the benefits of async concurrency.",
                            f"Use async alternatives (e.g., asyncio.sleep() instead of time.sleep(), aiohttp instead of requests).",
                            "runtime", parent_func, "Blocking the event loop degrades async performance and may timeout other tasks.",
                        ))

    def _check_memory_leak_risks_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                growing_append = 0
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "append":
                        growing_append += 1
                if growing_append > 10:
                    errors.append(self._make_error(
                        "Memory Leak Risk",
                        f"Function '{node.name}()' has {growing_append} list append operations, which may grow unbounded.",
                        "Medium", 65, rel, node.lineno, node.col_offset,
                        self._snippet(lines, node.lineno),
                        f"The function '{node.name}()' appends to lists many times without any corresponding removal. If called repeatedly, this may cause unbounded memory growth.",
                        f"Consider using fixed-size data structures, setting a maximum size, or using deque with maxlen.",
                        "runtime", node.name, "Unbounded list growth may lead to MemoryError over time.",
                    ))

    def _check_thread_safety_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        uses_threading = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if any("threading" in (alias.name if isinstance(alias, ast.alias) else "") for alias in (node.names if isinstance(node, (ast.Import, ast.ImportFrom)) else [])):
                    uses_threading = True

        if uses_threading:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "start" and isinstance(child.func.value, ast.Attribute) and "Thread" in child.func.value.attr:
                            errors.append(self._make_error(
                                "Thread Safety Risk",
                                f"Thread started in '{node.name}()' without visible lock or synchronization.",
                                "Medium", 60, rel, node.lineno, node.col_offset or 0,
                                self._snippet(lines, node.lineno),
                                f"Starting a thread without visible synchronization may lead to race conditions and data corruption.",
                                f"Use threading.Lock or queue.Queue to safely share data between threads.",
                                "runtime", node.name, "Race conditions may cause data corruption and intermittent crashes.",
                            ))
                            break

    def _check_timeout_risks_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                if func_name in ("get", "post", "put", "delete", "request", "urlopen"):
                    has_timeout = False
                    for kw in node.keywords if hasattr(node, "keywords") else []:
                        if kw.arg == "timeout":
                            has_timeout = True
                            break
                    if not has_timeout:
                        parent = self._find_parent_func(tree, node) or ""
                        errors.append(self._make_error(
                            "Timeout Risk",
                            f"Network call '{func_name}()' at line {node.lineno} without a timeout parameter.",
                            "High", 80, rel, node.lineno, node.col_offset or 0,
                            self._snippet(lines, node.lineno),
                            f"The network call '{func_name}()' does not specify a timeout and may hang indefinitely if the remote server is unresponsive.",
                            f"Add a timeout parameter (e.g., timeout=10) to prevent indefinite blocking.",
                            "runtime", parent, "Network calls may hang indefinitely, freezing the application.",
                        ))

    def _check_crash_points_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name == "eval":
                    parent = self._find_parent_func(tree, node) or ""
                    errors.append(self._make_error(
                        "Potential Crash Point",
                        f"Use of eval() at line {node.lineno} can execute arbitrary code and crash the application.",
                        "Critical", 95, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"The eval() function executes arbitrary Python code and can crash the application with any exception, or worse, be exploited for code injection.",
                        f"Avoid eval() entirely. Use ast.literal_eval() for safe evaluation of literal expressions.",
                        "runtime", parent, "Arbitrary code execution and application crash risk.",
                    ))

    # ── JS/TS Analysis ──

    def _analyze_jsts(self, content: str, rel: str, lines: list[str], lang: str) -> list[dict]:
        errors: list[dict] = []
        self._check_infinite_loops_jsts(content, rel, lines, errors)
        self._check_unhandled_promises_jsts(content, rel, lines, errors)
        self._check_async_await_misuse_jsts(content, rel, lines, errors)
        self._check_null_ref_jsts(content, rel, lines, errors)
        self._check_blocking_async_jsts(content, rel, lines, errors)
        self._check_timeout_risks_jsts(content, rel, lines, errors)
        self._check_crash_points_jsts(content, rel, lines, errors)
        self._check_resource_leaks_jsts(content, rel, lines, errors)
        self._check_bare_catch_jsts(content, rel, lines, errors)
        return errors

    def _check_infinite_loops_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'while\s*\(\s*true\s*\)', stripped, re.IGNORECASE):
                body_start = i
                body_end = min(i + 30, len(lines))
                body = "\n".join(lines[i:body_end])
                if "break" not in body:
                    errors.append(self._make_error(
                        "Infinite Loop Risk",
                        f"'while (true)' at line {i} has no break statement and may run forever.",
                        "High", 90, rel, i, line.find("while") + 1,
                        self._snippet_for_line(lines, i),
                        f"A 'while (true)' loop without a break statement will run indefinitely, potentially freezing the application.",
                        f"Add a break condition inside the loop or use a conditional while expression.",
                        "runtime", "", "May cause application freeze and unresponsive UI.",
                    ))

    def _check_unhandled_promises_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'\.then\s*\(', line) and not re.search(r'\.catch\s*\(', line) and not re.search(r'await\b', line):
                next_lines = "\n".join(lines[i:i + 15])
                if ".catch(" not in next_lines and "catch(" not in next_lines:
                    errors.append(self._make_error(
                        "Unhandled Promise Rejection",
                        f"Promise on line {i} has a .then() but no .catch() handler.",
                        "High", 85, rel, i, line.find(".then") + 1,
                        self._snippet_for_line(lines, i),
                        f"A Promise with a .then() handler but no .catch() will cause an unhandled promise rejection if the promise fails.",
                        f"Add a .catch() handler to handle promise rejections, or use async/await with try/catch.",
                        "runtime", "", "Unhandled promise rejections may crash Node.js processes.",
                    ))

    def _check_async_await_misuse_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if "async" in line and "function" in line:
                body_start = i
                body = "\n".join(lines[i:min(i + 50, len(lines))])
                has_await = "await " in body
                if not has_await:
                    errors.append(self._make_error(
                        "Async/Await Misuse",
                        f"Async function declared at line {i} but contains no await expression.",
                        "Medium", 80, rel, i, line.find("async") + 1,
                        self._snippet_for_line(lines, i),
                        f"An async function that never uses 'await' does not need to be async and may mislead callers into expecting async behavior.",
                        f"Remove the 'async' keyword if the function does not perform async operations, or add proper await calls.",
                        "runtime", "", "Misleading async declarations may cause incorrect error handling assumptions.",
                    ))

    def _check_null_ref_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'\b(get|find|fetch)\w*\s*\(', line, re.IGNORECASE) and "?" not in line:
                if re.search(r'\b(get|find|fetch)\w*\s*\(\)', line, re.IGNORECASE):
                    errors.append(self._make_error(
                        "Possible Null Reference",
                        f"Call to getter function at line {i} may return null/undefined but result is not checked with optional chaining.",
                        "Medium", 65, rel, i, line.find("(") + 1,
                        self._snippet_for_line(lines, i),
                        f"Getter functions like get(), find(), fetch() may return null/undefined. Accessing properties on the result without optional chaining (?.) may cause TypeError.",
                        f"Use optional chaining (result?.property) or add a null check before accessing properties.",
                        "runtime", "", "TypeError: Cannot read properties of null/undefined.",
                    ))
                    break

    def _check_blocking_async_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if "async" in line and "function" in line:
                body = "\n".join(lines[i:min(i + 40, len(lines))])
                if "require(" in body or "readFileSync" in body or "writeFileSync" in body or "execSync" in body:
                    errors.append(self._make_error(
                        "Blocking Operation in Async Code",
                        f"Blocking synchronous call found in async function at line {i}.",
                        "High", 85, rel, i, 1,
                        self._snippet_for_line(lines, i),
                        f"Synchronous calls inside async functions block the event loop, negating the benefits of asynchronous execution.",
                        f"Replace synchronous calls with their async alternatives (e.g., fs.promises.readFile instead of fs.readFileSync).",
                        "runtime", "", "Blocking the event loop reduces application throughput and responsiveness.",
                    ))
                    break

    def _check_timeout_risks_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'\b(fetch|axios\.get|axios\.post|request)\s*\(', line) and "timeout" not in line:
                next_lines = "\n".join(lines[i:min(i + 5, len(lines))])
                if "timeout" not in next_lines:
                    errors.append(self._make_error(
                        "Timeout Risk",
                        f"Network request at line {i} without a timeout configuration.",
                        "High", 80, rel, i, line.find("(") + 1,
                        self._snippet_for_line(lines, i),
                        f"A network request without a timeout may hang indefinitely if the server is slow or unresponsive.",
                        "Add a timeout option to the request (e.g., fetch(url, { signal: AbortSignal.timeout(5000) }), axios.get(url, { timeout: 5000 })).",
                        "runtime", "", "Network requests may hang indefinitely, freezing the application.",
                    ))

    def _check_crash_points_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if "JSON.parse" in line:
                body = "\n".join(lines[i:min(i + 5, len(lines))])
                if "try" not in body and "catch" not in body:
                    errors.append(self._make_error(
                        "Potential Crash Point",
                        f"JSON.parse() at line {i} without try/catch will crash on invalid JSON.",
                        "Critical", 90, rel, i, line.find("JSON.parse") + 1,
                        self._snippet_for_line(lines, i),
                        f"JSON.parse() throws an exception if the input is not valid JSON. Without try/catch, invalid input will crash the application.",
                        f"Wrap JSON.parse() in a try/catch block or use a safe parsing function.",
                        "runtime", "", "Application crashes on malformed JSON input.",
                    ))

    def _check_resource_leaks_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'(createReadStream|createWriteStream|open\(|createConnection)', line):
                body = "\n".join(lines[i:min(i + 15, len(lines))])
                if ".close" not in body and ".destroy" not in body and "destroy" not in body:
                    errors.append(self._make_error(
                        "Resource Leak Risk",
                        f"Stream/connection opened at line {i} without visible close/destroy handling.",
                        "High", 75, rel, i, line.find("(") + 1,
                        self._snippet_for_line(lines, i),
                        f"A stream or connection was opened but no close() or destroy() call is visible in the surrounding code. This may cause resource leaks.",
                        f"Ensure streams are properly closed using .close() or .destroy(), or use pipe with 'end' option.",
                        "runtime", "", "File handles and connections may leak, causing resource exhaustion.",
                    ))

    def _check_bare_catch_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.match(r'\s*\}\s*catch\s*\(?\s*(e|err|error)\s*\)?\s*\{', line, re.IGNORECASE):
                body = "\n".join(lines[i:min(i + 5, len(lines))])
                if not body.strip() or body.strip() in ("{}", "{ }", "{", "}"):
                    errors.append(self._make_error(
                        "Invalid Exception Handling",
                        f"Empty catch block at line {i} silently swallows exceptions.",
                        "High", 90, rel, i, 1,
                        self._snippet_for_line(lines, i),
                        f"An empty catch block silently swallows all exceptions, making debugging extremely difficult.",
                        f"Log the error, handle it appropriately, or at minimum re-throw it. Never leave empty catch blocks.",
                        "runtime", "", "Silent error suppression makes debugging impossible.",
                    ))
                    break

    # ── Generic Analysis ──

    def _analyze_generic(self, content: str, rel: str, lines: list[str], lang: str) -> list[dict]:
        errors: list[dict] = []
        self._check_infinite_loops_generic(lines, rel, errors)
        self._check_null_ref_generic(lines, rel, errors, lang)
        self._check_resource_leaks_generic(lines, rel, errors)
        self._check_crash_points_generic(lines, rel, errors)
        return errors

    def _check_infinite_loops_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'while\s*\(\s*(true|1)\s*\)', stripped, re.IGNORECASE):
                body = "\n".join(lines[i:min(i + 30, len(lines))])
                if "break" not in body:
                    errors.append(self._make_error(
                        "Infinite Loop Risk",
                        f"'while (true)' at line {i} has no break statement.",
                        "High", 90, rel, i, line.find("while") + 1,
                        self._snippet_for_line(lines, i),
                        f"A 'while (true)' loop without a break statement will run indefinitely.",
                        f"Add a break condition inside the loop.",
                        "runtime", "", "May cause application freeze.",
                    ))

    def _check_null_ref_generic(self, lines: list[str], rel: str, errors: list[dict], lang: str) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'(get\w*|find\w*)\(', line) and "null" in line:
                errors.append(self._make_error(
                    "Possible Null Reference",
                    f"Getter call at line {i} may return null.",
                    "Medium", 60, rel, i, line.find("(") + 1,
                    self._snippet_for_line(lines, i),
                    f"Functions that may return null should have their results checked before use.",
                    f"Add a null check before accessing properties on the result.",
                    "runtime", "", "NullPointerException risk.",
                ))
                break

    def _check_resource_leaks_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'(new\s+(File(Input|Output)Stream|Socket|ServerSocket|HttpURLConnection))', line):
                body = "\n".join(lines[i:min(i + 15, len(lines))])
                if ".close" not in body:
                    errors.append(self._make_error(
                        "Resource Leak Risk",
                        f"Resource opened at line {i} without visible .close() call.",
                        "High", 75, rel, i, line.find("new") + 1,
                        self._snippet_for_line(lines, i),
                        f"A system resource was allocated without a corresponding close() call in the surrounding code.",
                        f"Use try-with-resources (Java) or ensure close() is called in a finally block.",
                        "runtime", "", "Resource handles may leak, causing system resource exhaustion.",
                    ))
                    break

    def _check_crash_points_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if "parseInt" in line or "Integer.parseInt" in line:
                body = "\n".join(lines[i:min(i + 5, len(lines))])
                if "try" not in body and "catch" not in body:
                    errors.append(self._make_error(
                        "Potential Crash Point",
                        f"parseInt at line {i} without try/catch may crash on invalid input.",
                        "High", 85, rel, i, line.find("parseInt") + 1,
                        self._snippet_for_line(lines, i),
                        f"Parsing functions like parseInt throw NumberFormatException on invalid input. Without handling, unparseable input crashes the application.",
                        f"Wrap the parse call in a try/catch or validate the input before parsing.",
                        "runtime", "", "Application crashes on invalid numeric input.",
                    ))
                    break

    # ── Helpers ──

    def _find_parent_try(self, tree: ast.Module, target: ast.AST) -> ast.ExceptHandler | None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    for child in ast.walk(handler):
                        if child is target:
                            return handler
        return None

    def _find_parent_func(self, tree: ast.Module, target: ast.AST) -> str | None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if child is target:
                        return node.name
        return None

    def _make_error(self, title: str, desc: str, severity: str, confidence: int,
                    rel: str, line: int, col: int, snippet: str,
                    explanation: str, fix: str, error_type: str, func_name: str,
                    possible_impact: str) -> dict:
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
            "possible_impact": possible_impact,
        }

    def _snippet(self, lines: list[str], line_num: int, ctx: int = 1) -> str:
        start = max(0, line_num - 1 - ctx)
        end = min(len(lines), line_num + ctx)
        return "\n".join(
            f"{'>' if i == line_num - 1 else ' '} {lines[i]}"
            for i in range(start, end)
        )

    def _snippet_for_line(self, lines: list[str], line_num: int) -> str:
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1][:100]
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

    def _empty_result(self) -> dict:
        return {
            "session_id": uuid.uuid4().hex,
            "status": "unavailable",
            "total_errors": 0, "total_files_scanned": 0, "files_with_errors": 0,
            "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0,
            "results": [], "scanned_languages": [],
        }
