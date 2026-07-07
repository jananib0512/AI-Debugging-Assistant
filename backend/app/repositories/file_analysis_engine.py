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


class FileAnalysisEngine:
    def analyze(self, workspace_path: Path) -> dict:
        files: list[dict] = []
        lang_counts: dict[str, int] = defaultdict(int)

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

                lang_counts[language] += 1

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
                n_lines = len(lines)
                size = os.path.getsize(file_path)
                comment_lines, blank_lines = CodeQualityEngine._count_comments_blanks(lines, language)
                code_lines = max(0, n_lines - comment_lines - blank_lines)
                complexity = CodeQualityEngine._compute_complexity(lines, language)

                info = self._analyze_file(lines, content, rel_path, language, workspace_path)

                # Per-file scores
                scores = self._compute_file_scores(
                    complexity, comment_lines, n_lines,
                    info, language,
                )
                health = self._score_to_health(scores["overall"])
                tags = self._auto_tag(rel_path, language, info)
                ai_summary = self._generate_file_summary(rel_path, scores, health, info, tags)

                files.append({
                    "path": rel_path,
                    "file_name": f,
                    "extension": ext,
                    "language": language,
                    "size": size,
                    "total_lines": n_lines,
                    "code_lines": code_lines,
                    "blank_lines": blank_lines,
                    "comment_lines": comment_lines,
                    "functions": info["func_count"],
                    "classes": info["class_count"],
                    "imports": info["import_count"],
                    "complexity": complexity,
                    "scores": scores,
                    "health": health,
                    "tags": tags,
                    "ai_summary": ai_summary,
                    "issues": info["issues"],
                })

        return {
            "files": files,
            "total_files": len(files),
            "language_counts": dict(lang_counts),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _analyze_file(self, lines: list[str], content: str, rel_path: str,
                       language: str, workspace_path: Path) -> dict:
        issues: list[dict] = []
        n = len(lines)

        funcs: list[dict] = []
        classes: list[tuple[str, int, int]] = []
        defined_funcs: set[str] = set()
        called_funcs: set[str] = set()
        imports: list[str] = []
        todo_lines: list[tuple[int, str]] = []
        nesting_depths: list[int] = []

        in_func = False
        func_name = ""
        func_start = 0
        func_loc = 0
        func_params: list[str] = []
        func_return_count = 0
        func_has_doc = False
        func_has_type_hints = False

        class_name = ""
        class_start = 0
        class_methods = 0
        current_nesting = 0
        inside_multiline_comment = False
        inside_multiline_string = False
        seen_excepts: set[str] = set()
        defs_found_in_func: defaultdict[str, list[str]] = defaultdict(list)

        for i, raw in enumerate(lines):
            stripped = raw.strip()
            line_before_comment = (stripped.split("#")[0].split("//")[0].strip()
                                   if language != "Python" else stripped.split("#")[0].strip())

            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                if "todo" in stripped.lower() or "fixme" in stripped.lower():
                    todo_lines.append((i, stripped))
                continue

            if language in ("Python",) and (stripped.startswith('"""') or stripped.startswith("'''")):
                inside_multiline_string = not inside_multiline_string
                continue
            if inside_multiline_string:
                continue
            if language in ("C", "C++", "Java", "C#", "JavaScript", "TypeScript", "CSS"):
                if stripped.startswith("/*"):
                    inside_multiline_comment = True
                    if "*/" in stripped:
                        inside_multiline_comment = False
                    continue
                if inside_multiline_comment:
                    if "*/" in stripped:
                        inside_multiline_comment = False
                    continue

            delta = (stripped.count("{") + stripped.count("(") + stripped.count("[")
                     - stripped.count("}") - stripped.count(")") - stripped.count("]"))
            if language == "Python":
                if re.match(r"^\s*(if|elif|else|for|while|with|try|except)\b", stripped):
                    current_nesting += 1
            else:
                current_nesting = max(0, current_nesting + delta)
            if current_nesting > 0:
                nesting_depths.append(current_nesting)
            if language != "Python":
                current_nesting = max(0, current_nesting + delta)

            fm = CodeQualityEngine._match_function(stripped, language)
            if fm:
                if in_func:
                    self._finalize_function(issues, func_name, func_start, func_loc,
                                            func_params, func_return_count,
                                            func_has_doc, func_has_type_hints,
                                            rel_path, language, i)
                func_name = fm["name"]
                func_start = i
                func_loc = 0
                func_params = fm["params"]
                func_return_count = 0
                func_has_doc = False
                func_has_type_hints = bool(fm["has_type_hints"])
                in_func = True
                defined_funcs.add(func_name)
                defs_found_in_func[func_name] = []

                if len(func_params) > 5:
                    issues.append(self._make_issue(
                        "excessive_parameters", "medium",
                        f"Function '{func_name}' has {len(func_params)} parameters",
                        "Long parameter lists make functions hard to call and test.",
                        "Consolidate parameters into a single configuration object.",
                        "medium", i + 1,
                    ))

                doc_line = i + 1
                while doc_line < min(i + 6, n):
                    dl = lines[doc_line].strip()
                    if dl.startswith('"""') or dl.startswith("'''") or (dl.startswith('"') and len(dl) > 15):
                        func_has_doc = True
                        break
                    if dl and not dl.startswith("#") and not dl.startswith("@"):
                        break
                    doc_line += 1
                continue

            if in_func:
                func_loc += 1
                if re.search(r"\breturn\b", line_before_comment):
                    func_return_count += 1
                for token in re.findall(r'\b([a-zA-Z_]\w*)\s*\(', line_before_comment):
                    if token not in ("if", "elif", "while", "for", "switch", "catch", "with"):
                        called_funcs.add(token)
                        defs_found_in_func[func_name].append(token)

            cm = CodeQualityEngine._match_class(stripped, language)
            if cm:
                if class_name and class_methods > 20:
                    issues.append(self._make_issue(
                        "large_class", "medium",
                        f"Class '{class_name}' has {class_methods} methods",
                        "Classes with excessive methods violate SRP.",
                        "Split into smaller focused classes.",
                        "medium", class_start + 1,
                    ))
                class_name = cm
                class_start = i
                class_methods = 0
            if class_name and ("def " in line_before_comment or
                               re.search(r'\b(function|async\s+function)\b', line_before_comment)):
                class_methods += 1

            for tok in re.findall(r'(?<!\w)(\d{2,})(?!\w)', line_before_comment):
                val = int(tok)
                if val in (0, 1, -1, 100, 200, 404, 500):
                    continue
                if any(kw in line_before_comment for kw in ("import ", "from ", "range(", "len(", "version", "__")):
                    continue
                issues.append(self._make_issue(
                    "magic_number", "low",
                    f"Magic number {val} found",
                    "Numeric literals (except 0, 1, 100) should be named constants.",
                    f"Define a constant for this value.", "low", i + 1,
                ))
                break

            for m in re.finditer(r'["\']((https?://[^\s"\']+)|(/[^\s"\']+){2,})["\']', line_before_comment):
                if not any(p in raw for p in ("import ", "from ", "require(", "//")):
                    val = m.group(1)
                    is_secret = any(kw in val.lower() for kw in ("password", "secret", "token", "api_key"))
                    issues.append(self._make_issue(
                        "hardcoded_value", "high" if is_secret else "medium",
                        f"Hardcoded {'credential' if is_secret else 'path/URL'} found",
                        "Hardcoded values reduce flexibility.",
                        "Move to config or env vars.",
                        "high" if is_secret else "medium", i + 1,
                    ))
                    break

            for m in re.finditer(r'\b([a-z]{1,2}|_[a-z]+_)\b', line_before_comment):
                name = m.group(1)
                if name in ("id", "os", "ok", "in", "on", "to", "at", "if", "or", "is", "as", "be", "do", "go", "it", "my", "by", "up", "no", "we"):
                    continue
                if any(p in raw for p in ("import ", "from ", "//", "#", "def ", "class ")):
                    continue
                issues.append(self._make_issue(
                    "poor_naming", "low",
                    f"Poor naming: '{name}'",
                    "Short/ambiguous names reduce readability.",
                    f"Rename '{name}' to something descriptive.", "low", i + 1,
                ))
                break

            im = CodeQualityEngine._match_import(stripped, language)
            if im:
                imports.append(im)

            if language == "Python" and "except" in stripped:
                if ":" in stripped:
                    exc_part = stripped.split("except")[1].split(":")[0].strip()
                    if not exc_part:
                        seen_key = f"{rel_path}:{i}"
                        if seen_key not in seen_excepts:
                            seen_excepts.add(seen_key)
                            issues.append(self._make_issue(
                                "broad_exception", "high",
                                "Bare except: clause (catches all exceptions)",
                                "Catching all exceptions hides unexpected errors.",
                                "Specify the expected exception type (e.g., except ValueError:).",
                                "high", i + 1,
                            ))
                    elif exc_part in ("Exception", "BaseException", "StandardError"):
                        seen_key = f"{rel_path}:{i}"
                        if seen_key not in seen_excepts:
                            seen_excepts.add(seen_key)
                            issues.append(self._make_issue(
                                "broad_exception", "medium",
                                f"Broad except catches '{exc_part}'",
                                "Overly broad exception handling can mask bugs.",
                                "Catch only the specific exception types you expect.",
                                "medium", i + 1,
                            ))
                if "pass" in stripped:
                    seen_key2 = f"empty:{rel_path}:{i}"
                    if seen_key2 not in seen_excepts:
                        seen_excepts.add(seen_key2)
                        issues.append(self._make_issue(
                            "empty_exception_block", "high",
                            "Empty exception block (except: pass)",
                            "Empty except blocks silently swallow errors.",
                            "Either handle the exception or log it.",
                            "high", i + 1,
                        ))

            if language == "Python" and fm:
                if not fm["has_type_hints"]:
                    issues.append(self._make_issue(
                        "missing_type_hint", "low",
                        f"Function '{fm['name']}' lacks type hints",
                        "Type hints improve readability and enable static checking.",
                        "Add type annotations to parameters and return value.",
                        "low", i + 1,
                    ))

        if in_func:
            self._finalize_function(issues, func_name, func_start, func_loc,
                                    func_params, func_return_count,
                                    func_has_doc, func_has_type_hints,
                                    rel_path, language, n)

        if class_name and class_methods > 20:
            issues.append(self._make_issue(
                "large_class", "medium",
                f"Class '{class_name}' has {class_methods} methods",
                "Classes with excessive methods violate SRP.",
                "Split into smaller focused classes.",
                "medium", class_start + 1,
            ))

        if nesting_depths:
            max_depth = max(nesting_depths)
            if max_depth > 4:
                issues.append(self._make_issue(
                    "deep_nesting", "medium",
                    f"Deep nesting detected (depth {max_depth})",
                    "Nesting beyond 4 levels hurts readability.",
                    "Use early returns, guard clauses, or extract helper functions.",
                    "medium", None,
                ))

        # Unused function check
        for fn in defined_funcs:
            if fn not in called_funcs and not fn.startswith("_") and fn not in ("main", "setup", "teardown"):
                if fn.startswith("__") and fn.endswith("__"):
                    continue
                issues.append(self._make_issue(
                    "unused_function", "medium",
                    f"Function '{fn}' is defined but never called",
                    "Unused functions clutter the codebase and may indicate dead code.",
                    "Remove the function if it is no longer needed.",
                    "medium", None,
                ))

        for lineno, line_text in todo_lines:
            issues.append(self._make_issue(
                "todo_fixme", "low",
                f"TODO/FIXME: '{line_text.strip()}'",
                "Incomplete work items should be tracked or resolved.",
                "Address the TODO or create a tracking issue.",
                "low", lineno + 1,
            ))

        seen_imports_file: set[str] = set()
        for imp_src in imports:
            if imp_src in seen_imports_file:
                issues.append(self._make_issue(
                    "duplicate_import", "low",
                    f"Duplicate import: '{imp_src}'",
                    "Importing the same module multiple times is unnecessary.",
                    "Keep a single import per module.",
                    "low", None,
                ))
            seen_imports_file.add(imp_src)

        return {
            "issues": issues,
            "func_name": func_name,
            "func_count": len(defined_funcs),
            "class_count": len(set(c[0] for c in classes)),
            "defined_funcs": list(defined_funcs),
            "called_funcs": list(called_funcs),
            "imports": imports,
            "import_count": len(set(imports)),
            "todo_lines": todo_lines,
            "classes": classes,
            "funcs": funcs,
        }

    def _finalize_function(self, issues: list[dict], func_name: str, func_start: int,
                           func_loc: int, params: list[str], return_count: int,
                           has_doc: bool, has_hints: bool, rel_path: str,
                           language: str, end_line: int) -> None:
        if func_loc > 60:
            issues.append(self._make_issue(
                "long_function", "medium",
                f"Function '{func_name}' has {func_loc} lines",
                "Long functions are hard to understand and test.",
                "Extract logical blocks into well-named helper functions.",
                "medium", func_start + 1,
            ))
        if return_count > 5:
            issues.append(self._make_issue(
                "excessive_returns", "low",
                f"Function '{func_name}' has {return_count} return statements",
                "Multiple return points can make control flow confusing.",
                "Consider consolidating return paths.",
                "low", func_start + 1,
            ))

    @staticmethod
    def _make_issue(issue_type: str, severity: str, description: str,
                    reason: str, suggested_fix: str, priority: str,
                    line: int | None) -> dict:
        return {
            "type": issue_type,
            "severity": severity,
            "description": description,
            "reason": reason,
            "suggested_fix": suggested_fix,
            "priority": priority,
            "line": line,
        }

    @staticmethod
    def _compute_file_scores(complexity: int, comment_lines: int, total_lines: int,
                              info: dict, language: str) -> dict:
        n_issues = len(info["issues"])
        func_count = max(info["func_count"], 1)
        import_count = info["import_count"]
        has_doc = any(i["type"] == "missing_docstring" for i in info["issues"])
        has_magic = any(i["type"] == "magic_number" for i in info["issues"])
        has_naming = any(i["type"] == "poor_naming" for i in info["issues"])
        has_hardcoded = any(i["type"] == "hardcoded_value" for i in info["issues"])
        has_empty_except = any(i["type"] == "empty_exception_block" for i in info["issues"])
        has_broad_except = any(i["type"] == "broad_exception" for i in info["issues"])
        has_dead_code = any(i["type"] == "unused_function" for i in info["issues"])
        has_long_func = any(i["type"] == "long_function" for i in info["issues"])
        has_deep_nest = any(i["type"] == "deep_nesting" for i in info["issues"])
        has_large_class = any(i["type"] == "large_class" for i in info["issues"])
        has_missing_hints = any(i["type"] == "missing_type_hint" for i in info["issues"])
        has_excessive_params = any(i["type"] == "excessive_parameters" for i in info["issues"])

        comment_ratio = comment_lines / max(total_lines, 1)

        # Maintainability
        maint = 100.0
        if complexity > 10:
            maint -= min((complexity - 10) * 3, 20)
        if has_long_func:
            maint -= 15
        if has_large_class:
            maint -= 10
        if has_dead_code:
            maint -= 10
        if has_deep_nest:
            maint -= 10
        if comment_ratio < 0.05 and total_lines > 50:
            maint -= 10
        maint = max(0, min(100, maint))

        # Complexity
        comp = 100.0
        if complexity > 5:
            comp -= min((complexity - 5) * 5, 30)
        if has_long_func:
            comp -= 15
        if has_deep_nest:
            comp -= 10
        if has_excessive_params:
            comp -= 10
        if has_large_class:
            comp -= 10
        comp = max(0, min(100, comp))

        # Readability
        read = 100.0
        if has_naming:
            read -= 15
        if has_magic:
            read -= 10
        if has_deep_nest:
            read -= 10
        if has_doc:
            read -= 15
        if has_missing_hints:
            read -= 10
        if comment_ratio < 0.03:
            read -= 10
        read = max(0, min(100, read))

        # Documentation
        doc = min(100, comment_ratio * 200)
        if has_doc:
            doc -= 20
        doc = max(0, doc)

        # Security
        sec = 100.0
        if has_hardcoded:
            sec -= 25
        if has_empty_except:
            sec -= 30
        if has_broad_except:
            sec -= 15
        sec = max(0, min(100, sec))

        # Overall
        overall = (maint * 0.25 + comp * 0.20 + read * 0.20 + doc * 0.10 + sec * 0.25)
        overall = max(0, min(100, overall))

        return {
            "overall": round(overall, 1),
            "maintainability": round(maint, 1),
            "complexity": round(comp, 1),
            "readability": round(read, 1),
            "documentation": round(doc, 1),
            "security": round(sec, 1),
        }

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

    @staticmethod
    def _auto_tag(rel_path: str, language: str, info: dict) -> list[str]:
        tags: list[str] = []
        path_lower = rel_path.lower()

        if "test" in path_lower or "spec" in path_lower:
            tags.append("Testing")
        if "config" in path_lower or ".env" in path_lower or "settings" in path_lower:
            tags.append("Configuration")
        if "util" in path_lower or "helper" in path_lower or "common" in path_lower:
            tags.append("Utilities")
        if "model" in path_lower or "entity" in path_lower:
            tags.append("Database")
        if "api" in path_lower or "route" in path_lower or "endpoint" in path_lower or "controller" in path_lower:
            tags.append("API")
        if "auth" in path_lower or "login" in path_lower or "security" in path_lower:
            tags.append("Authentication")
        if "forecast" in path_lower or "predict" in path_lower or "ml_" in path_lower:
            tags.append("Machine Learning")
        if "doc" in path_lower and language in ("Markdown",):
            tags.append("Documentation")
        if "frontend" in path_lower or language in ("JavaScript", "TypeScript", "CSS", "HTML"):
            tags.append("Frontend")
        if "backend" in path_lower or ("server" in path_lower and language in ("Python", "Java", "Go", "C#", "C++")):
            tags.append("Backend")
        if "business" in path_lower or "service" in path_lower or "logic" in path_lower:
            tags.append("Business Logic")
        if language == "Python" and "init" in rel_path:
            tags.append("Module")
        if "middleware" in path_lower or "plugin" in path_lower:
            tags.append("Middleware")
        if "migration" in path_lower:
            tags.append("Migration")

        if not tags:
            if language in ("JavaScript", "TypeScript"):
                tags.append("Frontend")
            elif language in ("Python", "Java", "Go", "C#", "Ruby"):
                tags.append("Backend")
            elif language in ("Markdown",):
                tags.append("Documentation")
            elif language in ("JSON", "YAML", "TOML"):
                tags.append("Configuration")
            else:
                tags.append("Source")

        return tags

    @staticmethod
    def _generate_file_summary(rel_path: str, scores: dict, health: str,
                                info: dict, tags: list[str]) -> str:
        parts: list[str] = []
        n_issues = len(info["issues"])
        n_funcs = info["func_count"]
        n_classes = info["class_count"]

        if health in ("Excellent", "Good"):
            base = "well-structured"
        elif health == "Fair":
            base = "moderately structured"
        else:
            base = "needs improvement"

        quality = "high" if scores["overall"] >= 75 else ("moderate" if scores["overall"] >= 55 else "low")
        parts.append(f"This {base} file has {quality} quality (score {scores['overall']:.0f}/100)")

        issue_types = [i["type"] for i in info["issues"]]
        issues_desc = []
        if "long_function" in issue_types:
            issues_desc.append(f"{issue_types.count('long_function')} long function(s)")
        if "magic_number" in issue_types:
            issues_desc.append("magic numbers")
        if "poor_naming" in issue_types:
            issues_desc.append("naming violations")
        if "hardcoded_value" in issue_types:
            issues_desc.append("hardcoded values")
        if "broad_exception" in issue_types:
            issues_desc.append("broad exception handling")
        if "empty_exception_block" in issue_types:
            issues_desc.append("empty exception blocks")
        if "deep_nesting" in issue_types:
            issues_desc.append("deep nesting")
        if "unused_function" in issue_types:
            issues_desc.append("dead code")
        if "missing_docstring" in issue_types:
            issues_desc.append("missing docstrings")
        if "missing_type_hint" in issue_types:
            issues_desc.append("missing type hints")
        if "excessive_parameters" in issue_types:
            issues_desc.append("long parameter lists")
        if "duplicate_import" in issue_types:
            issues_desc.append("duplicate imports")
        if "large_class" in issue_types:
            issues_desc.append("large classes")

        if issues_desc:
            parts.append(f"with {', '.join(issues_desc)}")

        if n_funcs > 0:
            parts.append(f"containing {n_funcs} function(s)")
        if n_classes > 0:
            parts.append(f"and {n_classes} class(es)")

        if health == "Excellent":
            parts.append("following clean code practices")
        elif health in ("Needs Improvement", "Poor"):
            parts.append("requiring targeted improvements")

        return ". ".join(parts) + "." if parts else f"File has {n_issues} issue(s) with a score of {scores['overall']:.0f}/100."
