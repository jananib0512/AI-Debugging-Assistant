import hashlib
import os
import re
from pathlib import Path

IGNORED_DIRS: set[str] = {
    "node_modules", ".git", ".venv", "venv", "__pycache__",
    "dist", "build", "coverage", ".next", "target", "vendor",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".eggs", "eggs", ".svn",
}

IGNORED_FILES: set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".cs": "C#",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".md": "Markdown",
    ".markdown": "Markdown",
}

SUPPORTED_EXTENSIONS = set(EXTENSION_LANGUAGE_MAP.keys())


class SourceCodeIntelligenceEngine:
    def analyze(self, workspace_path: Path) -> dict:
        all_classes: list[dict] = []
        all_functions: list[dict] = []
        all_imports: list[dict] = []
        all_enums: list[dict] = []
        all_interfaces: list[dict] = []
        all_variables: list[dict] = []
        all_files: list[dict] = []
        all_modules: dict[str, dict] = {}
        seen_imports: set[tuple[str, str]] = set()
        content_hashes: dict[str, list[str]] = {}
        total_comment_lines = 0
        total_blank_lines = 0
        all_complexities: list[int] = []
        all_maintainability_scores: list[float] = []

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
                rel_path = os.path.relpath(file_path, workspace_path)

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                    encoding = "utf-8"
                except (OSError, UnicodeDecodeError):
                    try:
                        with open(file_path, "r", encoding="latin-1", errors="replace") as fh:
                            content = fh.read()
                        encoding = "latin-1"
                    except OSError:
                        continue

                lines = content.split("\n")
                total_lines = len(lines)

                file_result = self._parse_file(lines, language, rel_path)
                loc = file_result.get("loc", total_lines)
                comment_lines = file_result.get("comment_lines", 0)
                blank_lines = file_result.get("blank_lines", 0)
                complexity = file_result.get("complexity", 0)

                content_hash = hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()
                if content_hash not in content_hashes:
                    content_hashes[content_hash] = []
                content_hashes[content_hash].append(rel_path)

                comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
                maintainability = max(0.0, min(100.0, 100.0 - (complexity * 1.5) - (1.0 - comment_ratio) * 40.0))

                total_comment_lines += comment_lines
                total_blank_lines += blank_lines
                all_complexities.append(complexity)
                all_maintainability_scores.append(maintainability)

                code_file = {
                    "path": rel_path,
                    "language": language,
                    "lines_of_code": loc,
                    "total_lines": total_lines,
                    "comment_lines": comment_lines,
                    "blank_lines": blank_lines,
                    "functions": len(file_result["functions"]),
                    "classes": len(file_result["classes"]),
                    "imports": len(file_result["imports"]),
                    "exports": len(file_result["exports"]),
                    "complexity": complexity,
                    "maintainability_score": round(maintainability, 1),
                    "encoding": encoding,
                }
                all_files.append(code_file)

                # Deduplicate imports
                for imp in file_result["imports"]:
                    key = (imp["source"] or "", ",".join(sorted(imp["names"])))
                    imp_key = (imp.get("source") or "", str(imp["names"]))
                    is_dup = imp_key in seen_imports
                    seen_imports.add(imp_key)
                    imp["is_duplicate"] = is_dup
                    all_imports.append(imp)

                for cls in file_result["classes"]:
                    cls["file_path"] = rel_path
                    all_classes.append(cls)
                    for m in cls.get("methods", []):
                        m["file_path"] = rel_path
                        m["parent_class"] = cls["name"]
                        all_functions.append(m)

                for fn in file_result["functions"]:
                    fn["file_path"] = rel_path
                    all_functions.append(fn)

                for e in file_result["enums"]:
                    e["file_path"] = rel_path
                    all_enums.append(e)

                for inf in file_result["interfaces"]:
                    inf["file_path"] = rel_path
                    all_interfaces.append(inf)

                for v in file_result["variables"]:
                    v["file_path"] = rel_path
                    all_variables.append(v)

                # Module tracking
                rel_parts = Path(rel_path).parent.parts
                for i in range(len(rel_parts) + 1):
                    module_name = "/".join(rel_parts[:i]) if i > 0 else "."
                    if module_name not in all_modules:
                        all_modules[module_name] = {
                            "name": module_name,
                            "path": str(Path(workspace_path) / rel_parts[0] if rel_parts else "."),
                            "files": [],
                            "classes": [],
                            "functions": [],
                            "submodules": [],
                        }
                    all_modules[module_name]["files"].append(rel_path)
                    for cls in file_result["classes"]:
                        if cls["name"] not in all_modules[module_name]["classes"]:
                            all_modules[module_name]["classes"].append(cls["name"])
                    for fn in file_result["functions"]:
                        if fn["name"] not in all_modules[module_name]["functions"]:
                            all_modules[module_name]["functions"].append(fn["name"])

        # Build submodule lists
        module_names = sorted(all_modules.keys(), key=lambda x: x.count("/"))
        for mname in module_names:
            depth = mname.count("/")
            for other in module_names:
                if other != mname and other.startswith(mname + "/"):
                    sub = other[len(mname) + 1:]
                    if "/" not in sub and sub not in all_modules[mname]["submodules"]:
                        all_modules[mname]["submodules"].append(sub)

        # Class hierarchy: inherited_classes
        for cls in all_classes:
            if cls["base_classes"]:
                for bc in cls["base_classes"]:
                    bc_clean = bc.strip()
                    if bc_clean and bc_clean != "object" and not bc_clean[0].islower():
                        cls["inherited_classes"].append(bc_clean)

        # External imports analysis
        ext_modules = {"os", "sys", "re", "json", "datetime", "math", "random", "pathlib",
                       "collections", "itertools", "functools", "typing", "uuid", "hashlib",
                       "base64", "io", "shutil", "glob", "subprocess", "threading", "multiprocessing",
                       "sqlite3", "http", "urllib", "xml", "csv", "pickle", "tempfile",
                       "logging", "warnings", "traceback", "inspect", "pprint", "copy",
                       "decimal", "fractions", "statistics", "calendar", "time", "datetime",
                       "pathlib", "abc", "enum", "dataclasses", "functools", "operator",
                       "react", "react-dom", "express", "lodash", "axios", "vue", "next",
                       "angular", "@angular", "@nestjs", "mongoose", "sequelize", "typeorm",
                       "prisma", "graphql", "apollo", "jest", "mocha", "chai", "sinon",
                       "webpack", "vite", "esbuild", "rollup", "gulp", "grunt"}
        for imp in all_imports:
            src = imp.get("source") or ""
            first_part = src.split("/")[0].split(".")[0] if src else ""
            if first_part in ext_modules or (src and not src.startswith(".") and not src.startswith("/")):
                imp["is_external"] = True
            else:
                imp["is_external"] = False

        total_external = sum(1 for i in all_imports if i.get("is_external"))

        empty_files = [f for f in all_files if f["total_lines"] == 0]
        duplicate_file_count = sum(len(v) - 1 for v in content_hashes.values() if len(v) > 1)
        total_file_sizes = sum(f["total_lines"] for f in all_files)
        total_loc = sum(f["lines_of_code"] for f in all_files)
        avg_file_size = round(total_file_sizes / len(all_files), 1) if all_files else 0
        avg_loc = round(total_loc / len(all_files), 1) if all_files else 0
        largest = max(all_files, key=lambda f: f["total_lines"]) if all_files else None
        smallest = min(all_files, key=lambda f: f["total_lines"]) if all_files else None
        avg_complexity = round(sum(all_complexities) / len(all_complexities), 1) if all_complexities else 0
        avg_maintainability = round(sum(all_maintainability_scores) / len(all_maintainability_scores), 1) if all_maintainability_scores else 0

        summary = {
            "total_files": len(all_files),
            "total_classes": len(all_classes),
            "total_functions": len(all_functions),
            "total_imports": len(all_imports),
            "total_external_imports": total_external,
            "total_enums": len(all_enums),
            "total_interfaces": len(all_interfaces),
            "total_variables": len(all_variables),
            "total_constants": sum(1 for v in all_variables if v.get("is_constant")),
            "total_modules": len(all_modules),
            "total_comments": total_comment_lines,
            "total_blank_lines": total_blank_lines,
            "total_empty_files": len(empty_files),
            "total_duplicate_files": duplicate_file_count,
            "average_file_size": avg_file_size,
            "average_lines_of_code": avg_loc,
            "average_complexity": avg_complexity,
            "average_maintainability": avg_maintainability,
            "largest_file": largest["path"] if largest else "",
            "largest_file_size": largest["total_lines"] if largest else 0,
            "smallest_file": smallest["path"] if smallest else "",
            "smallest_file_size": smallest["total_lines"] if smallest else 0,
            "languages": list({f["language"] for f in all_files}),
        }

        # Sort all collections by file path then line
        all_classes.sort(key=lambda c: (c["file_path"], c["line_start"]))
        all_functions.sort(key=lambda f: (f["file_path"], f["line_start"]))
        all_imports.sort(key=lambda i: (i.get("file_path", ""), i.get("line", 0)))
        all_enums.sort(key=lambda e: (e["file_path"], e["line"]))
        all_interfaces.sort(key=lambda i: (i["file_path"], i["line"]))
        all_variables.sort(key=lambda v: (v["file_path"], v["line"]))
        all_files.sort(key=lambda f: f["path"])

        modules_list = [all_modules[m] for m in sorted(all_modules.keys())]

        return {
            "summary": summary,
            "files": all_files,
            "classes": all_classes,
            "functions": all_functions,
            "imports": all_imports,
            "enums": all_enums,
            "interfaces": all_interfaces,
            "variables": all_variables,
            "modules": modules_list,
        }

    @staticmethod
    def _parse_file(lines: list[str], language: str, rel_path: str) -> dict:
        parser_name = f"_parse_{language.lower()}"
        parser = getattr(SourceCodeIntelligenceEngine, parser_name, None)
        result = None
        if parser:
            result = parser(lines, rel_path)
        if not result:
            result = {
                "loc": len(lines),
                "classes": [], "functions": [], "imports": [],
                "enums": [], "interfaces": [], "variables": [],
                "exports": [],
            }
        comment_lines, blank_lines = SourceCodeIntelligenceEngine._count_comments_blanks(lines, language)
        complexity = SourceCodeIntelligenceEngine._compute_complexity(lines, language)
        result["comment_lines"] = comment_lines
        result["blank_lines"] = blank_lines
        result["complexity"] = complexity
        return result

    @staticmethod
    def _clean_line(line: str) -> str:
        return line.strip()

    @staticmethod
    def _count_loc(lines: list[str]) -> int:
        loc = 0
        in_multiline = False
        ml_chars = {"'": "'''", '"': '"""'}
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if in_multiline:
                if ml_end in stripped:
                    in_multiline = False
                continue
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            if stripped.startswith("/*"):
                if "*/" in stripped:
                    continue
                in_multiline = True
                ml_end = "*/"
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_multiline = True
                ml_end = stripped[:3] if stripped.startswith('"""') else "'''"
                continue
            loc += 1
        return loc

    @staticmethod
    def _count_comments_blanks(lines: list[str], language: str) -> tuple[int, int]:
        comment_lines = 0
        blank_lines = 0
        in_block = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
                continue
            if in_block:
                comment_lines += 1
                if "*/" in stripped:
                    in_block = False
                continue
            if language == "Python":
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    comment_lines += 1
                    if stripped.startswith('"""') and stripped.count('"""') == 1:
                        in_block = True
                    elif stripped.startswith("'''") and stripped.count("'''") == 1:
                        in_block = True
                    continue
            elif language in ("HTML",):
                if stripped.startswith("<!--"):
                    comment_lines += 1
                    if "-->" not in stripped:
                        in_block = True
                    continue
                if in_block:
                    comment_lines += 1
                    if "-->" in stripped:
                        in_block = False
                    continue
            elif language in ("CSS",):
                if stripped.startswith("/*"):
                    comment_lines += 1
                    if "*/" not in stripped:
                        in_block = True
                    continue
                if in_block:
                    comment_lines += 1
                    if "*/" in stripped:
                        in_block = False
                    continue
            else:
                if stripped.startswith("//"):
                    comment_lines += 1
                    continue
                if stripped.startswith("/*"):
                    comment_lines += 1
                    if "*/" not in stripped:
                        in_block = True
                    continue
                if stripped.startswith("#") and language in ("Python", "Ruby", "Shell", "R", "YAML"):
                    comment_lines += 1
                    continue
        return comment_lines, blank_lines

    @staticmethod
    def _compute_complexity(lines: list[str], language: str) -> int:
        complexity = 1
        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()
            if re.search(r"\b(if|else if|elif)\b", lower) and not stripped.startswith("//") and not stripped.startswith("#"):
                complexity += 1
            if re.search(r"\b(for|while)\b", lower) and not stripped.startswith("//") and not stripped.startswith("#"):
                complexity += 1
            if re.search(r"\bcase\b", lower) and not stripped.startswith("//") and not stripped.startswith("#") and ":" in stripped:
                complexity += 1
            if re.search(r"\bcatch\b", lower) and not stripped.startswith("//") and not stripped.startswith("#"):
                complexity += 1
            if re.search(r"\b&&\b|\b\|\|\b", lower) and not stripped.startswith("//") and not stripped.startswith("#"):
                complexity += 1
            if language == "Python" and re.search(r"\bexcept\b", lower):
                complexity += 1
        return complexity

    @staticmethod
    def _is_in_string(line: str, idx: int) -> bool:
        in_single = False
        in_double = False
        i = 0
        while i < idx:
            ch = line[i]
            if ch == "\\":
                i += 2
                continue
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            i += 1
        return in_single or in_double

    @staticmethod
    def _parse_python(lines: list[str], rel_path: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []

        current_decorators: list[str] = []
        in_multiline = False
        ml_end = ""
        in_class = False
        current_class: dict | None = None
        class_indent = 0
        docstring = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            if in_multiline:
                if ml_end in stripped:
                    in_multiline = False
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count(stripped[:3]) >= 2 and len(stripped) > 3:
                    continue
                in_multiline = True
                ml_end = stripped[:3]
                continue
            if stripped.startswith("#"):
                continue

            if stripped.startswith("@") and not SourceCodeIntelligenceEngine._is_in_string(line, line.find("@")):
                decorator = stripped.lstrip("@").strip()
                if "(" in decorator:
                    decorator = decorator[:decorator.index("(")]
                current_decorators.append(decorator)
                continue

            # Class detection
            class_match = re.match(r"^class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:", stripped)
            if class_match:
                cls_name = class_match.group(1)
                bases_raw = class_match.group(2) or ""
                base_classes = [b.strip() for b in bases_raw.split(",") if b.strip()]
                cls_dict: dict = {
                    "name": cls_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "base_classes": base_classes,
                    "inherited_classes": [],
                    "methods": [],
                    "properties": [],
                    "decorators": list(current_decorators),
                    "visibility": "public",
                    "is_abstract": False,
                }
                classes.append(cls_dict)
                current_class = cls_dict
                class_indent = len(line) - len(line.lstrip())
                in_class = True
                current_decorators = []
                continue

            if in_class and current_class is not None:
                indent = len(line) - len(line.lstrip())
                if indent <= class_indent and stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    in_class = False
                    current_class = None

            if in_class and current_class is not None:
                prop_match = re.match(r"^\s*(\w+)\s*(?::\s*(\w+(?:\[.*?\])?))?\s*=\s*", stripped)
                if prop_match and not stripped.startswith("def ") and not stripped.startswith("async ") and not stripped.startswith("@"):
                    prop_name = prop_match.group(1)
                    prop_type = prop_match.group(2)
                    visibility = "public"
                    if prop_name.startswith("__"):
                        visibility = "private"
                    elif prop_name.startswith("_"):
                        visibility = "protected"
                    current_class["properties"].append({
                        "name": prop_name,
                        "type": prop_type,
                        "visibility": visibility,
                        "is_static": False,
                    })
                    continue

            # Function/method detection
            fn_match = re.match(
                r"^(?:(async)\s+)?(?:(static)\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\S+))?\s*:",
                stripped,
            )
            if fn_match:
                fn_name = fn_match.group(3)
                params_raw = fn_match.group(4) or ""
                return_type = fn_match.group(5)
                is_async = bool(fn_match.group(1))
                is_static = bool(fn_match.group(2))

                params = []
                for p in params_raw.split(","):
                    p = p.strip()
                    if not p or p == "*" or p == "/" or p.startswith("**") or p.startswith("*"):
                        continue
                    if ":" in p:
                        p_name, p_type = p.split(":", 1)
                        p_type = p_type.strip()
                        if "=" in p_type:
                            p_type, p_default = p_type.split("=", 1)
                            p_type = p_type.strip()
                            p_default = p_default.strip()
                        else:
                            p_default = None
                    else:
                        p_name = p
                        p_type = None
                        p_default = None
                    if "=" in p_name and p_type is None:
                        p_name, p_default = p_name.split("=", 1)
                        p_name = p_name.strip()
                        p_default = p_default.strip()
                    params.append({
                        "name": p_name.strip(),
                        "type": p_type,
                        "default": p_default,
                    })

                fn_dict: dict = {
                    "name": fn_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "parameters": params,
                    "return_type": return_type,
                    "decorators": list(current_decorators),
                    "is_async": is_async,
                    "is_static": is_static,
                    "is_generator": "yield" in stripped,
                    "visibility": "public",
                    "parent_class": None,
                }

                if fn_name.startswith("__"):
                    fn_dict["visibility"] = "private"
                elif fn_name.startswith("_"):
                    fn_dict["visibility"] = "protected"

                if in_class and current_class is not None:
                    current_class["methods"].append(fn_dict)
                else:
                    functions.append(fn_dict)

                current_decorators = []
                continue

            # Import detection
            import_match = re.match(
                r"^(?:from\s+(\S+)\s+)?import\s+(.+)$", stripped
            )
            if import_match:
                source = import_match.group(1)
                names_raw = import_match.group(2)
                names = SourceCodeIntelligenceEngine._parse_import_names(names_raw)
                imports.append({
                    "source": source,
                    "names": names,
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Variable detection
            var_match = re.match(r"^(\w+)\s*(?::\s*(\w+(?:\[.*?\])?))?\s*=\s*(.+)$", stripped)
            if var_match:
                var_name = var_match.group(1)
                var_type = var_match.group(2)
                var_value = var_match.group(3).strip()
                is_const = var_name.isupper() and len(var_name) > 1
                if not var_value.startswith("import ") and not var_value.startswith("from "):
                    variables.append({
                        "name": var_name,
                        "line": line_no,
                        "type": var_type,
                        "is_constant": is_const,
                    })

            # Enum detection (Python 3.4+ enum)
            enum_match = re.match(r"^class\s+(\w+)\(.*Enum.*\)\s*:", stripped)
            if enum_match:
                enum_name = enum_match.group(1)
                enum_values: list[str] = []
                j = i + 1
                while j < len(lines):
                    ej_line = lines[j].strip()
                    if ej_line.startswith("class ") or (ej_line and not ej_line.startswith(" ") and not ej_line.startswith("\t") and not ej_line.startswith("#") and not ej_line.startswith('"')):
                        break
                    ev_match = re.match(r"^\s*(\w+)\s*=", ej_line)
                    if ev_match:
                        enum_values.append(ev_match.group(1))
                    j += 1
                enums.append({
                    "name": enum_name,
                    "line": line_no,
                    "values": enum_values,
                })

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_import_names(names_raw: str) -> list[str]:
        names = []
        for part in names_raw.split(","):
            part = part.strip()
            if not part:
                continue
            if " as " in part:
                part = part.split(" as ")[0].strip()
            if "(" in part:
                part = part.replace("(", "").replace(")", "")
            names.append(part)
        return names

    @staticmethod
    def _parse_javascript(lines: list[str], rel_path: str) -> dict:
        return SourceCodeIntelligenceEngine._parse_js_like(lines, rel_path, "JavaScript")

    @staticmethod
    def _parse_typescript(lines: list[str], rel_path: str) -> dict:
        return SourceCodeIntelligenceEngine._parse_js_like(lines, rel_path, "TypeScript")

    @staticmethod
    def _parse_js_like(lines: list[str], rel_path: str, language: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []

        in_block_comment = False
        in_class = False
        current_class: dict | None = None
        class_brace_count = 0
        current_export = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            if not stripped:
                continue

            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//"):
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped:
                    in_block_comment = True
                    continue
                continue

            # Track export default
            if stripped.startswith("export "):
                current_export = True
                stripped = stripped.replace("export ", "", 1).strip()
            else:
                current_export = False

            # Interface detection (TypeScript)
            if_match = re.match(r"^(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{", stripped)
            if if_match:
                if_name = if_match.group(1)
                interface_props: list[str] = []
                interface_methods: list[str] = []
                j = i + 1
                brace_depth = 1
                while j < len(lines) and brace_depth > 0:
                    ij_line = lines[j].strip()
                    brace_depth += ij_line.count("{") - ij_line.count("}")
                    if brace_depth > 0:
                        prop_match = re.match(r"^\s*(\w+)\s*(?:\?|:)", ij_line)
                        if prop_match:
                            interface_props.append(prop_match.group(1))
                    j += 1
                interfaces.append({
                    "name": if_name,
                    "line": line_no,
                    "properties": interface_props,
                    "methods": interface_methods,
                })
                if current_export:
                    exports.append(if_name)
                continue

            # Enum detection (TypeScript)
            enum_match = re.match(r"^(?:export\s+)?enum\s+(\w+)\s*\{", stripped)
            if enum_match:
                enum_name = enum_match.group(1)
                enum_values: list[str] = []
                enum_content = stripped[stripped.index("{"):] if "{" in stripped else ""
                if enum_content:
                    vals = enum_content.strip("{} ").split(",")
                    for v in vals:
                        v_match = re.match(r"\s*(\w+)", v)
                        if v_match:
                            enum_values.append(v_match.group(1))
                if not enum_values:
                    j = i + 1
                    while j < len(lines):
                        ej_line = lines[j].strip()
                        if ej_line.startswith("}"):
                            break
                        ev_match = re.match(r"^\s*(\w+)", ej_line)
                        if ev_match:
                            enum_values.append(ev_match.group(1))
                        j += 1
                enums.append({
                    "name": enum_name,
                    "line": line_no,
                    "values": enum_values,
                })
                continue

            # Class detection
            class_match = re.match(
                r"^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*\{",
                stripped,
            )
            if class_match:
                cls_name = class_match.group(1)
                extends = class_match.group(2)
                implements_raw = class_match.group(3) or ""
                base_classes = []
                if extends:
                    base_classes.append(extends)
                if implements_raw:
                    base_classes.extend([b.strip() for b in implements_raw.split(",") if b.strip()])
                cls_dict = {
                    "name": cls_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "base_classes": base_classes,
                    "inherited_classes": [],
                    "methods": [],
                    "properties": [],
                    "decorators": [],
                    "visibility": "public",
                    "is_abstract": "abstract" in stripped,
                }
                classes.append(cls_dict)
                current_class = cls_dict
                in_class = True
                class_brace_count = stripped.count("{") - stripped.count("}")
                if current_export:
                    exports.append(cls_name)
                continue

            if in_class and current_class is not None:
                brace_diff = stripped.count("{") - stripped.count("}")
                class_brace_count += brace_diff
                if class_brace_count <= 0:
                    in_class = False
                    current_class = None
                    continue

                # Class property
                prop_match = re.match(r"^\s*(?:(public|private|protected)\s+)?(?:(static)\s+)?(?:(readonly)\s+)?(\w+)\s*(?:\?|:|=)", stripped)
                if prop_match:
                    visibility = prop_match.group(1) or "public"
                    prop_name = prop_match.group(4)
                    current_class["properties"].append({
                        "name": prop_name,
                        "type": None,
                        "visibility": visibility,
                        "is_static": bool(prop_match.group(2)),
                    })
                    continue

                # Method inside class
                method_match = re.match(
                    r"^\s*(?:(public|private|protected)\s+)?(?:(static)\s+)?(?:(async)\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*(\S+))?\s*\{",
                    stripped,
                )
                if method_match:
                    pass  # Will be caught below as function, but with parent class context

            # Function detection (regular & arrow assigned to const/let/var)
            fn_match = re.match(
                r"^(?:async\s+)?function\s+(?:\*\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*(\S+))?\s*\{",
                stripped,
            )
            if fn_match:
                fn_name = fn_match.group(1)
                params_raw = fn_match.group(2)
                return_type = fn_match.group(3)
                params = SourceCodeIntelligenceEngine._parse_js_params(params_raw)
                fn_dict = {
                    "name": fn_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "parameters": params,
                    "return_type": return_type,
                    "decorators": [],
                    "is_async": "async" in stripped,
                    "is_static": False,
                    "is_generator": "function*" in stripped or "*" in stripped.split("function")[0] if "function" in stripped else False,
                    "visibility": "public",
                    "parent_class": None,
                }
                if in_class and current_class is not None:
                    current_class["methods"].append(fn_dict)
                else:
                    functions.append(fn_dict)
                if current_export:
                    exports.append(fn_name)
                continue

            # Arrow function: const/let/var name = (params) => or name => {
            arrow_match = re.match(
                r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\(([^)]*)\)|(\w+))\s*=>",
                stripped,
            )
            if arrow_match:
                fn_name = arrow_match.group(1)
                params_raw = arrow_match.group(2) or arrow_match.group(3) or ""
                params = SourceCodeIntelligenceEngine._parse_js_params(params_raw)
                fn_dict = {
                    "name": fn_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "parameters": params,
                    "return_type": None,
                    "decorators": [],
                    "is_async": "async" in stripped,
                    "is_static": False,
                    "is_generator": False,
                    "visibility": "public",
                    "parent_class": None,
                }
                if in_class and current_class is not None:
                    current_class["methods"].append(fn_dict)
                else:
                    functions.append(fn_dict)
                if current_export:
                    exports.append(fn_name)
                continue

            # Import detection (ES modules)
            import_match = re.match(
                r"^import\s+(?:\{([^}]*)\}|\*\s+as\s+(\w+)|\s*(\w+))\s*(?:,\s*\{([^}]*)\})?\s+from\s+['\"]([^'\"]+)['\"]",
                stripped,
            )
            if import_match:
                names = []
                for g in [import_match.group(1), import_match.group(2), import_match.group(3), import_match.group(4)]:
                    if g:
                        names.extend([n.strip() for n in g.split(",") if n.strip()])
                source = import_match.group(5)
                imports.append({
                    "source": source,
                    "names": names or ["*"],
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Require detection
            require_match = re.match(
                r"^(?:const|let|var)\s+(?:\{[^}]*\}|\w+)\s*=\s*require\s*\(['\"]([^'\"]+)['\"]\)",
                stripped,
            )
            if require_match:
                source = require_match.group(1)
                imports.append({
                    "source": source,
                    "names": [],
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Variable detection (top-level)
            if not in_class:
                var_match = re.match(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::\s*(\w+))?\s*=", stripped)
                if var_match:
                    var_name = var_match.group(1)
                    var_type = var_match.group(2)
                    is_const = "const" in stripped
                    variables.append({
                        "name": var_name,
                        "line": line_no,
                        "type": var_type,
                        "is_constant": is_const,
                    })

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_js_params(params_raw: str) -> list[dict]:
        params = []
        if not params_raw or params_raw.strip() == "":
            return params
        for p in params_raw.split(","):
            p = p.strip()
            if not p:
                continue
            # Handle destructuring
            if p.startswith("{") or p.startswith("["):
                params.append({"name": p[:30] + "...", "type": None, "default": None})
                continue
            if ":" in p:
                p_name, p_type = p.split(":", 1)
                p_name = p_name.strip()
                p_type = p_type.strip().rstrip(")")
                if "=" in p_name:
                    p_name, p_default = p_name.split("=", 1)
                    p_name = p_name.strip()
                    p_default = p_default.strip()
                    params.append({"name": p_name, "type": p_type, "default": p_default})
                else:
                    params.append({"name": p_name, "type": p_type, "default": None})
            else:
                if "=" in p:
                    p_name, p_default = p.split("=", 1)
                    params.append({"name": p_name.strip(), "type": None, "default": p_default.strip()})
                else:
                    params.append({"name": p.strip(), "type": None, "default": None})
        return params

    @staticmethod
    def _parse_java(lines: list[str], rel_path: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []
        in_block_comment = False

        package_name = ""

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            if not stripped:
                continue
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//"):
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped:
                    in_block_comment = True
                    continue
                continue

            # Package
            pkg_match = re.match(r"^package\s+([\w.]+)\s*;", stripped)
            if pkg_match:
                package_name = pkg_match.group(1)
                continue

            # Import
            imp_match = re.match(r"^import\s+(?:static\s+)?([\w.*]+)\s*;", stripped)
            if imp_match:
                source = imp_match.group(1)
                imports.append({
                    "source": source,
                    "names": [],
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Interface
            if_match = re.match(r"^(?:public\s+)?interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{", stripped)
            if if_match:
                if_name = if_match.group(1)
                extends = if_match.group(2)
                intf_props: list[str] = []
                intf_methods: list[str] = []
                interfaces.append({
                    "name": if_name,
                    "line": line_no,
                    "properties": intf_props,
                    "methods": intf_methods,
                })
                continue

            # Enum
            enum_match = re.match(r"^(?:public\s+)?enum\s+(\w+)\s*\{", stripped)
            if enum_match:
                enum_name = enum_match.group(1)
                enum_vals: list[str] = []
                j = i + 1
                while j < len(lines):
                    ej_line = lines[j].strip()
                    if ej_line.startswith("}"):
                        break
                    ev_match = re.match(r"^\s*(\w+)", ej_line)
                    if ev_match:
                        enum_vals.append(ev_match.group(1))
                    j += 1
                enums.append({
                    "name": enum_name,
                    "line": line_no,
                    "values": enum_vals,
                })
                continue

            # Class
            class_match = re.match(
                r"^(?:(public|private|protected)\s+)?(?:abstract\s+)?(?:static\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*\{",
                stripped,
            )
            if class_match:
                visibility = class_match.group(1) or "public"
                cls_name = class_match.group(2)
                extends = class_match.group(3)
                implements_raw = class_match.group(4) or ""
                base_classes: list[str] = []
                if extends:
                    base_classes.append(extends)
                if implements_raw:
                    base_classes.extend([b.strip() for b in implements_raw.split(",") if b.strip()])
                cls_dict = {
                    "name": cls_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "base_classes": base_classes,
                    "inherited_classes": [],
                    "methods": [],
                    "properties": [],
                    "decorators": [],
                    "visibility": visibility,
                    "is_abstract": "abstract" in stripped,
                }
                classes.append(cls_dict)
                continue

            # Method
            method_match = re.match(
                r"^\s*(?:(public|private|protected)\s+)?(?:(static)\s+)?(?:(abstract)\s+)?(?:\w+\[?\]?)\s+(\w+)\s*\(([^)]*)\)\s*(?:\{|;|throws)",
                stripped,
            )
            if method_match:
                visibility = method_match.group(1) or "public"
                fn_name = method_match.group(4)
                params_raw = method_match.group(5)
                if fn_name != stripped.split("(")[0].strip().split()[-1]:
                    continue
                params = []
                for p in params_raw.split(","):
                    p = p.strip()
                    if not p:
                        continue
                    parts = p.split()
                    if len(parts) >= 1:
                        p_type = " ".join(parts[:-1]) if len(parts) > 1 else None
                        p_name = parts[-1].replace("...", "")
                        params.append({"name": p_name, "type": p_type, "default": None})
                fn_dict = {
                    "name": fn_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "parameters": params,
                    "return_type": None,
                    "decorators": [],
                    "is_async": False,
                    "is_static": bool(method_match.group(2)),
                    "is_generator": False,
                    "visibility": visibility,
                    "parent_class": None,
                }
                functions.append(fn_dict)
                continue

            # Field/property (top level in class context approximate)
            field_match = re.match(
                r"^\s*(?:(public|private|protected)\s+)?(?:(static)\s+)?(?:(final)\s+)?(\w+(?:<[^>]*>)?)\s+(\w+)\s*(?:=.*)?;",
                stripped,
            )
            if field_match and "(" not in stripped and ")" not in stripped:
                visibility = field_match.group(1) or "public"
                field_type = field_match.group(4)
                field_name = field_match.group(5)
                variables.append({
                    "name": field_name,
                    "line": line_no,
                    "type": field_type,
                    "is_constant": bool(field_match.group(3)),
                })

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_go(lines: list[str], rel_path: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []
        in_block_comment = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            if not stripped:
                continue
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//"):
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped:
                    in_block_comment = True
                    continue
                continue

            # Import
            imp_match = re.match(r'^import\s+(?:\(?\s*)["]([^"]+)["]', stripped)
            if imp_match:
                imports.append({
                    "source": imp_match.group(1),
                    "names": [],
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Multi-import block
            if stripped == "import (":
                j = i + 1
                while j < len(lines):
                    ij_line = lines[j].strip()
                    if ij_line == ")":
                        break
                    imp_path_match = re.match(r'^\s*["]([^"]+)["]', ij_line)
                    if imp_path_match:
                        imports.append({
                            "source": imp_path_match.group(1),
                            "names": [],
                            "is_external": False,
                            "is_duplicate": False,
                            "line": line_no,
                            "file_path": rel_path,
                        })
                    j += 1
                continue

            # Interface
            if_match = re.match(r"^type\s+(\w+)\s+interface\s*\{", stripped)
            if if_match:
                    interfaces.append({
                        "name": if_match.group(1),
                        "line": line_no,
                        "properties": [],
                        "methods": [],
                    })
                    continue

            # Struct
            struct_match = re.match(r"^type\s+(\w+)\s+struct\s*\{", stripped)
            if struct_match:
                struct_name = struct_match.group(1)
                struct_props: list[dict] = []
                j = i + 1
                brace_depth = 1
                while j < len(lines) and brace_depth > 0:
                    sj_line = lines[j].strip()
                    brace_depth += sj_line.count("{") - sj_line.count("}")
                    if brace_depth > 0 and sj_line and not sj_line.startswith("//") and not sj_line.startswith("/*"):
                        f_match = re.match(r"^\s*(\w+)\s+(\S+)", sj_line)
                        if f_match:
                            struct_props.append({
                                "name": f_match.group(1),
                                "type": f_match.group(2).rstrip("`").rstrip(","),
                                "visibility": "public",
                                "is_static": False,
                            })
                    j += 1
                cls_dict = {
                    "name": struct_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "base_classes": [],
                    "inherited_classes": [],
                    "methods": [],
                    "properties": struct_props,
                    "decorators": [],
                    "visibility": "public",
                    "is_abstract": False,
                }
                classes.append(cls_dict)
                continue

            # Function
            fn_match = re.match(
                r"^func\s+(?:(?:\([^)]+\))\s+)?(\w+)\s*\(([^)]*)\)\s*(?:\(?([^)]*)\)?\s*)?\{",
                stripped,
            )
            if fn_match:
                fn_name = fn_match.group(1)
                params_raw = fn_match.group(2)
                return_raw = fn_match.group(3) or ""
                params = []
                if params_raw:
                    for p in params_raw.split(","):
                        p = p.strip()
                        if not p:
                            continue
                        p_parts = p.split()
                        if len(p_parts) >= 2:
                            p_name = p_parts[0]
                            p_type = " ".join(p_parts[1:])
                            params.append({"name": p_name, "type": p_type, "default": None})
                        elif len(p_parts) == 1:
                            params.append({"name": p_parts[0], "type": None, "default": None})
                is_method = "(" in stripped.split("func")[1].strip()[:2] if "func" in stripped else False
                fn_dict = {
                    "name": fn_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "parameters": params,
                    "return_type": return_raw.strip() or None,
                    "decorators": [],
                    "is_async": False,
                    "is_static": False,
                    "is_generator": False,
                    "visibility": "public",
                    "parent_class": None,
                }
                functions.append(fn_dict)
                if fn_name[0].isupper():
                    exports.append(fn_name)
                continue

            # Variable with := or =
            var_match = re.match(r"^(?:var\s+)?(\w+)\s*(?:=|:=)", stripped)
            if var_match and not stripped.startswith("import") and not stripped.startswith("package"):
                var_name = var_match.group(1)
                is_const = False
                variables.append({
                    "name": var_name,
                    "line": line_no,
                    "type": None,
                    "is_constant": is_const,
                })

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_rust(lines: list[str], rel_path: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []
        in_block_comment = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            if not stripped:
                continue
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//"):
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped:
                    in_block_comment = True
                    continue
                continue

            # Module declaration
            mod_match = re.match(r"^(?:pub\s+)?mod\s+(\w+)\s*;", stripped)
            if mod_match:
                continue

            # Use/import
            use_match = re.match(r"^(?:pub\s+)?use\s+([\w:]+(?:\s+as\s+\w+)?)\s*;", stripped)
            if use_match:
                source = use_match.group(1)
                imports.append({
                    "source": source,
                    "names": [],
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Struct
            struct_match = re.match(r"^(?:pub\s+)?(?:struct\s+(\w+))(?:\s*\{|;|$)", stripped)
            if struct_match:
                struct_name = struct_match.group(1)
                struct_props: list[dict] = []
                if "{" in stripped:
                    j = i + 1
                    brace_depth = 1
                    while j < len(lines) and brace_depth > 0:
                        sj_line = lines[j].strip()
                        brace_depth += sj_line.count("{") - sj_line.count("}")
                        if brace_depth > 0 and sj_line and not sj_line.startswith("//"):
                            f_match = re.match(r"^\s*(?:pub\s+)?(\w+)\s*:\s*(\S+)", sj_line)
                            if f_match:
                                struct_props.append({
                                    "name": f_match.group(1),
                                    "type": f_match.group(2).rstrip(","),
                                    "visibility": "public",
                                    "is_static": False,
                                })
                        j += 1
                classes.append({
                    "name": struct_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "base_classes": [],
                    "inherited_classes": [],
                    "methods": [],
                    "properties": struct_props,
                    "decorators": [],
                    "visibility": "public",
                    "is_abstract": False,
                })
                continue

            # Enum
            enum_match = re.match(r"^(?:pub\s+)?enum\s+(\w+)\s*\{", stripped)
            if enum_match:
                enum_name = enum_match.group(1)
                enum_vals: list[str] = []
                j = i + 1
                brace_depth = 1
                while j < len(lines) and brace_depth > 0:
                    ej_line = lines[j].strip()
                    brace_depth += ej_line.count("{") - ej_line.count("}")
                    if brace_depth > 0:
                        v_match = re.match(r"^\s*(\w+)", ej_line)
                        if v_match:
                            enum_vals.append(v_match.group(1))
                    j += 1
                enums.append({
                    "name": enum_name,
                    "line": line_no,
                    "values": enum_vals,
                })
                continue

            # Trait
            trait_match = re.match(r"^(?:pub\s+)?trait\s+(\w+)(?:\s*\{|$)", stripped)
            if trait_match:
                interfaces.append({
                    "name": trait_match.group(1),
                    "line": line_no,
                    "properties": [],
                    "methods": [],
                })
                continue

            # Function
            fn_match = re.match(
                r"^(?:pub\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\S+))?\s*(?:\{|where)",
                stripped,
            )
            if fn_match:
                fn_name = fn_match.group(1)
                params_raw = fn_match.group(2)
                return_type = fn_match.group(3)
                params = []
                if params_raw:
                    for p in params_raw.split(","):
                        p = p.strip()
                        if not p:
                            continue
                        if ":" in p:
                            p_name, p_type = p.split(":", 1)
                            if "=" in p_name:
                                p_name, p_default = p_name.split("=", 1)
                            params.append({
                                "name": p_name.strip(),
                                "type": p_type.strip(),
                                "default": None,
                            })
                fn_dict = {
                    "name": fn_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "parameters": params,
                    "return_type": return_type,
                    "decorators": [],
                    "is_async": "async" in stripped,
                    "is_static": False,
                    "is_generator": False,
                    "visibility": "public" if stripped.startswith("pub") else "private",
                    "parent_class": None,
                }
                functions.append(fn_dict)
                if stripped.startswith("pub"):
                    exports.append(fn_name)
                continue

            # Constant
            const_match = re.match(r"^(?:pub\s+)?const\s+(\w+)\s*:", stripped)
            if const_match:
                variables.append({
                    "name": const_match.group(1),
                    "line": line_no,
                    "type": None,
                    "is_constant": True,
                })
                continue

            # Let variable
            let_match = re.match(r"^(?:pub\s+)?(?:let\s+)(?:mut\s+)?(\w+)", stripped)
            if let_match:
                variables.append({
                    "name": let_match.group(1),
                    "line": line_no,
                    "type": None,
                    "is_constant": True,
                })

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_php(lines: list[str], rel_path: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []
        in_block_comment = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            if not stripped:
                continue
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//") or stripped.startswith("#"):
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped:
                    in_block_comment = True
                    continue
                continue

            # Use/import
            use_match = re.match(r"^use\s+([\w\\]+)(?:\s+as\s+(\w+))?\s*;", stripped)
            if use_match:
                source = use_match.group(1)
                imports.append({
                    "source": source,
                    "names": [use_match.group(2) or source.split("\\")[-1]],
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Require/include
            req_match = re.match(r"^(?:require|include)(?:_once)?\s+['\"]([^'\"]+)['\"]\s*;", stripped)
            if req_match:
                imports.append({
                    "source": req_match.group(1),
                    "names": [],
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Interface
            if_match = re.match(r"^(?:abstract\s+)?interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{", stripped)
            if if_match:
                interfaces.append({
                    "name": if_match.group(1),
                    "line": line_no,
                    "properties": [],
                    "methods": [],
                })
                continue

            # Enum (PHP 8.1+)
            enum_match = re.match(r"^(?:enum\s+(\w+))\s*(?:\s*\{|:)", stripped)
            if enum_match:
                enums.append({
                    "name": enum_match.group(1),
                    "line": line_no,
                    "values": [],
                })
                continue

            # Class
            class_match = re.match(
                r"^(?:(abstract|final)\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*\{",
                stripped,
            )
            if class_match:
                cls_name = class_match.group(2)
                extends = class_match.group(3)
                implements_raw = class_match.group(4) or ""
                base_classes: list[str] = []
                if extends:
                    base_classes.append(extends)
                if implements_raw:
                    base_classes.extend([b.strip() for b in implements_raw.split(",") if b.strip()])
                cls_dict = {
                    "name": cls_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "base_classes": base_classes,
                    "inherited_classes": [],
                    "methods": [],
                    "properties": [],
                    "decorators": [],
                    "visibility": "public",
                    "is_abstract": class_match.group(1) == "abstract",
                }
                classes.append(cls_dict)
                continue

            # Method
            method_match = re.match(
                r"^\s*(?:(public|private|protected)\s+)?(?:(static)\s+)?(?:abstract\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*(?:\{|;)",
                stripped,
            )
            if method_match:
                visibility = method_match.group(1) or "public"
                fn_name = method_match.group(3)
                params_raw = method_match.group(4) or ""
                params = []
                for p in params_raw.split(","):
                    p = p.strip()
                    if not p:
                        continue
                    if "$" in p:
                        p_name = p.split("$")[-1].split("=")[0].strip()
                        p_type = None
                        if " " in p and p.index(" ") < (p.index("$") if "$" in p else 999):
                            p_type = p.split("$")[0].strip()
                        p_default = p.split("=")[-1].strip() if "=" in p else None
                        params.append({"name": p_name, "type": p_type, "default": p_default})
                fn_dict = {
                    "name": fn_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "parameters": params,
                    "return_type": None,
                    "decorators": [],
                    "is_async": False,
                    "is_static": bool(method_match.group(2)),
                    "is_generator": False,
                    "visibility": visibility,
                    "parent_class": None,
                }
                functions.append(fn_dict)
                continue

            # Variable
            var_match = re.match(r"^\s*\$(\w+)\s*=", stripped)
            if var_match:
                variables.append({
                    "name": "$" + var_match.group(1),
                    "line": line_no,
                    "type": None,
                    "is_constant": False,
                })

            # Define constant
            def_match = re.match(r"^define\s*\(\s*['\"](\w+)['\"]", stripped)
            if def_match:
                variables.append({
                    "name": def_match.group(1),
                    "line": line_no,
                    "type": None,
                    "is_constant": True,
                })

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_c(lines: list[str], rel_path: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []
        in_block_comment = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            if not stripped:
                continue
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//"):
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped:
                    in_block_comment = True
                    continue
                continue

            # Using directive
            using_match = re.match(r"^using\s+([\w.]+)\s*;", stripped)
            if using_match:
                imports.append({
                    "source": using_match.group(1),
                    "names": [],
                    "is_external": False,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            # Namespace
            ns_match = re.match(r"^namespace\s+([\w.]+)\s*;", stripped)
            if ns_match:
                continue

            # Interface
            if_match = re.match(r"^(?:public\s+)?interface\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{", stripped)
            if if_match:
                interfaces.append({
                    "name": if_match.group(1),
                    "line": line_no,
                    "properties": [],
                    "methods": [],
                })
                continue

            # Enum
            enum_match = re.match(r"^(?:public\s+)?enum\s+(\w+)\s*(?:\s*\{|:)", stripped)
            if enum_match:
                enums.append({
                    "name": enum_match.group(1),
                    "line": line_no,
                    "values": [],
                })
                continue

            # Struct (C# also has struct as value type)
            struct_match = re.match(r"^(?:public\s+)?(?:readonly\s+)?struct\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{", stripped)
            if struct_match:
                classes.append({
                    "name": struct_match.group(1),
                    "line_start": line_no,
                    "line_end": line_no,
                    "base_classes": [b.strip() for b in (struct_match.group(2) or "").split(",") if b.strip()],
                    "inherited_classes": [],
                    "methods": [],
                    "properties": [],
                    "decorators": [],
                    "visibility": "public",
                    "is_abstract": False,
                })
                continue

            # Class
            class_match = re.match(
                r"^(?:(public|private|protected|internal)\s+)?(?:abstract\s+)?(?:static\s+)?(?:partial\s+)?(?:class|record)\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{",
                stripped,
            )
            if class_match:
                visibility = class_match.group(1) or "public"
                cls_name = class_match.group(2)
                bases_raw = class_match.group(3) or ""
                base_classes = [b.strip() for b in bases_raw.split(",") if b.strip()]
                cls_dict = {
                    "name": cls_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "base_classes": base_classes,
                    "inherited_classes": [],
                    "methods": [],
                    "properties": [],
                    "decorators": [],
                    "visibility": visibility,
                    "is_abstract": "abstract" in stripped,
                }
                classes.append(cls_dict)
                continue

            # Method
            method_match = re.match(
                r"^\s*(?:(public|private|protected|internal)\s+)?(?:(static)\s+)?(?:(async)\s+)?(?:(override|virtual|abstract)\s+)?(\w+(?:<[^>]*>)?)\s+(\w+)\s*\(([^)]*)\)\s*(?:\{|;)",
                stripped,
            )
            if method_match:
                visibility = method_match.group(1) or "public"
                return_type = method_match.group(5)
                fn_name = method_match.group(6)
                params_raw = method_match.group(7) or ""
                params = []
                for p in params_raw.split(","):
                    p = p.strip()
                    if not p:
                        continue
                    p_parts = p.split()
                    if len(p_parts) >= 2:
                        p_type = " ".join(p_parts[:-1])
                        p_name = p_parts[-1].replace("@", "")
                        params.append({"name": p_name, "type": p_type, "default": None})
                fn_dict = {
                    "name": fn_name,
                    "line_start": line_no,
                    "line_end": line_no,
                    "parameters": params,
                    "return_type": return_type,
                    "decorators": [],
                    "is_async": bool(method_match.group(3)),
                    "is_static": bool(method_match.group(2)),
                    "is_generator": False,
                    "visibility": visibility,
                    "parent_class": None,
                }
                functions.append(fn_dict)
                continue

            # Property
            prop_match = re.match(
                r"^\s*(?:(public|private|protected|internal)\s+)?(?:(static)\s+)?(?:(readonly)\s+)?(\w+(?:<[^>]*>)?)\s+(\w+)\s*\{",
                stripped,
            )
            if prop_match and "(" not in stripped:
                visibility = prop_match.group(1) or "public"
                variables.append({
                    "name": prop_match.group(4),
                    "line": line_no,
                    "type": prop_match.group(3),
                    "is_constant": False,
                })
                continue

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_cpp(lines: list[str], rel_path: str) -> dict:
        return SourceCodeIntelligenceEngine._parse_c(lines, rel_path)

    @staticmethod
    def _parse_html(lines: list[str], rel_path: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []
        in_script = False
        in_style = False
        script_lang = ""

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            script_tag = re.search(r"<script\b([^>]*)>", stripped, re.IGNORECASE)
            if script_tag:
                in_script = True
                attrs = script_tag.group(1)
                if "type" not in attrs or "javascript" in attrs.lower() or "ecmascript" in attrs.lower():
                    script_lang = "JavaScript"
                else:
                    script_lang = ""
                continue
            style_tag = re.search(r"<style\b([^>]*)>", stripped, re.IGNORECASE)
            if style_tag:
                in_style = True
                continue
            if in_script:
                if "</script>" in stripped:
                    in_script = False
                    continue
                if script_lang:
                    sub = SourceCodeIntelligenceEngine._parse_js_like([line], script_lang, script_lang)
                    classes.extend(sub.get("classes", []))
                    functions.extend(sub.get("functions", []))
                    imports.extend(sub.get("imports", []))
                    variables.extend(sub.get("variables", []))
                    exports.extend(sub.get("exports", []))
                continue
            if in_style:
                if "</style>" in stripped:
                    in_style = False
                    continue
                continue

            id_match = re.match(r'^\s*<[\w-]+\s[^>]*\bid=["\']([^"\']+)["\']', stripped)
            if id_match:
                variables.append({"name": id_match.group(1), "line": line_no, "type": "id", "is_constant": False})

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_css(lines: list[str], rel_path: str) -> dict:
        classes: list[dict] = []
        functions: list[dict] = []
        imports: list[dict] = []
        enums: list[dict] = []
        interfaces: list[dict] = []
        variables: list[dict] = []
        exports: list[str] = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1

            import_match = re.match(r"@import\s+['\"]([^'\"]+)['\"]", stripped)
            if import_match:
                imports.append({
                    "source": import_match.group(1),
                    "names": [],
                    "is_external": True,
                    "is_duplicate": False,
                    "line": line_no,
                    "file_path": rel_path,
                })
                continue

            custom_prop = re.match(r"--([\w-]+)\s*:", stripped)
            if custom_prop:
                variables.append({
                    "name": custom_prop.group(1),
                    "line": line_no,
                    "type": "custom-property",
                    "is_constant": False,
                })
                continue

            class_selector = re.match(r"\.([\w-]+)\s*\{", stripped)
            if class_selector:
                variables.append({
                    "name": class_selector.group(1),
                    "line": line_no,
                    "type": "css-class",
                    "is_constant": False,
                })
                continue

            id_selector = re.match(r"#([\w-]+)\s*\{", stripped)
            if id_selector:
                variables.append({
                    "name": id_selector.group(1),
                    "line": line_no,
                    "type": "css-id",
                    "is_constant": False,
                })
                continue

            keyframe_match = re.match(r"@keyframes\s+([\w-]+)", stripped)
            if keyframe_match:
                exports.append(keyframe_match.group(1))
                continue

        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "enums": enums,
            "interfaces": interfaces,
            "variables": variables,
            "exports": exports,
        }

    @staticmethod
    def _parse_json(lines: list[str], rel_path: str) -> dict:
        variables: list[dict] = []
        content = "".join(lines)
        try:
            import json as json_mod
            data = json_mod.loads(content)
            if isinstance(data, dict):
                for key in data:
                    variables.append({
                        "name": key,
                        "line": 1,
                        "type": type(data[key]).__name__ if data[key] is not None else "null",
                        "is_constant": True,
                    })
        except (ValueError, TypeError):
            pass
        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": [], "functions": [], "imports": [],
            "enums": [], "interfaces": [], "variables": variables,
            "exports": [],
        }

    @staticmethod
    def _parse_markdown(lines: list[str], rel_path: str) -> dict:
        variables: list[dict] = []
        exports: list[str] = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            line_no = i + 1
            heading = re.match(r"^(#{1,6})\s+(.+)", stripped)
            if heading:
                level = len(heading.group(1))
                title = heading.group(2).strip()
                exports.append(title)
                variables.append({
                    "name": title,
                    "line": line_no,
                    "type": f"h{level}",
                    "is_constant": False,
                })
        loc = SourceCodeIntelligenceEngine._count_loc(lines)
        return {
            "loc": loc,
            "classes": [], "functions": [], "imports": [],
            "enums": [], "interfaces": [], "variables": variables,
            "exports": exports,
        }
