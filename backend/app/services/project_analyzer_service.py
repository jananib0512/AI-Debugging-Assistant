import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.detector import detect_frameworks as old_detect_frameworks
from app.repositories.metadata_repository import MetadataRepository
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

        repo = ProjectAnalyzerRepository(workspace_path)
        raw = repo.analyze()

        project_type, project_type_reason = self._detect_project_type(raw, workspace_path, project.project_name)
        architecture, architecture_reason = self._detect_architecture(raw, project_type)
        detected_modules = self._detect_modules(raw, project_type)
        databases = self._detect_databases(raw, project_type)

        entry_points = [
            DetectedEntryPoint(**ep) for ep in raw["entry_points"]
        ]
        important_dirs = [
            DetectedDirectory(**d) for d in raw["important_dirs"]
        ]

        structure_summary = self._build_structure_summary(
            raw, project_type, architecture,
        )

        frontend_framework, backend_framework = self._detect_frameworks(raw)

        has_docker = self._has_docker(workspace_path)

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
            has_tests=raw["has_tests"],
            has_docker=has_docker,
            has_ci_cd=has_ci_cd,
            structure_summary=structure_summary,
            analyzed_at=datetime.now(timezone.utc),
        )

    def _detect_project_type(
        self,
        raw: dict,
        workspace_path: Path,
        project_name: str,
    ) -> tuple[str, str]:
        top_dirs = {d.lower() for d in raw["top_level_dirs"]}
        top_files = {f.lower() for f in raw["top_level_files"]}
        all_dirs_lower = {d.lower() for d in raw["all_dirs"]}

        has_backend_dir = bool(top_dirs & {"backend", "server", "api"})
        has_frontend_dir = bool(top_dirs & {"frontend", "client", "ui"})
        has_src_or_app = raw["has_src_or_app"]
        has_packages_dir = "packages" in top_dirs
        has_multiple_services = (
            len([d for d in top_dirs if "service" in d]) >= 2
        )

        has_main_py = "main.py" in top_files
        has_app_py = "app.py" in top_files
        has_manage_py = "manage.py" in top_files
        has_go_mod = "go.mod" in top_files
        has_cargo_toml = "cargo.toml" in top_files
        has_package_json = "package.json" in top_files
        has_dockerfile = "dockerfile" in top_files or "Dockerfile" in top_files
        has_docker_compose = any(
            f in top_files for f in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
        )
        has_angular_json = "angular.json" in top_files
        has_vite_config = any(
            f.startswith("vite.config.") for f in raw["top_level_files"]
        )
        has_electron_builder = any(
            "electron" in f for f in top_files
        )
        has_serverless = any(
            f in top_files for f in ("serverless.yml", "serverless.yaml", "serverless.json")
        )
        has_k8s_manifests = bool(all_dirs_lower & {"k8s", "kubernetes", "manifests", "helm", "chart"})

        if has_packages_dir and not has_frontend_dir and not has_backend_dir:
            return "Monorepo", "Contains packages directory with no dominant frontend or backend structure"

        if has_frontend_dir and has_backend_dir:
            return "Full Stack", "Detected both frontend and backend directories"

        if has_docker_compose and (has_multiple_services or has_k8s_manifests):
            return "Microservice", "Docker Compose with multiple service directories or Kubernetes manifests"

        if has_main_py or has_app_py or has_manage_py:
            is_api = bool(top_dirs & {"api", "routes"}) or has_main_py
            if is_api and has_frontend_dir:
                return "Full Stack", "Python application with API structure and frontend directory"
            if is_api:
                return "API", "Python application with API entry point detected"
            return "Backend", "Python application entry point detected"

        if has_go_mod:
            return "Backend", "Go module detected"

        if has_cargo_toml:
            return "CLI", "Rust/Cargo project detected"

        if has_package_json:
            has_api_routes = bool(top_dirs & {"api", "routes", "controllers"})
            has_backend_dir or bool(all_dirs_lower & {"api", "routes", "controllers", "middleware"})
            if has_frontend_dir or (not has_api_routes and has_src_or_app):
                if has_backend_dir or has_api_routes:
                    return "Full Stack", "Node.js project with both frontend and backend directories"
                return "Frontend", "Node.js project with frontend structure"
            if has_api_routes:
                return "API", "Node.js project with API routes"
            return "Backend", "Node.js project without frontend directory"

        if has_angular_json or has_vite_config:
            return "Frontend", "Frontend framework config detected"

        if has_dockerfile and not has_frontend_dir and not has_backend_dir:
            return "Microservice", "Dockerfile without explicit frontend or backend structure"

        if has_go_mod or has_cargo_toml:
            category = "CLI" if has_cargo_toml else "Backend"
            return category, f"{'Rust' if has_cargo_toml else 'Go'} project detected"

        for d in top_dirs:
            if d in {"cmd", "internal", "pkg"}:
                return "CLI", "Go-style directory structure detected"

        if has_k8s_manifests:
            return "Microservice", "Kubernetes manifests detected"

        if raw["has_src_or_app"]:
            return "Library", "Source code directory found with no clear application type"

        if len(raw["top_level_dirs"]) <= 2 and len(raw["top_level_files"]) <= 5:
            return "Library", "Minimal project structure with few files and directories"

        if raw["needs_analysis"]:
            return "Unknown", "Workspace is empty or inaccessible"

        return "Unknown", "Could not determine project type from directory structure"

    def _detect_architecture(
        self, raw: dict, project_type: str,
    ) -> tuple[str, str]:
        from app.repositories.project_analyzer_repository import ARCHITECTURE_DIR_PATTERNS

        all_dirs = {d.lower() for d in raw["all_dirs"]}
        all_files = {f.lower() for f in raw["all_files"]}

        if project_type == "Monorepo":
            return "Monorepo", "Packages or apps directory indicates a monorepo structure"

        for arch, patterns in ARCHITECTURE_DIR_PATTERNS.items():
            matching = patterns & all_dirs
            if len(matching) >= 2:
                display_names = {
                    "mvc": "MVC",
                    "layered": "Layered",
                    "clean_architecture": "Clean Architecture",
                    "hexagonal": "Hexagonal",
                    "feature_based": "Feature-Based",
                }
                return display_names.get(arch, arch), f"Detected directories: {', '.join(sorted(matching))}"

        if all_dirs & {"services", "repositories", "api"}:
            return "Layered", "Services, repositories, and API directories indicate layered architecture"

        if all_dirs & {"controllers", "models"}:
            return "MVC", "Controllers and models directories indicate MVC architecture"

        if all_dirs & {"features", "modules"}:
            return "Feature-Based", "Features or modules directory indicates feature-based architecture"

        if project_type == "Microservice":
            return "Microservice", "Project type suggests microservice architecture"

        if raw["has_src_or_app"]:
            return "Layered", "Source directory with no specific architecture pattern detected; defaulting to layered"

        return "Unknown", "Could not determine architecture from directory structure"

    def _detect_modules(self, raw: dict, project_type: str) -> list[str]:
        modules: list[str] = []
        top_dirs = {d.lower() for d in raw["top_level_dirs"]}
        all_dirs_lower = {d.lower() for d in raw["all_dirs"]}

        type_map = {
            "api": "API Layer",
            "routes": "API Layer",
            "controllers": "API Layer",
            "models": "Data Models",
            "schemas": "Data Schemas",
            "services": "Business Logic",
            "repositories": "Data Access",
            "components": "UI Components",
            "pages": "Page Components",
            "hooks": "React Hooks",
            "utils": "Utilities",
            "helpers": "Helpers",
            "store": "State Management",
            "state": "State Management",
            "middleware": "Middleware",
            "config": "Configuration",
            "tests": "Testing",
            "__tests__": "Testing",
            "spec": "Testing",
            "test": "Testing",
            "migrations": "Database Migrations",
            "seeds": "Database Seeds",
            "docs": "Documentation",
            "documentation": "Documentation",
            "public": "Static Assets",
            "static": "Static Assets",
            "assets": "Assets",
            "scripts": "Scripts",
            "bin": "Scripts",
            "types": "Type Definitions",
            "interfaces": "Type Definitions",
            "layouts": "Layouts",
            "features": "Features",
            "modules": "Modules",
            "context": "React Context",
            "providers": "Providers",
        }

        seen: set[str] = set()
        candidates = top_dirs | all_dirs_lower
        for name in sorted(candidates):
            module_type = type_map.get(name)
            if module_type and module_type not in seen:
                seen.add(module_type)
                modules.append(module_type)

        if "Authentication" not in modules and (
            "auth" in all_dirs_lower or "login" in all_dirs_lower
        ):
            modules.append("Authentication")

        if project_type == "Full Stack":
            if "API Layer" not in modules:
                modules.insert(0, "API Layer")
            if "Data Models" not in modules:
                modules.append("Data Models")

        if project_type == "Frontend":
            if "UI Components" not in modules:
                modules.insert(0, "UI Components")

        return modules

    def _detect_databases(self, raw: dict, project_type: str) -> list[str]:
        databases: list[str] = []
        all_dirs_lower = {d.lower() for d in raw["all_dirs"]}
        all_files_lower = {f.lower() for f in raw["all_files"]}

        if all_dirs_lower & {"migrations", "seeds", "db", "database"}:
            databases.append("Database layer detected (migrations/seeds)")

        if any("sql" in f for f in all_files_lower):
            databases.append("SQL files found")

        if "prisma" in all_dirs_lower or "prisma" in str(raw.get("all_dirs", [])):
            databases.append("Prisma ORM")

        return databases

    def _detect_frameworks(self, raw: dict) -> tuple[str | None, str | None]:
        frontend_framework: str | None = None
        backend_framework: str | None = None
        top_files = {f.lower() for f in raw["top_level_files"]}
        all_files_lower = {f.lower() for f in raw["all_files"]}
        all_dirs_lower = {d.lower() for d in raw["all_dirs"]}

        if any("next.config" in f for f in top_files):
            frontend_framework = "Next.js"
        elif "angular.json" in top_files:
            frontend_framework = "Angular"
        elif any("vite.config" in f for f in raw["top_level_files"]):
            frontend_framework = "Vite"
        elif any(f.endswith(".vue") for f in all_files_lower):
            frontend_framework = "Vue.js"
        elif any(f.endswith(".svelte") for f in all_files_lower):
            frontend_framework = "Svelte"
        elif raw["has_src_or_app"] and (
            "App.tsx" in top_files or "App.jsx" in top_files
            or any(f.endswith(".tsx") for f in all_files_lower)
        ):
            frontend_framework = "React"

        if "manage.py" in top_files:
            backend_framework = "Django"
        elif "app.py" in top_files and not frontend_framework:
            backend_framework = "Flask"
        elif "main.py" in top_files:
            backend_framework = "FastAPI (likely)"
        elif "go.mod" in top_files:
            backend_framework = "Go"
        elif "requirements.txt" in top_files:
            backend_framework = "Python"
        elif "cargo.toml" in top_files:
            backend_framework = "Rust"

        if not frontend_framework and all_dirs_lower & {"components", "pages"}:
            frontend_framework = "React"

        return frontend_framework, backend_framework

    @staticmethod
    def _has_docker(workspace_path: Path) -> bool:
        docker_names = {"dockerfile", "Dockerfile", "docker-compose.yml",
                        "docker-compose.yaml", "compose.yml", "compose.yaml",
                        ".dockerignore"}
        try:
            for entry in workspace_path.iterdir():
                if entry.name in docker_names:
                    return True
            return False
        except PermissionError:
            return False

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

    def analyze(self, user_id: int, project_id: int) -> AnalyzerResponse:
        # Prerequisite 1 & 2: Project exists and owned by user
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Prerequisite 3: Project must be extracted
        if project.extraction_status != "extracted":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project workspace has not been extracted. Please extract before analyzing.",
            )

        # Prerequisite 4: Workspace directory must exist on disk
        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace directory not found. Please re-extract the project.",
            )

        # Prerequisite 5: Validation must have been completed
        if not _is_workspace_healthy(workspace_path):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Workspace validation has not been completed. Please run validation first.",
            )

        # Prerequisite 6: Metadata must be available
        metadata = self.metadata_repo.get_by_project_id(project_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project metadata not available. Please scan project metadata first.",
            )

        repo = ProjectAnalyzerRepository(workspace_path)
        raw = repo.scan()

        workspace_status = "Ready"
        if raw["needs_analysis"]:
            workspace_status = "Empty"

        project_type = project.language or "Unknown"

        # Build technology stack
        languages = raw.get("languages", [])

        top_level_files = [f.name for f in workspace_path.iterdir() if f.is_file()]
        fake_raw = {
            "top_level_files": top_level_files,
            "all_files": [str(f.relative_to(workspace_path)) for f in workspace_path.rglob("*") if f.is_file() and not any(p.startswith(".") for p in f.relative_to(workspace_path).parts)],
            "all_dirs": [str(d.relative_to(workspace_path)) for d in workspace_path.rglob("*") if d.is_dir() and not any(p.startswith(".") for p in d.relative_to(workspace_path).parts)],
            "has_src_or_app": any(d.name.lower() in {"src", "app"} for d in workspace_path.iterdir() if d.is_dir()),
        }
        detected_frameworks = old_detect_frameworks(workspace_path, {l: 1 for l in languages})

        databases: list[str] = []
        try:
            from app.detection.detector import detect_databases
            databases = detect_databases(workspace_path)
        except Exception:
            pass

        tech_stack = TechnologyStack(
            languages=languages,
            frameworks=sorted(detected_frameworks),
            databases=databases,
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
            raw, project_type, metadata,
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
    def _build_workspace_summary(raw: dict, project_type: str, metadata) -> str:
        parts: list[str] = []

        file_count = raw["total_files"]
        folder_count = raw["total_folders"]
        size_bytes = raw["workspace_size"]

        size_str = _format_size(size_bytes)

        parts.append(
            f"Project contains {file_count} file{'s' if file_count != 1 else ''} "
            f"across {folder_count} director{'y' if folder_count == 1 else 'ies'} "
            f"({size_str})."
        )

        langs = raw.get("languages", [])
        if langs:
            top_langs = langs[:3]
            parts.append(f"Primary language{'s' if len(top_langs) > 1 else ''}: {', '.join(top_langs)}.")

        if project_type and project_type != "Unknown":
            parts.append(f"Detected as a {project_type} project.")

        meta_langs = getattr(metadata, "languages", None) or []
        meta_frameworks = getattr(metadata, "frameworks", None) or []
        if meta_frameworks:
            parts.append(f"Framework{'s' if len(meta_frameworks) > 1 else ''}: {', '.join(sorted(meta_frameworks))}.")

        cfg = raw.get("config_flags", {})
        configs_present = []
        if cfg.get("readme"): configs_present.append("README")
        if cfg.get("dockerfile"): configs_present.append("Dockerfile")
        if cfg.get("docker_compose"): configs_present.append("Docker Compose")
        if cfg.get("gitignore"): configs_present.append(".gitignore")
        if configs_present:
            parts.append(f"Config: {', '.join(configs_present)}.")

        cat = raw.get("folder_categories", {})
        has_frontend = cat.get("frontend", 0) > 0
        has_backend = cat.get("backend", 0) > 0
        has_tests = cat.get("tests", 0) > 0
        has_docs = cat.get("docs", 0) > 0

        if has_frontend and has_backend:
            parts.append("Both frontend and backend directories detected.")
        elif has_frontend:
            parts.append("Frontend directories detected.")
        elif has_backend:
            parts.append("Backend directories detected.")

        if has_tests:
            parts.append("Test directories present.")
        if has_docs:
            parts.append("Documentation directories present.")

        return " ".join(parts)


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
