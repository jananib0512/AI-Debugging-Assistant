import ast
import os
import re
import uuid
from pathlib import Path

from app.detection.detector import EXTENSION_LANGUAGE_MAP
from app.repositories.syntax_detection_engine import IGNORED_DIRS, SUPPORTED_LANGUAGES


class PerformanceDetectionEngine:

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
            errors = self._analyze_jsts(content, rel, lines)
        elif language in ("Java", "C#", "C++", "Go", "PHP", "Ruby"):
            errors = self._analyze_generic(content, rel, lines)

        errors = self._deduplicate(errors)
        return {
            "file_path": rel,
            "language": language,
            "errors": errors,
            "error_count": len(errors),
            "health_score": max(0.0, 100.0 - len(errors) * 5.0),
        }

    # ── Python AST Analysis ──

    def _analyze_python(self, content: str, rel: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return errors

        self._check_nested_loops_py(tree, rel, lines, errors)
        self._check_large_loops_py(tree, rel, lines, errors)
        self._check_repeated_computation_py(tree, rel, lines, errors)
        self._check_blocking_ops_py(tree, rel, lines, errors)
        self._check_slow_queries_py(tree, rel, lines, errors)
        self._check_excessive_logging_py(tree, rel, lines, errors)
        self._check_expensive_file_ops_py(tree, rel, lines, errors)
        self._check_inefficient_data_structures_py(tree, rel, lines, errors)
        self._check_memory_usage_py(tree, rel, lines, errors)
        self._check_scalability_py(tree, rel, lines, errors)
        return errors

    def _check_nested_loops_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                depth = self._loop_depth(tree, node)
                if depth >= 3:
                    func = self._find_parent_func(tree, node) or ""
                    errors.append(self._make_error(
                        "Deeply Nested Loops",
                        f"Loop nesting depth of {depth} detected at line {node.lineno}. O(n^{depth}) complexity may cause performance issues.",
                        "High", 85, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Nested loops at depth {depth} result in O(n^{depth}) time complexity. For large datasets, this can cause severe performance degradation.",
                        f"Consider flattening the loop structure, using dictionaries/sets for lookups, or using NumPy for vectorized operations.",
                        "performance", "nested_loops", func,
                        f"O(n^{depth}) time complexity — may not scale beyond small inputs.",
                    ))

    def _check_large_loops_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
                func_name = ""
                if isinstance(node.iter.func, ast.Name):
                    func_name = node.iter.func.id
                if func_name == "range" and node.iter.args:
                    arg = node.iter.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, int) and arg.value > 10000:
                        func = self._find_parent_func(tree, node) or ""
                        errors.append(self._make_error(
                            "Large Loop Iteration",
                            f"Loop iterates over range({arg.value}) at line {node.lineno}, processing {arg.value} items.",
                            "Medium", 70, rel, node.lineno, node.col_offset or 0,
                            self._snippet(lines, node.lineno),
                            f"Loop iterates {arg.value} times. If the operation inside is expensive, this can be a significant bottleneck.",
                            f"Consider using batch processing, pagination, or vectorized operations to reduce iteration count.",
                            "performance", "large_loop", func,
                            f"May process {arg.value} items sequentially.",
                        ))

    def _check_repeated_computation_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                computations: dict[str, list[int]] = {}
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        cname = ""
                        if isinstance(child.func, ast.Attribute):
                            cname = f"{child.func.attr}"
                        elif isinstance(child.func, ast.Name):
                            cname = child.func.id
                        if cname:
                            computations.setdefault(cname, []).append(child.lineno or 0)
                for cname, lines_found in computations.items():
                    if len(lines_found) > 3:
                        func = self._find_parent_func(tree, node) or ""
                        errors.append(self._make_error(
                            "Repeated Computation in Loop",
                            f"Function '{cname}()' called {len(lines_found)} times inside the same loop at line {node.lineno}.",
                            "Medium", 75, rel, node.lineno, node.col_offset or 0,
                            self._snippet(lines, node.lineno),
                            f"The function '{cname}()' is called {len(lines_found)} times inside a loop. This can often be optimized by moving the call outside the loop or caching results.",
                            f"Hoist the '{cname}()' call outside the loop if its result is invariant, or cache repeated calls with lru_cache.",
                            "performance", "repeated_computation", func,
                            f"Unnecessary repeated computation inside loop body.",
                        ))

    def _check_blocking_ops_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        blocking = {"time.sleep", "requests.get", "requests.post", "subprocess.run",
                     "subprocess.call", "os.system", "subprocess.check_output"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    func_name = f"{node.func.value.id}.{node.func.attr}"
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id
                if func_name in blocking:
                    parent = self._find_parent_func(tree, node) or ""
                    errors.append(self._make_error(
                        "Blocking Operation",
                        f"Blocking call '{func_name}()' at line {node.lineno} can block execution and degrade performance.",
                        "High", 80, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"The blocking call '{func_name}()' pauses execution until completion. In concurrent or async contexts, this blocks the entire thread.",
                        f"Use async alternatives (asyncio, aiohttp) or move blocking work to a thread pool executor.",
                        "performance", "blocking_op", parent,
                        "Thread-blocking operation degrades throughput and responsiveness.",
                    ))

    def _check_slow_queries_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = f"{node.func.attr}"
                if func_name in ("filter", "all", "get", "first"):
                    parent = self._find_parent_func(tree, node) or ""
                    if parent:
                        errors.append(self._make_error(
                            "Potential Slow Database Query",
                            f"Database query '{func_name}()' at line {node.lineno} without visible filtering/limiting — may scan full table.",
                            "Medium", 65, rel, node.lineno, node.col_offset or 0,
                            self._snippet(lines, node.lineno),
                            f"Queries using '{func_name}()' without a filter may scan all rows in the table, causing high latency for large datasets.",
                            f"Add filter conditions, limit rows, and ensure proper database indexes are created on filtered columns.",
                            "performance", "slow_query", parent,
                            "Full table scan may cause high latency for large datasets.",
                        ))
                        break

    def _check_excessive_logging_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                log_count = 0
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        cname = ""
                        if isinstance(child.func, ast.Attribute):
                            cname = f"{child.func.attr}"
                        if cname in ("info", "debug", "log", "warn", "error"):
                            log_count += 1
                if log_count > 2:
                    func = self._find_parent_func(tree, node) or ""
                    errors.append(self._make_error(
                        "Excessive Logging in Loop",
                        f"Logging statement called inside a loop at line {node.lineno} — {log_count} log calls found. May cause performance overhead.",
                        "Low", 65, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Calling logging functions inside loops adds significant I/O overhead. For high-iteration loops, this can slow execution considerably.",
                        f"Move log statements outside the loop or use conditional logging (e.g., log every Nth iteration).",
                        "performance", "excessive_logging", func,
                        "Logging I/O overhead inside hot loops.",
                    ))
                    break

    def _check_expensive_file_ops_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                if func_name == "open":
                    parent = self._find_parent_func(tree, node) or ""
                    errors.append(self._make_error(
                        "Expensive File Operation",
                        f"File open() at line {node.lineno} inside function '{parent}' — file I/O is slow and should not be in hot paths.",
                        "Medium", 70, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"File I/O operations are orders of magnitude slower than in-memory operations. Opening files inside frequently-called functions can be a major bottleneck.",
                        f"Read files once and cache contents in memory, or use memory-mapped files for large datasets.",
                        "performance", "file_io", parent,
                        "File I/O is ~1000x slower than memory access.",
                    ))
                    break

    def _check_inefficient_data_structures_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                in_check = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "count":
                        in_check = True
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "index":
                        in_check = True
                if in_check:
                    func = self._find_parent_func(tree, node) or ""
                    errors.append(self._make_error(
                        "Inefficient Data Structure",
                        f"List .count() or .index() inside loop at line {node.lineno} — O(n²) complexity.",
                        "High", 80, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Calling .count() or .index() on a list inside a loop results in O(n²) complexity. For large lists, this can be extremely slow.",
                        f"Use a dictionary or Counter for counting operations. Use a set or dict for membership tests and lookups.",
                        "performance", "inefficient_structure", func,
                        "O(n²) complexity due to linear search inside loop.",
                    ))
                    break

    def _check_memory_usage_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "read":
                parent = self._find_parent_func(tree, node) or ""
                errors.append(self._make_error(
                    "High Memory Usage",
                    f"File .read() at line {node.lineno} loads entire file into memory. May cause MemoryError for large files.",
                    "High", 80, rel, node.lineno, node.col_offset or 0,
                    self._snippet(lines, node.lineno),
                    f"Calling .read() on a file loads its entire contents into RAM. For large files (>100MB), this can exhaust available memory.",
                    f"Use .readline() for line-by-line processing, or .read(chunk_size) for chunked reading. Use memory-mapped files for very large data.",
                    "performance", "memory_usage", parent,
                    "May load entire file into RAM causing MemoryError.",
                ))
                break

    def _check_scalability_py(self, tree: ast.Module, rel: str, lines: list[str], errors: list[dict]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                num_loops = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.For, ast.While)):
                        num_loops += 1
                if num_loops > 5:
                    errors.append(self._make_error(
                        "Potential Scalability Risk",
                        f"Function '{node.name}()' contains {num_loops} loops. High complexity may not scale well under load.",
                        "Medium", 65, rel, node.lineno, node.col_offset or 0,
                        self._snippet(lines, node.lineno),
                        f"Functions with many loops often perform bulk data processing and can become bottlenecks under high load.",
                        f"Break the function into smaller units, consider batch processing, or use async parallel execution.",
                        "performance", "scalability", node.name,
                        f"High loop count ({num_loops}) may impact scalability under load.",
                    ))

    # ── JS/TS Analysis ──

    def _analyze_jsts(self, content: str, rel: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        self._check_nested_loops_jsts(content, rel, lines, errors)
        self._check_large_loops_jsts(content, rel, lines, errors)
        self._check_repeated_api_jsts(content, rel, lines, errors)
        self._check_blocking_jsts(content, rel, lines, errors)
        self._check_excessive_logging_jsts(lines, rel, errors)
        self._check_expensive_computation_jsts(lines, rel, errors)
        return errors

    def _check_nested_loops_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        stack = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'(for|while|forEach|map|filter|reduce)\s*[\( ]', stripped):
                stack += 1
            if stack >= 3:
                errors.append(self._make_error(
                    "Deeply Nested Loops",
                    f"Loop nesting of depth ≥3 detected at line {i}. O(n³) complexity may cause severe performance issues.",
                    "High", 80, rel, i, line.find("(") + 1 if "(" in line else 1,
                    self._snippet_for_line(lines, i),
                    f"Deeply nested loops and iterations result in O(n^depth) complexity, causing slowdowns with larger datasets.",
                    f"Consider using flat data structures, lookup tables, or Promise.all for parallel execution.",
                    "performance", "nested_loops", "",
                    "O(n³) complexity degrades exponentially with input size.",
                ))
                break
            if re.match(r'\s*\}', stripped):
                stack = max(0, stack - 1)

    def _check_large_loops_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'for\s*\(\s*(let|var|const)\s+\w+\s*=\s*\d+\s*;\s*\w+\s*[<>=]+\s*(\d{4,})\s*;', line):
                limit = re.search(r'[<>=]+\s*(\d{4,})', line)
                if limit:
                    val = limit.group(1)
                    errors.append(self._make_error(
                        "Large Loop Iteration",
                        f"Loop at line {i} iterates {val} times. May cause performance issues with large datasets.",
                        "Medium", 70, rel, i, line.find("(") + 1,
                        self._snippet_for_line(lines, i),
                        f"Loop iterating {val} times can be a bottleneck if the loop body contains expensive operations.",
                        f"Consider batch processing, pagination, or using Web Workers for parallel processing.",
                        "performance", "large_loop", "",
                        f"High iteration count ({val}).",
                    ))
                    break

    def _check_repeated_api_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        api_calls: dict[str, list[int]] = {}
        for i, line in enumerate(lines, 1):
            m = re.findall(r'(fetch|axios|axios\.get|axios\.post|axios\.put|api\.get|api\.post)\s*\(', line)
            for call in m:
                api_calls.setdefault(call, []).append(i)
        for call, locs in api_calls.items():
            if len(locs) > 3:
                errors.append(self._make_error(
                    "Repeated API Calls",
                    f"'{call}' called {len(locs)} times in the same file (lines: {locs[:5]}...). May cause excessive network requests.",
                    "Medium", 70, rel, locs[0], 1,
                    self._snippet_for_line(lines, locs[0]),
                    f"Multiple network API calls can be batched into fewer requests, reducing latency and server load.",
                    f"Batch API requests, use GraphQL, or implement request deduplication/caching.",
                    "performance", "repeated_api", "",
                    "Excessive network requests increase latency and server load.",
                ))
                break

    def _check_blocking_jsts(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'(readFileSync|writeFileSync|execSync|execFileSync)', line):
                errors.append(self._make_error(
                    "Blocking Operation",
                    f"Synchronous I/O at line {i} blocks the Node.js event loop and degrades performance.",
                    "High", 85, rel, i, line.find("Sync") + 1 if "Sync" in line else 1,
                    self._snippet_for_line(lines, i),
                    f"Synchronous I/O operations block the event loop, preventing Node.js from handling other requests during the operation.",
                    f"Use async alternatives: fs.promises.readFile, fs.promises.writeFile, or use worker threads for CPU-intensive tasks.",
                    "performance", "blocking_op", "",
                    "Blocks the event loop, reducing throughput significantly.",
                ))
                break

    def _check_excessive_logging_jsts(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        log_count = 0
        for i, line in enumerate(lines, 1):
            if re.search(r'console\.(log|info|debug|warn|error)\s*\(', line):
                log_count += 1
        if log_count > 10:
            errors.append(self._make_error(
                "Excessive Logging",
                f"File contains {log_count} console.log statements. Excessive logging can impact performance.",
                "Low", 60, rel, 1, 1,
                self._snippet_for_line(lines, 1),
                f"Excessive console logging in production can impact performance and clutter log files.",
                f"Remove debug logging, use a logging library with configurable levels, or limit logging in production builds.",
                "performance", "excessive_logging", "",
                "Logging overhead impacts performance in production.",
            ))

    def _check_expensive_computation_jsts(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'sort\(.*\)\s*\.\s*sort\(', line):
                errors.append(self._make_error(
                    "Expensive Computation",
                    f"Chained sort() operations at line {i} — sorting is O(n log n) and doing it twice is wasteful.",
                    "Medium", 75, rel, i, line.find("sort") + 1,
                    self._snippet_for_line(lines, i),
                    f"Calling sort() multiple times on the same or related data performs redundant sorting operations.",
                    f"Sort once and reuse the sorted result. Consider using a balanced BST or heap if maintaining order.",
                    "performance", "expensive_computation", "",
                    "Redundant O(n log n) sorting operations.",
                ))
                break

    # ── Generic Analysis ──

    def _analyze_generic(self, content: str, rel: str, lines: list[str]) -> list[dict]:
        errors: list[dict] = []
        self._check_nested_loops_generic(lines, rel, errors)
        self._check_expensive_computation_generic(lines, rel, errors)
        self._check_scalability_generic(lines, rel, errors)
        return errors

    def _check_nested_loops_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        depth = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'(for|while|foreach)\s*[\(]', stripped, re.IGNORECASE):
                depth += 1
            if depth >= 3:
                errors.append(self._make_error(
                    "Deeply Nested Loops",
                    f"Loop nesting depth ≥3 at line {i}. High computational complexity.",
                    "High", 80, rel, i, line.find("(") + 1 if "(" in line else 1,
                    self._snippet_for_line(lines, i),
                    f"Deeply nested loops result in O(n^depth) time complexity.",
                    f"Flatten nested loops or use hash-based lookups to reduce complexity.",
                    "performance", "nested_loops", "",
                    "O(n³) complexity.",
                ))
                break
            if re.match(r'\s*\}', stripped):
                depth = max(0, depth - 1)

    def _check_expensive_computation_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        for i, line in enumerate(lines, 1):
            if re.search(r'(sort|sortBy|orderBy)\s*\(.*\)\s*\.\s*(sort|sortBy|orderBy)', line, re.IGNORECASE):
                errors.append(self._make_error(
                    "Expensive Computation",
                    f"Multiple sort operations at line {i}. Sorting is O(n log n) — chaining is wasteful.",
                    "Medium", 70, rel, i, line.find("sort") + 1,
                    self._snippet_for_line(lines, i),
                    f"Chained sort operations perform redundant computation. Sorting is an O(n log n) operation.",
                    f"Sort once and cache the result.",
                    "performance", "expensive_computation", "",
                    "Redundant O(n log n) operations.",
                ))
                break

    def _check_scalability_generic(self, lines: list[str], rel: str, errors: list[dict]) -> None:
        loop_count = 0
        for line in lines:
            if re.match(r'\s*(for|while|foreach)\s*[\(]', line.strip(), re.IGNORECASE):
                loop_count += 1
        if loop_count > 8:
            errors.append(self._make_error(
                "Potential Scalability Risk",
                f"File contains {loop_count} loops. High complexity may not scale well under load.",
                "Medium", 60, rel, 1, 1,
                self._snippet_for_line(lines, 1),
                f"Files with many loops often perform bulk processing and may become bottlenecks under load.",
                f"Consider breaking into smaller functions, batch processing, or parallel execution.",
                "performance", "scalability", "",
                f"High loop count ({loop_count}) may affect scalability.",
            ))

    # ── Helpers ──

    def _loop_depth(self, tree: ast.Module, node: ast.AST, max_depth: int = 0) -> int:
        depth = 0
        current = node
        while current:
            if isinstance(current, (ast.For, ast.While)):
                depth += 1
            current = getattr(current, "parent", None) or getattr(current, "ctx", None)
        ancestors = self._find_ancestors(tree, node)
        return sum(1 for a in ancestors if isinstance(a, (ast.For, ast.While)))

    def _find_ancestors(self, tree: ast.Module, target: ast.AST) -> list[ast.AST]:
        ancestors: list[ast.AST] = []
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child is target:
                    ancestors.append(node)
                    ancestors.extend(self._find_ancestors(tree, node))
                    return ancestors
        return []

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
                    perf_category: str, func_name: str,
                    estimated_cost: str) -> dict:
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
            "performance_category": perf_category,
            "estimated_cost": estimated_cost,
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
            return lines[line_num - 1][:120]
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
