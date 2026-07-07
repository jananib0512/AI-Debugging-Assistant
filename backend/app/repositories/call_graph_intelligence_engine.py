import ast
import os
import re
from collections import defaultdict, deque
from pathlib import Path

from app.repositories.source_code_intelligence_engine import (
    IGNORED_DIRS,
    IGNORED_FILES,
    EXTENSION_LANGUAGE_MAP,
    SUPPORTED_EXTENSIONS,
)

ENTRY_POINT_PATTERNS = {
    "Python": [
        r'if\s+__name__\s*==\s*["\']__main__["\']',
        r'app\.run\s*\(',
        r'uvicorn\.run\s*\(',
        r'FastAPI\s*\(',
        r'@\w+\.(get|post|put|delete|patch|route)\s*\(',
        r'@app\.(before_request|after_request|teardown_request)',
        r'@\w+\.(cli|command)\s*\(',
        r'celery\s*=\s*Celery\s*\(',
        r'@celery\.(task|periodic_task)',
        r'def\s+main\s*\(',
        r'click\.(command|group)\s*\(',
        r'@click\.(command|group)',
        r'argparse\.ArgumentParser\s*\(',
        r'APScheduler',
        r'rq\.Worker',
        r'threading\.Thread\s*\(',
        r'asyncio\.run\s*\(',
    ],
    "JavaScript": [
        r'app\.(get|post|put|delete|patch|use|listen)\s*\(',
        r'router\.(get|post|put|delete|patch|use)\s*\(',
        r'express\s*\(',
        r'module\.exports\s*=',
        r'export\s+default',
        r'export\s+function',
        r'process\.on\s*\(',
        r'addEventListener\s*\(',
        r'window\.onload',
        r'listen\s*\(',
    ],
    "TypeScript": [
        r'app\.(get|post|put|delete|patch|use|listen)\s*\(',
        r'router\.(get|post|put|delete|patch|use)\s*\(',
        r'@(Get|Post|Put|Delete|Patch|Route)\s*\(',
        r'@Controller\s*\(',
        r'@Injectable\s*\(',
        r'NestFactory\.create\s*\(',
        r'export\s+(default\s+)?(class|function)',
        r'process\.on\s*\(',
        r'addEventListener\s*\(',
    ],
    "Java": [
        r'public\s+static\s+void\s+main\s*\(',
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(',
        r'@Controller\s*\(',
        r'@RestController\s*\(',
        r'@Service\s*\(',
        r'@Repository\s*\(',
        r'@Component\s*\(',
        r'@SpringBootApplication',
        r'SpringApplication\.run\s*\(',
        r'Application\.run\s*\(',
    ],
}

FRAMEWORK_PATTERNS = {
    "Python": {
        "FastAPI": [r"FastAPI", r"@app\.(get|post|put|delete)", r"uvicorn"],
        "Flask": [r"Flask", r"@app\.route", r"flask"],
        "Django": [r"django", r"urlpatterns", r"views\.", r"path\("],
        "Celery": [r"Celery", r"@celery\.task", r"celery"],
        "Click": [r"click\.(command|group)", r"@click"],
        "SQLAlchemy": [r"sqlalchemy", r"declarative_base", r"sessionmaker"],
    },
    "JavaScript": {
        "Express": [r"express", r"app\.(get|post|put|delete)", r"router\."],
        "React": [r"React", r"useState", r"useEffect", r"createElement"],
        "Node": [r"require\(", r"module\.exports", r"process\.argv"],
    },
    "TypeScript": {
        "NestJS": [r"NestFactory", r"@Module", r"@Controller", r"@Injectable"],
        "Express": [r"express", r"app\.(get|post|put|delete)"],
        "Angular": [r"@Component", r"@NgModule", r"@Injectable"],
    },
    "Java": {
        "Spring Boot": [r"@SpringBootApplication", r"SpringApplication"],
        "Spring MVC": [r"@Controller", r"@RequestMapping", r"@GetMapping"],
        "Spring Data": [r"@Repository", r"JpaRepository", r"CrudRepository"],
    },
}


def _compute_cyclomatic_complexity_ast(node) -> int:
    c = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            c += 1
        elif isinstance(child, ast.Try):
            c += len(child.handlers)
        elif isinstance(child, ast.ExceptHandler):
            c += 1
        elif isinstance(child, ast.BoolOp) and isinstance(child.op, (ast.And, ast.Or)):
            c += len(child.values) - 1
        elif isinstance(child, ast.Assert):
            c += 1
        elif isinstance(child, ast.Match):
            c += len(child.cases)
    return c


class CallGraphIntelligenceEngine:

    def analyze(self, workspace_path: Path) -> dict:
        nodes_map: dict[str, dict] = {}
        edges_list: list[dict] = []
        file_imports: dict[str, list[str]] = defaultdict(list)
        all_defined: dict[str, dict] = {}
        all_called: dict[str, set[str]] = defaultdict(set)
        entry_point_ids: set[str] = set()
        entry_point_nodes: list[dict] = []
        call_sites: dict[str, list[dict]] = defaultdict(list)
        file_language_map: dict[str, str] = {}
        module_map: dict[str, str] = {}
        language_breakdown: dict[str, int] = defaultdict(int)
        node_type_counts: dict[str, int] = defaultdict(int)
        node_id_to_file: dict[str, str] = {}

        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in files:
                if f.lower() in IGNORED_FILES:
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                file_path = os.path.join(root, f)
                language = EXTENSION_LANGUAGE_MAP[ext]
                rel_path = os.path.relpath(file_path, workspace_path).replace("\\", "/")
                file_language_map[rel_path] = language
                module = rel_path.replace("/", ".").rsplit(".", 1)[0] if "." in rel_path else rel_path
                module_map[rel_path] = module

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                except (OSError, UnicodeDecodeError):
                    continue

                lines = content.split("\n")
                language_breakdown[language] += 1

                if language == "Python":
                    self._process_python(content, lines, rel_path, f, language, module,
                                         nodes_map, edges_list, file_imports, all_defined,
                                         all_called, entry_point_ids, entry_point_nodes,
                                         call_sites, node_id_to_file, node_type_counts,
                                         file_language_map)
                else:
                    self._process_non_python(lines, rel_path, f, language, module,
                                             nodes_map, edges_list, file_imports, all_defined,
                                             all_called, entry_point_ids, entry_point_nodes,
                                             call_sites, node_id_to_file, node_type_counts,
                                             file_language_map)

        self._build_cross_references(nodes_map, edges_list, all_called, all_defined)

        self._detect_dead_functions(nodes_map, edges_list, entry_point_ids)

        self._detect_recursive_loops(nodes_map, edges_list)

        flows = self._build_execution_flows(nodes_map, edges_list, entry_point_ids, file_language_map,
                                             file_imports, all_defined, all_called, node_id_to_file, module_map)

        circular = self._detect_circular_calls(edges_list)

        unused = [n["id"] for n in nodes_map.values() if n.get("is_dead") and not n.get("is_entry_point") and not n.get("is_library")]

        orphan_methods = self._detect_orphan_methods(nodes_map, edges_list)

        broken_paths = self._detect_broken_paths(nodes_map, edges_list, entry_point_ids, flows)

        issues_list = self._generate_issues(nodes_map, edges_list, flows, circular, unused, orphan_methods, broken_paths)

        ai_insights = self._generate_ai_insights(nodes_map, edges_list, flows, issues_list, entry_point_ids, unused)

        stats = self._compute_stats(nodes_map, edges_list, entry_point_ids, flows, issues_list,
                                    unused, language_breakdown, node_type_counts)

        return {
            "nodes": list(nodes_map.values()),
            "edges": edges_list,
            "execution_flows": flows,
            "entry_points": entry_point_nodes,
            "stats": stats,
            "issues": issues_list,
            "ai_insights": ai_insights,
        }

    def _process_python(self, content: str, lines: list[str], rel_path: str, file_name: str,
                        language: str, module: str, nodes_map: dict, edges_list: list,
                        file_imports: dict, all_defined: dict, all_called: dict,
                        entry_point_ids: set, entry_point_nodes: list,
                        call_sites: dict, node_id_to_file: dict, node_type_counts: dict,
                        file_language_map: dict):
        try:
            tree = ast.parse(content)
        except SyntaxError:
            self._process_non_python(lines, rel_path, file_name, language, module,
                                     nodes_map, edges_list, file_imports, all_defined,
                                     all_called, entry_point_ids, entry_point_nodes,
                                     call_sites, node_id_to_file, node_type_counts)
            return

        content_str = content

        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                for alias in node.names:
                    if base:
                        imports.append(f"{base}.{alias.name}")
                    else:
                        imports.append(alias.name)
        file_imports[rel_path] = imports

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_id = f"{module}.{node.name}"
                is_async = isinstance(node, ast.AsyncFunctionDef)
                complexity = _compute_cyclomatic_complexity_ast(node)
                ntype = "method" if any(isinstance(p, ast.ClassDef) for p in ast.walk(tree) if
                                         isinstance(p, ast.ClassDef) and node in p.body) else "function"
                if func_id not in nodes_map:
                    nodes_map[func_id] = self._make_node(func_id, node.name, ntype, rel_path,
                                                         module, language, node.lineno, complexity,
                                                         is_async=is_async)
                    node_id_to_file[func_id] = rel_path
                    node_type_counts[ntype] += 1
                all_defined[func_id] = nodes_map[func_id]

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        self._record_call(child, func_id, rel_path, module, lines, edges_list,
                                          call_sites, imports, nodes_map, node_id_to_file,
                                          file_language_map=file_language_map,
                                          file_imports=file_imports)

            elif isinstance(node, ast.ClassDef):
                cls_id = f"{module}.{node.name}"
                if cls_id not in nodes_map:
                    cls_complexity = 0
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            cls_complexity += _compute_cyclomatic_complexity_ast(item)
                    nodes_map[cls_id] = self._make_node(cls_id, node.name, "class", rel_path,
                                                        module, language, node.lineno,
                                                        max(cls_complexity, 1))
                    node_id_to_file[cls_id] = rel_path
                    node_type_counts["class"] += 1

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{cls_id}.{item.name}"
                        is_async = isinstance(item, ast.AsyncFunctionDef)
                        method_complexity = _compute_cyclomatic_complexity_ast(item)
                        if method_id not in nodes_map:
                            nodes_map[method_id] = self._make_node(method_id, item.name, "method",
                                                                   rel_path, module, language,
                                                                   item.lineno, method_complexity,
                                                                   is_async=is_async,
                                                                   parent_class=node.name)
                            node_id_to_file[method_id] = rel_path
                            node_type_counts["method"] += 1
                        all_defined[method_id] = nodes_map[method_id]

                        for child in ast.walk(item):
                            if isinstance(child, ast.Call):
                                self._record_call(child, method_id, rel_path, module, lines,
                                                  edges_list, call_sites, imports, nodes_map,
                                                  node_id_to_file, file_language_map=file_language_map,
                                                  file_imports=file_imports)

        self._detect_entry_points_python(content_str, rel_path, module, nodes_map, entry_point_ids,
                                         entry_point_nodes, node_type_counts, file_imports[rel_path])

    def _process_non_python(self, lines: list[str], rel_path: str, file_name: str,
                            language: str, module: str, nodes_map: dict, edges_list: list,
                            file_imports: dict, all_defined: dict, all_called: dict,
                            entry_point_ids: set, entry_point_nodes: list,
                            call_sites: dict, node_id_to_file: dict, node_type_counts: dict,
                            file_language_map: dict):
        content_str = "\n".join(lines)
        flavor = "jslike" if language in ("JavaScript", "TypeScript") else "java" if language == "Java" else "other"

        imports: list[str] = []
        if flavor == "jslike":
            for m in re.finditer(r'(?:import\s+[\w{}*,\s]+\s+from\s+["\']([^"\']+)["\'])|(?:require\s*\(\s*["\']([^"\']+)["\']\s*\))', content_str):
                imp = m.group(1) or m.group(2)
                if imp:
                    imports.append(imp)
        elif flavor == "java":
            for m in re.finditer(r'import\s+([\w.]+)\s*;', content_str):
                imports.append(m.group(1))
        file_imports[rel_path] = imports

        inside_multiline = False
        for i, raw in enumerate(lines):
            stripped = raw.strip()
            if not stripped:
                continue
            if flavor == "jslike":
                if stripped.startswith("/*"):
                    inside_multiline = True
                    continue
                if inside_multiline:
                    if "*/" in stripped:
                        inside_multiline = False
                    continue
                if stripped.startswith("//"):
                    continue
            line_before_comment = stripped.split("//")[0].strip() if flavor != "other" else stripped.split("#")[0].strip()
            if not line_before_comment:
                continue

            # Function detection
            fn_match = None
            for pat in [
                r"(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
                r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
            ]:
                fn_match = re.search(pat, line_before_comment)
                if fn_match:
                    break

            if fn_match and "function" in line_before_comment:
                name = fn_match.group(1)
                func_id = f"{module}.{name}"
                if func_id not in nodes_map:
                    nodes_map[func_id] = self._make_node(func_id, name, "function", rel_path,
                                                         module, language, i + 1, 1)
                    node_id_to_file[func_id] = rel_path
                    node_type_counts["function"] += 1
                all_defined[func_id] = nodes_map[func_id]

                for token in re.findall(r'\b([a-zA-Z_]\w*)\s*\(', line_before_comment.split("function")[-1]):
                    if token not in ("if", "elif", "else", "while", "for", "switch", "catch", "with", "return", "throw", "typeof", "delete", "void", "new"):
                        target_id = self._resolve_call_target(token, rel_path, module, imports, file_imports)
                        if target_id and target_id not in nodes_map:
                            nodes_map[target_id] = self._make_node(target_id, token, "function", rel_path,
                                                                   module, language, i + 1, 0,
                                                                   is_library=self._is_library_call(token, imports))
                            node_type_counts["function"] += 1
                        if target_id:
                            edges_list.append(self._make_edge(func_id, target_id, "direct", rel_path, i + 1))
                            all_called[func_id].add(target_id)

            # Class detection
            cm = re.search(r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)", line_before_comment)
            if cm and not fn_match:
                cls_name = cm.group(1)
                cls_id = f"{module}.{cls_name}"
                if cls_id not in nodes_map:
                    nodes_map[cls_id] = self._make_node(cls_id, cls_name, "class", rel_path,
                                                        module, language, i + 1, 1)
                    node_id_to_file[cls_id] = rel_path
                    node_type_counts["class"] += 1

                # Detect methods
                for j in range(i + 1, min(i + 200, len(lines))):
                    method_line = lines[j].strip()
                    method_match = re.search(r"(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*{", method_line)
                    if method_match:
                        method_name = method_match.group(1)
                        if method_name not in ("if", "while", "for", "switch", "catch"):
                            method_id = f"{cls_id}.{method_name}"
                            if method_id not in nodes_map:
                                nodes_map[method_id] = self._make_node(method_id, method_name, "method",
                                                                       rel_path, module, language,
                                                                       j + 1, 1)
                                node_id_to_file[method_id] = rel_path
                                node_type_counts["method"] += 1
                            all_defined[method_id] = nodes_map[method_id]

                    brace_diff = lines[j].count("{") - lines[j].count("}")
                    if brace_diff <= 0 and j > i + 1:
                        break

        self._detect_entry_points_non_python(content_str, rel_path, language, module, nodes_map,
                                              entry_point_ids, entry_point_nodes, node_type_counts)

    def _record_call(self, call_node, caller_id: str, file_path: str, module: str, lines: list,
                     edges_list: list, call_sites: dict, imports: list, nodes_map: dict,
                     node_id_to_file: dict, file_language_map: dict,
                     file_imports: dict | None = None):
        callee_name = None
        if isinstance(call_node.func, ast.Name):
            callee_name = call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            callee_name = call_node.func.attr

        if callee_name is None or callee_name in ("print", "len", "str", "int", "float", "bool",
                                                    "list", "dict", "tuple", "set", "type", "isinstance",
                                                    "hasattr", "getattr", "setattr", "range", "enumerate",
                                                    "zip", "map", "filter", "sorted", "reversed", "open",
                                                    "super", "property", "staticmethod", "classmethod"):
            return

        fi = file_imports if file_imports is not None else {}
        target_id = self._resolve_call_target(callee_name, file_path, module, imports, fi)
        if target_id is None:
            return

        if target_id not in nodes_map:
            is_lib = self._is_library_call(callee_name, imports)
            nodes_map[target_id] = self._make_node(target_id, callee_name, "function", file_path,
                                                   module, "Python", call_node.lineno, 0,
                                                   is_library=is_lib)

        is_recursive = (target_id == caller_id)
        edges_list.append(self._make_edge(caller_id, target_id, "direct", file_path,
                                          call_node.lineno, is_recursive=is_recursive))
        call_sites[caller_id].append({"target": target_id, "line": call_node.lineno})

    def _resolve_call_target(self, name: str, file_path: str, module: str,
                              imports: list[str], file_imports: dict) -> str | None:
        if not name or name.startswith("_") and name != "__init__":
            return None

        local_target = f"{module}.{name}"
        if os.path.isfile(os.path.join(os.path.dirname(file_path) if file_path else "",
                                        name.lower() + ".py")):
            return local_target

        for imp in imports:
            if imp.endswith(f".{name}") or imp == name:
                return imp
            if imp.endswith(f".{name}"):
                return imp

        for imp in imports:
            parts = imp.split(".")
            if parts[-1] == name:
                return imp

        return local_target

    def _is_library_call(self, name: str, imports: list[str]) -> bool:
        if name in ("print", "len", "str", "int", "float", "bool"):
            return True
        for imp in imports:
            if imp.split(".")[0] == name:
                return True
            if imp.endswith(f".{name}"):
                return True
        return False

    def _make_node(self, node_id: str, name: str, ntype: str, file_path: str,
                    module: str, language: str, line_number: int, complexity: int,
                    is_async: bool = False, parent_class: str = "",
                    is_library: bool = False, is_framework: bool = False) -> dict:
        return {
            "id": node_id,
            "name": name,
            "type": ntype,
            "file_path": file_path,
            "module": module,
            "language": language,
            "line_number": line_number,
            "complexity": complexity,
            "maintainability": 100.0 - min(complexity * 2, 60) if complexity > 0 else 100.0,
            "call_depth": 0,
            "is_entry_point": False,
            "is_recursive": False,
            "is_dead": False,
            "is_library": is_library,
            "is_framework": is_framework,
        }

    def _make_edge(self, source: str, target: str, call_type: str, file_path: str,
                    line_number: int, is_recursive: bool = False) -> dict:
        return {
            "source": source,
            "target": target,
            "call_type": call_type,
            "call_count": 1,
            "is_cross_file": False,
            "is_cross_module": False,
            "is_recursive": is_recursive,
            "is_library": False,
            "file_path": file_path,
            "line_number": line_number,
        }

    def _detect_entry_points_python(self, content: str, rel_path: str, module: str,
                                     nodes_map: dict, entry_point_ids: set,
                                     entry_point_nodes: list, node_type_counts: dict,
                                     imports: list[str]):
        patterns = ENTRY_POINT_PATTERNS.get("Python", [])
        for pat in patterns:
            for m in re.finditer(pat, content):
                ep_id = f"{module}.entry_point"
                if "def " in m.group():
                    func_match = re.search(r"def\s+(\w+)\s*\(", content[m.start():m.end() + 50])
                    if func_match:
                        ep_id = f"{module}.{func_match.group(1)}"
                    else:
                        ep_id = f"{module}._entry_point_{len(entry_point_ids)}"
                elif "app." in m.group():
                    route_match = re.search(r"@\w+\.(get|post|put|delete|patch|route)\s*\(\s*['\"]([^'\"]+)['\"]", content[m.start() - 100:m.end() + 10])
                    if route_match:
                        ep_name = f"route_{route_match.group(2).replace('/', '_')}"
                        ep_id = f"{module}.{ep_name}"

                if ep_id not in nodes_map:
                    ep_name = ep_id.split(".")[-1]
                    nodes_map[ep_id] = self._make_node(ep_id, ep_name, "entry_point", rel_path,
                                                       module, "Python", 0, 0)
                    node_type_counts["entry_point"] += 1
                nodes_map[ep_id]["is_entry_point"] = True
                entry_point_ids.add(ep_id)
                if nodes_map[ep_id] not in entry_point_nodes:
                    entry_point_nodes.append(nodes_map[ep_id])

    def _detect_entry_points_non_python(self, content: str, rel_path: str, language: str,
                                         module: str, nodes_map: dict, entry_point_ids: set,
                                         entry_point_nodes: list, node_type_counts: dict):
        patterns = ENTRY_POINT_PATTERNS.get(language, [])
        for pat in patterns:
            for m in re.finditer(pat, content):
                ep_id = f"{module}.entry_point_{len(entry_point_ids)}"
                if m.group() and "function" in m.group():
                    func_match = re.search(r"function\s+(\w+)", content[m.start():m.end() + 50])
                    if func_match:
                        ep_id = f"{module}.{func_match.group(1)}"

                if ep_id not in nodes_map:
                    ep_name = ep_id.split(".")[-1]
                    nodes_map[ep_id] = self._make_node(ep_id, ep_name, "entry_point", rel_path,
                                                       module, language, 0, 0)
                    node_type_counts["entry_point"] += 1
                nodes_map[ep_id]["is_entry_point"] = True
                entry_point_ids.add(ep_id)
                if nodes_map[ep_id] not in entry_point_nodes:
                    entry_point_nodes.append(nodes_map[ep_id])

    def _build_cross_references(self, nodes_map: dict, edges_list: list,
                                 all_called: dict, all_defined: dict):
        for edge in edges_list:
            s = edge["source"]
            t = edge["target"]
            if s in nodes_map and t in nodes_map:
                src_file = nodes_map[s].get("file_path", "")
                tgt_file = nodes_map[t].get("file_path", "")
                edge["is_cross_file"] = bool(src_file and tgt_file and src_file != tgt_file)
                src_module = nodes_map[s].get("module", "")
                tgt_module = nodes_map[t].get("module", "")
                edge["is_cross_module"] = bool(src_module and tgt_module and src_module != tgt_module)
                edge["is_library"] = nodes_map[t].get("is_library", False)

        for node_id, node in nodes_map.items():
            outgoing = [e for e in edges_list if e["source"] == node_id]
            incoming = [e for e in edges_list if e["target"] == node_id]
            node["call_depth"] = max(len(outgoing), len(incoming)) if outgoing or incoming else 0
            node["is_dead"] = len(incoming) == 0 and not node.get("is_entry_point") and not node.get("is_library")

    def _detect_dead_functions(self, nodes_map: dict, edges_list: list, entry_point_ids: set):
        reachable = set(entry_point_ids)
        queue = deque(entry_point_ids)
        while queue:
            current = queue.popleft()
            for edge in edges_list:
                if edge["source"] == current and edge["target"] not in reachable:
                    reachable.add(edge["target"])
                    queue.append(edge["target"])
        for node_id, node in nodes_map.items():
            if node_id not in reachable and not node.get("is_entry_point") and not node.get("is_library"):
                node["is_dead"] = True

    def _detect_recursive_loops(self, nodes_map: dict, edges_list: list):
        for edge in edges_list:
            if edge["is_recursive"]:
                continue
            source = edge["source"]
            target = edge["target"]
            # Check if there's a path back from target to source
            visited = set()
            queue = deque([target])
            while queue:
                current = queue.popleft()
                if current == source:
                    edge["is_recursive"] = True
                    if source in nodes_map:
                        nodes_map[source]["is_recursive"] = True
                    break
                if current in visited:
                    continue
                visited.add(current)
                for e in edges_list:
                    if e["source"] == current and e["target"] not in visited:
                        queue.append(e["target"])

    def _detect_circular_calls(self, edges_list: list) -> list[list[str]]:
        adj: dict[str, list[str]] = defaultdict(list)
        for e in edges_list:
            adj[e["source"]].append(e["target"])

        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        parent: dict[str, str] = {}

        def dfs(u: str, path: list[str]):
            visited.add(u)
            rec_stack.add(u)
            for v in adj.get(u, []):
                if v not in visited:
                    parent[v] = u
                    dfs(v, path + [v])
                elif v in rec_stack:
                    cycle = []
                    cur = u
                    while cur != v:
                        cycle.append(cur)
                        cur = parent.get(cur, "")
                    cycle.append(v)
                    cycle.reverse()
                    if len(cycle) > 1 and cycle not in cycles:
                        cycles.append(cycle)
            rec_stack.discard(u)

        for node in list(adj.keys()):
            if node not in visited:
                parent[node] = ""
                dfs(node, [node])

        return cycles

    def _build_execution_flows(self, nodes_map: dict, edges_list: list,
                                entry_point_ids: set, file_language_map: dict,
                                file_imports: dict, all_defined: dict,
                                all_called: dict, node_id_to_file: dict,
                                module_map: dict) -> list[dict]:
        flows: list[dict] = []
        visited_flows: set[str] = set()

        adj: dict[str, list[str]] = defaultdict(list)
        reverse_adj: dict[str, list[str]] = defaultdict(list)
        for e in edges_list:
            adj[e["source"]].append(e["target"])
            reverse_adj[e["target"]].append(e["source"])

        # 1. Entry point DFS flows (existing)
        for ep in entry_point_ids:
            if ep not in nodes_map:
                continue
            paths = self._dfs_paths(ep, adj, max_depth=20, max_paths=8)
            for path_nodes in paths:
                if len(path_nodes) < 2:
                    continue
                flow = self._make_flow(path_nodes, nodes_map, edges_list, ep, flows)
                if flow:
                    key = "->".join(flow["path"])
                    if key not in visited_flows:
                        visited_flows.add(key)
                        flows.append(flow)

        # 2. Architectural flows: Controller → Service → Repository
        arch_flows = self._detect_architectural_flows(nodes_map, edges_list, file_language_map, node_id_to_file)
        for flow in arch_flows:
            key = "->".join(flow["path"])
            if key not in visited_flows:
                visited_flows.add(key)
                flows.append(flow)

        # 3. Business flows from naming patterns
        biz_flows = self._detect_business_flows_from_naming(nodes_map, edges_list, file_language_map, node_id_to_file)
        for flow in biz_flows:
            key = "->".join(flow["path"])
            if key not in visited_flows:
                visited_flows.add(key)
                flows.append(flow)

        # 4. Import-chain flows
        import_flows = self._detect_import_flows(nodes_map, file_imports, module_map, node_id_to_file)
        for flow in import_flows:
            key = "->".join(flow["path"])
            if key not in visited_flows:
                visited_flows.add(key)
                flows.append(flow)

        # 5. File-module flow chains
        file_flows = self._detect_file_based_flows(nodes_map, file_language_map, node_id_to_file, entry_point_ids)
        for flow in file_flows:
            key = "->".join(flow["path"])
            if key not in visited_flows:
                visited_flows.add(key)
                flows.append(flow)

        return flows

    def _make_flow(self, path_nodes: list[str], nodes_map: dict,
                    edges_list: list, ep: str, existing_flows: list) -> dict | None:
        if len(path_nodes) < 2:
            return None
        flow_type = self._classify_flow(nodes_map, ep, path_nodes)
        exit_node = path_nodes[-1] if path_nodes else ep

        flow_name = self._generate_flow_name(path_nodes, nodes_map, flow_type)

        flow_issues: list[str] = []
        if len(path_nodes) > 12:
            flow_issues.append("Deep execution chain")

        is_complete = True
        last_outgoing = [e for e in edges_list if e["source"] == exit_node]
        if last_outgoing:
            is_complete = False
            flow_issues.append("Path may be incomplete")

        return {
            "id": f"flow_{len(existing_flows)}",
            "name": flow_name,
            "description": f"{flow_type.replace('_', ' ').title()} execution: {' → '.join(nodes_map.get(n, {}).get('name', n) for n in path_nodes[:8])}",
            "flow_type": flow_type,
            "entry_node": ep,
            "exit_node": exit_node,
            "path": path_nodes,
            "depth": len(path_nodes),
            "is_complete": is_complete,
            "issues": flow_issues,
        }

    def _generate_flow_name(self, path: list[str], nodes_map: dict, flow_type: str) -> str:
        type_labels = {
            "api": "API Request",
            "authentication": "Authentication",
            "authorization": "Authorization",
            "forecast": "Forecast Pipeline",
            "ml": "ML Pipeline",
            "pipeline": "Data Pipeline",
            "database": "Database",
            "background": "Background Job",
            "scheduled": "Scheduled Task",
            "upload": "Dataset Upload",
            "validation": "Data Validation",
            "eda": "EDA",
            "preprocessing": "Preprocessing",
            "forecast_generation": "Forecast Generation",
            "comparison": "Comparison",
            "report": "Report Generation",
            "main": "Application Startup",
            "framework": "Framework Startup",
            "request": "Request Flow",
            "controller": "Controller",
            "service": "Service",
            "repository": "Repository",
            "response": "Response",
            "cli": "CLI Command",
        }
        base = type_labels.get(flow_type, f"{flow_type.replace('_', ' ').title()} Flow")

        entry_name = nodes_map.get(path[0], {}).get("name", "")
        exit_name = nodes_map.get(path[-1], {}).get("name", "")
        if entry_name and exit_name:
            return f"{base}: {entry_name} → {exit_name}"
        return base

    def _dfs_paths(self, start: str, adj: dict[str, list[str]],
                    max_depth: int, max_paths: int) -> list[list[str]]:
        paths: list[list[str]] = []
        visited_in_path: set[str] = set()

        def dfs(current: str, path: list[str]):
            if len(path) > max_depth:
                return
            if len(paths) >= max_paths:
                return
            if current in visited_in_path:
                paths.append(path + [current])
                return
            visited_in_path.add(current)
            neighbors = adj.get(current, [])
            if not neighbors:
                paths.append(path[:])
                visited_in_path.discard(current)
                return
            for neighbor in neighbors:
                dfs(neighbor, path + [neighbor])
            visited_in_path.discard(current)

        dfs(start, [start])
        return paths

    def _classify_flow(self, nodes_map: dict, ep_id: str, path: list[str]) -> str:
        ep_node = nodes_map.get(ep_id, {})
        ep_name = ep_node.get("name", "").lower()
        ep_file = ep_node.get("file_path", "").lower()
        ep_module = ep_node.get("module", "").lower()

        path_names = [nodes_map.get(n, {}).get("name", "").lower() for n in path]
        path_files = [nodes_map.get(n, {}).get("file_path", "").lower() for n in path]
        combined_names = " ".join(path_names)
        combined_files = " ".join(path_files)

        text = f"{ep_name} {ep_file} {ep_module} {combined_names} {combined_files}"

        if any(kw in text for kw in ("forecast", "predict", "projection", "forecasting")):
            return "forecast"
        if any(kw in text for kw in ("pipeline", "etl", "data_pipeline")):
            return "pipeline"
        if any(kw in text for kw in ("train", "model", "ml_", "tensorflow", "torch", "sklearn")):
            return "ml"
        if any(kw in text for kw in ("eda", "exploratory", "analysis")):
            return "eda"
        if any(kw in text for kw in ("preprocess", "pre_process", "feature_eng", "normalize", "scale")):
            return "preprocessing"
        if any(kw in text for kw in ("upload", "ingest", "import_file", "receive_file")):
            return "upload"
        if any(kw in text for kw in ("validate", "sanitize", "check_data")):
            return "validation"
        if any(kw in text for kw in ("login", "logout", "signin", "signup", "register", "auth", "authenticate", "oauth")):
            return "authentication"
        if any(kw in text for kw in ("authorize", "permission", "role", "access_control")):
            return "authorization"
        if any(kw in text for kw in ("compare", "comparison", "diff", "delta")):
            return "comparison"
        if any(kw in text for kw in ("report", "generate_report", "summary", "export_report")):
            return "report"
        if any(kw in text for kw in ("forecast_generation", "generate_forecast", "run_forecast")):
            return "forecast_generation"
        if any(kw in text for kw in ("celery", "task", "background", "worker", "thread", "job")):
            return "background"
        if any(kw in text for kw in ("schedule", "cron", "timer", "periodic")):
            return "scheduled"
        if any(kw in text for kw in ("route", "get", "post", "put", "delete", "patch", "api", "endpoint")):
            return "api"
        if any(kw in text for kw in ("controller", "handler")):
            return "controller"
        if any(kw in text for kw in ("service", "business")):
            return "service"
        if any(kw in text for kw in ("repository", "repo", "dao")):
            return "repository"
        if any(kw in text for kw in ("database", "db_", "sql", "query", "mongo", "redis")):
            return "database"
        if any(kw in text for kw in ("response", "render", "return_result")):
            return "response"
        if any(kw in text for kw in ("cli", "command", "argparse", "click", "console")):
            return "cli"
        if any(kw in text for kw in ("main", "run", "start", "bootstrap")):
            return "main"
        if any(kw in text for kw in ("app", "application", "config", "initialize", "setup")):
            return "framework"
        return "request"

    def _detect_architectural_flows(self, nodes_map: dict, edges_list: list,
                                     file_language_map: dict,
                                     node_id_to_file: dict) -> list[dict]:
        flows: list[dict] = []
        file_to_nodes: dict[str, list[str]] = defaultdict(list)
        for nid, node in nodes_map.items():
            fp = node.get("file_path", "")
            if fp:
                file_to_nodes[fp].append(nid)

        controller_nodes: list[str] = []
        service_nodes: list[str] = []
        repository_nodes: list[str] = []
        model_nodes: list[str] = []
        api_nodes: list[str] = []
        middleware_nodes: list[str] = []
        config_nodes: list[str] = []

        for nid, node in nodes_map.items():
            name = node.get("name", "").lower()
            fpath = node.get("file_path", "").lower()
            nt = node.get("type", "")
            text = f"{name} {fpath} {nt}"

            if any(kw in text for kw in ("controller", "handler")):
                controller_nodes.append(nid)
            if any(kw in text for kw in ("service", "business")):
                service_nodes.append(nid)
            if any(kw in text for kw in ("repository", "repo", "dao")):
                repository_nodes.append(nid)
            if any(kw in text for kw in ("model", "entity", "schema")):
                model_nodes.append(nid)
            if any(kw in text for kw in ("route", "api", "endpoint")):
                api_nodes.append(nid)
            if any(kw in text for kw in ("middleware", "pipe", "filter")):
                middleware_nodes.append(nid)
            if any(kw in text for kw in ("config", "setting")):
                config_nodes.append(nid)

        adj: dict[str, set[str]] = defaultdict(set)
        for e in edges_list:
            adj[e["source"]].add(e["target"])

        def build_chain(start_nodes: list[str], type_name: str) -> list[dict]:
            chains: list[dict] = []
            seen: set[str] = set()
            for cn in start_nodes:
                if cn in seen:
                    continue
                seen.add(cn)
                path = [cn]
                current = cn
                depth = 0
                while depth < 15:
                    targets = adj.get(current, set())
                    next_found = None
                    for t in targets:
                        if t in service_nodes:
                            next_found = t
                            break
                        if t in repository_nodes:
                            next_found = t
                            break
                        if t in model_nodes:
                            next_found = t
                            break
                    if next_found and next_found not in seen:
                        seen.add(next_found)
                        path.append(next_found)
                        current = next_found
                        depth += 1
                    else:
                        break

                if len(path) >= 2:
                    flow = self._make_flow(path, nodes_map, edges_list, path[0], flows)
                    if flow:
                        flow["flow_type"] = type_name
                        flow["name"] = f"{type_name.replace('_', ' ').title()} Chain"
                        chains.append(flow)
            return chains

        if controller_nodes:
            flows.extend(build_chain(controller_nodes, "controller"))
        if api_nodes:
            flows.extend(build_chain(api_nodes, "api"))
        if service_nodes:
            service_chains = build_chain(service_nodes, "service")
            for sc in service_chains:
                if sc["path"][0] in service_nodes and sc["depth"] >= 2:
                    flows.append(sc)

        return flows

    def _detect_business_flows_from_naming(self, nodes_map: dict, edges_list: list,
                                            file_language_map: dict,
                                            node_id_to_file: dict) -> list[dict]:
        flows: list[dict] = []
        file_to_nodes: dict[str, list[str]] = defaultdict(list)
        for nid, node in nodes_map.items():
            fp = node.get("file_path", "")
            if fp:
                file_to_nodes[fp].append(nid)

        business_patterns: list[tuple[str, list[str], str]] = [
            ("forecast", ["forecast", "predict", "forecasting", "prediction", "projection"], "forecast"),
            ("ml_pipeline", ["train", "model", "ml_", "tensorflow", "torch", "sklearn", "learn"], "ml"),
            ("eda", ["eda", "exploratory", "analyze_data", "describe"], "eda"),
            ("preprocessing", ["preprocess", "pre_process", "clean_data", "feature_eng", "normalize", "scale", "transform"], "preprocessing"),
            ("authentication", ["login", "logout", "signin", "signup", "register", "auth", "authenticate", "oauth"], "authentication"),
            ("authorization", ["authorize", "permission", "role", "access", "rbac"], "authorization"),
            ("upload", ["upload", "ingest", "import_data", "receive", "file_upload"], "upload"),
            ("validation", ["validate", "sanitize", "check", "verify", "assert"], "validation"),
            ("report", ["report", "summary", "generate_report", "export"], "report"),
            ("comparison", ["compare", "comparison", "diff", "delta", "benchmark"], "comparison"),
            ("database", ["database", "db_", "sql", "query", "mongo", "redis", "connection"], "database"),
            ("background", ["background", "celery", "worker", "task", "async_job", "queue"], "background"),
            ("scheduled", ["schedule", "cron", "timer", "periodic", "recurring"], "scheduled"),
            ("forecast_generation", ["generate_forecast", "run_forecast", "compute_forecast", "produce_forecast"], "forecast_generation"),
            ("data_pipeline", ["pipeline", "etl", "extract", "transform", "load", "process_data"], "pipeline"),
            ("response", ["response", "render", "format_output", "serialize"], "response"),
        ]

        adj: dict[str, set[str]] = defaultdict(set)
        for e in edges_list:
            adj[e["source"]].add(e["target"])
        reverse_adj: dict[str, set[str]] = defaultdict(set)
        for e in edges_list:
            reverse_adj[e["target"]].add(e["source"])

        for pattern_name, keywords, flow_type in business_patterns:
            matched_nodes: list[str] = []
            for nid, node in nodes_map.items():
                name = node.get("name", "").lower()
                fpath = node.get("file_path", "").lower()
                text = f"{name} {fpath}"
                if any(kw in text for kw in keywords):
                    matched_nodes.append(nid)

            if len(matched_nodes) >= 2:
                path: list[str] = []
                seen: set[str] = set()
                for mn in matched_nodes:
                    if mn not in seen:
                        seen.add(mn)
                        path.append(mn)

                if len(path) >= 2:
                    flow = self._make_flow(path, nodes_map, edges_list, path[0], flows)
                    if flow:
                        flow["flow_type"] = flow_type
                        flow["name"] = f"{pattern_name.replace('_', ' ').title()} Pipeline"
                        description_parts = []
                        for p in path:
                            nm = nodes_map.get(p, {}).get("name", p)
                            description_parts.append(nm)
                        flow["description"] = f"{flow['name']}: {' → '.join(description_parts[:6])}"
                        flows.append(flow)

        return flows

    def _detect_import_flows(self, nodes_map: dict, file_imports: dict,
                              module_map: dict, node_id_to_file: dict) -> list[dict]:
        flows: list[dict] = []
        file_to_nodes: dict[str, list[str]] = defaultdict(list)
        for nid, node in nodes_map.items():
            fp = node.get("file_path", "")
            if fp:
                file_to_nodes[fp].append(nid)

        import_adj: dict[str, set[str]] = defaultdict(set)
        for src_path, imports in file_imports.items():
            for imp in imports:
                imp_lower = imp.lower()
                for tgt_path in file_to_nodes:
                    tgt_mod = module_map.get(tgt_path, "")
                    if tgt_mod and tgt_mod.lower() in imp_lower:
                        import_adj[src_path].add(tgt_path)
                    if tgt_path.replace("/", ".").rsplit(".", 1)[0].lower() in imp_lower:
                        import_adj[src_path].add(tgt_path)

        visited_paths: set[str] = set()
        for src_path in list(import_adj.keys()):
            if src_path not in file_to_nodes:
                continue
            chain_paths = self._dfs_paths_str(src_path, import_adj, max_depth=10, max_paths=3)
            for p in chain_paths:
                if len(p) < 2:
                    continue
                key = "->".join(p)
                if key in visited_paths:
                    continue
                visited_paths.add(key)

                node_path = []
                for fp in p:
                    nodes_in_file = file_to_nodes.get(fp, [])
                    if nodes_in_file:
                        node_path.append(nodes_in_file[0])

                if len(node_path) >= 2:
                    ep = node_path[0]
                    flow = self._make_flow(node_path, nodes_map, [], ep, flows)
                    if flow:
                        flow["flow_type"] = "pipeline"
                        flow["name"] = f"Module Flow: {p[0]} → {p[-1]}"
                        flows.append(flow)

        return flows

    def _dfs_paths_str(self, start: str, adj: dict[str, set[str]],
                        max_depth: int, max_paths: int) -> list[list[str]]:
        paths: list[list[str]] = []
        visited: set[str] = set()

        def dfs(current: str, path: list[str]):
            if len(path) > max_depth or len(paths) >= max_paths:
                return
            if current in visited:
                return
            visited.add(current)
            neighbors = adj.get(current, set())
            if not neighbors:
                paths.append(path[:])
            else:
                for n in neighbors:
                    dfs(n, path + [n])
            visited.discard(current)

        dfs(start, [start])
        return paths

    def _detect_file_based_flows(self, nodes_map: dict, file_language_map: dict,
                                  node_id_to_file: dict,
                                  entry_point_ids: set) -> list[dict]:
        flows: list[dict] = []
        file_to_nodes: dict[str, list[str]] = defaultdict(list)
        node_type_by_file: dict[str, str] = {}

        for nid, node in nodes_map.items():
            fp = node.get("file_path", "")
            if fp:
                file_to_nodes[fp].append(nid)
                current = node_type_by_file.get(fp, "")
                nt = node.get("type", "")
                if nt == "entry_point":
                    node_type_by_file[fp] = "entry_point"
                elif nt in ("controller", "route") and current != "entry_point":
                    node_type_by_file[fp] = "controller"
                elif nt in ("service",) and current not in ("entry_point", "controller"):
                    node_type_by_file[fp] = "service"
                elif nt == "repository" and current not in ("entry_point", "controller", "service"):
                    node_type_by_file[fp] = "repository"
                elif nt == "model" and not current:
                    node_type_by_file[fp] = "model"

        type_order = ["entry_point", "controller", "service", "repository", "model"]
        type_files: dict[str, list[str]] = defaultdict(list)
        for fp, tp in node_type_by_file.items():
            type_files[tp].append(fp)

        for i in range(len(type_order) - 1):
            src_type = type_order[i]
            tgt_type = type_order[i + 1]
            src_files = type_files.get(src_type, [])
            tgt_files = type_files.get(tgt_type, [])
            if src_files and tgt_files:
                path: list[str] = []
                for sf in src_files:
                    nodes_in_sf = file_to_nodes.get(sf, [])
                    if nodes_in_sf:
                        path.append(nodes_in_sf[0])
                for tf in tgt_files:
                    nodes_in_tf = file_to_nodes.get(tf, [])
                    if nodes_in_tf:
                        path.append(nodes_in_tf[0])

                if len(path) >= 2:
                    ep = path[0]
                    flow = self._make_flow(path, nodes_map, [], ep, flows)
                    if flow:
                        flow["flow_type"] = src_type
                        flow["name"] = f"{src_type.title()} → {tgt_type.title()} Flow"
                        flows.append(flow)

        return flows

    def _detect_orphan_methods(self, nodes_map: dict, edges_list: list) -> list[str]:
        method_nodes = {nid for nid, n in nodes_map.items() if n.get("type") == "method"}
        called: set[str] = set()
        for e in edges_list:
            called.add(e["source"])
            called.add(e["target"])
        orphans = [nid for nid in method_nodes if nid not in called]
        return orphans

    def _detect_broken_paths(self, nodes_map: dict, edges_list: list,
                              entry_point_ids: set, flows: list[dict]) -> list[dict]:
        broken: list[dict] = []
        for flow in flows:
            path = flow["path"]
            for i in range(len(path) - 1):
                src = path[i]
                tgt = path[i + 1]
                if src not in nodes_map or tgt not in nodes_map:
                    broken.append({
                        "source": src,
                        "target": tgt,
                        "flow_id": flow["id"],
                        "reason": "Node not in graph",
                    })
                elif not any(e["source"] == src and e["target"] == tgt for e in edges_list):
                    broken.append({
                        "source": src,
                        "target": tgt,
                        "flow_id": flow["id"],
                        "reason": "Missing edge",
                    })
        return broken

    def _generate_issues(self, nodes_map: dict, edges_list: list, flows: list[dict],
                          circular: list[list[str]], unused: list[str],
                          orphan_methods: list[str], broken_paths: list[dict]) -> list[dict]:
        issues_list: list[dict] = []

        for cycle in circular[:5]:
            issues_list.append({
                "type": "circular_call",
                "severity": "high",
                "description": f"Circular call chain: {' → '.join(cycle)}",
                "nodes": cycle,
                "detail": "This circular dependency can cause infinite loops and stack overflows.",
            })

        for fn_id in unused[:10]:
            if fn_id in nodes_map:
                issues_list.append({
                    "type": "unused_function",
                    "severity": "medium",
                    "description": f"Function '{nodes_map[fn_id]['name']}' is unused",
                    "nodes": [fn_id],
                    "detail": "This function is never called from any entry point.",
                })

        for fn_id in orphan_methods[:5]:
            issues_list.append({
                "type": "orphan_method",
                "severity": "medium",
                "description": f"Method '{nodes_map[fn_id]['name']}' is orphaned" if fn_id in nodes_map else f"Method '{fn_id}' is orphaned",
                "nodes": [fn_id],
                "detail": "This method is defined but never called.",
            })

        for bp in broken_paths[:5]:
            issues_list.append({
                "type": "broken_path",
                "severity": "high",
                "description": f"Broken call path: {bp.get('source', '?')} → {bp.get('target', '?')}",
                "nodes": [bp.get("source", ""), bp.get("target", "")],
                "detail": f"Reason: {bp.get('reason', 'unknown')}",
            })

        for node_id, node in nodes_map.items():
            if node.get("is_recursive"):
                issues_list.append({
                    "type": "recursive_loop",
                    "severity": "low",
                    "description": f"Function '{node['name']}' contains a recursive call",
                    "nodes": [node_id],
                    "detail": "Recursive functions should have a base case to prevent stack overflow.",
                })

        return issues_list

    def _generate_ai_insights(self, nodes_map: dict, edges_list: list, flows: list[dict],
                               issues_list: list[dict], entry_point_ids: set,
                               unused: list[str]) -> list[str]:
        insights: list[str] = []
        if not nodes_map:
            insights.append("No functions or methods detected in the project.")
            return insights

        total_nodes = len(nodes_map)
        total_edges = len(edges_list)
        total_flows = len(flows)

        ep_count = len(entry_point_ids)
        insights.append(
            f"Project contains {total_nodes} callable nodes and {total_edges} call relationships "
            f"across {total_flows} execution flows from {ep_count} entry point(s)."
        )

        node_types = defaultdict(int)
        for n in nodes_map.values():
            node_types[n.get("type", "unknown")] += 1
        type_desc = ", ".join(f"{count} {ntype}(s)" for ntype, count in sorted(node_types.items()))
        insights.append(f"Call graph composition: {type_desc}.")

        deep_flows = [f for f in flows if f["depth"] > 5]
        if deep_flows:
            deep_flows.sort(key=lambda f: f["depth"], reverse=True)
            df = deep_flows[0]
            insights.append(
                f"Deepest execution chain has {df['depth']} nodes ({df['name']}). "
                f"Consider optimizing long call chains for better performance."
            )

        high_issues = [i for i in issues_list if i.get("severity") == "high"]
        med_issues = [i for i in issues_list if i.get("severity") == "medium"]
        if high_issues:
            insights.append(
                f"Found {len(high_issues)} high-severity issue(s): "
                f"{', '.join(i['type'] for i in high_issues[:4])}. "
                f"These may cause runtime failures."
            )
        if med_issues:
            insights.append(
                f"Found {len(med_issues)} medium-severity issue(s): "
                f"{', '.join(i['type'] for i in med_issues[:4])}."
            )

        if unused:
            unused_names = [nodes_map.get(fid, {}).get("name", fid) for fid in unused[:3]]
            insights.append(
                f"{len(unused)} unused function(s) detected: {', '.join(unused_names)}. "
                f"Removing dead code improves maintainability."
            )

        circular_issues = [i for i in issues_list if i["type"] == "circular_call"]
        if circular_issues:
            insights.append(
                f"{len(circular_issues)} circular call chain(s) found. "
                f"Review and refactor to eliminate circular dependencies."
            )

        cross_file_edges = [e for e in edges_list if e.get("is_cross_file")]
        if cross_file_edges:
            insights.append(
                f"{len(cross_file_edges)} cross-file call(s) detected, indicating "
                f"modular dependency structure."
            )

        orphan_count = len([i for i in issues_list if i["type"] == "orphan_method"])
        if orphan_count:
            insights.append(
                f"{orphan_count} orphan method(s) exist - methods defined but never invoked. "
                f"Review for dead code or missing call sites."
            )

        if total_edges > 0 and total_nodes > 0:
            avg_fan = round(total_edges / total_nodes, 1)
            if avg_fan > 3:
                insights.append(
                    f"Average call fan-out is {avg_fan}, suggesting high interconnectivity. "
                    f"Consider modularizing to reduce coupling."
                )

        return insights

    def _compute_stats(self, nodes_map: dict, edges_list: list, entry_point_ids: set,
                        flows: list[dict], issues_list: list[dict], unused: list[str],
                        language_breakdown: dict, node_type_counts: dict) -> dict:
        depths = [f["depth"] for f in flows] if flows else [0]
        avg_depth = sum(depths) / len(depths) if depths else 0.0
        max_depth = max(depths) if depths else 0

        recursive_count = sum(1 for n in nodes_map.values() if n.get("is_recursive"))
        circular_count = len([i for i in issues_list if i["type"] == "circular_call"])
        dead_chain_count = len([i for i in issues_list if i["type"] == "dead_chain"])
        orphan_count = len([i for i in issues_list if i["type"] == "orphan_method"])
        broken_count = len([i for i in issues_list if i["type"] == "broken_path"])

        return {
            "total_nodes": len(nodes_map),
            "total_edges": len(edges_list),
            "total_entry_points": len(entry_point_ids),
            "total_execution_flows": len(flows),
            "total_issues": len(issues_list),
            "average_call_depth": round(avg_depth, 1),
            "max_call_depth": max_depth,
            "total_unused": len(unused),
            "total_recursive": recursive_count,
            "total_circular": circular_count,
            "total_dead_chains": dead_chain_count,
            "total_orphans": orphan_count,
            "total_broken_paths": broken_count,
            "language_breakdown": dict(language_breakdown),
            "node_type_counts": dict(node_type_counts),
        }
