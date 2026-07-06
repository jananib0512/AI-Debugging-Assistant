import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

IGNORED_DIRS: set[str] = {
    "node_modules", ".git", ".venv", "venv", "__pycache__",
    "dist", "build", "coverage", ".next", "target", "vendor",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".eggs", "eggs", ".svn",
    ".gitlab", ".circleci", ".hg", ".bzr", ".serverless",
    ".terraform", ".pytest_cache", ".mypy_cache",
    ".docusaurus", ".cache", ".parcel-cache",
    "__MACOSX", "env",
}

IGNORED_FILES: set[str] = {
    ".ds_store", "thumbs.db", "desktop.ini",
}

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python", ".pyx": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java", ".go": "Go", ".rs": "Rust",
    ".c": "C", ".cpp": "C++", ".h": "C", ".hpp": "C++",
    ".cs": "C#", ".php": "PHP", ".rb": "Ruby",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sass": "SCSS", ".less": "SCSS",
    ".sql": "SQL", ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".swift": "Swift", ".r": "R", ".m": "Objective-C", ".mm": "Objective-C",
    ".dart": "Dart", ".lua": "Lua", ".pl": "Perl", ".pm": "Perl",
    ".ex": "Elixir", ".exs": "Elixir",
    ".clj": "Clojure", ".cljs": "Clojure",
    ".scala": "Scala", ".groovy": "Groovy",
    ".vue": "Vue", ".svelte": "Svelte",
    ".astro": "Astro", ".sol": "Solidity",
    ".zig": "Zig", ".nim": "Nim",
    ".tf": "Terraform", ".hcl": "Terraform",
    ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".json": "JSON", ".xml": "XML", ".md": "Markdown",
    ".dockerfile": "Docker",
}

LANGUAGE_REVERSE_MAP: dict[str, set[str]] = {}
for _ext, _lang in EXTENSION_LANGUAGE_MAP.items():
    LANGUAGE_REVERSE_MAP.setdefault(_lang, set()).add(_ext)

IMAGE_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".bmp", ".tiff", ".avif",
}
VIDEO_EXTENSIONS: set[str] = {
    ".mp4", ".webm", ".avi", ".mov", ".mkv", ".wmv",
}
ARCHIVE_EXTENSIONS: set[str] = {
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
}
TEMPLATE_EXTENSIONS: set[str] = {
    ".jinja", ".jinja2", ".mustache", ".hbs", ".handlebars",
    ".ejs", ".pug", ".jade", ".erb", ".haml",
}
ASSET_EXTENSIONS: set[str] = {
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".wav", ".ogg", ".flac", ".pdf",
}
SCRIPT_EXTENSIONS: set[str] = {".sh", ".bash", ".zsh", ".bat", ".cmd", ".ps1"}

DOC_FILENAMES: set[str] = {
    "readme.md", "readme.rst", "readme.txt", "readme",
    "contributing.md", "changelog.md", "license", "license.md",
    "code_of_conduct.md", "security.md", "support.md",
}

DOC_FILENAMES_LOWER: set[str] = {f.lower() for f in DOC_FILENAMES}

CONFIG_FILENAMES: set[str] = {
    "package.json", "requirements.txt", "pyproject.toml",
    "pipfile", "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml",
    "tsconfig.json", "vite.config.ts", "vite.config.js",
    "next.config.js", "next.config.mjs", "next.config.ts",
    "angular.json", "pom.xml", "build.gradle", "build.gradle.kts",
    "cargo.toml", "composer.json", "gemfile", "podfile",
    "cmakelists.txt", "makefile", "setup.py", "setup.cfg",
    "go.mod", "go.sum", ".gitignore", ".dockerignore",
    "nginx.conf", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "poetry.lock", "cargo.lock",
    "composer.lock", "gemfile.lock",
    ".editorconfig", ".prettierrc", ".eslintrc",
    "eslint.config.js", "tailwind.config.js", "tailwind.config.ts",
    "postcss.config.js", "webpack.config.js", "webpack.config.ts",
    ".env", ".env.example", ".env.sample",
    "manage.py", "settings.py", "wsgi.py", "asgi.py",
    "config.py", "database.py", "db.py",
    "docker-entrypoint.sh", "entrypoint.sh",
    ".phpunit.xml", "phpunit.xml",
    ".hound.yml", ".travis.yml", "appveyor.yml",
}

IMPORT_PATTERNS: dict[str, list[str]] = {
    "fastapi": [r"from\s+fastapi\s+import", r"import\s+fastapi"],
    "flask": [r"from\s+flask\s+import", r"import\s+flask"],
    "django": [r"from\s+django\s+import", r"import\s+django", r"django\.conf"],
    "sqlalchemy": [r"from\s+sqlalchemy\s+import", r"import\s+sqlalchemy"],
    "flask_sqlalchemy": [r"flask_sqlalchemy", r"flask\.sqlalchemy"],
    "tensorflow": [r"import\s+tensorflow", r"from\s+tensorflow\s+import"],
    "torch": [r"import\s+torch\b", r"from\s+torch\s+import"],
    "sklearn": [r"import\s+sklearn\b", r"from\s+sklearn\s+import"],
    "pandas": [r"import\s+pandas\b", r"from\s+pandas\s+import"],
    "numpy": [r"import\s+numpy\b", r"from\s+numpy\s+import"],
    "matplotlib": [r"import\s+matplotlib\b", r"from\s+matplotlib\s+import"],
    "react": [r"from\s+['\"]react['\"]", r"require\(['\"]react['\"]\)"],
    "axios": [r"from\s+['\"]axios['\"]", r"require\(['\"]axios['\"]\)"],
    "express": [r"require\(['\"]express['\"]\)", r"from\s+['\"]express['\"]"],
    "vue": [r"from\s+['\"]vue['\"]", r"require\(['\"]vue['\"]\)"],
}

DB_URI_PATTERN = re.compile(
    r"(?:postgres(?:ql)?|mysql|sqlite|mongodb|redis|mssql|oracle)"
    r"(?:\+[a-z]+)?:\/\/[^\s'\"`]+",
    re.IGNORECASE,
)

DB_REF_PATTERN = re.compile(
    r"(?:database|db)_(?:url|uri|name|host|port|password|user|engine|backend)\s*[:=]",
    re.IGNORECASE,
)


@dataclass
class ProjectScanResult:
    workspace_path: Path
    total_files: int = 0
    total_folders: int = 0
    workspace_size: int = 0

    root_files: list[str] = field(default_factory=list)
    root_dirs: list[str] = field(default_factory=list)
    all_files: list[str] = field(default_factory=list)
    all_dirs: set[str] = field(default_factory=set)
    all_dir_names: set[str] = field(default_factory=set)

    file_path_map: dict[str, str] = field(default_factory=dict)
    file_sizes: dict[str, int] = field(default_factory=dict)

    language_counts: dict[str, int] = field(default_factory=dict)
    language_file_map: dict[str, list[str]] = field(default_factory=dict)
    total_source_files: int = 0

    source_file_count: int = 0
    config_file_count: int = 0
    doc_file_count: int = 0
    image_file_count: int = 0
    video_file_count: int = 0
    archive_file_count: int = 0
    template_file_count: int = 0
    asset_file_count: int = 0
    script_file_count: int = 0

    package_json: dict | None = None
    requirements_txt_deps: list[str] = field(default_factory=list)
    pyproject_toml_content: str | None = None
    package_lock_json: dict | None = None
    pnpm_lock_yaml: str | None = None
    yarn_lock: str | None = None
    poetry_lock: str | None = None
    dockerfile_content: str | None = None
    docker_compose_content: str | None = None
    env_example_content: str | None = None
    env_content: str | None = None
    config_py_content: str | None = None
    settings_py_content: str | None = None
    database_py_content: str | None = None
    manage_py_content: str | None = None
    readme_content: str | None = None
    gitignore_content: str | None = None
    dockerignore_content: str | None = None
    nginx_conf_content: str | None = None
    go_mod_content: str | None = None
    composer_json: dict | None = None

    found_configs: dict[str, str] = field(default_factory=dict)
    config_flags: dict[str, bool] = field(default_factory=lambda: {
        "readme": False, "gitignore": False, "env_example": False,
        "dockerfile": False, "docker_compose": False,
        "package_json": False, "requirements_txt": False,
        "pyproject_toml": False, "env": False,
    })

    python_imports: set[str] = field(default_factory=set)
    js_imports: set[str] = field(default_factory=set)
    db_uris: list[str] = field(default_factory=list)
    needs_analysis: bool = True

    has_tests: bool = False
    has_docs: bool = False
    has_scripts: bool = False
    has_src_or_app: bool = False


class ProjectScanner:
    def scan(self, workspace_path: Path) -> ProjectScanResult:
        result = ProjectScanResult(workspace_path=workspace_path)

        if not workspace_path.exists():
            result.needs_analysis = True
            return result

        for root_str, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            root = Path(root_str)
            rel = root.relative_to(workspace_path)
            is_root = rel == Path(".")

            for d in dirs:
                result.total_folders += 1
                if is_root:
                    result.root_dirs.append(d)
                rel_dir = str(rel / d) if not is_root else d
                result.all_dirs.add(rel_dir)
                result.all_dir_names.add(d.lower())

            for f in files:
                if f.startswith(".") and f.lower() not in CONFIG_FILENAMES:
                    continue
                if f.lower() in IGNORED_FILES:
                    continue

                result.total_files += 1
                rel_file = str(rel / f) if not is_root else f
                full_path = str(root / f)
                result.all_files.append(rel_file)
                result.file_path_map[rel_file] = full_path

                try:
                    fsize = os.path.getsize(full_path)
                    result.workspace_size += fsize
                    result.file_sizes[rel_file] = fsize
                except OSError:
                    pass

                if is_root:
                    result.root_files.append(f)

                self._categorize_file(result, f, rel_file, full_path)

        result.needs_analysis = result.total_files == 0

        self._compute_aggregates(result)
        self._scan_imports(result)
        self._detect_db_uris(result)

        return result

    def _categorize_file(
        self, result: ProjectScanResult, fname: str,
        rel_file: str, full_path: str,
    ) -> None:
        ext = os.path.splitext(fname)[1].lower()
        name_lower = fname.lower()

        is_config_file = name_lower in CONFIG_FILENAMES
        is_doc_file = name_lower in DOC_FILENAMES_LOWER or name_lower in DOC_FILENAMES

        if is_config_file:
            result.config_file_count += 1
            self._read_config_file(result, fname, rel_file, full_path)

        if ext in EXTENSION_LANGUAGE_MAP or name_lower == "dockerfile":
            result.source_file_count += 1
            lang = EXTENSION_LANGUAGE_MAP.get(ext, "Docker")
            result.language_counts[lang] = result.language_counts.get(lang, 0) + 1
            result.language_file_map.setdefault(lang, []).append(rel_file)
            result.total_source_files += 1

        if is_doc_file:
            result.doc_file_count += 1
            if not is_config_file:
                self._read_config_file(result, fname, rel_file, full_path)
        elif is_config_file:
            pass
        elif ext in IMAGE_EXTENSIONS:
            result.image_file_count += 1
        elif ext in VIDEO_EXTENSIONS:
            result.video_file_count += 1
        elif ext in ARCHIVE_EXTENSIONS:
            result.archive_file_count += 1
        elif ext in TEMPLATE_EXTENSIONS:
            result.template_file_count += 1
            result.source_file_count += 1
        elif ext in ASSET_EXTENSIONS:
            result.asset_file_count += 1
        elif ext in SCRIPT_EXTENSIONS:
            result.script_file_count += 1

    def _read_config_file(
        self, result: ProjectScanResult, fname: str,
        rel_file: str, full_path: str,
    ) -> None:
        name_lower = fname.lower()
        result.found_configs[rel_file] = full_path

        try:
            content = Path(full_path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = ""

        if name_lower == "package.json" and result.package_json is None:
            try:
                result.package_json = json.loads(content)
                result.config_flags["package_json"] = True
            except json.JSONDecodeError:
                pass

        elif name_lower == "requirements.txt" and not result.requirements_txt_deps:
            result.requirements_txt_deps = self._parse_requirements_txt(content)
            result.config_flags["requirements_txt"] = True

        elif name_lower == "pyproject.toml" and result.pyproject_toml_content is None:
            result.pyproject_toml_content = content
            result.config_flags["pyproject_toml"] = True

        elif name_lower == "package-lock.json" and result.package_lock_json is None:
            try:
                result.package_lock_json = json.loads(content)
            except json.JSONDecodeError:
                pass

        elif name_lower == "pnpm-lock.yaml" and result.pnpm_lock_yaml is None:
            result.pnpm_lock_yaml = content

        elif name_lower == "yarn.lock" and result.yarn_lock is None:
            result.yarn_lock = content

        elif name_lower == "poetry.lock" and result.poetry_lock is None:
            result.poetry_lock = content

        elif name_lower == "dockerfile" and result.dockerfile_content is None:
            result.dockerfile_content = content
            result.config_flags["dockerfile"] = True

        elif name_lower in (
            "docker-compose.yml", "docker-compose.yaml",
            "compose.yml", "compose.yaml",
        ) and result.docker_compose_content is None:
            result.docker_compose_content = content
            result.config_flags["docker_compose"] = True

        elif name_lower == ".env.example" and result.env_example_content is None:
            result.env_example_content = content
            result.config_flags["env_example"] = True

        elif name_lower == ".env" and result.env_content is None:
            result.env_content = content
            result.config_flags["env"] = True

        elif name_lower == "config.py" and result.config_py_content is None:
            result.config_py_content = content

        elif name_lower == "settings.py" and result.settings_py_content is None:
            result.settings_py_content = content

        elif name_lower == "database.py" and result.database_py_content is None:
            result.database_py_content = content

        elif name_lower == "manage.py" and result.manage_py_content is None:
            result.manage_py_content = content

        elif name_lower.startswith("readme") and result.readme_content is None:
            result.readme_content = content
            result.config_flags["readme"] = True

        elif name_lower == ".gitignore" and result.gitignore_content is None:
            result.gitignore_content = content
            result.config_flags["gitignore"] = True

        elif name_lower == ".dockerignore" and result.dockerignore_content is None:
            result.dockerignore_content = content

        elif name_lower == "nginx.conf" and result.nginx_conf_content is None:
            result.nginx_conf_content = content

        elif name_lower == "go.mod" and result.go_mod_content is None:
            result.go_mod_content = content

        elif name_lower == "composer.json" and result.composer_json is None:
            try:
                result.composer_json = json.loads(content)
            except json.JSONDecodeError:
                pass

    @staticmethod
    def _parse_requirements_txt(content: str) -> list[str]:
        deps: list[str] = []
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                pkg = re.split(r"[=<>~!@#;]", line, maxsplit=1)[0].strip().lower()
                extras_match = re.match(r"^([a-zA-Z0-9_.-]+)", pkg)
                if extras_match:
                    deps.append(extras_match.group(1))
        return deps

    @staticmethod
    def _get_npm_deps_from_pkg(pkg: dict | None) -> dict[str, str]:
        if not pkg:
            return {}
        deps: dict[str, str] = {}
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            section_data = pkg.get(section, {})
            if isinstance(section_data, dict):
                deps.update(section_data)
        return deps

    @staticmethod
    def _get_npm_dep_names(pkg: dict | None) -> set[str]:
        return set(ProjectScanner._get_npm_deps_from_pkg(pkg).keys())

    def _compute_aggregates(self, result: ProjectScanResult) -> None:
        result.all_dirs.discard(".")
        result.all_files.sort()

        for dir_name in result.all_dir_names:
            if dir_name in {"tests", "__tests__", "spec", "test", "e2e", "integration"}:
                result.has_tests = True
            if dir_name in {"docs", "documentation", "wiki"}:
                result.has_docs = True
            if dir_name in {"scripts", "bin"}:
                result.has_scripts = True
            if dir_name in {"src", "app"} and "." not in result.root_dirs:
                result.has_src_or_app = True

        if not result.has_src_or_app:
            result.has_src_or_app = any(d in {"src", "app"} for d in result.root_dirs)

    def _scan_imports(self, result: ProjectScanResult) -> None:
        py_files: list[str] = result.language_file_map.get("Python", [])
        limit = min(len(py_files), 50)
        for pf in py_files[:limit]:
            full_path = result.file_path_map.get(pf)
            if not full_path:
                continue
            try:
                content = Path(full_path).read_text(
                    encoding="utf-8", errors="ignore", 
                )
            except Exception:
                continue
            for lib_name, patterns in IMPORT_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, content, re.IGNORECASE):
                        result.python_imports.add(lib_name)
                        break

        js_langs = ["JavaScript", "TypeScript"]
        js_files: list[str] = []
        for jl in js_langs:
            js_files.extend(result.language_file_map.get(jl, []))
        limit = min(len(js_files), 50)
        for jf in js_files[:limit]:
            full_path = result.file_path_map.get(jf)
            if not full_path:
                continue
            try:
                content = Path(full_path).read_text(
                    encoding="utf-8", errors="ignore",
                )
            except Exception:
                continue
            for lib_name, patterns in IMPORT_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, content, re.IGNORECASE):
                        result.js_imports.add(lib_name)
                        break

    def _detect_db_uris(self, result: ProjectScanResult) -> None:
        config_texts: list[str | None] = [
            result.config_py_content,
            result.settings_py_content,
            result.database_py_content,
            result.env_content,
            result.env_example_content,
        ]
        for text in config_texts:
            if not text:
                continue
            uris = DB_URI_PATTERN.findall(text)
            result.db_uris.extend(uris)

        for text in config_texts:
            if not text:
                continue
            if DB_REF_PATTERN.search(text):
                continue

        py_files: list[str] = result.language_file_map.get("Python", [])
        for pf in py_files[:20]:
            full_path = result.file_path_map.get(pf)
            if not full_path:
                continue
            try:
                content = Path(full_path).read_text(
                    encoding="utf-8", errors="ignore",
                )
            except Exception:
                continue
            uris = DB_URI_PATTERN.findall(content)
            result.db_uris.extend(uris)
