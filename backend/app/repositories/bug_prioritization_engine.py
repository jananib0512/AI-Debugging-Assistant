import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from app.repositories.syntax_detection_engine import SyntaxDetectionEngine
from app.repositories.static_code_analysis_engine import StaticCodeAnalysisEngine
from app.repositories.dependency_detection_engine import DependencyDetectionEngine
from app.repositories.runtime_detection_engine import RuntimeDetectionEngine
from app.repositories.security_detection_engine import SecurityDetectionEngine
from app.repositories.performance_detection_engine import PerformanceDetectionEngine
from app.repositories.architecture_detection_engine import ArchitectureDetectionEngine

SEVERITY_WEIGHTS = {"Critical": 1000, "High": 500, "Medium": 200, "Low": 50}
ENGINE_NAMES = {
    "syntax": SyntaxDetectionEngine,
    "static": StaticCodeAnalysisEngine,
    "dependency": DependencyDetectionEngine,
    "runtime": RuntimeDetectionEngine,
    "security": SecurityDetectionEngine,
    "performance": PerformanceDetectionEngine,
    "architecture": ArchitectureDetectionEngine,
}


class BugPrioritizationEngine:

    def analyze(self, workspace_path: Path | None = None) -> dict:
        if not workspace_path or not workspace_path.exists():
            return self._empty_result()

        all_issues: list[dict] = []
        file_engine_map: dict[str, set[str]] = defaultdict(set)

        for engine_name, engine_cls in ENGINE_NAMES.items():
            engine = engine_cls()
            result = engine.analyze(workspace_path)
            for file_result in result.get("results", []):
                fp = file_result.get("file_path", "")
                for issue in file_result.get("errors", []):
                    issue["source_engine"] = engine_name
                    score = self._calc_priority(issue)
                    issue["priority_score"] = score
                    issue["cross_cutting_categories"] = []
                    all_issues.append(issue)
                    file_engine_map[fp].add(engine_name)

        for issue in all_issues:
            fp = issue.get("affected_file", "")
            engines_in_file = file_engine_map.get(fp, set())
            other_engines = [e for e in engines_in_file if e != issue.get("source_engine")]
            issue["cross_cutting_categories"] = other_engines
            bonus = len(other_engines) * 200
            issue["priority_score"] = round(issue["priority_score"] + bonus, 1)

        all_issues.sort(key=lambda x: x["priority_score"], reverse=True)

        file_groups: dict[str, dict] = {}
        for issue in all_issues:
            fp = issue.get("affected_file", "")
            if fp not in file_groups:
                file_groups[fp] = {
                    "file_path": fp,
                    "language": issue.get("language", ""),
                    "total_issues": 0,
                    "avg_priority": 0.0,
                    "max_severity": "Low",
                    "issues": [],
                }
            g = file_groups[fp]
            g["issues"].append(issue)
            g["total_issues"] += 1
            sev = issue.get("severity", "Low")
            sev_order = ["Critical", "High", "Medium", "Low"]
            if sev_order.index(sev) < sev_order.index(g["max_severity"]):
                g["max_severity"] = sev

        for g in file_groups.values():
            scores = [i["priority_score"] for i in g["issues"]]
            g["avg_priority"] = round(sum(scores) / len(scores), 1) if scores else 0.0

        groups_sorted = sorted(file_groups.values(), key=lambda g: g["avg_priority"], reverse=True)

        recs = self._generate_recommendations(all_issues, file_groups)

        critical = sum(1 for i in all_issues if i["severity"] == "Critical")
        high = sum(1 for i in all_issues if i["severity"] == "High")
        medium = sum(1 for i in all_issues if i["severity"] == "Medium")
        low = sum(1 for i in all_issues if i["severity"] == "Low")

        return {
            "session_id": uuid.uuid4().hex,
            "status": "completed",
            "total_issues": len(all_issues),
            "total_files_affected": len(file_groups),
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "prioritized_issues": all_issues,
            "file_groups": groups_sorted,
            "ai_recommendations": recs,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _calc_priority(self, issue: dict) -> float:
        sev = issue.get("severity", "Low")
        weight = SEVERITY_WEIGHTS.get(sev, 50)
        conf = issue.get("confidence", 50)
        return round(float(weight + conf), 1)

    def _generate_recommendations(self, issues: list[dict], file_groups: dict) -> list[str]:
        recs: list[str] = []

        critical = [i for i in issues if i["severity"] == "Critical"]
        high = [i for i in issues if i["severity"] == "High"]

        if critical:
            top_files = list(set(i.get("affected_file", "") for i in critical[:5]))
            recs.append(
                f"Immediately address {len(critical)} Critical issue(s) in {len(top_files)} file(s): "
                f"{', '.join(top_files[:3])}{'...' if len(top_files) > 3 else ''}."
            )

        if high:
            high_files = list(set(i.get("affected_file", "") for i in high[:5]))
            recs.append(
                f"Resolve {len(high)} High severity issue(s) across {len(high_files)} file(s) "
                f"after addressing critical items."
            )

        cross_cutting = [i for i in issues if len(i.get("cross_cutting_categories", [])) > 0]
        cross_cutting.sort(key=lambda x: x["priority_score"], reverse=True)
        if cross_cutting:
            top_cc = cross_cutting[0]
            fp = top_cc.get("affected_file", "")
            cats = top_cc.get("cross_cutting_categories", [])
            src = top_cc.get("source_engine", "")
            recs.append(
                f"File '{fp}' has cross-cutting issues ({src} + {', '.join(cats[:3])}). "
                f"Prioritize fixes here as they affect multiple quality dimensions."
            )

        file_with_most = max(file_groups.values(), key=lambda g: g["total_issues"]) if file_groups else None
        if file_with_most and file_with_most["total_issues"] > 2:
            recs.append(
                f"'{file_with_most['file_path']}' has {file_with_most['total_issues']} issues "
                f"(avg priority {file_with_most['avg_priority']}). Consider refactoring this file."
            )

        if not recs:
            recs.append("No issues detected — the project is in good shape.")
        elif len(critical) == 0 and len(high) == 0:
            recs.append("No critical or high severity issues. Focus on medium/low items for incremental improvement.")

        return recs[:5]

    def _empty_result(self) -> dict:
        return {
            "session_id": uuid.uuid4().hex,
            "status": "unavailable",
            "total_issues": 0, "total_files_affected": 0,
            "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0,
            "prioritized_issues": [], "file_groups": [], "ai_recommendations": [],
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
