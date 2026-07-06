import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult

logger = logging.getLogger(__name__)

ALL_CONFIG_FILE_DEFS: dict[str, dict] = {
    "requirements.txt": {"purpose": "Python package dependencies", "lang": "python"},
    "pyproject.toml": {"purpose": "Python project metadata & build config", "lang": "python"},
    "setup.py": {"purpose": "Python package setup script", "lang": "python"},
    "Pipfile": {"purpose": "Pipenv dependency manifest", "lang": "python"},
    "Pipfile.lock": {"purpose": "Pipenv dependency lock", "lang": "python"},
    "poetry.lock": {"purpose": "Poetry dependency lock", "lang": "python"},
    "config.py": {"purpose": "Application configuration", "lang": "python"},
    "settings.py": {"purpose": "Django/application settings", "lang": "python"},
    "alembic.ini": {"purpose": "Database migration configuration", "lang": "python"},
    "gunicorn.conf.py": {"purpose": "Gunicorn WSGI server config", "lang": "python"},
    "package.json": {"purpose": "Node.js package metadata & dependencies", "lang": "javascript"},
    "package-lock.json": {"purpose": "npm dependency lock file", "lang": "javascript"},
    "yarn.lock": {"purpose": "Yarn dependency lock file", "lang": "javascript"},
    "pnpm-lock.yaml": {"purpose": "pnpm dependency lock file", "lang": "javascript"},
    "vite.config.js": {"purpose": "Vite build configuration", "lang": "javascript"},
    "vite.config.ts": {"purpose": "Vite build configuration (TypeScript)", "lang": "javascript"},
    "webpack.config.js": {"purpose": "Webpack bundler configuration", "lang": "javascript"},
    "webpack.config.ts": {"purpose": "Webpack bundler configuration (TypeScript)", "lang": "javascript"},
    "tsconfig.json": {"purpose": "TypeScript compiler configuration", "lang": "javascript"},
    "next.config.js": {"purpose": "Next.js framework configuration", "lang": "javascript"},
    "next.config.mjs": {"purpose": "Next.js framework configuration (ESM)", "lang": "javascript"},
    "next.config.ts": {"purpose": "Next.js framework configuration (TypeScript)", "lang": "javascript"},
    "angular.json": {"purpose": "Angular workspace configuration", "lang": "javascript"},
    ".env": {"purpose": "Environment variables", "lang": "any"},
    ".env.example": {"purpose": "Environment variable template", "lang": "any"},
    ".env.local": {"purpose": "Local environment overrides", "lang": "any"},
    ".env.production": {"purpose": "Production environment variables", "lang": "any"},
    ".env.development": {"purpose": "Development environment variables", "lang": "any"},
    "Dockerfile": {"purpose": "Docker container image definition", "lang": "any"},
    "docker-compose.yml": {"purpose": "Docker Compose multi-service definition", "lang": "any"},
    "docker-compose.yaml": {"purpose": "Docker Compose multi-service definition", "lang": "any"},
    "compose.yml": {"purpose": "Docker Compose multi-service definition", "lang": "any"},
    "compose.yaml": {"purpose": "Docker Compose multi-service definition", "lang": "any"},
    ".dockerignore": {"purpose": "Docker build exclusion rules", "lang": "any"},
    ".gitignore": {"purpose": "Git exclusion rules", "lang": "any"},
    ".gitattributes": {"purpose": "Git attribute configuration", "lang": "any"},
    "Procfile": {"purpose": "Heroku process declaration", "lang": "any"},
    "Makefile": {"purpose": "Build automation", "lang": "any"},
    "nginx.conf": {"purpose": "Nginx web server configuration", "lang": "any"},
    ".github/workflows": {"purpose": "GitHub Actions CI/CD workflows", "lang": "any"},
    ".gitlab-ci.yml": {"purpose": "GitLab CI/CD pipeline", "lang": "any"},
    "azure-pipelines.yml": {"purpose": "Azure Pipelines CI/CD", "lang": "any"},
    "Jenkinsfile": {"purpose": "Jenkins CI/CD pipeline", "lang": "any"},
    ".prettierrc": {"purpose": "Prettier code formatter config", "lang": "any"},
    ".eslintrc": {"purpose": "ESLint JavaScript linter config", "lang": "javascript"},
    ".editorconfig": {"purpose": "Cross-editor coding style config", "lang": "any"},
    ".flake8": {"purpose": "Flake8 Python linter config", "lang": "python"},
    "mypy.ini": {"purpose": "MyPy static type checker config", "lang": "python"},
    "ruff.toml": {"purpose": "Ruff Python linter config", "lang": "python"},
    "pytest.ini": {"purpose": "Pytest test runner config", "lang": "python"},
    "tox.ini": {"purpose": "Tox test environment manager", "lang": "python"},
    "jest.config.js": {"purpose": "Jest JavaScript test runner config", "lang": "javascript"},
    "jest.config.ts": {"purpose": "Jest JavaScript test runner config (TypeScript)", "lang": "javascript"},
    "README.md": {"purpose": "Project documentation / README", "lang": "any"},
    "CHANGELOG.md": {"purpose": "Release changelog", "lang": "any"},
    "LICENSE": {"purpose": "Software license", "lang": "any"},
    "CONTRIBUTING.md": {"purpose": "Contribution guidelines", "lang": "any"},
}

SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)(?:password|passwd|pwd)\s*[=:]\s*['\"](?!.*(?:placeholder|your_password|changeme|example|test|123))[^'\"]{4,}['\"]"),
    re.compile(r"(?i)(?:api[_-]?key|apikey)\s*[=:]\s*['\"](?!.*(?:your_key|placeholder|example|test|123))[^'\"]{8,}['\"]"),
    re.compile(r"(?i)(?:secret|token)\s*[=:]\s*['\"](?!.*(?:your_secret|placeholder|example|test|123))[^'\"]{8,}['\"]"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(?:sk-[a-zA-Z0-9]{20,}|pk-[a-zA-Z0-9]{20,})"),
    re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----"),
]

DEPRECATED_PACKAGES: dict[str, str] = {
    "gulp": "Use webpack, esbuild, or vite instead",
    "bower": "Use npm/yarn/pnpm instead",
    "coffeescript": "Use TypeScript or ES6+ JS",
    "jade": "Renamed to pug",
    "node-sass": "Use sass (dart-sass)",
    "request": "Use node-fetch, axios, or ky",
    "moment": "Use date-fns or dayjs",
    "bluebird": "Native promises are available in Node.js 10+",
    "underscore": "Use lodash or native Array methods",
    "hogan.js": "Use mustache.js or handlebars.js",
    "python-dateutil": "Use standard datetime or pendulum",
    "pylint": "Use ruff or flake8 instead",
    "pycodestyle": "Merged into pycodestyle; use ruff or flake8",
    "nose": "Use pytest instead",
}

VERSION_SPEC_PATTERN = re.compile(r"^[\d]+(?:\.[\d]+)*(?:[.*xX])?$")
VERSION_RANGE_PATTERN = re.compile(r"^[<>=!~^]+[\d]+(?:\.[\d]+)*")


class ConfigurationIntelligenceEngine:
    def __init__(self, scan_result: ProjectScanResult):
        self.scan = scan_result
        self._detected: list[dict] = []
        self._missing: list[dict] = []
        self._dependency_issues: list[dict] = []
        self._env_issues: list[dict] = []
        self._docker_info: dict = {}
        self._cicd_info: list[dict] = []
        self._security_issues: list[dict] = []

    def analyze(self) -> dict:
        self._detect_config_files()
        self._validate_dependencies()
        self._validate_environment()
        self._validate_docker()
        self._detect_cicd()
        self._check_security()

        scores = self._compute_scores()
        recommendations = self._generate_recommendations()

        health_label = self._health_label(scores["configuration_health"])
        warnings = self._build_warnings()

        return {
            "detected_files": self._detected,
            "missing_files": self._missing,
            "dependency_validation": self._dependency_issues,
            "environment_validation": self._env_issues,
            "docker_validation": self._docker_info,
            "cicd": self._cicd_info,
            "security_checks": self._security_issues,
            "scores": scores,
            "warnings": warnings,
            "recommendations": recommendations,
            "health": {"score": scores["configuration_health"], "label": health_label},
            "readiness_score": scores["readiness"],
        }

    # ------------------------------------------------------------------
    # Config file detection
    # ------------------------------------------------------------------
    def _detect_config_files(self) -> None:
        scan = self.scan
        all_files = scan.all_files
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        root_files_lower = {f.lower() for f in scan.root_files}

        basename_map: dict[str, str] = {}
        for rel_path in all_files:
            basename_map[Path(rel_path).name.lower()] = rel_path

        has_python = scan.language_counts.get("Python", 0) > 0
        has_js = (
            scan.language_counts.get("JavaScript", 0) > 0 or
            scan.language_counts.get("TypeScript", 0) > 0
        )

        for fname, fdef in ALL_CONFIG_FILE_DEFS.items():
            flang = fdef.get("lang", "any")
            fname_lower = fname.lower()

            if flang == "python" and not has_python:
                continue
            if flang == "javascript" and not has_js:
                continue

            category = self._file_category(fname, has_python, has_js)

            if fname_lower == ".github/workflows":
                has_gh = "github" in all_dir_names or any("github" in d for d in all_dir_names)
                if has_gh:
                    self._detected.append(self._make_detected(fname, "Detected", category, "Directory", ".github/workflows"))
                else:
                    self._missing.append(self._make_missing(fname, category, fname))
                continue

            path = basename_map.get(fname_lower)

            if path:
                self._detected.append(self._make_detected(
                    fname, "Detected", category, "Directory scan", path,
                ))
            elif fname_lower in root_files_lower:
                self._detected.append(self._make_detected(
                    fname, "Detected", category, "Directory scan", fname,
                ))
            else:
                self._missing.append(self._make_missing(fname, category, fname))

    @staticmethod
    def _make_detected(fname: str, status: str, category: str, source: str, rel_path: str | None = None) -> dict:
        return {
            "file_name": fname,
            "status": status,
            "category": category,
            "purpose": ALL_CONFIG_FILE_DEFS.get(fname, {}).get("purpose", ""),
            "recommendation": None,
            "confidence": 100,
            "detection_source": source,
            "path": rel_path,
        }

    @staticmethod
    def _make_missing(fname: str, category: str, rec: str | None = None) -> dict:
        return {
            "file_name": fname,
            "status": "Missing",
            "category": category,
            "purpose": ALL_CONFIG_FILE_DEFS.get(fname, {}).get("purpose", ""),
            "recommendation": rec,
            "confidence": 0,
            "detection_source": "",
            "path": None,
        }

    def _file_category(self, fname: str, has_python: bool, has_js: bool) -> str:
        name = fname.lower()

        core_python = {"requirements.txt", "pyproject.toml", "setup.py", "config.py", "settings.py"}
        core_js = {"package.json", "tsconfig.json"}
        core_any = {"README.md", "LICENSE", ".gitignore"}
        env_vars = {".env", ".env.example", ".env.local", ".env.production", ".env.development"}
        docker = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", ".dockerignore"}
        git = {".gitignore", ".gitattributes"}
        ci_cd = {".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile"}
        fmt = {".prettierrc", ".eslintrc", ".editorconfig", ".flake8", "mypy.ini", "ruff.toml"}
        testing = {"pytest.ini", "tox.ini", "jest.config.js", "jest.config.ts"}
        docs = {"README.md", "CHANGELOG.md", "LICENSE", "CONTRIBUTING.md"}

        if name in core_python and has_python:
            return "Required"
        if name in core_js and has_js:
            return "Required"
        if name in docs:
            return "Recommended"
        if name in env_vars:
            return "Recommended"
        if name in docker:
            return "Recommended"
        if name in ci_cd:
            return "Recommended"
        if name in fmt:
            return "Optional"
        if name in testing:
            return "Optional"
        if name in {"alembic.ini", "gunicorn.conf.py", "Procfile", "Makefile", "nginx.conf", "Pipfile", "Pipfile.lock", "poetry.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "CHANGELOG.md", "CONTRIBUTING.md", ".gitattributes", ".dockerignore", "black"}:
            return "Optional"
        return "Optional"

    # ------------------------------------------------------------------
    # Dependency validation
    # ------------------------------------------------------------------
    def _validate_dependencies(self) -> None:
        scan = self.scan
        issues: list[dict] = []

        if scan.requirements_txt_deps:
            issues.extend(self._check_pip_deps(scan.requirements_txt_deps))

        if scan.pyproject_toml_content:
            issues.extend(self._check_pyproject_deps(scan.pyproject_toml_content))

        pkg_json = scan.package_json
        if pkg_json:
            issues.extend(self._check_npm_deps(pkg_json))

        self._dependency_issues = issues

    def _check_pip_deps(self, deps: list[str]) -> list[dict]:
        issues: list[dict] = []
        seen: set[str] = set()
        for dep in deps:
            dep_lower = dep.lower()
            parts = re.split(r"[=<>~!@#;]", dep, maxsplit=1)
            pkg_name = parts[0].strip().lower()
            if not pkg_name:
                continue

            if pkg_name in seen:
                issues.append({
                    "type": "Duplicate dependency",
                    "package": pkg_name,
                    "severity": "warning",
                    "detail": f"Package '{pkg_name}' is listed multiple times.",
                })
            seen.add(pkg_name)

            version_part = parts[1].strip() if len(parts) > 1 else ""
            if version_part and not VERSION_SPEC_PATTERN.match(version_part) and not VERSION_RANGE_PATTERN.match(version_part):
                if version_part not in ("", "*", "latest"):
                    issues.append({
                        "type": "Invalid version syntax",
                        "package": pkg_name,
                        "severity": "warning",
                        "detail": f"Version spec '{version_part}' has unusual syntax.",
                    })

            if pkg_name in DEPRECATED_PACKAGES:
                issues.append({
                    "type": "Deprecated package",
                    "package": pkg_name,
                    "severity": "info",
                    "detail": DEPRECATED_PACKAGES[pkg_name],
                })

        return issues

    def _check_pyproject_deps(self, content: str) -> list[dict]:
        issues: list[dict] = []
        try:
            import tomllib
            data = tomllib.loads(content)
        except Exception:
            try:
                import toml
                data = toml.loads(content)
            except Exception:
                return []
        deps_list: list[str] = []

        proj = data.get("project", {})
        deps_list.extend(proj.get("dependencies", []) or [])

        poetry = data.get("tool", {}).get("poetry", {})
        for section in ("dependencies", "dev-dependencies"):
            deps_list.extend(list(poetry.get(section, {}).keys()))

        seen: set[str] = set()
        for dep in deps_list:
            pkg_name = re.split(r"[=<>~!@#;^]", dep.strip(), maxsplit=1)[0].strip().lower()
            if not pkg_name:
                continue
            if pkg_name in seen:
                issues.append({
                    "type": "Duplicate dependency",
                    "package": pkg_name,
                    "severity": "warning",
                    "detail": f"Package '{pkg_name}' is listed multiple times.",
                })
            seen.add(pkg_name)
            if pkg_name in DEPRECATED_PACKAGES:
                issues.append({
                    "type": "Deprecated package",
                    "package": pkg_name,
                    "severity": "info",
                    "detail": DEPRECATED_PACKAGES[pkg_name],
                })
        return issues

    def _check_npm_deps(self, pkg: dict) -> list[dict]:
        issues: list[dict] = []
        seen: dict[str, list[str]] = {}
        sections = [
            ("dependencies", "dependency"),
            ("devDependencies", "devDependency"),
            ("peerDependencies", "peerDependency"),
        ]
        for section, dep_type in sections:
            deps = pkg.get(section, {})
            if not isinstance(deps, dict):
                continue
            for name, version in deps.items():
                name_lower = name.lower()
                if not isinstance(version, str):
                    version = str(version)
                if name_lower in seen:
                    issues.append({
                        "type": "Duplicate dependency",
                        "package": name,
                        "severity": "warning",
                        "detail": f"Package '{name}' is declared in multiple sections.",
                    })
                seen.setdefault(name_lower, []).append(section)

                if version and not VERSION_SPEC_PATTERN.match(version) and not VERSION_RANGE_PATTERN.match(version):
                    if version not in ("*", "latest", ""):
                        issues.append({
                            "type": "Invalid version syntax",
                            "package": name,
                            "severity": "warning",
                            "detail": f"Version '{version}' for '{name}' has unusual syntax.",
                        })

                if name_lower in DEPRECATED_PACKAGES:
                    issues.append({
                        "type": "Deprecated package",
                        "package": name,
                        "severity": "info",
                        "detail": DEPRECATED_PACKAGES[name_lower],
                    })

        return issues

    # ------------------------------------------------------------------
    # Environment validation
    # ------------------------------------------------------------------
    def _validate_environment(self) -> None:
        scan = self.scan
        issues: list[dict] = []

        has_example = scan.env_example_content is not None
        has_env = scan.env_content is not None

        if not has_example:
            issues.append({
                "type": "Missing .env.example",
                "file": None,
                "severity": "warning",
                "detail": "No .env.example file found. Add one as a template for required environment variables.",
            })

        if has_env:
            env_content = scan.env_content or ""
            secret_matches = self._find_secrets_in_text(env_content, ".env")
            issues.extend(secret_matches)

        config_texts = [
            (scan.config_py_content, "config.py"),
            (scan.settings_py_content, "settings.py"),
            (scan.database_py_content, "database.py"),
        ]
        for text, fname in config_texts:
            if not text:
                continue
            secret_matches = self._find_secrets_in_text(text, fname)
            issues.extend(secret_matches)

        for uri in scan.db_uris:
            if "://" in uri and "@" in uri:
                issues.append({
                    "type": "Hardcoded database credential",
                    "file": None,
                    "severity": "error",
                    "detail": f"Database URI contains inline credentials: {self._mask_uri(uri)}",
                })

        self._env_issues = issues

    @staticmethod
    def _mask_uri(uri: str) -> str:
        masked = re.sub(r"(://)([^:]+):([^@]+)@", r"\1***:***@", uri)
        masked = re.sub(r"(password=)[^&\s]+", r"\1***", masked)
        return masked

    @staticmethod
    def _find_secrets_in_text(text: str, source: str) -> list[dict]:
        issues: list[dict] = []
        for line_num, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(stripped):
                    issues.append({
                        "type": "Hardcoded secret",
                        "file": source,
                        "severity": "error",
                        "detail": f"Potential hardcoded secret in {source}:{line_num}",
                    })
                    break
        return issues

    # ------------------------------------------------------------------
    # Docker validation
    # ------------------------------------------------------------------
    def _validate_docker(self) -> None:
        scan = self.scan
        info: dict = {
            "has_dockerfile": False,
            "has_docker_compose": False,
            "multi_stage_build": False,
            "production_ready": False,
            "detail": "",
        }
        has_df = scan.dockerfile_content is not None
        has_dc = scan.docker_compose_content is not None

        info["has_dockerfile"] = has_df
        info["has_docker_compose"] = has_dc

        if has_df:
            content = scan.dockerfile_content or ""
            info["multi_stage_build"] = "as " in content.lower()
            has_prod_cmd = bool(re.search(
                r"(?i)(CMD\s+\[?(?:gunicorn|uvicorn|waitress|\\./start|\\./entrypoint)",
                content,
            ))
            has_expose = bool(re.search(r"(?i)EXPOSE\s+\d+", content))
            has_healthcheck = bool(re.search(r"(?i)HEALTHCHECK", content))
            info["production_ready"] = has_prod_cmd or has_expose

            features = []
            if info["multi_stage_build"]:
                features.append("multi-stage build")
            if has_prod_cmd:
                features.append("production server command")
            if has_expose:
                features.append("port exposure")
            if has_healthcheck:
                features.append("healthcheck")

            info["detail"] = (
                f"Dockerfile detected with {', '.join(features) if features else 'basic configuration'}."
                if has_df else ""
            )
        else:
            info["detail"] = "No Dockerfile found."

        self._docker_info = info

    # ------------------------------------------------------------------
    # CI/CD detection
    # ------------------------------------------------------------------
    def _detect_cicd(self) -> None:
        scan = self.scan
        results: list[dict] = []

        gh_workflows = any(
            "github" in d.lower() and "workflows" in str(scan.all_dirs)
            for d in scan.all_dir_names
        ) or any(
            f.endswith(".yml") and "workflows" in f
            for f in scan.all_files
        )
        results.append({
            "platform": "GitHub Actions",
            "configured": gh_workflows,
            "file": ".github/workflows" if gh_workflows else None,
        })

        has_gitlab = any(f.lower() == ".gitlab-ci.yml" for f in scan.root_files)
        results.append({
            "platform": "GitLab CI",
            "configured": has_gitlab,
            "file": ".gitlab-ci.yml" if has_gitlab else None,
        })

        has_azure = any(f.lower() == "azure-pipelines.yml" for f in scan.root_files)
        results.append({
            "platform": "Azure Pipelines",
            "configured": has_azure,
            "file": "azure-pipelines.yml" if has_azure else None,
        })

        has_jenkins = any(f.lower() == "jenkinsfile" for f in scan.root_files)
        results.append({
            "platform": "Jenkins",
            "configured": has_jenkins,
            "file": "Jenkinsfile" if has_jenkins else None,
        })

        has_circle = any(d.lower() == ".circleci" for d in scan.all_dir_names) or \
                     any("circle" in d.lower() for d in scan.all_dir_names)
        results.append({
            "platform": "CircleCI",
            "configured": has_circle,
            "file": ".circleci" if has_circle else None,
        })

        self._cicd_info = results

    # ------------------------------------------------------------------
    # Security checks
    # ------------------------------------------------------------------
    def _check_security(self) -> None:
        issues: list[dict] = []

        if not self.scan.env_example_content and self.scan.env_content:
            issues.append({
                "type": "Missing .env.example",
                "severity": "warning",
                "detail": ".env exists but no .env.example template is provided.",
            })

        if self._docker_info.get("has_dockerfile") and not self.scan.dockerignore_content:
            issues.append({
                "type": "Missing .dockerignore",
                "severity": "warning",
                "detail": "Dockerfile exists but no .dockerignore to reduce image size and avoid leaking secrets.",
            })

        has_cicd = any(c.get("configured") for c in self._cicd_info)
        if not has_cicd:
            issues.append({
                "type": "No CI/CD pipeline",
                "severity": "info",
                "detail": "No CI/CD configuration detected.",
            })

        if not self.scan.gitignore_content:
            issues.append({
                "type": "Missing .gitignore",
                "severity": "warning",
                "detail": "No .gitignore file to prevent committing sensitive files.",
            })

        if not self.scan.config_flags.get("license"):
            has_license = any(
                f.lower().startswith("license") for f in self.scan.root_files
            )
            if not has_license:
                issues.append({
                    "type": "Missing LICENSE",
                    "severity": "info",
                    "detail": "No LICENSE file detected. Consider adding an open-source license.",
                })

        self._security_issues = issues

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def _compute_scores(self) -> dict:
        config_health = self._compute_config_health()
        readiness = self._compute_readiness()
        security = self._compute_security_score()
        maintainability = self._compute_maintainability()

        return {
            "configuration_health": config_health,
            "readiness": readiness,
            "security": security,
            "maintainability": maintainability,
        }

    def _compute_config_health(self) -> int:
        detected_count = len(self._detected)
        total = detected_count + len(self._missing)
        if total == 0:
            return 0
        required_found = sum(1 for d in self._detected if d["category"] == "Required")
        required_total = required_found + sum(1 for m in self._missing if m["category"] == "Required")
        recommended_found = sum(1 for d in self._detected if d["category"] == "Recommended")
        recommended_total = recommended_found + sum(1 for m in self._missing if m["category"] == "Recommended")
        optional_found = sum(1 for d in self._detected if d["category"] == "Optional")
        optional_total = optional_found + sum(1 for m in self._missing if m["category"] == "Optional")

        req_score = (required_found / max(required_total, 1)) * 60
        rec_score = (recommended_found / max(recommended_total, 1)) * 25
        opt_score = (optional_found / max(optional_total, 1)) * 15

        return min(int(req_score + rec_score + opt_score), 100)

    def _compute_readiness(self) -> int:
        required_found = sum(1 for d in self._detected if d["category"] == "Required")
        required_total = required_found + sum(1 for m in self._missing if m["category"] == "Required")
        if required_total == 0:
            return 100
        return int((required_found / required_total) * 100)

    def _compute_security_score(self) -> int:
        score = 80
        if not self.scan.env_example_content:
            score -= 15
        if self._env_issues:
            hardcoded_count = sum(1 for e in self._env_issues if e.get("severity") == "error")
            score -= min(hardcoded_count * 10, 30)
        if not self.scan.gitignore_content:
            score -= 10
        if not self.scan.dockerignore_content and self._docker_info.get("has_dockerfile"):
            score -= 5
        has_cicd = any(c.get("configured") for c in self._cicd_info)
        if not has_cicd:
            score -= 10
        return max(0, min(100, score))

    def _compute_maintainability(self) -> int:
        score = 50
        if self.scan.gitignore_content:
            score += 10
        if self.scan.config_flags.get("readme"):
            score += 10
        if any(f.lower().startswith("license") for f in self.scan.root_files):
            score += 10
        fmt_files = {".prettierrc", ".eslintrc", ".editorconfig", ".flake8", "mypy.ini", "ruff.toml", "black"}
        found_fmt = sum(1 for d in self._detected if d["file_name"].lower() in fmt_files)
        score += min(found_fmt * 5, 15)
        test_files = {"pytest.ini", "tox.ini", "jest.config.js", "jest.config.ts"}
        found_test = sum(1 for d in self._detected if d["file_name"].lower() in test_files)
        score += min(found_test * 5, 10)
        has_tests_dir = self.scan.has_tests
        if has_tests_dir:
            score += 5
        return max(0, min(100, score))

    @staticmethod
    def _health_label(score: int) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 70:
            return "Good"
        if score >= 40:
            return "Average"
        return "Poor"

    # ------------------------------------------------------------------
    # Warnings & recommendations
    # ------------------------------------------------------------------
    def _build_warnings(self) -> list[dict]:
        warnings: list[dict] = []
        for m in self._missing:
            if m["category"] in ("Required", "Recommended"):
                warnings.append({
                    "message": f"Missing {m['category'].lower()} file: {m['file_name']}.",
                    "severity": "warning" if m["category"] == "Required" else "info",
                    "file_name": m["file_name"],
                })
        for issue in self._dependency_issues:
            if issue["severity"] == "error":
                warnings.append({
                    "message": issue["detail"],
                    "severity": "warning",
                    "file_name": issue["package"],
                })
        for issue in self._env_issues:
            if issue["severity"] == "error":
                warnings.append({
                    "message": issue["detail"],
                    "severity": "warning",
                    "file_name": issue.get("file"),
                })
        return warnings

    def _generate_recommendations(self) -> list[str]:
        recs: list[str] = []

        for m in self._missing:
            if m["category"] == "Required":
                recs.append(f"Add missing required file: {m['file_name']}.")
            elif m["category"] == "Recommended":
                recs.append(f"Consider adding: {m['file_name']} ({m['purpose']}).")

        if self._docker_info.get("has_dockerfile") and not self._docker_info.get("multi_stage_build"):
            recs.append("Use multi-stage builds in Dockerfile to reduce image size.")

        if self._docker_info.get("has_dockerfile") and not self._docker_info.get("production_ready"):
            recs.append("Add production server configuration (gunicorn/uvicorn) to Dockerfile.")

        has_cicd = any(c.get("configured") for c in self._cicd_info)
        if not has_cicd:
            recs.append("Set up a CI/CD pipeline (GitHub Actions, GitLab CI, etc.).")

        dep_errors = [d for d in self._dependency_issues if d["severity"] in ("error", "warning")]
        for dep in dep_errors[:3]:
            recs.append(f"Fix dependency issue: {dep['detail']}")

        if self._env_issues:
            env_errors = [e for e in self._env_issues if e.get("severity") in ("error", "warning")]
            for env in env_errors[:3]:
                recs.append(f"Environment: {env['detail']}")

        formatted_recs: list[str] = []
        seen: set[str] = set()
        for r in recs:
            r_stripped = r.rstrip(".")
            if r_stripped not in seen:
                seen.add(r_stripped)
                formatted_recs.append(r)

        return formatted_recs[:12]
