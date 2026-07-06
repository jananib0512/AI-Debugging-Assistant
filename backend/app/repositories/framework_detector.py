import json
import os
import re
from pathlib import Path

from app.detection.project_scanner import ProjectScanResult, ProjectScanner

LANGUAGE_PATTERNS: list[dict] = [
    {"name": "Python", "config_files": ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py", "setup.cfg"], "extensions": {".py", ".pyx", ".pyi"}},
    {"name": "JavaScript", "config_files": ["package.json", "package-lock.json"], "extensions": {".js", ".mjs", ".cjs"}},
    {"name": "TypeScript", "config_files": ["tsconfig.json", "tsconfig.node.json"], "extensions": {".ts", ".tsx"}},
    {"name": "Java", "config_files": ["pom.xml", "build.gradle", "build.gradle.kts"], "extensions": {".java"}},
    {"name": "Go", "config_files": ["go.mod", "go.sum"], "extensions": {".go"}},
    {"name": "Rust", "config_files": ["Cargo.toml"], "extensions": {".rs"}},
    {"name": "PHP", "config_files": ["composer.json"], "extensions": {".php"}},
    {"name": "C#", "config_files": [], "extensions": {".cs", ".csproj", ".sln"}},
    {"name": "C++", "config_files": ["CMakeLists.txt", "Makefile"], "extensions": {".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".hh"}},
    {"name": "Ruby", "config_files": ["Gemfile"], "extensions": {".rb"}},
    {"name": "Kotlin", "config_files": [], "extensions": {".kt", ".kts"}},
    {"name": "Swift", "config_files": [], "extensions": {".swift"}},
    {"name": "Dart", "config_files": [], "extensions": {".dart"}},
    {"name": "Vue", "config_files": [], "extensions": {".vue"}},
    {"name": "Svelte", "config_files": [], "extensions": {".svelte"}},
]

FRAMEWORK_PATTERNS: list[dict] = [
    {"name": "React", "package_dep": "react", "config_files": [], "confidence_bonus": {"jsx", "tsx"}},
    {"name": "Next.js", "package_dep": "next", "config_files": ["next.config.js", "next.config.mjs", "next.config.ts", "next-env.d.ts"], "confidence_bonus": set()},
    {"name": "Vue", "package_dep": "vue", "config_files": [], "confidence_bonus": set()},
    {"name": "Angular", "package_dep": "@angular/core", "config_files": ["angular.json"], "confidence_bonus": set()},
    {"name": "Nuxt", "package_dep": "nuxt", "config_files": ["nuxt.config.js", "nuxt.config.ts"], "confidence_bonus": set()},
    {"name": "SvelteKit", "package_dep": "@sveltejs/kit", "config_files": ["svelte.config.js"], "confidence_bonus": set()},
    {"name": "Gatsby", "package_dep": "gatsby", "config_files": ["gatsby-config.js"], "confidence_bonus": set()},
    {"name": "Remix", "package_dep": "@remix-run/react", "config_files": ["remix.config.js"], "confidence_bonus": set()},
    {"name": "FastAPI", "pip_dep": "fastapi", "config_files": [], "confidence_bonus": set()},
    {"name": "Flask", "pip_dep": "flask", "config_files": [], "confidence_bonus": set()},
    {"name": "Django", "pip_dep": "django", "config_files": ["manage.py"], "confidence_bonus": set()},
    {"name": "Express", "package_dep": "express", "config_files": [], "confidence_bonus": set()},
    {"name": "NestJS", "package_dep": "@nestjs/core", "config_files": [], "confidence_bonus": set()},
    {"name": "Spring Boot", "pom_parent": "spring-boot-starter-parent", "config_files": [], "confidence_bonus": set()},
    {"name": "Laravel", "composer_dep": "laravel/framework", "config_files": ["artisan"], "confidence_bonus": set()},
    {"name": "ASP.NET", "config_files": [], "confidence_bonus": set()},
    {"name": "Electron", "package_dep": "electron", "config_files": [], "confidence_bonus": set()},
    {"name": "React Native", "package_dep": "react-native", "config_files": [], "confidence_bonus": set()},
    {"name": "TensorFlow", "pip_dep": "tensorflow", "config_files": [], "confidence_bonus": set()},
    {"name": "PyTorch", "pip_dep": "torch", "config_files": [], "confidence_bonus": set()},
    {"name": "Scikit-learn", "pip_dep": "scikit-learn", "config_files": [], "confidence_bonus": set()},
    {"name": "Pandas", "pip_dep": "pandas", "config_files": [], "confidence_bonus": set()},
    {"name": "Fastify", "package_dep": "fastify", "config_files": [], "confidence_bonus": set()},
    {"name": "Koa", "package_dep": "koa", "config_files": [], "confidence_bonus": set()},
    {"name": "Flask-SQLAlchemy", "pip_dep": "flask-sqlalchemy", "config_files": [], "confidence_bonus": set()},
    {"name": "SQLAlchemy", "pip_dep": "sqlalchemy", "config_files": [], "confidence_bonus": set()},
    {"name": "Hugging Face", "pip_dep": "transformers", "config_files": [], "confidence_bonus": set()},
    {"name": "Jupyter", "config_files": [], "extensions": {".ipynb"}, "confidence_bonus": set()},
]

RUNTIME_PATTERNS: list[dict] = [
    {"name": "Node.js", "evidence": ["package.json", "node_modules", ".nvmrc", ".node-version"]},
    {"name": "Python", "evidence": ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]},
    {"name": "JVM", "evidence": ["pom.xml", "build.gradle", "build.gradle.kts", "gradlew"]},
    {"name": ".NET", "evidence": [".csproj", ".sln"]},
    {"name": "Go", "evidence": ["go.mod"]},
    {"name": "Rust", "evidence": ["Cargo.toml"]},
    {"name": "PHP", "evidence": ["composer.json"]},
    {"name": "Ruby", "evidence": ["Gemfile"]},
    {"name": "Elixir", "evidence": ["mix.exs"]},
    {"name": "Deno", "evidence": ["deno.json", "deno.jsonc", "import_map.json"]},
]

PM_PATTERNS: list[dict] = [
    {"name": "npm", "lock_files": ["package-lock.json"], "config_file": "package.json"},
    {"name": "yarn", "lock_files": ["yarn.lock"], "config_file": "package.json"},
    {"name": "pnpm", "lock_files": ["pnpm-lock.yaml"], "config_file": "package.json"},
    {"name": "pip", "lock_files": ["requirements.txt"], "config_file": None},
    {"name": "Poetry", "lock_files": ["poetry.lock", "pyproject.toml"], "config_file": "pyproject.toml"},
    {"name": "Pipenv", "lock_files": ["Pipfile", "Pipfile.lock"], "config_file": None},
    {"name": "Conda", "lock_files": ["environment.yml"], "config_file": None},
    {"name": "Cargo", "lock_files": ["Cargo.toml", "Cargo.lock"], "config_file": "Cargo.toml"},
    {"name": "Composer", "lock_files": ["composer.json", "composer.lock"], "config_file": "composer.json"},
    {"name": "Bundler", "lock_files": ["Gemfile", "Gemfile.lock"], "config_file": "Gemfile"},
    {"name": "Go Modules", "lock_files": ["go.mod", "go.sum"], "config_file": "go.mod"},
    {"name": "Maven", "lock_files": ["pom.xml"], "config_file": "pom.xml"},
    {"name": "Gradle", "lock_files": ["build.gradle", "build.gradle.kts"], "config_file": "build.gradle"},
]

BUILD_TOOL_PATTERNS: list[dict] = [
    {"name": "Vite", "config_files": ["vite.config.ts", "vite.config.js", "vite.config.mjs"]},
    {"name": "Webpack", "config_files": ["webpack.config.js", "webpack.config.ts"]},
    {"name": "Rollup", "config_files": ["rollup.config.js", "rollup.config.ts"]},
    {"name": "esbuild", "config_files": ["esbuild.config.js", "esbuild.config.ts"]},
    {"name": "Gradle", "config_files": ["build.gradle", "build.gradle.kts", "gradlew"]},
    {"name": "Maven", "config_files": ["pom.xml", "mvnw"]},
    {"name": "TurboRepo", "config_files": ["turbo.json"]},
    {"name": "Nx", "config_files": ["nx.json", "workspace.json"]},
    {"name": "Lerna", "config_files": ["lerna.json"]},
    {"name": "Rush", "config_files": ["rush.json"]},
    {"name": "Pants", "config_files": ["pants.toml", "pants.ini"]},
    {"name": "Bazel", "config_files": ["BUILD", "WORKSPACE", "BUILD.bazel"]},
    {"name": "Make", "config_files": ["Makefile"]},
    {"name": "CMake", "config_files": ["CMakeLists.txt"]},
]

DATABASE_PATTERNS: list[dict] = [
    {"name": "PostgreSQL", "pip_deps": ["psycopg2", "psycopg2-binary", "psycopg", "asyncpg"], "npm_deps": ["pg", "pg-promise", "pg-native", "sequelize", "typeorm"], "imports": ["psycopg2"]},
    {"name": "MySQL", "pip_deps": ["mysqlclient", "pymysql", "mysql-connector-python", "aiomysql"], "npm_deps": ["mysql", "mysql2"], "imports": ["pymysql", "mysqlclient"]},
    {"name": "SQLite", "pip_deps": ["sqlite3"], "npm_deps": ["sqlite3", "better-sqlite3"], "imports": ["sqlite3"]},
    {"name": "MongoDB", "pip_deps": ["pymongo", "mongoengine", "motor"], "npm_deps": ["mongoose", "mongodb", "mongosh"], "imports": ["pymongo", "motor", "mongoengine"]},
    {"name": "Redis", "pip_deps": ["redis", "aioredis", "redis-py"], "npm_deps": ["redis", "ioredis"], "imports": ["redis", "aioredis"]},
    {"name": "MariaDB", "pip_deps": ["mariadb"], "npm_deps": ["mariadb"], "imports": ["mariadb"]},
    {"name": "SQL Server", "pip_deps": ["pyodbc", "pymssql"], "npm_deps": ["tedious", "mssql"], "imports": ["pyodbc", "pymssql"]},
    {"name": "Oracle", "pip_deps": ["cx_oracle", "oracledb"], "npm_deps": ["oracledb"], "imports": ["cx_oracle", "oracledb"]},
    {"name": "DynamoDB", "npm_deps": ["aws-sdk", "@aws-sdk/client-dynamodb"], "pip_deps": ["boto3", "aiobotocore"], "imports": ["boto3"]},
    {"name": "Firebase", "npm_deps": ["firebase", "firebase-admin"], "pip_deps": ["firebase-admin"], "imports": ["firebase_admin"]},
    {"name": "Supabase", "npm_deps": ["@supabase/supabase-js", "@supabase/realtime-js"], "pip_deps": ["supabase"], "imports": ["supabase"]},
    {"name": "Elasticsearch", "pip_deps": ["elasticsearch", "elasticsearch-dsl"], "npm_deps": ["@elastic/elasticsearch"], "imports": ["elasticsearch"]},
    {"name": "Cassandra", "pip_deps": ["cassandra-driver"], "npm_deps": ["cassandra-driver"], "imports": ["cassandra"]},
    {"name": "Neo4j", "pip_deps": ["neo4j", "py2neo"], "npm_deps": ["neo4j-driver"], "imports": ["neo4j", "py2neo"]},
]

ORM_PATTERNS: list[dict] = [
    {"name": "SQLAlchemy", "pip_deps": ["sqlalchemy"], "npm_deps": [], "imports": ["sqlalchemy"], "migration": "Alembic"},
    {"name": "Flask-SQLAlchemy", "pip_deps": ["flask-sqlalchemy"], "npm_deps": [], "imports": ["flask_sqlalchemy"], "migration": "Flask-Migrate"},
    {"name": "Django ORM", "pip_deps": ["django"], "npm_deps": [], "imports": ["django"], "migration": "Django Migrations"},
    {"name": "Peewee", "pip_deps": ["peewee"], "npm_deps": [], "imports": ["peewee"], "migration": None},
    {"name": "Pony ORM", "pip_deps": ["pony"], "npm_deps": [], "imports": ["pony"], "migration": None},
    {"name": "Tortoise ORM", "pip_deps": ["tortoise-orm"], "npm_deps": [], "imports": ["tortoise"], "migration": "Aerich"},
    {"name": "MongoEngine", "pip_deps": ["mongoengine"], "npm_deps": [], "imports": ["mongoengine"], "migration": None},
    {"name": "Beanie", "pip_deps": ["beanie"], "npm_deps": [], "imports": ["beanie"], "migration": None},
    {"name": "Prisma", "npm_deps": ["@prisma/client"], "pip_deps": ["prisma"], "imports": ["prisma"], "migration": "Prisma Migrate"},
    {"name": "Sequelize", "npm_deps": ["sequelize"], "pip_deps": [], "imports": [], "migration": None},
    {"name": "TypeORM", "npm_deps": ["typeorm"], "pip_deps": [], "imports": [], "migration": None},
    {"name": "Mongoose", "npm_deps": ["mongoose"], "pip_deps": [], "imports": [], "migration": None},
]

MIGRATION_PATTERNS: list[dict] = [
    {"name": "Alembic", "dirs": ["alembic"], "files": ["alembic.ini"], "pip_dep": "alembic"},
    {"name": "Flask-Migrate", "dirs": ["migrations"], "files": [], "pip_dep": "flask-migrate"},
    {"name": "Django Migrations", "dirs": [], "files": [], "detect": "django"},
    {"name": "Prisma Migrate", "dirs": ["prisma"], "files": ["schema.prisma"], "npm_dep": "@prisma/client"},
    {"name": "Flyway", "dirs": ["flyway"], "files": ["flyway.conf", "flyway.toml"], "npm_dep": None},
    {"name": "Liquibase", "dirs": ["liquibase"], "files": ["liquibase.properties"], "npm_dep": None},
]

DB_FILE_EXTENSIONS: set[str] = {".db", ".sqlite", ".sqlite3", ".sqlitedb", ".db3"}

CONTAINER_PATTERNS: list[dict] = [
    {"name": "Docker", "files": ["Dockerfile", "Dockerfile.dev", "Dockerfile.prod"]},
    {"name": "Docker Compose", "files": ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]},
    {"name": "Kubernetes", "files": [], "dirs": ["k8s", "kubernetes", "helm", "charts"]},
]

ML_PATTERNS: list[str] = [
    "jupyter", "notebook", "tensorflow", "pytorch", "sklearn",
    "scikit-learn", "keras", "onnx", "xgboost", "lightgbm",
    "transformers", "datasets", "huggingface",
]


class FrameworkDetectorRepository:
    def __init__(self, scan_result: ProjectScanResult | None = None) -> None:
        self._scan: ProjectScanResult | None = scan_result
        self._root_files: set[str] = set()
        self._root_dirs: set[str] = set()
        self._all_extensions: set[str] = set()

    def scan(self, workspace_path: str) -> None:
        scanner = ProjectScanner()
        self._scan = scanner.scan(Path(workspace_path))

    def _ensure_scan(self) -> ProjectScanResult:
        assert self._scan is not None, "call scan() first"
        return self._scan

    def _get_npm_deps(self) -> dict[str, str]:
        scan = self._ensure_scan()
        if not scan.package_json:
            return {}
        return ProjectScanner._get_npm_deps_from_pkg(scan.package_json)

    def _get_npm_dep_names(self) -> set[str]:
        return set(self._get_npm_deps().keys())

    def _get_pip_deps(self) -> list[str]:
        return self._ensure_scan().requirements_txt_deps

    def _check_pip_dep(self, dep_name: str) -> bool:
        return dep_name.lower() in self._get_pip_deps()

    def _get_root_file_names(self) -> set[str]:
        return {f.lower() for f in self._ensure_scan().root_files}

    def _get_root_dir_names(self) -> set[str]:
        return {d.lower() for d in self._ensure_scan().root_dirs}

    def detect_languages(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        root_files = self._get_root_file_names()
        root_dirs = self._get_root_dir_names()

        for lang in LANGUAGE_PATTERNS:
            confidence = 0
            reasons: list[str] = []
            lang_exts: set[str] = lang["extensions"] & {os.path.splitext(f)[1].lower() for f in scan.root_files}
            lang_exts |= lang["extensions"] & {os.path.splitext(f)[1].lower() for f in scan.all_files}

            has_source = scan.language_counts.get(lang["name"], 0) > 0
            has_config = any(f in root_files for f in lang["config_files"])

            if has_source:
                confidence += 50
                file_count = scan.language_counts[lang["name"]]
                reasons.append(f"{file_count} source file(s) detected")

            if has_config:
                confidence += 30
                config_found = [f for f in lang["config_files"] if f in root_files]
                reasons.append(f"Found {config_found[0]}")

            if has_source and has_config:
                confidence += 10

            if confidence > 0:
                pct = 0.0
                if scan.total_source_files > 0:
                    pct = round(scan.language_counts.get(lang["name"], 0) / scan.total_source_files * 100, 1)
                results.append({
                    "name": lang["name"],
                    "version": None,
                    "confidence": min(confidence, 99),
                    "percentage": pct,
                    "reason": "; ".join(reasons),
                })

        results.sort(key=lambda r: (-r["confidence"], -r.get("percentage", 0)))
        return results

    def detect_frameworks(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        root_files = self._get_root_file_names()
        npm_deps = self._get_npm_deps()
        pip_deps = self._get_pip_deps()
        python_imports = scan.python_imports
        js_imports = scan.js_imports
        root_dirs = self._get_root_dir_names()

        has_pyproject = scan.pyproject_toml_content is not None
        pyproject_lower = (scan.pyproject_toml_content or "").lower()

        all_exts: set[str] = set()
        for f in scan.root_files:
            all_exts.add(os.path.splitext(f)[1].lower())
        for f in scan.all_files:
            all_exts.add(os.path.splitext(f)[1].lower())

        for fw in FRAMEWORK_PATTERNS:
            confidence = 0
            reasons: list[str] = []

            if "package_dep" in fw:
                dep_name = fw["package_dep"]
                if dep_name in npm_deps:
                    version = npm_deps[dep_name]
                    if version and version not in ("*", "latest"):
                        confidence += 60
                        reasons.append(f"Dependency: {dep_name}@{version}")
                    else:
                        confidence += 55
                        reasons.append(f"Dependency: {dep_name}")
                elif dep_name in js_imports:
                    confidence += 45
                    reasons.append(f"Import: {dep_name}")

            if "pip_dep" in fw:
                dep_name = fw["pip_dep"]
                if self._check_pip_dep(dep_name):
                    confidence += 60
                    reasons.append(f"Python dependency: {dep_name}")
                elif dep_name in python_imports:
                    confidence += 50
                    reasons.append(f"Python import: {dep_name}")

                if has_pyproject and dep_name in pyproject_lower:
                    if confidence == 0:
                        confidence += 50
                        reasons.append(f"Found in pyproject.toml: {dep_name}")

            if "composer_dep" in fw:
                if scan.composer_json and "require" in scan.composer_json:
                    requires = scan.composer_json["require"]
                    if isinstance(requires, dict) and fw["composer_dep"] in requires:
                        confidence += 60
                        reasons.append(f"Composer: {fw['composer_dep']}")

            if "pom_parent" in fw:
                if "pom.xml" in root_files:
                    confidence += 45
                    reasons.append(f"Maven POM with {fw['pom_parent']}")

            if "config_files" in fw:
                has_config = any(f in root_files for f in fw["config_files"])
                if has_config:
                    confidence += 30
                    config_found = [f for f in fw["config_files"] if f in root_files]
                    reasons.append(f"Found {config_found[0]}")

            if "confidence_bonus" in fw and fw["confidence_bonus"]:
                matched = all_exts & fw["confidence_bonus"]
                if matched:
                    confidence += 10
                    reasons.append(f"File extensions: {', '.join(matched)}")

            if "extensions" in fw:
                matched = all_exts & fw.get("extensions", set())
                if matched:
                    confidence += 15
                    reasons.append(f"Source files: {', '.join(matched)}")

            if fw["name"] == "Django":
                if "manage.py" in root_files:
                    if confidence < 70:
                        confidence = max(confidence, 65)
                    reasons.append("manage.py detected")
                if "settings.py" in root_files:
                    confidence = max(confidence, 75)
                    reasons.append("Django settings.py detected")
                if "wsgi.py" in root_files:
                    confidence = max(confidence, 60)
                    reasons.append("Django WSGI entry point")

            if fw["name"] == "Flask":
                if "app.py" in root_files:
                    if confidence < 60:
                        confidence = max(confidence, 55)
                    reasons.append("app.py detected")
                if "run.py" in root_files:
                    if "run.py" not in reasons:
                        reasons.append("run.py detected")
                if scan.dockerfile_content and "flask" in scan.dockerfile_content.lower():
                    confidence = max(confidence, 60)
                    reasons.append("Flask referenced in Dockerfile")
                if "templates" in root_dirs or "static" in root_dirs:
                    confidence = max(confidence, 50)
                    reasons.append("Flask project dirs found")

            if fw["name"] == "FastAPI":
                if "main.py" in root_files:
                    confidence = max(confidence, 50)
                    if "fastapi" not in reasons:
                        reasons.append("main.py detected")

            if confidence > 0:
                results.append({
                    "name": fw["name"],
                    "version": None,
                    "confidence": min(confidence, 99),
                    "reason": "; ".join(reasons),
                })

        return sorted(results, key=lambda r: -r["confidence"])

    def detect_runtimes(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        root_files = self._get_root_file_names()
        root_dirs = self._get_root_dir_names()

        for rt in RUNTIME_PATTERNS:
            matched = [e for e in rt["evidence"] if e in root_files or e in root_dirs]
            if not matched:
                matched = [e for e in rt["evidence"] if e.lower() in {f.lower() for f in scan.root_files}]
            if matched:
                confidence = min(50 + len(matched) * 15, 99)
                results.append({
                    "name": rt["name"],
                    "version": self._detect_runtime_version(rt["name"]),
                    "confidence": confidence,
                    "reason": f"Evidence: {', '.join(matched[:3])}",
                })
        return results

    def _detect_runtime_version(self, runtime: str) -> str | None:
        scan = self._ensure_scan()
        if runtime == "Node.js" and scan.package_json:
            engines = scan.package_json.get("engines", {})
            return engines.get("node", None)
        if runtime == "Python" and scan.pyproject_toml_content:
            m = re.search(r'requires-python\s*=\s*"([^"]+)"', scan.pyproject_toml_content)
            if m:
                return m.group(1)
        return None

    def detect_package_managers(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        root_files = self._get_root_file_names()

        for pm in PM_PATTERNS:
            matched_locks = [f for f in pm["lock_files"] if f in root_files]
            if matched_locks:
                confidence = 70 + (15 if pm["config_file"] and pm["config_file"] in root_files else 0)
                if len(matched_locks) > 1:
                    confidence += 10
                confidence = min(confidence, 99)
                reasons = [f"Found {matched_locks[0]}"]
                if pm["config_file"] and pm["config_file"] in root_files:
                    reasons.append(f"Config: {pm['config_file']}")
                if len(matched_locks) > 1:
                    reasons.append(f"Also found {matched_locks[1]}")
                results.append({
                    "name": pm["name"],
                    "version": None,
                    "confidence": confidence,
                    "reason": "; ".join(reasons),
                })

        if not results:
            if "composer.json" in root_files:
                results.append({
                    "name": "Composer",
                    "version": None,
                    "confidence": 50,
                    "reason": "composer.json detected (no lock file)",
                })
            if "Gemfile" in root_files:
                results.append({
                    "name": "Bundler",
                    "version": None,
                    "confidence": 50,
                    "reason": "Gemfile detected (no lock file)",
                })

        return results

    def detect_build_tools(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        root_files = self._get_root_file_names()

        for bt in BUILD_TOOL_PATTERNS:
            matched = [f for f in bt["config_files"] if f in root_files]
            if matched:
                results.append({
                    "name": bt["name"],
                    "version": None,
                    "confidence": min(60 + len(matched) * 15, 99),
                    "reason": f"Found {matched[0]}",
                })
        return results

    @staticmethod
    def _mask_uri(uri: str) -> str:
        masked = re.sub(r"(://[^:]+:)[^@]+(@)", r"\1****\2", uri)
        masked = re.sub(r"(://:)[^@]+(@)", r"\1****\2", masked)
        masked = re.sub(r"(password=)[^&\s]+", r"\1****", masked, flags=re.IGNORECASE)
        return masked

    def detect_databases(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        npm_deps = self._get_npm_deps()
        pip_deps = self._get_pip_deps()
        python_imports = scan.python_imports
        root_files = self._get_root_file_names()
        all_files = scan.all_files
        all_dir_names = scan.all_dir_names

        config_text = ""
        for txt in [scan.config_py_content, scan.settings_py_content,
                     scan.database_py_content, scan.env_content,
                     scan.env_example_content]:
            if txt:
                config_text += txt.lower() + "\n"

        all_npm_names = set(npm_deps.keys())
        all_pip_names = set(pip_deps)

        orms_found = self.detect_orms()
        orm_names = {o["name"].lower() for o in orms_found}
        migrations_found = self.detect_migrations()
        db_files_found = self.detect_database_files()

        for db in DATABASE_PATTERNS:
            confidence = 0
            reasons: list[str] = []

            # Dependency evidence
            matched_npm = [d for d in db["npm_deps"] if d in all_npm_names]
            matched_pip = [d for d in db["pip_deps"] if d in all_pip_names]
            if matched_npm:
                confidence += 40
                reasons.append(f"npm: {matched_npm[0]}")
            if matched_pip:
                confidence += 40
                reasons.append(f"pip: {matched_pip[0]}")

            # Import evidence
            db_imports = db.get("imports", [])
            matched_imports = [i for i in db_imports if i in python_imports]
            if matched_imports:
                confidence += 30
                reasons.append(f"Import: {matched_imports[0]}")

            # Config reference evidence
            db_name_lower = db["name"].lower().replace(" ", "")
            if db_name_lower in config_text:
                confidence += 25
                reasons.append("Referenced in config")

            # URI evidence (masked)
            db_uri_keys = {
                "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
                "mysql": "MySQL", "sqlite": "SQLite",
                "mongodb": "MongoDB", "redis": "Redis",
                "mssql": "SQL Server", "oracle": "Oracle",
                "firebase": "Firebase", "elasticsearch": "Elasticsearch",
                "cassandra": "Cassandra", "neo4j": "Neo4j",
                "supabase": "Supabase", "dynamodb": "DynamoDB",
            }
            for uri in scan.db_uris:
                for key, dname in db_uri_keys.items():
                    if dname == db["name"] and key in uri.lower():
                        masked = self._mask_uri(uri)
                        confidence += 35
                        reasons.append(f"URI: {masked}")
                        break
                else:
                    continue
                break

            # Database file evidence
            for dbf in db_files_found:
                if db["name"].lower() == "sqlite":
                    if any(dbf["path"].lower().endswith(ext) for ext in DB_FILE_EXTENSIONS):
                        confidence += 25
                        reasons.append(f"File: {dbf['path']} ({dbf['size']})")

            # ORM evidence
            for orm in orms_found:
                orm_name = orm["name"].lower()
                orm_pip = orm.get("pip_deps", [])
                orm_npm = orm.get("npm_deps", [])
                if db["name"].lower() in ("sqlite", "postgresql", "mysql", "mariadb"):
                    if "sqlalchemy" in orm_name or "peewee" in orm_name or "pony" in orm_name:
                        if any(d in all_pip_names for d in orm_pip if isinstance(orm_pip, list)):
                            confidence += 15
                            reasons.append(f"ORM: {orm['name']}")
                elif db["name"].lower() == "mongodb":
                    if "mongoengine" in orm_name or "beanie" in orm_name or "mongoose" in orm_name:
                        confidence += 15
                        reasons.append(f"ORM: {orm['name']}")

            # Migration evidence
            for mig in migrations_found:
                if mig.get("orm_relation") and mig["orm_relation"].lower() in orm_names:
                    confidence += 10
                    reasons.append(f"Migration: {mig['name']}")

            if confidence > 0:
                results.append({
                    "name": db["name"],
                    "version": None,
                    "confidence": min(confidence, 99),
                    "reason": "; ".join(reasons),
                })

        return results

    def detect_orms(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        npm_deps = self._get_npm_deps()
        pip_deps = self._get_pip_deps()
        python_imports = scan.python_imports
        all_npm_names = set(npm_deps.keys())
        all_pip_names = set(pip_deps)

        for orm in ORM_PATTERNS:
            confidence = 0
            reasons: list[str] = []

            matched_pip = [d for d in orm["pip_deps"] if d in all_pip_names]
            matched_npm = [d for d in orm["npm_deps"] if d in all_npm_names]

            if matched_pip:
                confidence += 50
                reasons.append(f"pip: {matched_pip[0]}")
            if matched_npm:
                confidence += 50
                reasons.append(f"npm: {matched_npm[0]}")

            matched_imports = [i for i in orm["imports"] if i in python_imports]
            if matched_imports:
                confidence += 35
                reasons.append(f"Import: {matched_imports[0]}")

            if confidence > 0:
                results.append({
                    "name": orm["name"],
                    "version": None,
                    "confidence": min(confidence, 99),
                    "reason": "; ".join(reasons),
                    "migration": orm.get("migration"),
                })

        return results

    def detect_migrations(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        pip_deps = self._get_pip_deps()
        all_pip_names = set(pip_deps)
        all_dir_names = scan.all_dir_names
        root_files = self._get_root_file_names()
        all_file_names = {Path(f).name.lower() for f in scan.all_files}

        for mig in MIGRATION_PATTERNS:
            confidence = 0
            reasons: list[str] = []

            matched_dirs = [d for d in mig["dirs"] if d in all_dir_names]
            if matched_dirs:
                confidence += 40
                reasons.append(f"Dir: {matched_dirs[0]}")

            matched_files = [f for f in mig["files"] if f.lower() in root_files or f.lower() in all_file_names]
            if matched_files:
                confidence += 30
                reasons.append(f"File: {matched_files[0]}")

            pip_dep = mig.get("pip_dep")
            if pip_dep and pip_dep in all_pip_names:
                confidence += 25
                reasons.append(f"pip: {pip_dep}")

            npm_dep = mig.get("npm_dep")
            if npm_dep and npm_dep in self._get_npm_deps():
                confidence += 25
                reasons.append(f"npm: {npm_dep}")

            detect = mig.get("detect")
            if detect == "django" and "django" in scan.python_imports:
                if "migrations" in all_dir_names:
                    confidence += 50
                    reasons.append("Django migrations dir")
                else:
                    confidence += 20
                    reasons.append("Django project")

            if confidence > 0:
                results.append({
                    "name": mig["name"],
                    "version": None,
                    "confidence": min(confidence, 99),
                    "reason": "; ".join(reasons),
                    "orm_relation": None,
                })

        return results

    def detect_database_files(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        for f in scan.all_files:
            ext = Path(f).suffix.lower()
            if ext in DB_FILE_EXTENSIONS:
                fsize = scan.file_sizes.get(f, 0)
                size_str = f"{fsize / 1024:.1f} KB" if fsize > 0 else "unknown"
                results.append({
                    "path": f,
                    "size": size_str,
                })
        return results

    def detect_connection_details(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        for uri in scan.db_uris:
            masked = self._mask_uri(uri)
            details = {"raw_uri": masked, "host": None, "port": None, "database": None, "type": None}

            m = re.match(r"(\w+)(?:\+\w+)?://", uri)
            if m:
                details["type"] = m.group(1)

            host_m = re.search(r"@([^:/]+)", uri)
            if host_m:
                details["host"] = host_m.group(1)

            port_m = re.search(r":(\d+)/", uri)
            if port_m:
                details["port"] = port_m.group(1)

            db_m = re.search(r"/([^/?]+)(?:\?|$)", uri)
            if db_m:
                details["database"] = db_m.group(1)

            results.append(details)

        return results

    def detect_containers(self) -> list[dict]:
        scan = self._ensure_scan()
        results: list[dict] = []
        root_files = self._get_root_file_names()
        root_dirs = self._get_root_dir_names()

        for ct in CONTAINER_PATTERNS:
            matched_files = [f for f in ct["files"] if f in root_files]
            matched_dirs = [d for d in ct.get("dirs", []) if d in root_dirs]
            confidence = len(matched_files) * 40 + len(matched_dirs) * 30
            if confidence > 0:
                reasons: list[str] = []
                if matched_files:
                    reasons.append(f"Found {matched_files[0]}")
                if matched_dirs:
                    reasons.append(f"Directory: {matched_dirs[0]}")
                results.append({
                    "name": ct["name"],
                    "version": None,
                    "confidence": min(confidence, 99),
                    "reason": "; ".join(reasons),
                })
        return results

    def detect_ml_stack(self) -> list[str]:
        scan = self._ensure_scan()
        detected: set[str] = set()
        lower_readme = (scan.readme_content or "").lower()
        lower_config = ""
        for txt in [scan.config_py_content, scan.pyproject_toml_content]:
            if txt:
                lower_config += txt.lower() + "\n"

        all_text = lower_readme + lower_config
        for pat in ML_PATTERNS:
            if pat in all_text:
                detected.add(pat.capitalize())

        for dep_name in self._get_pip_deps():
            dep_lower = dep_name.lower()
            if dep_lower in ML_PATTERNS:
                detected.add(dep_lower.capitalize())
                break

        ipynb_files = [f for f in scan.all_files if f.endswith(".ipynb")]
        if ipynb_files:
            detected.add("Jupyter")

        return sorted(detected)
