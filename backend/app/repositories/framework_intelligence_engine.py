import re
import json
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult


FRAMEWORK_VERSIONS: dict[str, dict[str, int]] = {
    "Flask": {"latest": 310, "stable": 300},
    "FastAPI": {"latest": 115, "stable": 110},
    "Django": {"latest": 52, "stable": 50},
    "React": {"latest": 19, "stable": 18},
    "Vue": {"latest": 3, "stable": 3},
    "Angular": {"latest": 18, "stable": 17},
    "Next.js": {"latest": 14, "stable": 14},
    "Nuxt": {"latest": 3, "stable": 3},
    "Express": {"latest": 5, "stable": 4},
    "NestJS": {"latest": 10, "stable": 10},
    "TensorFlow": {"latest": 216, "stable": 210},
    "PyTorch": {"latest": 2, "stable": 2},
    "Scikit-learn": {"latest": 12, "stable": 11},
    "Pandas": {"latest": 2, "stable": 2},
    "NumPy": {"latest": 2, "stable": 1},
    "SQLAlchemy": {"latest": 2, "stable": 2},
    "Spring Boot": {"latest": 3, "stable": 3},
    "Laravel": {"latest": 11, "stable": 10},
    "ASP.NET": {"latest": 8, "stable": 8},
    "Rails": {"latest": 7, "stable": 7},
    "Svelte": {"latest": 4, "stable": 4},
}

COMPATIBILITY_MATRIX: dict[str, list[dict]] = {
    "Flask": [
        {"with": "SQLAlchemy", "status": "compatible", "note": "Flask-SQLAlchemy provides seamless integration"},
        {"with": "Python", "status": "compatible", "note": "Compatible with Python 3.8+"},
    ],
    "FastAPI": [
        {"with": "SQLAlchemy", "status": "compatible", "note": "Compatible via async SQLAlchemy"},
        {"with": "Python", "status": "compatible", "note": "Compatible with Python 3.8+"},
    ],
    "Django": [
        {"with": "Python", "status": "compatible", "note": "Compatible with Python 3.10+"},
    ],
    "React": [
        {"with": "Node.js", "status": "compatible", "note": "Requires Node.js 18+"},
    ],
    "TensorFlow": [
        {"with": "NumPy", "status": "compatible", "note": "Requires NumPy 1.23+"},
        {"with": "Python", "status": "compatible", "note": "Compatible with Python 3.9-3.11"},
    ],
    "PyTorch": [
        {"with": "NumPy", "status": "compatible", "note": "Compatible with NumPy 1.x"},
        {"with": "Python", "status": "compatible", "note": "Compatible with Python 3.8+"},
    ],
    "Next.js": [
        {"with": "React", "status": "compatible", "note": "Built on React"},
        {"with": "Node.js", "status": "compatible", "note": "Requires Node.js 18+"},
    ],
    "SQLAlchemy": [
        {"with": "Python", "status": "compatible", "note": "Compatible with Python 3.7+"},
    ],
    "Scikit-learn": [
        {"with": "NumPy", "status": "compatible", "note": "Requires NumPy 1.17+"},
        {"with": "SciPy", "status": "compatible", "note": "Requires SciPy 1.5+"},
        {"with": "Python", "status": "compatible", "note": "Compatible with Python 3.8-3.11"},
    ],
    "Pandas": [
        {"with": "NumPy", "status": "compatible", "note": "Requires NumPy 1.20+"},
        {"with": "Python", "status": "compatible", "note": "Compatible with Python 3.8+"},
    ],
}

FEATURE_PATTERNS: dict[str, list[dict]] = {
    "REST API": [
        {"type": "import", "patterns": ["flask_restful", "flask-restful", "flask_restx", "rest_framework", "fastapi", "express", "rest"]},
        {"type": "directory", "patterns": ["api", "routes", "endpoints"]},
        {"type": "file", "patterns": ["urls.py", "router.py", "routes.py"]},
    ],
    "Authentication": [
        {"type": "import", "patterns": ["flask_login", "flask-login", "flask_httpauth", "flask_jwt", "jwt", "oauthlib", "passlib", "flask_jwt_extended", "django.contrib.auth", "authlib"]},
        {"type": "directory", "patterns": ["auth", "authentication"]},
    ],
    "ORM": [
        {"type": "import", "patterns": ["sqlalchemy", "flask_sqlalchemy", "peewee", "tortoise", "beanie", "mongoengine", "pony"]},
        {"type": "directory", "patterns": ["models", "migrations"]},
    ],
    "Database": [
        {"type": "dependency", "patterns": ["psycopg2", "pymysql", "pymongo", "redis", "mongoose", "pg"]},
        {"type": "file", "patterns": ["database.py", "db.py", "config.py"]},
    ],
    "Templates": [
        {"type": "import", "patterns": ["jinja2", "mako", "mustache", "handlebars"]},
        {"type": "directory", "patterns": ["templates", "views", "layouts"]},
        {"type": "file", "patterns": ["*.html", "*.jinja", "*.jinja2"]},
    ],
    "Middleware": [
        {"type": "import", "patterns": ["middleware", "middlewares"]},
        {"type": "directory", "patterns": ["middleware"]},
    ],
    "WebSockets": [
        {"type": "import", "patterns": ["socketio", "websocket", "websockets", "flask_socketio", "fastapi"]},
    ],
    "CLI": [
        {"type": "import", "patterns": ["click", "argparse", "typer", "fire"]},
        {"type": "file", "patterns": ["cli.py", "manage.py", "console.py"]},
    ],
    "Caching": [
        {"type": "import", "patterns": ["redis", "flask_caching", "django.core.cache", "cachetools"]},
        {"type": "directory", "patterns": ["cache"]},
    ],
    "Sessions": [
        {"type": "import", "patterns": ["flask_session", "flask.sessions", "django.contrib.sessions"]},
    ],
    "Admin Panel": [
        {"type": "import", "patterns": ["django.contrib.admin", "flask_admin", "flask-admin", "admin"]},
        {"type": "directory", "patterns": ["admin"]},
    ],
    "Scheduler": [
        {"type": "import", "patterns": ["celery", "rq", "apscheduler", "schedule", "dramatiq", "huey"]},
    ],
    "Blueprints": [
        {"type": "import", "patterns": ["blueprint", "flask.blueprints"]},
        {"type": "directory", "patterns": ["blueprints"]},
    ],
    "Testing": [
        {"type": "import", "patterns": ["pytest", "unittest", "jest", "mocha", "chai"]},
        {"type": "directory", "patterns": ["tests", "test", "__tests__", "spec"]},
    ],
}

FRAMEWORK_ROLES: dict[str, str] = {
    "Python": "Runtime",
    "JavaScript": "Runtime",
    "TypeScript": "Runtime",
    "HTML": "Markup",
    "CSS": "Styling",
    "Flask": "Backend Framework",
    "FastAPI": "Backend Framework",
    "Django": "Backend Framework",
    "React": "Frontend Framework",
    "Vue": "Frontend Framework",
    "Angular": "Frontend Framework",
    "Next.js": "Full Stack Framework",
    "Nuxt": "Full Stack Framework",
    "Express": "Backend Framework",
    "NestJS": "Backend Framework",
    "Svelte": "Frontend Framework",
    "SvelteKit": "Full Stack Framework",
    "Spring Boot": "Backend Framework",
    "Spring MVC": "Backend Framework",
    "Laravel": "Backend Framework",
    "CodeIgniter": "Backend Framework",
    "Symfony": "Backend Framework",
    "ASP.NET": "Backend Framework",
    "Blazor": "Frontend Framework",
    "Rails": "Backend Framework",
    "Sinatra": "Backend Framework",
    "Gin": "Backend Framework",
    "Echo": "Backend Framework",
    "Fiber": "Backend Framework",
    "Actix": "Backend Framework",
    "Rocket": "Backend Framework",
    "TensorFlow": "Deep Learning Library",
    "PyTorch": "Deep Learning Library",
    "Keras": "Deep Learning Library",
    "Scikit-learn": "Machine Learning Library",
    "XGBoost": "Machine Learning Library",
    "LightGBM": "Machine Learning Library",
    "CatBoost": "Machine Learning Library",
    "Pandas": "Data Processing Library",
    "NumPy": "Data Processing Library",
    "Polars": "Data Processing Library",
    "Matplotlib": "Visualization Library",
    "Seaborn": "Visualization Library",
    "Plotly": "Visualization Library",
    "SQLAlchemy": "ORM",
    "Flask-SQLAlchemy": "ORM",
    "Django ORM": "ORM",
    "Prisma": "ORM",
    "TypeORM": "ORM",
    "SQLite": "Database",
    "PostgreSQL": "Database",
    "MySQL": "Database",
    "MongoDB": "Database",
    "Redis": "Cache & Database",
    "JWT": "Authentication Library",
    "OAuth": "Authentication Library",
    "Flask-Login": "Authentication Library",
    "pytest": "Testing Library",
    "Jest": "Testing Library",
    "Mocha": "Testing Library",
    "Celery": "Task Queue",
    "Gunicorn": "WSGI Server",
    "Uvicorn": "ASGI Server",
    "Waitress": "WSGI Server",
    "Docker": "Container Runtime",
}


class FrameworkIntelligenceEngine:
    def __init__(self, scan_result: ProjectScanResult):
        self.scan = scan_result
        self._npm_deps: dict[str, str] = {}
        self._pip_deps: list[str] = []
        self._all_dir_names: set[str] = set()
        self._root_files: set[str] = set()

    def _setup(self) -> None:
        from app.repositories.framework_detector import FrameworkDetectorRepository
        from app.detection.project_scanner import ProjectScanner

        detector = FrameworkDetectorRepository(self.scan)
        self._npm_deps = detector._get_npm_deps()
        self._pip_deps = detector._get_pip_deps()
        self._all_dir_names = self.scan.all_dir_names
        self._root_files = {f.lower() for f in self.scan.root_files}

    @staticmethod
    def _parse_version(version_str: str) -> int:
        parts = re.findall(r"\d+", str(version_str))
        if not parts:
            return 0
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        return major * 100 + minor

    def extract_version(self, name: str) -> str | None:
        name_lower = name.lower().replace("-", "").replace("_", "")

        for dep_name, version in self._npm_deps.items():
            dep_clean = dep_name.lower().replace("-", "").replace("_", "").replace("@", "")
            if dep_clean == name_lower or dep_clean.endswith(name_lower):
                v = re.sub(r"^[\^~>=<]*", "", version.strip())
                return v

        pip_name_map: dict[str, str] = {
            "flask": "flask", "fastapi": "fastapi", "django": "django",
            "react": "react", "vue": "vue", "angular": "@angular/core",
            "tensorflow": "tensorflow", "torch": "torch", "pandas": "pandas",
            "numpy": "numpy", "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
            "sqlalchemy": "sqlalchemy", "flask-sqlalchemy": "flask-sqlalchemy",
            "pytest": "pytest", "celery": "celery",
        }
        pip_key = pip_name_map.get(name_lower)

        if pip_key:
            for dep in self._pip_deps:
                if dep.lower() == pip_key:
                    return None
                m = re.match(rf"^{re.escape(pip_key)}[=~<>!]+\s*([\d.]+)", dep, re.IGNORECASE)
                if m:
                    return m.group(1)

        has_pyproject = self.scan.pyproject_toml_content
        if has_pyproject and pip_key:
            for match in re.finditer(rf'"{re.escape(pip_key)}"\s*=\s*"\^?([\d.]+)"', has_pyproject):
                return match.group(1)

        return None

    def compute_health(self, name: str, version: str | None) -> dict:
        score = 50
        details: dict[str, int] = {}

        version_int = self._parse_version(version) if version else 0

        fw_info = FRAMEWORK_VERSIONS.get(name)
        if fw_info:
            latest = fw_info["latest"]
            stable = fw_info["stable"]
            if version_int >= latest:
                score += 40
                details["version"] = 100
            elif version_int >= stable:
                score += 30
                details["version"] = 80
            elif version_int > 0:
                score += 15
                details["version"] = 50
            else:
                score += 10
                details["version"] = 30
        else:
            if version_int > 0:
                score += 20
                details["version"] = 60
            else:
                score += 5
                details["version"] = 20

        if version:
            score += 10
            details["detected"] = 100
        else:
            details["detected"] = 50

        supports_python3 = name in (
            "Flask", "FastAPI", "Django", "SQLAlchemy", "Pandas", "NumPy",
            "Scikit-learn", "TensorFlow", "PyTorch", "pytest",
        )
        if supports_python3:
            score += 10
            details["support"] = 100
        else:
            details["support"] = 80

        is_deprecated = name in ("Tornado", "Bottle", "Pyramid", "web2py")
        if is_deprecated:
            score -= 20
            details["deprecated"] = 0
        else:
            details["deprecated"] = 100

        if name == "TensorFlow" and version_int > 0 and version_int < 200:
            score -= 10
            details["compat"] = 60
        elif name == "NumPy" and version_int > 0 and version_int < 120:
            score -= 5
            details["compat"] = 70
        else:
            details["compat"] = 100

        score = max(0, min(100, score))

        if score >= 85:
            label = "Excellent"
        elif score >= 70:
            label = "Good"
        elif score >= 50:
            label = "Fair"
        else:
            label = "Poor"

        return {"score": score, "label": label, "details": details}

    def check_compatibility(self, frameworks: list[str]) -> list[dict]:
        results: list[dict] = []
        checked: set[tuple[str, str]] = set()
        for fw in frameworks:
            compat_list = COMPATIBILITY_MATRIX.get(fw, [])
            for check in compat_list:
                pair = (fw, check["with"])
                if pair not in checked and check["with"] in frameworks:
                    checked.add(pair)
                    results.append({
                        "framework": fw,
                        "with": check["with"],
                        "status": check["status"],
                        "note": check["note"],
                    })
        for fw in frameworks:
            for fw2 in frameworks:
                if fw != fw2:
                    pair = (fw, fw2)
                    reverse = (fw2, fw)
                    if pair not in checked and reverse not in checked:
                        fw_compat = COMPATIBILITY_MATRIX.get(fw, [])
                        for check in fw_compat:
                            if check["with"] == fw2:
                                checked.add(pair)
                                results.append({
                                    "framework": fw,
                                    "with": fw2,
                                    "status": check["status"],
                                    "note": check["note"],
                                })
        return results

    def build_dependency_graph(self, technologies: list[dict]) -> list[dict]:
        layers = [
            ("Application Framework", "Application", ["Flask", "FastAPI", "Django", "React", "Vue", "Angular", "Next.js", "Express", "Spring Boot", "Laravel"]),
            ("Backend Framework", "Backend", ["Flask", "FastAPI", "Django", "Express", "NestJS", "Spring Boot", "Laravel"]),
            ("Frontend Framework", "Frontend", ["React", "Vue", "Angular", "Next.js", "Nuxt", "Svelte"]),
            ("ORM", "ORM", ["SQLAlchemy", "Flask-SQLAlchemy", "Prisma", "TypeORM", "Mongoose"]),
            ("Database", "Database", ["PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis"]),
            ("Deep Learning", "Deep Learning", ["TensorFlow", "PyTorch", "Keras", "Hugging Face"]),
            ("Machine Learning", "Machine Learning", ["Scikit-learn", "XGBoost", "LightGBM", "CatBoost"]),
            ("Data Processing", "Data Processing", ["Pandas", "NumPy", "Polars"]),
            ("Visualization", "Visualization", ["Matplotlib", "Seaborn", "Plotly"]),
            ("Testing", "Testing", ["pytest", "Jest", "Mocha"]),
            ("Authentication", "Authentication", ["JWT", "OAuth", "Flask-Login"]),
            ("Task Queue", "Task Queue", ["Celery"]),
        ]

        tech_names = {t.get("name", "") for t in technologies}

        graph: list[dict] = []
        seen_names: set[str] = set()

        for layer_name, alias, candidates in layers:
            layer_techs = [c for c in candidates if c in tech_names and c not in seen_names]
            for t in layer_techs:
                seen_names.add(t)
            if layer_techs:
                graph.append({
                    "layer": layer_name,
                    "label": alias,
                    "technologies": layer_techs,
                })

        remaining = [t.get("name", "") for t in technologies if t.get("name") not in seen_names]
        if remaining:
            graph.append({
                "layer": "Utilities",
                "label": "Utilities",
                "technologies": remaining,
            })

        return graph

    def detect_features(self) -> list[dict]:
        scan = self.scan
        all_dir_names = scan.all_dir_names
        import_set = scan.python_imports | scan.js_imports
        pip_set = set(self._pip_deps)
        npm_names = set(self._npm_deps.keys())
        all_files_set = set(scan.all_files)
        root_files_set = set(scan.root_files)

        detected: list[dict] = []

        for feature_name, patterns in FEATURE_PATTERNS.items():
            confidence = 0
            evidence: list[str] = []

            for pattern in patterns:
                ptype = pattern["type"]
                pvalues = pattern["patterns"]

                if ptype == "import":
                    matched = [p for p in pvalues if p in import_set]
                    if matched:
                        confidence += 30
                        evidence.append(f"Import: {matched[0]}")

                elif ptype == "directory":
                    matched = [p for p in pvalues if p in all_dir_names]
                    if matched:
                        confidence += 20
                        evidence.append(f"Dir: {matched[0]}")

                elif ptype == "file":
                    matched = [p for p in pvalues if p in root_files_set or p in all_files_set]
                    if not matched:
                        matched = []
                        for p in pvalues:
                            if p.startswith("*."):
                                ext = p[1:]
                                if any(f.endswith(ext) for f in all_files_set):
                                    matched.append(p)
                    if matched:
                        confidence += 25
                        evidence.append(f"File: {matched[0]}")

                elif ptype == "dependency":
                    matched = [p for p in pvalues if p in pip_set or p in npm_names]
                    if matched:
                        confidence += 30
                        evidence.append(f"Dep: {matched[0]}")

            if confidence > 0:
                detected.append({
                    "name": feature_name,
                    "confidence": min(confidence, 99),
                    "evidence": evidence[:3],
                })

        detected.sort(key=lambda f: -f["confidence"])
        return detected

    def get_role(self, name: str) -> str:
        return FRAMEWORK_ROLES.get(name, "Library")

    def analyze(self) -> dict:
        self._setup()

        from app.repositories.framework_detector import FrameworkDetectorRepository
        from app.repositories.technology_classifier import TechnologyClassifier

        detector = FrameworkDetectorRepository(self.scan)
        framework_list = detector.detect_frameworks()
        database_list = detector.detect_databases()
        orm_list = detector.detect_orms()
        pm_list = detector.detect_package_managers()

        categorized = TechnologyClassifier.build_response(
            framework_techs=framework_list,
            database_techs=database_list,
            orm_techs=orm_list,
            pm_techs=pm_list,
        )

        all_techs: list[dict] = []
        tech_names: list[str] = []
        for cat, items in categorized.items():
            for item in items:
                all_techs.append(item)
                tech_names.append(item["name"])

        app_frameworks = [t for t in all_techs if t.get("category") == "Application Framework"]
        primary_framework = app_frameworks[0] if app_frameworks else (all_techs[0] if all_techs else None)

        for tech in all_techs:
            tech["version"] = self.extract_version(tech["name"]) or tech.get("version")
            health = self.compute_health(tech["name"], tech["version"])
            tech["health"] = health
            tech["role"] = self.get_role(tech["name"])

        framework_names = [t["name"] for t in all_techs]
        compatibility = self.check_compatibility(framework_names)
        features = self.detect_features()
        dep_graph = self.build_dependency_graph(all_techs)

        # Detect project type
        project_type = "Unknown"
        if primary_framework:
            project_type = f"{primary_framework['name']} Application"

        evidence: list[dict] = []
        for tech in all_techs[:5]:
            evidence.append({
                "name": tech["name"],
                "source": tech.get("detection_source", "Unknown"),
                "confidence": tech["confidence"],
            })

        return {
            "project_type": project_type,
            "primary_framework": primary_framework,
            "frameworks": all_techs,
            "compatibility": compatibility,
            "features": features,
            "dependency_graph": dep_graph,
            "evidence": evidence,
        }
