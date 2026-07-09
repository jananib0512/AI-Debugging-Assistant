from __future__ import annotations

from pathlib import Path
from typing import Any


class AiEngineeringReadinessEngine:

    def analyze(
        self,
        workspace_path: Path | None = None,
        project_analysis: dict | None = None,
        code_intel: dict | None = None,
        code_quality: dict | None = None,
        file_analysis: dict | None = None,
        dep_analysis: dict | None = None,
        call_graph: dict | None = None,
        semantic: dict | None = None,
        config_intel: dict | None = None,
        recommendations: dict | None = None,
        security_intel: dict | None = None,
        performance_intel: dict | None = None,
        maintainability_intel: dict | None = None,
        documentation_intel: dict | None = None,
        test_intel: dict | None = None,
        production_intel: dict | None = None,
    ) -> dict:
        findings: list[dict] = []

        health = self._compute_project_health(
            project_analysis, code_quality, dep_analysis, security_intel,
            performance_intel, maintainability_intel, documentation_intel,
            test_intel, production_intel, semantic, code_intel,
        )
        capabilities = self._evaluate_capabilities(
            health, code_intel, test_intel, security_intel, production_intel,
            dep_analysis, code_quality, documentation_intel, maintainability_intel,
        )
        score = self._compute_engineering_score(health, capabilities)
        repair = self._estimate_repair_readiness(
            code_intel, file_analysis, dep_analysis, test_intel,
        )
        roadmap = self._generate_roadmap(score, capabilities, health)
        findings = self._generate_findings(health, capabilities, score)

        ai_summary_lines = []
        ai_summary_lines.append(self._generate_ai_summary(score, health, capabilities, repair))

        summary = {
            "summary_text": " ".join(ai_summary_lines),
            "capabilities_ready": sum(1 for c in capabilities if c.get("score", 0) >= 70),
            "capabilities_total": 7,
            "critical_findings": len([f for f in findings if f.get("severity") == "critical"]),
            "high_findings": len([f for f in findings if f.get("severity") == "high"]),
            "prioritized_recommendations": [
                f"[{f['severity'].upper()}] {f['name']}: {f['recommendation']}"
                for f in sorted(
                    findings,
                    key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
                        x.get("severity", "low"), 4
                    ),
                )[:15]
            ],
        }

        return {
            "engineering_score": score,
            "capabilities": capabilities,
            "project_health": health,
            "findings": findings,
            "repair_readiness": repair,
            "roadmap": roadmap,
            "summary": summary,
        }

    def _compute_project_health(
        self, project_analysis, code_quality, dep_analysis, security_intel,
        performance_intel, maintainability_intel, documentation_intel,
        test_intel, production_intel, semantic, code_intel,
    ) -> dict:
        arch_health = 50.0
        if project_analysis:
            arch = project_analysis.get("architecture", "")
            if arch and arch.lower() not in ("unknown", "none"):
                arch_health = 75.0
            eps = project_analysis.get("entry_points", [])
            if isinstance(eps, list) and len(eps) > 0:
                arch_health = min(100, arch_health + 10)
            mods = project_analysis.get("detected_modules", [])
            if isinstance(mods, list) and len(mods) > 0:
                arch_health = min(100, arch_health + 5)
        if semantic:
            understanding = semantic.get("understanding_score", {})
            if isinstance(understanding, dict):
                arch_val = understanding.get("architecture", understanding.get("overall", 50))
                if isinstance(arch_val, (int, float)):
                    arch_health = (arch_health + arch_val) / 2

        code_health = 50.0
        if code_quality:
            qs = code_quality.get("overall_score", {})
            if isinstance(qs, dict):
                score_val = qs.get("score", qs.get("overall", 50))
                if isinstance(score_val, (int, float)):
                    code_health = score_val
            counts = code_quality.get("severity_counts", {})
            if isinstance(counts, dict):
                critical = counts.get("critical", 0)
                high = counts.get("high", 0)
                if isinstance(critical, (int, float)) and critical > 5:
                    code_health = max(0, code_health - 15)
                if isinstance(high, (int, float)) and high > 10:
                    code_health = max(0, code_health - 10)

        dep_health = 50.0
        if dep_analysis:
            metrics = dep_analysis.get("metrics", dep_analysis.get("summary", {}))
            if isinstance(metrics, dict):
                coupling = metrics.get("coupling_score", metrics.get("coupling", 50))
                if isinstance(coupling, (int, float)):
                    dep_health = max(0, 100 - coupling)
                broken = metrics.get("broken_dependencies", metrics.get("broken", 0))
                if isinstance(broken, (int, float)) and broken > 0:
                    dep_health = max(0, dep_health - broken * 10)
                circular = metrics.get("circular_dependencies", metrics.get("circular", 0))
                if isinstance(circular, (int, float)) and circular > 0:
                    dep_health = max(0, dep_health - circular * 5)

        sec_health = 50.0
        if security_intel:
            ss = security_intel.get("security_score", {})
            if isinstance(ss, dict):
                sec_health = ss.get("overall_security_score", ss.get("security_health", 50))
                if isinstance(sec_health, (int, float)):
                    pass
                else:
                    sec_health = 50
            s_findings = security_intel.get("findings", [])
            if isinstance(s_findings, list):
                critical = [f for f in s_findings if isinstance(f, dict) and f.get("severity") == "critical"]
                high = [f for f in s_findings if isinstance(f, dict) and f.get("severity") == "high"]
                if len(critical) > 0:
                    sec_health = max(0, sec_health - len(critical) * 8)
                if len(high) > 2:
                    sec_health = max(0, sec_health - 5)

        perf_health = 50.0
        if performance_intel:
            ps = performance_intel.get("performance_score", {})
            if isinstance(ps, dict):
                perf_health = ps.get("overall_performance_score", ps.get("performance_score", 50))
                if not isinstance(perf_health, (int, float)):
                    perf_health = 50

        maint_health = 50.0
        if maintainability_intel:
            ms = maintainability_intel.get("maintainability_score", {})
            if isinstance(ms, dict):
                maint_health = ms.get("overall_maintainability_score", ms.get("maintainability_score", 50))
                if not isinstance(maint_health, (int, float)):
                    maint_health = 50

        doc_health = 50.0
        if documentation_intel:
            ds = documentation_intel.get("documentation_score", documentation_intel.get("score", {}))
            if isinstance(ds, dict):
                doc_health = ds.get("overall_documentation_score", ds.get("overall", 50))
                if not isinstance(doc_health, (int, float)):
                    doc_health = 50

        test_health = 50.0
        if test_intel:
            ts = test_intel.get("test_score", {})
            if isinstance(ts, dict):
                test_health = ts.get("overall_test_score", ts.get("test_score", 50))
                if not isinstance(test_health, (int, float)):
                    test_health = 50

        prod_health = 50.0
        if production_intel:
            ps_val = production_intel.get("production_score", {})
            if isinstance(ps_val, dict):
                prod_health = ps_val.get("overall_production_score", 50)
                if not isinstance(prod_health, (int, float)):
                    prod_health = 50

        return {
            "architecture_health": round(arch_health, 1),
            "code_health": round(code_health, 1),
            "dependency_health": round(dep_health, 1),
            "security_health": round(sec_health, 1),
            "performance_health": round(perf_health, 1),
            "maintainability_health": round(maint_health, 1),
            "documentation_health": round(doc_health, 1),
            "testing_health": round(test_health, 1),
            "production_health": round(prod_health, 1),
        }

    def _evaluate_capabilities(self, health: dict, code_intel, test_intel,
                                security_intel, production_intel, dep_analysis,
                                code_quality, documentation_intel,
                                maintainability_intel) -> list[dict]:
        cap = []

        bug_detection_score = (
            health.get("code_health", 50) * 0.35 +
            health.get("dependency_health", 50) * 0.20 +
            health.get("architecture_health", 50) * 0.20 +
            health.get("security_health", 50) * 0.15 +
            health.get("performance_health", 50) * 0.10
        )
        bug_reqs = []
        if health.get("code_health", 50) < 60:
            bug_reqs.append("Improve code quality score above 60")
        if health.get("dependency_health", 50) < 60:
            bug_reqs.append("Resolve dependency issues")
        if code_quality:
            counts = code_quality.get("severity_counts", {})
            if isinstance(counts, dict) and counts.get("critical", 0) > 0:
                bug_reqs.append("Fix critical code quality issues")
        cap.append(self._make_capability(
            "Bug Detection Readiness", bug_detection_score,
            "Ability to automatically detect bugs and defects in the codebase",
            bug_reqs,
        ))

        root_cause_score = (
            health.get("architecture_health", 50) * 0.30 +
            health.get("code_health", 50) * 0.20 +
            health.get("maintainability_health", 50) * 0.20 +
            health.get("documentation_health", 50) * 0.15 +
            health.get("performance_health", 50) * 0.15
        )
        rc_reqs = []
        if health.get("architecture_health", 50) < 60:
            rc_reqs.append("Improve architecture clarity")
        if health.get("documentation_health", 50) < 50:
            rc_reqs.append("Improve documentation coverage")
        cap.append(self._make_capability(
            "Root Cause Readiness", root_cause_score,
            "Ability to trace issues to their root cause through code analysis",
            rc_reqs,
        ))

        auto_refactor_score = (
            health.get("code_health", 50) * 0.30 +
            health.get("maintainability_health", 50) * 0.25 +
            health.get("architecture_health", 50) * 0.20 +
            health.get("testing_health", 50) * 0.15 +
            health.get("documentation_health", 50) * 0.10
        )
        ar_reqs = []
        if health.get("testing_health", 50) < 50:
            ar_reqs.append("Increase test coverage to validate refactoring")
        if health.get("code_health", 50) < 50:
            ar_reqs.append("Improve code quality baseline")
        if maintainability_intel:
            td = maintainability_intel.get("technical_debt", {})
            if isinstance(td, dict):
                debt_ratio = td.get("debt_ratio", td.get("ratio", 0))
                if isinstance(debt_ratio, (int, float)) and debt_ratio > 30:
                    ar_reqs.append("Reduce technical debt before automated refactoring")
        cap.append(self._make_capability(
            "Automatic Refactoring Readiness", auto_refactor_score,
            "Ability to automatically refactor code while preserving behavior",
            ar_reqs,
        ))

        auto_repair_score = (
            health.get("code_health", 50) * 0.25 +
            health.get("testing_health", 50) * 0.25 +
            health.get("security_health", 50) * 0.15 +
            health.get("dependency_health", 50) * 0.15 +
            health.get("maintainability_health", 50) * 0.10 +
            health.get("performance_health", 50) * 0.10
        )
        apr_reqs = []
        if health.get("testing_health", 50) < 40:
            apr_reqs.append("Implement comprehensive test suite for repair validation")
        if health.get("security_health", 50) < 50:
            apr_reqs.append("Address security issues before automated repair")
        if dep_analysis:
            metrics = dep_analysis.get("metrics", {})
            if isinstance(metrics, dict):
                broken = metrics.get("broken_dependencies", 0)
                if isinstance(broken, (int, float)) and broken > 0:
                    apr_reqs.append("Fix broken dependencies before automated repair")
        cap.append(self._make_capability(
            "Automatic Repair Readiness", auto_repair_score,
            "Ability to automatically fix bugs and issues in the codebase",
            apr_reqs,
        ))

        auto_test_score = (
            health.get("testing_health", 50) * 0.35 +
            health.get("code_health", 50) * 0.20 +
            health.get("dependency_health", 50) * 0.15 +
            health.get("architecture_health", 50) * 0.15 +
            health.get("documentation_health", 50) * 0.15
        )
        at_reqs = []
        if health.get("testing_health", 50) < 30:
            at_reqs.append("Add initial test files before automatic test generation")
        if health.get("code_health", 50) < 50:
            at_reqs.append("Improve code structure for testability")
        if test_intel:
            summary = test_intel.get("summary", {})
            if isinstance(summary, dict):
                frameworks = summary.get("detected_frameworks", summary.get("frameworks", []))
                if not frameworks:
                    at_reqs.append("Set up a testing framework")
        cap.append(self._make_capability(
            "Automatic Testing Readiness", auto_test_score,
            "Ability to automatically generate and run tests",
            at_reqs,
        ))

        auto_val_score = (
            health.get("code_health", 50) * 0.25 +
            health.get("testing_health", 50) * 0.25 +
            health.get("security_health", 50) * 0.20 +
            health.get("documentation_health", 50) * 0.15 +
            health.get("production_health", 50) * 0.15
        )
        av_reqs = []
        if health.get("testing_health", 50) < 40:
            av_reqs.append("Expand test coverage for validation")
        if health.get("security_health", 50) < 50:
            av_reqs.append("Address security findings for safe validation")
        cap.append(self._make_capability(
            "Automatic Validation Readiness", auto_val_score,
            "Ability to automatically validate code changes and ensure correctness",
            av_reqs,
        ))

        deploy_score = (
            health.get("production_health", 50) * 0.35 +
            health.get("testing_health", 50) * 0.20 +
            health.get("security_health", 50) * 0.15 +
            health.get("code_health", 50) * 0.15 +
            health.get("dependency_health", 50) * 0.15
        )
        dp_reqs = []
        if health.get("production_health", 50) < 50:
            dp_reqs.append("Improve production readiness score")
        dp_reqs.append("Configure CI/CD pipeline for automated deployments")
        cap.append(self._make_capability(
            "Deployment Readiness", deploy_score,
            "Ability to automatically deploy changes to production",
            dp_reqs,
        ))

        return cap

    def _compute_engineering_score(self, health: dict, capabilities: list[dict]) -> dict:
        health_avg = sum(v for v in health.values() if isinstance(v, (int, float))) / max(len(health), 1)
        cap_avg = sum(c.get("score", 0) for c in capabilities) / max(len(capabilities), 1)

        overall = round(health_avg * 0.55 + cap_avg * 0.45, 1)
        readiness = round(health_avg * 0.5 + cap_avg * 0.5, 1)
        ai_conf = round(min(95, health_avg * 0.4 + cap_avg * 0.4 + 15), 1)
        repair = round(
            health.get("testing_health", 50) * 0.30 +
            health.get("code_health", 50) * 0.25 +
            health.get("maintainability_health", 50) * 0.20 +
            health.get("security_health", 50) * 0.15 +
            health.get("documentation_health", 50) * 0.10,
            1,
        )
        auto = round(cap_avg, 1)
        stability = round(
            health.get("dependency_health", 50) * 0.25 +
            health.get("architecture_health", 50) * 0.20 +
            health.get("code_health", 50) * 0.20 +
            health.get("production_health", 50) * 0.20 +
            health.get("performance_health", 50) * 0.15,
            1,
        )

        return {
            "overall_engineering_score": overall,
            "engineering_readiness": readiness,
            "ai_confidence": ai_conf,
            "repair_readiness": repair,
            "automation_readiness": auto,
            "project_stability": stability,
        }

    def _estimate_repair_readiness(self, code_intel, file_analysis, dep_analysis, test_intel) -> dict:
        total_files = 0
        if code_intel:
            summary = code_intel.get("summary", {})
            if isinstance(summary, dict):
                total_files = summary.get("total_files", 0)
        if not total_files and file_analysis:
            if isinstance(file_analysis, dict):
                total_files = file_analysis.get("total_files", 0)

        if total_files == 0:
            return {
                "files_safe_to_modify": 0,
                "high_risk_files": 0,
                "protected_files": 0,
                "configuration_files": 0,
                "core_modules": 0,
                "utility_modules": 0,
            }

        safe = max(0, int(total_files * 0.35))
        high_risk = max(0, int(total_files * 0.15))
        protected = max(0, int(total_files * 0.10))
        config = max(0, int(total_files * 0.08))
        core = max(0, int(total_files * 0.20))
        utility = max(0, int(total_files * 0.12))

        if dep_analysis:
            metrics = dep_analysis.get("metrics", {})
            if isinstance(metrics, dict):
                broken = metrics.get("broken_dependencies", 0)
                if isinstance(broken, (int, float)) and broken > 0:
                    high_risk = min(total_files, high_risk + broken)
                    safe = max(0, safe - int(broken * 0.5))

        if test_intel:
            ts = test_intel.get("test_score", {})
            if isinstance(ts, dict):
                coverage = ts.get("test_coverage", 0)
                if isinstance(coverage, (int, float)) and coverage > 50:
                    safe = min(total_files, safe + int(total_files * 0.1))
                    high_risk = max(0, high_risk - int(total_files * 0.05))

        return {
            "files_safe_to_modify": safe,
            "high_risk_files": min(total_files, high_risk),
            "protected_files": min(total_files, protected),
            "configuration_files": min(total_files, config),
            "core_modules": min(total_files, core),
            "utility_modules": min(total_files, utility),
        }

    def _generate_roadmap(self, score: dict, capabilities: list[dict], health: dict) -> list[dict]:
        stages = [
            {
                "step": 1,
                "name": "Bug Detection",
                "status": self._stage_status(capabilities[0]["score"] if len(capabilities) > 0 else 0),
                "readiness": capabilities[0]["score"] if len(capabilities) > 0 else 0,
                "detail": "Scan the codebase for bugs, vulnerabilities, and code smells using automated analysis tools.",
            },
            {
                "step": 2,
                "name": "Root Cause Analysis",
                "status": self._stage_status(capabilities[1]["score"] if len(capabilities) > 1 else 0),
                "readiness": capabilities[1]["score"] if len(capabilities) > 1 else 0,
                "detail": "Trace detected issues to their root cause through call graph and dependency analysis.",
            },
            {
                "step": 3,
                "name": "Repair Planning",
                "status": self._stage_status(capabilities[3]["score"] if len(capabilities) > 3 else 0),
                "readiness": capabilities[3]["score"] if len(capabilities) > 3 else 0,
                "detail": "Generate repair plans for each identified issue with estimated impact analysis.",
            },
            {
                "step": 4,
                "name": "Code Modification",
                "status": self._stage_status(capabilities[2]["score"] if len(capabilities) > 2 else 0),
                "readiness": capabilities[2]["score"] if len(capabilities) > 2 else 0,
                "detail": "Apply automated code modifications to fix issues while preserving existing behavior.",
            },
            {
                "step": 5,
                "name": "Validation",
                "status": self._stage_status(capabilities[5]["score"] if len(capabilities) > 5 else 0),
                "readiness": capabilities[5]["score"] if len(capabilities) > 5 else 0,
                "detail": "Validate code changes through static analysis, type checking, and linting.",
            },
            {
                "step": 6,
                "name": "Regression Testing",
                "status": self._stage_status(capabilities[4]["score"] if len(capabilities) > 4 else 0),
                "readiness": capabilities[4]["score"] if len(capabilities) > 4 else 0,
                "detail": "Run existing and auto-generated tests to verify no regressions were introduced.",
            },
            {
                "step": 7,
                "name": "Project Packaging",
                "status": self._stage_status(capabilities[6]["score"] if len(capabilities) > 6 else 0),
                "readiness": capabilities[6]["score"] if len(capabilities) > 6 else 0,
                "detail": "Package the modified project with updated configuration and deployment artifacts.",
            },
        ]
        return stages

    def _stage_status(self, score: float) -> str:
        if score >= 70:
            return "ready"
        elif score >= 40:
            return "needs-work"
        return "not-ready"

    def _generate_findings(self, health: dict, capabilities: list[dict], score: dict) -> list[dict]:
        findings: list[dict] = []

        for key, label in [
            ("architecture_health", "Architecture Health"),
            ("code_health", "Code Health"),
            ("dependency_health", "Dependency Health"),
            ("security_health", "Security Health"),
            ("performance_health", "Performance Health"),
            ("maintainability_health", "Maintainability Health"),
            ("documentation_health", "Documentation Health"),
            ("testing_health", "Testing Health"),
            ("production_health", "Production Health"),
        ]:
            val = health.get(key, 50)
            if isinstance(val, (int, float)) and val < 40:
                findings.append(self._make_finding(
                    f"Critical {label} Issue", "health", "critical",
                    detail=f"{label} score is {val}/100 — requires immediate attention before AI engineering can proceed",
                    impact="Blocks automated engineering capabilities that depend on this dimension",
                    recommendation=f"Improve {label.lower()} to at least 60/100 before enabling related automated capabilities",
                ))
            elif isinstance(val, (int, float)) and val < 60:
                findings.append(self._make_finding(
                    f"Low {label}", "health", "high",
                    detail=f"{label} score is {val}/100 — improvements needed for reliable AI engineering",
                    impact="May reduce quality and reliability of automated engineering outputs",
                    recommendation=f"Address issues in {label.lower()} to achieve a score above 60",
                ))

        for cap in capabilities:
            cap_score = cap.get("score", 0)
            if isinstance(cap_score, (int, float)) and cap_score < 40:
                findings.append(self._make_finding(
                    f"{cap['name']} Not Ready", "capability", "medium",
                    detail=f"{cap['name']} score is {cap_score}/100 — automated {cap['name'].lower()} cannot be reliably performed",
                    impact=f"Project is not ready for {cap['name'].lower()}",
                    recommendation=cap.get("requirements", ["Review and address capability requirements"])[0]
                    if cap.get("requirements") else "Address the requirements listed for this capability",
                ))

        overall = score.get("overall_engineering_score", 0)
        if isinstance(overall, (int, float)):
            if overall < 40:
                findings.append(self._make_finding(
                    "Low Overall Engineering Readiness", "readiness", "critical",
                    detail=f"Overall AI engineering score is {overall}/100 — project is not ready for automated software engineering",
                    impact="All automated engineering capabilities will produce unreliable results",
                    recommendation="Focus on improving code quality, testing, and documentation before enabling AI engineering",
                ))
            elif overall < 65:
                findings.append(self._make_finding(
                    "Moderate Engineering Readiness", "readiness", "high",
                    detail=f"Overall AI engineering score is {overall}/100 — some capabilities are viable",
                    impact="Core capabilities may work but quality will be limited",
                    recommendation="Address the lowest-scoring health dimensions to improve overall readiness",
                ))

        return findings

    def _generate_ai_summary(self, score: dict, health: dict, capabilities: list[dict], repair: dict) -> str:
        overall = score.get("overall_engineering_score", 0)
        lines = []

        if overall >= 80:
            lines.append("Project is highly suitable for automatic AI software engineering.")
            lines.append("All core capabilities are viable for automated operations.")
        elif overall >= 60:
            lines.append("Project is moderately suitable for AI software engineering.")
            lines.append("Core capabilities require some improvements before full automation.")
        elif overall >= 40:
            lines.append("Project has limited suitability for AI software engineering.")
            lines.append("Significant improvements required across multiple dimensions.")
        else:
            lines.append("Project is not suitable for AI software engineering in its current state.")
            lines.append("Major foundational improvements are required before automated engineering can begin.")

        for key, label, condition_text in [
            ("architecture_health", "Architecture", "stable." if health.get("architecture_health", 0) >= 60 else "needs improvement."),
            ("code_health", "Code quality", "acceptable." if health.get("code_health", 0) >= 60 else "needs improvement."),
            ("dependency_health", "Dependency health", "acceptable." if health.get("dependency_health", 0) >= 60 else "needs improvement."),
            ("security_health", "Security", "adequate." if health.get("security_health", 0) >= 60 else "requires improvement before automated fixes."),
            ("testing_health", "Testing coverage", "insufficient." if health.get("testing_health", 0) < 50 else "adequate."),
            ("documentation_health", "Documentation", "insufficient." if health.get("documentation_health", 0) < 50 else "adequate."),
        ]:
            val = health.get(key, 50)
            lines.append(f"{label} is {condition_text}" if isinstance(val, (int, float)) else f"{label}: unknown.")

        ready_count = sum(1 for c in capabilities if c.get("score", 0) >= 70)
        total_cap = len(capabilities)
        lines.append(f"Automation readiness: {ready_count}/{total_cap} capabilities are ready for automated operation.")

        safe_files = repair.get("files_safe_to_modify", 0)
        if safe_files > 0:
            lines.append(f"Estimated {safe_files} files are safe for automated modification.")
        high_risk = repair.get("high_risk_files", 0)
        if high_risk > 0:
            lines.append(f"Approximately {high_risk} files are high-risk and should be handled with caution.")

        return " ".join(lines)

    def _make_capability(self, name: str, score: float, detail: str, requirements: list[str]) -> dict:
        status = "ready" if score >= 70 else "needs-work" if score >= 40 else "not-ready"
        return {
            "name": name,
            "score": round(score, 1),
            "status": status,
            "detail": detail,
            "requirements": requirements,
        }

    def _make_finding(
        self, name: str, category: str = "", severity: str = "medium",
        detail: str = "", modules: list[str] | None = None,
        impact: str = "", recommendation: str = "",
    ) -> dict:
        return {
            "name": name,
            "category": category,
            "severity": severity,
            "detail": detail,
            "affected_modules": modules or [],
            "impact": impact,
            "recommendation": recommendation,
        }
