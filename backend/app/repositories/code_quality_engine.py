import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.repositories.source_code_intelligence_engine import (
    IGNORED_DIRS,
    IGNORED_FILES,
    EXTENSION_LANGUAGE_MAP,
    SUPPORTED_EXTENSIONS,
)


class CodeQualityEngine:
    def analyze(self, workspace_path: Path) -> dict:
        all_issues: list[dict] = []
        file_records: list[dict] = []
        content_hashes: dict[str, list[str]] = {}

        total_files = 0
        total_loc = 0
        total_lines = 0
        total_comments = 0
        total_blank = 0
        all_complexities: list[int] = []
        all_func_counts: list[int] = []
        all_class_counts: list[int] = []
        has_test_files = False

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

                if not has_test_files and ("test" in f.lower() or "spec" in f.lower()):
                    has_test_files = True

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

                # ---- comment / blank / loc ----
                comment_lines, blank_lines = self._count_comments_blanks(lines, language)
                loc = max(0, n_lines - comment_lines - blank_lines)
                complexity = self._compute_complexity(lines, language)

                total_files += 1
                total_loc += loc
                total_lines += n_lines
                total_comments += comment_lines
                total_blank += blank_lines
                all_complexities.append(complexity)

                # ---- duplicate content tracking ----
                content_hash = self._hash_content(content)
                if content_hash not in content_hashes:
                    content_hashes[content_hash] = []
                content_hashes[content_hash].append(rel_path)

                # ---- per-file analysis ----
                file_issues: list[dict] = []
                info = self._analyze_file(lines, content, rel_path, language, workspace_path)

                file_issues.extend(info["issues"])

                # ---- large file check ----
                if n_lines > 500:
                    file_issues.append(self._make_issue(
                        "large_file", "medium", f"Large file ({n_lines} lines)", rel_path,
                        "Files over 500 lines become difficult to navigate and maintain.",
                        "Consider splitting this file into smaller, focused modules.",
                        "medium", info["func_name"], None,
                    ))

                # ---- high complexity check ----
                if complexity > 15:
                    file_issues.append(self._make_issue(
                        "high_cyclomatic_complexity", "high",
                        f"Cyclomatic complexity is {complexity}", rel_path,
                        "High complexity makes code hard to test and maintain.",
                        "Break complex functions into smaller, well-named helper functions.",
                        "high", info["func_name"], None,
                    ))

                # ---- large class check (by lines) ----
                for cls_name, cls_start, cls_end in info["classes"]:
                    cls_lines = cls_end - cls_start
                    if cls_lines > 300:
                        file_issues.append(self._make_issue(
                            "large_class", "medium",
                            f"Class '{cls_name}' spans {cls_lines} lines", rel_path,
                            "Large classes tend to violate the Single Responsibility Principle.",
                            "Extract related behaviour into separate classes.",
                            "medium", cls_name, cls_start + 1,
                        ))

                # ---- unused function check ----
                defined_funcs = set(info["defined_funcs"])
                called_funcs = info["called_funcs"]
                for fn in defined_funcs:
                    if fn not in called_funcs and not fn.startswith("_") and fn not in ("main", "setup", "teardown"):
                        # Skip dunder methods
                        if fn.startswith("__") and fn.endswith("__"):
                            continue
                        file_issues.append(self._make_issue(
                            "unused_function", "medium",
                            f"Function '{fn}' is defined but never called", rel_path,
                            "Unused functions clutter the codebase and may indicate dead code.",
                            "Remove the function if it is no longer needed, or add a caller.",
                            "medium", fn, None,
                        ))

                # ---- TODO / FIXME check ----
                for lineno, line_text in info["todo_lines"]:
                    file_issues.append(self._make_issue(
                        "todo_fixme", "low",
                        f"TODO/FIXME comment found: '{line_text.strip()}'", rel_path,
                        "Incomplete work items should be tracked or resolved.",
                        "Either address the TODO or create a tracking issue and reference it here.",
                        "low", info["func_name"], lineno + 1,
                    ))

                # ---- duplicate imports ----
                seen_imports_file: set[str] = set()
                for imp_src in info["imports"]:
                    if imp_src in seen_imports_file:
                        file_issues.append(self._make_issue(
                            "duplicate_import", "low",
                            f"Duplicate import: '{imp_src}'", rel_path,
                            "Importing the same module multiple times is unnecessary.",
                            "Keep a single import per module at the top of the file.",
                            "low", None, None,
                        ))
                    seen_imports_file.add(imp_src)

                # ---- high coupling check ----
                if info["import_count"] > 15:
                    file_issues.append(self._make_issue(
                        "high_coupling", "medium",
                        f"File imports {info['import_count']} modules (high coupling)", rel_path,
                        "Too many dependencies make a module fragile and hard to test.",
                        "Consider reducing dependencies or introducing abstraction layers.",
                        "medium", None, None,
                    ))

                all_issues.extend(file_issues)
                file_records.append({
                    "path": rel_path,
                    "language": language,
                    "lines_of_code": loc,
                    "total_lines": n_lines,
                    "complexity": complexity,
                    "issue_count": len(file_issues),
                    "issues": file_issues,
                    "func_count": info["func_count"],
                    "class_count": info["class_count"],
                    "import_count": info["import_count"],
                })
                all_func_counts.append(info["func_count"])
                all_class_counts.append(info["class_count"])

        # ---- duplicate code detection (cross-file) ----
        duplicate_groups = {h: paths for h, paths in content_hashes.items() if len(paths) > 1}
        for group_paths in duplicate_groups.values():
            for dup_path in group_paths[1:]:
                all_issues.append(self._make_issue(
                    "duplicate_code", "medium",
                    f"File is a duplicate of '{group_paths[0]}'", dup_path,
                    "Identical files increase maintenance burden.",
                    "Remove the duplicate and import from the canonical source.",
                    "medium", None, None,
                ))

        # ---- compile totals ----
        total_issues = len(all_issues)
        avg_complexity = sum(all_complexities) / max(len(all_complexities), 1)
        max_complexity = max(all_complexities) if all_complexities else 0
        comment_ratio = total_comments / max(total_lines, 1)

        # ---- severity counts ----
        sev: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for i in all_issues:
            s = i.get("severity", "low")
            if s in sev:
                sev[s] += 1

        # ---- typed aggregators ----
        type_counts: Counter[str] = Counter()
        file_issue_map: dict[str, list[dict]] = defaultdict(list)
        for i in all_issues:
            type_counts[i["type"]] += 1
            file_issue_map[i["affected_file"]].append(i)

        funcs_long = type_counts.get("long_function", 0)
        classes_large = type_counts.get("large_class", 0)
        dup_code = type_counts.get("duplicate_code", 0)
        unused_imports = type_counts.get("unused_import", 0)
        unused_vars = type_counts.get("unused_variable", 0)
        dead_code = type_counts.get("unused_function", 0)
        magic_nums = type_counts.get("magic_number", 0)
        deep_nest = type_counts.get("deep_nesting", 0)
        long_params = type_counts.get("excessive_parameters", 0)
        missing_doc = type_counts.get("missing_docstring", 0)
        empty_except = type_counts.get("empty_exception_block", 0)
        hardcoded = type_counts.get("hardcoded_value", 0)
        poor_names = type_counts.get("poor_naming", 0)
        broad_except = type_counts.get("broad_exception", 0)
        missing_hints = type_counts.get("missing_type_hint", 0)
        excessive_returns = type_counts.get("excessive_returns", 0)
        high_coupling = type_counts.get("high_coupling", 0)
        low_cohesion = type_counts.get("low_cohesion", 0)
        todo_fixme = type_counts.get("todo_fixme", 0)
        high_complexity = type_counts.get("high_cyclomatic_complexity", 0)
        large_files = type_counts.get("large_file", 0)
        unused_funcs = type_counts.get("unused_function", 0)
        dup_imports = type_counts.get("duplicate_import", 0)

        # ---- scores ----
        overall = self._compute_overall(
            total_files, total_issues, avg_complexity, max_complexity,
            comment_ratio, funcs_long, high_complexity, hardcoded, empty_except,
        )
        maintainability = self._compute_maintainability(
            avg_complexity, comment_ratio, funcs_long, classes_large, dup_code, dead_code,
        )
        readability = self._compute_readability(
            poor_names, magic_nums, deep_nest, missing_doc, missing_hints,
        )
        complexity_score = self._compute_complexity_score(
            avg_complexity, max_complexity, funcs_long, high_complexity, deep_nest, long_params,
        )
        documentation = self._compute_documentation_score(
            comment_ratio, missing_doc, total_files,
        )
        security = self._compute_security_score(
            hardcoded, empty_except, broad_except, todo_fixme,
        )
        tech_debt = self._compute_technical_debt(
            total_issues, funcs_long, long_params, deep_nest, dup_code, unused_funcs, high_complexity,
        )

        # ---- checks ----
        checks = self._build_checks(
            all_issues, type_counts, has_test_files,
        )

        # ---- insights ----
        insights = self._generate_insights(
            all_issues, type_counts, overall, avg_complexity, file_records, total_files,
            all_complexities, max_complexity, total_loc, total_comments, comment_ratio,
            has_test_files, list(duplicate_groups.keys()),
            total_funcs=sum(all_func_counts),
            total_classes=sum(all_class_counts),
        )

        # ---- recommendations ----
        recommendations = self._generate_recommendations(
            all_issues, type_counts, file_records, overall, avg_complexity,
            readability, security, tech_debt,
        )

        # ---- AI summary ----
        ai_summary = self._generate_ai_summary(
            overall_score=overall,
            maintainability_score=maintainability,
            readability_score=readability,
            complexity_score=complexity_score,
            documentation_score=documentation,
            security_score=security,
            technical_debt_score=tech_debt,
            avg_complexity=avg_complexity,
            max_complexity=max_complexity,
            total_files=total_files,
            total_issues=total_issues,
            total_loc=total_loc,
            total_comments=total_comments,
            comment_ratio=comment_ratio,
            has_test_files=has_test_files,
            duplicate_groups=list(duplicate_groups.keys()),
            file_records=file_records,
            type_counts=type_counts,
        )

        # ---- top problematic / clean files ----
        scored_files = []
        for fr in file_records:
            sc = max(0, 100 - fr["issue_count"] * 8)
            scored_files.append({**fr, "score": sc})
        top_problematic = sorted(
            [f for f in scored_files if f["issue_count"] > 0],
            key=lambda x: -x["issue_count"],
        )[:5]
        top_clean = sorted(
            [f for f in scored_files if f["issue_count"] == 0],
            key=lambda x: x["path"],
        )[:5]

        language_breakdown = self._build_language_breakdown(file_records)

        return {
            "overall_score": {"score": round(overall, 1), "label": self._score_label(overall)},
            "maintainability_score": {"score": round(maintainability, 1), "label": self._score_label(maintainability)},
            "readability_score": {"score": round(readability, 1), "label": self._score_label(readability)},
            "complexity_score": {"score": round(complexity_score, 1), "label": self._score_label(complexity_score)},
            "documentation_score": {"score": round(documentation, 1), "label": self._score_label(documentation)},
            "security_score": {"score": round(security, 1), "label": self._score_label(security)},
            "technical_debt_score": {"score": round(tech_debt, 1), "label": self._score_label(tech_debt)},
            "checks": checks,
            "insights": insights,
            "recommendations": recommendations,
            "severity_counts": sev,
            "total_issues": total_issues,
            "top_problematic_files": [{"path": f["path"], "issue_count": f["issue_count"], "score": int(f["score"])} for f in top_problematic],
            "top_clean_files": [{"path": f["path"], "issue_count": f["issue_count"], "score": int(f["score"])} for f in top_clean],
            "language_breakdown": language_breakdown,
            "ai_summary": ai_summary,
        }

    # ======================================================================
    # Per-file analysis
    # ======================================================================

    def _analyze_file(self, lines: list[str], content: str, rel_path: str, language: str, workspace_path: Path) -> dict:
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

        defs_found_in_func: dict[str, list[str]] = defaultdict(list)  # fn -> [called within]

        for i, raw in enumerate(lines):
            stripped = raw.strip()
            line_before_comment = stripped.split("#")[0].split("//")[0].strip() if language != "Python" else stripped.split("#")[0].strip()

            # ---- skip blanks / comments ----
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

            # ---- nesting ----
            delta = stripped.count("{") + stripped.count("(") + stripped.count("[") - stripped.count("}") - stripped.count(")") - stripped.count("]")
            if language == "Python":
                if re.match(r"^\s*(if|elif|else|for|while|with|try|except)\b", stripped):
                    current_nesting += 1
            else:
                current_nesting = max(0, current_nesting + delta)
            if current_nesting > 0:
                nesting_depths.append(current_nesting)
            if language != "Python":
                current_nesting = max(0, current_nesting + delta)

            # ---- function detection ----
            fm = self._match_function(stripped, language)
            if fm:
                # close previous function if open
                if in_func:
                    self._finalize_function(issues, func_name, func_start, func_loc, func_params,
                                            func_return_count, func_has_doc, func_has_type_hints,
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

                # excessive parameters
                if len(func_params) > 5:
                    issues.append(self._make_issue(
                        "excessive_parameters", "medium",
                        f"Function '{func_name}' has {len(func_params)} parameters", rel_path,
                        "Long parameter lists make functions hard to call and test.",
                        "Consolidate parameters into a single configuration object.",
                        "medium", func_name, i + 1,
                    ))

                # docstring check
                doc_line = i + 1
                while doc_line < min(i + 6, n):
                    dl = lines[doc_line].strip()
                    if dl.startswith('"""') or dl.startswith("'''") or dl.startswith('"') and len(dl) > 15:
                        func_has_doc = True
                        break
                    if dl and not dl.startswith("#") and not dl.startswith("@"):
                        break
                    doc_line += 1
                continue

            if in_func:
                func_loc += 1
                # return counting
                if re.search(r"\breturn\b", line_before_comment):
                    func_return_count += 1
                # track calls within this function
                for token in re.findall(r'\b([a-zA-Z_]\w*)\s*\(', line_before_comment):
                    if token not in ("if", "elif", "while", "for", "switch", "catch", "with"):
                        called_funcs.add(token)
                        defs_found_in_func[func_name].append(token)

            # ---- class detection ----
            cm = self._match_class(stripped, language)
            if cm:
                if class_name and class_methods > 20:
                    issues.append(self._make_issue(
                        "large_class", "medium",
                        f"Class '{class_name}' has {class_methods} methods", rel_path,
                        "Classes with excessive methods violate SRP.",
                        "Split into smaller focused classes.",
                        "medium", class_name, class_start + 1,
                    ))
                class_name = cm
                class_start = i
                class_methods = 0
            if class_name and ("def " in line_before_comment or re.search(r'\b(function|async\s+function)\b', line_before_comment)):
                class_methods += 1

            # ---- magic numbers ----
            for tok in re.findall(r'(?<!\w)(\d{2,})(?!\w)', line_before_comment):
                val = int(tok)
                if val in (0, 1, -1, 100, 200, 404, 500):
                    continue
                if any(kw in line_before_comment for kw in ("import ", "from ", "range(", "len(", "version", "__")):
                    continue
                if 10 < val < 100 and line_before_comment.count("\"") > 1 or line_before_comment.count("'") > 1:
                    continue  # likely a test value or index
                issues.append(self._make_issue(
                    "magic_number", "low",
                    f"Magic number {val} found", rel_path,
                    "Numeric literals (except 0, 1, 100) should be named constants.",
                    f"Define a constant like {func_name.upper() if func_name else 'MAX_RETRIES'} = {val}.",
                    "low", func_name, i + 1,
                ))
                break  # cap at 1 per function unless another comes much later

            # ---- hardcoded values ----
            for m in re.finditer(r'["\']((https?://[^\s"\']+)|(/[^\s"\']+){2,})["\']', line_before_comment):
                if not any(p in raw for p in ("import ", "from ", "require(", "//")):
                    val = m.group(1)
                    is_secret = any(kw in val.lower() for kw in ("password", "secret", "token", "api_key"))
                    issues.append(self._make_issue(
                        "hardcoded_value", "high" if is_secret else "medium",
                        f"Hardcoded {'credential' if is_secret else 'path/URL'} found", rel_path,
                        "Hardcoded values reduce flexibility.", "Move to config or env vars.",
                        "high" if is_secret else "medium", func_name, i + 1,
                    ))
                    break

            # ---- naming convention ----
            for m in re.finditer(r'\b([a-z]{1,2}|_[a-z]+_)\b', line_before_comment):
                name = m.group(1)
                if name in ("id", "os", "ok", "in", "on", "to", "at", "if", "or", "is", "as", "be", "do", "go", "it", "my", "by", "up", "no", "we"):
                    continue
                if any(p in raw for p in ("import ", "from ", "//", "#", "def ", "class ")):
                    continue
                issues.append(self._make_issue(
                    "poor_naming", "low",
                    f"Poor naming: '{name}'", rel_path,
                    "Short/ambiguous names reduce readability.",
                    f"Rename '{name}' to something descriptive.",
                    "low", func_name, i + 1,
                ))
                break  # 1 naming issue per function

            # ---- imports ----
            im = self._match_import(stripped, language)
            if im:
                imports.append(im)

            # ---- empty / broad exception ----
            if language == "Python" and "except" in stripped:
                if ":" in stripped:
                    exc_part = stripped.split("except")[1].split(":")[0].strip()
                    if not exc_part:
                        seen_key = f"{rel_path}:{i}"
                        if seen_key not in seen_excepts:
                            seen_excepts.add(seen_key)
                            issues.append(self._make_issue(
                                "broad_exception", "high",
                                "Bare except: clause (catches all exceptions)", rel_path,
                                "Catching all exceptions hides unexpected errors.",
                                "Specify the expected exception type (e.g., except ValueError:).",
                                "high", func_name, i + 1,
                            ))
                    elif exc_part in ("Exception", "BaseException", "StandardError"):
                        seen_key = f"{rel_path}:{i}"
                        if seen_key not in seen_excepts:
                            seen_excepts.add(seen_key)
                            issues.append(self._make_issue(
                                "broad_exception", "medium",
                                f"Broad except catches '{exc_part}'", rel_path,
                                "Overly broad exception handling can mask bugs.",
                                "Catch only the specific exception types you expect.",
                                "medium", func_name, i + 1,
                            ))
                if "pass" in stripped:
                    seen_key2 = f"empty:{rel_path}:{i}"
                    if seen_key2 not in seen_excepts:
                        seen_excepts.add(seen_key2)
                        issues.append(self._make_issue(
                            "empty_exception_block", "high",
                            "Empty exception block (except: pass)", rel_path,
                            "Empty except blocks silently swallow errors.",
                            "Either handle the exception or log it, never leave it empty.",
                            "high", func_name, i + 1,
                        ))

            # ---- missing type hints (Python only) ----
            if language == "Python" and fm:
                if not fm["has_type_hints"]:
                    issues.append(self._make_issue(
                        "missing_type_hint", "low",
                        f"Function '{fm['name']}' lacks type hints", rel_path,
                        "Type hints improve readability and enable static checking.",
                        "Add type annotations to parameters and return value.",
                        "low", fm["name"], i + 1,
                    ))

        # ----------------------------------------------------------------
        # End-of-file checks
        # ----------------------------------------------------------------
        if in_func:
            self._finalize_function(issues, func_name, func_start, func_loc, func_params,
                                    func_return_count, func_has_doc, func_has_type_hints,
                                    rel_path, language, n)

        if class_name and class_methods > 20:
            issues.append(self._make_issue(
                "large_class", "medium",
                f"Class '{class_name}' has {class_methods} methods", rel_path,
                "Classes with excessive methods violate SRP.",
                "Split into smaller focused classes.",
                "medium", class_name, class_start + 1,
            ))

        # ---- deep nesting ----
        if nesting_depths:
            max_depth = max(nesting_depths)
            if max_depth > 4:
                issues.append(self._make_issue(
                    "deep_nesting", "medium",
                    f"Deep nesting detected (depth {max_depth})", rel_path,
                    "Nesting beyond 4 levels hurts readability.",
                    "Use early returns, guard clauses, or extract helper functions.",
                    "medium", func_name, None,
                ))

        return {
            "issues": issues,
            "func_name": func_name,
            "func_count": len([f for f in defined_funcs if not f.startswith("_") or f == "__init__"]),
            "class_count": len(classes),
            "defined_funcs": list(defined_funcs),
            "called_funcs": list(called_funcs),
            "imports": imports,
            "import_count": len(set(imports)),
            "todo_lines": todo_lines,
            "classes": classes,
        }

    # ======================================================================
    # Helpers
    # ======================================================================

    def _finalize_function(self, issues: list[dict], func_name: str, func_start: int,
                           func_loc: int, params: list[str], return_count: int,
                           has_doc: bool, has_hints: bool, rel_path: str,
                           language: str, end_line: int) -> None:
        if func_loc > 60:
            issues.append(self._make_issue(
                "long_function", "medium",
                f"Function '{func_name}' has {func_loc} lines", rel_path,
                "Long functions are hard to understand and test.",
                "Extract logical blocks into well-named helper functions.",
                "medium", func_name, func_start + 1,
            ))
        if return_count > 5:
            issues.append(self._make_issue(
                "excessive_returns", "low",
                f"Function '{func_name}' has {return_count} return statements", rel_path,
                "Multiple return points can make control flow confusing.",
                "Consider consolidating return paths or using a single exit point.",
                "low", func_name, func_start + 1,
            ))

    @staticmethod
    def _make_issue(issue_type: str, severity: str, description: str,
                    affected_file: str, reason: str, suggested_fix: str,
                    priority: str, affected_function: str | None, line: int | None) -> dict:
        return {
            "type": issue_type,
            "severity": severity,
            "description": description,
            "reason": reason,
            "suggested_fix": suggested_fix,
            "priority": priority,
            "affected_file": affected_file,
            "affected_function": affected_function,
            "line": line,
        }

    @staticmethod
    def _match_function(stripped: str, language: str) -> dict | None:
        name, params, has_hints = None, [], False
        if language == "Python":
            m = re.match(r"^\s*(?:async\s+)?def\s+(\w+)\s*\((.*?)\)\s*(?:->\s*\w+)?\s*:", stripped)
            if m:
                name = m.group(1)
                raw_params = m.group(2)
                if raw_params.strip():
                    for p in re.split(r",\s*(?![^()]*\))", raw_params):
                        p = p.strip()
                        if p and p != "self" and p != "cls" and not p.startswith("*"):
                            if ":" in p:
                                has_hints = True
                            params.append(p.split(":")[0].split("=")[0].strip())
        elif language in ("JavaScript", "TypeScript"):
            m = re.match(r"^\s*(?:export\s+)?(?:async\s+)?(?:function\s+)?(\w+)\s*\((.*?)\)", stripped)
            if not m:
                m = re.match(r"^\s*(\w+)\s*=\s*(?:async\s+)?\((.*?)\)\s*=>", stripped)
            if not m:
                m = re.match(r"^\s*(\w+)\s*\((.*?)\)\s*\{", stripped)
            if m:
                name = m.group(1)
                raw = m.group(2)
                if raw.strip():
                    params = [p.strip() for p in raw.split(",") if p.strip()]
        elif language in ("Java", "C#", "C++"):
            m = re.match(r"^\s*(?:public|private|protected|static|\s)*\s+(\w+(?:\[\])?)\s+(\w+)\s*\((.*?)\)", stripped)
            if m:
                name = m.group(2)
                raw = m.group(3)
                if raw.strip():
                    params = [p.strip().split()[-1] if " " in p.strip() else p.strip() for p in raw.split(",") if p.strip()]
        elif language == "C":
            m = re.match(r"^\s*\w+\s+(\w+)\s*\((.*?)\)", stripped)
            if m:
                name = m.group(1)
                raw = m.group(2)
                if raw.strip():
                    params = [p.strip().split()[-1] for p in raw.split(",") if p.strip()]
        if name and name not in ("if", "elif", "else", "while", "for", "switch", "catch"):
            return {"name": name, "params": params, "has_type_hints": has_hints}
        return None

    @staticmethod
    def _match_class(stripped: str, language: str) -> str | None:
        if language == "Python":
            m = re.match(r"^\s*class\s+(\w+)", stripped)
        elif language in ("Java", "C#", "C++"):
            m = re.match(r"^\s*(?:public|private|protected|static|\s)*\s*(?:class|interface)\s+(\w+)", stripped)
        elif language in ("JavaScript", "TypeScript"):
            m = re.match(r"^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)", stripped)
        else:
            return None
        return m.group(1) if m else None

    @staticmethod
    def _match_import(stripped: str, language: str) -> str | None:
        if language == "Python":
            m = re.match(r"^\s*import\s+(\S+)", stripped)
            if m:
                return m.group(1).split(" as ")[0].split("#")[0].strip()
            m = re.match(r"^\s*from\s+(\S+)\s+import", stripped)
            if m:
                return m.group(1).split("#")[0].strip()
        elif language in ("JavaScript", "TypeScript"):
            m = re.search(r"(?:import|require)\s*\(?\s*['\"]([^'\"]+)['\"]", stripped)
            if m:
                return m.group(1)
            m = re.match(r"^\s*import\s+\S+\s+from\s+['\"]([^'\"]+)['\"]", stripped)
            if m:
                return m.group(1)
        elif language == "Java":
            m = re.match(r"^\s*import\s+(\S+)", stripped)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def _count_comments_blanks(lines: list[str], language: str) -> tuple[int, int]:
        comments = 0
        blanks = 0
        in_multiline = False
        for line in lines:
            s = line.strip()
            if not s:
                blanks += 1
                continue
            if in_multiline:
                comments += 1
                if "*/" in s:
                    in_multiline = False
                continue
            if language == "Python":
                if s.startswith('#') or s.startswith('"""') or s.startswith("'''"):
                    comments += 1
                    if (s.startswith('"""') and s.count('"""') == 1 and not s.endswith('"""')) or \
                       (s.startswith("'''") and s.count("'''") == 1 and not s.endswith("'''")):
                        in_multiline = True
                    continue
            else:
                if s.startswith("//"):
                    comments += 1
                    continue
                if s.startswith("/*"):
                    comments += 1
                    if "*/" not in s:
                        in_multiline = True
                    continue
        return comments, blanks

    @staticmethod
    def _hash_content(content: str) -> str:
        import hashlib
        return hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()

    @staticmethod
    def _compute_complexity(lines: list[str], language: str) -> int:
        c = 1
        for line in lines:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("//"):
                continue
            for kw in ("if ", "elif ", "else:", "for ", "while ", "except ", "case ", "catch "):
                if kw in s:
                    c += 1
                    break
            c += s.count("&&") + s.count("||")
        return c

    # ======================================================================
    # Score calculations
    # ======================================================================

    @staticmethod
    def _score_label(score: float) -> str:
        if score >= 90: return "Excellent"
        if score >= 75: return "Good"
        if score >= 60: return "Fair"
        if score >= 40: return "Poor"
        return "Critical"

    @staticmethod
    def _compute_overall(total_files: int, total_issues: int, avg_complexity: float,
                         max_complexity: int, comment_ratio: float, long_funcs: int,
                         high_complexity: int, hardcoded: int, empty_except: int) -> float:
        issue_density = total_issues / max(total_files, 1)
        base = 100.0
        base -= min(issue_density * 5, 30)
        if avg_complexity > 5:
            base -= min((avg_complexity - 5) * 2, 15)
        if max_complexity > 20:
            base -= min((max_complexity - 20) * 0.5, 10)
        if comment_ratio < 0.1:
            base -= 10
        base -= min(long_funcs * 2, 10)
        base -= min(high_complexity * 3, 10)
        base -= min(hardcoded * 5, 10)
        base -= min(empty_except * 8, 10)
        return max(0, min(100, base))

    @staticmethod
    def _compute_maintainability(avg_complexity: float, comment_ratio: float,
                                  long_funcs: int, large_classes: int,
                                  duplicate_code: int, dead_code: int) -> float:
        base = 100.0
        if avg_complexity > 4:
            base -= min((avg_complexity - 4) * 3, 20)
        if comment_ratio < 0.1:
            base -= 15
        base -= min(long_funcs * 4, 20)
        base -= min(large_classes * 5, 15)
        base -= min(duplicate_code * 5, 15)
        base -= min(dead_code * 3, 10)
        return max(0, min(100, base))

    @staticmethod
    def _compute_readability(poor_names: int, magic_numbers: int, deep_nesting: int,
                              missing_docstrings: int, missing_hints: int) -> float:
        base = 100.0
        base -= min(poor_names * 5, 20)
        base -= min(magic_numbers * 3, 15)
        base -= min(deep_nesting * 8, 20)
        base -= min(missing_docstrings * 2, 15)
        base -= min(missing_hints * 2, 10)
        return max(0, min(100, base))

    @staticmethod
    def _compute_complexity_score(avg_complexity: float, max_complexity: int,
                                   long_funcs: int, high_complexity: int,
                                   deep_nesting: int, long_params: int) -> float:
        base = 100.0
        if avg_complexity > 3:
            base -= min((avg_complexity - 3) * 5, 25)
        if max_complexity > 15:
            base -= min((max_complexity - 15) * 1.5, 15)
        base -= min(long_funcs * 3, 15)
        base -= min(high_complexity * 4, 15)
        base -= min(deep_nesting * 5, 10)
        base -= min(long_params * 2, 10)
        return max(0, min(100, base))

    @staticmethod
    def _compute_documentation_score(comment_ratio: float, missing_docstrings: int, total_files: int) -> float:
        base = comment_ratio * 100
        base -= min(missing_docstrings * 3, 30)
        return max(0, min(100, base))

    @staticmethod
    def _compute_security_score(hardcoded: int, empty_except: int, broad_except: int, todo_fixme: int) -> float:
        base = 100.0
        base -= min(hardcoded * 12, 30)
        base -= min(empty_except * 15, 30)
        base -= min(broad_except * 8, 20)
        base -= min(todo_fixme * 2, 10)
        return max(0, min(100, base))

    @staticmethod
    def _compute_technical_debt(total_issues: int, long_funcs: int, long_params: int,
                                deep_nesting: int, duplicate_code: int,
                                unused_funcs: int, high_complexity: int) -> float:
        debt = total_issues * 3 + long_funcs * 8 + long_params * 4 + deep_nesting * 6 + duplicate_code * 10 + unused_funcs * 4 + high_complexity * 5
        score = max(0, 100 - debt / max(total_issues + 1, 1) * 2)
        return score

    # ======================================================================
    # Checks builder
    # ======================================================================

    @staticmethod
    def _build_checks(all_issues: list[dict], type_counts: Counter, has_test_files: bool) -> list[dict]:
        check_map = [
            ("long_function", "Long Functions", "medium"),
            ("large_class", "Large Classes", "medium"),
            ("duplicate_code", "Duplicate Code", "medium"),
            ("unused_import", "Unused Imports", "low"),
            ("unused_variable", "Unused Variables", "low"),
            ("unused_function", "Dead/Unused Code", "medium"),
            ("magic_number", "Magic Numbers", "low"),
            ("deep_nesting", "Deep Nesting", "medium"),
            ("excessive_parameters", "Long Parameter Lists", "medium"),
            ("circular_import", "Circular Imports", "high"),
            ("repeated_logic", "Repeated Logic", "medium"),
            ("missing_docstring", "Missing Docstrings", "low"),
            ("empty_exception_block", "Empty Exception Blocks", "high"),
            ("hardcoded_value", "Hardcoded Values", "high"),
            ("poor_naming", "Poor Naming Conventions", "low"),
            ("broad_exception", "Broad Exception Blocks", "high"),
            ("missing_type_hint", "Missing Type Hints", "low"),
            ("excessive_returns", "Excessive Returns", "low"),
            ("high_coupling", "High Coupling", "medium"),
            ("todo_fixme", "TODO/FIXME Comments", "low"),
            ("high_cyclomatic_complexity", "High Cyclomatic Complexity", "high"),
            ("large_file", "Large Files", "medium"),
            ("duplicate_import", "Duplicate Imports", "low"),
        ]

        test_check = ("test_coverage", "Test Coverage", "medium")

        checks = []
        for issue_type, label, default_severity in check_map:
            count = type_counts.get(issue_type, 0)
            matching = [i for i in all_issues if i["type"] == issue_type]
            checks.append({
                "check_name": label,
                "status": "pass" if count == 0 else "fail",
                "severity": default_severity,
                "count": count,
                "issues": matching,
            })

        # test coverage
        if not has_test_files:
            checks.append({
                "check_name": "Test Coverage",
                "status": "fail",
                "severity": "medium",
                "count": 1,
                "issues": [{
                    "type": "test_coverage", "severity": "medium",
                    "description": "No test files detected",
                    "reason": "No test files were found in the workspace.",
                    "suggested_fix": "Add unit tests for core functionality.",
                    "priority": "medium", "affected_file": "", "affected_function": None, "line": None,
                }],
            })
        else:
            checks.append({
                "check_name": "Test Coverage",
                "status": "pass",
                "severity": "medium",
                "count": 0,
                "issues": [],
            })

        return checks

    # ======================================================================
    # Insights generator
    # ======================================================================

    @staticmethod
    def _generate_insights(
        all_issues: list[dict], type_counts: Counter, overall_score: float,
        avg_complexity: float, file_records: list[dict], total_files: int,
        all_complexities: list[int], max_complexity: int, total_loc: int,
        total_comments: int, comment_ratio: float, has_test_files: bool,
        duplicate_hash_keys: list[str],
        total_funcs: int = 0, total_classes: int = 0,
    ) -> list[dict]:
        ins: list[dict] = []
        total_issues = len(all_issues)
        sev_counts = Counter(i["severity"] for i in all_issues)

        # ---- overall quality ----
        if overall_score >= 85:
            ins.append({"message": f"Overall code quality is strong ({overall_score:.0f}/100). Maintain current development practices.", "type": "overall", "sentiment": "positive", "module": None, "files": [], "category": "overall"})
        elif overall_score >= 65:
            ins.append({"message": f"Code quality is acceptable ({overall_score:.0f}/100) with moderate room for improvement.", "type": "overall", "sentiment": "neutral", "module": None, "files": [], "category": "overall"})
        else:
            ins.append({"message": f"Code quality needs significant attention ({overall_score:.0f}/100). Prioritise high-severity and security-related fixes.", "type": "overall", "sentiment": "negative", "module": None, "files": [], "category": "overall"})

        # ---- complexity ----
        if avg_complexity > 8:
            worst = sorted(file_records, key=lambda x: -x["complexity"])[:3]
            ins.append({
                "message": f"Average cyclomatic complexity is high ({avg_complexity:.1f}). {worst[0]['path']} has the highest complexity ({worst[0]['complexity']}).",
                "type": "complexity", "sentiment": "negative", "module": None,
                "files": [f["path"] for f in worst], "category": "complexity",
            })
        elif avg_complexity < 4:
            ins.append({"message": f"Complexity is well-managed (avg {avg_complexity:.1f}). Logic is kept simple across the codebase.", "type": "complexity", "sentiment": "positive", "module": None, "files": [], "category": "complexity"})

        # ---- module-level health ----
        mod_issues: defaultdict[str, list[dict]] = defaultdict(list)
        mod_files: defaultdict[str, set[str]] = defaultdict(set)
        for i in all_issues:
            parts = i["affected_file"].split("/")
            mod = parts[0] if len(parts) > 1 else "(root)"
            mod_issues[mod].append(i)
            mod_files[mod].add(i["affected_file"])

        worst_mods = sorted(mod_issues.items(), key=lambda x: -len(x[1]))[:3]
        for mod, m_issues in worst_mods:
            m_types = [i["type"] for i in m_issues]
            type_detail = []
            if "high_cyclomatic_complexity" in m_types or "long_function" in m_types:
                type_detail.append("complexity or long functions")
            if "missing_docstring" in m_types or "poor_naming" in m_types:
                type_detail.append("readability issues")
            if "hardcoded_value" in m_types or "broad_exception" in m_types:
                type_detail.append("security concerns")
            if "duplicate_code" in m_types:
                type_detail.append("duplication")
            sent = "negative" if len(m_issues) > 5 else "neutral"
            ins.append({
                "message": f"Module '{mod}' has {len(m_issues)} issue(s) — {' and '.join(type_detail)}. Affects {len(mod_files[mod])} file(s)." if type_detail else f"Module '{mod}' has {len(m_issues)} issue(s) across {len(mod_files[mod])} file(s).",
                "type": "module_health", "sentiment": sent, "module": mod,
                "files": sorted(mod_files[mod])[:5], "category": "module",
            })

        # ---- module with zero issues ----
        mod_all_issue_files: set[str] = set(i["affected_file"] for i in all_issues)
        clean_modules: set[str] = set()
        for fr in file_records:
            p = fr["path"]
            if p not in mod_all_issue_files:
                mod = p.split("/")[0] if "/" in p else "(root)"
                clean_modules.add(mod)
        for cm in sorted(clean_modules)[:3]:
            ins.append({
                "message": f"Module '{cm}' has no detected quality issues — clean code practices are being followed.",
                "type": "module_health", "sentiment": "positive", "module": cm, "files": [], "category": "module",
            })

        # ---- architecture & structure ----
        dirs_seen: set[str] = set()
        for fr in file_records:
            d = "/".join(fr["path"].split("/")[:-1]) or "."
            dirs_seen.add(d)
        if len(dirs_seen) > 1:
            ins.append({
                "message": f"Project is organised across {len(dirs_seen)} directories with {total_files} source files.",
                "type": "structure", "sentiment": "positive", "module": None, "files": [], "category": "architecture",
            })
        if total_classes > 0 and total_funcs > 0:
            ratio = total_funcs / max(total_classes, 1)
            if ratio > 10:
                ins.append({
                    "message": f"Function-to-class ratio is {ratio:.0f}:1 ({total_funcs} functions, {total_classes} classes). Consider whether a more object-oriented approach would benefit organisation.",
                    "type": "architecture", "sentiment": "neutral", "module": None, "files": [], "category": "architecture",
                })

        # ---- documentation ----
        missing_doc = type_counts.get("missing_docstring", 0)
        if comment_ratio > 0.2:
            ins.append({"message": f"Documentation is healthy ({comment_ratio*100:.0f}% comment ratio). Code is well-annotated.", "type": "documentation", "sentiment": "positive", "module": None, "files": [], "category": "documentation"})
        elif comment_ratio < 0.05 and total_files > 3:
            mods_missing_doc: set[str] = set()
            for i in all_issues:
                if i["type"] == "missing_docstring":
                    mods_missing_doc.add(i["affected_file"].split("/")[0])
            doc_msg = f"Comment ratio is very low ({comment_ratio*100:.1f}%)."
            if missing_doc > 0:
                doc_msg += f" {missing_doc} function(s) lack docstrings."
            if mods_missing_doc:
                doc_msg += f" Affected modules: {', '.join(sorted(mods_missing_doc)[:3])}."
            ins.append({"message": doc_msg, "type": "documentation", "sentiment": "negative", "module": None, "files": [], "category": "documentation"})

        # ---- duplication ----
        if duplicate_hash_keys:
            ins.append({
                "message": f"Identical content found across {len(duplicate_hash_keys)} group(s). Duplicate files increase maintenance burden.",
                "type": "duplication", "sentiment": "negative", "module": None, "files": [], "category": "duplication",
            })

        # ---- security ----
        high_crit = sev_counts.get("high", 0) + sev_counts.get("critical", 0)
        if high_crit > 0:
            security_files: set[str] = set()
            for i in all_issues:
                if i["severity"] in ("high", "critical"):
                    security_files.add(i["affected_file"])
            ins.append({
                "message": f"Found {high_crit} high/critical-severity issue(s) across {len(security_files)} file(s). Priority attention needed for security and stability.",
                "type": "severity", "sentiment": "negative", "module": None,
                "files": sorted(security_files)[:5], "category": "security",
            })

        # ---- testing ----
        if has_test_files:
            test_files = [fr for fr in file_records if "test" in fr["path"].lower() or "spec" in fr["path"].lower()]
            ins.append({
                "message": f"Test suite detected with {len(test_files)} test file(s). Testing is in place.",
                "type": "testing", "sentiment": "positive", "module": None, "files": [f["path"] for f in test_files[:3]], "category": "testing",
            })

        # ---- clean file highlights ----
        clean = sorted([f for f in file_records if f["issue_count"] == 0], key=lambda x: x["path"])[:3]
        if clean:
            ins.append({
                "message": f"{len(clean)} file(s) have zero issues: {', '.join(f['path'] for f in clean)}. Exemplary code quality.",
                "type": "file_health", "sentiment": "positive", "module": None, "files": [f["path"] for f in clean], "category": "cleanliness",
            })

        # ---- language insight ----
        langs: set[str] = set(f["language"] for f in file_records)
        if len(langs) > 1:
            counts = Counter(f["language"] for f in file_records)
            primary = counts.most_common(1)[0]
            ins.append({
                "message": f"Project uses {len(langs)} language(s). Primary language is {primary[0]} ({primary[1]} files).",
                "type": "language", "sentiment": "neutral", "module": None, "files": [], "category": "language",
            })

        return ins

    # ======================================================================
    # Recommendations generator
    # ======================================================================

    @staticmethod
    def _generate_recommendations(
        all_issues: list[dict], type_counts: Counter,
        file_records: list[dict], overall_score: float,
        avg_complexity: float, readability_score: float,
        security_score: float, tech_debt_score: float,
    ) -> list[dict]:
        recs: list[dict] = []
        seen_actions: set[str] = set()
        total_issues = len(all_issues)

        def add(action: str, impact: str, effort: str, detail: str,
                priority: str = "medium", improvement: str = "",
                files: list[str] | None = None, category: str = "") -> None:
            key = action.lower().strip()
            if key not in seen_actions:
                seen_actions.add(key)
                recs.append({
                    "action": action, "impact": impact, "effort": effort,
                    "detail": detail, "priority": priority,
                    "estimated_improvement": improvement,
                    "affected_file_count": len(files) if files else 0,
                    "affected_files": files or [],
                    "category": category,
                })

        def files_for_type(issue_type: str) -> list[str]:
            return sorted(set(
                i["affected_file"] for i in all_issues if i["type"] == issue_type
            ))

        def count_for_type(issue_type: str) -> int:
            return type_counts.get(issue_type, 0)

        # ======== HIGH PRIORITY ========

        cnt = count_for_type("empty_exception_block")
        if cnt > 0:
            ff = files_for_type("empty_exception_block")
            add(
                f"Fix {cnt} empty exception block(s) that silently swallow errors",
                "high", "low",
                "Replace 'except: pass' with proper error handling or logging. Empty exception blocks hide bugs and make debugging difficult.",
                priority="high", improvement=f"+{min(cnt * 3, 12)}%",
                files=ff, category="error_handling",
            )

        cnt = count_for_type("broad_exception")
        if cnt > 0:
            ff = files_for_type("broad_exception")
            add(
                f"Replace {cnt} broad exception clause(s) with specific exception types",
                "high", "low",
                "Catching Exception or BaseException masks unexpected errors. Specify the exact exception types you expect.",
                priority="high", improvement=f"+{min(cnt * 2, 10)}%",
                files=ff, category="error_handling",
            )

        cnt = count_for_type("hardcoded_value")
        if cnt > 0:
            ff = files_for_type("hardcoded_value")
            add(
                f"Externalise {cnt} hardcoded value(s) to configuration or environment variables",
                "high", "medium",
                "Move URLs, file paths, and credentials to environment variables or config files for flexibility and security.",
                priority="high", improvement=f"+{min(cnt * 4, 15)}%",
                files=ff, category="security",
            )

        cnt = count_for_type("high_cyclomatic_complexity")
        if cnt > 0:
            worst = sorted(
                [f for f in file_records if f["complexity"] > 15],
                key=lambda x: -x["complexity"],
            )[:3]
            ff = [w["path"] for w in worst]
            add(
                f"Reduce cyclomatic complexity in {len(ff)} file(s) with complex logic",
                "high", "medium",
                "Break complex functions into smaller, focused helpers. High complexity makes code hard to test and maintain.",
                priority="high", improvement=f"+{min(cnt * 3, 10)}%",
                files=ff, category="complexity",
            )

        cnt = count_for_type("high_coupling")
        if cnt > 0:
            ff = files_for_type("high_coupling")
            add(
                f"Reduce coupling in {cnt} over-importing file(s) by introducing abstraction layers",
                "high", "high",
                "Files importing more than 15 modules are tightly coupled. Introduce interfaces or split modules to decouple dependencies.",
                priority="high", improvement=f"+{min(cnt * 2, 8)}%",
                files=ff, category="architecture",
            )

        # ======== MEDIUM PRIORITY ========

        cnt = count_for_type("long_function")
        if cnt > 0:
            ff = files_for_type("long_function")
            add(
                f"Refactor {cnt} long function(s) exceeding 60 lines into smaller helpers",
                "medium", "medium",
                "Functions over 60 lines become hard to understand and test. Extract logical blocks into well-named helper functions.",
                priority="medium", improvement=f"+{min(cnt * 2, 8)}%",
                files=ff, category="maintainability",
            )

        cnt = count_for_type("duplicate_code")
        if cnt > 0:
            ff = files_for_type("duplicate_code")
            add(
                f"Remove {cnt} duplicate file(s) by consolidating identical content",
                "medium", "medium",
                "Identical files increase maintenance burden. Remove duplicates and import from the canonical location.",
                priority="medium", improvement=f"+{min(cnt * 3, 10)}%",
                files=ff, category="duplication",
            )

        cnt = count_for_type("deep_nesting")
        if cnt > 0:
            ff = files_for_type("deep_nesting")
            add(
                f"Flatten {cnt} deeply nested block(s) using guard clauses and early returns",
                "medium", "medium",
                "Nesting beyond 4 levels reduces readability. Use early returns, guard clauses, and extracted helper functions.",
                priority="medium", improvement=f"+{min(cnt * 2, 6)}%",
                files=ff, category="readability",
            )

        cnt = count_for_type("large_class")
        if cnt > 0:
            ff = files_for_type("large_class")
            add(
                f"Split {cnt} large class(es) into smaller single-responsibility classes",
                "medium", "high",
                "Large classes with many methods violate the Single Responsibility Principle. Extract related behaviour into separate classes.",
                priority="medium", improvement=f"+{min(cnt * 3, 8)}%",
                files=ff, category="architecture",
            )

        cnt = count_for_type("unused_function")
        if cnt > 0:
            ff = files_for_type("unused_function")
            add(
                f"Remove {cnt} unused function(s) or add callers to eliminate dead code",
                "medium", "low",
                "Unused functions clutter the codebase and may indicate incomplete refactoring. Remove them or add callers.",
                priority="medium", improvement=f"+{min(cnt * 1, 5)}%",
                files=ff, category="maintainability",
            )

        cnt = count_for_type("excessive_parameters")
        if cnt > 0:
            ff = files_for_type("excessive_parameters")
            add(
                f"Simplify {cnt} function(s) with more than 5 parameters using a configuration object",
                "medium", "medium",
                "Long parameter lists make functions hard to call and test. Consolidate related parameters into a single data object.",
                priority="medium", improvement=f"+{min(cnt * 2, 5)}%",
                files=ff, category="readability",
            )

        # ======== LOW PRIORITY ========

        cnt = count_for_type("missing_docstring")
        if cnt > 0:
            ff = files_for_type("missing_docstring")
            add(
                f"Add documentation to {cnt} function(s) and classes missing docstrings",
                "low", "medium",
                "Documenting public functions and classes improves maintainability and makes the codebase more accessible to new contributors.",
                priority="low", improvement=f"+{min(cnt * 1, 8)}%",
                files=ff, category="documentation",
            )

        cnt = count_for_type("missing_type_hint")
        if cnt > 0:
            ff = files_for_type("missing_type_hint")
            add(
                f"Add type hints to {cnt} function(s) for improved readability and static analysis",
                "low", "low",
                "Type annotations improve code readability and enable static type checking with mypy or pyright.",
                priority="low", improvement=f"+{min(cnt * 1, 5)}%",
                files=ff, category="readability",
            )

        cnt = count_for_type("magic_number")
        if cnt > 0:
            ff = files_for_type("magic_number")
            add(
                f"Replace {cnt} magic number(s) with named constants",
                "low", "low",
                "Raw numeric literals (other than 0, 1, 100) should be defined as named constants to convey meaning.",
                priority="low", improvement=f"+{min(cnt * 1, 3)}%",
                files=ff, category="readability",
            )

        cnt = count_for_type("poor_naming")
        if cnt > 0:
            ff = files_for_type("poor_naming")
            add(
                f"Rename {cnt} poorly named variable(s) to descriptive names",
                "low", "low",
                "Short or ambiguous names reduce code readability. Use names that convey the purpose of the variable.",
                priority="low", improvement=f"+{min(cnt * 1, 3)}%",
                files=ff, category="readability",
            )

        cnt = count_for_type("todo_fixme")
        if cnt > 0:
            ff = files_for_type("todo_fixme")
            add(
                f"Resolve {cnt} TODO/FIXME comment(s) or link them to tracking issues",
                "low", "low",
                "Incomplete work items should be addressed or tracked in your issue tracker. Reference the issue number in the comment.",
                priority="low", improvement=f"+{min(cnt * 1, 3)}%",
                files=ff, category="maintainability",
            )

        cnt = count_for_type("excessive_returns")
        if cnt > 0:
            ff = files_for_type("excessive_returns")
            add(
                f"Simplify {cnt} function(s) with many return statements using a single exit point",
                "low", "low",
                "Multiple return points can make control flow confusing. Consider using a result variable with a single return.",
                priority="low", improvement=f"+{min(cnt * 1, 3)}%",
                files=ff, category="readability",
            )

        cnt = count_for_type("large_file")
        if cnt > 0:
            ff = files_for_type("large_file")
            add(
                f"Split {cnt} large file(s) exceeding 500 lines into smaller modules",
                "low", "high",
                "Large files are hard to navigate and maintain. Divide them into smaller, focused modules with clear responsibilities.",
                priority="low", improvement=f"+{min(cnt * 2, 5)}%",
                files=ff, category="maintainability",
            )

        cnt = count_for_type("duplicate_import")
        if cnt > 0:
            ff = files_for_type("duplicate_import")
            add(
                f"Remove {cnt} duplicate import(s) from affected files",
                "low", "low",
                "Importing the same module multiple times in one file is unnecessary. Keep one import statement per module at the top.",
                priority="low", improvement="+1%",
                files=ff, category="readability",
            )

        if not recs:
            add(
                "Maintain current code quality practices with continued code reviews and testing",
                "low", "low",
                "No significant issues found. Continue code reviews, automated testing, and adherence to coding standards.",
                priority="low", improvement="+0%",
                files=[], category="general",
            )

        # Sort: high first, then medium, then low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recs.sort(key=lambda r: priority_order.get(r["priority"], 99))
        return recs

    # ======================================================================
    # AI Summary generator
    # ======================================================================

    @staticmethod
    def _generate_ai_summary(
        overall_score: float,
        maintainability_score: float,
        readability_score: float,
        complexity_score: float,
        documentation_score: float,
        security_score: float,
        technical_debt_score: float,
        avg_complexity: float,
        max_complexity: int,
        total_files: int,
        total_issues: int,
        total_loc: int,
        total_comments: int,
        comment_ratio: float,
        has_test_files: bool,
        duplicate_groups: list[str],
        file_records: list[dict],
        type_counts: Counter,
    ) -> dict:
        parts: list[str] = []

        # Architecture assessment
        dirs: set[str] = set()
        for fr in file_records:
            d = "/".join(fr["path"].split("/")[:-1]) or "."
            dirs.add(d)
        if len(dirs) <= 3 and total_files > 5:
            parts.append("well-organised directory structure")
        elif len(dirs) > 10:
            parts.append("deep directory hierarchy")

        # Complexity
        if avg_complexity < 4:
            parts.append("low cyclomatic complexity")
        elif avg_complexity > 8:
            parts.append("elevated complexity needing attention")

        # Readability
        missing_doc = type_counts.get("missing_docstring", 0)
        poor_names = type_counts.get("poor_naming", 0)
        magic_nums = type_counts.get("magic_number", 0)
        readability_flaws = missing_doc + poor_names + magic_nums
        if readability_flaws == 0 and total_files > 3:
            parts.append("clean readable code")
        elif readability_flaws > total_files * 2:
            parts.append("readability concerns from undocumented or poorly-named code")
        else:
            parts.append("generally readable code")

        # Security
        hardcoded = type_counts.get("hardcoded_value", 0)
        broad_except = type_counts.get("broad_exception", 0)
        empty_except = type_counts.get("empty_exception_block", 0)
        security_bugs = hardcoded + broad_except + empty_except
        if security_bugs == 0:
            parts.append("no critical security gaps detected")
        elif security_bugs > 5:
            parts.append("security improvements recommended")

        # Testing
        if has_test_files:
            parts.append("includes test coverage")

        # Duplication
        if not duplicate_groups:
            parts.append("no file duplication detected")

        # Documentation
        if comment_ratio > 0.15:
            parts.append("adequate documentation")
        elif comment_ratio < 0.03 and total_files > 5:
            parts.append("sparse documentation")

        # Scores summary
        low_scores = []
        if maintainability_score < 60:
            low_scores.append("maintainability")
        if readability_score < 60:
            low_scores.append("readability")
        if security_score < 60:
            low_scores.append("security")
        if technical_debt_score < 60:
            low_scores.append("technical debt")

        summary = f"The project scores {overall_score:.0f}/100 overall with "
        if parts:
            summary += ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1] + ". "
        else:
            summary += "typical code quality characteristics. "
        if low_scores:
            summary += f"Areas needing improvement: {', '.join(low_scores)}. "

        # Strengths
        strengths = []
        if overall_score >= 75:
            strengths.append("Strong overall code quality score")
        if avg_complexity < 4:
            strengths.append(f"Low average complexity ({avg_complexity:.1f})")
        if not duplicate_groups:
            strengths.append("No duplicate files")
        if has_test_files:
            strengths.append("Test suite present")
        if comment_ratio > 0.15:
            strengths.append("Good documentation coverage")
        if security_bugs == 0:
            strengths.append("No security vulnerabilities detected")
        if not strengths:
            strengths.append("Codebase is functional and structured")

        # Weaknesses
        weaknesses = []
        if total_issues > 50:
            weaknesses.append(f"High issue count ({total_issues} total)")
        if avg_complexity > 8:
            weaknesses.append("High average cyclomatic complexity")
        if missing_doc > 5:
            weaknesses.append(f"{missing_doc} functions lack documentation")
        if security_bugs > 5:
            weaknesses.append("Security improvements recommended")
        if duplicate_groups:
            weaknesses.append(f"Duplicate code in {len(duplicate_groups)} group(s)")
        if not has_test_files:
            weaknesses.append("No test suite detected")
        if comment_ratio < 0.03:
            weaknesses.append("Very low comment ratio")
        if not weaknesses:
            weaknesses.append("No significant weaknesses identified")

        # Architecture label
        arch_label = "Modular"
        if len(dirs) <= 3:
            arch_label = "Flat/Simple"
        elif len(dirs) > 10:
            arch_label = "Deeply nested"

        # Recommended focus
        focus_areas = []
        if security_bugs > 0:
            focus_areas.append("security hardening")
        if missing_doc > 5:
            focus_areas.append("documentation coverage")
        if avg_complexity > 6:
            focus_areas.append("complexity reduction")
        if duplicate_groups:
            focus_areas.append("duplication elimination")
        if not has_test_files:
            focus_areas.append("test implementation")
        recommended_focus = ", ".join(focus_areas) if focus_areas else "maintaining current quality levels"

        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "architecture": arch_label,
            "recommended_focus": recommended_focus,
        }

    # ======================================================================
    # Language breakdown
    # ======================================================================

    @staticmethod
    def _build_language_breakdown(file_records: list[dict]) -> list[dict]:
        by: dict[str, dict] = {}
        for f in file_records:
            lang = f["language"]
            if lang not in by:
                by[lang] = {"language": lang, "file_count": 0, "issue_count": 0, "total_complexity": 0, "file_count_for_avg": 0}
            by[lang]["file_count"] += 1
            by[lang]["issue_count"] += f["issue_count"]
            by[lang]["total_complexity"] += f["complexity"]
            by[lang]["file_count_for_avg"] += 1
        result = []
        for lang, info in by.items():
            result.append({
                "language": lang,
                "file_count": info["file_count"],
                "issue_count": info["issue_count"],
                "avg_complexity": round(info["total_complexity"] / max(info["file_count_for_avg"], 1), 1),
            })
        result.sort(key=lambda x: -x["file_count"])
        return result
