import os
import logging
from pathlib import Path

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

PROJECT_TYPE_DIR_HINTS: dict[str, set[str]] = {
    "monorepo": {"packages", "apps", "modules"},
}

ARCHITECTURE_DIR_PATTERNS: dict[str, set[str]] = {
    "mvc": {"controllers", "models", "views"},
    "layered": {"services", "repositories", "api", "controllers"},
    "clean_architecture": {"entities", "usecases", "adapters", "infrastructure"},
    "hexagonal": {"adapters", "ports", "infrastructure"},
    "feature_based": {"features", "modules"},
}

FOLDER_CATEGORIES: dict[str, set[str]] = {
    "frontend": {"frontend", "client", "ui", "components", "pages", "layouts", "public", "static"},
    "backend": {"backend", "server", "api", "controllers", "services", "repositories", "models", "routes", "middleware", "providers"},
    "source": {"src", "app", "core", "lib", "utils", "helpers", "types", "interfaces", "context", "store", "state", "hooks"},
    "config": {"config", "configuration", "settings", ".github"},
    "assets": {"assets", "images", "img", "icons", "fonts", "styles", "css", "sass", "scss"},
    "docs": {"docs", "documentation", "wiki"},
    "tests": {"tests", "__tests__", "spec", "test"},
    "scripts": {"scripts", "bin"},
}

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SCSS",
    ".less": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".dart": "Dart",
    ".r": "R",
    ".m": "Objective-C",
    ".mm": "Objective-C",
    ".lua": "Lua",
    ".pl": "Perl",
}

FRAMEWORK_HINTS: dict[str, set[str]] = {
    "react": {"App.tsx", "App.jsx", "jsx", "tsx"},
    "vue": {".vue"},
    "angular": {"angular.json"},
    "svelte": {".svelte"},
    "nextjs": {"next.config"},
    "fastapi": {"main.py"},
    "flask": {"app.py"},
    "django": {"manage.py", "settings.py"},
    "express": {"app.js"},
    "spring": {"pom.xml", "build.gradle"},
}


class ProjectAnalyzerRepository:
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path.resolve()

    def analyze(self) -> dict:
        top_level_dirs: list[str] = []
        top_level_files: list[str] = []
        all_dirs: set[str] = set()
        all_files: set[str] = set()

        if not self.workspace.exists():
            return {
                "top_level_dirs": [],
                "top_level_files": [],
                "all_dirs": [],
                "all_files": [],
                "entry_points": [],
                "important_dirs": [],
                "has_tests": False,
                "has_docs": False,
                "has_scripts": False,
                "has_src_or_app": False,
                "needs_analysis": True,
            }

        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(HIDDEN_PREFIX)]
            rel_root = Path(root).relative_to(self.workspace)
            if rel_root != Path("."):
                parts = rel_root.parts
                if parts and parts[0].startswith(HIDDEN_PREFIX):
                    dirs.clear()
                    continue
                for p in parts:
                    if p in IGNORED_DIRS or p.startswith(HIDDEN_PREFIX):
                        dirs.clear()
                        break

            is_root = rel_root == Path(".")
            for d in dirs:
                rel = str(rel_root / d) if not is_root else d
                all_dirs.add(rel)
                if is_root:
                    top_level_dirs.append(d)

            for f in files:
                if f.startswith(HIDDEN_PREFIX):
                    continue
                rel = str(rel_root / f) if not is_root else f
                all_files.add(rel)
                if is_root:
                    top_level_files.append(f)

        entry_points = self._find_entry_points(top_level_files, all_files, all_dirs)
        important_dirs = self._find_important_dirs(all_dirs)
        has_tests = self._has_tests(all_dirs)
        has_docs = self._has_docs(all_dirs)
        has_scripts = self._has_scripts(all_dirs, top_level_files)
        has_src_or_app = self._has_src_or_app(top_level_dirs)

        return {
            "top_level_dirs": top_level_dirs,
            "top_level_files": top_level_files,
            "all_dirs": sorted(all_dirs),
            "all_files": sorted(all_files),
            "entry_points": entry_points,
            "important_dirs": important_dirs,
            "has_tests": has_tests,
            "has_docs": has_docs,
            "has_scripts": has_scripts,
            "has_src_or_app": has_src_or_app,
            "needs_analysis": False,
        }

    def _find_entry_points(
        self,
        top_level_files: list[str],
        all_files: set[str],
        all_dirs: set[str],
    ) -> list[dict]:
        found: list[dict] = []
        candidates = set(top_level_files) | all_files
        for fname, etype in ENTRY_POINT_FILES.items():
            if fname in candidates:
                found.append({"file_name": fname, "path": fname, "type": etype})
                continue
            if fname in all_files:
                found.append({"file_name": fname, "path": fname, "type": etype})
                continue
        for d in all_dirs:
            for fname, etype in ENTRY_POINT_FILES.items():
                candidate = f"{d}/{fname}"
                if candidate in all_files:
                    found.append({"file_name": fname, "path": candidate, "type": etype})
        return found

    def _find_important_dirs(self, all_dirs: set[str]) -> list[dict]:
        found: list[dict] = []
        seen_purposes: set[str] = set()
        for d in sorted(all_dirs):
            name = Path(d).name.lower()
            purpose = IMPORTANT_DIR_PURPOSE.get(name)
            if purpose:
                if purpose not in seen_purposes:
                    seen_purposes.add(purpose)
                    found.append({"name": name, "path": d, "purpose": purpose})
            else:
                parts = Path(d).parts
                for part in parts:
                    part_lower = part.lower()
                    if part_lower in IMPORTANT_DIR_PURPOSE and part_lower != name:
                        purpose = IMPORTANT_DIR_PURPOSE[part_lower]
                        if purpose not in seen_purposes:
                            seen_purposes.add(purpose)
                            found.append({"name": part_lower, "path": d, "purpose": purpose})
        return found

    @staticmethod
    def _has_tests(all_dirs: set[str]) -> bool:
        for d in all_dirs:
            name = Path(d).name.lower()
            if name in {"tests", "__tests__", "spec", "test"}:
                return True
        return False

    @staticmethod
    def _has_docs(all_dirs: set[str]) -> bool:
        for d in all_dirs:
            name = Path(d).name.lower()
            if name in {"docs", "documentation", "wiki"}:
                return True
        return False

    @staticmethod
    def _has_scripts(all_dirs: set[str], top_level_files: list[str]) -> bool:
        for d in all_dirs:
            name = Path(d).name.lower()
            if name in {"scripts", "bin"}:
                return True
        for f in top_level_files:
            if f.startswith("scripts") or f.startswith("bin"):
                return True
        return False

    @staticmethod
    def _has_src_or_app(top_level_dirs: list[str]) -> bool:
        names = {d.lower() for d in top_level_dirs}
        return bool(names & {"src", "app"})

    def scan(self) -> dict:
        total_files = 0
        total_folders = 0
        workspace_size = 0
        folder_categories: dict[str, int] = {k: 0 for k in FOLDER_CATEGORIES}
        folder_categories["other"] = 0
        language_counts: dict[str, int] = {}
        config_flags: dict[str, bool] = {
            "package_json": False,
            "requirements_txt": False,
            "dockerfile": False,
            "docker_compose": False,
            "readme": False,
            "pyproject_toml": False,
            "env_example": False,
            "gitignore": False,
        }

        if not self.workspace.exists():
            return self._empty_scan(config_flags)

        for root_str, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(HIDDEN_PREFIX)]
            root = Path(root_str)
            rel = root.relative_to(self.workspace)
            is_root = rel == Path(".")

            if not is_root:
                parts = rel.parts
                if parts and parts[0].startswith(HIDDEN_PREFIX):
                    dirs.clear()
                    continue
                skip = False
                for p in parts:
                    if p in IGNORED_DIRS or p.startswith(HIDDEN_PREFIX):
                        skip = True
                        break
                if skip:
                    dirs.clear()
                    continue

            for d in dirs:
                total_folders += 1
                categorized = False
                for cat, keywords in FOLDER_CATEGORIES.items():
                    if d.lower() in keywords:
                        folder_categories[cat] += 1
                        categorized = True
                        break
                if not categorized:
                    folder_categories["other"] += 1

            for f in files:
                if f.startswith(HIDDEN_PREFIX) and f.lower() not in {
                    ".env", ".env.example", ".gitignore", ".dockerignore",
                }:
                    continue
                total_files += 1
                fp = root / f
                try:
                    workspace_size += fp.stat().st_size
                except OSError:
                    pass

                ext = os.path.splitext(f)[1].lower()
                if ext in EXTENSION_LANGUAGE_MAP:
                    lang = EXTENSION_LANGUAGE_MAP[ext]
                    language_counts[lang] = language_counts.get(lang, 0) + 1

                f_lower = f.lower()
                if f_lower == "package.json":
                    config_flags["package_json"] = True
                elif f_lower == "requirements.txt":
                    config_flags["requirements_txt"] = True
                elif f_lower in ("dockerfile",):
                    config_flags["dockerfile"] = True
                elif f_lower in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
                    config_flags["docker_compose"] = True
                elif f_lower.startswith("readme"):
                    config_flags["readme"] = True
                elif f_lower == "pyproject.toml":
                    config_flags["pyproject_toml"] = True
                elif f_lower == ".env.example":
                    config_flags["env_example"] = True
                elif f_lower == ".gitignore":
                    config_flags["gitignore"] = True

        sorted_languages = sorted(language_counts.keys(), key=lambda l: -language_counts[l])

        return {
            "total_files": total_files,
            "total_folders": total_folders,
            "workspace_size": workspace_size,
            "folder_categories": folder_categories,
            "languages": sorted_languages,
            "language_counts": language_counts,
            "config_flags": config_flags,
            "needs_analysis": False,
        }

    @staticmethod
    def _empty_scan(config_flags: dict[str, bool]) -> dict:
        return {
            "total_files": 0,
            "total_folders": 0,
            "workspace_size": 0,
            "folder_categories": {k: 0 for k in FOLDER_CATEGORIES} | {"other": 0},
            "languages": [],
            "language_counts": {},
            "config_flags": config_flags,
            "needs_analysis": True,
        }

    def has_workspace(self) -> bool:
        return self.workspace.exists() and any(self.workspace.iterdir())
