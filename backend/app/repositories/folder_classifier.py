from pathlib import Path

from app.detection.project_scanner import ProjectScanResult


PROJECT_TYPE_MAPPINGS: dict[str, dict[str, set[str]]] = {
    "Flask": {
        "frontend": {"templates", "static", "static/css", "static/js", "static/images", "static/fonts"},
        "backend": {"routes", "services", "models", "instance", "controllers", "middleware"},
        "source": {"utils", "core", "config", "database", "data"},
    },
    "Django": {
        "frontend": {"templates", "static"},
        "backend": {"apps", "models", "views", "urls", "admin", "forms", "serializers", "signals"},
        "source": {"utils", "core", "config", "settings", "wsgi", "asgi"},
    },
    "FastAPI": {
        "frontend": {"templates", "static"},
        "backend": {"routes", "api", "services", "models", "controllers", "middleware"},
        "source": {"utils", "core", "config", "database", "data", "schemas"},
    },
    "React": {
        "frontend": {"src", "public", "components", "pages", "hooks", "layouts", "styles"},
        "backend": set(),
        "source": {"utils", "lib", "helpers", "types", "api"},
    },
    "Vue": {
        "frontend": {"src", "public", "components", "pages", "layouts", "assets", "router", "store"},
        "backend": set(),
        "source": {"utils", "lib", "helpers", "types"},
    },
    "Angular": {
        "frontend": {"src", "public", "components", "pages", "shared", "core", "features"},
        "backend": set(),
        "source": {"utils", "services", "guards", "interceptors"},
    },
    "Express": {
        "frontend": {"public", "views", "static"},
        "backend": {"routes", "controllers", "services", "models", "middleware"},
        "source": {"utils", "config", "helpers", "lib"},
    },
    "Next.js": {
        "frontend": {"pages", "app", "components", "public", "styles", "hooks", "layouts"},
        "backend": {"api"},
        "source": {"utils", "lib", "helpers", "types"},
    },
    "Laravel": {
        "frontend": {"resources", "public"},
        "backend": {"app", "routes", "controllers", "models", "middleware"},
        "source": {"config", "database", "bootstrap"},
    },
    "Spring Boot": {
        "frontend": {"static", "templates", "public"},
        "backend": {"controller", "service", "repository", "model", "entity", "config", "security"},
        "source": {"util", "dto", "exception", "mapper"},
    },
}

GENERIC_FOLDER_MAP: dict[str, str] = {
    "frontend": "frontend",
    "client": "frontend",
    "ui": "frontend",
    "backend": "backend",
    "server": "backend",
    "api": "backend",
    "src": "source",
    "app": "source",
    "core": "source",
    "lib": "source",
    "utils": "source",
    "helpers": "source",
    "types": "source",
    "interfaces": "source",
    "context": "source",
    "store": "source",
    "state": "source",
    "hooks": "source",
    "models": "backend",
    "schemas": "source",
    "entities": "backend",
    "validators": "source",
    "config": "config",
    "configuration": "config",
    "settings": "config",
    ".github": "config",
    "assets": "assets",
    "images": "assets",
    "img": "assets",
    "icons": "assets",
    "fonts": "assets",
    "docs": "docs",
    "documentation": "docs",
    "wiki": "docs",
    "tests": "tests",
    "__tests__": "tests",
    "spec": "tests",
    "test": "tests",
    "e2e": "tests",
    "integration": "tests",
    "scripts": "scripts",
    "bin": "scripts",
    "templates": "frontend",
    "views": "frontend",
    "static": "frontend",
    "public": "frontend",
    "pages": "frontend",
    "layouts": "frontend",
    "styles": "frontend",
    "css": "assets",
    "sass": "assets",
    "scss": "assets",
    "components": "frontend",
}


def _count_files_in_dir(scan: ProjectScanResult, dir_path: str) -> int:
    prefix = dir_path + "/" if dir_path else ""
    return sum(1 for f in scan.all_files if f.startswith(prefix))


def _normalize_dir_paths(all_dirs: set[str]) -> list[tuple[str, str, int]]:
    result: list[tuple[str, str, int]] = []
    for d in all_dirs:
        depth = len(Path(d).parts)
        leaf_name = Path(d).name.lower()
        result.append((d, leaf_name, depth))
    result.sort(key=lambda x: (x[2], x[0]))
    return result


def classify_folders(
    scan: ProjectScanResult,
    project_type: str,
    language_counts: dict[str, int],
) -> dict[str, int]:
    folder_counts: dict[str, int] = {
        "frontend": 0,
        "backend": 0,
        "source": 0,
        "config": 0,
        "assets": 0,
        "docs": 0,
        "tests": 0,
        "scripts": 0,
        "other": 0,
    }

    project_type_lower = project_type.lower()

    project_key = None
    for known_type in PROJECT_TYPE_MAPPINGS:
        if known_type.lower() in project_type_lower:
            project_key = known_type
            break

    known_frontend_dirs: set[str] = set()
    known_backend_dirs: set[str] = set()
    known_source_dirs: set[str] = set()

    if project_key:
        mapping = PROJECT_TYPE_MAPPINGS[project_key]
        known_frontend_dirs = mapping.get("frontend", set())
        known_backend_dirs = mapping.get("backend", set())
        known_source_dirs = mapping.get("source", set())

    dirs = _normalize_dir_paths(scan.all_dirs)
    counted: set[str] = set()

    def count_dir(d: str, category: str) -> None:
        if d in counted:
            return
        counted.add(d)
        if category in folder_counts:
            folder_counts[category] += 1

    has_html = language_counts.get("HTML", 0) > 0
    has_css = language_counts.get("CSS", 0) > 0
    has_js = language_counts.get("JavaScript", 0) > 0 or language_counts.get("TypeScript", 0) > 0
    has_frontend_langs = has_html or has_css or has_js

    has_static_or_templates = any(
        name in {"static", "templates", "public", "views"}
        for _, name, _ in dirs
    )

    force_frontend = has_frontend_langs and has_static_or_templates

    for full_path, leaf, depth in dirs:
        parts = Path(full_path).parts
        parent = parts[-2].lower() if len(parts) >= 2 else None

        category: str | None = None

        if known_frontend_dirs:
            if leaf in known_frontend_dirs or full_path in known_frontend_dirs:
                category = "frontend"
            elif leaf in known_backend_dirs or full_path in known_backend_dirs:
                category = "backend"
            elif leaf in known_source_dirs or full_path in known_source_dirs:
                category = "source"

        if category is None:
            if parent in ("templates", "static", "public", "views", "frontend"):
                category = "frontend"
            elif parent in ("backend", "server", "api"):
                category = "backend"
            elif leaf in GENERIC_FOLDER_MAP:
                category = GENERIC_FOLDER_MAP[leaf]
            else:
                category = "other"

        if force_frontend and category in ("other", "assets") and leaf in ("css", "js", "images", "img", "fonts", "icons"):
            category = "frontend"

        if force_frontend and leaf in ("static", "templates", "public"):
            category = "frontend"

        count_dir(full_path, category)

    for f in scan.root_files:
        f_lower = f.lower()
        if f_lower in ("config.py", "settings.py", ".env", ".env.example"):
            if f"__config_file_{f_lower}" not in counted:
                counted.add(f"__config_file_{f_lower}")
                folder_counts["config"] += 1

    return folder_counts
