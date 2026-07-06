import os
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult, ProjectScanner

ARCHITECTURE_DEFS: list[dict] = [
    {
        "name": "Layered Architecture",
        "required": ["controllers", "services", "repositories", "models"],
        "supporting": ["routes", "handlers", "middleware", "validators", "serializers",
                       "helpers", "utils", "config", "dto", "daos"],
        "conflicts": [],
        "weight": 1.0,
    },
    {
        "name": "MVC",
        "required": ["controllers", "models", "views"],
        "supporting": ["routes", "helpers", "middleware", "templates", "public",
                       "components", "layouts"],
        "conflicts": ["repositories", "services", "domain", "application"],
        "weight": 1.0,
    },
    {
        "name": "MVVM",
        "required": ["models", "views", "viewmodels"],
        "supporting": ["viewmodels", "view-models", "view_models", "bindings",
                       "components", "pages"],
        "conflicts": ["controllers", "services", "repositories"],
        "weight": 1.0,
    },
    {
        "name": "Clean Architecture",
        "required": ["domain", "application", "infrastructure", "adapters"],
        "supporting": ["entities", "usecases", "use-cases", "use_cases",
                       "interfaces", "ports", "drivers", "gateways",
                       "presenters", "controllers", "repository"],
        "conflicts": ["views", "templates"],
        "weight": 1.0,
    },
    {
        "name": "Hexagonal Architecture",
        "required": ["adapters", "ports", "domain", "application", "infrastructure"],
        "supporting": ["inbound", "outbound", "drivers", "driven",
                       "interfaces", "core", "spi", "api"],
        "conflicts": ["views", "templates", "controllers", "models"],
        "weight": 1.0,
    },
    {
        "name": "Onion Architecture",
        "required": ["domain", "application", "infrastructure", "presentation"],
        "supporting": ["core", "services", "interfaces", "repository",
                       "persistence", "external"],
        "conflicts": ["views", "templates", "controllers"],
        "weight": 1.0,
    },
    {
        "name": "Feature-Based Architecture",
        "required": ["features", "modules"],
        "supporting": ["components", "pages", "screens", "blocks",
                       "widgets", "sections"],
        "conflicts": ["controllers", "services", "repositories"],
        "weight": 1.0,
    },
    {
        "name": "Microservices",
        "required": [],
        "supporting": [],
        "conflicts": [],
        "weight": 1.0,
    },
    {
        "name": "API-Only",
        "required": ["api", "routes", "endpoints"],
        "supporting": ["openapi", "swagger", "schemas", "validators",
                       "middleware", "handlers"],
        "conflicts": ["views", "templates", "components", "pages"],
        "weight": 1.0,
    },
    {
        "name": "Serverless",
        "required": ["functions", "lambda"],
        "supporting": ["triggers", "handlers", "events", "steps",
                       "serverless", "workflows"],
        "conflicts": ["controllers", "services", "repositories"],
        "weight": 1.0,
    },
]

LAYER_ORDER: list[str] = [
    "Presentation",
    "Application",
    "Business Logic",
    "Service Layer",
    "Repository Layer",
    "Data Access",
    "Infrastructure",
    "Domain",
    "Configuration",
    "Utilities",
    "Testing",
]

LAYER_DEFINITIONS: list[dict] = [
    {"name": "Presentation", "directories": ["views", "templates", "components", "pages",
                                               "public", "ui", "screens", "layouts",
                                               "widgets", "presentation"]},
    {"name": "Application", "directories": ["services", "usecases", "use-cases", "use_cases",
                                             "controllers", "api", "routes", "endpoints",
                                             "handlers", "application"]},
    {"name": "Business Logic", "directories": ["domain", "entities", "models", "business",
                                                 "logic", "core", "engine"]},
    {"name": "Service Layer", "directories": ["services", "service", "servicelayer",
                                                "service-layer"]},
    {"name": "Repository Layer", "directories": ["repositories", "repository", "repo",
                                                   "daos", "dao"]},
    {"name": "Data Access", "directories": ["data", "dal", "dao", "persistence",
                                              "datastore", "queries"]},
    {"name": "Infrastructure", "directories": ["infrastructure", "config", "configuration",
                                                 "database", "db", "cache", "queue",
                                                 "logging", "monitoring", "metrics"]},
    {"name": "Domain", "directories": ["domain", "entities", "aggregates", "value-objects",
                                         "value_objects", "domain-events", "domain_events"]},
    {"name": "Configuration", "directories": ["config", "configuration", "settings",
                                                "env", "environments"]},
    {"name": "Utilities", "directories": ["utils", "util", "helpers", "helper",
                                            "common", "shared", "lib", "support"]},
    {"name": "Testing", "directories": ["tests", "test", "__tests__", "spec", "specs",
                                          "e2e", "integration"]},
]


class ArchitectureDetectorRepository:
    def __init__(self, scan_result: ProjectScanResult | None = None) -> None:
        self._scan: ProjectScanResult | None = scan_result

    def scan(self, workspace_path: str) -> None:
        scanner = ProjectScanner()
        self._scan = scanner.scan(Path(workspace_path))

    def _ensure_scan(self) -> ProjectScanResult:
        assert self._scan is not None, "call scan() first"
        return self._scan

    def detect_architectures(self) -> list[dict]:
        scan = self._ensure_scan()
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        root_files_lower = {f.lower() for f in scan.root_files}
        known_dirs = all_dir_names | root_dirs_lower

        raw_scores: list[dict] = []
        for arch in ARCHITECTURE_DEFS:
            required = arch["required"]
            supporting = arch["supporting"]
            conflicts = arch["conflicts"]

            matched_required = [d for d in required if d in known_dirs]
            matched_supporting = [d for d in supporting if d in known_dirs]
            matched_conflicts = [d for d in conflicts if d in known_dirs]

            req_count = len(required)
            sup_count = len(supporting)
            req_matched = len(matched_required)
            sup_matched = len(matched_supporting)
            conflict_matched = len(matched_conflicts)

            if req_count == 0 and sup_count == 0:
                continue

            evidence_raw: list[str] = []
            for d in matched_required:
                evidence_raw.append(f"Required directory: {d}")
            for d in matched_supporting:
                evidence_raw.append(f"Supporting directory: {d}")

            req_score = (req_matched / max(req_count, 1)) * 100 if req_count > 0 else 60
            sup_score = (sup_matched / max(sup_count, 1)) * 40 if sup_count > 0 else 0
            conflict_penalty = conflict_matched * 15

            confidence = int((req_score + sup_score) * arch["weight"] - conflict_penalty)
            confidence = max(0, min(confidence, 99))

            if confidence <= 0:
                continue

            reason = self._build_arch_reason(arch["name"], matched_required,
                                              matched_supporting, confidence)

            raw_scores.append({
                "architecture": arch["name"],
                "confidence": confidence,
                "reason": reason,
                "evidence": evidence_raw,
            })

        micro_result = self._detect_microservices(scan)
        if micro_result and micro_result["confidence"] > 0:
            raw_scores.append(micro_result)

        monolith_result = self._detect_monolith(scan)
        if monolith_result:
            raw_scores.append(monolith_result)

        frontend_only = self._detect_frontend_only(scan)
        if frontend_only:
            raw_scores.append(frontend_only)

        backend_only = self._detect_backend_only(scan)
        if backend_only:
            raw_scores.append(backend_only)

        cli_result = self._detect_cli_app(scan)
        if cli_result:
            raw_scores.append(cli_result)

        library_result = self._detect_library(scan)
        if library_result:
            raw_scores.append(library_result)

        if not raw_scores:
            raw_scores.append({
                "architecture": "Unknown",
                "confidence": 0,
                "reason": "No recognizable architectural pattern detected",
                "evidence": [],
            })

        raw_scores.sort(key=lambda r: r["confidence"], reverse=True)
        return raw_scores

    def detect_layers(self) -> list[dict]:
        scan = self._ensure_scan()
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        known_dirs = all_dir_names | root_dirs_lower

        layer_set: dict[str, list[str]] = {}
        for layer in LAYER_DEFINITIONS:
            matching = [d for d in layer["directories"] if d in known_dirs]
            if matching:
                layer_set[layer["name"]] = list(set(matching))

        ordered: list[dict] = []
        added = set()
        for ln in LAYER_ORDER:
            if ln in layer_set and ln not in added:
                ordered.append({"name": ln, "directories": layer_set[ln]})
                added.add(ln)
        for ln in sorted(layer_set.keys()):
            if ln not in added:
                ordered.append({"name": ln, "directories": layer_set[ln]})

        return ordered

    def detect_microservices(self) -> dict | None:
        scan = self._ensure_scan()
        return self._detect_microservices(scan)

    def _detect_microservices(self, scan: ProjectScanResult) -> dict | None:
        root_dirs = {d.lower() for d in scan.root_dirs}
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        root_files_lower = {f.lower() for f in scan.root_files}

        service_dirs = [
            d for d in root_dirs
            if d.startswith("service-") or d.startswith("svc-")
            or d.endswith("-service") or d.endswith("-api")
            or d in {"backend", "frontend", "auth", "gateway", "api-gateway",
                     "services", "microservices", "svc"}
        ]

        has_docker_compose = (scan.docker_compose_content is not None
                              or "docker-compose.yml" in root_files_lower
                              or "docker-compose.yaml" in root_files_lower)
        has_k8s = "k8s" in all_dir_names or "kubernetes" in all_dir_names
        has_helm = "helm" in all_dir_names or "charts" in all_dir_names
        has_deploy = "deploy" in all_dir_names or "deployment" in all_dir_names
        has_proto = any(f.endswith(".proto") for f in scan.root_files)
        has_api_gateway = ("gateway" in root_dirs or "api-gateway" in root_dirs
                           or "apigateway" in root_dirs)
        has_messaging = any(d in all_dir_names for d in ["queue", "rabbitmq", "kafka",
                                                          "nats", "pubsub", "events"])
        has_service_dirs = len(service_dirs) > 1

        score = 0
        evidence: list[str] = []

        if has_service_dirs:
            score += min(len(service_dirs) * 12, 40)
            evidence.append(f"Service directories: {', '.join(service_dirs[:5])}")
        if has_docker_compose:
            score += 15
            evidence.append("Docker Compose found")
        if has_k8s:
            score += 10
            evidence.append("Kubernetes configs found")
        if has_helm:
            score += 5
            evidence.append("Helm charts found")
        if has_deploy:
            score += 5
            evidence.append("Deployment directory found")
        if has_proto:
            score += 8
            evidence.append("Protobuf definitions found")
        if has_api_gateway:
            score += 10
            evidence.append("API gateway directory found")
        if has_messaging:
            score += 8
            evidence.append("Messaging/queue infrastructure found")
        if has_service_dirs and has_docker_compose:
            score += 10

        if score < 15:
            return {"architecture": "Microservices", "confidence": 0,
                    "reason": "Insufficient evidence", "evidence": []}

        confidence = min(score, 99)
        reasons_parts: list[str] = []
        if has_service_dirs:
            reasons_parts.append(f"{len(service_dirs)} service directories")
        if has_docker_compose:
            reasons_parts.append("Docker Compose")
        if has_k8s:
            reasons_parts.append("Kubernetes")
        reason = "Detected microservices pattern: " + "; ".join(reasons_parts)

        return {
            "architecture": "Microservices",
            "confidence": confidence,
            "reason": reason,
            "evidence": evidence,
        }

    def _detect_monolith(self, scan: ProjectScanResult) -> dict | None:
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        known_dirs = all_dir_names | root_dirs_lower

        has_src = "src" in known_dirs or "app" in known_dirs
        has_lib = "lib" in known_dirs
        has_single_entry = any(
            f.lower() in {f.lower() for f in scan.root_files}
            for f in ["main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs"]
        )

        layered_dirs = len([d for d in known_dirs if d in {
            "controllers", "services", "models", "routes", "api", "middleware"
        }])
        no_service_separation = layered_dirs >= 2

        monorepo_dirs = len([d for d in root_dirs_lower if d in {
            "packages", "apps", "modules"
        }])

        score = 0
        evidence: list[str] = []

        if has_src or has_lib:
            score += 25
            evidence.append("Single source root directory")
        if has_single_entry:
            score += 15
            evidence.append("Single entry point file at root")
        if no_service_separation:
            score += 15
            evidence.append("Layered directories within same project")
        if monorepo_dirs == 0:
            score += 10
            evidence.append("Monorepo pattern not detected")
        if scan.total_files < 200:
            score += 10

        if score < 20:
            return None

        confidence = min(score, 75)
        return {
            "architecture": "Monolith",
            "confidence": confidence,
            "reason": f"Single deployment unit with {layered_dirs} layered directories",
            "evidence": evidence,
        }

    def _detect_frontend_only(self, scan: ProjectScanResult) -> dict | None:
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        known_dirs = all_dir_names | root_dirs_lower

        frontend_dirs = [d for d in known_dirs if d in {
            "components", "pages", "views", "templates", "styles", "assets",
            "public", "frontend", "app", "src", "ui",
        }]
        backend_dirs = [d for d in known_dirs if d in {
            "api", "routes", "controllers", "services", "repositories",
            "database", "db", "backend", "server",
        }]

        is_frontend_framework = any(
            imp in scan.python_imports or imp in scan.js_imports
            for imp in ["react", "vue", "angular", "svelte"]
        )
        has_frontend_config = any(
            f.lower() in {f.lower() for f in scan.root_files}
            for f in ["package.json", "vite.config.ts", "vite.config.js",
                       "next.config.js", "angular.json", "svelte.config.js"]
        )

        score = 0
        evidence = []
        if len(frontend_dirs) >= 3:
            score += 35
            evidence.append(f"{len(frontend_dirs)} frontend directories found")
        if is_frontend_framework:
            score += 25
            evidence.append("Frontend framework detected")
        if has_frontend_config:
            score += 15
            evidence.append("Frontend config files found")
        if len(backend_dirs) <= 1:
            score += 15
            evidence.append("No significant backend directories")
        if not any(f.lower().endswith((".py", ".go", ".rs", ".java", ".cs", ".php"))
                   for f in scan.root_files):
            score += 10

        if score < 30 or len(backend_dirs) > len(frontend_dirs):
            return None

        confidence = min(score, 95)
        return {
            "architecture": "Frontend-Only",
            "confidence": confidence,
            "reason": f"{len(frontend_dirs)} frontend directories with frontend framework",
            "evidence": evidence,
        }

    def _detect_backend_only(self, scan: ProjectScanResult) -> dict | None:
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        known_dirs = all_dir_names | root_dirs_lower

        backend_dirs = [d for d in known_dirs if d in {
            "api", "routes", "controllers", "services", "repositories",
            "database", "db", "backend", "server", "middleware", "models",
            "config", "migrations",
        }]
        frontend_dirs = [d for d in known_dirs if d in {
            "components", "pages", "views", "templates", "styles",
            "assets", "public", "frontend", "ui",
        }]

        has_backend_lang = any(
            f.lower().endswith((".py", ".go", ".rs", ".java", ".kt", ".cs"))
            for f in scan.all_files
        )
        has_backend_config = any(
            f.lower() in {f.lower() for f in scan.root_files}
            for f in ["requirements.txt", "pyproject.toml", "go.mod",
                       "pom.xml", "build.gradle", "cargo.toml"]
        )

        score = 0
        evidence = []
        if len(backend_dirs) >= 3:
            score += 35
            evidence.append(f"{len(backend_dirs)} backend directories found")
        if has_backend_lang:
            score += 25
            evidence.append("Backend programming language detected")
        if has_backend_config:
            score += 15
            evidence.append("Backend config files found")
        if len(frontend_dirs) <= 1:
            score += 15
            evidence.append("No significant frontend directories")

        if score < 30 or len(frontend_dirs) > len(backend_dirs):
            return None

        confidence = min(score, 95)
        return {
            "architecture": "Backend-Only",
            "confidence": confidence,
            "reason": f"{len(backend_dirs)} backend directories with backend configuration",
            "evidence": evidence,
        }

    def _detect_cli_app(self, scan: ProjectScanResult) -> dict | None:
        root_files_lower = {f.lower() for f in scan.root_files}
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        known_dirs = all_dir_names | root_dirs_lower

        has_cli_entry = any(
            f in root_files_lower
            for f in ["cli.py", "main.py", "cmd", "cli", "console"]
        )
        has_cli_dir = "cli" in known_dirs or "cmd" in known_dirs or "console" in known_dirs
        has_cli_framework = any(
            imp in scan.python_imports
            for imp in ["click", "typer", "argparse", "prompt_toolkit", "rich"]
        ) or any(
            f.lower() in root_files_lower
            for f in ["setup.py", "setup.cfg", "pyproject.toml"]
            if scan.pyproject_toml_content and "console_scripts" in scan.pyproject_toml_content
        )

        is_simple_and_flat = (
            len(known_dirs) <= 3
            and len(scan.root_files) <= 10
            and scan.total_files <= 30
            and has_cli_entry
        )

        score = 0
        evidence = []
        if has_cli_entry:
            score += 30
            evidence.append("CLI entry point found")
        if has_cli_dir:
            score += 25
            evidence.append("CLI directory found")
        if has_cli_framework:
            score += 20
            evidence.append("CLI framework/library detected")
        if is_simple_and_flat:
            score += 20
            evidence.append("Minimal flat structure typical of CLI tools")

        if score < 30:
            return None

        confidence = min(score, 90)
        return {
            "architecture": "CLI Application",
            "confidence": confidence,
            "reason": "Command-line interface structure detected",
            "evidence": evidence,
        }

    def _detect_library(self, scan: ProjectScanResult) -> dict | None:
        root_files_lower = {f.lower() for f in scan.root_files}
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        known_dirs = all_dir_names | root_dirs_lower

        has_setup = any(
            f in root_files_lower
            for f in ["setup.py", "setup.cfg", "pyproject.toml", "cargo.toml",
                       "package.json", "pom.xml", "build.gradle"]
        )
        has_lib_dir = "lib" in known_dirs or "src" in known_dirs
        no_app_structure = not any(
            d in known_dirs for d in ["controllers", "routes", "views", "templates", "api"]
        )
        has_module_pattern = "modules" in known_dirs or "packages" in known_dirs
        mostly_source = scan.source_file_count > 0 and scan.config_file_count <= 3
        few_root_files = len(scan.root_files) <= 8
        has_readme = scan.config_flags.get("readme", False)

        score = 0
        evidence = []
        if has_setup:
            score += 25
            evidence.append("Library package configuration found")
        if has_lib_dir:
            score += 20
            evidence.append("Library source directory found")
        if no_app_structure:
            score += 20
            evidence.append("No application-specific directories")
        if has_module_pattern:
            score += 10
            evidence.append("Module/package structure found")
        if mostly_source and few_root_files:
            score += 10
            evidence.append("Focused source with minimal config files")
        if has_readme:
            score += 5
            evidence.append("Documentation found")

        if score < 30:
            return None

        confidence = min(score, 85)
        return {
            "architecture": "Library",
            "confidence": confidence,
            "reason": "Package/library structure without application-layer directories",
            "evidence": evidence,
        }

    @staticmethod
    def _build_arch_reason(name: str, required: list[str],
                            supporting: list[str], confidence: int) -> str:
        parts: list[str] = []
        if required:
            parts.append(f"Required: {', '.join(required)}")
        if supporting:
            parts.append(f"Supporting: {', '.join(supporting[:3])}")
        if not parts:
            return f"Matched {name} pattern"
        return f"Detected {name} ({'; '.join(parts)})"

    def compute_health(self, arch_name: str) -> dict:
        scan = self._ensure_scan()
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        known_dirs = all_dir_names | root_dirs_lower

        detail: dict[str, int] = {}

        known_layer_names = {l["name"] for l in LAYER_DEFINITIONS}
        all_layer_dirs: set[str] = set()
        for l in LAYER_DEFINITIONS:
            all_layer_dirs.update(l["directories"])
        dirs_in_layers = [d for d in known_dirs if d in all_layer_dirs]
        ratio = len(dirs_in_layers) / max(len(known_dirs), 1)
        if ratio > 0.4:
            detail["folder_organization"] = 25
        elif ratio > 0.2:
            detail["folder_organization"] = 15
        else:
            detail["folder_organization"] = 5

        layer_count = len(self.detect_layers())
        if layer_count >= 4:
            detail["layer_separation"] = 30
        elif layer_count >= 2:
            detail["layer_separation"] = 15
        else:
            detail["layer_separation"] = 5

        naming_variants: set[tuple[str, str]] = set()
        for d in known_dirs:
            if "_" in d:
                naming_variants.add(("snake", d))
            if "-" in d:
                naming_variants.add(("kebab", d))
            if d.islower() and d.isalpha():
                naming_variants.add(("lower", d))
        naming_styles = {v[0] for v in naming_variants}
        if len(naming_styles) <= 2:
            detail["naming_consistency"] = 20
        elif len(naming_styles) <= 3:
            detail["naming_consistency"] = 10
        else:
            detail["naming_consistency"] = 5

        config_count = scan.config_file_count
        if config_count >= 3:
            detail["config_organization"] = 25
        elif config_count >= 1:
            detail["config_organization"] = 15
        else:
            detail["config_organization"] = 5

        total = sum(detail.values())
        if total >= 85:
            label = "Excellent"
        elif total >= 65:
            label = "Good"
        elif total >= 40:
            label = "Fair"
        else:
            label = "Poor"

        return {
            "score": total,
            "label": label,
            "details": detail,
        }

    def generate_recommendations(self) -> list[str]:
        scan = self._ensure_scan()
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        known_dirs = all_dir_names | root_dirs_lower

        recs: list[str] = []

        controllers = any(d in known_dirs for d in ["controllers", "routes"])
        services = any(d in known_dirs for d in ["services", "service"])
        repositories = any(d in known_dirs for d in ["repositories", "repository", "repo"])
        models = any(d in known_dirs for d in ["models", "schemas", "entities"])
        tests = any(d in known_dirs for d in ["tests", "test", "__tests__", "spec"])
        domain = any(d in known_dirs for d in ["domain", "entities", "aggregates"])
        application = any(d in known_dirs for d in ["application", "usecases", "use-cases"])
        infrastructure = any(d in known_dirs for d in ["infrastructure", "config"])
        api = any(d in known_dirs for d in ["api", "routes", "endpoints"])
        views = any(d in known_dirs for d in ["views", "templates", "components", "pages"])

        if controllers and not services:
            recs.append("Service layer missing between controllers and data access.")
        elif controllers and not repositories:
            recs.append("Repository layer missing. Consider abstracting data access.")
        if controllers and not models and not services:
            recs.append("Business logic appears mixed with controllers. Consider extracting services.")
        if not tests:
            recs.append("No test directory detected. Consider adding tests/ for better maintainability.")
        if views and not controllers and not api:
            recs.append("Views or templates found without clear controller layer.")
        if domain and not application:
            recs.append("Domain entities found without application use-cases layer.")
        if domain and not infrastructure:
            recs.append("Domain layer detected but no infrastructure layer for persistence.")
        if not models and (controllers or services or repositories):
            recs.append("No models or schemas directory found for data definitions.")
        if api and not services:
            recs.append("API endpoints detected without service layer for business logic.")
        if controllers and services and repositories and models:
            recs.append("Project structure is well organized with clear layer separation.")
        if not recs:
            recs.append("Consider organizing code into clearly named directories by concern.")

        return recs

    def compute_organization_summary(self) -> str:
        scan = self._ensure_scan()
        root_dirs_lower = {d.lower() for d in scan.root_dirs}
        all_dir_names = {d.lower() for d in scan.all_dir_names}
        known_dirs = all_dir_names | root_dirs_lower

        parts: list[str] = []
        if scan.has_src_or_app:
            parts.append("src/app root")

        layered = 0
        for ld in LAYER_DEFINITIONS:
            if any(d in known_dirs for d in ld["directories"]):
                layered += 1
        if layered >= 4:
            parts.append(f"{layered} functional layers")
        elif layered >= 2:
            parts.append(f"{layered} functional layers")
        else:
            parts.append("flat structure")

        distinct_langs = len(scan.language_counts)
        if distinct_langs <= 2:
            parts.append(f"{distinct_langs} languages")
        elif distinct_langs <= 4:
            parts.append(f"{distinct_langs} languages")

        total_dirs = len(known_dirs)
        parts.append(f"{total_dirs} directories")

        return " | ".join(parts)

    def compute_visual_layers(self) -> list[str]:
        layers = self.detect_layers()
        ordered_names = []
        for name in LAYER_ORDER:
            if any(l["name"] == name for l in layers):
                ordered_names.append(name)
        return ordered_names
