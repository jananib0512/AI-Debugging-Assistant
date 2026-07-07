import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from app.repositories.source_code_intelligence_engine import (
    IGNORED_DIRS,
    IGNORED_FILES,
    EXTENSION_LANGUAGE_MAP,
    SUPPORTED_EXTENSIONS,
)


class ImportDependencyEngine:

    # Known external packages (sample) for external/internal classification
    STDLIB_MODULES: dict[str, set[str]] = {
        "Python": {
            "os", "sys", "re", "json", "math", "datetime", "collections",
            "pathlib", "typing", "functools", "itertools", "hashlib",
            "subprocess", "threading", "multiprocessing", "asyncio",
            "logging", "argparse", "unittest", "pytest", "copy", "abc",
            "dataclasses", "enum", "io", "base64", "uuid", "random",
            "statistics", "decimal", "fractions", "socket", "http",
            "urllib", "xml", "csv", "tempfile", "shutil", "glob",
            "inspect", "traceback", "warnings", "contextlib",
        },
        "JavaScript": {
            "fs", "path", "os", "http", "https", "url", "util",
            "stream", "buffer", "crypto", "events", "assert",
            "child_process", "cluster", "dns", "net", "readline",
            "tls", "zlib", "process",
        },
        "TypeScript": {
            "fs", "path", "os", "http", "https", "url", "util",
            "stream", "buffer", "crypto", "events", "assert",
            "child_process", "cluster", "dns", "net", "readline",
            "tls", "zlib", "process",
        },
        "Java": {
            "java.lang", "java.util", "java.io", "java.nio",
            "java.net", "java.sql", "java.time", "java.math",
            "java.text", "java.security", "java.awt",
        },
    }

    # Known external framework/lib packages
    KNOWN_EXTERNAL_PACKAGES: dict[str, set[str]] = {
        "Python": {
            "flask", "django", "fastapi", "sqlalchemy", "pydantic",
            "requests", "numpy", "pandas", "scipy", "matplotlib",
            "click", "pyyaml", "jinja2", "aiohttp", "httpx",
            "pytest", "celery", "redis", "boto3", "psycopg2",
            "motor", "beanie", "tortoise", "aioredis",
        },
        "JavaScript": {
            "react", "vue", "angular", "express", "lodash", "axios",
            "moment", "chalk", "commander", "ws", "socket.io",
            "next", "nuxt", "redux", "mobx", "graphql",
        },
        "TypeScript": {
            "react", "vue", "angular", "express", "lodash", "axios",
            "moment", "chalk", "commander", "ws", "socket.io",
            "next", "nuxt", "redux", "mobx", "graphql",
            "@nestjs", "@angular", "@types",
        },
        "Java": {
            "org.springframework", "org.apache", "com.fasterxml",
            "org.slf4j", "org.junit", "org.mockito", "com.google",
            "org.hibernate", "javax.persistence", "io.netty",
        },
    }

    # Language-specific patterns for detecting framework/lib from import
    FRAMEWORK_PATTERNS: dict[str, dict[str, str]] = {
        "Python": {
            "flask": "Flask",
            "django": "Django",
            "fastapi": "FastAPI",
            "sqlalchemy": "SQLAlchemy",
            "requests": "Requests",
            "numpy": "NumPy",
            "pandas": "Pandas",
        },
        "JavaScript": {
            "react": "React",
            "vue": "Vue",
            "express": "Express",
            "axios": "Axios",
            "lodash": "Lodash",
        },
        "TypeScript": {
            "react": "React",
            "vue": "Vue",
            "express": "Express",
            "axios": "Axios",
            "lodash": "Lodash",
        },
    }

    def analyze(self, workspace_path: Path) -> dict:
        imports: list[dict] = []
        file_deps: list[dict] = []
        file_import_map: dict[str, list[dict]] = defaultdict(list)
        file_content: dict[str, str] = {}
        file_language: dict[str, str] = {}
        used_symbols: dict[str, set[str]] = defaultdict(set)
        import_lines: dict[str, list[tuple[int, str]]] = defaultdict(list)
        file_stack: list[str] = []
        circular_chains: list[dict] = []
        seen_circular: set[str] = set()

        all_rel_paths: set[str] = set()
        workspace_str = str(workspace_path)

        for root, dirs, _files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in _files:
                if f.lower() in IGNORED_FILES:
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                rel = os.path.relpath(os.path.join(root, f), workspace_path).replace("\\", "/")
                all_rel_paths.add(rel)

        module_to_file: dict[str, str] = {}
        for rp in all_rel_paths:
            mod = rp.replace("/", ".").rsplit(".", 1)[0] if "." in rp else rp
            module_to_file[mod] = rp
            module_to_file[rp] = rp

        for root, dirs, _files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in _files:
                if f.lower() in IGNORED_FILES:
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                file_path = os.path.join(root, f)
                language = EXTENSION_LANGUAGE_MAP[ext]
                rel_path = os.path.relpath(file_path, workspace_path).replace("\\", "/")

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                except (OSError, UnicodeDecodeError):
                    try:
                        with open(file_path, "r", encoding="latin-1", errors="replace") as fh:
                            content = fh.read()
                    except OSError:
                        continue

                file_content[rel_path] = content
                file_language[rel_path] = language
                lines = content.split("\n")

                file_imports = self._extract_imports(lines, rel_path, language, workspace_str)
                imports.extend(file_imports)
                file_import_map[rel_path] = file_imports

                # Track used symbols (everything after import lines)
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if not stripped or stripped.startswith(("#", "//", "/*", "*")):
                        continue
                    if re.match(r"^\s*(import|from|using|require|include)", stripped):
                        import_lines[rel_path].append((i, stripped))
                        continue
                    for token in re.findall(r'\b([a-zA-Z_]\w*)\b', stripped):
                        if token not in ("if", "else", "for", "while", "return", "import", "from", "def", "class", "var", "let", "const", "function", "new", "throw", "try", "catch", "finally", "switch", "case", "break", "continue", "this", "self", "null", "None", "True", "False", "undefined", "true", "false"):
                            used_symbols[rel_path].add(token)

        # Build file dependencies
        all_modules_set = set(module_to_file.keys())
        for src_file, file_imports_list in file_import_map.items():
            lang = file_language.get(src_file, "Unknown")
            for imp in file_imports_list:
                target_module = imp["module"]
                target_file = self._resolve_target(target_module, src_file, all_rel_paths, module_to_file, lang)
                imp["target_file"] = target_file
                imp["resolved"] = target_file is not None

                is_ext = self._is_external_import(target_module, lang)
                imp["import_type"] = "external" if is_ext else "internal"

                file_deps.append({
                    "source_file": src_file,
                    "target_file": target_file,
                    "target_module": target_module,
                    "dependency_type": imp.get("type_override", "import"),
                    "language": lang,
                    "import_count": 1,
                    "is_external": is_ext,
                    "is_circular": False,
                    "is_broken": not imp["resolved"] and not is_ext,
                    "is_unused": False,
                })

        # Detect unused imports
        for src_file, file_imports_list in file_import_map.items():
            used = used_symbols.get(src_file, set())
            for imp in file_imports_list:
                symbol = imp.get("symbol", "")
                if symbol and symbol not in used and symbol not in ("*", "default"):
                    for dep in file_deps:
                        if dep["source_file"] == src_file and dep["target_module"] == imp["module"]:
                            dep["is_unused"] = True
                            imp["is_unused"] = True
                            break

        # Detect duplicate imports
        seen_imports_set: set[tuple[str, str, str]] = set()
        for imp in imports:
            key = (imp["source_file"], imp["module"], imp.get("symbol", ""))
            if key in seen_imports_set:
                imp["is_duplicate"] = True
            seen_imports_set.add(key)

        # Detect circular dependencies via DFS
        dep_graph: dict[str, list[str]] = defaultdict(list)
        for dep in file_deps:
            if dep["target_file"] and not dep["is_external"]:
                dep_graph[dep["source_file"]].append(dep["target_file"])
                dep_graph[dep["target_file"]]

        all_files_sorted = sorted(dep_graph.keys())
        for start_file in all_files_sorted:
            if start_file in seen_circular:
                continue
            visited: set[str] = set()
            stack: list[tuple[str, list[str]]] = [(start_file, [start_file])]
            while stack:
                current, path = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                if current not in dep_graph:
                    continue
                for neighbor in dep_graph[current]:
                    if neighbor == start_file and len(path) > 1:
                        chain = path + [neighbor]
                        chain_key = "->".join(chain)
                        if chain_key not in seen_circular:
                            seen_circular.add(chain_key)
                            severity = "high" if len(chain) > 4 else "medium"
                            circular_chains.append({
                                "chain": chain,
                                "files": list(set(chain)),
                                "severity": severity,
                                "suggested_resolution": self._suggest_circular_resolution(chain),
                            })
                    elif neighbor not in visited:
                        stack.append((neighbor, path + [neighbor]))
                        for cd in circular_chains:
                            if neighbor in cd["files"] and start_file in cd["files"]:
                                break

        # Mark circular deps
        for cd in circular_chains:
            for i in range(len(cd["chain"]) - 1):
                src = cd["chain"][i]
                tgt = cd["chain"][i + 1]
                for dep in file_deps:
                    if dep["source_file"] == src and dep["target_file"] == tgt:
                        dep["is_circular"] = True

        # Build dependency graph (module-level aggregation)
        module_nodes: dict[str, dict] = {}
        module_edges: list[dict] = []
        for dep in file_deps:
            src_mod = dep["source_file"].replace("/", ".").rsplit(".", 1)[0] if "." in dep["source_file"] else dep["source_file"]
            tgt_mod = dep["target_module"].split(".")[0] if dep["is_external"] else (
                dep["target_file"].replace("/", ".").rsplit(".", 1)[0] if dep["target_file"] else dep["target_module"]
            )
            if src_mod not in module_nodes:
                module_nodes[src_mod] = {"id": src_mod, "label": src_mod.split(".")[-1], "type": "module", "language": dep["language"], "file_count": 0, "import_count": 0}
            module_nodes[src_mod]["file_count"] += 0
            if tgt_mod not in module_nodes:
                node_type = "external" if dep["is_external"] else "module"
                module_nodes[tgt_mod] = {"id": tgt_mod, "label": tgt_mod.split(".")[-1], "type": node_type, "language": dep["language"], "file_count": 0, "import_count": 0}
            edge_key = (src_mod, tgt_mod)
            existing = None
            for e in module_edges:
                if (e["source"], e["target"]) == edge_key:
                    existing = e
                    break
            if existing:
                existing["weight"] += 1
            else:
                module_edges.append({"source": src_mod, "target": tgt_mod, "weight": 1, "type": "import"})

        # Build file-level graph nodes
        file_nodes: list[dict] = []
        for rp in sorted(all_rel_paths):
            lang = file_language.get(rp, "Unknown")
            import_count = len(file_import_map.get(rp, []))
            file_nodes.append({
                "id": rp,
                "label": os.path.basename(rp),
                "type": "file",
                "language": lang,
                "file_count": 1,
                "import_count": import_count,
            })

        # Metrics
        total_imports = len(imports)
        total_external = sum(1 for d in file_deps if d["is_external"])
        total_internal = sum(1 for d in file_deps if not d["is_external"])
        total_broken = sum(1 for d in file_deps if d["is_broken"])
        total_unused = sum(1 for d in file_deps if d["is_unused"])
        total_circular = len(circular_chains)

        lang_breakdown: dict[str, int] = defaultdict(int)
        type_counts: dict[str, int] = defaultdict(int)
        for dep in file_deps:
            lang_breakdown[dep["language"]] += 1
            type_counts[dep["dependency_type"]] += 1

        # Coupling score: ratio of actual inter-file deps to possible deps
        n_files = len(all_rel_paths)
        possible = max(n_files * (n_files - 1), 1)
        actual_inter = sum(1 for d in file_deps if not d["is_external"] and d["target_file"])
        coupling = round(actual_inter / possible * 100, 1) if possible > 1 else 0.0

        dep_depth = self._compute_depth(dep_graph)

        insights = self._generate_insights(file_deps, circular_chains, total_unused, total_broken, coupling)
        recommendations = self._generate_recommendations(file_deps, circular_chains, total_unused, total_broken)

        graph_nodes = file_nodes + list(module_nodes.values())

        return {
            "imports": imports,
            "dependencies": file_deps,
            "circular_dependencies": circular_chains,
            "graph": {
                "nodes": graph_nodes,
                "edges": module_edges,
            },
            "metrics": {
                "total_files": len(all_rel_paths),
                "total_imports": total_imports,
                "total_dependencies": len(file_deps),
                "external_libraries": total_external,
                "internal_libraries": total_internal,
                "broken_dependencies": total_broken,
                "unused_imports": total_unused,
                "circular_dependencies": total_circular,
                "average_dependency_depth": round(dep_depth, 2),
                "coupling_score": coupling,
                "language_breakdown": dict(lang_breakdown),
                "dependency_type_counts": dict(type_counts),
            },
            "insights": insights,
            "recommendations": recommendations,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _extract_imports(self, lines: list[str], rel_path: str,
                          language: str, workspace_str: str) -> list[dict]:
        imports: list[dict] = []
        inside_multiline = False

        for i, raw in enumerate(lines):
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith("/*"):
                inside_multiline = True
                continue
            if inside_multiline:
                if "*/" in stripped:
                    inside_multiline = False
                continue
            if stripped.startswith("//") or stripped.startswith("#"):
                continue

            if language == "Python":
                imports.extend(self._extract_python_import(stripped, rel_path, i))
            elif language in ("JavaScript", "TypeScript"):
                imports.extend(self._extract_js_import(stripped, rel_path, i))
            elif language == "Java":
                imports.extend(self._extract_java_import(stripped, rel_path, i))
            elif language in ("C#",):
                imports.extend(self._extract_csharp_import(stripped, rel_path, i))
            elif language in ("Go",):
                imports.extend(self._extract_go_import(stripped, rel_path, i))
            elif language in ("PHP",):
                imports.extend(self._extract_php_import(stripped, rel_path, i))
            elif language in ("Rust",):
                imports.extend(self._extract_rust_import(stripped, rel_path, i))

        return imports

    def _extract_python_import(self, line: str, rel_path: str, lineno: int) -> list[dict]:
        results: list[dict] = []
        m = re.match(r"^\s*from\s+(\S+)\s+import\s+(.+)", line)
        if m:
            module = m.group(1).strip()
            symbols_raw = m.group(2)
            is_relative = module.startswith(".")
            if is_relative:
                module = module.lstrip(".")
            is_wildcard = "*" in symbols_raw
            parts = [p.strip() for p in re.split(r",\s*(?![^()]*\))", symbols_raw)]
            for part in parts:
                if not part:
                    continue
                symbol = part
                alias = None
                if " as " in part:
                    symbol, alias = [x.strip() for x in part.split(" as ", 1)]
                results.append({
                    "module": module,
                    "symbol": symbol,
                    "alias": alias,
                    "source_file": rel_path,
                    "target_file": None,
                    "import_type": "external",
                    "language": "Python",
                    "is_relative": is_relative,
                    "is_wildcard": is_wildcard,
                    "is_dynamic": False,
                    "is_unused": False,
                    "is_duplicate": False,
                    "is_broken": False,
                    "line_number": lineno + 1,
                    "resolved": False,
                    "confidence": 1.0,
                    "type_override": "import",
                })
            return results

        m = re.match(r"^\s*import\s+(.+)", line)
        if m:
            imports_raw = m.group(1)
            if "(" in imports_raw:
                imports_raw = imports_raw.replace("(", "").replace(")", "")
            for part in imports_raw.split(","):
                part = part.strip()
                if not part:
                    continue
                symbol = part
                alias = None
                if " as " in part:
                    symbol, alias = [x.strip() for x in part.split(" as ", 1)]
                is_dynamic = "importlib" in line or "__import__" in line
                results.append({
                    "module": symbol.split(".")[0],
                    "symbol": symbol,
                    "alias": alias,
                    "source_file": rel_path,
                    "target_file": None,
                    "import_type": "external",
                    "language": "Python",
                    "is_relative": False,
                    "is_wildcard": False,
                    "is_dynamic": is_dynamic,
                    "is_unused": False,
                    "is_duplicate": False,
                    "is_broken": False,
                    "line_number": lineno + 1,
                    "resolved": False,
                    "confidence": 1.0,
                    "type_override": "import",
                })
        return results

    def _extract_js_import(self, line: str, rel_path: str, lineno: int) -> list[dict]:
        results: list[dict] = []

        m = re.search(r"(?:import|require)\s*\(\s*['\"]([^'\"]+)['\"]", line)
        if m:
            module = m.group(1)
            is_relative = module.startswith(".")
            is_dynamic = "import(" in line
            results.append({
                "module": module,
                "symbol": "",
                "alias": None,
                "source_file": rel_path,
                "target_file": None,
                "import_type": "external",
                "language": "JavaScript",
                "is_relative": is_relative,
                "is_wildcard": False,
                "is_dynamic": is_dynamic,
                "is_unused": False,
                "is_duplicate": False,
                "is_broken": False,
                "line_number": lineno + 1,
                "resolved": False,
                "confidence": 1.0,
                "type_override": "import",
            })
            return results

        m = re.match(r"^\s*import\s+(\S+(?:\s+as\s+\S+)?)\s+from\s+['\"]([^'\"]+)['\"]", line)
        if m:
            symbol = m.group(1)
            module = m.group(2)
            alias = None
            if " as " in symbol:
                parts = symbol.split(" as ", 1)
                symbol = parts[0].strip()
                alias = parts[1].strip()
            is_relative = module.startswith(".")
            results.append({
                "module": module,
                "symbol": symbol,
                "alias": alias,
                "source_file": rel_path,
                "target_file": None,
                "import_type": "external",
                "language": "JavaScript",
                "is_relative": is_relative,
                "is_wildcard": False,
                "is_dynamic": False,
                "is_unused": False,
                "is_duplicate": False,
                "is_broken": False,
                "line_number": lineno + 1,
                "resolved": False,
                "confidence": 1.0,
                "type_override": "import",
            })
            return results

        m = re.match(r"^\s*import\s+\{\s*([^}]+)\s*\}\s+from\s+['\"]([^'\"]+)['\"]", line)
        if m:
            module = m.group(2)
            symbols_raw = m.group(1)
            is_relative = module.startswith(".")
            for part in symbols_raw.split(","):
                part = part.strip()
                if not part:
                    continue
                symbol = part
                alias = None
                if " as " in part:
                    symbol, alias = [x.strip() for x in part.split(" as ", 1)]
                results.append({
                    "module": module,
                    "symbol": symbol,
                    "alias": alias,
                    "source_file": rel_path,
                    "target_file": None,
                    "import_type": "external",
                    "language": "JavaScript",
                    "is_relative": is_relative,
                    "is_wildcard": False,
                    "is_dynamic": False,
                    "is_unused": False,
                    "is_duplicate": False,
                    "is_broken": False,
                    "line_number": lineno + 1,
                    "resolved": False,
                    "confidence": 1.0,
                    "type_override": "import",
                })
            return results

        m = re.match(r"^\s*import\s+\*\s+as\s+(\S+)\s+from\s+['\"]([^'\"]+)['\"]", line)
        if m:
            alias = m.group(1)
            module = m.group(2)
            is_relative = module.startswith(".")
            results.append({
                "module": module,
                "symbol": "*",
                "alias": alias,
                "source_file": rel_path,
                "target_file": None,
                "import_type": "external",
                "language": "JavaScript",
                "is_relative": is_relative,
                "is_wildcard": True,
                "is_dynamic": False,
                "is_unused": False,
                "is_duplicate": False,
                "is_broken": False,
                "line_number": lineno + 1,
                "resolved": False,
                "confidence": 1.0,
                "type_override": "import",
            })

        return results

    def _extract_java_import(self, line: str, rel_path: str, lineno: int) -> list[dict]:
        results: list[dict] = []
        m = re.match(r"^\s*import\s+(?:static\s+)?(\S+)\s*;", line)
        if m:
            module = m.group(1)
            is_wildcard = module.endswith(".*")
            symbol = ""
            if is_wildcard:
                module = module[:-2]
            results.append({
                "module": module,
                "symbol": symbol,
                "alias": None,
                "source_file": rel_path,
                "target_file": None,
                "import_type": "external",
                "language": "Java",
                "is_relative": False,
                "is_wildcard": is_wildcard,
                "is_dynamic": False,
                "is_unused": False,
                "is_duplicate": False,
                "is_broken": False,
                "line_number": lineno + 1,
                "resolved": False,
                "confidence": 1.0,
                "type_override": "import",
            })
        return results

    def _extract_csharp_import(self, line: str, rel_path: str, lineno: int) -> list[dict]:
        results: list[dict] = []
        m = re.match(r"^\s*using\s+(?:static\s+)?(\S+)\s*;", line)
        if m:
            module = m.group(1)
            results.append({
                "module": module,
                "symbol": "",
                "alias": None,
                "source_file": rel_path,
                "target_file": None,
                "import_type": "external",
                "language": "C#",
                "is_relative": False,
                "is_wildcard": False,
                "is_dynamic": False,
                "is_unused": False,
                "is_duplicate": False,
                "is_broken": False,
                "line_number": lineno + 1,
                "resolved": False,
                "confidence": 1.0,
                "type_override": "import",
            })
        return results

    def _extract_go_import(self, line: str, rel_path: str, lineno: int) -> list[dict]:
        results: list[dict] = []
        m = re.search(r'["]([^"]+)["]', line)
        if m:
            module = m.group(1)
            results.append({
                "module": module,
                "symbol": "",
                "alias": None,
                "source_file": rel_path,
                "target_file": None,
                "import_type": "external",
                "language": "Go",
                "is_relative": False,
                "is_wildcard": False,
                "is_dynamic": False,
                "is_unused": False,
                "is_duplicate": False,
                "is_broken": False,
                "line_number": lineno + 1,
                "resolved": False,
                "confidence": 1.0,
                "type_override": "import",
            })
        return results

    def _extract_php_import(self, line: str, rel_path: str, lineno: int) -> list[dict]:
        results: list[dict] = []
        m = re.match(r"^\s*use\s+(\S+)(?:\s+as\s+(\S+))?\s*;", line)
        if m:
            module = m.group(1)
            alias = m.group(2)
            results.append({
                "module": module,
                "symbol": module.rsplit("\\", 1)[-1] if "\\" in module else module.rsplit("/", 1)[-1],
                "alias": alias,
                "source_file": rel_path,
                "target_file": None,
                "import_type": "external",
                "language": "PHP",
                "is_relative": False,
                "is_wildcard": False,
                "is_dynamic": False,
                "is_unused": False,
                "is_duplicate": False,
                "is_broken": False,
                "line_number": lineno + 1,
                "resolved": False,
                "confidence": 1.0,
                "type_override": "import",
            })
            return results

        for keyword in ("require_once", "require", "include_once", "include"):
            m = re.match(rf"^\s*{keyword}\s+['\"]([^'\"]+)['\"]\s*;", line)
            if m:
                module = m.group(1)
                results.append({
                    "module": module,
                    "symbol": "",
                    "alias": None,
                    "source_file": rel_path,
                    "target_file": None,
                    "import_type": "internal",
                    "language": "PHP",
                    "is_relative": module.startswith(".") or module.startswith("/"),
                    "is_wildcard": False,
                    "is_dynamic": False,
                    "is_unused": False,
                    "is_duplicate": False,
                    "is_broken": False,
                    "line_number": lineno + 1,
                    "resolved": False,
                    "confidence": 1.0,
                    "type_override": "include",
                })
                return results

        return results

    def _extract_rust_import(self, line: str, rel_path: str, lineno: int) -> list[dict]:
        results: list[dict] = []
        m = re.match(r"^\s*use\s+(\S+)(?:\s+as\s+(\S+))?\s*;", line)
        if m:
            module = m.group(1)
            alias = m.group(2)
            is_wildcard = module.endswith("::*")
            if is_wildcard:
                module = module[:-3]
            is_relative = module.startswith("crate::") or module.startswith("self::") or module.startswith("super::")
            results.append({
                "module": module,
                "symbol": module.rsplit("::", 1)[-1] if "::" in module and not is_wildcard else "",
                "alias": alias,
                "source_file": rel_path,
                "target_file": None,
                "import_type": "external",
                "language": "Rust",
                "is_relative": is_relative,
                "is_wildcard": is_wildcard,
                "is_dynamic": False,
                "is_unused": False,
                "is_duplicate": False,
                "is_broken": False,
                "line_number": lineno + 1,
                "resolved": False,
                "confidence": 1.0,
                "type_override": "import",
            })
        return results

    def _resolve_target(self, module: str, source_file: str,
                         all_paths: set[str],
                         module_map: dict[str, str],
                         language: str) -> str | None:
        if language in ("JavaScript", "TypeScript", "PHP"):
            if module.startswith(".") or module.startswith("/"):
                base = os.path.dirname(source_file) if "/" in source_file else ""
                resolved = os.path.normpath(os.path.join(base, module))
                for rp in all_paths:
                    if rp == resolved or rp.startswith(resolved) or resolved.startswith(rp):
                        return rp
                return None
            for ext in ("", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".json"):
                candidate = module + ext if ext else module
                if candidate in all_paths:
                    return candidate
            return None

        if "." in module:
            mod_path = module.replace(".", "/")
            for ext in ("", ".py", ".java", ".cs", ".go", ".rs", ".php"):
                candidate = mod_path + ext if ext else mod_path
                if candidate in all_paths:
                    return candidate
            parts = module.rsplit(".", 1)
            if len(parts) == 2:
                base_path = parts[0].replace(".", "/")
                for f in all_paths:
                    if f.startswith(base_path) or f == base_path:
                        return f
            return None

        if module in module_map:
            return module_map[module]

        for ext in ("", ".py", ".java", ".cs", ".go", ".rs", ".php"):
            candidate = module + ext if ext else module
            if candidate in all_paths:
                return candidate

        for f in all_paths:
            base = os.path.splitext(f)[0].replace("/", ".")
            if base == module or base.endswith("." + module):
                return f

        return None

    def _is_external_import(self, module: str, language: str) -> bool:
        top_level = module.split(".")[0].split("/")[0].split("\\")[0] if "/" in module or "\\" in module else module.split(".")[0]
        if language in self.STDLIB_MODULES:
            for std in self.STDLIB_MODULES[language]:
                if top_level == std or top_level.startswith(std):
                    return False
        if language in self.KNOWN_EXTERNAL_PACKAGES:
            for ext_pkg in self.KNOWN_EXTERNAL_PACKAGES[language]:
                if top_level == ext_pkg or top_level.startswith(ext_pkg):
                    return True
        if language == "Java":
            if any(top_level.startswith(p) for p in ("com.", "org.", "io.", "net.", "javax.")):
                return True
        return False

    def _compute_depth(self, dep_graph: dict[str, list[str]]) -> float:
        if not dep_graph:
            return 0.0
        depths: list[int] = []
        for start in dep_graph:
            if not dep_graph[start]:
                depths.append(0)
                continue
            max_d = 0
            stack = [(start, 0)]
            visited: set[str] = set()
            while stack:
                node, d = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                max_d = max(max_d, d)
                for neighbor in dep_graph.get(node, []):
                    if neighbor not in visited:
                        stack.append((neighbor, d + 1))
            depths.append(max_d)
        return sum(depths) / len(depths) if depths else 0.0

    def _suggest_circular_resolution(self, chain: list[str]) -> str:
        files_part = ", ".join(chain[:5])
        if len(chain) <= 3:
            return f"Extract the shared dependency between {files_part} into a separate module."
        return f"Refactor by introducing an interface or shared module to break the cycle involving {len(chain)} files."

    def _generate_insights(self, deps: list[dict], circular: list[dict],
                            unused_count: int, broken_count: int,
                            coupling: float) -> list[str]:
        insights: list[str] = []
        if coupling > 50:
            insights.append(f"High dependency coupling detected ({coupling}%). Consider reducing inter-module dependencies.")
        elif coupling < 10:
            insights.append("Low dependency coupling detected. The project has well-separated modules.")

        if circular:
            chains = [c["chain"] for c in circular[:3]]
            chain_strs = [" -> ".join(c[:4]) for c in chains]
            insights.append(f"Circular {'dependencies' if len(circular) > 1 else 'dependency'} detected: {'; '.join(chain_strs)}.")

        if unused_count > 0:
            insights.append(f"{unused_count} unused import(s) detected. Remove them to improve clarity.")

        if broken_count > 0:
            insights.append(f"{broken_count} broken import(s) found. The referenced files may be missing.")

        external_count = sum(1 for d in deps if d["is_external"])
        internal_count = sum(1 for d in deps if not d["is_external"])
        if external_count > internal_count * 2 and internal_count > 0:
            insights.append("Heavy reliance on external libraries. Consider evaluating if all are necessary.")

        high_dep_files = sorted(
            [(d["source_file"], sum(1 for dd in deps if dd["source_file"] == d["source_file"]))
             for d in deps],
            key=lambda x: -x[1],
        )
        if high_dep_files:
            top_file = high_dep_files[0]
            if top_file[1] > 10:
                insights.append(f"'{top_file[0]}' has {top_file[1]} dependencies making it a hub. Consider splitting.")

        if not insights:
            insights.append("Dependency structure appears clean and well-organized.")

        return insights

    def _generate_recommendations(self, deps: list[dict], circular: list[dict],
                                   unused_count: int, broken_count: int) -> list[str]:
        recs: list[str] = []
        if unused_count > 0:
            recs.append(f"Remove the {unused_count} unused import(s) to reduce clutter and improve maintainability.")

        for cd in circular[:3]:
            recs.append(f"Break circular dependency: {cd['suggested_resolution']}")

        if broken_count > 0:
            recs.append(f"Fix the {broken_count} broken import(s) by installing missing packages or correcting paths.")

        high_dep_files: dict[str, int] = defaultdict(int)
        for d in deps:
            high_dep_files[d["source_file"]] += 1
        for f, cnt in sorted(high_dep_files.items(), key=lambda x: -x[1])[:2]:
            if cnt > 15:
                recs.append(f"'{f}' has {cnt} dependencies. Extract shared logic into utility modules.")

        ext_count = sum(1 for d in deps if d["is_external"])
        if ext_count > 30:
            recs.append(f"Review the {ext_count} external dependencies. Remove unused packages from configuration.")

        if deps:
            avg_deps = len(deps) / max(len(set(d["source_file"] for d in deps)), 1)
            if avg_deps > 8:
                recs.append("Average dependency count per file is high. Consider modularizing the codebase.")

        if not recs:
            recs.append("No significant dependency issues found.")

        return recs
