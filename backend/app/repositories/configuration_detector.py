import logging
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult, ProjectScanner

logger = logging.getLogger(__name__)


class ConfigurationDetectorRepository:
    def __init__(self, scan_result: ProjectScanResult | None = None) -> None:
        self._scan: ProjectScanResult | None = scan_result
        self._project_type: str = ""
        self._last_missing: list[dict] = []

    def scan(self, workspace_path: str) -> None:
        scanner = ProjectScanner()
        self._scan = scanner.scan(Path(workspace_path))

    def set_project_context(self, project_type: str, frameworks: list[str] | None = None) -> None:
        self._project_type = project_type

    def _ensure_scan(self) -> ProjectScanResult:
        assert self._scan is not None, "call scan() first"
        return self._scan

    def _detect_project_type(self, scan: ProjectScanResult) -> str:
        top_dirs = {d.lower() for d in scan.root_dirs}
        top_files = {f.lower() for f in scan.root_files}

        has_python = scan.language_counts.get("Python", 0) > 0
        has_js = (scan.language_counts.get("JavaScript", 0) > 0 or scan.language_counts.get("TypeScript", 0) > 0)

        has_django = "django" in scan.python_imports
        has_fastapi = "fastapi" in scan.python_imports
        has_flask = "flask" in scan.python_imports
        has_react = "react" in scan.js_imports

        is_next = has_js and (
            "next.config.js" in top_files or "next.config.mjs" in top_files or "next.config.ts" in top_files
            or "next" in {f.lower() for f in (scan.package_json or {}).get("dependencies", {})}
        )

        has_angular_json = "angular.json" in top_files
        has_vite_config = any(f.startswith("vite.config.") for f in top_files)
        has_backend_dir = bool(top_dirs & {"backend", "server", "api"})
        has_frontend_dir = bool(top_dirs & {"frontend", "client", "ui"})
        has_packages_dir = "packages" in top_dirs
        has_manage_py = "manage.py" in top_files
        has_main_py = "main.py" in top_files
        has_app_py = "app.py" in top_files
        has_go_mod = "go.mod" in top_files
        has_cargo_toml = "cargo.toml" in top_files
        has_package_json = "package.json" in top_files
        has_dockerfile = scan.dockerfile_content is not None
        has_docker_compose = scan.docker_compose_content is not None
        has_k8s = bool(scan.all_dir_names & {"k8s", "kubernetes", "manifests", "helm", "chart"})
        has_notebooks = any(f.endswith(".ipynb") for f in scan.all_files)
        has_multiple_services = len([d for d in top_dirs if "service" in d]) >= 2

        ml_deps = {"tensorflow", "torch", "sklearn", "transformers", "keras"}
        has_ml = bool(scan.python_imports & ml_deps) or any(
            any(m in d for m in ml_deps) for d in scan.requirements_txt_deps
        )
        ds_dirs = top_dirs & {"notebooks", "data", "datasets", "analysis"}
        has_ds = has_notebooks or bool(ds_dirs)

        if has_packages_dir and not has_frontend_dir and not has_backend_dir:
            return "Monorepo"
        if has_docker_compose and (has_multiple_services or has_k8s):
            return "Microservice"
        if has_frontend_dir and has_backend_dir:
            return "Full Stack"
        if is_next:
            return "Next.js Application"
        if has_angular_json:
            return "Angular Application"
        if has_vite_config and has_react:
            return "React Application"
        if has_django or has_manage_py:
            return "Django Application"
        if has_fastapi:
            return "FastAPI Application"
        if has_flask or has_app_py:
            return "Flask Application"
        if has_ml or has_ds:
            return "Machine Learning Project"
        if has_main_py or has_app_py:
            return "Python Application"
        if has_go_mod:
            return "CLI Tool"
        if has_cargo_toml:
            return "CLI Tool"
        if has_package_json and has_js:
            if has_frontend_dir:
                return "React Application"
            if has_react or "react" in top_files or "components" in top_dirs or "pages" in top_dirs:
                return "React Application"
            return "Node.js Project"
        if has_dockerfile:
            return "Microservice"
        if scan.has_src_or_app:
            return "Library"
        return "Unknown"

    def _get_rules(self, project_type: str, scan: ProjectScanResult) -> dict:
        has_python = scan.language_counts.get("Python", 0) > 0
        has_js = (scan.language_counts.get("JavaScript", 0) > 0 or scan.language_counts.get("TypeScript", 0) > 0)

        base_rules: dict = {"required": [], "recommended": [], "optional": []}

        if project_type == "Flask Application":
            base_rules["required"] = ["requirements.txt"]
            ep_found = any(Path(f).name.lower() in ("app.py", "run.py") for f in scan.all_files)
            if not ep_found:
                base_rules["required"].append("app.py")
            if scan.config_py_content:
                base_rules["recommended"].append("config.py")
            base_rules["recommended"] += ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", "docker-compose.yml", ".env.example"]

        elif project_type in ("FastAPI Application",):
            base_rules["required"] = ["main.py", "requirements.txt"]
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", "docker-compose.yml", ".env.example"]

        elif project_type in ("Django Application",):
            base_rules["required"] = ["requirements.txt", "manage.py"]
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", "docker-compose.yml", ".env.example"]

        elif project_type in ("React Application", "Angular Application", "Vue Application", "Next.js Application"):
            base_rules["required"] = ["package.json"]
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", ".env.example"]

        elif project_type in ("Node.js Project", "Full Stack"):
            base_rules["required"] = ["package.json"]
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", "docker-compose.yml", ".env.example"]

        elif project_type in ("Machine Learning Project", "Data Science Project"):
            if has_python:
                base_rules["required"].append("requirements.txt")
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", ".env.example", "Makefile"]

        elif project_type in ("Python Application",):
            base_rules["required"] = ["requirements.txt"]
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", "docker-compose.yml", ".env.example", "Makefile", "setup.py", "setup.cfg"]

        elif project_type in ("CLI Tool", "Desktop Application"):
            if has_python:
                base_rules["required"] = ["requirements.txt"]
            elif has_js:
                base_rules["required"] = ["package.json"]
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", ".env.example"]

        elif project_type in ("Monorepo", "Microservice"):
            if has_python:
                base_rules["required"] = ["requirements.txt"]
            elif has_js:
                base_rules["required"] = ["package.json"]
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", "docker-compose.yml", ".env.example"]

        else:
            if has_python:
                base_rules["required"] = ["requirements.txt"]
            elif has_js:
                base_rules["required"] = ["package.json"]
            base_rules["recommended"] = ["README.md", ".gitignore"]
            base_rules["optional"] = ["Dockerfile", ".env.example"]

        return base_rules

    @staticmethod
    def _readme_detected(scan: ProjectScanResult) -> str | None:
        readme_names = {"readme.md", "readme.rst", "readme.txt", "readme"}
        for f in scan.all_files:
            if Path(f).name.lower() in readme_names:
                return f
        return None

    @staticmethod
    def _check_readme_alias(fname: str, processed: set[str]) -> bool:
        readme_aliases = {"readme.md", "readme.rst", "readme.txt", "readme"}
        return fname.lower() in readme_aliases and bool(processed & readme_aliases)

    @staticmethod
    def _rec_for(fname: str) -> str | None:
        recs = {
            "requirements.txt": "Add requirements.txt to manage Python dependencies.",
            "pyproject.toml": "Add pyproject.toml for Python project configuration.",
            "package.json": "Add package.json to manage Node.js dependencies.",
            "app.py": "Add app.py as the Flask application entry point.",
            "run.py": "Add run.py as the application entry point.",
            "main.py": "Add main.py as the FastAPI application entry point.",
            "manage.py": "Add manage.py for Django project management.",
            ".gitignore": "Add a .gitignore to exclude build artifacts and dependencies.",
            "config.py": "Add config.py for application configuration.",
        }
        return recs.get(fname.lower())

    @staticmethod
    def _msg_for(fname: str) -> str:
        msgs = {
            "README.md": "README is recommended for project documentation.",
            ".gitignore": "Git ignore file is recommended for version control.",
            "Dockerfile": "Docker support can be added.",
            "docker-compose.yml": "Docker Compose support can be added.",
            ".env.example": "Environment example file is recommended.",
            "Makefile": "A Makefile can be added for build automation.",
            "setup.py": "Add setup.py for package distribution.",
            "setup.cfg": "Add setup.cfg for package configuration.",
            "config.py": "Add config.py for centralized settings.",
        }
        return msgs.get(fname.lower(), f"{fname} can be added.")

    def detect_files(self) -> tuple[list[dict], list[dict], list[dict], list[str]]:
        scan = self._ensure_scan()
        project_type = self._detect_project_type(scan)
        rules = self._get_rules(project_type, scan)

        all_file_basenames: dict[str, str] = {}
        for f in scan.all_files:
            all_file_basenames[Path(f).name.lower()] = f

        def _path_for(name: str) -> str | None:
            return all_file_basenames.get(name.lower())

        detected: list[dict] = []
        missing: list[dict] = []
        processed: set[str] = set()

        # -- README detection: case-insensitive, all variants --
        readme_path = self._readme_detected(scan)
        if readme_path:
            rn = Path(readme_path).name
            detected.append({
                "file_name": rn,
                "status": "Detected",
                "category": "Recommended",
                "recommendation": None,
                "path": readme_path,
            })
            for alias in ("readme.md", "readme.rst", "readme.txt", "readme"):
                processed.add(alias)

        # -- Required files --
        for fname in rules["required"]:
            if self._check_readme_alias(fname, processed):
                continue
            p = _path_for(fname)
            if p:
                detected.append({
                    "file_name": fname,
                    "status": "Detected",
                    "category": "Required",
                    "recommendation": None,
                    "path": p,
                })
            else:
                missing.append({
                    "file_name": fname,
                    "status": "Missing",
                    "category": "Required",
                    "recommendation": self._rec_for(fname),
                    "path": None,
                })
            processed.add(fname.lower())

        # -- Recommended files --
        for fname in rules["recommended"]:
            if self._check_readme_alias(fname, processed):
                continue
            if fname.lower() in processed:
                continue
            p = _path_for(fname)
            if p:
                detected.append({
                    "file_name": fname,
                    "status": "Detected",
                    "category": "Recommended",
                    "recommendation": None,
                    "path": p,
                })
            else:
                missing.append({
                    "file_name": fname,
                    "status": "Missing",
                    "category": "Recommended",
                    "recommendation": self._rec_for(fname),
                    "path": None,
                })
            processed.add(fname.lower())

        # -- Optional files --
        for fname in rules["optional"]:
            if fname.lower() in processed:
                continue
            p = _path_for(fname)
            if p:
                detected.append({
                    "file_name": fname,
                    "status": "Detected",
                    "category": "Optional",
                    "recommendation": None,
                    "path": p,
                })
            else:
                missing.append({
                    "file_name": fname,
                    "status": "Not Configured",
                    "category": "Optional",
                    "recommendation": None,
                    "path": None,
                })
            processed.add(fname.lower())

        # -- Warnings: ONLY for missing Required files --
        warnings = []
        for m in missing:
            if m["category"] == "Required":
                warnings.append({
                    "message": f"Missing required file: {m['file_name']}.",
                    "severity": "warning",
                    "file_name": m["file_name"],
                })

        # -- Recommendations: for missing Recommended/Optional (as helpful suggestions) --
        recommendations = []
        for m in missing:
            if m["category"] == "Recommended":
                msg = self._msg_for(m["file_name"])
                if msg:
                    recommendations.append(msg)
            elif m["category"] == "Optional":
                msg = self._msg_for(m["file_name"])
                if msg and msg not in recommendations:
                    recommendations.append(msg)

        self._last_missing = missing
        return detected, missing, warnings, recommendations[:8]

    def calculate_health(self, detected: list[dict], missing: list[dict]) -> tuple[int, str]:
        required_total = (sum(1 for d in detected if d["category"] == "Required") +
                         sum(1 for m in missing if m["category"] == "Required"))
        required_found = sum(1 for d in detected if d["category"] == "Required")
        recommended_total = (sum(1 for d in detected if d["category"] == "Recommended") +
                            sum(1 for m in missing if m["category"] == "Recommended"))
        recommended_found = sum(1 for d in detected if d["category"] == "Recommended")
        optional_total = (sum(1 for d in detected if d["category"] == "Optional") +
                         sum(1 for m in missing if m["category"] == "Optional"))
        optional_found = sum(1 for d in detected if d["category"] == "Optional")

        req_score = (required_found / max(required_total, 1)) * 60 if required_total > 0 else 60
        rec_score = (recommended_found / max(recommended_total, 1)) * 25 if recommended_total > 0 else 25
        opt_score = (optional_found / max(optional_total, 1)) * 15 if optional_total > 0 else 15

        score = min(int(req_score + rec_score + opt_score), 100)

        if score >= 90:
            label = "Excellent"
        elif score >= 70:
            label = "Good"
        elif score >= 40:
            label = "Average"
        else:
            label = "Poor"

        return score, label

    def calculate_readiness(self, detected: list[dict]) -> int:
        required_total = (sum(1 for d in detected if d["category"] == "Required") +
                         sum(1 for m in self._last_missing if m["category"] == "Required"))
        required_found = sum(1 for d in detected if d["category"] == "Required")

        if required_total == 0:
            return 100
        return int((required_found / required_total) * 100)
