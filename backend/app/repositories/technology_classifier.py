import re


CATEGORIES: dict[str, list[str]] = {
    "Application Framework": [
        "flask", "django", "fastapi", "express", "react", "vue", "angular",
        "next.js", "nextjs", "nuxt", "sveltekit", "svelte", "gatsby", "remix",
        "nestjs", "nest", "spring boot", "spring-boot", "spring", "laravel",
        "asp.net", "aspnet", "koa", "fastify", "hapi", "sinatra", "rails",
        "phoenix", "actix", "rocket", "axum", "tornado", "aiohttp", "sanic",
        "quart", "bottle", "pyramid", "web2py", "cubicweb",
        "ember", "backbone", "aurelia", "preact", "solid", "qwik",
    ],
    "ORM": [
        "sqlalchemy", "flask-sqlalchemy", "flask_sqlalchemy", "django orm",
        "prisma", "typeorm", "mongoose", "sequelize", "hibernate",
        "peewee", "pony orm", "tortoise-orm", "tortoise_orm", "beanie",
        "mongoengine", "diesel", "sqlx", "gorm", "ent", "doctrine",
        "eloquent", "active record", "entity framework", "ef core",
        "dapper", "nhibernate", "realm", "objectbox",
    ],
    "Deep Learning": [
        "tensorflow", "pytorch", "torch", "keras", "onnx", "transformers",
        "hugging face", "huggingface", "jax", "flax", "haiku",
        "caffe", "caffe2", "chainer", "mxnet", "paddlepaddle", "paddle",
        "deeplearning4j", "theano", "cntk", "tvm",
    ],
    "Machine Learning": [
        "scikit-learn", "sklearn", "xgboost", "lightgbm", "catboost",
        "mlflow", "wandb", "weights & biases", "ray", "darts",
        "prophet", "statsmodels", "imbalanced-learn", "imblearn",
        "h2o", "spark ml", "mllib", "weka", "orange",
    ],
    "Data Science": [
        "pandas", "numpy", "polars", "dask", "modin", "vaex",
        "cuDF", "pyspark", "spark", "databricks", "dataframe",
        "pandas-profiling", "ydata-profiling", "sweetviz", "autoviz",
    ],
    "Visualization": [
        "matplotlib", "seaborn", "plotly", "altair", "bokeh",
        "ggplot", "pyplot", "d3.js", "d3", "chart.js", "chartjs",
        "highcharts", "echarts", "vega", "vega-lite", "vispy",
        "mayavi", "plotnine", "holoviews", "panel", "streamlit",
        "gradio", "dash", "bokeh", "pygal",
    ],
    "API": [
        "flask-restful", "flask_restful", "flask-restx", "flask_restx",
        "django-rest-framework", "djangorestframework", "rest_framework",
        "graphql", "graphene", "strawberry", "ariadne", "tartiflette",
        "grpc", "grpcio", "protobuf", "thrift", "avro",
        "openapi", "swagger", "drf-yasg", "spectacular",
    ],
    "Database": [
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis",
        "mariadb", "mssql", "oracle", "dynamodb", "firebase",
        "supabase", "elasticsearch", "cassandra", "neo4j",
        "couchdb", "couchbase", "influxdb", "timescaledb",
        "cockroachdb", "clickhouse", "druid", "pinot",
        "singlestore", "memcached", "hbase", "couchbase",
    ],
    "Testing": [
        "pytest", "unittest", "jest", "mocha", "chai", "vitest",
        "cypress", "playwright", "selenium", "puppeteer",
        "jasmine", "karma", "ava", "tape", "tap",
        "rspec", "minitest", "phpunit", "junit", "testng",
        "mock", "mockito", "sinon", "nock", "msw",
        "coverage", "codecov", "istanbul", "nyc",
    ],
    "Authentication": [
        "jwt", "pyjwt", "python-jose", "jose", "oauth", "oauthlib",
        "flask-login", "flask_login", "flask-httpauth", "flask_httpauth",
        "flask-jwt", "flask_jwt", "flask-jwt-extended", "flask_jwt_extended",
        "django.contrib.auth", "django-allauth", "django-rest-auth",
        "passlib", "bcrypt", "argon2", "cryptography",
        "authlib", "python-social-auth", "social-auth-app-django",
        "devise", "cancancan", "pundit", "casl",
        "keycloak", "auth0", "firebase-auth",
    ],
    "Task Queue": [
        "celery", "redis-queue", "rq", "dramatiq", "huey",
        "taskiq", "arq", "sanic", "rabbitmq", "pika",
        "kafka", "confluent-kafka", "aiokafka",
        "bull", "bullmq", "bee-queue", "kue",
        "sidekiq", "resque", "delayed_job",
    ],
    "Package Manager": [
        "pip", "poetry", "npm", "yarn", "pnpm", "pipenv",
        "conda", "mamba", "cargo", "composer", "bundler",
        "gem", "nuget", "chocolatey", "homebrew", "apt",
        "go modules", "go-modules", "gradle", "maven",
    ],
}


CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Application Framework", [
        "app", "web", "mvc", "route", "template", "controller",
        "middleware", "blueprint", "view", "model",
    ]),
    ("ORM", [
        "orm", "model", "entity", "migration", "schema", "database model",
        "object-relational", "active record", "data mapper",
    ]),
    ("Database", [
        "database", "db", "sql", "nosql", "datastore", "data store",
        "connector", "driver", "client",
    ]),
    ("API", [
        "rest", "api", "graphql", "grpc", "endpoint", "web service",
    ]),
    ("Testing", [
        "test", "spec", "assert", "mock", "expect", "should",
    ]),
]


TECHNOLOGY_ALIASES: dict[str, str] = {
    "torch": "PyTorch",
    "sklearn": "Scikit-learn",
    "transformers": "Hugging Face Transformers",
    "flask_sqlalchemy": "Flask-SQLAlchemy",
    "flask-sqlalchemy": "Flask-SQLAlchemy",
    "flask_restful": "Flask-RESTful",
    "flask-restful": "Flask-RESTful",
    "flask_restx": "Flask-RESTX",
    "flask-restx": "Flask-RESTX",
    "flask_login": "Flask-Login",
    "flask-login": "Flask-Login",
    "flask_httpauth": "Flask-HTTPAuth",
    "flask-httpauth": "Flask-HTTPAuth",
    "flask_jwt": "Flask-JWT",
    "flask-jwt": "Flask-JWT",
    "rest_framework": "Django REST Framework",
    "djangorestframework": "Django REST Framework",
    "django-rest-framework": "Django REST Framework",
    "django.contrib.auth": "Django Auth",
    "scikit-learn": "Scikit-learn",
    "plotly": "Plotly",
    "pyspark": "PySpark",
    "elasticsearch": "Elasticsearch",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "sveltekit": "SvelteKit",
    "nestjs": "NestJS",
    "spring-boot": "Spring Boot",
    "react-native": "React Native",
    "d3.js": "D3.js",
    "chart.js": "Chart.js",
}


DETECTION_SOURCE_PATTERNS: list[tuple[str, str]] = [
    (r"requirement", "requirements.txt"),
    (r"pip dep", "requirements.txt"),
    (r"python dep", "requirements.txt"),
    (r"python dependency", "requirements.txt"),
    (r"python import", "Import statements"),
    (r"npm dep", "package.json"),
    (r"dependency:", "package.json"),
    (r"(?:npm )?dependenc", "package.json"),
    (r"import:", "Import statements"),
    (r"config", "Configuration files"),
    (r"manage\.py", "Configuration files"),
    (r"settings\.py", "Configuration files"),
    (r"dockerfile", "Dockerfile"),
    (r"composer", "composer.json"),
    (r"pyproject\.toml", "Configuration files"),
    (r"found in", "Configuration files"),
    (r"file ext", "Project structure"),
    (r"source file", "Project structure"),
    (r"folder", "Project structure"),
    (r"directory", "Project structure"),
    (r"pom\.xml", "Configuration files"),
    (r"environment", "Environment files"),
    (r".env", "Environment files"),
    (r"database", "Configuration files"),
    (r"uri", "Configuration files"),
    (r"connection", "Configuration files"),
    (r"migration", "Project structure"),
    (r"alembic", "Project structure"),
]


class TechnologyClassifier:
    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.lower().replace("-", "").replace("_", "").replace(".", "").replace(" ", "")

    @staticmethod
    def _get_canonical_name(name: str) -> str:
        return TECHNOLOGY_ALIASES.get(name.lower(), name)

    @staticmethod
    def _detect_source(reason: str) -> str:
        for pattern, source in DETECTION_SOURCE_PATTERNS:
            if re.search(pattern, reason, re.IGNORECASE):
                return source
        if reason and reason.strip():
            return reason.split(":")[0].strip() if ":" in reason else reason[:60]
        return "Unknown"

    @classmethod
    def classify_technology(cls, name: str) -> str:
        normalized = cls._normalize_name(name)

        best_category: str | None = None
        best_length = 0

        for category, techs in CATEGORIES.items():
            for tech in techs:
                tech_normalized = cls._normalize_name(tech)

                exact_match = normalized == tech_normalized

                contains_match = tech_normalized in normalized and len(tech_normalized) > 3

                if exact_match or contains_match:
                    if not best_category or len(tech_normalized) > best_length:
                        best_category = category
                        best_length = len(tech_normalized)

        if best_category:
            return best_category

        for category, keywords in CATEGORY_KEYWORDS:
            for kw in keywords:
                if kw.lower() in normalized:
                    return category

        return "Other"

    @classmethod
    def _compute_source_confidence(cls, source: str) -> int:
        if "requirements.txt" in source:
            return 100
        if "package.json" in source:
            return 100
        if "Import" in source:
            return 90
        if "Dockerfile" in source:
            return 85
        if "Configuration" in source:
            return 80
        if "pyproject.toml" in source or "Pipfile" in source or "setup.py" in source or "poetry" in source:
            return 95
        if "composer.json" in source or "pom.xml" in source or "build.gradle" in source:
            return 80
        if "Environment" in source:
            return 75
        if "Project structure" in source or "folder" in source.lower() or "directory" in source.lower():
            return 60
        if "file" in source.lower():
            return 40
        return 50

    @classmethod
    def classify_many(
        cls,
        technologies: list[dict],
        database_technologies: list[dict] | None = None,
        orm_technologies: list[dict] | None = None,
        pm_technologies: list[dict] | None = None,
    ) -> dict[str, list[dict]]:
        result: dict[str, list[dict]] = {
            "Application Framework": [],
            "ORM": [],
            "Database": [],
            "Deep Learning": [],
            "Machine Learning": [],
            "Data Science": [],
            "Visualization": [],
            "API": [],
            "Testing": [],
            "Authentication": [],
            "Task Queue": [],
            "Package Manager": [],
            "Other": [],
        }

        seen_names: set[str] = set()

        def add_tech(tech: dict, category: str | None = None) -> None:
            name = tech.get("name", "")
            canonical = cls._get_canonical_name(name)

            normalized = cls._normalize_name(canonical)
            if normalized in seen_names:
                return
            seen_names.add(normalized)

            source = cls._detect_source(tech.get("reason", ""))
            confidence = tech.get("confidence", 0)
            source_confidence = cls._compute_source_confidence(source)
            final_confidence = max(confidence, source_confidence)

            if category is None:
                category = cls.classify_technology(name)

            entry = {
                "name": canonical,
                "version": tech.get("version"),
                "confidence": min(final_confidence, 99),
                "reason": tech.get("reason", ""),
                "category": category,
                "detection_source": source,
            }

            result.setdefault(category, []).append(entry)

        for tech in technologies:
            name = tech.get("name", "")
            category = cls.classify_technology(name)
            if category == "API" and cls.classify_technology(name) == "Application Framework":
                pass
            add_tech(tech, category)

        if database_technologies:
            for db in database_technologies:
                add_tech(db, "Database")

        if orm_technologies:
            for orm in orm_technologies:
                add_tech(orm, "ORM")

        if pm_technologies:
            for pm in pm_technologies:
                add_tech(pm, "Package Manager")

        for cat in result:
            result[cat].sort(key=lambda t: -t["confidence"])

        return result

    @classmethod
    def build_response(
        cls,
        framework_techs: list[dict],
        database_techs: list[dict] | None = None,
        orm_techs: list[dict] | None = None,
        pm_techs: list[dict] | None = None,
    ) -> dict[str, list[dict]]:
        categorized = cls.classify_many(
            framework_techs,
            database_technologies=database_techs,
            orm_technologies=orm_techs,
            pm_technologies=pm_techs,
        )

        ordered_categories = [
            "Application Framework",
            "ORM",
            "Database",
            "Deep Learning",
            "Machine Learning",
            "Data Science",
            "Visualization",
            "API",
            "Testing",
            "Authentication",
            "Task Queue",
            "Package Manager",
            "Other",
        ]

        result: dict[str, list[dict]] = {}
        for cat in ordered_categories:
            if categorized.get(cat):
                result[cat] = categorized[cat]
        return result
