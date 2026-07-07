import math
import os
import re
from pathlib import Path
from typing import Any


MAGIC_NUMBERS_PATTERN: list[tuple[str, str, str]] = [
    ("magic_number_value", r'(?<![.\w])-?\b\d{3,}\b(?!\s*[:=]?\s*["\'\)])', "Magic Number"),
]

DEEP_NESTING_PATTERN = re.compile(
    r'(for\s+\w+|while\s+[^:]+|if\s+[^:]+)[\s\S]{0,300}?'
    r'(for\s+\w+|while\s+[^:]+|if\s+[^:]+)[\s\S]{0,300}?'
    r'(for\s+\w+|while\s+[^:]+|if\s+[^:]+)[\s\S]{0,300}?'
    r'(for\s+\w+|while\s+[^:]+|if\s+[^:]+)',
    re.DOTALL,
)

LARGE_SWITCH_PATTERN = re.compile(
    r'(switch|case)\s+\w+.*?(?:\bcase\s+\w+.*?){5,}',
    re.DOTALL,
)

POOR_NAMING_PATTERN = re.compile(
    r'\b([a-z]+_[a-z]+\s*=\s*[A-Z]\w+|'
    r'[A-Z][a-z]+(?:_[a-z]+)+\s*=\s*\d+|'
    r'temp\d*|data\d*|val\d*|obj\d*|item\d*|thing\d*|stuff\d*|var\d*|result\d*|test\d*|t\d+)\b',
)

DOCSTRING_PATTERN = re.compile(
    r'(def|class|async def)\s+\w+\s*\([^)]*\)\s*(?::|->)',
)
DOCSTRING_BODY_PATTERN = re.compile(r'""".*?"""', re.DOTALL)


class MaintainabilityIntelligenceEngine:

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
        smells = self._detect_all(workspace_path, code_intel, code_quality,
                                   file_analysis, func_class, dep_analysis,
                                   call_graph, semantic, config_intel,
                                   recommendations)
        score = self._compute_score(smells)
        tech_debt = self._compute_technical_debt(smells, score)
        module_health = self._compute_module_health(workspace_path, smells, func_class, file_analysis)
        summary = self._generate_summary(smells, score, tech_debt)
        return {
            "maintainability_score": score,
            "code_smells": smells,
            "technical_debt": tech_debt,
            "module_health": module_health,
            "summary": summary,
        }

    def _detect_all(self, workspace_path, code_intel, code_quality,
                     file_analysis, func_class, dep_analysis,
                     call_graph, semantic, config_intel,
                     recommendations) -> list[dict]:
        smells: list[dict] = []

        self._detect_large_classes(func_class, smells)
        self._detect_god_classes(func_class, smells)
        self._detect_large_functions(func_class, smells)
        self._detect_long_parameters(func_class, smells)
        self._detect_duplication(code_quality, smells)
        self._detect_unused_elements(func_class, call_graph, smells)
        self._detect_pattern_smells(workspace_path, code_intel, smells)
        self._detect_coupling_cohesion(semantic, dep_analysis, call_graph, smells)
        self._detect_naming_issues(workspace_path, code_intel, func_class, smells)
        self._detect_documentation_gaps(workspace_path, code_intel, func_class, smells)
        self._detect_deep_nesting(workspace_path, code_intel, smells)
        self._detect_large_switch(workspace_path, code_intel, smells)
        self._detect_architecture_smells(file_analysis, dep_analysis, semantic, func_class, smells)
        self._detect_maintainability_smells(code_quality, recommendations, smells)

        return smells

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
                           (".py", ".js", ".ts", ".jsx", ".tsx", ".java")):
                        fpath = os.path.join(root, fn)
                        try:
                            with open(fpath, "r", errors="ignore") as fh:
                                files[fpath] = fh.read()
                        except Exception:
                            pass
        return files

    def _detect_large_classes(self, func_class, smells):
        if not func_class:
            return
        classes = func_class.get("classes", [])
        if isinstance(classes, list):
            for cls in classes:
                name = cls.get("name", "")
                file = cls.get("file", "")
                methods = cls.get("methods", [])
                if len(methods) > 20:
                    smells.append(self._make_smell(
                        f"Large Class: {name}", "large-class", "high",
                        [file], [], [name],
                        desc=f"Class has {len(methods)} methods — violates Single Responsibility Principle",
                        effort=f"{len(methods) // 4} hours estimated",
                        suggestion=f"Split {name} into smaller focused classes by concern",
                    ))
                elif len(methods) > 12:
                    smells.append(self._make_smell(
                        f"Large Class: {name}", "large-class", "medium",
                        [file], [], [name],
                        desc=f"Class has {len(methods)} methods — moderate size",
                        effort=f"{len(methods) // 5} hours estimated",
                        suggestion=f"Consider extracting interfaces or base classes from {name}",
                    ))

    def _detect_god_classes(self, func_class, smells):
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
                    smells.append(self._make_smell(
                        f"God Class: {name}", "god-class", "critical",
                        [file], [], [name],
                        desc=f"Class has {len(methods)} methods spanning ~{cls_lines} lines — God Class anti-pattern",
                        effort=f"{cls_lines // 10} hours estimated",
                        suggestion=f"Decompose {name} into multiple cohesive classes using Extract Class refactoring",
                    ))

    def _detect_large_functions(self, func_class, smells):
        if not func_class:
            return
        functions = func_class.get("functions", [])
        if isinstance(functions, list):
            for fn in functions:
                name = fn.get("name", "")
                file = fn.get("file", "")
                lines = fn.get("end_line", 0) - fn.get("start_line", 0)
                if lines > 100:
                    smells.append(self._make_smell(
                        f"God Function: {name}", "long-function", "critical",
                        [file], [name], [],
                        desc=f"Function spans {lines} lines — extremely long, violates Single Responsibility",
                        effort=f"{lines // 8} hours estimated",
                        suggestion=f"Break {name} into smaller functions of 15-20 lines each",
                    ))
                elif lines > 50:
                    smells.append(self._make_smell(
                        f"Long Function: {name}", "long-function", "high",
                        [file], [name], [],
                        desc=f"Function spans {lines} lines — high complexity",
                        effort=f"{lines // 10} hours estimated",
                        suggestion=f"Extract logical blocks from {name} into separate methods",
                    ))

    def _detect_long_parameters(self, func_class, smells):
        if not func_class:
            return
        functions = func_class.get("functions", [])
        if isinstance(functions, list):
            for fn in functions:
                name = fn.get("name", "")
                file = fn.get("file", "")
                params_raw = fn.get("parameters", fn.get("params", []))
                num_params = len(params_raw) if isinstance(params_raw, (list, tuple)) else 0
                if num_params > 8:
                    smells.append(self._make_smell(
                        f"Long Parameter List: {name}", "long-parameter-list", "high",
                        [file], [name], [],
                        desc=f"Function has {num_params} parameters — poor abstraction",
                        effort="1-2 hours estimated",
                        suggestion="Group related parameters into a configuration object or dataclass",
                    ))
                elif num_params > 5:
                    smells.append(self._make_smell(
                        f"Long Parameter List: {name}", "long-parameter-list", "medium",
                        [file], [name], [],
                        desc=f"Function has {num_params} parameters",
                        effort="1 hour estimated",
                        suggestion="Consider introducing a parameter object for related parameters",
                    ))

    def _detect_duplication(self, code_quality, smells):
        if not code_quality or not isinstance(code_quality, dict):
            return
        issues = code_quality.get("issues", [])
        if isinstance(issues, list):
            dup = [i for i in issues if isinstance(i, dict) and
                   i.get("type", "") in ("duplicate", "redundant", "repeated")]
            for i in dup[:10]:
                name = i.get("name", i.get("title", "Duplicate Code"))
                sev = i.get("severity", "medium")
                aff = i.get("files", [])
                smells.append(self._make_smell(
                    f"Duplicate Logic: {name}", "duplicate-code", sev,
                    aff, [],
                    desc=i.get("description", i.get("detail", "Duplicated code increases maintenance burden")),
                    effort="1-3 hours estimated",
                    suggestion="Extract shared logic into reusable utility functions or modules",
                ))

        duplications = code_quality.get("duplications", code_quality.get("duplicates", []))
        if isinstance(duplications, list):
            for d in duplications[:10]:
                aff = [d] if isinstance(d, str) else [d.get("file", "")]
                sev = "medium" if isinstance(d, str) else d.get("severity", "medium")
                smells.append(self._make_smell(
                    f"Repeated Code Block", "duplicate-code", sev,
                    aff, [],
                    desc="Code duplication increases maintenance cost and risk of inconsistencies",
                    effort="1-2 hours estimated",
                    suggestion="Consolidate duplicated blocks into shared functions",
                ))

    def _detect_unused_elements(self, func_class, call_graph, smells):
        if not func_class:
            return
        all_functions = func_class.get("functions", [])
        all_classes = func_class.get("classes", [])

        called_functions: set[str] = set()
        if call_graph and isinstance(call_graph, dict):
            nodes = call_graph.get("nodes", [])
            if isinstance(nodes, list):
                for n in nodes:
                    name = n.get("name", n.get("label", ""))
                    called_functions.add(name)

        func_names: dict[str, str] = {}
        for fn in (all_functions if isinstance(all_functions, list) else []):
            fname = fn.get("name", "")
            ffile = fn.get("file", "")
            if fname:
                func_names[fname] = ffile

        for fname, ffile in func_names.items():
            if fname not in called_functions:
                smells.append(self._make_smell(
                    f"Unused Function: {fname}", "unused-code", "medium",
                    [ffile], [fname], [],
                    desc=f"Function '{fname}' is defined but never called in the call graph",
                    effort="0.5-1 hour estimated",
                    suggestion=f"Remove {fname} or add it to the public API if externally consumed",
                ))

        class_names: dict[str, str] = {}
        for cls in (all_classes if isinstance(all_classes, list) else []):
            cname = cls.get("name", "")
            cfile = cls.get("file", "")
            if cname:
                class_names[cname] = cfile

        for cname, cfile in class_names.items():
            if cname not in called_functions:
                smells.append(self._make_smell(
                    f"Unused Class: {cname}", "unused-code", "low",
                    [cfile], [], [cname],
                    desc=f"Class '{cname}' is defined but may not be imported or used",
                    effort="0.5 hour estimated",
                    suggestion=f"Verify {cname} is used; consider removing if unnecessary",
                ))

    def _detect_pattern_smells(self, workspace_path, code_intel, smells):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath

            for pattern_id, pattern, label in MAGIC_NUMBERS_PATTERN:
                matches = re.findall(pattern, content)
                if len(matches) > 10:
                    smells.append(self._make_smell(
                        f"Magic Numbers: {rel}", "magic-number", "medium",
                        [rel], [],
                        desc=f"Found {len(matches)} magic numeric literals in {rel} — use named constants",
                        effort="1-2 hours estimated",
                        suggestion="Replace magic numbers with named constants (e.g. MAX_RETRIES = 3)",
                    ))
                    break

    def _detect_coupling_cohesion(self, semantic, dep_analysis, call_graph, smells):
        coupling_score = None
        cohesion_score = None

        if semantic and isinstance(semantic, dict):
            score = semantic.get("understanding_score", {})
            if isinstance(score, dict):
                coupling_score = score.get("coupling", score.get("dependency_score"))
                cohesion_score = score.get("cohesion")

        if dep_analysis and isinstance(dep_analysis, dict):
            files = dep_analysis.get("files", [])
            if isinstance(files, list):
                for f in files:
                    if isinstance(f, dict):
                        cs = f.get("coupling_score", f.get("afferent_coupling", 0))
                        ch = f.get("cohesion_score", f.get("cohesion", 0))
                        if isinstance(cs, (int, float)) and cs > 0.7:
                            fname = f.get("name", f.get("file", ""))
                            smells.append(self._make_smell(
                                f"High Coupling: {os.path.basename(fname)}", "high-coupling", "high",
                                [fname], [],
                                desc=f"Coupling score {round(cs, 2)} — excessive dependencies make changes risky",
                                effort="2-4 hours estimated",
                                suggestion="Introduce interfaces or facades to decouple dependencies",
                            ))
                        if isinstance(ch, (int, float)) and ch < 0.3:
                            fname = f.get("name", f.get("file", ""))
                            smells.append(self._make_smell(
                                f"Low Cohesion: {os.path.basename(fname)}", "low-cohesion", "medium",
                                [fname], [],
                                desc=f"Cohesion score {round(ch, 2)} — module has unrelated responsibilities",
                                effort="1-3 hours estimated",
                                suggestion="Split module into focused units by concern",
                            ))

    def _detect_naming_issues(self, workspace_path, code_intel, func_class, smells):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            matches = POOR_NAMING_PATTERN.findall(content)
            if len(matches) > 5:
                smells.append(self._make_smell(
                    f"Poor Naming: {rel}", "poor-naming", "low",
                    [rel], [],
                    desc=f"Found {len(matches)} poorly named variables (temp, data, val, etc.) — reduce readability",
                    effort="1-3 hours estimated",
                    suggestion="Rename variables with meaningful, domain-specific names",
                ))

        if func_class:
            functions = func_class.get("functions", [])
            if isinstance(functions, list):
                vague_names = 0
                vague_files: set[str] = set()
                for fn in functions:
                    name = fn.get("name", "")
                    ffile = fn.get("file", "")
                    if re.match(r'^(do_?|handle_?|process_?|run_?|execute_?|foo|bar|baz|test_?\d)', name, re.I):
                        vague_names += 1
                        if ffile:
                            vague_files.add(ffile)
                if vague_names > 3:
                    smells.append(self._make_smell(
                        f"Inconsistent Naming: {vague_names} vague function names", "poor-naming", "low",
                        list(vague_files), [],
                        desc=f"{vague_names} functions have non-descriptive names (do_, handle_, process_, etc.)",
                        effort="1-2 hours estimated",
                        suggestion="Use domain-specific verbs that describe the actual behavior",
                    ))

    def _detect_documentation_gaps(self, workspace_path, code_intel, func_class, smells):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath

            func_decls = DOCSTRING_PATTERN.findall(content)
            docstring_bodies = DOCSTRING_BODY_PATTERN.findall(content)
            documented = len(docstring_bodies)
            total = len(func_decls)

            if total > 0 and documented / total < 0.3:
                smells.append(self._make_smell(
                    f"Missing Documentation: {rel}", "missing-documentation", "medium",
                    [rel], [],
                    desc=f"Only {documented}/{total} functions/classes have docstrings (< 30% documented)",
                    effort="2-4 hours estimated",
                    suggestion="Add docstrings to all public functions and classes explaining purpose, params, and returns",
                ))
                break

    def _detect_deep_nesting(self, workspace_path, code_intel, smells):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            matches = DEEP_NESTING_PATTERN.findall(content)
            if len(matches) > 2:
                smells.append(self._make_smell(
                    f"Deep Nesting: {rel}", "deep-nesting", "high",
                    [rel], [],
                    desc=f"Found {len(matches)} deeply nested control structures (4+ levels) — high complexity",
                    effort="2-4 hours estimated",
                    suggestion="Extract nested blocks into separate functions; use early returns or guard clauses",
                ))

    def _detect_large_switch(self, workspace_path, code_intel, smells):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            if LARGE_SWITCH_PATTERN.search(content):
                smells.append(self._make_smell(
                    f"Large Switch Statement: {rel}", "maintainability-smell", "medium",
                    [rel], [],
                    desc="Large switch/case with 5+ branches — violates Open/Closed Principle",
                    effort="2-3 hours estimated",
                    suggestion="Replace with polymorphism, strategy pattern, or a dictionary dispatch",
                ))

    def _detect_architecture_smells(self, file_analysis, dep_analysis, semantic, func_class, smells):
        if not file_analysis:
            return
        items = file_analysis if isinstance(file_analysis, list) else file_analysis.get("files", [])
        if isinstance(items, list):
            small_files = [f for f in items if isinstance(f, dict) and
                           isinstance(f.get("lines", 0), (int, float)) and f["lines"] < 10]
            if len(small_files) > 5:
                smells.append(self._make_smell(
                    "Many Small Files", "architecture-smell", "low",
                    [f.get("name", "") for f in small_files[:5]], [],
                    desc=f"{len(small_files)} files with < 10 lines — fragmentation indicates poor organization",
                    effort="1-3 hours estimated",
                    suggestion="Consolidate related small files into cohesive modules",
                ))

            large_files = [f for f in items if isinstance(f, dict) and
                           isinstance(f.get("lines", 0), (int, float)) and f["lines"] > 800]
            if len(large_files) > 2:
                smells.append(self._make_smell(
                    "Multiple Large Files", "architecture-smell", "high",
                    [f.get("name", "") for f in large_files[:3]], [],
                    desc=f"{len(large_files)} files exceed 800 lines — indicates poor modularization",
                    effort="3-8 hours estimated",
                    suggestion="Split large files into smaller modules with clear responsibilities",
                ))

        if dep_analysis and isinstance(dep_analysis, dict):
            circular = dep_analysis.get("circular_dependencies", [])
            if isinstance(circular, list) and len(circular) > 0:
                smells.append(self._make_smell(
                    f"Circular Dependencies ({len(circular)})", "architecture-smell", "critical",
                    [str(c) if not isinstance(c, str) else c for c in circular[:5]], [],
                    desc=f"Found {len(circular)} circular dependencies — makes refactoring risky",
                    effort="3-8 hours estimated",
                    suggestion="Break cycles by introducing interfaces or event-driven communication",
                ))

    def _detect_maintainability_smells(self, code_quality, recommendations, smells):
        if code_quality and isinstance(code_quality, dict):
            deps = code_quality.get("duplications", code_quality.get("duplicates", []))
            if isinstance(deps, list) and len(deps) > 3:
                smells.append(self._make_smell(
                    f"High Duplication Across {len(deps)} Locations", "maintainability-smell", "medium",
                    [], [],
                    desc=f"Code is duplicated in {len(deps)} locations — increases maintenance cost",
                    effort=f"{len(deps)} hours estimated",
                    suggestion="Implement DRY principle by extracting common logic into shared utilities",
                ))

            issues = code_quality.get("issues", [])
            if isinstance(issues, list):
                design_issues = [i for i in issues if isinstance(i, dict) and
                                 i.get("type", "") in ("complexity", "design", "architecture")]
                for i in design_issues[:5]:
                    name = i.get("name", i.get("title", "Design Issue"))
                    sev = i.get("severity", "medium")
                    aff = i.get("files", [])
                    smells.append(self._make_smell(
                        f"Design Smell: {name}", "maintainability-smell", sev,
                        aff, [],
                        desc=i.get("description", i.get("detail", "Design-level issue")),
                        effort="2-4 hours estimated",
                        suggestion=i.get("suggestion", "Review and refactor design"),
                    ))

    def _make_smell(self, name: str, stype: str, severity: str = "medium",
                    files: list[str] | None = None,
                    functions: list[str] | None = None,
                    classes: list[str] | None = None,
                    desc: str = "", effort: str = "", suggestion: str = "") -> dict:
        return {
            "name": name,
            "type": stype,
            "severity": severity,
            "affected_files": files or [],
            "affected_functions": functions or [],
            "affected_classes": classes or [],
            "description": desc,
            "refactoring_effort": effort,
            "ai_suggestion": suggestion,
        }

    def _compute_score(self, smells) -> dict:
        total = len(smells)
        sev_weights = {"critical": 10, "high": 7, "medium": 4, "low": 2}
        weighted = sum(sev_weights.get(s.get("severity", "low"), 1) for s in smells)
        max_possible = total * 10 if total > 0 else 1
        raw_debt = min(weighted / max_possible * 100, 100) if total > 0 else 0

        overall = round(max(0, 100 - raw_debt * 1.3), 1)
        health = round(max(0, overall - 8), 1)
        tds = round(min(raw_debt * 1.1, 100), 1)
        readiness = round(max(0, 100 - raw_debt * 0.9), 1)
        stability = round(max(0, 100 - raw_debt * 0.7), 1)
        confidence = round(min(total * 3, 90), 1)

        readability_smells = [s for s in smells if s["type"] in (
            "poor-naming", "missing-documentation", "magic-number", "deep-nesting")]
        readability_penalty = min(sum(
            sev_weights.get(s.get("severity", "low"), 1) for s in readability_smells
        ) * 8, 100) if readability_smells else 0
        readability = round(max(0, 100 - readability_penalty), 1)

        modularity_smells = [s for s in smells if s["type"] in (
            "high-coupling", "low-cohesion", "architecture-smell", "god-class", "large-class")]
        modularity_penalty = min(sum(
            sev_weights.get(s.get("severity", "low"), 1) for s in modularity_smells
        ) * 7, 100) if modularity_smells else 0
        modularity = round(max(0, 100 - modularity_penalty), 1)

        org_smells = [s for s in smells if s["type"] in (
            "large-class", "long-function", "duplicate-code", "long-parameter-list",
            "architecture-smell", "maintainability-smell")]
        org_penalty = min(sum(
            sev_weights.get(s.get("severity", "low"), 1) for s in org_smells
        ) * 6, 100) if org_smells else 0
        code_organization = round(max(0, 100 - org_penalty), 1)

        if raw_debt >= 55:
            level = "critical"
        elif raw_debt >= 38:
            level = "high"
        elif raw_debt >= 20:
            level = "medium"
        elif raw_debt >= 8:
            level = "low"
        else:
            level = "informational"

        return {
            "overall_maintainability_score": overall,
            "maintainability_health": health,
            "technical_debt_score": tds,
            "refactoring_readiness": readiness,
            "long_term_stability": stability,
            "readability": readability,
            "modularity": modularity,
            "code_organization": code_organization,
            "ai_confidence": confidence,
            "risk_level": level,
        }

    def _compute_technical_debt(self, smells, score) -> dict:
        hour_estimates = {"critical": 8, "high": 4, "medium": 2, "low": 0.5}
        total_hours = 0.0
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for s in smells:
            sev = s.get("severity", "low")
            total_hours += hour_estimates.get(sev, 0.5)
            if sev in counts:
                counts[sev] += 1

        if total_hours > 100:
            debt_level = "critical"
        elif total_hours > 50:
            debt_level = "high"
        elif total_hours > 20:
            debt_level = "medium"
        elif total_hours > 5:
            debt_level = "low"
        else:
            debt_level = "informational"

        effort_str = f"{total_hours:.0f} hours"
        if total_hours >= 40:
            weeks = round(total_hours / 40, 1)
            effort_str += f" (~{weeks} week{'s' if weeks > 1 else ''})"

        cost = f"${round(total_hours * 100):,}"
        if total_hours >= 40:
            cost += f" - ${round(total_hours * 150):,}"

        return {
            "total_debt_hours": round(total_hours, 1),
            "debt_level": debt_level,
            "estimated_refactoring_effort": effort_str,
            "maintenance_cost": cost,
            "critical_file_count": counts["critical"],
            "high_file_count": counts["high"],
            "medium_file_count": counts["medium"],
            "low_file_count": counts["low"],
        }

    def _compute_module_health(self, workspace_path, smells, func_class, file_analysis) -> list[dict]:
        module_map: dict[str, dict] = {}

        for s in smells:
            for f in s.get("affected_files", []):
                if f not in module_map:
                    module_map[f] = {"issues": [], "complexity": 0, "smell_count": 0}
                module_map[f]["issues"].append(s.get("type", ""))
                module_map[f]["smell_count"] = module_map[f].get("smell_count", 0) + 1

        if func_class and not module_map:
            functions = func_class.get("functions", [])
            if isinstance(functions, list):
                for fn in functions:
                    ffile = fn.get("file", "")
                    if ffile and ffile not in module_map:
                        module_map[ffile] = {"issues": [], "complexity": 0, "smell_count": 0}

        results = []
        for fname, info in module_map.items():
            issue_count = info["smell_count"]
            complexity = min(issue_count * 15, 100)
            score = max(0, 100 - complexity)
            cohesion = max(0, 100 - issue_count * 10)
            coupling = min(issue_count * 8, 100)
            debt_est = f"{issue_count * 2}-{issue_count * 4} hours"

            results.append({
                "file_name": os.path.basename(fname) if workspace_path else fname,
                "score": round(score, 1),
                "issues": info["issues"][:5],
                "complexity": round(complexity, 1),
                "cohesion": round(cohesion, 1),
                "coupling": round(coupling, 1),
                "debt_estimate": debt_est,
            })

        results.sort(key=lambda x: x["score"])
        return results[:30]

    def _generate_summary(self, smells, score, tech_debt) -> dict:
        critical = [s for s in smells if s["severity"] == "critical"]
        high = [s for s in smells if s["severity"] == "high"]
        medium = [s for s in smells if s["severity"] == "medium"]
        low = [s for s in smells if s["severity"] == "low"]

        lines = []
        if critical:
            lines.append(f"Found {len(critical)} critical code smell(s) requiring immediate refactoring.")
        if high:
            lines.append(f"{len(high)} high-severity maintainability issue(s) identified.")
        if medium:
            lines.append(f"{len(medium)} moderate improvement(s) available for upcoming sprints.")

        by_type: dict[str, int] = {}
        for s in smells:
            by_type[s["type"]] = by_type.get(s["type"], 0) + 1
        if by_type:
            top = max(by_type, key=by_type.get)
            type_labels = {
                "large-class": "Large class",
                "god-class": "God class",
                "long-function": "Long function",
                "duplicate-code": "Duplicated code",
                "unused-code": "Unused code",
                "magic-number": "Magic number",
                "high-coupling": "High coupling",
                "low-cohesion": "Low cohesion",
                "poor-naming": "Poor naming",
                "missing-documentation": "Missing documentation",
                "deep-nesting": "Deep nesting",
                "architecture-smell": "Architecture smell",
                "long-parameter-list": "Long parameter list",
                "maintainability-smell": "Maintainability smell",
            }
            label = type_labels.get(top, top.replace("_", " ").title())
            lines.append(f"Most common issue: {label} ({by_type[top]} occurrence(s)).")

        score_val = score.get("overall_maintainability_score", 0)
        tds = tech_debt.get("total_debt_hours", 0)
        effort = tech_debt.get("estimated_refactoring_effort", "")
        lines.append(f"Maintainability score: {score_val}/100. Estimated technical debt: {tds}h ({effort}).")

        if score_val < 40:
            lines.append("Immediate refactoring recommended for critical code smells and high debt areas.")
        elif score_val < 70:
            lines.append("Scheduled refactoring recommended to reduce technical debt.")

        prioritized = []
        for s in sorted(smells, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}.get(x.get("severity", "low"), 5)):
            suggestion = s.get("ai_suggestion", "")
            effort = s.get("refactoring_effort", "")
            line = f"[{s['severity'].upper()}] {s['name']}: {suggestion}"
            if effort:
                line += f" ({effort})"
            prioritized.append(line)

        return {
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "low_count": len(low),
            "informational_count": 0,
            "summary_text": " ".join(lines),
            "prioritized_recommendations": prioritized[:25],
        }
