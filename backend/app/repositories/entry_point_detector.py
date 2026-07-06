import json
import logging
import os
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult, ProjectScanner

logger = logging.getLogger(__name__)

ENTRY_POINT_RULES: list[dict] = [
    {"file": "manage.py", "framework": "Django", "project_type": "Python", "base_confidence": 98},
    {"file": "wsgi.py", "framework": "Django", "project_type": "Python", "base_confidence": 85},
    {"file": "asgi.py", "framework": "Django", "project_type": "Python", "base_confidence": 85},
    {"file": "main.py", "framework": "FastAPI", "project_type": "Python", "base_confidence": 80},
    {"file": "app.py", "framework": "Flask", "project_type": "Python", "base_confidence": 80},
    {"file": "server.py", "framework": "FastAPI", "project_type": "Python", "base_confidence": 75},
    {"file": "run.py", "framework": "Python", "project_type": "Python", "base_confidence": 70},
    {"file": "server.js", "framework": "Node.js", "project_type": "JavaScript", "base_confidence": 85},
    {"file": "app.js", "framework": "Express", "project_type": "JavaScript", "base_confidence": 80},
    {"file": "index.js", "framework": "Node.js", "project_type": "JavaScript", "base_confidence": 75},
    {"file": "main.js", "framework": "Node.js", "project_type": "JavaScript", "base_confidence": 70},
    {"file": "server.ts", "framework": "TypeScript", "project_type": "TypeScript", "base_confidence": 85},
    {"file": "index.ts", "framework": "TypeScript", "project_type": "TypeScript", "base_confidence": 75},
    {"file": "main.ts", "framework": "TypeScript", "project_type": "TypeScript", "base_confidence": 70},
    {"file": "src/main.jsx", "framework": "React", "project_type": "JavaScript", "base_confidence": 95},
    {"file": "src/main.tsx", "framework": "React", "project_type": "TypeScript", "base_confidence": 95},
    {"file": "src/index.js", "framework": "React", "project_type": "JavaScript", "base_confidence": 85},
    {"file": "src/index.tsx", "framework": "React", "project_type": "TypeScript", "base_confidence": 85},
    {"file": "Application.java", "framework": "Spring Boot", "project_type": "Java", "base_confidence": 90},
    {"file": "Main.java", "framework": "Java", "project_type": "Java", "base_confidence": 75},
    {"file": "main.go", "framework": "Go", "project_type": "Go", "base_confidence": 95},
    {"file": "main.rs", "framework": "Rust", "project_type": "Rust", "base_confidence": 95},
    {"file": "index.php", "framework": "PHP", "project_type": "PHP", "base_confidence": 90},
    {"file": "serverless.yml", "framework": "Serverless", "project_type": "JavaScript", "base_confidence": 60},
    {"file": "serverless.yaml", "framework": "Serverless", "project_type": "JavaScript", "base_confidence": 60},
    {"file": "serverless.json", "framework": "Serverless", "project_type": "JavaScript", "base_confidence": 60},
]

# Directory prefixes that indicate a file is NOT an application entry point
STATIC_PATH_PREFIXES: set[str] = {
    "static", "public", "dist", "build", "assets", "images", "img",
    "icons", "fonts", "css", "styles", "sass", "scss", "js",
    "vendor", "lib", "node_modules",
}

# Priority groups for primary entry point (lower = higher priority)
ENTRY_POINT_PRIORITY: dict[str, int] = {
    "main.py": 1, "app.py": 2, "run.py": 3, "manage.py": 1,
    "main.jsx": 1, "main.tsx": 1, "main.js": 2, "index.js": 3,
    "main.ts": 2, "index.ts": 3, "server.js": 1, "app.js": 2,
    "server.ts": 1, "main.go": 1, "main.rs": 1,
    "Application.java": 1, "Main.java": 2, "index.php": 1,
}

NEXTJS_DIRS = ["app", "pages"]


class EntryPointDetector:
    def __init__(self, workspace_path: Path | None = None, scan_result: ProjectScanResult | None = None):
        self.workspace = workspace_path.resolve() if workspace_path else Path()
        self._scan: ProjectScanResult | None = scan_result

    def scan(self, workspace_path: str | Path) -> None:
        self.workspace = Path(workspace_path).resolve()
        scanner = ProjectScanner()
        self._scan = scanner.scan(self.workspace)

    @staticmethod
    def _is_static_path(filepath: str) -> bool:
        parts = Path(filepath).parts
        return any(p in STATIC_PATH_PREFIXES for p in parts[:-1] if p != ".")

    def detect(self) -> list[dict]:
        if self._scan is None:
            scanner = ProjectScanner()
            self._scan = scanner.scan(self.workspace)

        scan = self._scan
        all_files_set = set(scan.all_files) | set(scan.root_files)
        all_basenames = {Path(f).name for f in scan.all_files}
        all_dirs_set = scan.all_dir_names | {d.lower() for d in scan.root_dirs}

        candidates: list[dict] = []
        config_hints = self._detect_config_hints(scan)

        for rule in ENTRY_POINT_RULES:
            target = rule["file"]
            target_base = Path(target).name

            matched_path = None
            if target in all_files_set:
                matched_path = target
            elif "/" not in target and target_base in all_basenames:
                for f in scan.all_files:
                    f_name = Path(f).name
                    f_parents = Path(f).parts
                    if f_name == target_base:
                        if self._is_static_path(f):
                            continue
                        matched_path = f
                        break

            if matched_path is not None:
                confidence, reason = self._compute_confidence(rule, config_hints, scan, True)
                candidates.append({
                    "entry_file": matched_path,
                    "framework": rule["framework"],
                    "project_type": rule["project_type"],
                    "confidence": confidence,
                    "reason": reason,
                })

        for ndir in NEXTJS_DIRS:
            if ndir in all_dirs_set or ndir in scan.root_dirs:
                next_entry = f"{ndir}/"
                confidence, reason = self._compute_nextjs_confidence(config_hints, ndir)
                candidates.append({
                    "entry_file": next_entry,
                    "framework": "Next.js",
                    "project_type": "TypeScript",
                    "confidence": confidence,
                    "reason": reason,
                })

        if not candidates:
            fallback = self._fallback_detection(scan, config_hints)
            if fallback:
                candidates.append(fallback)

        # Generate execution commands for each candidate
        for c in candidates:
            ep_path = c["entry_file"]
            ep_name = Path(ep_path).name
            framework = c["framework"]

            # Check package.json scripts first
            exec_cmd = None
            if scan.package_json:
                scripts = scan.package_json.get("scripts", {})
                if isinstance(scripts, dict):
                    for script_name, script_cmd in scripts.items():
                        if isinstance(script_cmd, str) and ep_name.split(".")[0] in script_cmd:
                            exec_cmd = f"{script_name}: {script_cmd}"
                            break

            # Python entry point commands
            if exec_cmd is None and ep_name.endswith(".py"):
                if framework == "Flask":
                    exec_cmd = "flask run"
                elif framework == "FastAPI":
                    app_module = ep_path.replace(".py", "").replace("/", ".")
                    exec_cmd = f"uvicorn {app_module}:app"
                elif framework == "Django":
                    exec_cmd = "python manage.py runserver"
                elif ep_name == "manage.py":
                    exec_cmd = "python manage.py runserver"
                else:
                    exec_cmd = f"python {ep_path}"

            # JS/TS entry point commands
            if exec_cmd is None and ep_name.endswith((".js", ".mjs")):
                exec_cmd = f"node {ep_path}"
            elif exec_cmd is None and ep_name.endswith((".ts",)):
                exec_cmd = f"npx ts-node {ep_path}"

            if exec_cmd:
                c["execution_command"] = exec_cmd

        # Sort by confidence, then by priority group
        def _sort_key(c: dict) -> tuple:
            ep = Path(c["entry_file"]).name
            priority = ENTRY_POINT_PRIORITY.get(ep, 99)
            return (-c["confidence"], priority)

        candidates.sort(key=_sort_key)
        return candidates

    def _detect_config_hints(self, scan: ProjectScanResult) -> dict:
        root_files = {f.lower() for f in scan.root_files}
        pkg = scan.package_json
        deps: set[str] = set()
        if pkg:
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                section_data = pkg.get(section, {})
                if isinstance(section_data, dict):
                    deps.update(section_data.keys())

        pip_deps = scan.requirements_txt_deps

        hints: dict[str, bool | str] = {
            "has_package_json": "package.json" in root_files,
            "has_requirements_txt": "requirements.txt" in root_files,
            "has_pyproject_toml": "pyproject.toml" in root_files,
            "has_dockerfile": scan.dockerfile_content is not None,
            "has_docker_compose": scan.docker_compose_content is not None,
            "has_vite_config": any(f.startswith("vite.config.") for f in root_files),
            "has_next_config": any(f.startswith("next.config.") for f in root_files),
            "has_tsconfig": "tsconfig.json" in root_files,
            "has_pom_xml": "pom.xml" in root_files,
            "has_build_gradle": "build.gradle" in root_files or "build.gradle.kts" in root_files,
            "has_cargo_toml": "cargo.toml" in root_files,
            "has_go_mod": "go.mod" in root_files,
            "has_composer_json": "composer.json" in root_files,
            "has_angular_json": "angular.json" in root_files,
            "dep_react": "react" in deps,
            "dep_next": "next" in deps,
            "dep_express": "express" in deps,
            "dep_vue": "vue" in deps,
            "dep_angular": "@angular/core" in deps,
            "dep_fastapi": "fastapi" in pip_deps or "fastapi" in (scan.pyproject_toml_content or "").lower(),
            "dep_flask": "flask" in pip_deps or "flask" in (scan.pyproject_toml_content or "").lower(),
            "dep_django": "django" in pip_deps or "django" in (scan.pyproject_toml_content or "").lower(),
            "dep_uvicorn": "uvicorn" in pip_deps,
            "dep_gunicorn": "gunicorn" in pip_deps,
        }

        if pkg:
            scripts = pkg.get("scripts", {})
            if isinstance(scripts, dict):
                hints["has_start_script"] = "start" in scripts
                hints["has_dev_script"] = "dev" in scripts
                if "start" in scripts:
                    hints["start_script"] = scripts["start"]

        return hints

    def _compute_confidence(self, rule: dict, hints: dict, scan: ProjectScanResult, file_found: bool) -> tuple[int, str]:
        base = rule["base_confidence"]
        framework = rule["framework"]
        entry_file = rule["file"]
        reasons: list[str] = []
        root_files = {f.lower() for f in scan.root_files}

        if not file_found:
            return 0, "File not found"

        fw_checks = {
            "Django": ("dep_django", ["manage.py", "wsgi.py", "asgi.py", "settings.py"]),
            "FastAPI": ("dep_fastapi", ["uvicorn"]),
            "Flask": ("dep_flask", ["gunicorn"]),
        }

        if framework in fw_checks:
            dep_key, extra_files = fw_checks[framework]
            if hints.get(dep_key):
                base += 5
                reasons.append(f"{framework} dependency detected")
            for ef in extra_files:
                if ef in root_files:
                    base += 2
                    if ef != dep_key:
                        reasons.append(f"{ef} detected")
            if hints.get("has_dockerfile"):
                base += 1
                reasons.append("Dockerfile present")

        if framework in ("React", "Next.js") and hints.get("dep_react"):
            base += 5
            if "react" not in reasons:
                reasons.append("React dependency detected")
        if framework == "Next.js" and hints.get("dep_next"):
            base += 5
            reasons.append("Next.js dependency detected")
        if framework in ("React", "Next.js", "TypeScript") and hints.get("has_tsconfig") and entry_file.endswith(("tsx", "ts")):
            base += 2
            reasons.append("TypeScript config detected")
        if framework in ("React",) and hints.get("has_vite_config"):
            base += 3
            reasons.append("Vite config detected")
        if framework == "Next.js" and hints.get("has_next_config"):
            base += 3
            reasons.append("Next.js config detected")

        if framework == "Node.js":
            if hints.get("has_package_json"):
                base += 3
                reasons.append("package.json detected")
            if hints.get("has_start_script"):
                base += 2
                reasons.append("npm start script configured")
            if hints.get("has_dockerfile"):
                base += 1

        if framework == "Express":
            if hints.get("dep_express"):
                base += 5
                reasons.append("Express dependency detected")
            if hints.get("has_package_json"):
                base += 2

        if framework == "TypeScript" and hints.get("has_tsconfig"):
            base += 5
            reasons.append("tsconfig.json detected")

        if framework in ("Spring Boot", "Java"):
            if hints.get("has_pom_xml"):
                base += 3
                reasons.append("Maven POM detected")
            if hints.get("has_build_gradle"):
                base += 3
                reasons.append("Gradle detected")

        if framework == "Go" and hints.get("has_go_mod"):
            base += 5
            reasons.append("Go module detected")
        if framework == "Rust" and hints.get("has_cargo_toml"):
            base += 5
            reasons.append("Cargo.toml detected")
        if framework == "PHP" and hints.get("has_composer_json"):
            base += 5
            reasons.append("Composer detected")

        if framework == "Python":
            if hints.get("has_requirements_txt"):
                base += 3
                reasons.append("requirements.txt detected")
            if hints.get("has_pyproject_toml"):
                base += 3
                reasons.append("pyproject.toml detected")
            if hints.get("has_dockerfile"):
                base += 1
            if not reasons:
                reasons.append("Python entry point detected")

        if not reasons:
            reasons.append(f"{framework} entry point detected")
        if hints.get("has_dockerfile") and "Dockerfile" not in str(reasons):
            base += 1

        confidence = min(base, 99)
        reason_text = " ".join(reasons) if reasons else f"Detected {entry_file} as entry point"
        return confidence, reason_text

    def _compute_nextjs_confidence(self, hints: dict, ndir: str) -> tuple[int, str]:
        base = 85
        reasons: list[str] = []

        if hints.get("dep_next"):
            base += 5
            reasons.append("Next.js dependency detected")
        if hints.get("has_next_config"):
            base += 3
            reasons.append("Next.js configuration detected")
        if hints.get("has_tsconfig"):
            base += 2
            reasons.append("TypeScript configuration detected")
        if ndir == "app":
            reasons.append("Next.js App Router detected")
        elif ndir == "pages":
            reasons.append("Next.js Pages Router detected")

        confidence = min(base, 99)
        reason_text = " ".join(reasons) if reasons else f"Next.js {ndir}/ directory detected"
        return confidence, reason_text

    def _fallback_detection(self, scan: ProjectScanResult, hints: dict) -> dict | None:
        root_files = {f.lower() for f in scan.root_files}

        for file_candidate in sorted(root_files):
            name = Path(file_candidate).name.lower()
            if name in ("main.py", "app.py", "index.js", "index.ts"):
                framework = "Unknown"
                project_type = "Unknown"
                base = 40
                reasons: list[str] = []
                exec_cmd: str | None = None

                if name.endswith(".py"):
                    framework = "Python"
                    project_type = "Python"
                elif name.endswith((".js", ".ts")):
                    framework = "Node.js"
                    project_type = "JavaScript"
                    if hints.get("has_package_json"):
                        base += 10
                        reasons.append("package.json detected")
                    if hints.get("has_tsconfig"):
                        base += 5
                        reasons.append("tsconfig.json detected")
                        project_type = "TypeScript"

                if hints.get("has_dockerfile"):
                    base += 5
                    reasons.append("Dockerfile present")

                # Look for execution command from package.json scripts
                if scan.package_json:
                    scripts = scan.package_json.get("scripts", {})
                    if isinstance(scripts, dict):
                        for script_name, script_cmd in scripts.items():
                            if isinstance(script_cmd, str) and name.split(".")[0] in script_cmd:
                                exec_cmd = f"{script_name}: {script_cmd}"
                                base += 5
                                reasons.append(f"npm script: {script_name}")
                                break

                if not reasons:
                    reasons.append(f"Fallback: {file_candidate} found")

                confidence = min(base, 65)
                result: dict = {
                    "entry_file": file_candidate,
                    "framework": framework,
                    "project_type": project_type,
                    "confidence": confidence,
                    "reason": " ".join(reasons),
                }
                if exec_cmd:
                    result["execution_command"] = exec_cmd
                return result
        return None
