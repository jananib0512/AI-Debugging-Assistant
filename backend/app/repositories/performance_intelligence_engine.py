import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


INNER_LOOP_PATTERNS: list[tuple[str, str, str]] = [
    ("nested_for", r'for\s+\w+\s+in\s+\w+[\s\S]*?for\s+\w+\s+in\s+\w+', "Deep Nested Loop"),
    ("nested_while", r'while\s+[^:]+:[\s\S]*?while\s+[^:]+:', "Nested While Loop"),
    ("query_in_loop", r'(for|while)\s+[\s\S]{0,200}?(execute|query|find|find_all|select|raw)',
     "Database Query Inside Loop"),
    ("api_in_loop", r'(for|while)\s+[\s\S]{0,200}?(fetch|axios\.get|axios\.post|request|requests\.|http\.|api\.get|api\.post)',
     "API Call Inside Loop"),
    ("sync_io", r'(time\.sleep|read\(|write\(|recv\(|send\(|file\.read|file\.write)\s*\(',
     "Blocking I/O Operation"),
    ("large_list_comp", r'\[[\s\S]{0,200}?for\s+\w+\s+in\s+[\s\S]{0,200}?for\s+\w+\s+in\s+',
     "Large List Comprehension"),
    ("recursive_call", r'def\s+(\w+)[\s\S]*?\1\s*\(',
     "Recursive Function"),
    ("redundant_slice", r'\[\s*:\s*\]|\.copy\s*\(\s*\)|dict\(|list\(|set\(',
     "Unnecessary Data Copy"),
    ("string_concat_loop", r'(for|while)[\s\S]{0,200}?\+\=\s*["\']|concat\s*\(',
     "String Concatenation in Loop"),
]


class PerformanceIntelligenceEngine:

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
        findings = self._detect_all(workspace_path, code_intel, code_quality,
                                     file_analysis, func_class, dep_analysis,
                                     call_graph, semantic, config_intel,
                                     recommendations)
        score = self._compute_score(findings)
        summary = self._generate_summary(findings, score)
        return {
            "performance_score": score,
            "findings": findings,
            "summary": summary,
        }

    def _detect_all(self, workspace_path, code_intel, code_quality,
                     file_analysis, func_class, dep_analysis,
                     call_graph, semantic, config_intel,
                     recommendations) -> list[dict]:
        findings: list[dict] = []

        self._detect_function_performance(func_class, findings)
        self._detect_code_patterns(workspace_path, code_intel, findings)
        self._detect_file_performance(file_analysis, findings)
        self._detect_call_chain_performance(call_graph, findings)
        self._detect_duplicate_computation(code_quality, findings)
        self._detect_database_performance(dep_analysis, findings)
        self._detect_semantic_performance(semantic, findings)
        self._detect_recommendation_performance(recommendations, findings)

        return findings

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

    def _detect_function_performance(self, func_class, findings):
        if not func_class:
            return
        functions = func_class.get("functions", [])
        if isinstance(functions, list):
            for fn in functions:
                name = fn.get("name", "")
                file = fn.get("file", "")
                lines = fn.get("end_line", 0) - fn.get("start_line", 0)
                params = fn.get("parameters", fn.get("params", []))
                if isinstance(params, int):
                    params = []
                num_params = len(params) if isinstance(params, (list, tuple)) else 0

                if lines > 80:
                    findings.append(self._make_finding(
                        f"Very Large Function: {name}", "large-function", "high",
                        [file], [name],
                        cost="High — increases cognitive load and maintenance cost",
                        detail=f"Function spans {lines} lines in {file} — should be broken down",
                        suggestion="Split into smaller helper functions of 15-20 lines each",
                        gain="30-50% readability improvement, easier testing",
                        reduction="40-60% per-function complexity"
                    ))
                elif lines > 40:
                    findings.append(self._make_finding(
                        f"Large Function: {name}", "large-function", "medium",
                        [file], [name],
                        cost="Medium — increased complexity and testing effort",
                        detail=f"Function spans {lines} lines in {file}",
                        suggestion="Extract logical blocks into named functions",
                        gain="20-30% maintainability improvement",
                        reduction="20-40% per-function complexity"
                    ))

                if num_params > 6:
                    findings.append(self._make_finding(
                        f"High Parameter Count: {name}", "large-function", "medium",
                        [file], [name],
                        cost="Medium — high parameter count indicates missing abstraction",
                        detail=f"Function has {num_params} parameters",
                        suggestion="Group related parameters into a configuration object or dataclass",
                        gain="Reduced complexity at call sites",
                        reduction="30-50% parameter complexity"
                    ))

        classes = func_class.get("classes", [])
        if isinstance(classes, list):
            for cls in classes:
                name = cls.get("name", "")
                file = cls.get("file", "")
                methods = cls.get("methods", [])
                if len(methods) > 20:
                    findings.append(self._make_finding(
                        f"Large Class: {name}", "large-object", "high",
                        [file], [],
                        cost="High — large classes violate single responsibility",
                        detail=f"Class has {len(methods)} methods in {file}",
                        suggestion="Split into focused sub-classes by concern",
                        gain="Improved testability and maintainability",
                        reduction="40-50% per-class complexity"
                    ))

    def _detect_code_patterns(self, workspace_path, code_intel, findings):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            for ptype, pattern, label in INNER_LOOP_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    sev = "critical" if ptype in ("query_in_loop", "api_in_loop") else \
                          "high" if ptype in ("nested_for", "nested_while", "string_concat_loop") else "medium"
                    findings.append(self._make_finding(
                        label, ptype, sev,
                        [rel], [],
                        cost="High — multiplies operations linearly with each nesting level" if sev == "critical" else
                             "Medium — affects execution time proportionally",
                        detail=f"Found in {rel} — {len(matches)} occurrence(s)",
                        suggestion=self._suggestion_for(ptype),
                        gain="50-80% performance improvement" if sev == "critical" else "20-40% improvement",
                        reduction="Reduces time complexity by one order of magnitude" if sev == "critical" else
                                  "Moderate complexity reduction"
                    ))

    def _detect_file_performance(self, file_analysis, findings):
        if not file_analysis:
            return
        items = file_analysis if isinstance(file_analysis, list) else file_analysis.get("files", [])
        if isinstance(items, list):
            for f in items:
                fname = f.get("name", "") or f.get("path", "")
                size = f.get("size", f.get("bytes", 0))
                lines = f.get("lines", f.get("line_count", 0))
                if isinstance(size, (int, float)) and size > 500000:
                    findings.append(self._make_finding(
                        f"Large File: {os.path.basename(fname)}", "large-object", "medium",
                        [fname], [],
                        cost=f"Approximately {size / 1024:.0f} KB — affects parsing and loading time",
                        detail=f"File size is {size / 1024:.0f} KB in {fname}",
                        suggestion="Split into smaller files by module concern",
                        gain="30-50% faster parsing and IDE performance",
                        reduction="Reduces per-file memory footprint"
                    ))
                if isinstance(lines, (int, float)) and lines > 500:
                    findings.append(self._make_finding(
                        f"Long File: {os.path.basename(fname)}", "large-object", "low",
                        [fname], [],
                        cost=f"Over {lines} lines — difficult to navigate and maintain",
                        detail=f"File has {lines} lines",
                        suggestion="Break into modules of 200-300 lines maximum",
                        gain="Improved developer productivity",
                        reduction="20-30% navigation overhead"
                    ))

    def _detect_call_chain_performance(self, call_graph, findings):
        if not call_graph:
            return
        flows = call_graph.get("execution_flows", []) if isinstance(call_graph, dict) else []
        if isinstance(flows, list):
            for flow in flows:
                fname = flow.get("name", "Unknown Flow")
                steps = len(flow.get("steps", flow.get("nodes", [])))
                if steps > 15:
                    findings.append(self._make_finding(
                        f"Long Execution Chain: {fname}", "deep-call-chain", "high",
                        detail=f"Execution flow has {steps} steps — high latency and debugging cost",
                        cost="High — each step adds latency and failure points",
                        suggestion="Reduce chain length by merging sequential steps or using async patterns",
                        gain="30-60% latency reduction",
                        reduction="Reduces execution path complexity"
                    ))
                elif steps > 8:
                    findings.append(self._make_finding(
                        f"Moderate Execution Chain: {fname}", "deep-call-chain", "medium",
                        detail=f"Execution flow has {steps} steps",
                        cost="Medium — moderate latency accumulation",
                        suggestion="Consider optimizing the longest path segments",
                        gain="15-30% latency reduction",
                        reduction="Moderate complexity reduction"
                    ))

        nodes = call_graph.get("nodes", []) if isinstance(call_graph, dict) else []
        edges = call_graph.get("edges", []) if isinstance(call_graph, dict) else []
        if isinstance(nodes, list) and isinstance(edges, list) and len(nodes) > 0:
            avg_edges = len(edges) / max(len(nodes), 1)
            if avg_edges > 5:
                findings.append(self._make_finding(
                    "High Call Graph Density", "repeated-computation", "medium",
                    detail=f"Average {round(avg_edges, 1)} edges per node — high interconnectivity",
                    cost="Medium — dense call graphs are harder to trace and optimize",
                    suggestion="Reduce coupling by introducing service interfaces",
                    gain="Improved modularity and testability",
                    reduction="Reduces call graph complexity"
                ))

    def _detect_duplicate_computation(self, code_quality, findings):
        if not code_quality or not isinstance(code_quality, dict):
            return
        issues = code_quality.get("issues", [])
        if isinstance(issues, list):
            dup_issues = [i for i in issues if isinstance(i, dict) and
                          i.get("type", "") in ("duplicate", "redundant", "repeated")]
            for iss in dup_issues[:10]:
                name = iss.get("name", iss.get("title", "Duplicate Computation"))
                sev = iss.get("severity", "medium")
                aff = iss.get("files", []) if isinstance(iss.get("files"), list) else []
                findings.append(self._make_finding(
                    f"Duplicate Computation: {name}", "repeated-computation", sev,
                    aff,
                    cost="Medium — redundant work increases execution time",
                    detail=iss.get("description", iss.get("detail", "Repeated computation detected")),
                    suggestion=iss.get("suggestion", "Extract duplicated logic into shared utility functions"),
                    gain="20-50% reduction in redundant operations",
                    reduction="Eliminates repeated processing"
                ))

        duplications = code_quality.get("duplications", code_quality.get("duplicates", []))
        if isinstance(duplications, list):
            for d in duplications[:10]:
                name = d if isinstance(d, str) else d.get("name", d.get("file", "Duplicate Block"))
                aff = [d] if isinstance(d, str) else [d.get("file", "")]
                sev = "medium" if isinstance(d, str) else d.get("severity", "medium")
                findings.append(self._make_finding(
                    f"Code Duplication: {name}", "repeated-computation", sev,
                    aff,
                    cost="Medium — duplicated code increases maintenance and risks inconsistency",
                    detail=f"Duplicated code block in {name}",
                    suggestion="Extract common logic into a shared function or module",
                    gain="Reduced code size and improved consistency",
                    reduction="Removes redundant code paths"
                ))

    def _detect_database_performance(self, dep_analysis, findings):
        if not dep_analysis:
            return
        imports = dep_analysis.get("imports", dep_analysis.get("total_imports", 0))
        if isinstance(imports, (int, float)) and imports > 200:
            findings.append(self._make_finding(
                "Large Import Footprint", "repeated-computation", "low",
                detail=f"Project has {imports} total imports — may indicate slow startup time",
                cost="Low — increases module loading time",
                suggestion="Use lazy imports for rarely-used modules",
                gain="10-30% faster startup time",
                reduction="Reduces import chain complexity"
            ))

        files = dep_analysis.get("files", [])
        if isinstance(files, list):
            orm_imports = [f for f in files if isinstance(f, dict) and
                           any(kw in f.get("name", "").lower()
                               for kw in ("sqlalchemy", "django.db", "mongoose", "prisma",
                                          "typeorm", "sequelize", "knex"))]
            if len(orm_imports) > 0:
                findings.append(self._make_finding(
                    "ORM/Database Layer Detected", "repeated-query", "low",
                    detail=f"Project uses {len(orm_imports)} ORM/database libraries — review query patterns",
                    cost="Low — ORM overhead is generally acceptable",
                    suggestion="Use select_related/prefetch_related or equivalent to avoid N+1 queries",
                    gain="50-90% reduction in query count with eager loading",
                    reduction="Eliminates N+1 query patterns"
                ))

    def _detect_semantic_performance(self, semantic, findings):
        if not semantic:
            return
        flows = semantic.get("business_flows", [])
        if isinstance(flows, list):
            for flow in flows:
                fname = flow.get("name", "Unknown")
                steps = flow.get("steps", flow.get("components", []))
                if isinstance(steps, (list, tuple)) and len(steps) > 12:
                    findings.append(self._make_finding(
                        f"Long Business Flow: {fname}", "deep-call-chain", "high",
                        detail=f"Business flow '{fname}' has {len(steps)} stages",
                        cost="High — long business flows are hard to optimize and monitor",
                        suggestion="Break into smaller orchestrations or use event-driven architecture",
                        gain="30-50% reduction in end-to-end latency",
                        reduction="Simplifies flow logic"
                    ))

        score = semantic.get("understanding_score", {})
        if isinstance(score, dict):
            da = score.get("data_flow", 50)
            if isinstance(da, (int, float)) and da < 30:
                findings.append(self._make_finding(
                    "Poor Data Flow Understanding", "repeated-computation", "medium",
                    detail=f"Data flow understanding score is {da}% — inefficient data pipelines",
                    cost="Medium — unclear data flow leads to redundant processing",
                    suggestion="Audit data transformation pipelines for redundant steps",
                    gain="20-40% reduction in data processing overhead",
                    reduction="Streamlines data flow"
                ))

    def _detect_recommendation_performance(self, recommendations, findings):
        if not recommendations or not isinstance(recommendations, dict):
            return
        recs = recommendations.get("recommendations", [])
        if isinstance(recs, list):
            perf_recs = [r for r in recs if isinstance(r, dict) and
                         r.get("category", r.get("type", "")) in ("performance", "optimization")]
            for r in perf_recs[:10]:
                findings.append(self._make_finding(
                    r.get("title", r.get("name", "Performance Recommendation")),
                    r.get("type", "repeated-computation"),
                    r.get("severity", r.get("priority", "medium")),
                    r.get("affected_files", []),
                    cost=r.get("impact", r.get("cost", "Medium")),
                    detail=r.get("description", r.get("detail", "")),
                    suggestion=r.get("suggestion", r.get("recommendation", "")),
                    gain=r.get("gain", "Moderate performance improvement"),
                    reduction=r.get("reduction", "Moderate complexity reduction")
                ))

    def _make_finding(self, name: str, ftype: str, severity: str = "medium",
                      files: list[str] | None = None,
                      functions: list[str] | None = None,
                      cost: str = "",
                      detail: str = "",
                      suggestion: str = "",
                      gain: str = "",
                      reduction: str = "") -> dict:
        return {
            "name": name,
            "type": ftype,
            "severity": severity,
            "estimated_cost": cost,
            "affected_files": files or [],
            "affected_functions": functions or [],
            "detail": detail,
            "optimization_suggestion": suggestion,
            "estimated_gain": gain,
            "complexity_reduction": reduction,
        }

    def _suggestion_for(self, ptype: str) -> str:
        suggestions = {
            "nested_for": "Flatten nested loops or use vectorized operations (NumPy, map, comprehensions)",
            "nested_while": "Replace nested while loops with for loops or recursion with memoization",
            "query_in_loop": "Move database queries outside loops; use batch queries or eager loading",
            "api_in_loop": "Replace sequential API calls with Promise.all, asyncio.gather, or batch endpoints",
            "sync_io": "Use async I/O or thread pools for blocking operations",
            "large_list_comp": "Use generator expressions instead of list comprehensions for large datasets",
            "recursive_call": "Consider iterative solutions or add memoization to avoid stack overflow",
            "redundant_slice": "Avoid unnecessary data copies; use views or references where possible",
            "string_concat_loop": "Use join() or StringBuilder pattern instead of += string concatenation",
        }
        return suggestions.get(ptype, "Review and optimize the detected pattern")

    def _compute_score(self, findings) -> dict:
        total = len(findings)
        sev_weights = {"critical": 10, "high": 7, "medium": 4, "low": 2, "informational": 1}
        weighted = sum(sev_weights.get(f.get("severity", "low"), 1) for f in findings)
        max_possible = total * 10 if total > 0 else 1
        raw_risk = min(weighted / max_possible * 100, 100) if total > 0 else 0

        overall = round(max(0, 100 - raw_risk * 1.1), 1)
        health = round(max(0, overall - 10), 1)
        readiness = round(max(0, 100 - raw_risk * 0.9), 1)
        potential = round(min(raw_risk * 0.8, 100), 1)
        confidence = round(min(len(findings) * 4, 90), 1)

        if raw_risk >= 55:
            level = "critical"
        elif raw_risk >= 38:
            level = "high"
        elif raw_risk >= 20:
            level = "medium"
        elif raw_risk >= 8:
            level = "low"
        else:
            level = "informational"

        return {
            "overall_performance_score": overall,
            "performance_health": health,
            "performance_readiness": readiness,
            "optimization_potential": potential,
            "ai_confidence": confidence,
            "risk_level": level,
        }

    def _generate_summary(self, findings, score) -> dict:
        critical = [f for f in findings if f["severity"] == "critical"]
        high = [f for f in findings if f["severity"] == "high"]
        medium = [f for f in findings if f["severity"] == "medium"]
        low = [f for f in findings if f["severity"] == "low"]

        lines = []
        if critical:
            lines.append(f"Found {len(critical)} critical performance bottleneck(s) requiring immediate optimization.")
        if high:
            lines.append(f"{len(high)} high-impact performance issue(s) identified for the next optimization cycle.")
        if medium:
            lines.append(f"{len(medium)} optimization opportunity (medium) available for upcoming sprints.")

        if findings:
            by_type: dict[str, int] = {}
            for f in findings:
                by_type[f["type"]] = by_type.get(f["type"], 0) + 1
            top_type = max(by_type, key=by_type.get)
            type_labels = {
                "large-function": "Large function",
                "large-object": "Large object/file",
                "nested_for": "Nested loop",
                "query_in_loop": "Query-in-loop",
                "api_in_loop": "API-in-loop",
                "deep-call-chain": "Deep call chain",
                "repeated-computation": "Repeated computation",
                "repeated-query": "Repeated query",
                "sync_io": "Blocking I/O",
                "string_concat_loop": "String concat in loop",
            }
            label = type_labels.get(top_type, top_type.replace("_", " ").title())
            lines.append(f"Most common issue: {label} ({by_type[top_type]} occurrence(s)).")

        score_val = score.get("overall_performance_score", 0)
        pot = score.get("optimization_potential", 0)
        lines.append(f"Performance score: {score_val}/100. Optimization potential: {round(pot)}%.")

        if score_val < 40:
            lines.append("Immediate performance optimization recommended for critical paths.")
        elif score_val < 70:
            lines.append("Performance improvements recommended for high-traffic execution paths.")

        prioritized = []
        for f in sorted(findings, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 4)):
            suggestion = f.get("optimization_suggestion", "")
            gain = f.get("estimated_gain", "")
            line = f"[{f['severity'].upper()}] {f['name']}: {suggestion}"
            if gain:
                line += f" ({gain})"
            prioritized.append(line)

        return {
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "low_count": len(low),
            "summary_text": " ".join(lines),
            "prioritized_recommendations": prioritized[:25],
        }
