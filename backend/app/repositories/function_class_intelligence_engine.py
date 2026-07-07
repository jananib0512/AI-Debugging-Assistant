import ast
import hashlib
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


def _compute_cyclomatic_complexity_ast(node) -> int:
    c = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            c += 1
        elif isinstance(child, ast.Try):
            c += len(child.handlers)
        elif isinstance(child, ast.ExceptHandler):
            c += 1
        elif isinstance(child, ast.BoolOp):
            if isinstance(child.op, (ast.And, ast.Or)):
                c += len(child.values) - 1
        elif isinstance(child, ast.Assert):
            c += 1
        elif isinstance(child, ast.Match):
            c += len(child.cases)
    return c


def _compute_deepest_nesting(node) -> int:
    max_depth = 0
    current_depth = 0

    class NestingVisitor(ast.NodeVisitor):
        nonlocal max_depth, current_depth

        def visit_If(self, n):
            nonlocal max_depth, current_depth
            current_depth += 1
            max_depth = max(max_depth, current_depth)
            self.generic_visit(n)
            current_depth -= 1

        def visit_While(self, n):
            nonlocal max_depth, current_depth
            current_depth += 1
            max_depth = max(max_depth, current_depth)
            self.generic_visit(n)
            current_depth -= 1

        def visit_For(self, n):
            nonlocal max_depth, current_depth
            current_depth += 1
            max_depth = max(max_depth, current_depth)
            self.generic_visit(n)
            current_depth -= 1

        def visit_Try(self, n):
            nonlocal max_depth, current_depth
            current_depth += 1
            max_depth = max(max_depth, current_depth)
            self.generic_visit(n)
            current_depth -= 1

        def visit_With(self, n):
            nonlocal max_depth, current_depth
            current_depth += 1
            max_depth = max(max_depth, current_depth)
            self.generic_visit(n)
            current_depth -= 1

    NestingVisitor().visit(node)
    return max_depth


def _has_type_hints(node) -> bool:
    for arg in node.args.args:
        if arg.annotation:
            return True
    if node.returns:
        return True
    return False


def _get_function_body_hash(node) -> str:
    try:
        body_source = ast.unparse(node.body)
        return hashlib.md5(body_source.encode()).hexdigest()[:12]
    except Exception:
        return ""


def _compute_maintainability(complexity: int, loc: int, issue_count: int, has_doc: bool) -> float:
    maint = 100.0
    if complexity > 5:
        maint -= min((complexity - 5) * 5, 25)
    if loc > 30:
        maint -= min((loc - 30) * 0.5, 15)
    if issue_count > 0:
        maint -= issue_count * 5
    if not has_doc and loc > 10:
        maint -= 10
    return max(0.0, min(100.0, maint))


def _compute_class_maintainability(complexity: int, loc: int, issue_count: int, has_doc: bool) -> float:
    maint = 100.0
    if complexity > 10:
        maint -= min((complexity - 10) * 3, 20)
    if loc > 200:
        maint -= min((loc - 200) * 0.1, 15)
    if issue_count > 0:
        maint -= issue_count * 3
    if not has_doc:
        maint -= 10
    return max(0.0, min(100.0, maint))


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


class FunctionClassIntelligenceEngine:

    def analyze(self, workspace_path: Path) -> dict:
        all_functions: list[dict] = []
        all_classes: list[dict] = []
        all_relationships: list[dict] = []
        class_inheritance_map: dict[str, list[str]] = defaultdict(list)
        class_file_map: dict[str, str] = {}
        function_file_map: dict[str, list[str]] = defaultdict(list)
        all_called_funcs: dict[str, set[str]] = defaultdict(set)
        all_definitions: dict[str, str] = {}
        function_body_hashes: dict[str, list[str]] = defaultdict(list)

        total_funcs = 0
        total_classes_count = 0
        total_methods = 0
        health_counts: dict[str, int] = defaultdict(int)
        lang_func_count: dict[str, int] = defaultdict(int)
        lang_class_count: dict[str, int] = defaultdict(int)
        complexities: list[int] = []
        maintainabilities: list[float] = []
        undocumented = 0
        unused_set: set[str] = set()
        recursive_set: set[str] = set()
        deep_nesting_funcs: list[str] = []
        missing_type_hints_list: list[str] = []

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
                    funcs, classes, relationships, stats = self._analyze_python(content, lines, rel_path, f, language, function_body_hashes)
                elif language in ("JavaScript", "TypeScript"):
                    funcs, classes, relationships, stats = self._analyze_non_python(lines, rel_path, f, language, "jslike")
                elif language in ("Java",):
                    funcs, classes, relationships, stats = self._analyze_non_python(lines, rel_path, f, language, "java")
                else:
                    funcs, classes, relationships, stats = self._analyze_non_python(lines, rel_path, f, language, "other")

                total_funcs += stats["func_count"]
                total_classes_count += stats["class_count"]
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
                deep_nesting_funcs.extend(stats.get("deep_nesting_funcs", []))
                missing_type_hints_list.extend(stats.get("missing_type_hints", []))

                for func in funcs:
                    function_file_map[func["name"]].append(rel_path)
                    all_definitions[func["name"]] = rel_path
                for cls in classes:
                    class_file_map[cls["name"]] = rel_path
                    for parent in cls.get("base_classes", []):
                        class_inheritance_map[parent].append(cls["name"])

                for called in stats.get("called_funcs", []):
                    all_called_funcs[called].add(rel_path)

                all_functions.extend(funcs)
                all_classes.extend(classes)
                all_relationships.extend(relationships)

        # Enhance functions with relationship data
        for func in all_functions:
            fn = func["name"]
            callers_list: list[str] = []
            for caller_name, called_set in all_called_funcs.items():
                if fn in called_set:
                    caller_files = function_file_map.get(caller_name, [])
                    if caller_files:
                        callers_list.append(f"{caller_name} ({', '.join(caller_files)})")
                    else:
                        callers_list.append(caller_name)
            func["_callers"] = callers_list
            func["_is_unused"] = fn in unused_set or (len(callers_list) == 0 and not fn.startswith("_"))
            func["_is_recursive"] = fn in recursive_set
            func["_cross_file_calls"] = list(all_called_funcs.get(fn, set()))

        # Build class relationships
        for cls in all_classes:
            name = cls["name"]
            file_path = cls["file_path"]
            inheritance = cls.get("base_classes", [])
            children = class_inheritance_map.get(name, [])

            # Inheritance relationships
            for parent in inheritance:
                all_relationships.append({
                    "type": "inheritance",
                    "source": name,
                    "target": parent,
                    "source_file": file_path,
                    "target_file": class_file_map.get(parent, ""),
                    "strength": "strong",
                })
            for child in children:
                all_relationships.append({
                    "type": "inheritance",
                    "source": child,
                    "target": name,
                    "source_file": class_file_map.get(child, ""),
                    "target_file": file_path,
                    "strength": "strong",
                })

            # Composition / Aggregation / Association from property types
            for prop in cls.get("properties", []):
                # If property type matches a known class, create relationship
                for other_cls in all_classes:
                    if other_cls["name"] != name and other_cls["name"].lower() in prop.lower():
                        all_relationships.append({
                            "type": "association",
                            "source": name,
                            "target": other_cls["name"],
                            "source_file": file_path,
                            "target_file": other_cls["file_path"],
                            "strength": "medium",
                        })

            # Dependency from method parameters/imports
            for method in cls.get("methods", []):
                return_type = method.get("return_type", "")
                if return_type:
                    for other_cls in all_classes:
                        if other_cls["name"] != name and other_cls["name"] in return_type:
                            all_relationships.append({
                                "type": "dependency",
                                "source": name,
                                "target": other_cls["name"],
                                "source_file": file_path,
                                "target_file": other_cls["file_path"],
                                "strength": "weak",
                            })

        # Generate AI insights
        ai_insights = self._generate_ai_insights(all_functions, all_classes)

        avg_complexity = (sum(complexities) / len(complexities)) if complexities else 0.0
        avg_maint = (sum(maintainabilities) / len(maintainabilities)) if maintainabilities else 100.0
        total_issues = sum(len(f.get("issues", [])) for f in all_functions) + sum(len(c.get("issues", [])) for c in all_classes)

        return {
            "functions": all_functions,
            "classes": all_classes,
            "relationships": all_relationships,
            "stats": {
                "total_functions": total_funcs,
                "total_classes": total_classes_count,
                "total_methods": total_methods,
                "average_complexity": round(avg_complexity, 1),
                "average_maintainability": round(avg_maint, 1),
                "total_issues": total_issues,
                "language_breakdown": {**lang_func_count, **{f"_{k}": v for k, v in lang_class_count.items()}},
                "health_counts": dict(health_counts),
                "unused_functions": len(unused_set),
                "recursive_functions": len(recursive_set),
                "undocumented_count": undocumented,
                "deep_nesting_count": len(deep_nesting_funcs),
                "missing_type_hints_count": len(missing_type_hints_list),
            },
            "ai_insights": ai_insights,
        }

    def _analyze_python(self, content: str, lines: list[str], rel_path: str, file_name: str, language: str,
                        function_body_hashes: dict[str, list[str]]) -> tuple:
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
        deep_nesting_funcs: list[str] = []
        missing_type_hints: list[str] = []

        module = rel_path.replace("/", ".").rsplit(".", 1)[0] if "." in rel_path else rel_path

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._analyze_fallback(lines, rel_path, file_name, language)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_async = isinstance(node, ast.AsyncFunctionDef)
                func_info = self._extract_python_function(node, rel_path, file_name, language, module, lines, is_async)
                functions.append(func_info)
                all_defined.add(node.name)
                complexities_list.append(func_info["cyclomatic_complexity"])
                maintainabilities_list.append(func_info["maintainability_score"])
                health_counts[func_info["health_status"]] += 1
                if not func_info["has_documentation"]:
                    undocumented_count += 1
                if func_info.get("deepest_nesting", 0) > 4:
                    deep_nesting_funcs.append(node.name)
                if not func_info.get("has_type_hints", False):
                    missing_type_hints.append(node.name)

                # Track body hash for duplicate detection
                body_hash = _get_function_body_hash(node)
                if body_hash:
                    function_body_hashes[body_hash].append(f"{rel_path}:{node.name}")

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            all_called.add(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            all_called.add(child.func.attr)

                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == node.name:
                        recursive_funcs.add(node.name)

            elif isinstance(node, ast.ClassDef):
                cls_info = self._extract_python_class(node, rel_path, file_name, language, module, lines, all_classes_defined)
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
                        all_defined.add(item.name)
                        complexities_list.append(_compute_cyclomatic_complexity_ast(item))
                        for child in ast.walk(item):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Name):
                                    all_called.add(child.func.id)
                                elif isinstance(child.func, ast.Attribute):
                                    all_called.add(child.func.attr)

        # Detect unused functions
        for fn_name in all_defined:
            if fn_name not in all_called and not fn_name.startswith("__"):
                unused_funcs.add(fn_name)

        # Detect duplicate functions
        for bh, locs in function_body_hashes.items():
            if len(locs) > 1:
                for loc in locs:
                    for func in functions:
                        if f"{rel_path}:{func['name']}" == loc:
                            func.setdefault("issues", []).append({
                                "type": "duplicate_function",
                                "severity": "medium",
                                "description": f"Function '{func['name']}' has duplicate body with {', '.join(l for l in locs if l != loc)}",
                                "reason": "Duplicate code increases maintenance burden.",
                                "suggested_fix": "Extract the common logic into a shared helper function.",
                                "line": func.get("start_line", 0),
                            })

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
                "deep_nesting_funcs": deep_nesting_funcs,
                "missing_type_hints": missing_type_hints,
            },
        )

    def _extract_python_function(self, node, rel_path: str, file_name: str, language: str, module: str,
                                  lines: list[str], is_async: bool) -> dict:
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
            if 0 <= idx < len(params):
                params[idx]["default_value"] = ast.unparse(default)
                params[idx]["is_optional"] = True

        return_type = ast.unparse(node.returns) if node.returns else None
        decorators = [ast.unparse(d) for d in node.decorator_list]
        is_generator = self._is_generator_ast(node)
        is_lambda = False

        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start_line + 1
        loc = max(0, end_line - start_line)

        complexity = _compute_cyclomatic_complexity_ast(node)
        deepest_nesting = _compute_deepest_nesting(node)
        has_type_hints_flag = _has_type_hints(node)
        has_doc = ast.get_docstring(node) is not None

        issues = self._detect_function_issues(name, params, complexity, loc, has_doc, deepest_nesting, has_type_hints_flag)
        maint = _compute_maintainability(complexity, loc, len(issues), has_doc)
        health = _score_to_health(maint)

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
            "start_line": start_line,
            "end_line": end_line,
            "cyclomatic_complexity": complexity,
            "maintainability_score": round(maint, 1),
            "has_documentation": has_doc,
            "has_type_hints": has_type_hints_flag,
            "deepest_nesting": deepest_nesting,
            "issue_count": len(issues),
            "health_status": health,
            "issues": issues,
            "callers": [],
            "called_functions": [],
            "is_recursive": False,
            "is_unused": False,
            "cross_file_calls": [],
            "ai_insight": self._generate_function_insight(name, params, complexity, loc, has_doc, health, issues, deepest_nesting),
        }

    def _extract_python_class(self, node, rel_path: str, file_name: str, language: str, module: str,
                               lines: list[str], all_classes_defined: set[str]) -> dict:
        name = node.name
        base_classes = [ast.unparse(b) for b in node.bases]
        decorators = [ast.unparse(d) for d in node.decorator_list]
        is_abstract = any("abstract" in d.lower() or "ABC" in d for d in decorators + base_classes)

        methods: list[dict] = []
        properties: list[str] = []
        class_variables: list[str] = []
        constructors: list[dict] = []
        interfaces: list[str] = []
        total_loc = 0
        total_complexity = 0
        has_nested = False

        for item in node.body:
            if isinstance(item, ast.ClassDef):
                has_nested = True
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
                        if not target.id.startswith("_"):
                            class_variables.append(target.id)
                    elif isinstance(target, ast.Attribute):
                        if not target.attr.startswith("_"):
                            class_variables.append(target.attr)

        for base in base_classes:
            if "Interface" in base or "Protocol" in base:
                interfaces.append(base)

        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start_line + 1
        loc = max(0, end_line - start_line + 1)

        complexity = max(total_complexity, 1)
        has_doc = ast.get_docstring(node) is not None
        issues = self._detect_class_issues(name, len(methods), len(properties), loc, has_doc, complexity)
        maint = _compute_class_maintainability(complexity, loc, len(issues), has_doc)
        health = _score_to_health(maint)

        # Compute coupling: number of unique types referenced
        coupling_set: set[str] = set()
        for base in base_classes:
            coupling_set.add(base)
        for method in methods:
            rt = method.get("return_type", "")
            if rt and rt not in ("None", "str", "int", "float", "bool", "list", "dict", "tuple", "set"):
                coupling_set.add(rt)
            for p in method.get("parameters", []):
                pt = p.get("type", "")
                if pt and pt not in ("None", "str", "int", "float", "bool", "list", "dict", "tuple", "set"):
                    coupling_set.add(pt)

        return {
            "name": name,
            "file_path": rel_path,
            "file_name": file_name,
            "language": language,
            "module": module,
            "base_classes": base_classes,
            "parent_class": base_classes[0] if base_classes else None,
            "child_classes": [],
            "methods": methods,
            "properties": properties,
            "class_variables": class_variables,
            "constructors": constructors,
            "decorators": decorators,
            "interfaces": interfaces,
            "is_abstract": is_abstract,
            "has_nested_classes": has_nested,
            "lines_of_code": loc,
            "complexity": complexity,
            "maintainability_score": round(maint, 1),
            "has_documentation": has_doc,
            "issue_count": len(issues),
            "health_status": health,
            "issues": issues,
            "coupling": len(coupling_set),
            "method_count": len(methods),
            "property_count": len(properties),
            "ai_insight": self._generate_class_insight(name, len(methods), len(properties), complexity, loc, health, issues, len(coupling_set)),
        }

    def _extract_python_method(self, item, rel_path: str, file_name: str, language: str, module: str,
                                parent_class: str, lines: list[str], is_async: bool) -> dict:
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
            if 0 <= idx < len(params):
                params[idx]["default_value"] = ast.unparse(default)
                params[idx]["is_optional"] = True

        return_type = ast.unparse(item.returns) if item.returns else None
        decorators = [ast.unparse(d) for d in item.decorator_list]
        is_static = any("staticmethod" in d for d in decorators)
        is_classmethod = any("classmethod" in d for d in decorators)
        is_property = any("property" in d for d in decorators)

        start_line = item.lineno
        end_line = item.end_lineno if hasattr(item, "end_lineno") and item.end_lineno else start_line + 1
        loc = max(0, end_line - start_line)

        complexity = _compute_cyclomatic_complexity_ast(item)
        has_type_hints_flag = _has_type_hints(item)
        deepest_nesting = _compute_deepest_nesting(item)
        has_doc = ast.get_docstring(item) is not None
        issues = self._detect_function_issues(name, params, complexity, loc, has_doc, deepest_nesting, has_type_hints_flag)
        maint = _compute_maintainability(complexity, loc, len(issues), has_doc)
        health = _score_to_health(maint)

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
            "visibility": "private" if name.startswith("__") else "protected" if name.startswith("_") else "public",
            "lines_of_code": loc,
            "start_line": start_line,
            "end_line": end_line,
            "cyclomatic_complexity": complexity,
            "maintainability_score": round(maint, 1),
            "has_documentation": has_doc,
            "has_type_hints": has_type_hints_flag,
            "issue_count": len(issues),
            "health_status": health,
            "issues": issues,
            "ai_insight": "",
        }

    def _analyze_non_python(self, lines: list[str], rel_path: str, file_name: str, language: str, flavor: str) -> tuple:
        functions: list[dict] = []
        classes: list[dict] = []
        relationships: list[dict] = []
        all_defined: set[str] = set()
        all_called: set[str] = set()
        complexities_list: list[int] = []
        maintainabilities_list: list[float] = []
        health_counts: dict[str, int] = defaultdict(int)
        unused_funcs: set[str] = set()
        recursive_funcs: set[str] = set()
        undocumented_count = 0
        method_count = 0
        deep_nesting_funcs: list[str] = []
        missing_type_hints: list[str] = []

        module = rel_path.replace("/", ".").rsplit(".", 1)[0] if "." in rel_path else rel_path
        content = "\n".join(lines)
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
            fn_patterns = [
                r"(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
                r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
                r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>",
            ]
            fn_match = None
            for pat in fn_patterns:
                fn_match = re.search(pat, line_before_comment)
                if fn_match:
                    break

            if fn_match and "function" in line_before_comment:
                name = fn_match.group(1) if fn_match.lastindex >= 1 else ""
                params_raw = fn_match.group(2) if fn_match.lastindex >= 2 else ""
                if name:
                    params_list = [p.strip() for p in params_raw.split(",") if p.strip()]
                    is_async = "async" in line_before_comment.lower()
                    has_doc = False
                    if i > 0:
                        prev = lines[i - 1].strip()
                        if prev.startswith("/**") or prev.startswith("/*") or prev.startswith("//"):
                            has_doc = True

                    complexity = 1
                    loc = 1
                    has_type_hints_flag = any(":" in p for p in params_list)
                    deepest_nesting_val = 0
                    issues = self._detect_function_issues(name, [{"name": p} for p in params_list], complexity, loc, has_doc, deepest_nesting_val, has_type_hints_flag)
                    maint = _compute_maintainability(complexity, loc, len(issues), has_doc)
                    health = _score_to_health(maint)

                    functions.append({
                        "name": name,
                        "file_path": rel_path,
                        "file_name": file_name,
                        "language": language,
                        "module": module,
                        "parameters": [{"name": p, "type": None, "default_value": None, "is_optional": False} for p in params_list],
                        "return_type": None,
                        "decorators": [],
                        "is_async": is_async,
                        "is_generator": False,
                        "is_lambda": False,
                        "visibility": "public",
                        "lines_of_code": loc,
                        "start_line": i + 1,
                        "end_line": i + 2,
                        "cyclomatic_complexity": complexity,
                        "maintainability_score": round(maint, 1),
                        "has_documentation": has_doc,
                        "has_type_hints": has_type_hints_flag,
                        "deepest_nesting": deepest_nesting_val,
                        "issue_count": len(issues),
                        "health_status": health,
                        "issues": issues,
                        "callers": [],
                        "called_functions": [],
                        "is_recursive": False,
                        "is_unused": False,
                        "cross_file_calls": [],
                        "ai_insight": self._generate_function_insight(name, [{"name": p} for p in params_list], complexity, loc, has_doc, health, issues, deepest_nesting_val),
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

            # Class detection
            class_patterns = [
                r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)",
                r"class\s+(\w+)",
            ]
            cm = None
            for pat in class_patterns:
                cm = re.search(pat, line_before_comment)
                if cm:
                    break

            if cm and not fn_match:
                name = cm.group(1)
                base_classes_list: list[str] = []
                if flavor in ("jslike", "java"):
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

                is_abstract = "abstract" in line_before_comment.lower()
                loc = 1
                brace_count = 0
                for j in range(i, min(i + 200, len(lines))):
                    brace_count += lines[j].count("{") - lines[j].count("}")
                    if brace_count > 0:
                        loc = j - i + 1
                        break

                issues = self._detect_class_issues(name, 0, 0, loc, has_doc, 1)
                maint = _compute_class_maintainability(1, loc, len(issues), has_doc)
                health = _score_to_health(maint)

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
                    "class_variables": [],
                    "constructors": [],
                    "decorators": [],
                    "interfaces": [],
                    "is_abstract": is_abstract,
                    "has_nested_classes": False,
                    "lines_of_code": loc,
                    "complexity": 1,
                    "maintainability_score": 100.0,
                    "has_documentation": has_doc,
                    "issue_count": len(issues),
                    "health_status": "Good",
                    "issues": issues,
                    "coupling": len(base_classes_list),
                    "method_count": 0,
                    "property_count": 0,
                    "ai_insight": self._generate_class_insight(name, 0, 0, 1, loc, health, issues, len(base_classes_list)),
                })

                complexities_list.append(1)
                maintainabilities_list.append(100.0)
                health_counts["Good"] += 1

        for fn_name in all_defined:
            if fn_name not in all_called and not fn_name.startswith("_"):
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
                "deep_nesting_funcs": deep_nesting_funcs,
                "missing_type_hints": missing_type_hints,
            },
        )

    def _analyze_fallback(self, lines: list[str], rel_path: str, file_name: str, language: str) -> tuple:
        return self._analyze_non_python(lines, rel_path, file_name, language, "other")

    @staticmethod
    def _is_generator_ast(node) -> bool:
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _detect_function_issues(self, name: str, params: list[dict], complexity: int, loc: int,
                                 has_doc: bool, deepest_nesting: int, has_type_hints: bool) -> list[dict]:
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
        if deepest_nesting > 4:
            issues.append({
                "type": "deep_nesting",
                "severity": "medium",
                "description": f"Function '{name}' has {deepest_nesting} levels of nesting",
                "reason": "Deeply nested code is hard to follow and test.",
                "suggested_fix": "Use guard clauses, early returns, or extract nested blocks into separate functions.",
                "line": None,
            })
        if not has_type_hints and loc > 10:
            issues.append({
                "type": "missing_type_hints",
                "severity": "low",
                "description": f"Function '{name}' lacks type hints",
                "reason": "Type hints improve code clarity and catch errors early.",
                "suggested_fix": "Add type annotations to parameters and return values.",
                "line": None,
            })
        return issues

    def _detect_class_issues(self, name: str, method_count: int, property_count: int,
                              loc: int, has_doc: bool, complexity: int) -> list[dict]:
        issues: list[dict] = []
        if method_count > 15:
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
        if method_count > 10 and property_count > 10 and complexity > 20:
            issues.append({
                "type": "god_class",
                "severity": "high",
                "description": f"Class '{name}' has many methods ({method_count}), properties ({property_count}), and high complexity ({complexity})",
                "reason": "Classes with too many responsibilities violate SRP.",
                "suggested_fix": "Split into multiple focused classes based on responsibility boundaries.",
                "line": None,
            })
        if method_count > 8 and property_count < 3:
            issues.append({
                "type": "low_cohesion",
                "severity": "medium",
                "description": f"Class '{name}' has {method_count} methods but only {property_count} properties",
                "reason": "Low cohesion indicates methods may not share common state.",
                "suggested_fix": "Group related methods into separate classes.",
                "line": None,
            })
        return issues

    def _generate_function_insight(self, name: str, params: list[dict], complexity: int, loc: int,
                                    has_doc: bool, health: str, issues: list[dict], deepest_nesting: int) -> str:
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
        if deepest_nesting > 4:
            parts.append(f"and {deepest_nesting} nesting levels - simplify logic")
        if not has_doc and loc > 10:
            parts.append("(missing documentation)")

        high_sev = [i for i in issues if i.get("severity") == "high"]
        med_sev = [i for i in issues if i.get("severity") == "medium"]
        if high_sev:
            types_str = ", ".join(i["type"] for i in high_sev[:3])
            parts.append(f"high-severity issues: {types_str}")
        elif med_sev:
            types_str = ", ".join(i["type"] for i in med_sev[:3])
            parts.append(f"medium-severity issues: {types_str}")

        return ". ".join(parts) + "."

    def _generate_class_insight(self, name: str, method_count: int, property_count: int,
                                 complexity: int, loc: int, health: str,
                                 issues: list[dict], coupling: int) -> str:
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
        if coupling > 5:
            parts.append(f"with {coupling} type dependencies")

        high_sev = [i for i in issues if i.get("severity") == "high"]
        if high_sev:
            parts.append(f"high-severity issues: {', '.join(i['type'] for i in high_sev)}")
        elif issues:
            parts.append(f"issues: {', '.join(i['type'] for i in issues[:4])}")

        if not issues and health in ("Excellent", "Good"):
            parts.append("and no significant issues")

        return ". ".join(parts) + "."

    def _generate_ai_insights(self, functions: list[dict], classes: list[dict]) -> list[str]:
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

        unused = [f for f in functions if f.get("_is_unused")]
        if len(unused) > 0:
            names = [f["name"] for f in unused[:3]]
            insights.append(
                f"Unused functions detected: {', '.join(names)}. "
                f"Review and remove dead code to reduce maintenance burden."
            )

        deep_nest = [f for f in functions if f.get("deepest_nesting", 0) > 4]
        for func in deep_nest[:2]:
            insights.append(
                f"'{func['name']}' has {func['deepest_nesting']} levels of nesting. "
                f"Deep nesting reduces readability - use guard clauses to flatten."
            )

        no_hints = [f for f in functions if not f.get("has_type_hints") and f.get("lines_of_code", 0) > 10]
        for func in no_hints[:2]:
            insights.append(
                f"'{func['name']}' in {func['file_path']} lacks type hints. "
                f"Adding type annotations improves code documentation and catches errors."
            )

        god_classes = [
            c for c in classes
            if c.get("method_count", 0) > 10 and c.get("property_count", 0) > 10 and c.get("complexity", 0) > 20
        ]
        for cls in god_classes[:2]:
            insights.append(
                f"'{cls['name']}' appears to be a god class with {cls['method_count']} methods, "
                f"{cls['property_count']} properties, and complexity {cls['complexity']}. "
                f"Split by responsibility."
            )

        low_cohesion = [
            c for c in classes
            if c.get("method_count", 0) > 8 and c.get("property_count", 0) < 3 and c.get("method_count", 0) > 0
        ]
        for cls in low_cohesion[:2]:
            insights.append(
                f"'{cls['name']}' has low cohesion: {cls['method_count']} methods but only "
                f"{cls['property_count']} properties. Methods may not share common state."
            )

        high_coupling = [c for c in classes if c.get("coupling", 0) > 8]
        for cls in high_coupling[:2]:
            insights.append(
                f"'{cls['name']}' has high coupling ({cls['coupling']} type dependencies). "
                f"Reduce coupling by depending on abstractions, not concrete types."
            )

        duplicates = defaultdict(list)
        for func in functions:
            bh = func.get("_body_hash", "")
            if bh:
                duplicates[bh].append(func["name"])
        for bh, names in duplicates.items():
            if len(names) > 1:
                insights.append(
                    f"Duplicate code detected: {', '.join(names[:4])} share the same function body. "
                    f"Extract the common logic into a shared utility."
                )

        if not insights:
            insights.append("No significant issues detected. Codebase follows good practices.")

        return insights[:12]
