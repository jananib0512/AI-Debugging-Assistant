import os
from collections import Counter
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult, ProjectScanner


class ComplexityAnalyzerRepository:
    def __init__(self, scan_result: ProjectScanResult | None = None) -> None:
        self._scan: ProjectScanResult | None = scan_result

    def scan(self, workspace_path: str) -> None:
        scanner = ProjectScanner()
        self._scan = scanner.scan(Path(workspace_path))

    def _ensure_scan(self) -> ProjectScanResult:
        assert self._scan is not None, "call scan() first"
        return self._scan

    def compute_workspace_statistics(self) -> dict:
        scan = self._ensure_scan()
        all_files = scan.all_files
        file_sizes = scan.file_sizes
        all_dirs = scan.all_dirs

        total_files = scan.total_files
        total_folders = scan.total_folders

        largest_file = ""
        largest_file_size = 0
        for f in all_files:
            fsize = file_sizes.get(f, 0)
            if fsize > largest_file_size:
                largest_file_size = fsize
                largest_file = f

        parent_counter: Counter = Counter()
        for f in all_files:
            parent = str(Path(f).parent)
            if parent != ".":
                parent_counter[parent] += 1

        largest_folder = ""
        largest_folder_count = 0
        for folder, count in parent_counter.most_common(5):
            if count > largest_folder_count:
                largest_folder_count = count
                largest_folder = folder

        folder_depths: list[int] = []
        for d in all_dirs:
            depth = len(Path(d).parts)
            folder_depths.append(depth)

        avg_depth = 0.0
        max_depth = 0
        if folder_depths:
            avg_depth = sum(folder_depths) / len(folder_depths)
            max_depth = max(folder_depths)

        avg_file_size = 0
        if total_files > 0:
            avg_file_size = scan.workspace_size // total_files

        return {
            "total_files": total_files,
            "total_folders": total_folders,
            "source_files": scan.source_file_count,
            "config_files": scan.config_file_count,
            "doc_files": scan.doc_file_count,
            "image_files": scan.image_file_count,
            "video_files": scan.video_file_count,
            "archive_files": scan.archive_file_count,
            "template_files": scan.template_file_count,
            "script_files": scan.script_file_count,
            "asset_files": scan.asset_file_count,
            "largest_file": largest_file,
            "largest_file_size": largest_file_size,
            "largest_folder": largest_folder,
            "largest_folder_count": largest_folder_count,
            "average_file_size": avg_file_size,
            "average_folder_depth": round(avg_depth, 2),
            "max_folder_depth": max_depth,
            "workspace_size": scan.workspace_size,
        }

    def compute_language_distribution(self) -> list[dict]:
        scan = self._ensure_scan()
        if not scan.language_counts:
            return []

        total_source = sum(scan.language_counts.values())
        if total_source == 0:
            return []

        dist: list[dict] = []
        for lang, count in sorted(
            scan.language_counts.items(), key=lambda x: x[1], reverse=True,
        ):
            dist.append({
                "language": lang,
                "file_count": count,
                "percentage": round((count / total_source) * 100, 1),
            })
        return dist

    def compute_project_scale(self) -> dict:
        scan = self._ensure_scan()
        total = scan.total_files
        folders = scan.total_folders
        lang_count = len(scan.language_counts)
        source_count = scan.source_file_count
        size_mb = scan.workspace_size / (1024 * 1024)

        if total >= 50000 or size_mb >= 2000:
            return {"scale": "Enterprise", "confidence": 95}
        if total >= 10000 or size_mb >= 500 or folders >= 500:
            return {"scale": "Enterprise", "confidence": 80}

        score = 0
        if total >= 2000:
            score += 40
        elif total >= 500:
            score += 25
        elif total >= 100:
            score += 10
        else:
            score += 5

        if folders >= 100:
            score += 20
        elif folders >= 30:
            score += 15
        elif folders >= 10:
            score += 10
        else:
            score += 5

        if lang_count >= 5:
            score += 20
        elif lang_count >= 3:
            score += 15
        else:
            score += 5

        if source_count >= 1000:
            score += 20
        elif source_count >= 200:
            score += 15
        elif source_count >= 50:
            score += 10
        else:
            score += 5

        if score >= 85:
            return {"scale": "Large", "confidence": min(score, 95)}
        elif score >= 55:
            return {"scale": "Medium", "confidence": score}
        elif score >= 30:
            return {"scale": "Small", "confidence": score}
        else:
            return {"scale": "Tiny", "confidence": max(score, 10)}

    def compute_complexity_score(self) -> dict:
        scan = self._ensure_scan()
        factors: dict[str, int] = {}

        folder_depth = self._folder_depth_score(scan)
        factors["folder_depth"] = folder_depth

        module_count = len(scan.all_dir_names)
        module_score = min(module_count, 25)
        factors["module_count"] = module_score

        tech_count = len(scan.language_counts)
        tech_score = min(tech_count * 5, 20)
        factors["technology_count"] = tech_score

        config_score = min(scan.config_file_count * 5, 15)
        factors["configuration_count"] = config_score

        file_count = scan.total_files
        size_score = 0
        if file_count >= 5000:
            size_score = 20
        elif file_count >= 1000:
            size_score = 15
        elif file_count >= 200:
            size_score = 10
        elif file_count >= 50:
            size_score = 5
        factors["project_size"] = size_score

        lang_diversity = len(scan.language_counts)
        diversity_score = min(lang_diversity * 3, 10)
        factors["language_diversity"] = diversity_score

        total = sum(factors.values())
        total = min(total, 100)

        if total >= 80:
            level = "Very High"
        elif total >= 60:
            level = "High"
        elif total >= 40:
            level = "Medium"
        elif total >= 20:
            level = "Low"
        else:
            level = "Very Low"

        return {"score": total, "level": level, "factors": factors}

    @staticmethod
    def _folder_depth_score(scan: ProjectScanResult) -> int:
        depths: list[int] = []
        for d in scan.all_dirs:
            depths.append(len(Path(d).parts))
        if not depths:
            return 0
        avg = sum(depths) / len(depths)
        if avg >= 6:
            return 20
        elif avg >= 4:
            return 15
        elif avg >= 3:
            return 10
        elif avg >= 2:
            return 5
        return 2

    def compute_organization(self) -> dict:
        scan = self._ensure_scan()
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        known_dirs = all_dir_names | root_dirs_lower

        score = 0

        known_layer_dirs = {
            "controllers", "services", "repositories", "models", "views",
            "templates", "components", "pages", "api", "routes", "domain",
            "application", "infrastructure", "config", "utils", "helpers",
            "tests", "docs", "scripts", "assets", "public",
        }
        organized = [d for d in known_dirs if d in known_layer_dirs]
        if len(organized) >= 5:
            score += 25
        elif len(organized) >= 3:
            score += 15
        elif len(organized) >= 1:
            score += 5

        naming_styles = set()
        for d in known_dirs:
            if "_" in d:
                naming_styles.add("snake")
            if "-" in d:
                naming_styles.add("kebab")
            if d.islower() and d.isalpha():
                naming_styles.add("lower")
        if len(naming_styles) <= 2:
            score += 20
        elif len(naming_styles) <= 3:
            score += 10

        if scan.config_file_count >= 2:
            score += 20
        elif scan.config_file_count >= 1:
            score += 10

        depths: list[int] = []
        for d in scan.all_dirs:
            depths.append(len(Path(d).parts))
        max_depth = max(depths) if depths else 0
        if max_depth <= 4:
            score += 20
        elif max_depth <= 6:
            score += 15
        elif max_depth <= 8:
            score += 10
        else:
            score += 5

        if score >= 70:
            level = "Excellent"
        elif score >= 50:
            level = "Good"
        elif score >= 30:
            level = "Fair"
        else:
            level = "Poor"

        return {"level": level, "score": score}

    def compute_maintainability(self) -> dict:
        scan = self._ensure_scan()
        factors: dict[str, int] = {}

        org = self.compute_organization()
        factors["folder_organization"] = org["score"] // 2

        config_score = min(scan.config_file_count * 5, 20)
        factors["configuration_quality"] = config_score

        doc_score = 0
        if scan.config_flags.get("readme"):
            doc_score += 10
        if scan.has_docs:
            doc_score += 5
        factors["documentation"] = doc_score

        has_src_or_app = scan.has_src_or_app
        has_test = scan.has_tests
        struct_score = 0
        if has_src_or_app:
            struct_score += 10
        if has_test:
            struct_score += 10
        factors["project_structure"] = struct_score

        module_org = min(len(scan.all_dir_names), 10)
        factors["module_organization"] = module_org

        total = sum(factors.values())
        total = min(total, 100)

        if total >= 70:
            level = "High"
        elif total >= 40:
            level = "Medium"
        else:
            level = "Low"

        return {"score": total, "level": level, "factors": factors}

    def compute_documentation_coverage(self) -> dict:
        scan = self._ensure_scan()
        flags = scan.config_flags
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        root_files_lower = {f.lower() for f in scan.root_files}

        has_readme = flags.get("readme", False)
        has_license = any(
            f.startswith("license") or f == "license.txt" or f == "license.md"
            for f in root_files_lower
        ) or "license" in root_files_lower
        has_changelog = any(
            f.startswith("changelog") or f.startswith("change_log") or f == "history.md"
            for f in root_files_lower
        )
        has_api_docs = any(
            d in all_dir_names for d in ["docs", "documentation", "apidocs", "api-docs",
                                           "swagger", "openapi"]
        ) or any(
            f in root_files_lower for f in ["swagger.json", "swagger.yaml", "openapi.json",
                                              "openapi.yaml", "api.md", "api-docs.md"]
        )

        covered = sum([has_readme, has_license, has_changelog, has_api_docs])
        coverage = round((covered / 4) * 100, 1)

        return {
            "coverage_percentage": coverage,
            "has_readme": has_readme,
            "has_license": has_license,
            "has_changelog": has_changelog,
            "has_api_docs": has_api_docs,
        }

    def compute_build_readiness(self) -> dict:
        scan = self._ensure_scan()
        reasons: list[str] = []
        score = 0

        has_entry = scan.has_src_or_app or len(scan.root_files) > 0
        if has_entry:
            score += 20
        else:
            reasons.append("No clear entry point detected")

        config_count = scan.config_file_count
        if config_count >= 3:
            score += 25
            reasons.append("Multiple configuration files found")
        elif config_count >= 1:
            score += 15
            reasons.append("Configuration files found")
        else:
            reasons.append("No configuration files found")

        has_deps = bool(scan.requirements_txt_deps) or bool(scan.package_json)
        if has_deps:
            score += 25
            reasons.append("Dependencies declared")
        else:
            reasons.append("No dependency declarations found")

        has_framework = bool(scan.python_imports) or bool(scan.js_imports)
        if has_framework:
            score += 20
            reasons.append("Framework/libraries detected")
        else:
            reasons.append("No frameworks detected")

        if scan.dockerfile_content:
            score += 10
            reasons.append("Dockerfile present")

        if score >= 80:
            status = "Ready"
        elif score >= 50:
            status = "Partially Ready"
        elif score >= 20:
            status = "Needs Configuration"
        else:
            status = "Not Ready"

        return {"status": status, "score": score, "reasons": reasons}

    def compute_performance_estimate(self) -> dict:
        scan = self._ensure_scan()
        total = scan.total_files

        if total >= 100000:
            scan_time = "> 30s"
            analysis_time = "5-10s"
            impact = "High"
        elif total >= 50000:
            scan_time = "15-30s"
            analysis_time = "3-5s"
            impact = "High"
        elif total >= 10000:
            scan_time = "5-15s"
            analysis_time = "1-3s"
            impact = "Medium"
        elif total >= 1000:
            scan_time = "1-5s"
            analysis_time = "< 1s"
            impact = "Low"
        else:
            scan_time = "< 1s"
            analysis_time = "< 1s"
            impact = "Very Low"

        return {
            "expected_analysis_time": analysis_time,
            "workspace_scan_time": scan_time,
            "complexity_impact": impact,
        }
