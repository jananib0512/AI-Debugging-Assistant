import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.project_scanner import ProjectScanner, ProjectScanResult

from app.repositories.architecture_detector import ArchitectureDetectorRepository
from app.repositories.configuration_detector import ConfigurationDetectorRepository
from app.repositories.entry_point_detector import EntryPointDetector
from app.repositories.framework_detector import FrameworkDetectorRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.module_detector import ModuleDetectorRepository
from app.repositories.project_analyzer_repository import ProjectAnalyzerRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    AnalyzerResponse,
    ConfigSummary,
    DetectedDirectory,
    DetectedEntryPoint,
    FolderSummary,
    ProjectAnalysisResponse,
    TechnologyStack,
)

logger = logging.getLogger(__name__)


class ProjectAnalyzerService:
    def __init__(self, db: Session = Depends(get_db)):
        self.project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> ProjectAnalysisResponse:
        project = self.project_repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.extraction_status != "extracted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has not been extracted yet. Extract the project before analysis.",
            )

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace directory not found on disk. Please re-extract the project.",
            )

        scanner = ProjectScanner()
        scan_result = scanner.scan(workspace_path)

        repo = ProjectAnalyzerRepository(workspace_path, scan_result)
        raw = repo.analyze()

        project_type, project_type_reason = self._detect_project_type(
            scan_result, project.project_name,
        )
        architecture, architecture_reason = self._detect_architecture(
            scan_result, project_type,
        )
        detected_modules = self._detect_modules(scan_result, project_type)
        databases = self._detect_databases(scan_result)

        frontend_framework, backend_framework = self._detect_frameworks(scan_result)

        entry_points = [
            DetectedEntryPoint(**ep) for ep in raw["entry_points"]
        ]
        important_dirs = [
            DetectedDirectory(**d) for d in raw["important_dirs"]
        ]

        structure_summary = self._build_structure_summary(
            raw, project_type, architecture,
        )

        has_docker = scan_result.dockerfile_content is not None
        has_ci_cd = self._has_ci_cd(workspace_path)

        return ProjectAnalysisResponse(
            project_type=project_type,
            project_type_reason=project_type_reason,
            architecture=architecture,
            architecture_reason=architecture_reason,
            entry_points=entry_points,
            important_directories=important_dirs,
            detected_modules=sorted(detected_modules),
            frontend_framework=frontend_framework,
            backend_framework=backend_framework,
            database_detected=databases,
            has_tests=scan_result.has_tests,
            has_docker=has_docker,
            has_ci_cd=has_ci_cd,
            structure_summary=structure_summary,
            analyzed_at=datetime.now(timezone.utc),
        )

    def _detect_project_type(
        self, scan: ProjectScanResult, project_name: str,
    ) -> tuple[str, str]:
        top_dirs = {d.lower() for d in scan.root_dirs}
        top_files = {f.lower() for f in scan.root_files}

        has_python = scan.language_counts.get("Python", 0) > 0
        has_js = (scan.language_counts.get("JavaScript", 0) > 0 or scan.language_counts.get("TypeScript", 0) > 0)
        has_react = "react" in scan.js_imports
        has_vue = "vue" in scan.js_imports
        has_django = "django" in scan.python_imports
        has_fastapi = "fastapi" in scan.python_imports
        has_flask = "flask" in scan.python_imports

        is_next = has_js and ("next.config.js" in top_files or "next.config.mjs" in top_files or "next.config.ts" in top_files or "next" in {f.lower() for f in (scan.package_json or {}).get("dependencies", {})})
        is_nuxt = "nuxt" in scan.js_imports

        has_backend_dir = bool(top_dirs & {"backend", "server", "api"})
        has_frontend_dir = bool(top_dirs & {"frontend", "client", "ui"})
        has_src_or_app = scan.has_src_or_app
        has_packages_dir = "packages" in top_dirs
        has_multiple_services = len([d for d in top_dirs if "service" in d]) >= 2

        has_main_py = "main.py" in top_files
        has_app_py = "app.py" in top_files
        has_manage_py = "manage.py" in top_files
        has_go_mod = "go.mod" in top_files
        has_cargo_toml = "cargo.toml" in top_files
        has_package_json = "package.json" in top_files
        has_angular_json = "angular.json" in top_files
        has_vite_config = any(f.startswith("vite.config.") for f in top_files)
        has_dockerfile = scan.dockerfile_content is not None
        has_docker_compose = scan.docker_compose_content is not None
        has_k8s = bool(scan.all_dir_names & {"k8s", "kubernetes", "manifests", "helm", "chart"})
        has_notebooks = any(f.endswith(".ipynb") for f in scan.all_files)

        ml_deps = {"tensorflow", "torch", "sklearn", "transformers", "keras"}
        has_ml = bool(scan.python_imports & ml_deps) or bool(
            d for d in scan.requirements_txt_deps
            if any(m in d for m in ml_deps)
        )
        ml_deps_in_req = any(
            any(m in d for m in ml_deps) for d in scan.requirements_txt_deps
        )
        if ml_deps_in_req:
            has_ml = True

        ds_dirs = top_dirs & {"notebooks", "data", "datasets", "analysis"}
        has_ds = has_notebooks or bool(ds_dirs)

        if has_packages_dir and not has_frontend_dir and not has_backend_dir:
            return "Monorepo", "Contains packages directory with no dominant frontend or backend structure"

        if has_docker_compose and (has_multiple_services or has_k8s):
            return "Microservice", "Docker Compose with multiple service directories or Kubernetes manifests"

        if has_k8s and not has_docker_compose:
            return "Microservice", "Kubernetes manifests detected"

        if has_frontend_dir and has_backend_dir:
            return "Full Stack", "Detected both frontend and backend directories"

        if is_next:
            return "Next.js Application", "Next.js framework detected with app/pages router"

        if has_angular_json:
            return "Angular Application", "Angular CLI configuration detected"

        if has_vite_config and has_react:
            return "React Application", "Vite + React project"
        if has_vite_config and has_vue:
            return "Vue Application", "Vite + Vue project"

        if has_django or has_manage_py:
            return "Django Application", "Django framework detected"

        if has_fastapi or (has_main_py and "api" in top_dirs):
            return "FastAPI Application", "FastAPI framework detected"

        if has_flask or has_app_py:
            return "Flask Application", "Flask framework detected"

        if has_ml or has_ds:
            if has_notebooks:
                return "Data Science Project", "Jupyter notebooks and ML dependencies detected"
            return "Machine Learning Project", "ML framework dependencies detected"

        if has_main_py or has_app_py:
            is_api = bool(top_dirs & {"api", "routes"}) or has_main_py
            if is_api:
                return "API", "Python application with API entry point detected"
            return "Backend", "Python application entry point detected"

        if has_go_mod:
            if "cmd" in top_dirs:
                return "CLI", "Go CLI project with cmd directory"
            return "Backend", "Go module detected"

        if has_cargo_toml:
            return "CLI", "Rust/Cargo project detected"

        if has_package_json and has_js:
            has_api_routes = bool(top_dirs & {"api", "routes", "controllers"})
            if is_next or is_nuxt:
                return "Full Stack" if (has_backend_dir or has_api_routes) else "Frontend", "JS framework app"
            if has_frontend_dir or (not has_api_routes and has_src_or_app):
                if has_backend_dir or has_api_routes:
                    return "Full Stack", "Node.js project with both frontend and backend directories"
                return "Frontend", "Node.js project with frontend structure"
            if has_api_routes:
                return "API", "Node.js project with API routes"
            return "Backend", "Node.js project without frontend directory"

        if has_dockerfile and not has_frontend_dir and not has_backend_dir:
            return "Microservice", "Dockerfile without explicit frontend or backend structure"

        if has_k8s:
            return "Microservice", "Kubernetes manifests detected"

        if scan.has_src_or_app:
            return "Library", "Source code directory found with no clear application type"

        if len(scan.root_dirs) <= 2 and len(scan.root_files) <= 5:
            return "Library", "Minimal project structure with few files and directories"

        if scan.needs_analysis:
            return "Unknown", "Workspace is empty or inaccessible"

        return "Unknown", "Could not determine project type from directory structure"

    def _detect_architecture(
        self, scan: ProjectScanResult, project_type: str,
    ) -> tuple[str, str]:
        detector = ArchitectureDetectorRepository(scan)
        arch_results = detector.detect_architectures()

        if arch_results and arch_results[0]["confidence"] >= 30:
            top = arch_results[0]
            return top["architecture"], top["reason"]

        return "Unknown", "Could not determine architecture from directory structure"

    def _detect_modules(self, scan: ProjectScanResult, project_type: str) -> list[str]:
        all_dir_names = scan.all_dir_names
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        all_dir_names |= root_dirs_lower

        type_map: dict[str, str] = {
            "api": "API Layer", "routes": "API Layer", "controllers": "API Layer",
            "endpoints": "API Layer",
            "models": "Data Models", "schemas": "Data Schemas", "entities": "Data Models",
            "services": "Business Logic", "repositories": "Data Access",
            "components": "UI Components", "pages": "Page Components",
            "hooks": "React Hooks", "store": "State Management", "state": "State Management",
            "middleware": "Middleware",
            "config": "Configuration", "configuration": "Configuration", "settings": "Configuration",
            "tests": "Testing", "__tests__": "Testing", "spec": "Testing", "test": "Testing",
            "migrations": "Database Migrations", "seeds": "Database Seeds",
            "docs": "Documentation", "documentation": "Documentation",
            "public": "Static Assets", "static": "Static Assets", "assets": "Assets",
            "scripts": "Scripts", "bin": "Scripts",
            "types": "Type Definitions", "interfaces": "Type Definitions",
            "layouts": "Layouts", "features": "Features", "modules": "Modules",
            "context": "React Context", "providers": "Providers",
            "utils": "Utilities", "helpers": "Helpers",
            "auth": "Authentication", "authentication": "Authentication",
            "database": "Database", "db": "Database",
            "logging": "Logging", "cache": "Caching",
            "validation": "Validation", "templates": "Templates",
            "ml": "ML/AI", "ai": "ML/AI",
            "reports": "Reports", "report": "Reports",
            "locales": "Localization", "i18n": "Localization",
        }

        seen: set[str] = set()
        modules: list[str] = []

        for name in sorted(all_dir_names):
            module_type = type_map.get(name)
            if module_type and module_type not in seen:
                seen.add(module_type)
                modules.append(module_type)

        if "Authentication" not in modules and (
            "auth" in all_dir_names or "login" in all_dir_names
        ):
            modules.append("Authentication")

        if project_type in ("Full Stack",):
            if "API Layer" not in modules:
                modules.insert(0, "API Layer")
            if "Data Models" not in modules:
                modules.append("Data Models")

        if project_type == "Frontend":
            if "UI Components" not in modules:
                modules.insert(0, "UI Components")

        if project_type in ("Machine Learning Project", "Data Science Project"):
            if "ML/AI" not in modules:
                modules.insert(0, "ML/AI")

        return modules

    def _detect_databases(self, scan: ProjectScanResult) -> list[str]:
        databases: list[str] = []
        all_dir_names = scan.all_dir_names
        root_files = {f.lower() for f in scan.root_files}
        has_python = scan.language_counts.get("Python", 0) > 0

        pip_deps = scan.requirements_txt_deps
        npm_deps_names: set[str] = set()
        if scan.package_json:
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                section_data = scan.package_json.get(section, {})
                if isinstance(section_data, dict):
                    npm_deps_names.update(section_data.keys())

        if all_dir_names & {"migrations", "seeds", "db", "database"}:
            databases.append("Database layer detected (migrations/seeds)")

        if "prisma" in all_dir_names or "prisma" in npm_deps_names:
            databases.append("Prisma ORM")

        if "sqlalchemy" in scan.python_imports or "sqlalchemy" in pip_deps:
            databases.append("SQLAlchemy ORM")

        if "flask_sqlalchemy" in scan.python_imports:
            databases.append("Flask-SQLAlchemy")

        db_pkg_map = {
            "PostgreSQL": ["psycopg2", "psycopg2-binary", "psycopg", "asyncpg", "pg", "pg-promise"],
            "MySQL": ["mysqlclient", "pymysql", "mysql-connector-python", "mysql2"],
            "SQLite": ["sqlite3"],
            "MongoDB": ["pymongo", "mongoose", "motor", "mongoengine"],
            "Redis": ["redis", "ioredis"],
        }

        for db_name, db_pkgs in db_pkg_map.items():
            if any(d in pip_deps for d in db_pkgs) or any(d in npm_deps_names for d in db_pkgs):
                databases.append(db_name)

        config_text = ""
        for txt in [scan.config_py_content, scan.settings_py_content,
                     scan.database_py_content, scan.env_content,
                     scan.env_example_content]:
            if txt:
                config_text += txt.lower() + "\n"

        if config_text:
            for uri in scan.db_uris:
                for db in ["postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis"]:
                    if db in uri.lower():
                        db_name = {"postgresql": "PostgreSQL", "postgres": "PostgreSQL",
                                   "mysql": "MySQL", "sqlite": "SQLite",
                                   "mongodb": "MongoDB", "redis": "Redis"}.get(db, db)
                        if db_name not in databases:
                            databases.append(db_name)

        return databases

    def _detect_frameworks(self, scan: ProjectScanResult) -> tuple[str | None, str | None]:
        frontend_framework: str | None = None
        backend_framework: str | None = None
        root_files = {f.lower() for f in scan.root_files}

        # Frontend
        if any(f.startswith("next.config.") for f in root_files) or "next" in scan.js_imports:
            frontend_framework = "Next.js"
        elif "angular.json" in root_files:
            frontend_framework = "Angular"
        elif any(f.startswith("vite.config.") for f in root_files):
            if "react" in scan.js_imports or "react" in (scan.package_json or {}).get("dependencies", {}):
                frontend_framework = "React (Vite)"
            elif "vue" in scan.js_imports:
                frontend_framework = "Vue.js (Vite)"
            else:
                frontend_framework = "Vite"
        elif any(f.endswith(".vue") for f in scan.root_files):
            frontend_framework = "Vue.js"
        elif any(f.endswith(".svelte") for f in scan.root_files):
            frontend_framework = "Svelte"
        elif scan.has_src_or_app and (
            "App.tsx" in root_files or "App.jsx" in root_files
            or "react" in scan.js_imports
        ):
            frontend_framework = "React"

        if not frontend_framework and (
            "components" in scan.all_dir_names or "pages" in scan.all_dir_names
        ):
            frontend_framework = "React"

        # Backend
        if "django" in scan.python_imports or "manage.py" in root_files:
            backend_framework = "Django"
        elif "fastapi" in scan.python_imports:
            backend_framework = "FastAPI"
        elif "flask" in scan.python_imports or "app.py" in root_files:
            backend_framework = "Flask"
        elif "express" in scan.js_imports:
            backend_framework = "Express"
        elif "main.py" in root_files and not frontend_framework:
            backend_framework = "FastAPI (likely)"
        elif "go.mod" in root_files:
            backend_framework = "Go"
        elif "requirements.txt" in root_files:
            backend_framework = "Python"
        elif "cargo.toml" in root_files:
            backend_framework = "Rust"
        elif scan.package_json and not frontend_framework:
            deps = set()
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                section_data = scan.package_json.get(section, {})
                if isinstance(section_data, dict):
                    deps.update(section_data.keys())
            if "express" in deps:
                backend_framework = "Express"
            elif "@nestjs/core" in deps:
                backend_framework = "NestJS"

        return frontend_framework, backend_framework

    @staticmethod
    def _has_ci_cd(workspace_path: Path) -> bool:
        ci_dirs = {".github", ".gitlab", ".circleci", "ci"}
        try:
            for entry in workspace_path.iterdir():
                if not entry.is_dir():
                    continue
                if entry.name.lower() in ci_dirs:
                    return True
                if entry.name == ".github":
                    ci_path = entry / "workflows"
                    if ci_path.exists():
                        return True
            return False
        except PermissionError:
            return False

    @staticmethod
    def _build_structure_summary(raw: dict, project_type: str, architecture: str) -> str:
        parts: list[str] = []
        top_count = len(raw["top_level_dirs"])
        file_count = len(raw["top_level_files"])
        ep_count = len(raw["entry_points"])

        parts.append(f"Project root contains {top_count} director{'y' if top_count == 1 else 'ies'} and {file_count} file{'s' if file_count != 1 else ''}.")

        if raw["has_src_or_app"]:
            parts.append("Has a dedicated source directory.")
        if raw["has_tests"]:
            parts.append("Test directory detected.")
        if raw["has_docs"]:
            parts.append("Documentation directory detected.")
        if raw["has_scripts"]:
            parts.append("Scripts or binary directory detected.")

        if ep_count > 0:
            names = [ep["file_name"] for ep in raw["entry_points"][:5]]
            parts.append(f"Entry point{'s' if ep_count > 1 else ''}: {', '.join(names)}.")

        return " ".join(parts)


class ProjectAnalyzerCoreService:
    def __init__(self, db: Session = Depends(get_db)):
        self.project_repo = ProjectRepository(db)
        self.metadata_repo = MetadataRepository(db)

    def _detect_project_type(self, scan: ProjectScanResult) -> str:
        top_dirs = {d.lower() for d in scan.root_dirs}
        top_files = {f.lower() for f in scan.root_files}

        has_python = scan.language_counts.get("Python", 0) > 0
        has_js = (scan.language_counts.get("JavaScript", 0) > 0 or scan.language_counts.get("TypeScript", 0) > 0)
        has_react = "react" in scan.js_imports
        has_django = "django" in scan.python_imports
        has_fastapi = "fastapi" in scan.python_imports
        has_flask = "flask" in scan.python_imports

        is_next = has_js and (
            "next.config.js" in top_files or "next.config.mjs" in top_files or "next.config.ts" in top_files
            or "next" in {f.lower() for f in (scan.package_json or {}).get("dependencies", {})}
        )

        has_backend_dir = bool(top_dirs & {"backend", "server", "api"})
        has_frontend_dir = bool(top_dirs & {"frontend", "client", "ui"})
        has_packages_dir = "packages" in top_dirs
        has_multiple_services = len([d for d in top_dirs if "service" in d]) >= 2

        has_main_py = "main.py" in top_files
        has_app_py = "app.py" in top_files
        has_manage_py = "manage.py" in top_files
        has_go_mod = "go.mod" in top_files
        has_cargo_toml = "cargo.toml" in top_files
        has_package_json = "package.json" in top_files
        has_angular_json = "angular.json" in top_files
        has_vite_config = any(f.startswith("vite.config.") for f in top_files)
        has_dockerfile = scan.dockerfile_content is not None
        has_docker_compose = scan.docker_compose_content is not None
        has_k8s = bool(scan.all_dir_names & {"k8s", "kubernetes", "manifests", "helm", "chart"})
        has_notebooks = any(f.endswith(".ipynb") for f in scan.all_files)

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
            if has_notebooks:
                return "Data Science Project"
            return "Machine Learning Project"
        if has_main_py or has_app_py:
            return "API"
        if has_go_mod:
            return "Backend"
        if has_cargo_toml:
            return "CLI"
        if has_package_json and has_js:
            if has_backend_dir or has_frontend_dir:
                return "Full Stack"
            return "Frontend"
        if has_dockerfile and not has_frontend_dir and not has_backend_dir:
            return "Microservice"
        if has_k8s:
            return "Microservice"
        if scan.has_src_or_app:
            return "Library"
        if scan.needs_analysis:
            return "Unknown"
        return "Unknown"

    def analyze(self, user_id: int, project_id: int) -> AnalyzerResponse:
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project workspace has not been extracted. Please extract before analyzing.")

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace directory not found. Please re-extract the project.")

        if not _is_workspace_healthy(workspace_path):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workspace validation has not been completed. Please run validation first.")

        metadata = self.metadata_repo.get_by_project_id(project_id)
        if not metadata:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project metadata not available. Please scan project metadata first.")

        scanner = ProjectScanner()
        scan_result = scanner.scan(workspace_path)

        project_type = self._detect_project_type(scan_result)

        repo = ProjectAnalyzerRepository(workspace_path, scan_result)
        raw = repo.scan(project_type=project_type)

        workspace_status = "Ready"
        if raw["needs_analysis"]:
            workspace_status = "Empty"

        languages = raw.get("languages", [])

        detector = FrameworkDetectorRepository(scan_result)
        framework_items = detector.detect_frameworks()
        detected_frameworks = sorted({f["name"] for f in framework_items})

        database_items = detector.detect_databases()
        databases = sorted({d["name"] for d in database_items})

        pm_items = detector.detect_package_managers()
        package_managers = sorted({p["name"] for p in pm_items})

        tech_stack = TechnologyStack(
            languages=languages,
            frameworks=detected_frameworks,
            databases=databases,
            package_managers=package_managers,
        )

        cfg = raw.get("config_flags", {})
        config_summary = ConfigSummary(
            has_package_json=cfg.get("package_json", False),
            has_requirements_txt=cfg.get("requirements_txt", False),
            has_dockerfile=cfg.get("dockerfile", False),
            has_docker_compose=cfg.get("docker_compose", False),
            has_readme=cfg.get("readme", False),
            has_pyproject_toml=cfg.get("pyproject_toml", False),
            has_env_example=cfg.get("env_example", False),
            has_gitignore=cfg.get("gitignore", False),
        )

        folder_cats = raw.get("folder_categories", {})
        folder_summary = FolderSummary(
            frontend=folder_cats.get("frontend", 0),
            backend=folder_cats.get("backend", 0),
            source=folder_cats.get("source", 0),
            config=folder_cats.get("config", 0),
            assets=folder_cats.get("assets", 0),
            docs=folder_cats.get("docs", 0),
            tests=folder_cats.get("tests", 0),
            scripts=folder_cats.get("scripts", 0),
            other=folder_cats.get("other", 0),
        )

        workspace_summary = self._build_workspace_summary(
            scan_result, project_type, metadata,
        )

        return AnalyzerResponse(
            project_name=project.project_name,
            project_type=project_type,
            workspace_status=workspace_status,
            technology_stack=tech_stack,
            total_files=raw["total_files"],
            total_folders=raw["total_folders"],
            workspace_size=raw["workspace_size"],
            folder_summary=folder_summary,
            config_summary=config_summary,
            workspace_summary=workspace_summary,
            analyzed_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _build_workspace_summary(scan: ProjectScanResult, project_type: str, metadata) -> str:
        parts: list[str] = []

        file_count = scan.total_files
        folder_count = scan.total_folders
        size_bytes = scan.workspace_size
        size_str = _format_size(size_bytes)

        lang_counts = scan.language_counts
        langs = sorted(lang_counts.keys(), key=lambda l: -lang_counts[l])
        primary_lang = langs[0] if langs else None

        detector = FrameworkDetectorRepository(scan)
        frameworks = [f["name"] for f in detector.detect_frameworks()]
        databases = [d["name"] for d in detector.detect_databases()]
        pms = [p["name"] for p in detector.detect_package_managers()]

        # Build a meaningful description
        desc_parts: list[str] = []

        if primary_lang:
            lang_desc = primary_lang
            if frameworks:
                fw_names = frameworks[:3]
                if len(fw_names) == 1:
                    lang_desc = f"{fw_names[0]} ({primary_lang})"
                else:
                    lang_desc = f"{' / '.join(fw_names)}"
            desc_parts.append(f"This is a {project_type.lower()} project using {lang_desc}.")

        if databases:
            if len(databases) == 1:
                desc_parts.append(f"Uses {databases[0]} as the database.")
            else:
                desc_parts.append(f"Uses {', '.join(databases[:3])} as data stores.")

        has_frontend = any(v > 0 for k, v in scan.language_counts.items()
                          if k in {"JavaScript", "TypeScript", "HTML", "CSS"})
        has_ml = any(imp in scan.python_imports for imp in
                    ["tensorflow", "torch", "sklearn", "transformers"])
        has_test = scan.has_tests

        if has_frontend and primary_lang and primary_lang not in ("JavaScript", "TypeScript", "HTML", "CSS"):
            desc_parts.append("Includes frontend assets.")
        if has_ml:
            desc_parts.append("Machine Learning libraries detected.")
        if has_test:
            desc_parts.append("Test suites are configured.")

        # File/folder stats
        stats = (
            f"The project contains {file_count} file{'s' if file_count != 1 else ''} "
            f"across {folder_count} director{'y' if folder_count == 1 else 'ies'} "
            f"({size_str})."
        )
        desc_parts.append(stats)

        if pms:
            desc_parts.append(f"Package manager{'s' if len(pms) > 1 else ''}: {', '.join(pms[:3])}.")

        configs_present = []
        if scan.config_flags.get("readme"): configs_present.append("README")
        if scan.dockerfile_content: configs_present.append("Dockerfile")
        if scan.gitignore_content: configs_present.append(".gitignore")
        if configs_present:
            desc_parts.append(f"Config: {', '.join(configs_present)}.")

        return " ".join(desc_parts)


def _is_workspace_healthy(workspace_path: Path) -> bool:
    try:
        if not workspace_path.exists():
            return False
        if not os.access(str(workspace_path), os.R_OK | os.X_OK):
            return False
        entries = list(workspace_path.iterdir())
        non_ignored = [e for e in entries if not e.name.startswith(".") and e.name not in {
            "node_modules", ".git", ".venv", "__pycache__", "dist", "build",
        }]
        return len(non_ignored) > 0
    except (OSError, PermissionError):
        return False


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
