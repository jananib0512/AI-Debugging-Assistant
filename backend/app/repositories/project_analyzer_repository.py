import os
import logging
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult, ProjectScanner
from app.repositories.folder_classifier import classify_folders

logger = logging.getLogger(__name__)

IGNORED_DIRS: set[str] = {
    "node_modules", ".git", ".venv", "venv", "__pycache__",
    "dist", "build", "coverage", ".next", "target", "vendor",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".eggs", "eggs", ".svn",
}

HIDDEN_PREFIX = "."

ENTRY_POINT_FILES: dict[str, str] = {
    "main.py": "application",
    "app.py": "application",
    "server.py": "application",
    "manage.py": "application",
    "cli.py": "cli",
    "wsgi.py": "server",
    "asgi.py": "server",
    "index.js": "application",
    "index.ts": "application",
    "main.ts": "application",
    "main.jsx": "application",
    "main.tsx": "application",
    "App.tsx": "application",
    "App.jsx": "application",
    "_app.tsx": "application",
    "_app.jsx": "application",
    "main.go": "application",
    "Program.cs": "application",
    "Program.fs": "application",
    "index.html": "web_entry",
    "entrypoint.sh": "container_entry",
    "entrypoint.py": "container_entry",
    "docker-entrypoint.sh": "container_entry",
    "cmd": "container_entry",
    "main.rs": "application",
    "lib.rs": "library",
    "pubspec.yaml": "application",
}

IMPORTANT_DIR_PURPOSE: dict[str, str] = {
    "src": "Source code",
    "app": "Application logic",
    "backend": "Backend application",
    "frontend": "Frontend application",
    "api": "API endpoints",
    "controllers": "Request handlers",
    "models": "Data models",
    "schemas": "Data schemas",
    "routes": "Route definitions",
    "services": "Business logic",
    "repositories": "Data access layer",
    "components": "UI components",
    "pages": "Page components",
    "hooks": "React hooks",
    "utils": "Utility functions",
    "helpers": "Helper functions",
    "lib": "Library code",
    "core": "Core functionality",
    "config": "Configuration",
    "configuration": "Configuration",
    "settings": "Configuration",
    "tests": "Test suite",
    "__tests__": "Test suite",
    "spec": "Test suite",
    "test": "Test suite",
    "docs": "Documentation",
    "documentation": "Documentation",
    "wiki": "Documentation",
    "public": "Static assets",
    "static": "Static files",
    "assets": "Assets",
    "images": "Image assets",
    "img": "Image assets",
    "icons": "Icon assets",
    "fonts": "Font assets",
    "scripts": "Scripts",
    "bin": "Executables",
    "migrations": "Database migrations",
    "seeds": "Database seeds",
    "db": "Database",
    "database": "Database",
    "middleware": "Middleware",
    "store": "State management",
    "state": "State management",
    "types": "Type definitions",
    "interfaces": "Interface definitions",
    "layouts": "Layout components",
    "features": "Feature modules",
    "modules": "Feature modules",
    "sections": "Page sections",
    "context": "React context",
    "providers": "React providers",
}


class ProjectAnalyzerRepository:
    def __init__(self, workspace_path: Path, scan_result: ProjectScanResult | None = None):
        self.workspace = workspace_path.resolve()
        self._scan: ProjectScanResult | None = scan_result

    def _ensure_scan(self) -> ProjectScanResult:
        if self._scan is None:
            scanner = ProjectScanner()
            self._scan = scanner.scan(self.workspace)
        return self._scan

    def analyze(self) -> dict:
        scan = self._ensure_scan()

        entry_points = self._find_entry_points(scan)

        important_dirs = self._find_important_dirs(scan)

        return {
            "top_level_dirs": scan.root_dirs.copy(),
            "top_level_files": scan.root_files.copy(),
            "all_dirs": sorted(scan.all_dirs),
            "all_files": scan.all_files.copy(),
            "entry_points": entry_points,
            "important_dirs": important_dirs,
            "has_tests": scan.has_tests,
            "has_docs": scan.has_docs,
            "has_scripts": scan.has_scripts,
            "has_src_or_app": scan.has_src_or_app,
            "needs_analysis": scan.needs_analysis,
        }

    def _find_entry_points(self, scan: ProjectScanResult) -> list[dict]:
        found: list[dict] = []
        all_file_set = set(scan.all_files) | set(scan.root_files)

        for fname, etype in ENTRY_POINT_FILES.items():
            if fname in all_file_set:
                found.append({"file_name": fname, "path": fname, "type": etype})
                continue

        for d in scan.all_dirs:
            for fname, etype in ENTRY_POINT_FILES.items():
                candidate = f"{d}/{fname}"
                if candidate in all_file_set:
                    found.append({"file_name": fname, "path": candidate, "type": etype})

        return found

    def _find_important_dirs(self, scan: ProjectScanResult) -> list[dict]:
        found: list[dict] = []
        seen_purposes: set[str] = set()
        all_known_dirs = scan.all_dir_names | {d.lower() for d in scan.root_dirs}

        for d in sorted(all_known_dirs):
            name = Path(d).name.lower()
            purpose = IMPORTANT_DIR_PURPOSE.get(name)
            if purpose and purpose not in seen_purposes:
                seen_purposes.add(purpose)
                found.append({"name": name, "path": d, "purpose": purpose})

        return found

    def scan(self, project_type: str = "") -> dict:
        scan = self._ensure_scan()

        language_counts = scan.language_counts.copy()
        folder_categories = classify_folders(scan, project_type, language_counts)

        config_file_names = {"config.py", "settings.py", ".env", ".env.example"}
        for f in scan.root_files:
            f_lower = f.lower()
            if f_lower in config_file_names:
                dedup_key = f"__file__{f_lower}"
                if dedup_key not in folder_categories:
                    folder_categories["config"] += 1

        config_flags = scan.config_flags.copy()

        return {
            "total_files": scan.total_files,
            "total_folders": scan.total_folders,
            "workspace_size": scan.workspace_size,
            "folder_categories": folder_categories,
            "languages": sorted(scan.language_counts.keys(), key=lambda l: -scan.language_counts[l]),
            "language_counts": scan.language_counts.copy(),
            "config_flags": config_flags,
            "needs_analysis": scan.needs_analysis,
        }

    def has_workspace(self) -> bool:
        return self.workspace.exists() and any(self.workspace.iterdir())
