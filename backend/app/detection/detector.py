import json
import os
import re
from pathlib import Path

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
    ".h": "C",
    ".hpp": "C++",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SCSS",
    ".less": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".swift": "Swift",
    ".r": "R",
    ".m": "Objective-C",
    ".mm": "Objective-C",
    ".dart": "Dart",
    ".lua": "Lua",
    ".pl": "Perl",
    ".pm": "Perl",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".clj": "Clojure",
    ".cljs": "Clojure",
    ".scala": "Scala",
    ".groovy": "Groovy",
}

CONFIG_FILES: set[str] = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "README.md",
    "README.rst",
    "README.txt",
    ".env.example",
    ".env",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "angular.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Cargo.toml",
    "composer.json",
    "Gemfile",
    "Podfile",
    "CMakeLists.txt",
    "Makefile",
    "Rakefile",
    "setup.py",
    "setup.cfg",
    "go.mod",
    "go.sum",
    ".gitignore",
    ".dockerignore",
    "nginx.conf",
    ".github/workflows/main.yml",
    ".github/workflows/deploy.yml",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
}

IMAGE_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".bmp", ".tiff", ".avif",
}

VIDEO_EXTENSIONS: set[str] = {
    ".mp4", ".webm", ".avi", ".mov", ".mkv", ".wmv",
}

ASSET_EXTENSIONS: set[str] = {
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".wav", ".ogg", ".flac",
    ".pdf",
}


def detect_languages(workspace: Path) -> dict[str, int]:
    lang_counts: dict[str, int] = {}
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in _IGNORED_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXTENSION_LANGUAGE_MAP:
                lang = EXTENSION_LANGUAGE_MAP[ext]
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
    return lang_counts


def detect_frameworks(workspace: Path, languages: dict[str, int]) -> set[str]:
    frameworks: set[str] = set()

    pkg_json = workspace / "package.json"
    if pkg_json.exists():
        deps = _parse_package_json_deps(pkg_json)
        framework_map = {
            "react": "React",
            "next": "Next.js",
            "vue": "Vue",
            "angular": "Angular",
            "express": "Express",
            "@nestjs/core": "NestJS",
            "electron": "Electron",
            "react-native": "React Native",
            "gatsby": "Gatsby",
            "nuxt": "Nuxt",
            "svelte": "Svelte",
        }
        for key, name in framework_map.items():
            if key in deps:
                frameworks.add(name)

    pyproject = workspace / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        if "django" in content.lower():
            frameworks.add("Django")
        if "fastapi" in content.lower():
            frameworks.add("FastAPI")
        if "flask" in content.lower():
            frameworks.add("Flask")

    requirements = workspace / "requirements.txt"
    if requirements.exists():
        content = requirements.read_text(encoding="utf-8", errors="ignore").lower()
        if "django" in content:
            frameworks.add("Django")
        if "fastapi" in content:
            frameworks.add("FastAPI")
        if "flask" in content:
            frameworks.add("Flask")

    spring_files = list(workspace.rglob("pom.xml")) + list(workspace.rglob("build.gradle"))
    if spring_files and "Java" in languages:
        for sf in spring_files:
            content = sf.read_text(encoding="utf-8", errors="ignore").lower()
            if "spring" in content:
                frameworks.add("Spring Boot")
                break

    laravel = workspace / "composer.json"
    if laravel.exists():
        content = laravel.read_text(encoding="utf-8", errors="ignore").lower()
        if "laravel" in content:
            frameworks.add("Laravel")

    asp = list(workspace.rglob("*.csproj"))
    if asp:
        for f in asp:
            content = f.read_text(encoding="utf-8", errors="ignore").lower()
            if "microsoft.aspnetcore" in content:
                frameworks.add("ASP.NET")
                break

    if not frameworks:
        if "JavaScript" in languages or "TypeScript" in languages:
            if pkg_json.exists():
                frameworks.add("Node.js")

    return frameworks


def detect_package_manager(workspace: Path) -> str | None:
    if (workspace / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (workspace / "yarn.lock").exists():
        return "yarn"
    if (workspace / "package-lock.json").exists():
        return "npm"
    if (workspace / "poetry.lock").exists() or (workspace / "pyproject.toml").exists():
        return "poetry"
    if (workspace / "Pipfile").exists() or (workspace / "requirements.txt").exists():
        return "pip"
    if (workspace / "build.gradle").exists() or (workspace / "build.gradle.kts").exists():
        return "gradle"
    if (workspace / "pom.xml").exists():
        return "maven"
    if (workspace / "Cargo.toml").exists():
        return "cargo"
    if (workspace / "go.mod").exists():
        return "go"
    if (workspace / "composer.json").exists():
        return "composer"
    return None


def detect_databases(workspace: Path) -> list[str]:
    databases: set[str] = set()

    pkg_json = workspace / "package.json"
    if pkg_json.exists():
        deps = _parse_package_json_deps(pkg_json)
        db_map = {
            "pg": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mysql2": "MySQL",
            "sqlite3": "SQLite",
            "mongodb": "MongoDB",
            "mongoose": "MongoDB",
            "redis": "Redis",
            "ioredis": "Redis",
            "oracledb": "Oracle",
            "tedious": "SQL Server",
            "mssql": "SQL Server",
        }
        for key, name in db_map.items():
            if key in deps:
                databases.add(name)

    config_files = list(workspace.rglob("*.py")) + list(workspace.rglob("*.env*"))
    for cf in config_files:
        try:
            content = cf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        patterns = {
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mysql": "MySQL",
            "sqlite": "SQLite",
            "mongodb": "MongoDB",
            "redis": "Redis",
            "oracle": "Oracle",
            "sqlserver": "SQL Server",
        }
        for pattern, name in patterns.items():
            if pattern in content.lower():
                databases.add(name)

    req_files = list(workspace.rglob("requirements.txt")) + list(workspace.rglob("pyproject.toml"))
    for rf in req_files:
        try:
            content = rf.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        db_pkgs = {
            "psycopg": "PostgreSQL",
            "psycopg2": "PostgreSQL",
            "asyncpg": "PostgreSQL",
            "sqlalchemy": None,
            "mysqlclient": "MySQL",
            "pymysql": "MySQL",
            "aiomysql": "MySQL",
            "sqlite": "SQLite",
            "pymongo": "MongoDB",
            "motor": "MongoDB",
            "redis": "Redis",
            "cx_oracle": "Oracle",
            "pyodbc": "SQL Server",
        }
        for pkg, name in db_pkgs.items():
            if pkg in content and name:
                databases.add(name)

    return sorted(databases)


def detect_devops(workspace: Path) -> dict[str, bool | list[str]]:
    result: dict[str, bool | list[str]] = {
        "docker": (workspace / "Dockerfile").exists(),
        "docker_compose": (
            (workspace / "docker-compose.yml").exists()
            or (workspace / "docker-compose.yaml").exists()
        ),
        "kubernetes": False,
        "ci_cd": [],
    }

    k8s_dir = workspace / "k8s"
    if k8s_dir.exists():
        result["kubernetes"] = True
    for k8s_file in workspace.rglob("*.yaml"):
        try:
            content = k8s_file.read_text(encoding="utf-8", errors="ignore")
            if "apiVersion:" in content and "kind:" in content:
                result["kubernetes"] = True
                break
        except Exception:
            continue

    gh_actions = workspace / ".github" / "workflows"
    if gh_actions.exists():
        result["ci_cd"].append("GitHub Actions")

    if (workspace / ".gitlab-ci.yml").exists():
        result["ci_cd"].append("GitLab CI")

    if (workspace / "Jenkinsfile").exists():
        result["ci_cd"].append("Jenkins")

    if (workspace / "nginx.conf").exists() or (workspace / "nginx").exists():
        result["nginx"] = True

    return result


def collect_statistics(workspace: Path) -> dict:
    total_files = 0
    total_folders = 0
    total_size = 0
    source_files = 0
    config_count = 0
    doc_count = 0
    image_count = 0
    video_count = 0
    asset_count = 0

    config_names = {f.lower() for f in CONFIG_FILES}
    doc_names = {"readme.md", "readme.rst", "readme.txt", "readme",
                 "contributing.md", "changelog.md", "license", "license.md"}

    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in _IGNORED_DIRS]
        if dirs:
            total_folders += len(dirs)
        for file in files:
            total_files += 1
            try:
                fp = os.path.join(root, file)
                total_size += os.path.getsize(fp)
            except OSError:
                pass

            name_lower = file.lower()
            ext = os.path.splitext(file)[1].lower()

            if ext in EXTENSION_LANGUAGE_MAP:
                source_files += 1
            elif name_lower in config_names or name_lower in doc_names:
                config_count += 1
            elif ext in IMAGE_EXTENSIONS:
                image_count += 1
            elif ext in VIDEO_EXTENSIONS:
                video_count += 1
            elif ext in ASSET_EXTENSIONS:
                asset_count += 1

    return {
        "total_files": total_files,
        "total_folders": total_folders,
        "total_size_bytes": total_size,
        "source_files": source_files,
        "config_files_count": config_count,
        "documentation_files": doc_count,
        "image_files": image_count,
        "video_files": video_count,
        "asset_files": asset_count,
    }


def _parse_package_json_deps(pkg_path: Path) -> set[str]:
    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, Exception):
        return set()
    deps: set[str] = set()
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        section_data = data.get(section, {})
        if isinstance(section_data, dict):
            deps.update(section_data.keys())
    return deps


_IGNORED_DIRS: set[str] = {
    "node_modules", ".git", ".venv", "venv", "__pycache__",
    "dist", "build", "coverage", ".next", "target", "vendor",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".eggs", "eggs", ".svn",
}
