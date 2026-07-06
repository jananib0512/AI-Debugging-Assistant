import os
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult, ProjectScanner

MODULE_PATTERNS: list[dict] = [
    {"name": "Authentication", "directories": ["auth", "authentication", "login"], "imports": ["flask_login", "flask-login", "flask_login", "flask_httpauth", "flask-httpauth", "django.contrib.auth", "jose", "pyjwt", "python-jose", "passlib", "oauthlib"], "core": True},
    {"name": "Authorization", "directories": ["authorization", "permissions", "roles", "rbac"], "imports": ["casl", "ability", "cancan", "pundit"], "core": True},
    {"name": "API", "directories": ["api", "endpoints", "gateway"], "imports": ["fastapi", "flask_restful", "flask-restful", "flask_restx", "flask-restx", "django_rest_framework", "djangorestframework", "rest_framework"], "core": True},
    {"name": "Controllers", "directories": ["controllers", "controller"], "imports": [], "core": True},
    {"name": "Routes", "directories": ["routes", "router", "routing"], "imports": [], "core": True},
    {"name": "Services", "directories": ["services", "service", "business"], "imports": [], "core": True},
    {"name": "Repositories", "directories": ["repositories", "repository", "dal", "data-access"], "imports": [], "core": True},
    {"name": "Models", "directories": ["models", "model", "entities", "entity"], "imports": ["sqlalchemy", "django.db", "peewee", "pony", "tortoise", "beanie", "mongoengine"], "core": True},
    {"name": "Database", "directories": ["database", "db", "migrations", "schema", "prisma"], "imports": ["sqlalchemy", "psycopg2", "pymysql", "redis", "pymongo", "motor"], "core": True},
    {"name": "Configuration", "directories": ["config", "configuration", "settings", "env"], "imports": [], "core": True},
    {"name": "Utilities", "directories": ["utils", "util", "helpers", "helper", "common", "shared"], "imports": [], "core": True},
    {"name": "Middleware", "directories": ["middleware", "middlewares"], "imports": [], "core": False},
    {"name": "Components", "directories": ["components", "component"], "imports": [], "core": False},
    {"name": "Pages", "directories": ["pages", "screens"], "imports": [], "core": False},
    {"name": "Logging", "directories": ["logging", "logs", "logger"], "imports": ["logging", "loguru", "structlog"], "core": False},
    {"name": "Caching", "directories": ["cache", "caching"], "imports": ["redis", "django.core.cache", "flask_caching", "flask-caching"], "core": False},
    {"name": "Localization", "directories": ["locales", "i18n", "localization", "translations", "lang"], "imports": ["flask_babel", "flask-babel", "django.utils.translation", "gettext"], "core": False},
    {"name": "Storage", "directories": ["storage", "uploads", "files", "media"], "imports": ["boto3", "google.cloud.storage", "azure.storage", "minio"], "core": False},
    {"name": "ML/AI", "directories": ["ml", "ai", "training", "notebooks", "datasets"], "imports": ["tensorflow", "torch", "sklearn", "scikit-learn", "keras", "transformers", "xgboost", "lightgbm", "onnx", "pandas", "numpy"], "core": False},
    {"name": "Reports", "directories": ["reports", "report", "analytics", "analysis"], "imports": [], "core": False},
    {"name": "Validation", "directories": ["validation", "validators", "validations"], "imports": ["pydantic", "marshmallow", "cerberus", "voluptuous", "schema"], "core": False},
    {"name": "Templates", "directories": ["templates", "template", "views"], "imports": ["jinja2", "mako", "mustache", "handlebars"], "core": False},
    {"name": "Static Files", "directories": ["static", "public", "dist", "build"], "imports": [], "core": False},
    {"name": "Scripts", "directories": ["scripts", "script", "bin"], "imports": [], "core": False},
    {"name": "Tests", "directories": ["tests", "test", "__tests__", "spec", "specs", "e2e", "integration"], "imports": ["pytest", "unittest", "jest", "mocha", "chai", "vitest"], "core": True},
    {"name": "Documentation", "directories": ["docs", "documentation", "wiki"], "imports": [], "core": False},
    {"name": "Assets", "directories": ["assets"], "imports": [], "core": False},
]

EXECUTABLE_MODULE_NAMES: set[str] = {
    "auth", "api", "routes", "services", "controllers", "middleware",
    "config", "models", "database", "db", "utils", "helpers",
    "tests", "docs", "scripts",
}

EXECUTABLE_EXTENSIONS: set[str] = {".py", ".js", ".ts", ".jsx", ".tsx", ".sh", ".go", ".rs"}


class ModuleDetectorRepository:
    def __init__(self, scan_result: ProjectScanResult | None = None) -> None:
        self._scan: ProjectScanResult | None = scan_result

    def scan(self, workspace_path: str) -> None:
        scanner = ProjectScanner()
        self._scan = scanner.scan(Path(workspace_path))

    def _ensure_scan(self) -> ProjectScanResult:
        assert self._scan is not None, "call scan() first"
        return self._scan

    def detect_modules(self) -> list[dict]:
        scan = self._ensure_scan()
        all_dirs = scan.all_dir_names
        root_dirs = {d.lower() for d in scan.root_dirs}
        all_dir_paths = scan.all_dirs

        results: list[dict] = []
        for pattern in MODULE_PATTERNS:
            result = self._detect_single_module(pattern, all_dirs, root_dirs, all_dir_paths, scan)
            results.append(result)

        return results

    def _detect_single_module(
        self,
        pattern: dict,
        all_dir_names: set[str],
        root_dirs: set[str],
        all_dir_paths: set[str],
        scan: ProjectScanResult,
    ) -> dict:
        name = pattern["name"]
        candidates = pattern["directories"]
        imports = pattern.get("imports", [])

        best_match: str | None = None
        best_score = 0.0
        best_path: str | None = None
        detected_files: list[str] = []

        # Check import evidence first (independent of directories)
        matched_imports = [imp for imp in imports if imp in scan.python_imports or imp in scan.js_imports]

        for candidate in candidates:
            score = 0.0

            if candidate in root_dirs:
                score = 0.95
                best_path = candidate
            elif candidate in all_dir_names:
                score = 0.75
                for dp in all_dir_paths:
                    if Path(dp).name.lower() == candidate:
                        best_path = dp
                        break
                if best_path is None:
                    best_path = candidate
            else:
                continue

            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match:
            confidence = min(int(best_score * 100), 75)

            if matched_imports:
                confidence += 20
                confidence = min(confidence, 99)

            detected_files = self._find_files_in_module(
                scan, best_match, best_path,
            )

            folder_path = best_path or best_match
            reason_parts: list[str] = [f"detected via '{best_match}' directory"]
            if matched_imports:
                reason_parts.append(f"import: {matched_imports[0]}")
            if detected_files:
                reason_parts.append(f"{len(detected_files)} file(s)")
            reason = f"{name} functionality {'; '.join(reason_parts)}"

            return {
                "module_name": name,
                "status": "Detected",
                "detected_folder": folder_path,
                "confidence": confidence,
                "reason": reason,
                "core": pattern["core"],
                "detected_files": detected_files[:10],
            }

        if matched_imports:
            confidence = min(40 + len(matched_imports) * 10, 70)
            return {
                "module_name": name,
                "status": "Detected",
                "detected_folder": None,
                "confidence": confidence,
                "reason": f"{name} functionality detected via import: {matched_imports[0]}",
                "core": pattern["core"],
                "detected_files": [],
            }

        return {
            "module_name": name,
            "status": "Not Detected",
            "detected_folder": None,
            "confidence": 0,
            "reason": "No matching module folders identified.",
            "core": pattern["core"],
            "detected_files": [],
        }

    @staticmethod
    def _find_files_in_module(
        scan: ProjectScanResult,
        dir_name: str,
        dir_path: str | None,
    ) -> list[str]:
        if not dir_path:
            return []

        files: list[str] = []
        prefix = dir_path if not dir_path.startswith(".") else dir_name

        for f in scan.all_files:
            if f.startswith(prefix + "/") or (
                not f.startswith(".") and not "/" in f and Path(f).name.lower()
            ):
                ext = os.path.splitext(f)[1].lower()
                if ext in EXECUTABLE_EXTENSIONS:
                    files.append(f)
                    if len(files) >= 10:
                        break

        return files
