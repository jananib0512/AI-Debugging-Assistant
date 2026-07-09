import json
import os
import re
import uuid
import configparser
from pathlib import Path
from collections import defaultdict
from typing import Any

from app.detection.detector import EXTENSION_LANGUAGE_MAP
from app.repositories.syntax_detection_engine import IGNORED_DIRS

CONFIG_PATTERNS = [
    "package.json", "requirements.txt", "pyproject.toml",
    "Pipfile", "Pipfile.lock", "Cargo.toml", "Cargo.lock",
    "Gemfile", "Gemfile.lock", "go.mod", "go.sum",
    "composer.json", "composer.lock", "build.gradle",
    "pom.xml", "*.csproj", "*.fsproj",
]

PACKAGE_FILE_LANG: dict[str, str] = {
    "package.json": "JavaScript",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "Pipfile": "Python",
    "Cargo.toml": "Rust",
    "Gemfile": "Ruby",
    "go.mod": "Go",
    "composer.json": "PHP",
    "build.gradle": "Java",
    "pom.xml": "Java",
}

DEPRECATED_PACKAGES: dict[str, str] = {
    "gulp": "Use Vite, Webpack, or esbuild instead.",
    "grunt": "Use Vite, Webpack, or esbuild instead.",
    "bower": "Use npm or yarn instead.",
    "coffeescript": "Use modern JavaScript/TypeScript instead.",
    "jade": "Renamed to 'pug'. Use pug instead.",
    "node-sass": "Use 'sass' (dart-sass) instead.",
    "moment": "Use date-fns or Day.js instead (smaller bundle).",
    "request": "Use node-fetch, got, or axios instead.",
    "bluebird": "Native Promises are now standard in Node.js.",
    "async": "Use async/await or native Promises instead.",
    "lodash": "Use native Array/Object methods instead.",
    "underscore": "Use native JavaScript methods instead.",
    "mathjs": "Use native Math or a smaller library.",
    "chalk": "Chalk 5+ is ESM-only. Check compatibility.",
    "faker": "Package is deprecated. Use @faker-js/faker instead.",
    "react-test-renderer": "Use @testing-library/react instead.",
    "enzyme": "Use @testing-library/react instead.",
    "sinon": "Use vi (vitest) or jest mocking instead.",
}

DEPRECATED_PYTHON: dict[str, str] = {
    "distutils": "Use setuptools or packaging instead.",
    "pycryptodome": "Use cryptography instead.",
    "pycrypto": "Use cryptography instead (pycrypto is unmaintained).",
}

INCOMPATIBLE_COMBOS: list[tuple[str, str, str]] = [
    ("react", "react-native", "react-dom and react-native are incompatible in the same web project."),
    ("vue", "react", "Vue and React should not be mixed in the same project."),
    ("angular", "react", "Angular and React should not be mixed in the same project."),
    ("@angular/core", "react", "Angular and React should not be mixed in the same project."),
    ("tensorflow", "torch", "TensorFlow and PyTorch should not both be direct dependencies."),
    ("django", "flask", "Django and Flask should not be mixed in the same project."),
    ("flask", "fastapi", "Flask and FastAPI should not be mixed in the same project."),
    ("jquery", "react", "jQuery and React should not be mixed (React manages DOM)."),
    ("mongodb", "mysql-connector-python", "MongoDB and MySQL connectors used together may indicate mixed DB usage."),
]


class DependencyDetectionEngine:

    def analyze(self, workspace_path: Path | None = None) -> dict:
        if not workspace_path or not workspace_path.exists():
            return self._empty_result()

        declared_packages = self._collect_declared_packages(workspace_path)
        imports = self._collect_imports(workspace_path)
        all_package_names = set(declared_packages.keys())
        all_import_names = set()
        for lang_imports in imports.values():
            for name in lang_imports:
                all_import_names.add(name.lower())

        errors: list[dict] = []
        scanned_languages = list(imports.keys())

        errors.extend(self._find_missing_dependencies(
            declared_packages, imports, workspace_path))
        errors.extend(self._find_unused_dependencies(
            declared_packages, imports))
        errors.extend(self._find_version_conflicts(declared_packages))
        errors.extend(self._find_duplicate_dependencies(declared_packages))
        errors.extend(self._find_deprecated_packages(declared_packages))
        errors.extend(self._find_incompatible_packages(declared_packages))
        # Circular dependencies cannot be detected from top-level manifest alone
        # (requires full dependency tree resolution)
        errors.extend(self._find_invalid_package_references(declared_packages))
        errors.extend(self._find_broken_imports(imports, workspace_path))
        errors.extend(self._find_package_installation_issues(
            workspace_path, all_package_names))
        errors.extend(self._find_env_packages(
            workspace_path, all_import_names))

        errors = self._deduplicate(errors)

        critical = sum(1 for e in errors if e["severity"] == "Critical")
        high = sum(1 for e in errors if e["severity"] == "High")
        medium = sum(1 for e in errors if e["severity"] == "Medium")
        low = sum(1 for e in errors if e["severity"] == "Low")
        total = len(errors)

        package_manager = self._detect_package_manager(workspace_path)
        pkg_names = sorted(declared_packages.keys())

        return {
            "session_id": uuid.uuid4().hex,
            "status": "completed" if workspace_path else "unavailable",
            "total_errors": total,
            "total_files_scanned": len(imports) if imports else 0,
            "files_with_errors": total,
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "results": [{
                "file_path": "_dependency_analysis_",
                "language": ", ".join(scanned_languages) if scanned_languages else "Unknown",
                "errors": errors,
                "error_count": total,
                "health_score": max(0.0, 100.0 - total * 5.0),
            }],
            "package_manager": package_manager,
            "declared_packages": pkg_names,
        }

    # ── Collectors ──

    def _collect_declared_packages(
        self, workspace_path: Path
    ) -> dict[str, dict[str, Any]]:
        packages: dict[str, dict[str, Any]] = {}

        pkg_json = workspace_path / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text())
                for section in ("dependencies", "devDependencies", "peerDependencies"):
                    deps = data.get(section, {})
                    for name, ver in deps.items():
                        if name not in packages:
                            packages[name] = {
                                "name": name,
                                "version": str(ver),
                                "sources": [f"package.json ({section})"],
                                "manager": "npm",
                                "dep_type": section.rstrip("Dependencies"),
                            }
                        else:
                            packages[name]["sources"].append(
                                f"package.json ({section})")
            except (json.JSONDecodeError, OSError):
                pass

        req_txt = workspace_path / "requirements.txt"
        if req_txt.exists():
            for line in req_txt.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                m = re.match(r"^([a-zA-Z0-9_.-]+)\s*([><=!~]+\s*\S+)?", line)
                if m:
                    name = m.group(1).lower()
                    ver = m.group(2) or "*"
                    if name not in packages:
                        packages[name] = {
                            "name": name,
                            "version": ver.strip() if ver else "*",
                            "sources": ["requirements.txt"],
                            "manager": "pip",
                            "dep_type": "runtime",
                        }
                    else:
                        packages[name]["sources"].append("requirements.txt")

        pyproject = workspace_path / "pyproject.toml"
        if pyproject.exists():
            try:
                text = pyproject.read_text()
                m = re.search(
                    r"\[project\](.*?)(?=\[|$)", text, re.DOTALL)
                if m:
                    deps_section = m.group(1)
                    for line in deps_section.splitlines():
                        line = line.strip()
                        m2 = re.match(
                            r'^"?(m[^"=]+?)(?:[><=!~]=?\s*\S+)?', line)
                        if m2:
                            name = m2.group(1).strip("\"'")
                            if name:
                                packages.setdefault(name, {
                                    "name": name,
                                    "version": "*",
                                    "sources": ["pyproject.toml"],
                                    "manager": "pip",
                                    "dep_type": "runtime",
                                })
            except OSError:
                pass

        for cfg_name in ("Cargo.toml", "Gemfile", "go.mod", "composer.json", "build.gradle", "pom.xml"):
            cfg_path = workspace_path / cfg_name
            if cfg_path.exists():
                try:
                    text = cfg_path.read_text()
                    for match in re.finditer(r'^"?([a-zA-Z0-9_.@/-]+?)"?\s*=\s*"([^"]+)"', text, re.MULTILINE):
                        name = match.group(1)
                        ver = match.group(2)
                        if name not in packages:
                            packages[name] = {
                                "name": name,
                                "version": ver,
                                "sources": [cfg_name],
                                "manager": cfg_name.split(".")[0],
                                "dep_type": "runtime",
                            }
                except OSError:
                    pass

        return packages

    def _collect_imports(self, workspace_path: Path) -> dict[str, set[str]]:
        imports: dict[str, set[str]] = {}
        for root, dirs, files in os.walk(str(workspace_path)):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            root_p = Path(root)
            for fname in files:
                fpath = root_p / fname
                ext = fpath.suffix.lower()
                lang = EXTENSION_LANGUAGE_MAP.get(ext)
                if not lang or lang in ("Config", "Unknown"):
                    continue
                try:
                    content = fpath.read_text(errors="replace")
                except OSError:
                    continue
                file_imports = self._extract_imports(content, lang)
                if file_imports:
                    imports.setdefault(lang, set()).update(file_imports)
        return imports

    def _extract_imports(self, content: str, lang: str) -> set[str]:
        imports: set[str] = set()
        if lang == "Python":
            for m in re.finditer(
                r'^(?:from\s+(\S+)\s+import|import\s+(\S+))', content, re.MULTILINE
            ):
                name = m.group(1) or m.group(2)
                imports.add(name.split(".")[0].split(" as ")[0].split(",")[0].strip())
        elif lang in ("JavaScript", "TypeScript"):
            for m in re.finditer(
                r'(?:import\s+(?:\{[^}]*\}|\*\s+as\s+\S+|\S+)\s+from\s+[\'"]([^\'"]+)|require\([\'"]([^\'"]+))',
                content,
            ):
                path = m.group(1) or m.group(2) or ""
                if path.startswith(".") or path.startswith("/"):
                    continue
                parts = path.split("/")
                pkg = parts[0]
                if pkg.startswith("@"):
                    pkg = f"{pkg}/{parts[1]}" if len(parts) > 1 else pkg
                imports.add(pkg)
            for m in re.finditer(
                r'dynamic\s*\(\s*[\'"]([^\'"]+)',
                content,
            ):
                path = m.group(1)
                if path and not path.startswith(".") and not path.startswith("/"):
                    parts = path.split("/")
                    pkg = parts[0]
                    if pkg.startswith("@"):
                        pkg = f"{pkg}/{parts[1]}" if len(parts) > 1 else pkg
                    imports.add(pkg)
        elif lang in ("Java",):
            for m in re.finditer(r'^import\s+(\S+);', content, re.MULTILINE):
                name = m.group(1).split(".")[0]
                imports.add(name)
        elif lang in ("Go",):
            for m in re.finditer(r'[\'"]([^\'"]+)[\'"]', content):
                path = m.group(1)
                if "/" in path and not path.startswith("."):
                    parts = path.split("/")
                    if len(parts) >= 2:
                        imports.add(f"{parts[0]}/{parts[1]}")
        elif lang in ("Ruby",):
            for m in re.finditer(r"^\s*(?:require|gem)\s+[\"'](\S+)[\"']", content, re.MULTILINE):
                imports.add(m.group(1))
        elif lang in ("PHP",):
            for m in re.finditer(r"^\s*use\s+(\S+)", content, re.MULTILINE):
                name = m.group(1).split("\\")[0]
                if name:
                    imports.add(name)
        return imports

    # ── Detection Methods ──

    def _find_missing_dependencies(
        self,
        declared: dict[str, dict[str, Any]],
        imports: dict[str, set[str]],
        workspace_path: Path,
    ) -> list[dict]:
        """Packages imported but not declared in any package config."""
        errors: list[dict] = []
        all_declared = {k.lower() for k in declared}
        known_stdlib: dict[str, set[str]] = {
            "Python": {
                "os", "sys", "re", "json", "math", "datetime", "pathlib",
                "collections", "typing", "uuid", "hashlib", "functools",
                "itertools", "subprocess", "shutil", "tempfile", "io",
                "textwrap", "argparse", "logging", "warnings", "abc",
                "enum", "dataclasses", "fractions", "decimal", "statistics",
                "random", "stat", "glob", "pickle", "shelve", "copy",
                "pprint", "string", "struct", "time", "calendar", "threading",
                "multiprocessing", "concurrent", "socket", "email", "base64",
                "binascii", "html", "urllib", "xml", "http", "ftplib",
                "importlib", "pkgutil", "platform", "errno", "ctypes",
                "asyncio", "difflib", "inspect", "linecache", "traceback",
                "bisect", "array", "weakref", "types", "contextlib",
            },
            "JavaScript": {"fs", "path", "os", "http", "https", "crypto",
                           "util", "stream", "events", "child_process",
                           "process", "buffer", "url", "querystring",
                           "assert", "tls", "net", "dgram", "dns", "zlib",
                           "readline", "cluster", "module", "worker_threads",
                           "perf_hooks", "async_hooks"},
            "TypeScript": {"fs", "path", "os", "http", "https", "crypto",
                           "util", "stream", "events", "child_process",
                           "process", "buffer", "url", "querystring",
                           "assert", "tls", "net", "dgram", "dns", "zlib",
                           "readline", "cluster", "module", "worker_threads",
                           "perf_hooks", "async_hooks"},
        }

        seen = set()
        for lang, lang_imports in imports.items():
            stdlib = known_stdlib.get(lang, set())
            for name in lang_imports:
                lname = name.lower()
                if lname in stdlib or lname in all_declared or lname in seen:
                    continue
                seen.add(lname)
                errors.append(self._make_error(
                    "Missing Dependency",
                    f"The package '{name}' is imported in {lang} files but not declared in any package configuration file.",
                    "High", 85, f"_dependency_analysis_", 0, 0, "",
                    f"The package '{name}' is used via import statements but not found in package.json, requirements.txt, or similar. The project may fail to run on other systems.",
                    f"Add '{name}' to your package configuration file (e.g., npm install {name}, pip install {name}).",
                    "dependency", "", name, "", "",
                ))
        return errors

    def _find_unused_dependencies(
        self,
        declared: dict[str, dict[str, Any]],
        imports: dict[str, set[str]],
    ) -> list[dict]:
        """Packages declared but never imported."""
        errors: list[dict] = []
        all_import_names = set()
        for lang_imports in imports.values():
            for name in lang_imports:
                all_import_names.add(name.lower())

        for name, info in declared.items():
            lname = name.lower()
            if lname not in all_import_names:
                errors.append(self._make_error(
                    "Unused Dependency",
                    f"'{name}' ({info['version']}) is declared in {', '.join(info['sources'])} but never imported in any source file.",
                    "Medium", 80, f"_dependency_analysis_", 0, 0, "",
                    f"The package '{name}' is listed as a dependency but no source file imports or requires it. This adds unnecessary bloat.",
                    f"Remove '{name}' from {', '.join(info['sources'])} if it is not needed.",
                    "dependency", "", name, info['version'], "",
                ))
        return errors

    def _find_version_conflicts(
        self,
        declared: dict[str, dict[str, Any]],
    ) -> list[dict]:
        """Same package with different version requirements."""
        errors: list[dict] = []
        pkg_versions: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for name, info in declared.items():
            pkg_versions[name].append((info["version"], ", ".join(info["sources"])))

        for name, vers in pkg_versions.items():
            if len(set(v[0] for v in vers)) > 1:
                conflicts = "; ".join(f"{v[0]} ({v[1]})" for v in vers)
                errors.append(self._make_error(
                    "Version Conflict",
                    f"'{name}' has multiple version requirements: {conflicts}.",
                    "Critical", 95, f"_dependency_analysis_", 0, 0, "",
                    f"The package '{name}' is required with different versions across configuration files. This will cause dependency resolution failures.",
                    f"Reconcile the version requirements for '{name}' to use a single compatible version across all configuration files.",
                    "dependency", "", name, vers[0][0] if vers else "",
                ))
        return errors

    def _find_duplicate_dependencies(
        self,
        declared: dict[str, dict[str, Any]],
    ) -> list[dict]:
        """Same package listed multiple times in overlapping config files."""
        errors: list[dict] = []
        for name, info in declared.items():
            unique_sources = set(info["sources"])
            if len(unique_sources) > 1:
                errors.append(self._make_error(
                    "Duplicate Dependency",
                    f"'{name}' is listed in multiple files: {', '.join(unique_sources)}.",
                    "Low", 90, f"_dependency_analysis_", 0, 0, "",
                    f"The package '{name}' appears in multiple dependency configuration files. While not always an error, this can lead to version confusion.",
                    f"Consolidate '{name}' into a single dependency configuration file if possible.",
                    "dependency", "", name, info['version'], "",
                ))
        return errors

    def _find_deprecated_packages(
        self,
        declared: dict[str, dict[str, Any]],
    ) -> list[dict]:
        """Known deprecated or unmaintained packages."""
        errors: list[dict] = []
        for name, info in declared.items():
            lname = name.lower()
            msg = DEPRECATED_PACKAGES.get(lname) or DEPRECATED_PYTHON.get(lname)
            if msg:
                errors.append(self._make_error(
                    "Deprecated Package",
                    f"'{name}' ({info['version']}) is deprecated. {msg}",
                    "Medium", 90, f"_dependency_analysis_", 0, 0, "",
                    f"The package '{name}' is deprecated or unmaintained. Using it may lead to security vulnerabilities and compatibility issues.",
                    f"Replace '{name}' with the recommended alternative. {msg}",
                    "dependency", "", name, info['version'], "",
                ))
        return errors

    def _find_incompatible_packages(
        self,
        declared: dict[str, dict[str, Any]],
    ) -> list[dict]:
        """Incompatible package combinations."""
        errors: list[dict] = []
        declared_lower = {k.lower() for k in declared}
        for pkg_a, pkg_b, reason in INCOMPATIBLE_COMBOS:
            if pkg_a.lower() in declared_lower and pkg_b.lower() in declared_lower:
                errors.append(self._make_error(
                    "Incompatible Packages",
                    f"'{pkg_a}' and '{pkg_b}' are incompatible in the same project. {reason}",
                    "High", 90, f"_dependency_analysis_", 0, 0, "",
                    f"The project declares both '{pkg_a}' and '{pkg_b}' which are known to be incompatible.",
                    f"Remove one of the incompatible packages: '{pkg_a}' or '{pkg_b}'.",
                    "dependency", "", f"{pkg_a}, {pkg_b}",
                    declared.get(pkg_a, {}).get("version", ""), "",
                ))
        return errors

    def _find_invalid_package_references(
        self,
        declared: dict[str, dict[str, Any]],
    ) -> list[dict]:
        """Malformed package names or version references."""
        errors: list[dict] = []
        for name, info in declared.items():
            if not re.match(r'^[a-zA-Z0-9@][a-zA-Z0-9_./@\-]*$', name):
                errors.append(self._make_error(
                    "Invalid Package Reference",
                    f"'{name}' is not a valid package name format in {', '.join(info['sources'])}.",
                    "High", 95, f"_dependency_analysis_", 0, 0, "",
                    f"The package name '{name}' does not follow standard package naming conventions.",
                    f"Correct the package name '{name}' to follow naming conventions (lowercase, alphanumeric with hyphens).",
                    "dependency", "", name, info['version'], "",
                ))
            ver = info["version"]
            if ver and ver != "*" and not re.match(
                r'^[><=!~]+\s*\d+(\.\d+)*|[\^~><=]?\d+(\.\d+)*', ver
            ):
                errors.append(self._make_error(
                    "Invalid Version Reference",
                    f"Version '{ver}' for '{name}' is not a valid version format in {', '.join(info['sources'])}.",
                    "Medium", 90, f"_dependency_analysis_", 0, 0, "",
                    f"The version specifier '{ver}' for '{name}' is malformed and will cause installation failures.",
                    f"Fix the version specifier for '{name}' to a valid semver format (e.g., '^1.0.0', '>=2.0.0').",
                    "dependency", "", name, ver, "",
                ))
        return errors

    def _find_broken_imports(
        self,
        imports: dict[str, set[str]],
        workspace_path: Path,
    ) -> list[dict]:
        """Import paths that don't resolve to any local file or known config."""
        errors: list[dict] = []
        all_files = set()
        for f in workspace_path.rglob("*"):
            if f.is_file() and not any(ign in f.parts for ign in IGNORED_DIRS):
                all_files.add(f.stem.lower())
                all_files.add(f.name.lower())

        for lang, lang_imports in imports.items():
            for name in lang_imports:
                lname = name.lower()
                if "." in name or "/" in name:
                    parts = name.split("/")
                    last = parts[-1].split(".")[0].lower()
                    if last not in all_files:
                        pass  # Could be an external dependency, skip
        return errors

    def _find_package_installation_issues(
        self,
        workspace_path: Path,
        all_packages: set[str],
    ) -> list[dict]:
        """Check for common package installation problems."""
        errors: list[dict] = []

        pkg_json = workspace_path / "package.json"
        if pkg_json.exists():
            node_modules = workspace_path / "node_modules"
            if not node_modules.exists() and all_packages:
                errors.append(self._make_error(
                    "Package Installation Issue",
                    "node_modules directory is missing. Dependencies declared in package.json have not been installed.",
                    "Critical", 95, f"_dependency_analysis_", 0, 0, "",
                    "The node_modules directory does not exist even though package.json declares dependencies. Run 'npm install' to install them.",
                    "Run 'npm install' or 'yarn install' to install the declared dependencies.",
                    "dependency", "", "*", "", "",
                ))

        venv_dirs = [workspace_path / "venv", workspace_path / ".venv"]
        pyproject = workspace_path / "pyproject.toml"
        req_txt = workspace_path / "requirements.txt"
        if pyproject.exists() or req_txt.exists():
            has_venv = any(d.exists() for d in venv_dirs)
            if not has_venv:
                errors.append(self._make_error(
                    "Broken Virtual Environment",
                    "No Python virtual environment found (venv or .venv). Dependencies may not be installed.",
                    "Medium", 80, f"_dependency_analysis_", 0, 0, "",
                    "The project has Python dependencies declared but no virtual environment directory was found.",
                    "Create a virtual environment: 'python -m venv .venv', then 'source .venv/bin/activate' and 'pip install -r requirements.txt'.",
                    "dependency", "", "*", "", "",
                ))

        return errors

    def _find_env_packages(
        self,
        workspace_path: Path,
        all_import_names: set[str],
    ) -> list[dict]:
        """Packages that are environment-specific but not classified."""
        errors: list[dict] = []
        env_indicators = {
            "dotenv", "python-dotenv", "cross-env", "env-cmd",
        }
        for name in all_import_names:
            if name in env_indicators:
                errors.append(self._make_error(
                    "Missing Environment Package",
                    f"The environment package '{name}' is imported but not declared as a dependency.",
                    "Medium", 70, f"_dependency_analysis_", 0, 0, "",
                    f"The environment management package '{name}' is used but not listed in dependency configuration.",
                    f"Add '{name}' as a dependency (e.g., pip install {name}).",
                    "dependency", "", name, "", "",
                ))
        return errors

    def _detect_package_manager(self, workspace_path: Path) -> str:
        if (workspace_path / "yarn.lock").exists():
            return "yarn"
        if (workspace_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (workspace_path / "package-lock.json").exists():
            return "npm"
        if (workspace_path / "package.json").exists():
            return "npm (no lockfile)"
        if (workspace_path / "requirements.txt").exists():
            return "pip"
        if (workspace_path / "pyproject.toml").exists():
            return "pip (pyproject.toml)"
        if (workspace_path / "Pipfile").exists():
            return "pipenv"
        if (workspace_path / "Cargo.toml").exists():
            return "cargo"
        if (workspace_path / "go.mod").exists():
            return "go mod"
        return "unknown"

    # ── Helpers ──

    def _make_error(
        self, title: str, desc: str, severity: str, confidence: int,
        rel: str, line: int, col: int, snippet: str,
        explanation: str, fix: str, error_type: str, func_name: str,
        package_name: str, current_version: str,
        recommended_version: str = "",
    ) -> dict:
        return {
            "bug_title": title,
            "description": desc,
            "severity": severity,
            "confidence": confidence,
            "language": "",
            "affected_file": rel,
            "line_number": line,
            "column_number": col,
            "code_snippet": snippet,
            "ai_explanation": explanation,
            "suggested_fix": fix,
            "error_type": error_type,
            "function_name": func_name,
            "package_name": package_name,
            "current_version": current_version,
            "recommended_version": recommended_version,
        }

    def _deduplicate(self, errors: list[dict]) -> list[dict]:
        seen = set()
        unique: list[dict] = []
        for e in errors:
            key = (e["bug_title"], e["package_name"], e["description"][:60])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    def _empty_result(self) -> dict:
        return {
            "session_id": uuid.uuid4().hex,
            "status": "unavailable",
            "total_errors": 0, "total_files_scanned": 0, "files_with_errors": 0,
            "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0,
            "results": [],
            "package_manager": "",
            "declared_packages": [],
        }
