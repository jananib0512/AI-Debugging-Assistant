import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RiskIntelligenceEngine:

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
        risks, heatmap_items = self._detect_all_risks(
            project_analysis, code_intel, code_quality,
            file_analysis, func_class, dep_analysis,
            call_graph, semantic, config_intel, recommendations
        )
        risk_score = self._compute_risk_score(
            risks, code_quality, dep_analysis, file_analysis,
            config_intel, semantic
        )
        summary = self._generate_summary(risks, risk_score, project_analysis)
        return {
            "risk_score": risk_score,
            "risks": risks,
            "heatmap": heatmap_items,
            "summary": summary,
            "search_results": {},
        }

    def _detect_all_risks(self, project_analysis, code_intel, code_quality,
                           file_analysis, func_class, dep_analysis,
                           call_graph, semantic, config_intel,
                           recommendations) -> tuple[list[dict], list[dict]]:
        risks: list[dict] = []
        file_risk_map: dict[str, list[str]] = defaultdict(list)
        module_risk_map: dict[str, list[str]] = defaultdict(list)

        self._detect_complexity_risks(code_intel, code_quality, func_class, file_analysis, risks, file_risk_map)
        self._detect_dependency_risks(dep_analysis, risks, file_risk_map, module_risk_map)
        self._detect_call_graph_risks(call_graph, risks, file_risk_map)
        self._detect_semantic_risks(semantic, risks, file_risk_map, module_risk_map)
        self._detect_config_risks(config_intel, risks, file_risk_map)
        self._detect_entry_point_risks(project_analysis, risks, file_risk_map)
        self._detect_quality_risks(code_quality, recommendations, risks, file_risk_map)

        heatmap = self._build_heatmap(risks, file_risk_map, module_risk_map, project_analysis)
        return risks, heatmap

    def _detect_complexity_risks(self, code_intel, code_quality, func_class,
                                  file_analysis, risks, file_risk_map):
        if code_quality:
            issues = code_quality.get("issues", []) or code_quality.get("total_issues", [])
            if isinstance(issues, int):
                total = issues
                if total > 50:
                    sev = "critical" if total > 200 else ("high" if total > 100 else "medium")
                    risks.append(self._make_risk(
                        "Excessive Code Issues", "complexity", sev,
                        detail=f"{total} total code issues detected across the project",
                        recommendation="Run targeted refactoring sprints on modules with the highest issue density"
                    ))

        if code_intel:
            summary = code_intel.get("summary", {})
            files = summary.get("total_files", 0)
            loc = summary.get("total_lines_of_code", 0)
            if files > 0 and loc / files > 300:
                avg = round(loc / files)
                risks.append(self._make_risk(
                    "High Average File Complexity", "complexity",
                    "high" if avg > 500 else "medium",
                    detail=f"Average {avg} LOC per file across {files} files — indicates overly large files",
                    recommendation="Break large files into smaller, single-responsibility modules"
                ))

        if func_class:
            functions = func_class.get("functions", [])
            classes = func_class.get("classes", [])
            if isinstance(functions, list):
                for fn in functions:
                    name = fn.get("name", "")
                    file = fn.get("file", "")
                    lines = fn.get("end_line", 0) - fn.get("start_line", 0)
                    if lines > 100:
                        risks.append(self._make_risk(
                            f"Large Function: {name}", "large-function", "high",
                            [file], [], [name],
                            detail=f"Function spans {lines} lines in {file}",
                            recommendation="Refactor into smaller helper functions"
                        ))
                        file_risk_map[file].append("large-function")
                    elif lines > 50:
                        risks.append(self._make_risk(
                            f"Long Function: {name}", "large-function", "medium",
                            [file], [], [name],
                            detail=f"Function spans {lines} lines",
                            recommendation="Consider extracting logic into smaller functions"
                        ))
                        file_risk_map[file].append("large-function")
            if isinstance(classes, list):
                for cls in classes:
                    name = cls.get("name", "")
                    file = cls.get("file", "")
                    methods = cls.get("methods", [])
                    if len(methods) > 15:
                        risks.append(self._make_risk(
                            f"Large Class: {name}", "large-class", "high",
                            [file], [name], [],
                            detail=f"Class has {len(methods)} methods in {file}",
                            recommendation="Split class into focused sub-classes"
                        ))
                        file_risk_map[file].append("large-class")
                    elif len(methods) > 8:
                        risks.append(self._make_risk(
                            f"Overloaded Class: {name}", "large-class", "medium",
                            [file], [name], [],
                            detail=f"Class has {len(methods)} methods",
                            recommendation="Consider extracting related groups of methods"
                        ))
                        file_risk_map[file].append("large-class")

        if file_analysis and isinstance(file_analysis, dict):
            items = file_analysis if isinstance(file_analysis, list) else file_analysis.get("files", [])
            if isinstance(items, list):
                for f in items:
                    fname = f.get("name", "") or f.get("path", "")
                    score = f.get("health_score", f.get("score", 100))
                    if isinstance(score, (int, float)) and score < 30:
                        risks.append(self._make_risk(
                            f"Critical File Health: {os.path.basename(fname)}", "high-complexity", "critical",
                            [fname], [], [],
                            detail=f"File health score is {score}/100",
                            recommendation="Immediate refactoring required for this file"
                        ))
                        file_risk_map[fname].append("high-complexity")

    def _detect_dependency_risks(self, dep_analysis, risks, file_risk_map, module_risk_map):
        if not dep_analysis:
            return
        circular = dep_analysis.get("circular_dependencies", []) or dep_analysis.get("cycles", [])
        if isinstance(circular, list):
            for cycle in circular[:20]:
                if isinstance(cycle, dict):
                    members = cycle.get("members", cycle.get("files", []))
                    name = cycle.get("name", "|".join(members[:3]))
                elif isinstance(cycle, list):
                    members = cycle
                    name = "|".join(members[:3])
                else:
                    continue
                risks.append(self._make_risk(
                    f"Circular Dependency: {name[:80]}", "circular-dependency", "critical",
                    members if isinstance(members, list) else [],
                    detail=f"{len(members)} files in circular dependency cycle",
                    recommendation="Break the cycle by extracting shared logic into a common module"
                ))
                for m in (members if isinstance(members, list) else []):
                    file_risk_map[m].append("circular-dependency")

        unused = dep_analysis.get("unused_dependencies", []) or dep_analysis.get("unused", [])
        if isinstance(unused, list):
            for dep in unused:
                name = dep if isinstance(dep, str) else dep.get("name", str(dep))
                risks.append(self._make_risk(
                    f"Broken/Unused Dependency: {name}", "broken-dependency", "high",
                    detail=f"Dependency '{name}' is unused or unresolvable",
                    recommendation="Remove unused dependency or install missing package"
                ))

        total = dep_analysis.get("total_imports", dep_analysis.get("total", 0))
        depth = dep_analysis.get("max_depth", dep_analysis.get("max_depth", 0))
        if isinstance(depth, (int, float)) and depth > 8:
            risks.append(self._make_risk(
                "Deep Import Chains", "deep-call-chain", "medium",
                detail=f"Maximum import depth is {depth}",
                recommendation="Flatten deep import hierarchies to reduce coupling"
            ))

        coupling = dep_analysis.get("average_coupling", dep_analysis.get("avg_coupling", 0))
        if isinstance(coupling, (int, float)) and coupling > 0.7:
            risks.append(self._make_risk(
                "High Module Coupling", "high-coupling", "high",
                detail=f"Average coupling score is {round(coupling, 2)} — modules are tightly interdependent",
                recommendation="Apply dependency inversion and introduce interfaces"
            ))
        elif isinstance(coupling, (int, float)) and coupling > 0.5:
            risks.append(self._make_risk(
                "Moderate Module Coupling", "high-coupling", "medium",
                detail=f"Average coupling score is {round(coupling, 2)}",
                recommendation="Review module boundaries for potential decoupling"
            ))

        cohesion = dep_analysis.get("average_cohesion", dep_analysis.get("avg_cohesion", 1))
        if isinstance(cohesion, (int, float)) and cohesion < 0.3:
            risks.append(self._make_risk(
                "Low Module Cohesion", "low-cohesion", "high",
                detail=f"Average cohesion score is {round(cohesion, 2)} — modules mix unrelated concerns",
                recommendation="Restructure modules around single business capabilities"
            ))

    def _detect_call_graph_risks(self, call_graph, risks, file_risk_map):
        if not call_graph:
            return
        nodes = call_graph.get("nodes", []) if isinstance(call_graph, dict) else []
        edges = call_graph.get("edges", []) if isinstance(call_graph, dict) else []
        issues = call_graph.get("issues", []) if isinstance(call_graph, dict) else []
        flows = call_graph.get("execution_flows", []) if isinstance(call_graph, dict) else []

        if isinstance(issues, list):
            for iss in issues[:20]:
                name = iss.get("name", iss.get("type", "Unknown"))
                sev = iss.get("severity", "medium")
                desc = iss.get("detail", iss.get("description", ""))
                affected = iss.get("affected_files", iss.get("files", []))
                risks.append(self._make_risk(
                    f"Call Graph Issue: {name}", "dead-code" if "dead" in name.lower() else "deep-call-chain",
                    sev, affected if isinstance(affected, list) else [],
                    detail=desc,
                    recommendation="Review call graph issue and fix accordingly"
                ))
                for f in (affected if isinstance(affected, list) else []):
                    file_risk_map[f].append("call-graph-issue")

        if isinstance(flows, list):
            long_flows = [f for f in flows if len(f.get("steps", f.get("nodes", []))) > 10]
            for flow in long_flows[:10]:
                fname = flow.get("name", "Unknown Flow")
                steps = len(flow.get("steps", flow.get("nodes", [])))
                risks.append(self._make_risk(
                    f"Deep Execution Chain: {fname}", "deep-call-chain", "medium",
                    detail=f"Execution flow has {steps} steps — high cognitive load",
                    recommendation="Simplify execution flow by reducing chain length"
                ))

    def _detect_semantic_risks(self, semantic, risks, file_risk_map, module_risk_map):
        if not semantic:
            return
        score = semantic.get("understanding_score", {})
        if isinstance(score, dict):
            bl = score.get("business_logic", 50)
            da = score.get("data_flow", 50)
            sc = score.get("security", 50)
            ar = score.get("architecture", 50)
            if isinstance(bl, (int, float)) and bl < 30:
                risks.append(self._make_risk(
                    "Low Business Logic Understanding", "low-cohesion", "high",
                    detail=f"Business logic understanding score is {bl}% — logic may be scattered or opaque",
                    recommendation="Document and consolidate core business logic"
                ))
            if isinstance(sc, (int, float)) and sc < 30:
                risks.append(self._make_risk(
                    "Security Understanding Gap", "security-hotspot", "high",
                    detail=f"Security understanding score is {sc}% — auth/validation patterns may be missing",
                    recommendation="Audit authentication and input validation across endpoints"
                ))
            if isinstance(ar, (int, float)) and ar < 30:
                risks.append(self._make_risk(
                    "Architecture Understanding Gap", "architecture-risk", "high",
                    detail=f"Architecture understanding score is {ar}% — layers may be poorly organized",
                    recommendation="Review architecture layering and dependency flow"
                ))

        flows = semantic.get("business_flows", [])
        if isinstance(flows, list) and len(flows) == 0:
            risks.append(self._make_risk(
                "No Business Flows Detected", "dead-code", "medium",
                detail="Semantic engine found zero business flows — project may lack clear process structure",
                recommendation="Define and document core business processes"
            ))

        kg = semantic.get("knowledge_graph", {})
        if isinstance(kg, dict):
            nodes = kg.get("nodes", [])
            if isinstance(nodes, list) and len(nodes) == 0:
                risks.append(self._make_risk(
                    "Empty Knowledge Graph", "low-cohesion", "low",
                    detail="Knowledge graph has no nodes — semantic relationships are not mapped",
                    recommendation="Run semantic analysis with more source code context"
                ))

    def _detect_config_risks(self, config_intel, risks, file_risk_map):
        if not config_intel:
            return
        issues = config_intel.get("issues", []) if isinstance(config_intel, dict) else []
        files = config_intel.get("files", config_intel.get("config_files", []))
        if isinstance(issues, list):
            for iss in issues:
                name = iss if isinstance(iss, str) else iss.get("name", iss.get("file", "Unknown"))
                sev = "high" if isinstance(iss, str) else iss.get("severity", "medium")
                f = iss if isinstance(iss, str) else iss.get("file", "")
                risks.append(self._make_risk(
                    f"Configuration Issue: {name}", "configuration-risk", sev,
                    [f] if f else [],
                    detail=f"Configuration issue in {name}",
                    recommendation="Fix configuration according to project standards"
                ))
                if f:
                    file_risk_map[f].append("configuration-risk")

    def _detect_entry_point_risks(self, project_analysis, risks, file_risk_map):
        if not project_analysis:
            return
        eps = project_analysis.get("entry_points", [])
        if isinstance(eps, list) and len(eps) == 0:
            risks.append(self._make_risk(
                "No Entry Points Detected", "entry-point-risk", "high",
                detail="No application entry points found — project may be incomplete",
                recommendation="Ensure main entry point files are present and detectable"
            ))
        elif isinstance(eps, list) and len(eps) > 5:
            risks.append(self._make_risk(
                "Multiple Entry Points", "entry-point-risk", "medium",
                [e.get("path", "") for e in eps if isinstance(e, dict)],
                detail=f"Project has {len(eps)} entry points — may indicate split concerns",
                recommendation="Standardize entry points or document the multi-entry architecture"
            ))
            for e in eps:
                if isinstance(e, dict) and e.get("path"):
                    file_risk_map[e["path"]].append("entry-point-risk")

    def _detect_quality_risks(self, code_quality, recommendations, risks, file_risk_map):
        if code_quality and isinstance(code_quality, dict):
            score = code_quality.get("overall_score", code_quality.get("score", {}))
            if isinstance(score, dict):
                s_val = score.get("score", score.get("value", 0))
            else:
                s_val = score if isinstance(score, (int, float)) else 0
            if isinstance(s_val, (int, float)) and s_val < 40:
                risks.append(self._make_risk(
                    "Critical Code Quality", "security-hotspot", "critical",
                    detail=f"Overall quality score is {round(s_val)}/100 — project needs significant improvements",
                    recommendation="Prioritize code quality improvements across all modules"
                ))

        if recommendations and isinstance(recommendations, dict):
            recs = recommendations.get("recommendations", [])
            if isinstance(recs, list):
                high_risk = [r for r in recs if isinstance(r, dict) and r.get("priority") == "high"]
                for r in high_risk[:10]:
                    risks.append(self._make_risk(
                        r.get("title", r.get("name", "Recommendation")),
                        "performance-hotspot",
                        r.get("severity", "high"),
                        r.get("affected_files", []),
                        detail=r.get("description", r.get("detail", "")),
                        recommendation=r.get("suggestion", r.get("recommendation", ""))
                    ))

    def _make_risk(self, name: str, rtype: str, severity: str = "medium",
                   files: list[str] | None = None,
                   classes: list[str] | None = None,
                   functions: list[str] | None = None,
                   detail: str = "",
                   recommendation: str = "") -> dict:
        return {
            "name": name,
            "type": rtype,
            "severity": severity,
            "affected_files": files or [],
            "affected_classes": classes or [],
            "affected_functions": functions or [],
            "impact": {
                "business_impact": self._business_impact(rtype, severity),
                "technical_impact": self._technical_impact(rtype, severity),
                "recommended_priority": severity,
            },
            "detail": detail,
            "recommendation": recommendation,
        }

    def _business_impact(self, rtype: str, severity: str) -> str:
        impacts = {
            "circular-dependency": "Can cause deployment failures and runtime errors in production",
            "broken-dependency": "Application may fail to build or run in production",
            "security-hotspot": "Potential data breach or unauthorized access vector",
            "configuration-risk": "Misconfiguration can lead to environment-specific failures",
            "entry-point-risk": "Application may not start correctly in production",
            "large-function": "Reduced maintainability increases cost of feature changes",
            "large-class": "Slows down team velocity when modifying complex classes",
            "high-complexity": "Higher defect rate and longer testing cycles",
            "high-coupling": "Changes in one module cascade to others, increasing regression risk",
            "low-cohesion": "Harder to reason about module boundaries, slowing development",
            "deep-call-chain": "Difficult to trace bugs through long execution chains",
            "dead-code": "Unnecessary code increases maintenance surface area",
            "performance-hotspot": "May cause slowdowns or timeouts under production load",
            "architecture-risk": "Architecture issues compound over time, increasing technical debt",
        }
        base = impacts.get(rtype, "May impact project reliability and maintainability")
        if severity == "critical":
            return f"CRITICAL: {base}"
        return base

    def _technical_impact(self, rtype: str, severity: str) -> str:
        impacts = {
            "circular-dependency": "Circular imports prevent clean dependency injection and module isolation",
            "broken-dependency": "Missing or unused dependencies break the import graph",
            "security-hotspot": "Missing validation, weak auth, or exposed secrets",
            "configuration-risk": "Hardcoded values, missing config files, or invalid settings",
            "entry-point-risk": "Entry point misconfiguration affects startup sequence",
            "large-function": "Functions over 50 lines violate single-responsibility principle",
            "large-class": "Classes with many methods indicate missing abstraction layers",
            "high-complexity": "Cyclomatic complexity above threshold, hard to test",
            "high-coupling": "Tight coupling reduces reusability and testability",
            "low-cohesion": "Modules mix unrelated concerns, violating separation of concerns",
            "deep-call-chain": "Call chains over 10 steps deep increase debugging effort",
            "dead-code": "Unused exports, orphaned functions, and unreachable code paths",
            "performance-hotspot": "Inefficient algorithms, N+1 queries, or memory leaks",
            "architecture-risk": "Layer violations, missing patterns, or inconsistent structure",
        }
        base = impacts.get(rtype, "Increases technical debt and reduces code quality")
        if severity == "critical":
            return f"CRITICAL: {base}"
        return base

    def _compute_risk_score(self, risks, code_quality, dep_analysis,
                             file_analysis, config_intel, semantic) -> dict:
        total = len(risks)
        sev_scores = {"critical": 10, "high": 7, "medium": 4, "low": 2, "informational": 1}
        total_weighted = sum(sev_scores.get(r["severity"], 1) for r in risks)
        max_possible = total * 10 if total > 0 else 1
        raw_score = min(total_weighted / max_possible * 100, 100) if total > 0 else 0

        stability = 100 - raw_score
        maintainability_risk = raw_score
        architecture_risk = self._estimate_arch_risk(risks)
        dependency_risk = self._estimate_dep_risk(risks)
        security_risk = self._estimate_security_risk(risks)
        performance_risk = self._estimate_perf_risk(risks)

        overall = round((raw_score * 0.25 + maintainability_risk * 0.15
                         + architecture_risk * 0.15 + dependency_risk * 0.15
                         + security_risk * 0.15 + performance_risk * 0.15), 1)

        if overall >= 70:
            level = "critical"
        elif overall >= 50:
            level = "high"
        elif overall >= 30:
            level = "medium"
        elif overall >= 15:
            level = "low"
        else:
            level = "informational"

        return {
            "overall_risk": overall,
            "risk_level": level,
            "confidence_score": round(min(len(risks) * 5, 95), 1),
            "project_stability": round(max(50, 100 - overall * 0.7), 1),
            "maintainability_risk": round(min(maintainability_risk, 100), 1),
            "architecture_risk": round(min(architecture_risk, 100), 1),
            "dependency_risk": round(min(dependency_risk, 100), 1),
            "security_risk": round(min(security_risk, 100), 1),
            "performance_risk": round(min(performance_risk, 100), 1),
        }

    def _estimate_arch_risk(self, risks) -> float:
        arch_types = {"circular-dependency", "high-coupling", "low-cohesion",
                      "architecture-risk", "entry-point-risk"}
        score = sum(10 if r["severity"] == "critical" else 7 if r["severity"] == "high"
                    else 4 for r in risks if r["type"] in arch_types)
        return min(score, 100)

    def _estimate_dep_risk(self, risks) -> float:
        dep_types = {"circular-dependency", "broken-dependency", "deep-call-chain"}
        score = sum(10 if r["severity"] == "critical" else 7 if r["severity"] == "high"
                    else 4 for r in risks if r["type"] in dep_types)
        return min(score, 100)

    def _estimate_security_risk(self, risks) -> float:
        sec_types = {"security-hotspot", "configuration-risk"}
        score = sum(10 if r["severity"] == "critical" else 7 if r["severity"] == "high"
                    else 4 for r in risks if r["type"] in sec_types)
        return min(score, 100)

    def _estimate_perf_risk(self, risks) -> float:
        perf_types = {"high-complexity", "deep-call-chain", "performance-hotspot",
                      "large-function", "large-class"}
        score = sum(10 if r["severity"] == "critical" else 7 if r["severity"] == "high"
                    else 4 for r in risks if r["type"] in perf_types)
        return min(score, 100)

    def _build_heatmap(self, risks, file_risk_map, module_risk_map,
                        project_analysis) -> list[dict]:
        heatmap: list[dict] = []
        seen = set()

        for fpath, rtypes in file_risk_map.items():
            if fpath in seen:
                continue
            seen.add(fpath)
            max_sev = max(
                (r["severity"] for r in risks if fpath in r.get("affected_files", [])),
                key=lambda s: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(s, 0),
                default="low"
            )
            total = len(rtypes)
            heatmap.append({
                "name": os.path.basename(fpath),
                "path": fpath,
                "category": "file",
                "risk_score": min(total * 20, 100),
                "risk_level": max_sev,
                "top_risks": list(set(rtypes)),
            })

        if project_analysis:
            modules = project_analysis.get("detected_modules", [])
            for mod in modules:
                if mod in seen:
                    continue
                seen.add(mod)
                mod_risks = module_risk_map.get(mod, [])
                score = len(mod_risks) * 15
                heatmap.append({
                    "name": mod,
                    "path": mod,
                    "category": "module",
                    "risk_score": min(score, 100),
                    "risk_level": "high" if score > 50 else "medium" if score > 20 else "low",
                    "top_risks": list(set(mod_risks)),
                })

        heatmap.sort(key=lambda h: h["risk_score"], reverse=True)
        return heatmap

    def _generate_summary(self, risks, risk_score, project_analysis) -> dict:
        critical = [r for r in risks if r["severity"] == "critical"]
        high = [r for r in risks if r["severity"] == "high"]
        medium = [r for r in risks if r["severity"] == "medium"]
        low = [r for r in risks if r["severity"] == "low"]

        by_type: dict[str, list[dict]] = defaultdict(list)
        for r in risks:
            by_type[r["type"]].append(r)

        if by_type:
            highest_type = max(by_type, key=lambda t: len(by_type[t]))
            highest_area = highest_type.replace("-", " ").title()
        else:
            highest_area = "None"

        proj_type = (project_analysis or {}).get("project_type", "project")
        total = len(risks)

        lines = []
        if critical:
            lines.append(f"{proj_type.title()} has {len(critical)} critical risk(s) requiring immediate attention.")
        if high:
            lines.append(f"Found {len(high)} high-risk issues that should be addressed before production deployment.")
        if medium:
            lines.append(f"{len(medium)} medium-risk items identified for the next development sprint.")
        if not lines:
            lines.append(f"{proj_type.title()} has a clean risk profile with {total} low-level item(s).")

        level = risk_score.get("risk_level", "unknown")
        score = risk_score.get("overall_risk", 0)
        lines.append(f"Overall risk level is '{level}' with a score of {score}/100.")
        lines.append(f"Highest risk area: {highest_area}.")

        if critical:
            lines.append("Immediate action recommended on critical issues before proceeding with feature development.")
        elif score > 50:
            lines.append("Recommended to address high-risk items before starting new feature work.")

        prioritized = []
        for r in sorted(risks, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 4)):
            prioritized.append(f"[{r['severity'].upper()}] {r['name']}: {r['recommendation']}")

        return {
            "highest_risk_module": highest_area,
            "highest_risk_area": highest_area,
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "low_count": len(low),
            "summary_text": " ".join(lines),
            "prioritized_recommendations": prioritized[:20],
        }
