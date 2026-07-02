import os
import logging
from pathlib import Path

from app.schemas.config_detection import ConfigFilesDetectionResult

logger = logging.getLogger(__name__)

STRUCTURE_DIRS: set[str] = {
    "frontend", "src", "client", "ui", "app",
}

BACKEND_DIRS: set[str] = {
    "backend", "server", "api", "services", "core",
}

SOURCE_DIRS: set[str] = {
    "src", "lib", "app", "core", "components", "utils", "helpers",
}

CONFIG_DIR_NAMES: set[str] = {
    "config", "configuration", "settings",
}

ASSETS_DIRS: set[str] = {
    "assets", "static", "public", "images", "img", "icons", "fonts",
}

DOCS_DIRS: set[str] = {
    "docs", "documentation", "wiki",
}

HIDDEN_PREFIX = "."

SOURCE_EXTENSIONS: set[str] = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".rb", ".html",
    ".htm", ".css", ".scss", ".sass", ".less", ".sql", ".sh",
    ".bash", ".kt", ".kts", ".swift", ".r", ".dart", ".lua",
    ".pl", ".pm", ".ex", ".exs", ".clj", ".cljs", ".scala",
    ".groovy", ".yml", ".yaml", ".json", ".xml", ".toml",
    ".cfg", ".ini", ".conf", ".env", ".md", ".rst", ".txt",
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".wav", ".ogg", ".flac",
    ".mp4", ".webm", ".avi", ".mov", ".mkv",
    ".pdf",
}

IGNORED_DIRS: set[str] = {
    "node_modules", ".git", ".venv", "venv", "__pycache__",
    "dist", "build", "coverage", ".next", "target", "vendor",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".eggs", "eggs", ".svn",
}


class WorkspaceValidationRepository:
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path.resolve()

    def validate_all(
        self, config_result: ConfigFilesDetectionResult,
    ) -> dict:
        return {
            "workspace_exists": self._workspace_exists(),
            "workspace_accessible": self._workspace_accessible(),
            "workspace_not_empty": self._workspace_not_empty(),
            "has_source_files": self._has_source_files(),
            "total_file_count": self._total_file_count(),
            "total_size_bytes": self._total_size_bytes(),
            "corrupted_files": self._find_corrupted_files(),
            "invalid_paths": self._find_invalid_paths(),
            "structure": self._check_structure(),
            "config_files": self._build_config_dict(config_result),
        }

    def _workspace_exists(self) -> bool:
        return self.workspace.exists()

    def _workspace_accessible(self) -> bool:
        return os.access(str(self.workspace), os.R_OK | os.X_OK)

    def _workspace_not_empty(self) -> bool:
        try:
            entries = list(self.workspace.iterdir())
            non_ignored = [e for e in entries if e.name not in IGNORED_DIRS and not e.name.startswith(HIDDEN_PREFIX)]
            return len(non_ignored) > 0
        except PermissionError:
            return False

    def _has_source_files(self) -> int:
        count = 0
        for root, dirs, _ in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            root_path = Path(root)
            if any(part.startswith(HIDDEN_PREFIX) for part in root_path.relative_to(self.workspace).parts if part != "."):
                continue
            for f in os.listdir(root):
                if f.startswith(HIDDEN_PREFIX) or f in IGNORED_DIRS:
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext in SOURCE_EXTENSIONS:
                    count += 1
        return count

    def _total_file_count(self) -> int:
        count = 0
        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            root_path = Path(root)
            if any(part.startswith(HIDDEN_PREFIX) for part in root_path.relative_to(self.workspace).parts if part != "."):
                continue
            for f in files:
                if not f.startswith(HIDDEN_PREFIX) and f not in IGNORED_DIRS:
                    count += 1
        return count

    def _total_size_bytes(self) -> int:
        total = 0
        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            root_path = Path(root)
            if any(part.startswith(HIDDEN_PREFIX) for part in root_path.relative_to(self.workspace).parts if part != "."):
                continue
            for f in files:
                if f.startswith(HIDDEN_PREFIX) or f in IGNORED_DIRS:
                    continue
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        return total

    def _find_corrupted_files(self) -> list[str]:
        corrupted: list[str] = []
        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            root_path = Path(root)
            if any(part.startswith(HIDDEN_PREFIX) for part in root_path.relative_to(self.workspace).parts if part != "."):
                continue
            for f in files:
                if f.startswith(HIDDEN_PREFIX) or f in IGNORED_DIRS:
                    continue
                fp = os.path.join(root, f)
                try:
                    if not os.access(fp, os.R_OK):
                        corrupted.append(os.path.relpath(fp, self.workspace))
                except OSError:
                    corrupted.append(os.path.relpath(fp, self.workspace))
        return corrupted

    def _find_invalid_paths(self) -> list[str]:
        invalid: list[str] = []
        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            root_path = Path(root)
            if any(part.startswith(HIDDEN_PREFIX) for part in root_path.relative_to(self.workspace).parts if part != "."):
                continue
            for name in list(dirs) + files:
                if name in IGNORED_DIRS or name.startswith(HIDDEN_PREFIX):
                    continue
                try:
                    full = os.path.join(root, name)
                    resolved = os.path.realpath(full)
                    if not resolved.startswith(os.path.realpath(self.workspace)):
                        invalid.append(os.path.relpath(full, self.workspace))
                except (OSError, ValueError):
                    invalid.append(os.path.relpath(os.path.join(root, name), self.workspace))
        return invalid

    def _check_structure(self) -> dict:
        has_frontend = False
        has_backend = False
        has_source = False
        has_config = False
        has_assets = False
        has_docs = False
        has_hidden = False
        notes: list[str] = []

        try:
            for entry in self.workspace.iterdir():
                name = entry.name
                if name.startswith(HIDDEN_PREFIX):
                    has_hidden = True
                if not entry.is_dir():
                    continue
                name_lower = name.lower()

                if name_lower in STRUCTURE_DIRS:
                    has_frontend = True
                    has_source = True
                if name_lower in BACKEND_DIRS:
                    has_backend = True
                    has_source = True
                if name_lower in SOURCE_DIRS and name_lower not in STRUCTURE_DIRS | BACKEND_DIRS:
                    has_source = True
                if name_lower in CONFIG_DIR_NAMES:
                    has_config = True
                if name_lower in ASSETS_DIRS:
                    has_assets = True
                if name_lower in DOCS_DIRS:
                    has_docs = True

            if not has_frontend and not has_backend and not has_source:
                notes.append("No standard source directories detected; files may be at the workspace root")
            if not has_frontend:
                notes.append("No frontend directory detected")
            if not has_backend:
                notes.append("No backend directory detected")
            if not has_docs:
                notes.append("No documentation directory detected")
        except PermissionError:
            notes.append("Unable to scan workspace structure due to permissions")

        return {
            "has_frontend": has_frontend,
            "has_backend": has_backend,
            "has_source_folders": has_source,
            "has_config_folder": has_config,
            "has_assets_folder": has_assets,
            "has_documentation_folder": has_docs,
            "has_hidden_folders": has_hidden,
            "notes": notes,
        }

    @staticmethod
    def _build_config_dict(config: ConfigFilesDetectionResult) -> dict:
        missing: list[str] = []
        if not config.package_json:
            missing.append("package.json")
        if not config.requirements_txt:
            missing.append("requirements.txt")
        if not config.pyproject_toml:
            missing.append("pyproject.toml")
        if not config.dockerfile:
            missing.append("Dockerfile")
        if not config.docker_compose:
            missing.append("docker-compose.yml")
        if not config.readme:
            missing.append("README.md")
        if not config.env_example:
            missing.append(".env.example")

        return {
            "has_package_json": config.package_json,
            "has_requirements_txt": config.requirements_txt,
            "has_pyproject_toml": config.pyproject_toml,
            "has_dockerfile": config.dockerfile,
            "has_docker_compose": config.docker_compose,
            "has_readme": config.readme,
            "has_env_example": config.env_example,
            "files_found": config.files_found,
            "files_missing": missing,
        }
