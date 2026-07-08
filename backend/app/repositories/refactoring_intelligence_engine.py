import os
import re
from pathlib import Path
from typing import Any


REPEATED_LOGIC_PATTERN = re.compile(
    r'(validate|check|verify|assert|ensure)\w*\s*\(.*?\)[\s\S]{0,200}'
    r'(validate|check|verify|assert|ensure)\w*\s*\(',
    re.DOTALL,
)

REPEATED_DB_PATTERN = re.compile(
    r'(db|database|query|sql|session)\.[\s\S]{0,200}'
    r'(db|database|query|sql|session)\.',
    re.DOTALL,
)

REPEATED_BUSINESS_PATTERN = re.compile(
    r'(calculate|compute|transform|process|map|convert)\w*\s*\([\s\S]{0,200}'
    r'(calculate|compute|transform|process|map|convert)\w*\s*\(',
    re.DOTALL,
)

LAYER_SEPARATION_PATTERN = re.compile(
    r'(controller|route|endpoint)\s*\(?[\s\S]{0,300}(db|repository|model)\s*\.',
    re.DOTALL,
)


class RefactoringIntelligenceEngine:

    def analyze(self, workspace_path: Path | None = None,
                project_analysis: dict | None = None,
                code_intel: dict | None = None,
                code_quality: dict | None = None,
                file_analysis: dict | None = None,
                func_class: dict | None = None,
                dep_analysis: dict | None = None,
                call_graph: dict | None = None,
                semantic: dict | None = None,
                config_intel: dict | None = None,
                recommendations: dict | None = None) -> dict:
        opportunities = self._detect_all(
            workspace_path, code_intel, code_quality,
            file_analysis, func_class, dep_analysis,
            call_graph, semantic, config_intel, recommendations,
        )
        score = self._compute_score(opportunities)
        summary = self._generate_summary(opportunities, score)
        return {
            "refactoring_score": score,
            "opportunities": opportunities,
            "summary": summary,
        }

    def _get_source_files(self, workspace_path, code_intel) -> dict[str, str]:
        files: dict[str, str] = {}
        if code_intel and isinstance(code_intel, dict):
            raw = code_intel.get("files", code_intel.get("raw_files", []))
            if isinstance(raw, list):
                for f in raw:
                    path = f.get("path", f.get("file", ""))
                    content = f.get("content", f.get("source", ""))
                    if path and content:
                        files[path] = content
        if workspace_path and not files:
            for root, _, filenames in os.walk(workspace_path):
                for fn in filenames:
                    if any(fn.endswith(ext) for ext in
                           (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php")):
                        fpath = os.path.join(root, fn)
                        try:
                            with open(fpath, "r", errors="ignore") as fh:
                                files[fpath] = fh.read()
                        except Exception:
                            pass
        return files

    def _detect_all(self, workspace_path, code_intel, code_quality,
                    file_analysis, func_class, dep_analysis,
                    call_graph, semantic, config_intel,
                    recommendations) -> list[dict]:
        opps: list[dict] = []

        self._detect_large_classes(func_class, opps)
        self._detect_god_classes(func_class, opps)
        self._detect_large_functions(func_class, opps)
        self._detect_long_parameters(func_class, opps)
        self._detect_god_functions(func_class, opps)
        self._detect_duplication(code_quality, opps)
        self._detect_dead_code(func_class, call_graph, opps)
        self._detect_circular_dependencies(dep_analysis, opps)
        self._detect_high_coupling(semantic, dep_analysis, opps)
        self._detect_low_cohesion(semantic, dep_analysis, opps)
        self._detect_deep_nesting(workspace_path, code_intel, opps)
        self._detect_repeated_logic(workspace_path, code_intel, opps)
        self._detect_repeated_db_logic(workspace_path, code_intel, opps)
        self._detect_repeated_business_logic(workspace_path, code_intel, opps)
        self._detect_layer_violations(workspace_path, code_intel, opps)
        self._detect_architecture_violations(file_analysis, dep_analysis, opps)
        self._detect_poor_naming(workspace_path, code_intel, opps)

        opps.sort(key=lambda o: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(o.get("severity", "low"), 5))
        return opps

    def _detect_large_classes(self, func_class, opps):
        if not func_class:
            return
        classes = func_class.get("classes", [])
        if isinstance(classes, list):
            for cls in classes:
                name = cls.get("name", "")
                file = cls.get("file", "")
                methods = cls.get("methods", [])
                if len(methods) > 20:
                    aff_fns = [m.get("name", "") for m in (methods if isinstance(methods, list) else [])[:5]]
                    opps.append(self._make_opp(
                        f"Extract Class from {name}", "extract-class", "high",
                        [file], aff_fns, [name],
                        f"Class {name} has {len(methods)} methods — split into focused classes",
                        f"Responsibility overload detected — {name} handles too many concerns",
                        f"Extract related method groups into separate classes. "
                        f"Split {name} into smaller classes with single responsibilities",
                        [name], ["Extract class", "Reduce coupling", "Improve cohesion"],
                        f"~{len(methods) // 4}h", f"Complexity reduction: 40-60%",
                        f"Maintainability +15-25 pts", "medium",
                    ))

    def _detect_god_classes(self, func_class, opps):
        if not func_class:
            return
        classes = func_class.get("classes", [])
        if isinstance(classes, list):
            for cls in classes:
                name = cls.get("name", "")
                file = cls.get("file", "")
                methods = cls.get("methods", [])
                cls_lines = cls.get("end_line", 0) - cls.get("start_line", 0)
                if len(methods) > 25 or cls_lines > 500:
                    opps.append(self._make_opp(
                        f"Decompose God Class {name}", "split-service", "critical",
                        [file], [m.get("name", "") for m in (methods if isinstance(methods, list) else [])[:5]],
                        [name],
                        f"God Class {name} spans ~{cls_lines} lines with {len(methods)} methods",
                        f"Violates Single Responsibility — one class controlling many business flows",
                        f"Use Extract Class + Facade patterns to decompose into ~{max(len(methods)//5, 2)}"
                        f" focused classes by domain concern",
                        [name], ["Split service", "Extract class", "Apply facade"],
                        f"~{cls_lines // 10}h", f"Complexity reduction: 50-70%",
                        f"Maintainability +20-35 pts", "critical",
                    ))

    def _detect_large_functions(self, func_class, opps):
        if not func_class:
            return
        functions = func_class.get("functions", [])
        if isinstance(functions, list):
            for fn in functions:
                name = fn.get("name", "")
                file = fn.get("file", "")
                lines = fn.get("end_line", 0) - fn.get("start_line", 0)
                if lines > 60:
                    opps.append(self._make_opp(
                        f"Extract Method from {name}", "extract-method", "high",
                        [file], [name], [],
                        f"Function {name} spans {lines} lines — extract smaller methods",
                        f"High cognitive load — function does multiple things",
                        f"Break {name} into ~{max(lines // 20, 2)} smaller functions "
                        f"of 15-20 lines each, each with a single responsibility",
                        [name], ["Extract method", "Reduce complexity"],
                        f"~{lines // 8}h", f"Complexity reduction: 30-50%",
                        f"Readability +10-20 pts", "high",
                    ))

    def _detect_god_functions(self, func_class, opps):
        if not func_class:
            return
        functions = func_class.get("functions", [])
        if isinstance(functions, list):
            for fn in functions:
                name = fn.get("name", "")
                file = fn.get("file", "")
                params_raw = fn.get("parameters", fn.get("params", []))
                num_params = len(params_raw) if isinstance(params_raw, (list, tuple)) else 0
                lines = fn.get("end_line", 0) - fn.get("start_line", 0)
                if lines > 100:
                    opps.append(self._make_opp(
                        f"Split God Function {name}", "split-controller", "critical",
                        [file], [name], [],
                        f"God Function {name} spans {lines} lines — violates SRP",
                        f"Doing too much — contains multiple business logic paths",
                        f"Decompose {name} into a coordinating function that delegates "
                        f"to ~{max(lines // 20, 3)} focused helper functions",
                        [name], ["Split function", "Extract method", "Introduce delegation"],
                        f"~{lines // 6}h", f"Complexity reduction: 40-60%",
                        f"Testability +25-40 pts", "critical",
                    ))

    def _detect_long_parameters(self, func_class, opps):
        if not func_class:
            return
        functions = func_class.get("functions", [])
        if isinstance(functions, list):
            for fn in functions:
                name = fn.get("name", "")
                file = fn.get("file", "")
                params_raw = fn.get("parameters", fn.get("params", []))
                num_params = len(params_raw) if isinstance(params_raw, (list, tuple)) else 0
                if num_params > 6:
                    opps.append(self._make_opp(
                        f"Introduce Parameter Object for {name}", "extract-interface", "medium",
                        [file], [name], [],
                        f"Function has {num_params} parameters — use parameter object pattern",
                        f"Long parameter lists indicate poor abstraction boundaries",
                        f"Group related parameters into a dataclass/config object. "
                        f"Use Builder pattern for optional parameters",
                        [name], ["Introduce parameter object", "Reduce coupling"],
                        f"~{num_params // 2}h", f"Complexity reduction: 10-20%",
                        f"Readability +5-10 pts", "medium",
                    ))

    def _detect_duplication(self, code_quality, opps):
        if not code_quality or not isinstance(code_quality, dict):
            return
        issues = code_quality.get("issues", [])
        if isinstance(issues, list):
            dup = [i for i in issues if isinstance(i, dict) and
                   i.get("type", "") in ("duplicate", "redundant", "repeated")]
            if dup:
                aff_files = set()
                for i in dup:
                    for f in (i.get("files", []) if isinstance(i, dict) else []):
                        aff_files.add(f)
                opps.append(self._make_opp(
                    "Merge Duplicate Logic", "merge-duplicate", "high",
                    list(aff_files)[:8], [], [],
                    f"Found {len(dup)} duplicated code blocks across {len(aff_files)} file(s)",
                    f"Duplication increases maintenance cost and inconsistency risk",
                    f"Extract shared logic into reusable utility module. "
                    f"Apply DRY principle: one authoritative implementation",
                    [], ["Merge duplicate", "Extract utility", "Apply DRY"],
                    f"~{len(dup) * 2}h", f"Duplication reduction: 60-80%",
                    f"Maintainability +10-15 pts", "high",
                ))

        duplications = code_quality.get("duplications", code_quality.get("duplicates", []))
        if isinstance(duplications, list) and duplications:
            aff = [d if isinstance(d, str) else d.get("file", "") for d in duplications[:5]]
            opps.append(self._make_opp(
                "Consolidate Repeated Code Blocks", "merge-duplicate", "medium",
                aff, [], [],
                f"Code duplication detected in {len(duplications)} location(s)",
                f"Repeated patterns increase cognitive load and error risk",
                f"Centralize repeated logic into a shared module or base class",
                [], ["Consolidate", "Extract utility", "Reduce redundancy"],
                f"~{len(duplications)}h", f"Duplication reduction: 50-70%",
                f"Maintainability +5-10 pts", "medium",
            ))

    def _detect_dead_code(self, func_class, call_graph, opps):
        if not func_class or not call_graph:
            return
        all_functions = func_class.get("functions", [])
        called: set[str] = set()
        nodes = call_graph.get("nodes", [])
        if isinstance(nodes, list):
            for n in nodes:
                called.add(n.get("name", n.get("label", "")))

        unused = []
        for fn in (all_functions if isinstance(all_functions, list) else []):
            fname = fn.get("name", "")
            if fname and fname not in called:
                unused.append(fn)

        if unused:
            aff_files = list({fn.get("file", "") for fn in unused})
            aff_fns = [fn.get("name", "") for fn in unused[:8]]
            opps.append(self._make_opp(
                f"Remove Dead Code ({len(unused)} functions)", "remove-dead-code", "medium",
                aff_files, aff_fns, [],
                f"Found {len(unused)} function(s) never called — candidates for removal",
                f"Dead code increases maintenance burden and confusion",
                f"Review and remove unused functions. If they are public API, "
                f"mark them as deprecated first",
                [], ["Remove dead code", "Clean up exports"],
                f"~{len(unused) // 2}h", f"Codebase size reduction: ~{len(unused) * 20} lines",
                f"Maintainability +3-5 pts", "medium",
            ))

    def _detect_circular_dependencies(self, dep_analysis, opps):
        if not dep_analysis or not isinstance(dep_analysis, dict):
            return
        circular = dep_analysis.get("circular_dependencies", [])
        if isinstance(circular, list) and circular:
            opps.append(self._make_opp(
                f"Break {len(circular)} Circular Dependenc{'y' if len(circular)==1 else 'ies'}",
                "reduce-coupling", "critical",
                [str(c) for c in circular[:5]], [], [],
                f"Found {len(circular)} circular dependency chain(s) making refactoring risky",
                f"Circular dependencies prevent independent module testing and evolution",
                f"Break cycles by: extracting shared interfaces, "
                f"introducing event-driven communication, or using dependency inversion",
                [], ["Break circular dep", "Introduce interface", "Apply DIP"],
                f"~{len(circular) * 4}h", f"Complexity reduction: 30-40%",
                f"Architecture +20-30 pts", "critical",
            ))

    def _detect_high_coupling(self, semantic, dep_analysis, opps):
        files_with_high_coupling = []
        if dep_analysis and isinstance(dep_analysis, dict):
            deps_files = dep_analysis.get("files", [])
            if isinstance(deps_files, list):
                for f in deps_files:
                    if isinstance(f, dict):
                        cs = f.get("coupling_score", f.get("afferent_coupling", 0))
                        if isinstance(cs, (int, float)) and cs > 0.7:
                            files_with_high_coupling.append(f.get("name", f.get("file", "")))

        if semantic and isinstance(semantic, dict):
            score = semantic.get("understanding_score", {})
            if isinstance(score, dict):
                cs = score.get("coupling", score.get("dependency_score", 0))
                if isinstance(cs, (int, float)) and cs > 0.7 and not files_with_high_coupling:
                    files_with_high_coupling.append("major module")

        if files_with_high_coupling:
            opps.append(self._make_opp(
                "Reduce Coupling Across Modules", "reduce-coupling", "high",
                files_with_high_coupling[:5], [], [],
                f"High coupling detected in {len(files_with_high_coupling)} module(s)",
                f"Tight coupling makes changes risky and testing difficult",
                f"Introduce interfaces, facades, or adapter patterns between coupled modules. "
                f"Apply Dependency Inversion Principle",
                [], ["Reduce coupling", "Introduce interface", "Apply facade"],
                f"~{len(files_with_high_coupling) * 3}h",
                f"Complexity reduction: 20-30%",
                f"Testability +15-25 pts", "high",
            ))

    def _detect_low_cohesion(self, semantic, dep_analysis, opps):
        low_cohesion_files = []
        if dep_analysis and isinstance(dep_analysis, dict):
            deps_files = dep_analysis.get("files", [])
            if isinstance(deps_files, list):
                for f in deps_files:
                    if isinstance(f, dict):
                        ch = f.get("cohesion_score", f.get("cohesion", 0))
                        if isinstance(ch, (int, float)) and 0 < ch < 0.4:
                            low_cohesion_files.append(f.get("name", f.get("file", "")))

        if semantic and isinstance(semantic, dict):
            score = semantic.get("understanding_score", {})
            if isinstance(score, dict):
                ch = score.get("cohesion", 0)
                if isinstance(ch, (int, float)) and 0 < ch < 0.4 and not low_cohesion_files:
                    low_cohesion_files.append("core modules")

        if low_cohesion_files:
            opps.append(self._make_opp(
                "Increase Cohesion — Split Unrelated Responsibilities", "increase-cohesion", "high",
                low_cohesion_files[:5], [], [],
                f"Low cohesion detected in {len(low_cohesion_files)} file(s)",
                f"Modules with unrelated responsibilities are harder to understand and maintain",
                f"Split low-cohesion modules into focused units. "
                f"Group related functions/classes by domain concern",
                [], ["Increase cohesion", "Split module", "Reorganize by concern"],
                f"~{len(low_cohesion_files) * 2}h",
                f"Complexity reduction: 15-25%",
                f"Maintainability +10-20 pts", "high",
            ))

    def _detect_deep_nesting(self, workspace_path, code_intel, opps):
        files = self._get_source_files(workspace_path, code_intel)
        deep_pattern = re.compile(
            r'(for\s+\w+|while\s+[^:]+|if\s+[^:]+)[\s\S]{0,200}?'
            r'(for\s+\w+|while\s+[^:]+|if\s+[^:]+)[\s\S]{0,200}?'
            r'(for\s+\w+|while\s+[^:]+|if\s+[^:]+)[\s\S]{0,200}?'
            r'(for\s+\w+|while\s+[^:]+|if\s+[^:]+)',
            re.DOTALL,
        )
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            matches = deep_pattern.findall(content)
            if matches:
                opps.append(self._make_opp(
                    f"Simplify Deep Nesting in {os.path.basename(rel)}", "extract-method", "medium",
                    [rel], [], [],
                    f"Found {len(matches)} deeply nested blocks (4+ levels) in {os.path.basename(rel)}",
                    f"Deep nesting makes code hard to read, test, and debug",
                    f"Extract nested blocks into named functions. "
                    f"Use early returns, guard clauses, and flat structures",
                    [], ["Extract method", "Apply guard clauses", "Reduce nesting"],
                    f"~{len(matches)}h", f"Complexity reduction: 20-35%",
                    f"Readability +10-15 pts", "medium",
                ))
                break

    def _detect_repeated_logic(self, workspace_path, code_intel, opps):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            matches = REPEATED_LOGIC_PATTERN.findall(content)
            if len(matches) > 2:
                opps.append(self._make_opp(
                    f"Centralize Repeated Validation in {os.path.basename(rel)}",
                    "merge-duplicate", "medium",
                    [rel], [], [],
                    f"Repeated validation logic in {os.path.basename(rel)}",
                    f"Duplicated validation checks scattered across the file",
                    f"Extract validation logic into a shared validator class or utility. "
                    f"Use a validation library or decorator pattern",
                    [], ["Merge duplicate", "Extract utility", "Apply DRY"],
                    f"~{len(matches)}h", f"Duplication reduction: 60-70%",
                    f"Consistency +10-15 pts", "medium",
                ))
                break

    def _detect_repeated_db_logic(self, workspace_path, code_intel, opps):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            matches = REPEATED_DB_PATTERN.findall(content)
            if len(matches) > 2:
                opps.append(self._make_opp(
                    f"Centralize Database Access in {os.path.basename(rel)}",
                    "merge-duplicate", "high",
                    [rel], [], [],
                    f"Repeated database logic in {os.path.basename(rel)} — scattered queries",
                    f"Database access mixed with business logic — violates separation of concerns",
                    f"Extract DB access into a repository/data access layer. "
                    f"Use centralized query builders or ORM patterns",
                    [], ["Extract repository", "Apply repository pattern", "Centralize DB access"],
                    f"~{len(matches) * 2}h", f"Complexity reduction: 20-30%",
                    f"Maintainability +10-15 pts", "high",
                ))
                break

    def _detect_repeated_business_logic(self, workspace_path, code_intel, opps):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            matches = REPEATED_BUSINESS_PATTERN.findall(content)
            if len(matches) > 2:
                opps.append(self._make_opp(
                    f"Centralize Business Logic in {os.path.basename(rel)}",
                    "merge-duplicate", "high",
                    [rel], [], [],
                    f"Repeated business logic in {os.path.basename(rel)} — scattered computations",
                    f"Business rules duplicated across functions — high inconsistency risk",
                    f"Extract business rules into a dedicated service/domain layer. "
                    f"Apply Strategy pattern for variant behaviors",
                    [], ["Extract service", "Apply strategy pattern", "Centralize business logic"],
                    f"~{len(matches) * 2}h", f"Duplication reduction: 50-70%",
                    f"Consistency +15-20 pts", "high",
                ))
                break

    def _detect_layer_violations(self, workspace_path, code_intel, opps):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            matches = LAYER_SEPARATION_PATTERN.findall(content)
            if matches:
                opps.append(self._make_opp(
                    f"Fix Layer Separation in {os.path.basename(rel)}",
                    "split-controller", "high",
                    [rel], [], [],
                    f"Controllers directly accessing persistence in {os.path.basename(rel)}",
                    f"Mixing controller/presentation logic with data access",
                    f"Introduce a service layer between controllers and repositories. "
                    f"Keep controllers thin — only handle HTTP concerns",
                    [], ["Split controller", "Introduce service layer", "Apply layering"],
                    f"~{len(matches) * 2}h", f"Complexity reduction: 15-25%",
                    f"Architecture +15-20 pts", "high",
                ))
                break

    def _detect_architecture_violations(self, file_analysis, dep_analysis, opps):
        violations = []
        if dep_analysis and isinstance(dep_analysis, dict):
            circular = dep_analysis.get("circular_dependencies", [])
            if isinstance(circular, list):
                violations.extend(f"Circular: {c}" for c in circular[:5])

        if file_analysis:
            items = file_analysis if isinstance(file_analysis, list) else file_analysis.get("files", [])
            if isinstance(items, list):
                large = [f.get("name", "") for f in items if isinstance(f, dict)
                         and isinstance(f.get("lines"), (int, float)) and f["lines"] > 800]
                if len(large) > 1:
                    violations.append(f"{len(large)} files > 800 lines")

        if violations:
            opps.append(self._make_opp(
                f"Resolve {len(violations)} Architecture Violation(s)", "split-module", "critical",
                [v for v in violations], [], [],
                f"Architecture violations detected: {'; '.join(violations[:3])}",
                f"Architecture erosion increases technical debt and reduces agility",
                f"Refactor toward clean architecture: split large modules, "
                f"break cycles, and enforce layering via tooling",
                [], ["Split module", "Apply arch rules", "Restructure"],
                f"~{len(violations) * 3}h", f"Complexity reduction: 25-35%",
                f"Architecture +20-30 pts", "critical",
            ))

    def _detect_poor_naming(self, workspace_path, code_intel, opps):
        poor_pattern = re.compile(
            r'\b(temp\d*|data\d*|val\d*|obj\d*|item\d*|thing\d*|stuff\d*|var\d*|result\d*|test\d*|t\d+)\b',
        )
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            matches = poor_pattern.findall(content)
            if len(matches) > 5:
                opps.append(self._make_opp(
                    f"Rename {len(matches)} Poor Identifiers in {os.path.basename(rel)}",
                    "rename-identifier", "low",
                    [rel], [], [],
                    f"Found {len(matches)} poorly named variables (temp, data, val...) — hurts readability",
                    f"Poor naming increases cognitive load and code review time",
                    f"Replace vague names with domain-meaningful identifiers. "
                    f"Follow naming conventions per language (snake_case, camelCase, etc.)",
                    [], ["Rename identifier", "Improve naming convention"],
                    f"~{len(matches) // 2}h", f"Readability improvement: 10-15%",
                    f"Readability +5-10 pts", "low",
                ))
                break

    def _make_opp(self, name: str, opp_type: str, severity: str = "medium",
                  files: list[str] | None = None,
                  functions: list[str] | None = None,
                  classes: list[str] | None = None,
                  description: str = "", reason: str = "",
                  recommendation: str = "",
                  related_classes: list[str] | None = None,
                  roadmap: list[str] | None = None,
                  effort: str = "", comp_reduction: str = "",
                  maint_improvement: str = "", risk: str = "medium") -> dict:
        return {
            "name": name,
            "type": opp_type,
            "severity": severity,
            "affected_files": files or [],
            "affected_functions": functions or [],
            "affected_classes": classes or [],
            "description": description,
            "reason": reason,
            "recommendation": recommendation,
            "impact": {
                "estimated_files_changed": len(files or []),
                "estimated_complexity_reduction": comp_reduction,
                "estimated_maintainability_improvement": maint_improvement,
                "estimated_risk": risk,
            },
            "expected_benefit": (
                f"{comp_reduction}, {maint_improvement}, Risk: {risk}"
            ),
        }

    def _compute_score(self, opportunities) -> dict:
        total = len(opportunities)
        sev_weights = {"critical": 10, "high": 7, "medium": 4, "low": 2}
        weighted = sum(sev_weights.get(o.get("severity", "low"), 1) for o in opportunities)
        max_possible = total * 10 if total > 0 else 1
        raw = min(weighted / max_possible * 100, 100) if total > 0 else 0

        refactoring_score = round(max(0, 100 - raw * 1.2), 1)
        cleanliness = round(max(0, 100 - raw * 0.8), 1)
        code_org = round(max(0, 100 - raw * 0.9), 1)
        debt_red = round(min(raw * 1.5, 100), 1)
        readiness = round(max(0, 100 - raw * 0.7), 1)
        confidence = round(min(total * 4, 90), 1)

        if raw >= 50:
            level = "critical"
        elif raw >= 35:
            level = "high"
        elif raw >= 20:
            level = "medium"
        elif raw >= 8:
            level = "low"
        else:
            level = "informational"

        return {
            "refactoring_score": refactoring_score,
            "project_cleanliness": cleanliness,
            "code_organization": code_org,
            "debt_reduction_potential": debt_red,
            "refactoring_readiness": readiness,
            "ai_confidence": confidence,
            "risk_level": level,
        }

    def _generate_summary(self, opportunities, score) -> dict:
        critical = [o for o in opportunities if o["severity"] == "critical"]
        high = [o for o in opportunities if o["severity"] == "high"]
        medium = [o for o in opportunities if o["severity"] == "medium"]
        low = [o for o in opportunities if o["severity"] == "low"]

        lines = []
        if critical:
            lines.append(f"{len(critical)} critical refactoring opportunity(ies) requiring immediate attention.")
        if high:
            lines.append(f"{len(high)} high-priority refactoring opportunity(ies) identified.")
        if medium:
            lines.append(f"{len(medium)} medium-priority improvement(s) available.")
        if low:
            lines.append(f"{len(low)} low-priority cleanup(s) suggested.")

        by_type: dict[str, int] = {}
        for o in opportunities:
            by_type[o["type"]] = by_type.get(o["type"], 0) + 1
        if by_type:
            top = max(by_type, key=by_type.get)
            type_labels = {
                "extract-class": "Extract Class",
                "extract-method": "Extract Method",
                "extract-interface": "Extract Interface",
                "split-service": "Split Service",
                "split-controller": "Split Controller",
                "split-module": "Split Module",
                "merge-duplicate": "Merge Duplicate Logic",
                "remove-dead-code": "Remove Dead Code",
                "rename-identifier": "Rename Poor Identifiers",
                "reduce-coupling": "Reduce Coupling",
                "increase-cohesion": "Increase Cohesion",
            }
            label = type_labels.get(top, top.replace("_", " ").title())
            lines.append(f"Most common refactoring: {label} ({by_type[top]} occurrence(s)).")

        score_val = score.get("refactoring_score", 0)
        lines.append(f"Refactoring score: {score_val}/100.")

        if score_val < 40:
            lines.append("Comprehensive refactoring recommended to improve codebase structure.")
        elif score_val < 70:
            lines.append("Scheduled refactoring recommended for medium-risk areas.")

        roadmap = []
        for o in sorted(opportunities,
                        key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 5)):
            roadmap.append(f"[{o['severity'].upper()}] {o['name']}: {o.get('recommendation', '')[:120]}")

        return {
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "low_count": len(low),
            "summary_text": " ".join(lines),
            "roadmap": roadmap[:20],
        }
