import ast
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
from app.repositories.code_quality_engine import CodeQualityEngine


class FunctionClassEngine:

    def analyze(self, workspace_path: Path) -> dict:
        all_functions: list[dict] = []
        all_classes: list[dict] = []
        all_relationships: list[dict] = []
        class_inheritance_map: dict[str, list[str]] = defaultdict(list)
        class_file_map: dict[str, str] = {}
        function_file_map: dict[str, list[str]] = defaultdict(list)
        all_called_funcs: dict[str, set[str]] = defaultdict(set)
        all_definitions: dict[str, str] = {}

        total_funcs = 0
        total_classes = 0
        total_methods = 0
        health_counts: dict[str, int] = defaultdict(int)
        lang_func_count: dict[str, int] = defaultdict(int)
        lang_class_count: dict[str, int] = defaultdict(int)
        complexities: list[int] = []
        maintainabilities: list[float] = []
        undocumented = 0
        unused_set: set[str] = set()
        recursive_set: set[str] = set()

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

                lines = content.split("\n")

                if language == "Python":
                    funcs, classes, relationships, stats = self._analyze_python(
                        content, lines, rel_path, f, language
                    )
                elif language in ("JavaScript", "TypeScript"):
                    funcs, classes, relationships, stats = self._analyze_jsts(
                        content, lines, rel_path, f, language
                    )
                elif language in ("Java", "C", "C++"):
                    funcs, classes, relationships, stats = self._analyze_c_family(
                        content, lines, rel_path, f, language
                    )
                elif language in ("HTML", "CSS", "JSON"):
                    funcs, classes, relationships, stats = self._analyze_markup(
                        content, lines, rel_path, f, language
                    )
                else:
                    continue

                total_funcs += stats["func_count"]
                total_classes += stats["class_count"]
                total_methods += stats["method_count"]
                lang_func_count[language] += stats["func_count"]
                lang_class_count[language] += stats["class_count"]
                complexities.extend(stats["complexities"])
                maintainabilities.extend(stats["maintainabilities"])
                undocumented += stats["undocumented"]
                for h, c in stats.get("health_counts", {}).items():
                    health_counts[h] += c
                for fn in stats.get("unused_funcs", []):
                    unused_set.add(fn)
                for fn in stats.get("recursive_funcs", []):
                    recursive_set.add(fn)

                for func in funcs:
                    function_file_map[func["name"]].append(rel_path)
                    all_definitions[func["name"]] = rel_path
                for cls in classes:
                    class_file_map[cls["name"]] = rel_path
                    state = cls.get("_state", {})
                    for parent in state.get("base_classes", []):
                        class_inheritance_map[parent].append(cls["name"])

                for called in stats.get("called_funcs", []):
                    all_called_funcs[called].add(rel_path)

                all_functions.extend(funcs)
                all_classes.extend(classes)
                all_relationships.extend(relationships)

        for func in all_functions:
            fn = func["name"]
            callers_list = []
            for caller_name, called_set in all_called_funcs.items():
                if fn in called_set:
                    caller_file = function_file_map.get(caller_name, [])
                    callers_list.append(f"{caller_name} ({', '.join(caller_file)})" if caller_file else caller_name)
            func["_callers"] = callers_list
            fn_file = function_file_map.get(fn, [])
            func["_is_unused"] = fn in unused_set or (len(callers_list) == 0 and not fn.startswith("_"))
            func["_is_recursive"] = fn in recursive_set
            func["_cross_file_calls"] = list(all_called_funcs.get(fn, set()))

        all_func_names = {f["name"] for f in all_functions}
        all_class_names = {c["name"] for c in all_classes}

        ai_insights = self._generate_ai_insights(all_functions, all_classes)

        avg_complexity = (sum(complexities) / len(complexities)) if complexities else 0.0
        avg_maint = (sum(maintainabilities) / len(maintainabilities)) if maintainabilities else 100.0
        total_issues = sum(len(f.get("issues", [])) for f in all_functions) + sum(len(c.get("issues", [])) for c in all_classes)

        return {
            "functions": all_functions,
            "classes": all_classes,
            "relationships": all_relationships,
            "class_relationships": self._build_class_relationships(all_classes, class_inheritance_map),
            "stats": {
                "total_functions": total_funcs,
                "total_classes": total_classes,
                "total_methods": total_methods,
                "average_complexity": round(avg_complexity, 1),
                "average_maintainability": round(avg_maint, 1),
                "total_issues": total_issues,
                "language_breakdown": {**lang_func_count, **{f"_{k}": v for k, v in lang_class_count.items()}},
                "health_counts": dict(health_counts),
                "unused_functions": len(unused_set),
                "recursive_functions": len(recursive_set),
                "undocumented_count": undocumented,
            },
            "ai_insights": ai_insights,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _analyze_python(self, content: str, lines: list[str],
                        rel_path: str, file_name: str, language: str) -> tuple:
        functions: list[dict] = []
        classes: list[dict] = []
        relationships: list[dict] = []
        all_defined: set[str] = set()
        all_called: set[str] = set()
        all_classes_defined: set[str] = set()
        complexities_list: list[int] = []
        maintainabilities_list: list[float] = []
        health_counts: dict[str, int] = defaultdict(int)
        unused_funcs: set[str] = set()
        recursive_funcs: set[str] = set()
        undocumented_count = 0
        method_count = 0

        module = rel_path.replace("/", ".").rsplit(".", 1)[0] if "." in rel_path else rel_path

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._analyze_python_fallback(lines, rel_path, file_name, language)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._extract_python_function(node, rel_path, file_name, language, module, lines, False)
                functions.append(func_info)
                all_defined.add(node.name)
                complexities_list.append(func_info["cyclomatic_complexity"])
                maintainabilities_list.append(func_info["maintainability_score"])
                health_counts[func_info["health_status"]] += 1
                if not func_info["has_documentation"]:
                    undocumented_count += 1

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            all_called.add(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            all_called.add(child.func.attr)

                # Check recursion
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == node.name:
                        recursive_funcs.add(node.name)

                # Check async
                if isinstance(node, ast.AsyncFunctionDef):
                    func_info["is_async"] = True

            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = self._extract_python_function(node, rel_path, file_name, language, module, lines, True)
                functions.append(func_info)
                all_defined.add(node.name)
                complexities_list.append(func_info["cyclomatic_complexity"])
                maintainabilities_list.append(func_info["maintainability_score"])
                health_counts[func_info["health_status"]] += 1
                if not func_info["has_documentation"]:
                    undocumented_count += 1
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            all_called.add(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            all_called.add(child.func.attr)

            elif isinstance(node, ast.ClassDef):
                cls_info = self._extract_python_class(node, rel_path, file_name, language, module, lines)
                classes.append(cls_info)
                all_classes_defined.add(node.name)
                method_count += len(cls_info["methods"])
                complexities_list.append(cls_info["complexity"])
                maintainabilities_list.append(cls_info["maintainability_score"])
                health_counts[cls_info["health_status"]] += 1
                if not cls_info["has_documentation"]:
                    undocumented_count += 1

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_count_inner = 1
                        all_defined.add(item.name)
                        complexities_list.append(self._compute_cyclomatic_complexity_ast(item))
                        for child in ast.walk(item):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Name):
                                    all_called.add(child.func.id)
                                elif isinstance(child.func, ast.Attribute):
                                    all_called.add(child.func.attr)

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            all_called.add(child.func.id)

        # Detect unused functions (defined but never called)
        for fn_name in all_defined:
            if fn_name not in all_called and not fn_name.startswith("__"):
                unused_funcs.add(fn_name)

        return (
            functions,
            classes,
            relationships,
            {
                "func_count": len(functions),
                "class_count": len(classes),
                "method_count": method_count,
                "complexities": complexities_list,
                "maintainabilities": maintainabilities_list,
                "undocumented": undocumented_count,
                "health_counts": dict(health_counts),
                "unused_funcs": list(unused_funcs),
                "recursive_funcs": list(recursive_funcs),
                "called_funcs": list(all_called),
            },
        )

    def _analyze_python_fallback(self, lines: list[str], rel_path: str,
                                  file_name: str, language: str) -> tuple:
        return self._analyze_with_regex(lines, rel_path, file_name, language)

    def _extract_python_function(self, node, rel_path: str, file_name: str,
                                  language: str, module: str, lines: list[str],
                                  is_async: bool) -> dict:
        name = node.name
        params: list[dict] = []
        for arg in node.args.args:
            arg_name = arg.arg
            arg_type = ast.unparse(arg.annotation) if arg.annotation else None
            params.append({
                "name": arg_name,
                "type": arg_type,
                "default_value": None,
                "is_optional": False,
            })
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            idx = defaults_offset + i
            if idx >= 0 and idx < len(params):
                params[idx]["default_value"] = ast.unparse(default)
                params[idx]["is_optional"] = True

        return_type = ast.unparse(node.returns) if node.returns else None
        decorators = [ast.unparse(d) for d in node.decorator_list]
        is_generator = self._is_generator(node)
        is_lambda = False

        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start_line + 1
        loc = max(0, end_line - start_line)

        complexity = self._compute_cyclomatic_complexity_ast(node)
        has_doc = ast.get_docstring(node) is not None
        issues = self._detect_function_issues(name, params, complexity, loc, has_doc)
        maint = self._compute_function_maintainability(complexity, loc, len(issues), has_doc)
        health = self._score_to_health(maint)

        return {
            "name": name,
            "file_path": rel_path,
            "file_name": file_name,
            "language": language,
            "module": module,
            "parameters": params,
            "return_type": return_type,
            "decorators": decorators,
            "is_async": is_async,
            "is_generator": is_generator,
            "is_lambda": is_lambda,
            "visibility": "public",
            "lines_of_code": loc,
            "cyclomatic_complexity": complexity,
            "maintainability_score": round(maint, 1),
            "has_documentation": has_doc,
            "issue_count": len(issues),
            "health_status": health,
            "issues": issues,
            "ai_insight": self._generate_function_insight(name, params, complexity, loc, has_doc, health, issues),
        }

    def _extract_python_class(self, node, rel_path: str, file_name: str,
                               language: str, module: str, lines: list[str]) -> dict:
        name = node.name
        base_classes = [ast.unparse(b) for b in node.bases]
        decorators = [ast.unparse(d) for d in node.decorator_list]
        is_abstract = any("abstract" in d.lower() or "ABC" in d for d in decorators + base_classes)

        methods: list[dict] = []
        properties: list[str] = []
        constructors: list[dict] = []
        interfaces: list[str] = []
        total_loc = 0
        total_complexity = 0

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_async = isinstance(item, ast.AsyncFunctionDef)
                method_info = self._extract_python_method(item, rel_path, file_name, language, module, name, lines, is_async)
                methods.append(method_info)
                total_loc += method_info["lines_of_code"]
                total_complexity += method_info["cyclomatic_complexity"]

                if method_info["name"] == "__init__":
                    constructors.append(method_info)

                for d in method_info["decorators"]:
                    if "property" in d:
                        properties.append(method_info["name"])

            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if any(isinstance(a, ast.Name) and a.id == "Property" for a in ast.walk(item.value) if isinstance(a, ast.Name)):
                            properties.append(target.id)
                    elif isinstance(target, ast.Attribute):
                        properties.append(target.attr)

        # Detect interfaces implemented
        for base in base_classes:
            if "Interface" in base or "Protocol" in base:
                interfaces.append(base)

        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start_line + 1
        loc = max(0, end_line - start_line + 1)

        complexity = max(total_complexity, 1)
        has_doc = ast.get_docstring(node) is not None
        total_issues_count = sum(len(m.get("issues", [])) for m in methods) + len(methods) * 2
        issues = self._detect_class_issues(name, len(methods), len(properties), loc, has_doc)
        maint = self._compute_class_maintainability(complexity, loc, len(issues), has_doc)
        health = self._score_to_health(maint)

        child_classes: list[str] = []

        return {
            "name": name,
            "file_path": rel_path,
            "file_name": file_name,
            "language": language,
            "module": module,
            "base_classes": base_classes,
            "parent_class": base_classes[0] if base_classes else None,
            "child_classes": child_classes,
            "methods": methods,
            "properties": properties,
            "constructors": constructors,
            "decorators": decorators,
            "interfaces": interfaces,
            "is_abstract": is_abstract,
            "lines_of_code": loc,
            "complexity": complexity,
            "maintainability_score": round(maint, 1),
            "has_documentation": has_doc,
            "issue_count": len(issues),
            "health_status": health,
            "issues": issues,
            "ai_insight": self._generate_class_insight(name, len(methods), len(properties), complexity, loc, health, issues),
            "_state": {
                "base_classes": base_classes,
            },
        }

    def _extract_python_method(self, item, rel_path: str, file_name: str,
                                language: str, module: str, parent_class: str,
                                lines: list[str], is_async: bool) -> dict:
        name = item.name
        params: list[dict] = []
        for arg in item.args.args:
            arg_name = arg.arg
            arg_type = ast.unparse(arg.annotation) if arg.annotation else None
            params.append({
                "name": arg_name,
                "type": arg_type,
                "default_value": None,
                "is_optional": False,
            })
        defaults_offset = len(item.args.args) - len(item.args.defaults)
        for i, default in enumerate(item.args.defaults):
            idx = defaults_offset + i
            if idx >= 0 and idx < len(params):
                params[idx]["default_value"] = ast.unparse(default)
                params[idx]["is_optional"] = True

        return_type = ast.unparse(item.returns) if item.returns else None
        decorators = [ast.unparse(d) for d in item.decorator_list]
        is_static = any("staticmethod" in d for d in decorators)
        is_classmethod = any("classmethod" in d for d in decorators)
        is_property = any("property" in d for d in decorators)
        is_generator = self._is_generator(item)

        start_line = item.lineno - 1
        end_line = item.end_lineno if hasattr(item, "end_lineno") and item.end_lineno else start_line + 1
        loc = max(0, end_line - start_line)

        complexity = self._compute_cyclomatic_complexity_ast(item)
        has_doc = ast.get_docstring(item) is not None
        issues = self._detect_function_issues(name, params, complexity, loc, has_doc)
        maint = self._compute_function_maintainability(complexity, loc, len(issues), has_doc)
        health = self._score_to_health(maint)

        return {
            "name": name,
            "parent_class": parent_class,
            "parameters": params,
            "return_type": return_type,
            "decorators": decorators,
            "is_async": is_async,
            "is_static": is_static,
            "is_classmethod": is_classmethod,
            "is_property": is_property,
            "visibility": "public" if not name.startswith("_") else ("protected" if name.startswith("_") and not name.startswith("__") else "private"),
            "lines_of_code": loc,
            "cyclomatic_complexity": complexity,
            "maintainability_score": round(maint, 1),
            "has_documentation": has_doc,
            "issue_count": len(issues),
            "health_status": health,
            "issues": issues,
            "ai_insight": "",
        }

    def _analyze_jsts(self, content: str, lines: list[str],
                       rel_path: str, file_name: str, language: str) -> tuple:
        return self._analyze_with_regex(lines, rel_path, file_name, language)

    def _analyze_c_family(self, content: str, lines: list[str],
                           rel_path: str, file_name: str, language: str) -> tuple:
        return self._analyze_with_regex(lines, rel_path, file_name, language)

    def _analyze_markup(self, content: str, lines: list[str],
                         rel_path: str, file_name: str, language: str) -> tuple:
        functions: list[dict] = []
        classes: list[dict] = []
        relationships: list[dict] = []
        all_called: set[str] = set()
        complexities: list[int] = []
        maintainabilities: list[float] = []
        health_counts: dict[str, int] = defaultdict(int)
        method_count = 0
        undocumented = 0

        module = rel_path.replace("/", ".").rsplit(".", 1)[0] if "." in rel_path else rel_path

        if language == "CSS":
            class_matches = re.findall(r'\.([\w-]+)\s*\{', content)
            id_matches = re.findall(r'#([\w-]+)\s*\{', content)
            media_queries = re.findall(r'@media\s+[^{]+\{', content)
            func_matches = re.findall(r'@([\w-]+)\s+(?:\([^)]*\)\s*)?\{', content)

            for name in set(class_matches):
                classes.append({
                    "name": f".{name}",
                    "file_path": rel_path,
                    "file_name": file_name,
                    "language": language,
                    "module": module,
                    "base_classes": [],
                    "parent_class": None,
                    "child_classes": [],
                    "methods": [],
                    "properties": [],
                    "constructors": [],
                    "decorators": [],
                    "interfaces": [],
                    "is_abstract": False,
                    "lines_of_code": 1,
                    "complexity": 1,
                    "maintainability_score": 100.0,
                    "has_documentation": False,
                    "issue_count": 0,
                    "health_status": "Good",
                    "issues": [],
                    "ai_insight": "",
                    "_state": {"base_classes": []},
                })

            for name in set(id_matches):
                classes.append({
                    "name": f"#{name}",
                    "file_path": rel_path,
                    "file_name": file_name,
                    "language": language,
                    "module": module,
                    "base_classes": [],
                    "parent_class": None,
                    "child_classes": [],
                    "methods": [],
                    "properties": [],
                    "constructors": [],
                    "decorators": [],
                    "interfaces": [],
                    "is_abstract": False,
                    "lines_of_code": 1,
                    "complexity": 1,
                    "maintainability_score": 100.0,
                    "has_documentation": False,
                    "issue_count": 0,
                    "health_status": "Good",
                    "issues": [],
                    "ai_insight": "",
                    "_state": {"base_classes": []},
                })

            class_count = len(class_matches) + len(id_matches) + len(media_queries)

        elif language == "HTML":
            tags = re.findall(r'<([\w-]+)[^>]*>', content)
            template_funcs = re.findall(r'\{[\s%]\s*(?:function|def)\s+(\w+)', content)
            script_funcs = re.findall(r'(?:function|def)\s+(\w+)\s*\(', content)
            funcs_found = [f for f in set(template_funcs + script_funcs) if f not in ("if", "for", "while")]

            for name in funcs_found:
                functions.append({
                    "name": name,
                    "file_path": rel_path,
                    "file_name": file_name,
                    "language": language,
                    "module": module,
                    "parameters": [],
                    "return_type": None,
                    "decorators": [],
                    "is_async": False,
                    "is_generator": False,
                    "is_lambda": False,
                    "visibility": "public",
                    "lines_of_code": 1,
                    "cyclomatic_complexity": 1,
                    "maintainability_score": 100.0,
                    "has_documentation": False,
                    "issue_count": 0,
                    "health_status": "Good",
                    "issues": [],
                    "ai_insight": "",
                })
                complexities.append(1)
                maintainabilities.append(100.0)

            tag_types = defaultdict(int)
            for tag in tags:
                tag_types[tag] += 1

            for tag, count in sorted(tag_types.items(), key=lambda x: -x[1])[:10]:
                if tag not in ("html", "head", "body", "div", "span", "p", "a", "ul", "ol", "li", "table", "tr", "td", "th", "form", "input", "button", "h1", "h2", "h3", "h4", "h5", "h6", "meta", "link", "script", "style"):
                    classes.append({
                        "name": f"<{tag}>",
                        "file_path": rel_path,
                        "file_name": file_name,
                        "language": language,
                        "module": module,
                        "base_classes": [],
                        "parent_class": None,
                        "child_classes": [],
                        "methods": [],
                        "properties": [],
                        "constructors": [],
                        "decorators": [],
                        "interfaces": [],
                        "is_abstract": False,
                        "lines_of_code": content.count(f"<{tag}"),
                        "complexity": 1,
                        "maintainability_score": 100.0,
                        "has_documentation": False,
                        "issue_count": 0,
                        "health_status": "Good",
                        "issues": [],
                        "ai_insight": "",
                        "_state": {"base_classes": []},
                    })

            class_count = len(classes)

        else:  # JSON
            class_count = 0

        return (
            functions,
            classes,
            relationships,
            {
                "func_count": len(functions),
                "class_count": class_count if language != "JSON" else 0,
                "method_count": method_count,
                "complexities": complexities,
                "maintainabilities": maintainabilities,
                "undocumented": undocumented,
                "health_counts": dict(health_counts),
                "unused_funcs": [],
                "recursive_funcs": [],
                "called_funcs": list(all_called),
            },
        )

    def _analyze_with_regex(self, lines: list[str], rel_path: str,
                             file_name: str, language: str) -> tuple:
        functions: list[dict] = []
        classes: list[dict] = []
        relationships: list[dict] = []
        all_defined: set[str] = set()
        all_called: set[str] = set()
        all_classes_defined: set[str] = set()
        complexities_list: list[int] = []
        maintainabilities_list: list[float] = []
        health_counts: dict[str, int] = defaultdict(int)
        unused_funcs: set[str] = set()
        recursive_funcs: set[str] = set()
        undocumented_count = 0
        method_count = 0
        inside_multiline = False

        module = rel_path.replace("/", ".").rsplit(".", 1)[0] if "." in rel_path else rel_path
        content = "\n".join(lines)

        for i, raw in enumerate(lines):
            stripped = raw.strip()
            if not stripped:
                continue

            if language in ("C", "C++", "Java", "JavaScript", "TypeScript"):
                if stripped.startswith("/*"):
                    inside_multiline = True
                    continue
                if inside_multiline:
                    if "*/" in stripped:
                        inside_multiline = False
                    continue
                if stripped.startswith("//"):
                    todo_match = re.search(r"(TODO|FIXME)\s*[:-]?\s*(.+)", stripped, re.IGNORECASE)
                    continue

            line_before_comment = stripped.split("//")[0].strip() if language != "Python" else stripped.split("#")[0].strip()

            if not line_before_comment:
                continue

            fm = CodeQualityEngine._match_function(line_before_comment, language)
            if fm:
                name = fm["name"]
                params_list = fm["params"]
                has_type_hints = fm["has_type_hints"]
                has_doc = False
                doc_line = i + 1
                while doc_line < min(i + 5, len(lines)):
                    dl = lines[doc_line].strip()
                    if dl.startswith("/**") or dl.startswith("/*") or dl.startswith("//"):
                        has_doc = True
                        break
                    if dl and not dl.startswith("//") and not dl.startswith("*"):
                        break
                    doc_line += 1

                # Check for async
                is_async = "async" in line_before_comment.lower()

                # Check visibility
                visibility = "public"
                if language in ("Java", "C++", "C#"):
                    if "private" in line_before_comment:
                        visibility = "private"
                    elif "protected" in line_before_comment:
                        visibility = "protected"

                decorators_list = []
                if i > 0:
                    prev = lines[i - 1].strip()
                    if language in ("JavaScript", "TypeScript") and prev.startswith("@"):
                        decorators_list.append(prev)

                complexity = CodeQualityEngine._compute_complexity(
                    lines[max(0, i - 1):min(len(lines), i + 30)], language
                ) if False else 1
                loc = 1

                issues = self._detect_function_issues(name, [{"name": p} for p in params_list], complexity, loc, has_doc)
                maint = self._compute_function_maintainability(complexity, loc, len(issues), has_doc)
                health = self._score_to_health(maint)

                functions.append({
                    "name": name,
                    "file_path": rel_path,
                    "file_name": file_name,
                    "language": language,
                    "module": module,
                    "parameters": [{"name": p, "type": None, "default_value": None, "is_optional": False} for p in params_list],
                    "return_type": None,
                    "decorators": decorators_list,
                    "is_async": is_async,
                    "is_generator": False,
                    "is_lambda": False,
                    "visibility": visibility,
                    "lines_of_code": loc,
                    "cyclomatic_complexity": complexity,
                    "maintainability_score": round(maint, 1),
                    "has_documentation": has_doc,
                    "issue_count": len(issues),
                    "health_status": health,
                    "issues": issues,
                    "ai_insight": "",
                })

                all_defined.add(name)
                complexities_list.append(complexity)
                maintainabilities_list.append(maint)
                health_counts[health] += 1
                if not has_doc:
                    undocumented_count += 1

                for token in re.findall(r'\b([a-zA-Z_]\w*)\s*\(', line_before_comment.split("function")[-1]):
                    if token not in ("if", "elif", "while", "for", "switch", "catch", "with"):
                        all_called.add(token)

            cm = CodeQualityEngine._match_class(line_before_comment, language)
            if cm:
                name = cm
                base_classes_list = []
                if language in ("Java", "C#"):
                    ext = re.search(r"extends\s+(\w+)", line_before_comment)
                    if ext:
                        base_classes_list.append(ext.group(1))
                    impl = re.search(r"implements\s+([\w,\s]+)", line_before_comment)
                    if impl:
                        base_classes_list.extend([x.strip() for x in impl.group(1).split(",")])
                elif language in ("JavaScript", "TypeScript"):
                    ext = re.search(r"extends\s+(\w+)", line_before_comment)
                    if ext:
                        base_classes_list.append(ext.group(1))
                    impl = re.search(r"implements\s+([\w,\s]+)", line_before_comment)
                    if impl:
                        base_classes_list.extend([x.strip() for x in impl.group(1).split(",")])

                has_doc = False
                if i > 0:
                    prev = lines[i - 1].strip()
                    if prev.startswith("/**") or prev.startswith("/*") or prev.startswith("//"):
                        has_doc = True

                decorators_list = []
                if i > 0:
                    prev = lines[i - 1].strip()
                    if prev.startswith("@"):
                        decorators_list.append(prev)

                visibility = "public"
                if language in ("Java", "C++", "C#"):
                    if "private" in line_before_comment:
                        visibility = "private"
                    elif "protected" in line_before_comment:
                        visibility = "protected"

                is_abstract = "abstract" in line_before_comment.lower()
                loc = 1

                # Find class body
                brace_count = 0
                for j in range(i, min(i + 200, len(lines))):
                    brace_count += lines[j].count("{") - lines[j].count("}")
                    if brace_count > 0:
                        loc = j - i + 1
                        break

                classes.append({
                    "name": name,
                    "file_path": rel_path,
                    "file_name": file_name,
                    "language": language,
                    "module": module,
                    "base_classes": base_classes_list,
                    "parent_class": base_classes_list[0] if base_classes_list else None,
                    "child_classes": [],
                    "methods": [],
                    "properties": [],
                    "constructors": [],
                    "decorators": decorators_list,
                    "interfaces": [],
                    "is_abstract": is_abstract,
                    "lines_of_code": loc,
                    "complexity": 1,
                    "maintainability_score": 100.0,
                    "has_documentation": has_doc,
                    "issue_count": 0,
                    "health_status": "Good",
                    "issues": [],
                    "ai_insight": "",
                    "_state": {"base_classes": base_classes_list},
                })

                all_classes_defined.add(name)
                complexities_list.append(1)
                maintainabilities_list.append(100.0)
                health_counts["Good"] += 1

                # Look for methods inside class
                method_nest = 0
                for j in range(i + 1, min(i + 200, len(lines))):
                    sub = lines[j]
                    brace_count_sub = sub.count("{") - sub.count("}")
                    method_nest += brace_count_sub
                    if method_nest < 0:
                        break
                    sub_stripped = sub.strip()
                    if sub_stripped.startswith("function ") or re.match(r"\w+\s*\(.*?\)\s*\{", sub_stripped):
                        m_name = sub_stripped.split("(")[0].strip()
                        if "function" in sub_stripped:
                            m_name = sub_stripped.split("function")[-1].strip().split("(")[0].strip()
                        if m_name:
                            method_count += 1

        for fn in all_defined:
            if fn not in all_called and not fn.startswith("_") and fn not in ("main", "setup", "teardown"):
                if fn.startswith("__") and fn.endswith("__"):
                    continue
                unused_funcs.add(fn)

        return (
            functions,
            classes,
            relationships,
            {
                "func_count": len(functions),
                "class_count": len(classes),
                "method_count": method_count,
                "complexities": complexities_list,
                "maintainabilities": maintainabilities_list,
                "undocumented": undocumented_count,
                "health_counts": dict(health_counts),
                "unused_funcs": list(unused_funcs),
                "recursive_funcs": list(recursive_funcs),
                "called_funcs": list(all_called),
            },
        )

    def _compute_cyclomatic_complexity_ast(self, node) -> int:
        c = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                c += 1
            elif isinstance(child, ast.Try):
                c += len(child.handlers)
            elif isinstance(child, (ast.ExceptHandler,)):
                c += 1
            elif isinstance(child, ast.BoolOp):
                if isinstance(child.op, ast.And) or isinstance(child.op, ast.Or):
                    c += len(child.values) - 1
            elif isinstance(child, ast.Assert):
                c += 1
            elif isinstance(child, ast.Match):
                c += len(child.cases)
        return c

    def _is_generator(self, node) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Yield) or isinstance(child, ast.YieldFrom):
                return True
        return False

    def _detect_function_issues(self, name: str, params: list[dict],
                                 complexity: int, loc: int, has_doc: bool) -> list[dict]:
        issues: list[dict] = []
        if loc > 60:
            issues.append({
                "type": "long_function",
                "severity": "medium",
                "description": f"Function '{name}' has {loc} lines",
                "reason": "Long functions are hard to understand and test.",
                "suggested_fix": "Extract logical blocks into well-named helper functions.",
                "line": None,
            })
        if not has_doc:
            issues.append({
                "type": "missing_documentation",
                "severity": "low",
                "description": f"Function '{name}' lacks documentation",
                "reason": "Undocumented functions reduce maintainability.",
                "suggested_fix": "Add a docstring or comment explaining the purpose.",
                "line": None,
            })
        if complexity > 10:
            issues.append({
                "type": "high_complexity",
                "severity": "medium",
                "description": f"Function '{name}' has cyclomatic complexity {complexity}",
                "reason": "High complexity makes code hard to test and maintain.",
                "suggested_fix": "Break the function into smaller, focused units.",
                "line": None,
            })
        if len(params) > 5:
            issues.append({
                "type": "excessive_parameters",
                "severity": "medium",
                "description": f"Function '{name}' has {len(params)} parameters",
                "reason": "Long parameter lists reduce readability.",
                "suggested_fix": "Consolidate parameters into a single configuration object.",
                "line": None,
            })
        return issues

    def _detect_class_issues(self, name: str, method_count: int,
                              property_count: int, loc: int, has_doc: bool) -> list[dict]:
        issues: list[dict] = []
        if method_count > 20:
            issues.append({
                "type": "large_class",
                "severity": "medium",
                "description": f"Class '{name}' has {method_count} methods",
                "reason": "Classes with excessive methods violate SRP.",
                "suggested_fix": "Split into smaller focused classes.",
                "line": None,
            })
        if not has_doc:
            issues.append({
                "type": "missing_documentation",
                "severity": "low",
                "description": f"Class '{name}' lacks documentation",
                "reason": "Undocumented classes reduce maintainability.",
                "suggested_fix": "Add a docstring explaining the class purpose.",
                "line": None,
            })
        if loc > 500:
            issues.append({
                "type": "large_class_size",
                "severity": "medium",
                "description": f"Class '{name}' has {loc} lines",
                "reason": "Large classes are hard to navigate and maintain.",
                "suggested_fix": "Extract cohesive subsets into separate classes.",
                "line": None,
            })
        if method_count == 0:
            issues.append({
                "type": "empty_class",
                "severity": "low",
                "description": f"Class '{name}' has no methods",
                "reason": "Classes without methods may be unnecessary.",
                "suggested_fix": "Remove or implement methods for this class.",
                "line": None,
            })
        return issues

    def _compute_function_maintainability(self, complexity: int, loc: int,
                                            issue_count: int, has_doc: bool) -> float:
        maint = 100.0
        if complexity > 5:
            maint -= min((complexity - 5) * 5, 25)
        if loc > 30:
            maint -= min((loc - 30) * 0.5, 15)
        if issue_count > 0:
            maint -= issue_count * 5
        if not has_doc and loc > 10:
            maint -= 10
        return max(0, min(100, maint))

    def _compute_class_maintainability(self, complexity: int, loc: int,
                                        issue_count: int, has_doc: bool) -> float:
        maint = 100.0
        if complexity > 10:
            maint -= min((complexity - 10) * 3, 20)
        if loc > 200:
            maint -= min((loc - 200) * 0.1, 15)
        if issue_count > 0:
            maint -= issue_count * 3
        if not has_doc:
            maint -= 10
        return max(0, min(100, maint))

    @staticmethod
    def _score_to_health(score: float) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 75:
            return "Good"
        if score >= 60:
            return "Fair"
        if score >= 40:
            return "Needs Improvement"
        return "Poor"

    def _generate_function_insight(self, name: str, params: list[dict],
                                    complexity: int, loc: int,
                                    has_doc: bool, health: str,
                                    issues: list[dict]) -> str:
        parts: list[str] = []
        if health in ("Excellent", "Good"):
            parts.append(f"Function '{name}' is well-structured")
        elif health == "Fair":
            parts.append(f"Function '{name}' could be improved")
        else:
            parts.append(f"Function '{name}' needs attention")

        if complexity <= 5:
            parts.append("with low complexity")
        elif complexity <= 10:
            parts.append("with moderate complexity")
        else:
            parts.append(f"with high complexity ({complexity})")

        if len(params) > 5:
            parts.append(f"and {len(params)} parameters - consider reducing")
        if loc > 60:
            parts.append(f"and {loc} lines - consider splitting")
        if not has_doc:
            parts.append("(missing documentation)")

        return ". ".join(parts) + "."

    def _generate_class_insight(self, name: str, method_count: int,
                                 property_count: int, complexity: int,
                                 loc: int, health: str,
                                 issues: list[dict]) -> str:
        parts: list[str] = []
        if health in ("Excellent", "Good"):
            parts.append(f"Class '{name}' follows good design")
        elif health == "Fair":
            parts.append(f"Class '{name}' has room for improvement")
        else:
            parts.append(f"Class '{name}' requires significant refactoring")

        if method_count <= 5:
            parts.append(f"with {method_count} methods (focused)")
        elif method_count <= 15:
            parts.append(f"with {method_count} methods (moderate)")
        else:
            parts.append(f"with {method_count} methods (consider splitting)")

        if loc > 300:
            parts.append(f"spanning {loc} lines")
        if not issues and health in ("Excellent", "Good"):
            parts.append("and no significant issues")
        elif issues:
            issue_types = [i["type"] for i in issues]
            parts.append(f"issues: {', '.join(issue_types)}")

        return ". ".join(parts) + "."

    def _generate_ai_insights(self, functions: list[dict],
                               classes: list[dict]) -> list[str]:
        insights: list[str] = []
        large_funcs = [f for f in functions if f.get("lines_of_code", 0) > 80]
        for func in large_funcs[:3]:
            insights.append(
                f"'{func['name']}' in {func['file_path']} is very large "
                f"({func['lines_of_code']} lines). Consider extracting helper functions."
            )

        large_classes = [c for c in classes if len(c.get("methods", [])) > 15]
        for cls in large_classes[:3]:
            insights.append(
                f"'{cls['name']}' in {cls['file_path']} has {len(cls['methods'])} methods. "
                f"Consider splitting into smaller focused classes."
            )

        complex_funcs = [f for f in functions if f.get("cyclomatic_complexity", 0) > 15]
        for func in complex_funcs[:3]:
            insights.append(
                f"'{func['name']}' in {func['file_path']} has high cyclomatic complexity "
                f"({func['cyclomatic_complexity']}). Simplify with guard clauses or extracted methods."
            )

        undocumented_funcs = [f for f in functions if not f.get("has_documentation") and f.get("lines_of_code", 0) > 20]
        for func in undocumented_funcs[:2]:
            insights.append(
                f"'{func['name']}' in {func['file_path']} lacks documentation despite being "
                f"{func['lines_of_code']} lines long. Add a docstring."
            )

        unused_funcs_found = [f for f in functions if f.get("_is_unused")]
        if len(unused_funcs_found) > 0:
            names = [f["name"] for f in unused_funcs_found[:3]]
            insights.append(
                f"Unused functions detected: {', '.join(names)}. "
                f"Review and remove dead code to reduce maintenance burden."
            )

        high_maint = [c for c in classes if c.get("maintainability_score", 100) < 50]
        for cls in high_maint[:2]:
            insights.append(
                f"'{cls['name']}' has low maintainability score "
                f"({cls['maintainability_score']:.0f}/100). "
                f"Refactor to improve code quality."
            )

        if not insights:
            insights.append("No significant issues detected. Codebase follows good practices.")

        return insights

    def _build_class_relationships(self, all_classes: list[dict],
                                    inheritance_map: dict[str, list[str]]) -> list[dict]:
        relationships: list[dict] = []
        for cls in all_classes:
            name = cls["name"]
            file_path = cls["file_path"]
            inheritance = cls.get("base_classes", [])
            children = inheritance_map.get(name, [])

            if inheritance or children:
                relationships.append({
                    "name": name,
                    "file_path": file_path,
                    "inheritance": inheritance + children,
                    "composition": [],
                    "aggregation": [],
                    "dependency": [],
                    "association": [],
                })
        return relationships
