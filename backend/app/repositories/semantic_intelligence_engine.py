import ast
import os
import re
from collections import defaultdict
from pathlib import Path

from app.repositories.source_code_intelligence_engine import (
    IGNORED_DIRS,
    IGNORED_FILES,
    EXTENSION_LANGUAGE_MAP,
    SUPPORTED_EXTENSIONS,
)

COMPONENT_PATTERNS: dict[str, list[tuple[str, str, str, float]]] = {
    "Python": [
        (r"@app\.(route|get|post|put|delete|patch)", "api", "API Route", 1.0),
        (r"@router\.(route|get|post|put|delete|patch)", "api", "API Route", 1.0),
        (r"class\s+\w+Controller", "controller", "Controller", 1.0),
        (r"class\s+\w+Service", "service", "Service", 1.0),
        (r"class\s+\w+Repository", "repository", "Repository", 1.0),
        (r"class\s+\w+Model", "model", "Model", 1.0),
        (r"class\s+\w+Schema", "model", "Schema", 0.9),
        (r"class\s+\w+DTO", "model", "DTO", 0.9),
        (r"class\s+\w+Middleware", "middleware", "Middleware", 1.0),
        (r"class\s+\w+Config", "configuration", "Configuration", 0.9),
        (r"class\s+\w+Settings", "configuration", "Settings", 0.9),
        (r"class\s+\w+Factory", "utility", "Factory", 0.8),
        (r"class\s+\w+Builder", "utility", "Builder", 0.8),
        (r"class\s+\w+Manager", "service", "Manager", 0.7),
        (r"class\s+\w+Handler", "controller", "Handler", 0.7),
        (r"class\s+\w+Helper", "utility", "Helper", 0.9),
        (r"class\s+\w+Util", "utility", "Utility", 0.9),
        (r"class\s+\w+Validator", "utility", "Validator", 0.9),
        (r"class\s+\w+Converter", "utility", "Converter", 0.8),
        (r"class\s+\w+Serializer", "utility", "Serializer", 0.8),
        (r"class\s+\w+Parser", "utility", "Parser", 0.8),
        (r"class\s+\w+Loader", "utility", "Loader", 0.7),
        (r"class\s+\w+Exporter", "utility", "Exporter", 0.8),
        (r"class\s+\w+Importer", "utility", "Importer", 0.8),
        (r"class\s+\w+Generator", "utility", "Generator", 0.7),
        (r"class\s+\w+Transformer", "utility", "Transformer", 0.8),
        (r"class\s+\w+Adapter", "utility", "Adapter", 0.9),
        (r"class\s+\w+Proxy", "utility", "Proxy", 0.8),
        (r"class\s+\w+Decorator", "utility", "Decorator", 0.8),
        (r"class\s+\w+Provider", "service", "Provider", 0.7),
        (r"class\s+\w+Registry", "service", "Registry", 0.7),
        (r"class\s+\w+Engine", "service", "Engine", 0.7),
        (r"class\s+\w+Client", "service", "Client", 0.7),
        (r"class\s+\w+Base\w+", "model", "Base", 0.5),
        (r"class\s+\w+Abstract\w+", "model", "Abstract", 0.6),
        (r"class\s+\w+Exception", "utility", "Exception", 0.8),
        (r"class\s+\w+Error", "utility", "Error", 0.8),
        (r"from\s+flask\s+import", "api", "Flask Endpoint", 0.9),
        (r"from\s+fastapi\s+import", "api", "FastAPI Endpoint", 0.9),
        (r"from\s+django", "api", "Django View", 0.8),
        (r"import\s+flask", "api", "Flask App", 0.8),
        (r"import\s+fastapi", "api", "FastAPI App", 0.8),
        (r"from\s+sqlalchemy\s+import", "data", "Database Model", 0.7),
        (r"from\s+django\.db\s+import", "data", "Database Model", 0.7),
        (r"from\s+mongodb|pymongo", "data", "Database Access", 0.7),
        (r"from\s+redis", "data", "Cache Layer", 0.7),
        (r"from\s+kafka|celery|rabbitmq", "data", "Message Queue", 0.7),
        (r"from\s+tensorflow|torch|sklearn", "ml", "Machine Learning", 0.9),
        (r"from\s+pandas|numpy|scipy", "ml", "Data Processing", 0.8),
        (r"import\s+pandas|numpy|scipy", "ml", "Data Processing", 0.7),
        (r"from\s+pydantic\s+import", "model", "Pydantic Model", 0.8),
        (r"class\s+\w+\(.*BaseModel", "model", "Pydantic Model", 0.9),
        (r"class\s+\w+\(.*Model\)", "model", "ORM Model", 0.8),
        (r"class\s+\w+\(.*Serializer\)", "model", "Serializer", 0.8),
        (r"class\s+\w+\(.*Form\)", "model", "Form", 0.7),
        (r"from\s+pytest|unittest", "test", "Test Suite", 0.9),
        (r"import\s+pytest|unittest", "test", "Test Suite", 0.8),
        (r"def\s+test_", "test", "Test Function", 0.9),
        (r"class\s+Test\w+", "test", "Test Class", 0.9),
        (r"@pytest\.", "test", "Test", 0.9),
        (r"from\s+conftest", "test", "Test Configuration", 0.8),
        (r"@login_required|@require_auth", "auth", "Authentication", 0.9),
        (r"from\s+jwt|oauth|passlib", "auth", "Authentication", 0.8),
        (r"import\s+jwt|oauth|passlib", "auth", "Authentication", 0.7),
        (r"from\s+logging", "utility", "Logging", 0.8),
        (r"import\s+logging", "utility", "Logging", 0.7),
        (r"from\s+cachetools|lru_cache", "utility", "Caching", 0.8),
        (r"os\.environ|os\.getenv", "configuration", "Environment Config", 0.7),
        (r"dataclass", "model", "Data Class", 0.7),
        (r"@property|@staticmethod|@classmethod", "utility", "Utility Method", 0.5),
        (r"def\s+main\s*\(", "entry_point", "Entry Point", 0.9),
        (r'if\s+__name__\s*==\s*["\']__main__["\']', "entry_point", "Entry Point", 1.0),
        (r"app\.run\(|uvicorn\.run\(", "entry_point", "Application Entry", 1.0),
    ],
    "JavaScript": [
        (r"class\s+\w+Controller", "controller", "Controller", 1.0),
        (r"class\s+\w+Service", "service", "Service", 1.0),
        (r"class\s+\w+Repository", "repository", "Repository", 1.0),
        (r"class\s+\w+Model", "model", "Model", 1.0),
        (r"class\s+\w+Middleware", "middleware", "Middleware", 1.0),
        (r"class\s+\w+Config", "configuration", "Configuration", 0.9),
        (r"class\s+\w+Helper", "utility", "Helper", 0.9),
        (r"class\s+\w+Util", "utility", "Utility", 0.9),
        (r"class\s+\w+Validator", "utility", "Validator", 0.9),
        (r"class\s+\w+Adapter", "utility", "Adapter", 0.9),
        (r"class\s+\w+Provider", "service", "Provider", 0.7),
        (r"class\s+\w+Engine", "service", "Engine", 0.7),
        (r"class\s+\w+Client", "service", "Client", 0.7),
        (r"class\s+\w+Error", "utility", "Error", 0.8),
        (r"class\s+\w+Exception", "utility", "Exception", 0.8),
        (r"class\s+\w+Factory", "utility", "Factory", 0.8),
        (r"class\s+\w+Manager", "service", "Manager", 0.7),
        (r"class\s+\w+Handler", "controller", "Handler", 0.7),
        (r"class\s+\w+Pipe", "middleware", "Pipe", 0.7),
        (r"class\s+\w+Guard", "auth", "Guard", 0.9),
        (r"@Controller|@RestController", "controller", "Controller", 1.0),
        (r"@Injectable", "service", "Injectable", 0.9),
        (r"@Module\(", "configuration", "Module", 0.9),
        (r"@Get\(|@Post\(|@Put\(|@Delete\(|@Patch\(", "api", "API Route", 1.0),
        (r"express\(\)", "api", "Express App", 0.9),
        (r"Router\(\)", "api", "Router", 0.9),
        (r"app\.get\(|app\.post\(|app\.put\(|app\.delete\(|app\.patch\(", "api", "API Route", 1.0),
        (r"router\.get\(|router\.post\(|router\.put\(|router\.delete", "api", "API Route", 1.0),
        (r"from\s+['\"]@nestjs|require\(['\"]@nestjs", "api", "NestJS Module", 0.8),
        (r"mongoose|sequelize|typeorm", "data", "Database Model", 0.7),
        (r"prisma", "data", "Database Access", 0.7),
        (r"jest|mocha|chai|vitest", "test", "Test Suite", 0.9),
        (r"describe\(|it\(|test\(", "test", "Test", 0.9),
        (r"export\s+default", "utility", "Module Export", 0.4),
        (r"app\.listen\(|server\.listen\(", "entry_point", "Entry Point", 1.0),
        (r"process\.env", "configuration", "Environment Config", 0.7),
    ],
    "TypeScript": [
        (r"class\s+\w+Controller", "controller", "Controller", 1.0),
        (r"class\s+\w+Service", "service", "Service", 1.0),
        (r"class\s+\w+Repository", "repository", "Repository", 1.0),
        (r"class\s+\w+Model", "model", "Model", 1.0),
        (r"class\s+\w+Middleware", "middleware", "Middleware", 1.0),
        (r"class\s+\w+Config", "configuration", "Configuration", 0.9),
        (r"class\s+\w+Helper", "utility", "Helper", 0.9),
        (r"class\s+\w+Util", "utility", "Utility", 0.9),
        (r"class\s+\w+Validator", "utility", "Validator", 0.9),
        (r"class\s+\w+Adapter", "utility", "Adapter", 0.9),
        (r"class\s+\w+Provider", "service", "Provider", 0.7),
        (r"class\s+\w+Engine", "service", "Engine", 0.7),
        (r"class\s+\w+Client", "service", "Client", 0.7),
        (r"class\s+\w+Error", "utility", "Error", 0.8),
        (r"class\s+\w+Exception", "utility", "Exception", 0.8),
        (r"class\s+\w+Factory", "utility", "Factory", 0.8),
        (r"class\s+\w+Manager", "service", "Manager", 0.7),
        (r"class\s+\w+Handler", "controller", "Handler", 0.7),
        (r"class\s+\w+Pipe", "middleware", "Pipe", 0.7),
        (r"class\s+\w+Guard", "auth", "Guard", 0.9),
        (r"interface\s+\w+", "model", "Interface", 0.6),
        (r"type\s+\w+\s*=", "model", "Type Alias", 0.5),
        (r"@Controller|@RestController", "controller", "Controller", 1.0),
        (r"@Injectable", "service", "Injectable", 0.9),
        (r"@Module\(", "configuration", "Module", 0.9),
        (r"@Get\(|@Post\(|@Put\(|@Delete\(|@Patch\(", "api", "API Route", 1.0),
        (r"express\(\)", "api", "Express App", 0.9),
        (r"Router\(\)", "api", "Router", 0.9),
        (r"app\.get\(|app\.post\(|app\.put\(|app\.delete\(|app\.patch\(", "api", "API Route", 1.0),
        (r"router\.get\(|router\.post\(|router\.put\(|router\.delete", "api", "API Route", 1.0),
        (r"mongoose|sequelize|typeorm|prisma", "data", "Database Model", 0.7),
        (r"jest|mocha|chai|vitest", "test", "Test Suite", 0.9),
        (r"describe\(|it\(|test\(", "test", "Test", 0.9),
        (r"app\.listen\(|server\.listen\(", "entry_point", "Entry Point", 1.0),
        (r"process\.env", "configuration", "Environment Config", 0.7),
        (r"export\s+(default|interface|type|class|function|const)", "utility", "Export", 0.4),
    ],
    "Java": [
        (r"class\s+\w+Controller", "controller", "Controller", 1.0),
        (r"class\s+\w+Service", "service", "Service", 1.0),
        (r"class\s+\w+Repository", "repository", "Repository", 1.0),
        (r"class\s+\w+Model", "model", "Model", 1.0),
        (r"class\s+\w+Entity", "model", "Entity", 1.0),
        (r"class\s+\w+DTO", "model", "DTO", 0.9),
        (r"class\s+\w+Config", "configuration", "Configuration", 0.9),
        (r"class\s+\w+Middleware", "middleware", "Middleware", 1.0),
        (r"class\s+\w+Helper", "utility", "Helper", 0.9),
        (r"class\s+\w+Util", "utility", "Utility", 0.9),
        (r"class\s+\w+Validator", "utility", "Validator", 0.9),
        (r"class\s+\w+Factory", "utility", "Factory", 0.8),
        (r"class\s+\w+Manager", "service", "Manager", 0.7),
        (r"class\s+\w+Handler", "controller", "Handler", 0.7),
        (r"class\s+\w+Adapter", "utility", "Adapter", 0.9),
        (r"class\s+\w+Provider", "service", "Provider", 0.7),
        (r"class\s+\w+Engine", "service", "Engine", 0.7),
        (r"class\s+\w+Client", "service", "Client", 0.7),
        (r"@Controller|@RestController", "controller", "Controller", 1.0),
        (r"@Service", "service", "Service", 1.0),
        (r"@Repository", "repository", "Repository", 1.0),
        (r"@Entity|@Table", "model", "Entity", 1.0),
        (r"@Configuration|@SpringBootApplication", "configuration", "Configuration", 1.0),
        (r"@Component", "service", "Component", 0.7),
        (r"@GetMapping|@PostMapping|@PutMapping|@DeleteMapping|@PatchMapping", "api", "API Route", 1.0),
        (r"@RequestMapping", "api", "API Route", 1.0),
        (r"@Autowired", "service", "Dependency Injection", 0.6),
        (r"implements\s+\w+Repository", "repository", "Repository Impl", 0.8),
        (r"extends\s+\w+Repository", "repository", "Repository Ext", 0.8),
        (r"extends\s+\w+Service", "service", "Service Base", 0.7),
        (r"@Test|@Before|@After", "test", "Test", 0.9),
        (r"import\s+org\.junit|import\s+org\.mockito|import\s+org\.testng", "test", "Test Suite", 0.9),
        (r"import\s+org\.springframework", "api", "Spring Framework", 0.6),
        (r"import\s+jakarta\.persistence", "data", "JPA Entity", 0.7),
        (r"public\s+static\s+void\s+main", "entry_point", "Entry Point", 1.0),
        (r"SpringApplication\.run", "entry_point", "Spring Boot Entry", 1.0),
    ],
}

ROLE_PURPOSE_MAP: dict[str, tuple[str, str, str]] = {
    "controller": ("Handles HTTP requests and routes them to appropriate services",
                   "Request Handler",
                   "Processes incoming requests and returns responses"),
    "service": ("Contains business logic and coordinates between controllers and repositories",
                "Business Logic",
                "Implements core business operations and domain logic"),
    "repository": ("Manages data access and persistence operations",
                   "Data Access",
                   "Provides CRUD operations and database interactions"),
    "model": ("Defines data structures and business entities",
              "Data Definition",
              "Represents domain objects and their relationships"),
    "api": ("Defines API endpoints and request handling",
            "API Layer",
            "Exposes functionality through RESTful or other API interfaces"),
    "middleware": ("Intercepts and processes requests or responses",
                  "Request Pipeline",
                  "Handles cross-cutting concerns like logging, auth, error handling"),
    "configuration": ("Manages application settings and environment variables",
                      "Configuration",
                      "Centralizes application configuration and setup"),
    "auth": ("Handles authentication and authorization",
             "Security",
             "Manages user identity, access control, and permissions"),
    "data": ("Manages data storage, caching, and message queuing",
             "Data Management",
             "Handles data persistence, caching, and communication"),
    "ml": ("Performs machine learning and data processing",
           "Data Science",
           "Implements ML models, data pipelines, and analytics"),
    "test": ("Contains test cases and test utilities",
             "Testing",
             "Verifies code correctness through automated tests"),
    "utility": ("Provides reusable helper functions and utilities",
                "Utility",
                "Offers common functionality used across the application"),
    "entry_point": ("Serves as the application entry point",
                    "Entry Point",
                    "Initializes and starts the application"),
}

def _sanitize(text: str) -> str:
    return text.replace('"', "'").replace("\\", "/")


BUSINESS_FLOW_PATTERNS: list[tuple[str, str, list[str], list[str]]] = [
    ("User Login", "authentication", ["login", "auth", "signin", "authenticate"], ["token", "session", "cookie"]),
    ("User Registration", "authentication", ["register", "signup", "sign_up", "create_account"], ["email", "password", "verification"]),
    ("Password Reset", "authentication", ["password_reset", "forgot_password", "reset_password"], ["token", "email", "recovery"]),
    ("Data Validation", "validation", ["validate", "validator", "sanitize", "check"], ["error", "valid", "invalid"]),
    ("Report Generation", "reporting", ["report", "generate_report", "export", "summary"], ["pdf", "csv", "excel", "data"]),
    ("Prediction Flow", "prediction", ["predict", "forecast", "estimate", "infer"], ["model", "result", "output"]),
    ("Data Pipeline", "pipeline", ["pipeline", "process", "transform", "etl", "extract"], ["data", "load", "transform"]),
    ("Notification Flow", "notification", ["notify", "notification", "alert", "send_message"], ["email", "push", "sms"]),
    ("Payment Processing", "payment", ["payment", "checkout", "invoice", "billing", "charge"], ["amount", "transaction", "receipt"]),
    ("Search Flow", "search", ["search", "find", "query", "lookup", "retrieve"], ["result", "index", "filter"]),
    ("File Upload", "upload", ["upload", "import", "ingest", "receive_file"], ["file", "storage", "attachment"]),
    ("File Export", "export", ["export", "download", "generate_file", "write_file"], ["format", "output", "stream"]),
    ("Cache Management", "caching", ["cache", "clear_cache", "invalidate", "warmup"], ["redis", "memory", "ttl"]),
    ("Background Job", "background", ["job", "task", "worker", "schedule", "cron"], ["queue", "celery", "background"]),
    ("API Request", "api", ["endpoint", "route", "api", "request_handler", "view"], ["response", "status", "serialize"]),
    ("Database Migration", "migration", ["migrate", "migration", "schema_change", "alter"], ["database", "version", "upgrade"]),
    ("Authentication Flow", "authentication", ["login", "register", "auth", "oauth", "sso", "jwt"], ["token", "session", "password"]),
    ("Forecast Pipeline", "forecasting", ["forecast", "predict", "projection", "estimate"], ["model", "data", "result", "metric"]),
]


class SemanticCodeIntelligenceEngine:

    def analyze(self, workspace_path: Path, call_graph_data: dict | None = None,
                execution_flows: list[dict] | None = None) -> dict:
        components: list[dict] = []
        relationships: list[dict] = []
        symbols: list[dict] = []
        issues: list[dict] = []
        language_breakdown: dict[str, int] = defaultdict(int)
        type_breakdown: dict[str, int] = defaultdict(int)
        component_type_counts: dict[str, int] = defaultdict(int)
        file_component_map: dict[str, list[dict]] = defaultdict(list)
        component_map: dict[str, dict] = {}
        files_analyzed: set[str] = set()
        module_map: dict[str, str] = {}
        file_language_map: dict[str, str] = {}
        all_imports: dict[str, list[str]] = defaultdict(list)
        all_exports: dict[str, list[str]] = defaultdict(list)

        if call_graph_data and call_graph_data.get("nodes"):
            self._analyze_from_call_graph(components, relationships, symbols,
                language_breakdown, type_breakdown, component_type_counts,
                file_component_map, component_map, files_analyzed, module_map,
                file_language_map, all_imports, all_exports, call_graph_data,
                workspace_path)
        else:
            for root, dirs, files in os.walk(workspace_path):
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
                for f in files:
                    if f.lower() in IGNORED_FILES:
                        continue
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in SUPPORTED_EXTENSIONS:
                        continue
                    file_path = os.path.join(root, f)
                    language = EXTENSION_LANGUAGE_MAP[ext]
                    rel_path = os.path.relpath(file_path, workspace_path).replace("\\", "/")
                    module = rel_path.replace("/", ".").rsplit(".", 1)[0] if "." in rel_path else rel_path
                    module_map[rel_path] = module
                    file_language_map[rel_path] = language
                    language_breakdown[language] += 1
                    files_analyzed.add(rel_path)

                    try:
                        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                            content = fh.read()
                    except (OSError, UnicodeDecodeError):
                        continue

                    lines = content.split("\n")

                    file_component = self._analyze_file_semantics(
                        rel_path, module, language, f, content, lines
                    )
                    if file_component:
                        components.append(file_component)
                        cid = file_component["id"]
                        component_map[cid] = file_component
                        file_component_map[rel_path].append(file_component)
                        t = file_component.get("type", "unknown")
                        type_breakdown[t] += 1
                        st = file_component.get("sub_type", t)
                        component_type_counts[st] += 1

                    component_data = self._extract_components_from_source(
                        rel_path, module, language, f, content, lines
                    )
                    for comp in component_data:
                        components.append(comp)
                        cid = comp["id"]
                        component_map[cid] = comp
                        file_component_map[rel_path].append(comp)
                        t = comp.get("type", "unknown")
                        type_breakdown[t] += 1
                        st = comp.get("sub_type", t)
                        component_type_counts[st] += 1

                    file_imports, file_exported = self._extract_imports_exports(
                        rel_path, module, language, content, lines
                    )
                    all_imports[rel_path] = file_imports
                    all_exports[rel_path] = file_exported

                    file_symbols = self._extract_symbols(
                        rel_path, module, language, content, lines
                    )
                    symbols.extend(file_symbols)

        self._resolve_symbols_across_files(symbols, module_map)
        self._build_relationships(components, relationships, all_imports, all_exports, module_map, file_component_map)
        business_flows = self._detect_business_flows(components, relationships, all_imports, file_language_map, file_component_map)
        similarities = self._detect_similarities(components, component_map)
        component_issues = self._generate_component_issues(components, similarities)
        issues.extend(component_issues)
        self._enhance_purposes(components, all_imports, file_component_map)
        ai_insights = self._generate_ai_insights(
            components, relationships, business_flows, issues, similarities, type_breakdown
        )

        understanding_score = self._calculate_understanding_score(
            components, relationships, business_flows, issues,
            type_breakdown, language_breakdown, execution_flows or [],
        )
        knowledge_graph = self._build_knowledge_graph(components, relationships, understanding_score)
        business_components = self._detect_business_components(
            components, all_imports, file_component_map, call_graph_data
        )

        file_set = {c["file_path"] for c in components if c.get("file_path")}
        class_set = {c["id"] for c in components if c.get("type") in ("model", "class")}
        func_set = {c["id"] for c in components if c.get("type") in ("function", "method")}
        verified_flows = [f for f in business_flows if f.get("verified")]

        stats = {
            "total_components": len(components),
            "total_files": len(file_set),
            "total_classes": len(class_set),
            "total_functions": len(func_set),
            "type_breakdown": dict(type_breakdown),
            "language_breakdown": dict(language_breakdown),
            "total_relationships": len(relationships),
            "total_business_flows": len(business_flows),
            "total_verified_flows": len(verified_flows),
            "total_symbols": len(symbols),
            "total_issues": len(issues),
            "total_similarities": len(similarities),
            "component_type_counts": dict(component_type_counts),
        }

        return {
            "components": components,
            "relationships": relationships,
            "symbols": symbols,
            "business_flows": business_flows,
            "issues": issues,
            "similarities": similarities,
            "stats": stats,
            "understanding_score": understanding_score,
            "knowledge_graph": knowledge_graph,
            "business_components": business_components,
            "ai_insights": ai_insights,
        }

    def _analyze_file_semantics(self, rel_path: str, module: str, language: str,
                                 file_name: str, content: str, lines: list[str]) -> dict | None:
        patterns = COMPONENT_PATTERNS.get(language, [])
        best_type = "file"
        best_sub_type = "Module"
        best_confidence = 0.0
        best_reason = ""

        for pattern, ctype, subtype, confidence in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                if confidence > best_confidence:
                    best_type = ctype
                    best_sub_type = subtype
                    best_confidence = confidence
                    best_reason = f"Matched pattern: {pattern}"

        if best_type == "file":
            best_sub_type = self._guess_module_type(file_name, rel_path, content, lines)

        purpose, responsibility, role, business_context, summary = self._generate_semantic_description(
            rel_path, file_name, best_type, best_sub_type, content, lines
        )

        is_test = best_type == "test" or (re.search(r"(test_|_test|spec|\.test\.|\.spec\.)", rel_path, re.IGNORECASE) is not None)
        is_entry = best_type == "entry_point"
        is_abstract = bool(re.search(r"abstract\s+class|\bABC\b|@abstractmethod", content))
        is_deprecated = bool(re.search(r"@deprecated|\bdeprecated\b|#\s*TODO|#\s*HACK|#\s*FIXME", content, re.IGNORECASE))
        complexity = self._estimate_file_complexity(content, lines)

        comp_id = f"{module}.{file_name.rsplit('.', 1)[0]}"

        return {
            "id": comp_id,
            "name": file_name.rsplit(".", 1)[0],
            "type": best_type,
            "sub_type": best_sub_type,
            "file_path": rel_path,
            "module": module,
            "language": language,
            "line_number": 1,
            "purpose": purpose,
            "responsibility": responsibility,
            "role": role,
            "business_context": business_context,
            "summary": summary,
            "classification_reason": _sanitize(best_reason),
            "confidence": best_confidence,
            "complexity": complexity,
            "is_entry_point": is_entry,
            "is_exported": False,
            "is_test": is_test,
            "is_abstract": is_abstract,
            "is_deprecated": is_deprecated,
            "has_ai_summary": False,
        }

    def _guess_module_type(self, file_name: str, rel_path: str, content: str, lines: list[str]) -> str:
        path_lower = rel_path.lower()
        if "controller" in path_lower or "route" in path_lower:
            return "Controller"
        if "service" in path_lower:
            return "Service"
        if "repository" in path_lower or "dao" in path_lower or "repo" in path_lower:
            return "Repository"
        if "model" in path_lower or "entity" in path_lower or "schema" in path_lower:
            return "Model"
        if "middleware" in path_lower or "pipe" in path_lower:
            return "Middleware"
        if "config" in path_lower or "setting" in path_lower:
            return "Configuration"
        if "util" in path_lower or "helper" in path_lower or "common" in path_lower:
            return "Utility"
        if "auth" in path_lower or "login" in path_lower or "security" in path_lower:
            return "Authentication"
        if "test" in path_lower or "spec" in path_lower:
            return "Test"
        if "api" in path_lower or "endpoint" in path_lower:
            return "API"
        if "main" in path_lower or "index" in path_lower or "app" in path_lower:
            return "Entry Point"
        if "pipeline" in path_lower or "flow" in path_lower:
            return "Pipeline"
        if "ml" in path_lower or "model" in path_lower or "train" in path_lower or "predict" in path_lower:
            return "Machine Learning"
        if "data" in path_lower or "db" in path_lower or "database" in path_lower:
            return "Data"
        return "Module"

    def _extract_components_from_source(self, rel_path: str, module: str, language: str,
                                         file_name: str, content: str, lines: list[str]) -> list[dict]:
        result = []
        if language == "Python":
            result = self._extract_python_components(rel_path, module, language, file_name, content, lines)
        else:
            result = self._extract_non_python_components(rel_path, module, language, file_name, content, lines)
        return result

    def _extract_python_components(self, rel_path: str, module: str, language: str,
                                    file_name: str, content: str, lines: list[str]) -> list[dict]:
        components = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._extract_non_python_components(rel_path, module, language, file_name, content, lines)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                comp = self._classify_python_class(node, rel_path, module, language, content, lines)
                if comp:
                    components.append(comp)

            if isinstance(node, ast.FunctionDef):
                if not isinstance(node.parent_holder if hasattr(node, 'parent_holder') else None, ast.ClassDef):
                    comp = self._classify_python_function(node, rel_path, module, language, content, lines)
                    if comp:
                        components.append(comp)

        return components

    def _classify_python_class(self, node: ast.ClassDef, rel_path: str, module: str,
                                language: str, content: str, lines: list[str]) -> dict | None:
        class_name = node.name
        name_lower = class_name.lower()
        ctype = "model"
        sub_type = "Class"
        confidence = 0.5
        reason = "Generic class"

        bases = [b.id if isinstance(b, ast.Name) else (b.attr if isinstance(b, ast.Attribute) else "") for b in node.bases]
        for pattern, pt, pst, pconf in COMPONENT_PATTERNS.get("Python", []):
            if pattern.startswith("class"):
                if re.search(pattern, content[0:max(node.end_lineno or node.lineno, node.lineno) + 5], re.IGNORECASE):
                    if pconf > confidence:
                        ctype = pt
                        sub_type = pst
                        confidence = pconf
                        reason = f"Name pattern: {pattern}"

        decorators = [d.id if isinstance(d, ast.Name) else "" for d in node.decorator_list]
        for dec in decorators:
            for pattern, pt, pst, pconf in COMPONENT_PATTERNS.get("Python", []):
                if pattern.startswith("@"):
                    pat_name = pattern.lstrip("@").rstrip("\\(").rstrip("\\")
                    if dec and dec.lower() == pat_name.lower():
                        if pconf > confidence:
                            ctype = pt
                            sub_type = pst
                            confidence = pconf
                            reason = f"Decorator: @{dec}"

        if "Exception" in name_lower or "Error" in name_lower:
            ctype = "utility"
            sub_type = "Exception"
            reason = "Exception class naming"

        methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        has_route = any(m.startswith(("get", "post", "put", "delete", "patch")) for m in methods)
        if has_route and ctype == "model":
            ctype = "controller"
            sub_type = "Controller"
            confidence = 0.7
            reason = "Contains route-like methods"

        has_crud = any(m.lower().startswith(("create", "read", "update", "delete", "find", "save")) for m in methods)
        if has_crud and ctype in ("model",):
            ctype = "repository"
            sub_type = "Repository"
            confidence = 0.7
            reason = "Contains CRUD methods"

        method_count = len(methods)
        complexity = sum(
            sum(1 for _ in ast.walk(m) if isinstance(_, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Try)))
            for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
        is_abstract = any(
            isinstance(d, ast.Name) and d.id == "abstractmethod"
            for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            for d in m.decorator_list
        ) or any(
            b == "ABC" for b in bases
        )

        purpose, responsibility, role, business_context, summary = self._generate_semantic_description(
            rel_path, class_name, ctype, sub_type, content, lines
        )

        class_line = node.lineno
        id_str = f"{module}.{class_name}"

        return {
            "id": id_str,
            "name": class_name,
            "type": ctype,
            "sub_type": sub_type,
            "file_path": rel_path,
            "module": module,
            "language": language,
            "line_number": class_line,
            "purpose": purpose,
            "responsibility": responsibility,
            "role": role,
            "business_context": business_context,
            "summary": summary,
            "classification_reason": _sanitize(reason),
            "confidence": confidence,
            "complexity": complexity,
            "is_entry_point": False,
            "is_exported": False,
            "is_test": "_test" in rel_path.lower() or "test_" in class_name.lower(),
            "is_abstract": is_abstract,
            "is_deprecated": False,
            "has_ai_summary": False,
        }

    def _classify_python_function(self, node: ast.FunctionDef, rel_path: str, module: str,
                                   language: str, content: str, lines: list[str]) -> dict | None:
        func_name = node.name
        name_lower = func_name.lower()
        ctype = "function"
        sub_type = "Function"
        confidence = 0.5
        reason = "Generic function"

        if func_name == "main" or func_name == "run":
            ctype = "entry_point"
            sub_type = "Entry Point"
            confidence = 0.9
            reason = "Main entry point function"

        if name_lower.startswith("test") or name_lower.endswith("_test"):
            ctype = "test"
            sub_type = "Test Function"
            confidence = 0.9
            reason = "Test function naming"

        if name_lower.startswith(("get_", "post_", "put_", "delete_", "patch_")):
            ctype = "api"
            sub_type = "API Handler"
            confidence = 0.7
            reason = "API handler naming"

        if name_lower.startswith(("validate", "sanitize", "check")):
            ctype = "utility"
            sub_type = "Validator"
            confidence = 0.7
            reason = "Validation function"

        if name_lower.startswith(("convert", "transform", "map", "parse")):
            ctype = "utility"
            sub_type = "Transformer"
            confidence = 0.7
            reason = "Transformation function"

        if name_lower.startswith(("create_", "save_", "update_", "delete_", "find_", "get_by_")):
            ctype = "data"
            sub_type = "Data Operation"
            confidence = 0.7
            reason = "Data operation function"

        if name_lower.startswith(("predict", "forecast", "train", "evaluate")):
            ctype = "ml"
            sub_type = "ML Operation"
            confidence = 0.8
            reason = "Machine learning function"

        if name_lower.startswith(("format_", "render_", "generate_", "build_")):
            ctype = "utility"
            sub_type = "Generator"
            confidence = 0.6
            reason = "Generation function"

        if name_lower.startswith(("handle_", "process_", "on_")):
            ctype = "controller"
            sub_type = "Handler"
            confidence = 0.6
            reason = "Event handler function"

        complexity = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Try)))
        decorators = [d.id if isinstance(d, ast.Name) else "" for d in node.decorator_list]
        is_abstract = "abstractmethod" in decorators or "abc.abstractmethod" in decorators
        is_entry = ctype == "entry_point"

        purpose, responsibility, role, business_context, summary = self._generate_semantic_description(
            rel_path, func_name, ctype, sub_type, content, lines
        )

        id_str = f"{module}.{func_name}"

        return {
            "id": id_str,
            "name": func_name,
            "type": ctype,
            "sub_type": sub_type,
            "file_path": rel_path,
            "module": module,
            "language": language,
            "line_number": node.lineno,
            "purpose": purpose,
            "responsibility": responsibility,
            "role": role,
            "business_context": business_context,
            "summary": summary,
            "classification_reason": _sanitize(reason),
            "confidence": confidence,
            "complexity": complexity,
            "is_entry_point": is_entry,
            "is_exported": False,
            "is_test": ctype == "test",
            "is_abstract": is_abstract,
            "is_deprecated": False,
            "has_ai_summary": False,
        }

    def _extract_non_python_components(self, rel_path: str, module: str, language: str,
                                        file_name: str, content: str, lines: list[str]) -> list[dict]:
        components = []
        patterns = COMPONENT_PATTERNS.get(language, [])

        class_pattern = r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)"
        function_pattern = r"(?:export\s+)?(?:async\s+)?function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(.*\)\s*=>|(?:export\s+)?(?:async\s+)?(\w+)\s*=\s*(?:async\s*)?\(.*\)\s*=>"

        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            name_lower = class_name.lower()
            ctype = "model"
            sub_type = "Class"
            confidence = 0.5
            reason = "Generic class"
            class_line = content[:match.start()].count("\n") + 1

            class_context = content[max(0, match.start() - 200):match.end() + 100]
            for pattern, pt, pst, pconf in patterns:
                if "class" in pattern and re.search(pattern, class_context, re.IGNORECASE):
                    if pconf > confidence:
                        ctype = pt
                        sub_type = pst
                        confidence = pconf
                        reason = f"Name pattern: {pattern}"

            purpose, responsibility, role, business_context, summary = self._generate_semantic_description(
                rel_path, class_name, ctype, sub_type, content, lines
            )

            id_str = f"{module}.{class_name}"
            components.append({
                "id": id_str, "name": class_name, "type": ctype, "sub_type": sub_type,
                "file_path": rel_path, "module": module, "language": language,
                "line_number": class_line, "purpose": purpose, "responsibility": responsibility,
                "role": role, "business_context": business_context, "summary": summary,
                "classification_reason": _sanitize(reason), "confidence": confidence, "complexity": 0,
                "is_entry_point": False, "is_exported": bool(re.search(r"export\s+", match.group(0))),
                "is_test": "_test" in rel_path.lower() or "test_" in class_name.lower(),
                "is_abstract": "abstract" in match.group(0),
                "is_deprecated": False, "has_ai_summary": False,
            })

        for match in re.finditer(function_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3) or ""
            if not func_name:
                continue
            name_lower = func_name.lower()
            func_line = content[:match.start()].count("\n") + 1
            ctype = "function"
            sub_type = "Function"
            confidence = 0.5
            reason = "Generic function"

            if name_lower in ("main", "run", "start", "bootstrap"):
                ctype = "entry_point"
                sub_type = "Entry Point"
                confidence = 0.9
                reason = "Entry point function"

            if name_lower.startswith(("get", "post", "put", "delete", "patch")):
                ctype = "api"
                sub_type = "API Handler"
                confidence = 0.6
                reason = "API handler naming"

            purpose, responsibility, role, business_context, summary = self._generate_semantic_description(
                rel_path, func_name, ctype, sub_type, content, lines
            )

            id_str = f"{module}.{func_name}"
            components.append({
                "id": id_str, "name": func_name, "type": ctype, "sub_type": sub_type,
                "file_path": rel_path, "module": module, "language": language,
                "line_number": func_line, "purpose": purpose, "responsibility": responsibility,
                "role": role, "business_context": business_context, "summary": summary,
                        "classification_reason": _sanitize(reason), "confidence": confidence, "complexity": 0,
                "is_entry_point": ctype == "entry_point",
                "is_exported": bool(re.search(r"export\s+", match.group(0))),
                "is_test": "_test" in rel_path.lower() or "test_" in func_name.lower(),
                "is_abstract": False, "is_deprecated": False, "has_ai_summary": False,
            })

        return components

    def _generate_semantic_description(self, file_path: str, name: str, ctype: str,
                                        sub_type: str, content: str, lines: list[str]) -> tuple[str, str, str, str, str]:
        role_info = ROLE_PURPOSE_MAP.get(ctype, ("Component", "Module", "Provides functionality"))
        base_purpose = role_info[0]
        base_role = role_info[1]
        base_responsibility = role_info[2]

        name_purpose = self._infer_purpose_from_name(name)
        file_purpose = self._infer_purpose_from_path(file_path)
        imports = self._extract_import_lines(content)
        import_purpose = self._infer_purpose_from_imports(imports)

        purposes = [p for p in [name_purpose, file_purpose, import_purpose, base_purpose] if p]
        purpose = purposes[0] if purposes else base_purpose

        detail = self._generate_detail_description(content, lines)

        summary = f"{sub_type} `{name}`: {purpose}"
        if detail:
            summary += f". {detail}"

        business_context = self._infer_business_context(file_path, name, content)

        return purpose, base_responsibility, base_role, business_context, summary

    def _infer_purpose_from_name(self, name: str) -> str:
        name_lower = name.lower()
        purposes = {
            "login": "Handles user login and authentication",
            "logout": "Handles user logout and session cleanup",
            "register": "Handles user registration and account creation",
            "validate": "Validates data inputs and ensures data integrity",
            "sanitize": "Sanitizes and cleans data inputs",
            "authenticate": "Authenticates users and verifies credentials",
            "authorize": "Authorizes user actions and permissions",
            "encrypt": "Encrypts data for secure storage or transmission",
            "decrypt": "Decrypts data for secure retrieval",
            "convert": "Converts data between different formats",
            "transform": "Transforms data from one structure to another",
            "parse": "Parses structured data from text or files",
            "format": "Formats data into a specific structure or display",
            "generate": "Generates computed or derived data",
            "calculate": "Performs calculations and computations",
            "compute": "Computes results from input data",
            "fetch": "Retrieves data from external sources",
            "query": "Queries data from databases or data stores",
            "save": "Persists data to storage",
            "update": "Updates existing data in storage",
            "delete": "Removes data from storage",
            "create": "Creates new data entries",
            "find": "Searches for data matching criteria",
            "search": "Performs search operations on data",
            "predict": "Generates predictions using models",
            "forecast": "Produces forecasts from historical data",
            "train": "Trains machine learning models",
            "evaluate": "Evaluates model performance and accuracy",
            "notify": "Sends notifications to users or systems",
            "alert": "Generates alerts for specific conditions",
            "process": "Processes data through a defined pipeline",
            "handle": "Handles events, requests, or exceptions",
            "render": "Renders output to a specific format",
            "export": "Exports data to external formats",
            "import": "Imports data from external sources",
            "migrate": "Migrates data between storage systems",
            "backup": "Creates backup copies of data",
            "restore": "Restores data from backups",
            "initialize": "Initializes components or systems",
            "configure": "Configures system settings and parameters",
            "connect": "Establishes connections to external services",
            "disconnect": "Terminates connections to external services",
            "monitor": "Monitors system health and performance",
            "health": "Provides health check endpoints",
            "stats": "Computes and returns statistics",
            "report": "Generates reports from collected data",
        }
        for key, desc in purposes.items():
            if key in name_lower:
                return desc
        if name_lower.startswith(("is_", "has_", "can_")):
            return "Checks and returns a boolean condition"
        if name_lower.startswith("get_"):
            return "Retrieves and returns data"
        if name_lower.startswith("set_"):
            return "Sets and updates data values"
        if name_lower.startswith("to_"):
            return "Converts to a different representation"
        return ""

    def _infer_purpose_from_path(self, file_path: str) -> str:
        path_lower = file_path.lower()
        if "controller" in path_lower:
            return "Handles HTTP requests and route dispatch"
        if "service" in path_lower:
            return "Implements business logic and coordination"
        if "repository" in path_lower or "repo" in path_lower:
            return "Manages data persistence and retrieval"
        if "model" in path_lower or "entity" in path_lower:
            return "Defines domain models and data structures"
        if "schema" in path_lower:
            return "Defines data validation schemas"
        if "middleware" in path_lower:
            return "Processes requests through middleware pipeline"
        if "config" in path_lower or "setting" in path_lower:
            return "Centralizes application configuration"
        if "util" in path_lower or "helper" in path_lower:
            return "Provides reusable utility functions"
        if "test" in path_lower or "spec" in path_lower:
            return "Contains automated test cases"
        if "route" in path_lower or "api" in path_lower or "endpoint" in path_lower:
            return "Defines API endpoints and routing"
        if "auth" in path_lower or "login" in path_lower or "security" in path_lower:
            return "Manages authentication and authorization"
        if "pipeline" in path_lower or "flow" in path_lower:
            return "Orchestrates data processing pipelines"
        if "db" in path_lower or "database" in path_lower or "data" in path_lower:
            return "Manages database connections and data access"
        if "ml" in path_lower or "model" in path_lower or "train" in path_lower or "predict" in path_lower:
            return "Implements machine learning capabilities"
        if "decorator" in path_lower:
            return "Provides decorator utilities"
        if "exception" in path_lower or "error" in path_lower:
            return "Defines error handling and exceptions"
        if "adapter" in path_lower:
            return "Adapts external interfaces to internal APIs"
        if "factory" in path_lower:
            return "Factory for creating objects"
        if "main" in path_lower or "app" in path_lower or "index" in path_lower:
            return "Application entry point and bootstrap"
        if "migration" in path_lower:
            return "Manages database schema migrations"
        if "seed" in path_lower:
            return "Seeds database with initial data"
        if "guard" in path_lower:
            return "Guards routes and permissions"
        if "pipe" in path_lower:
            return "Transforms data through pipes"
        if "interceptor" in path_lower:
            return "Intercepts requests or responses"
        if "filter" in path_lower:
            return "Filters data based on criteria"
        if "handler" in path_lower:
            return "Handles specific event types"
        return ""

    def _extract_import_lines(self, content: str) -> list[str]:
        imports = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ", "require(", "#include", "using ")):
                imports.append(stripped)
        return imports

    def _infer_purpose_from_imports(self, imports: list[str]) -> str:
        import_text = " ".join(imports).lower()
        if "flask" in import_text or "fastapi" in import_text or "django" in import_text:
            return "Handles HTTP requests and serves API endpoints"
        if "sqlalchemy" in import_text or "django.db" in import_text or "sequelize" in import_text:
            return "Manages database models and ORM operations"
        if "pandas" in import_text or "numpy" in import_text or "scipy" in import_text:
            return "Performs data analysis and numerical computations"
        if "tensorflow" in import_text or "torch" in import_text or "sklearn" in import_text:
            return "Implements machine learning models and training"
        if "jwt" in import_text or "oauth" in import_text or "passlib" in import_text:
            return "Manages authentication and token-based security"
        if "pytest" in import_text or "unittest" in import_text or "jest" in import_text:
            return "Contains automated tests and test utilities"
        if "redis" in import_text:
            return "Manages Redis caching and data storage"
        if "celery" in import_text or "kafka" in import_text or "rabbitmq" in import_text:
            return "Manages task queues and message processing"
        if "logging" in import_text:
            return "Provides logging and diagnostic capabilities"
        if "pydantic" in import_text or "marshmallow" in import_text:
            return "Defines data validation and serialization schemas"
        if "click" in import_text or "argparse" in import_text:
            return "Provides CLI interface and command handling"
        if "aiohttp" in import_text or "httpx" in import_text or "requests" in import_text:
            return "Handles HTTP client requests to external services"
        return ""

    def _generate_detail_description(self, content: str, lines: list[str]) -> str:
        detail_parts = []
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            doc = docstring_match.group(1).strip()
            if doc:
                first_line = doc.split("\n")[0].strip()
                if first_line:
                    return first_line[:200]

        comment_lines = []
        for line in lines[:20]:
            stripped = line.strip()
            if stripped.startswith("#"):
                comment_text = stripped.lstrip("#").strip()
                if comment_text and len(comment_text) > 10:
                    comment_lines.append(comment_text)
        if comment_lines:
            return comment_lines[0][:200]

        if "This class" in content or "This function" in content or "This module" in content:
            for match in re.finditer(r'(?:This\s+\w+\s+)(.*?)[.\n]', content[:1000]):
                return match.group(0).strip()[:200]

        return ""

    def _infer_business_context(self, file_path: str, name: str, content: str) -> str:
        path_lower = file_path.lower()
        ctx_parts = []

        if "user" in path_lower or "user" in name.lower():
            ctx_parts.append("User management")
        if "auth" in path_lower or "login" in path_lower or "security" in path_lower:
            ctx_parts.append("Authentication & security")
        if "payment" in path_lower or "billing" in path_lower or "invoice" in path_lower:
            ctx_parts.append("Payment processing & billing")
        if "order" in path_lower:
            ctx_parts.append("Order management")
        if "product" in path_lower:
            ctx_parts.append("Product catalog")
        if "inventory" in path_lower:
            ctx_parts.append("Inventory management")
        if "report" in path_lower:
            ctx_parts.append("Reporting & analytics")
        if "notification" in path_lower or "alert" in path_lower:
            ctx_parts.append("Notification & alerts")
        if "forecast" in path_lower or "predict" in path_lower:
            ctx_parts.append("Forecasting & prediction")
        if "pipeline" in path_lower:
            ctx_parts.append("Data pipeline")
        if "dashboard" in path_lower:
            ctx_parts.append("Dashboard & visualization")
        if "admin" in path_lower:
            ctx_parts.append("Administration")
        if "api" in path_lower or "v1" in path_lower or "v2" in path_lower:
            ctx_parts.append("API layer")

        content_lower = content.lower()
        if "forecast" in content_lower:
            if "forecast" not in str(ctx_parts):
                ctx_parts.append("Forecasting")
        if "train" in content_lower and "model" in content_lower:
            if "machine learning" not in str(ctx_parts).lower():
                ctx_parts.append("Machine learning model training")
        if "database" in content_lower or "connection" in content_lower:
            if "database" not in str(ctx_parts).lower():
                ctx_parts.append("Database operations")

        return "; ".join(ctx_parts) if ctx_parts else "General application functionality"

    def _estimate_file_complexity(self, content: str, lines: list[str]) -> int:
        complexity = 1
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("if ", "elif ", "for ", "while ", "except", "with ", "try:")):
                complexity += 1
            if stripped.startswith(("class ", "def ", "async def ")):
                complexity += 1
            if " and " in stripped or " or " in stripped:
                complexity += 1
            if "?" in stripped or ":" in stripped:
                pass
        return min(complexity, 100)

    def _extract_imports_exports(self, rel_path: str, module: str, language: str,
                                  content: str, lines: list[str]) -> tuple[list[str], list[str]]:
        imports = []
        exports = []

        if language == "Python":
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    imports.append(stripped)

        elif language in ("JavaScript", "TypeScript"):
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("require("):
                    imports.append(stripped)
                if stripped.startswith("export "):
                    exports.append(stripped)

        elif language == "Java":
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import "):
                    imports.append(stripped)

        return imports, exports

    def _extract_symbols(self, rel_path: str, module: str, language: str,
                          content: str, lines: list[str]) -> list[dict]:
        symbols = []
        seen = set()

        if language == "Python":
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return symbols
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    sym_id = f"{module}.{node.name}"
                    if sym_id not in seen:
                        seen.add(sym_id)
                        symbols.append({
                            "name": node.name, "kind": "function",
                            "file_path": rel_path, "module": module,
                            "line_number": node.lineno, "is_definition": True,
                            "is_exported": False, "is_imported": False,
                            "resolved_target": "", "aliases": [],
                        })
                elif isinstance(node, ast.ClassDef):
                    sym_id = f"{module}.{node.name}"
                    if sym_id not in seen:
                        seen.add(sym_id)
                        symbols.append({
                            "name": node.name, "kind": "class",
                            "file_path": rel_path, "module": module,
                            "line_number": node.lineno, "is_definition": True,
                            "is_exported": False, "is_imported": False,
                            "resolved_target": "", "aliases": [],
                        })
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            sym_id = f"{module}.{target.id}"
                            if sym_id not in seen:
                                seen.add(sym_id)
                                symbols.append({
                                    "name": target.id, "kind": "constant",
                                    "file_path": rel_path, "module": module,
                                    "line_number": node.lineno, "is_definition": True,
                                    "is_exported": False, "is_imported": False,
                                    "resolved_target": "", "aliases": [],
                                })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        sym_id = f"{module}.{name}"
                        if sym_id not in seen:
                            seen.add(sym_id)
                            symbols.append({
                                "name": name, "kind": "import",
                                "file_path": rel_path, "module": module,
                                "line_number": node.lineno, "is_definition": False,
                                "is_exported": False, "is_imported": True,
                                "resolved_target": alias.name, "aliases": [alias.asname] if alias.asname else [],
                            })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        src = f"{node.module}.{alias.name}" if node.module else alias.name
                        sym_id = f"{module}.{name}"
                        if sym_id not in seen:
                            seen.add(sym_id)
                            symbols.append({
                                "name": name, "kind": "import",
                                "file_path": rel_path, "module": module,
                                "line_number": node.lineno, "is_definition": False,
                                "is_exported": False, "is_imported": True,
                                "resolved_target": src, "aliases": [alias.asname] if alias.asname else [],
                            })
        else:
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    parts = stripped.split()
                    if len(parts) >= 2 and parts[1] not in seen:
                        seen.add(parts[1])
                        symbols.append({
                            "name": parts[1], "kind": "import",
                            "file_path": rel_path, "module": module,
                            "line_number": lines.index(line) + 1, "is_definition": False,
                            "is_exported": False, "is_imported": True,
                            "resolved_target": parts[1], "aliases": [],
                        })
                func_m = re.match(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", stripped)
                if func_m and func_m.group(1) not in seen:
                    seen.add(func_m.group(1))
                    symbols.append({
                        "name": func_m.group(1), "kind": "function",
                        "file_path": rel_path, "module": module,
                        "line_number": lines.index(line) + 1, "is_definition": True,
                        "is_exported": "export" in stripped, "is_imported": False,
                        "resolved_target": "", "aliases": [],
                    })
                class_m = re.match(r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)", stripped)
                if class_m and class_m.group(1) not in seen:
                    seen.add(class_m.group(1))
                    symbols.append({
                        "name": class_m.group(1), "kind": "class",
                        "file_path": rel_path, "module": module,
                        "line_number": lines.index(line) + 1, "is_definition": True,
                        "is_exported": "export" in stripped, "is_imported": False,
                        "resolved_target": "", "aliases": [],
                    })

        return symbols

    def _resolve_symbols_across_files(self, symbols: list[dict], module_map: dict) -> None:
        module_syms: dict[str, list[dict]] = defaultdict(list)
        for sym in symbols:
            if sym["is_definition"]:
                module_syms[sym["name"]].append(sym)

        for sym in symbols:
            if sym["is_imported"] and sym.get("resolved_target") and sym["resolved_target"] in module_syms:
                resolved = module_syms[sym["resolved_target"]]
                if resolved:
                    sym["resolved_target"] = resolved[0].get("module", "") + "." + resolved[0]["name"]
                    sym["file_path"] = resolved[0].get("file_path", sym["file_path"])

    def _build_relationships(self, components: list[dict], relationships: list[dict],
                              all_imports: dict, all_exports: dict,
                              module_map: dict, file_component_map: dict) -> None:
        seen_rels: set[tuple[str, str, str]] = set()

        for src_path, imports in all_imports.items():
            src_components = file_component_map.get(src_path, [])
            if not src_components:
                continue

            for imp in imports:
                for tgt_path in file_component_map:
                    if imp and any(part in tgt_path.replace("/", ".").lower() for part in imp.lower().split()):
                        rel_key = (src_components[0]["id"], tgt_path, "imports")
                        if rel_key not in seen_rels:
                            seen_rels.add(rel_key)
                            relationships.append({
                                "source_id": src_components[0]["id"],
                                "target_id": file_component_map[tgt_path][0]["id"] if file_component_map[tgt_path] else tgt_path,
                                "relationship_type": "imports",
                                "description": f"Imports from {tgt_path}",
                                "strength": 0.7,
                                "is_direct": True,
                                "file_path": src_path,
                                "line_number": 0,
                            })

        for path, comps in file_component_map.items():
            for comp in comps:
                for other_path, other_comps in file_component_map.items():
                    if path == other_path:
                        continue
                    for other in other_comps:
                        if comp["module"] and other["module"]:
                            parts_comp = comp["module"].split(".")
                            parts_other = other["module"].split(".")
                            common = sum(1 for a, b in zip(parts_comp, parts_other) if a == b)
                            if common >= len(parts_comp) - 1 or common >= len(parts_other) - 1:
                                rel_key = (comp["id"], other["id"], "same_module")
                                if rel_key not in seen_rels:
                                    seen_rels.add(rel_key)
                                    relationships.append({
                                        "source_id": comp["id"],
                                        "target_id": other["id"],
                                        "relationship_type": "same_module",
                                        "description": f"Shares module with {other['name']}",
                                        "strength": 0.5,
                                        "is_direct": False,
                                        "file_path": path,
                                        "line_number": 0,
                                    })

        for path, exports in file_component_map.items():
            for exp in exports:
                for other_path, other_imports in all_imports.items():
                    if path == other_path:
                        continue
                    for imp in other_imports:
                        if exp["name"].lower() in imp.lower():
                            rel_key = (exp["id"], other_path, "exported_to")
                            if rel_key not in seen_rels:
                                seen_rels.add(rel_key)
                                relationships.append({
                                    "source_id": exp["id"],
                                    "target_id": f"{other_path}.module",
                                    "relationship_type": "exported_to",
                                    "description": f"Exported to {other_path}",
                                    "strength": 0.8,
                                    "is_direct": True,
                                    "file_path": path,
                                    "line_number": 0,
                                })

    def _detect_business_flows(self, components: list[dict], relationships: list[dict],
                                all_imports: dict, file_language_map: dict,
                                file_component_map: dict) -> list[dict]:
        flows = []
        seen_flows: set[str] = set()
        flow_id_counter = [0]

        project_files = set(file_language_map.keys())
        file_content_combined = ""
        file_import_text = ""
        for path in project_files:
            file_content_combined += path.lower() + " "
        for imports in all_imports.values():
            file_import_text += " ".join(imports).lower() + " "

        component_names = " ".join(c["name"].lower() + " " + c.get("file_path", "").lower() for c in components)
        component_imports = " ".join(c.get("file_path", "").lower() for c in components)
        search_text = file_content_combined + file_import_text + component_names + component_imports

        for flow_name, flow_type, entry_keywords, exit_keywords in BUSINESS_FLOW_PATTERNS:
            flow_key = flow_name.lower().replace(" ", "_")
            flow_id = f"flow_{flow_id_counter[0]}"

            has_entry = any(kw in search_text for kw in entry_keywords)
            has_exit = any(kw in search_text for kw in exit_keywords)

            entry_comps = []
            exit_comps = []
            path_comps = []
            verified = False
            confidence = "low"

            if has_entry and has_exit:
                confidence = "high"
                verified = True
            elif has_entry or has_exit:
                confidence = "medium"

            if verified:
                for comp in components:
                    comp_search = comp["name"].lower() + " " + comp.get("file_path", "").lower()
                    if any(kw in comp_search for kw in entry_keywords):
                        entry_comps.append(comp["id"])
                    if any(kw in comp_search for kw in exit_keywords):
                        exit_comps.append(comp["id"])
                    if any(kw in comp_search for kw in entry_keywords + exit_keywords):
                        path_comps.append(comp["id"])

            if verified and flow_key not in seen_flows:
                seen_flows.add(flow_key)
                flows.append({
                    "id": flow_id,
                    "name": flow_name,
                    "description": f"Detected {flow_type} flow involving business operations related to {', '.join(entry_keywords[:3])}",
                    "flow_type": flow_type,
                    "confidence": confidence,
                    "entry_components": entry_comps,
                    "exit_components": exit_comps,
                    "path": path_comps,
                    "components": path_comps,
                    "verified": verified,
                })
                flow_id_counter[0] += 1

        return flows

    def _detect_similarities(self, components: list[dict], component_map: dict) -> list[dict]:
        similarities = []
        seen_pairs: set[tuple[str, str]] = set()

        type_groups: dict[str, list[dict]] = defaultdict(list)
        for comp in components:
            t = comp.get("type", "unknown")
            type_groups[t].append(comp)

        for t, group in type_groups.items():
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    a = group[i]
                    b = group[j]
                    pair_key = (a["id"], b["id"]) if a["id"] < b["id"] else (b["id"], a["id"])
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    score = 0.0
                    patterns = []

                    if a["name"].lower() == b["name"].lower():
                        score += 0.3
                        patterns.append("Same name")

                    if a.get("file_path", "").rsplit("/", 1)[0] == b.get("file_path", "").rsplit("/", 1)[0]:
                        score += 0.1
                        patterns.append("Same directory")

                    if a.get("module", "").rsplit(".", 1)[0] == b.get("module", "").rsplit(".", 1)[0]:
                        score += 0.1
                        patterns.append("Same parent module")

                    a_name_parts = set(re.split(r"[_\s./]", a["name"].lower()))
                    b_name_parts = set(re.split(r"[_\s./]", b["name"].lower()))
                    common = a_name_parts & b_name_parts
                    if len(common) >= 2:
                        score += 0.15
                        patterns.append(f"Shared keywords: {', '.join(list(common)[:3])}")

                    if a.get("type") == b.get("type"):
                        score += 0.1
                        patterns.append("Same component type")

                    if score >= 0.3:
                        similarities.append({
                            "component_a_id": a["id"],
                            "component_b_id": b["id"],
                            "similarity_type": t,
                            "score": round(min(score, 1.0), 2),
                            "description": f"Similar {t} components with {int(score * 100)}% similarity",
                            "shared_patterns": patterns,
                        })

        return similarities

    def _generate_component_issues(self, components: list[dict], similarities: list[dict]) -> list[dict]:
        issues = []
        seen_issue_types: set[str] = set()

        deprecated = [c for c in components if c.get("is_deprecated")]
        if deprecated:
            issue_key = "deprecated_components"
            if issue_key not in seen_issue_types:
                seen_issue_types.add(issue_key)
                issues.append({
                    "type": "deprecated_component",
                    "severity": "warning",
                    "component_id": deprecated[0]["id"],
                    "description": f"Found {len(deprecated)} deprecated component(s) that should be reviewed",
                    "detail": f"Components: {', '.join(c['name'] for c in deprecated[:5])}",
                    "suggestion": "Review and update deprecated components to remove technical debt",
                })

        high_similarity = [s for s in similarities if s.get("score", 0) >= 0.6]
        if high_similarity:
            issue_key = "duplicate_logic"
            if issue_key not in seen_issue_types:
                seen_issue_types.add(issue_key)
                names = []
                for s in high_similarity[:3]:
                    names.append(f"{s['component_a_id']} & {s['component_b_id']}")
                issues.append({
                    "type": "duplicate_logic",
                    "severity": "warning",
                    "component_id": high_similarity[0]["component_a_id"],
                    "description": f"Found {len(high_similarity)} highly similar component pair(s) indicating possible duplication",
                    "detail": f"Pairs: {'; '.join(names)}",
                    "suggestion": "Consider consolidating duplicate logic into shared utilities",
                })

        misclassified = [c for c in components if c.get("confidence", 1) < 0.5]
        if misclassified:
            issue_key = "unclear_classification"
            if issue_key not in seen_issue_types:
                seen_issue_types.add(issue_key)
                issues.append({
                    "type": "unclear_classification",
                    "severity": "info",
                    "component_id": misclassified[0]["id"],
                    "description": f"Found {len(misclassified)} component(s) with unclear classification (confidence < 50%)",
                    "detail": f"Components: {', '.join(c['name'] for c in misclassified[:5])}",
                    "suggestion": "Review naming conventions to improve automatic classification",
                })

        return issues

    def _enhance_purposes(self, components: list[dict], all_imports: dict,
                           file_component_map: dict) -> None:
        for comp in components:
            fp = comp.get("file_path", "")
            imports = all_imports.get(fp, [])
            import_text = " ".join(imports).lower()

            if comp.get("purpose") == "Provides reusable utility functions" and "pandas" in import_text:
                comp["purpose"] = "Provides data processing and analysis utilities"
                comp["summary"] = f"{comp['sub_type']} `{comp['name']}`: {comp['purpose']}"

            if comp.get("purpose") == "Handles HTTP requests and serves API endpoints" and "database" in import_text:
                comp["purpose"] = "Provides API endpoints with database integration"
                comp["summary"] = f"{comp['sub_type']} `{comp['name']}`: {comp['purpose']}"

    def _generate_ai_insights(self, components: list[dict], relationships: list[dict],
                               business_flows: list[dict], issues: list[dict],
                               similarities: list[dict], type_breakdown: dict) -> list[str]:
        insights = []
        total = len(components)

        if total == 0:
            return ["No components were analyzed in this project."]

        type_names = {v: k for k, v in {
            "controller": "Controllers", "service": "Services", "repository": "Repositories",
            "model": "Models", "api": "API definitions", "middleware": "Middleware",
            "configuration": "Configuration", "auth": "Authentication logic",
            "data": "Data management", "ml": "ML components", "test": "Tests",
            "utility": "Utilities", "entry_point": "Entry points",
        }.items()}

        type_counts = []
        for t, count in sorted(type_breakdown.items(), key=lambda x: -x[1]):
            label = type_names.get(t, f"{t.capitalize()} components")
            if count > 0:
                type_counts.append(f"{count} {label.lower()}")
        if type_counts:
            insights.append(f"Project contains {', '.join(type_counts)} across {total} total semantic components.")

        controllers = [c for c in components if c.get("type") == "controller"]
        services = [c for c in components if c.get("type") == "service"]
        repositories = [c for c in components if c.get("type") == "repository"]

        if controllers and not services:
            insights.append("Business logic appears to bypass the service layer, as controllers directly interact with repositories or data sources without intermediate services.")
        if services and not repositories:
            insights.append("Services are defined but no dedicated repositories found. Data access may be embedded within services.")

        if repositories and services:
            insights.append("Clean separation between services and repositories suggests a well-layered architecture.")

        if business_flows:
            verified = [f for f in business_flows if f.get("verified")]
            if verified:
                flow_names = [f["name"] for f in verified[:3]]
                insights.append(f"Detected {len(verified)} verified business flow(s): {', '.join(flow_names)}.")
            else:
                insights.append(f"Detected {len(business_flows)} potential business flow(s) requiring further verification.")

        duplicate_issues = [i for i in issues if i.get("type") == "duplicate_logic"]
        if duplicate_issues:
            insights.append(f"Found {sum(1 for s in similarities if s.get('score', 0) >= 0.6)} similar component pair(s) that may benefit from consolidation.")

        deprecated = [c for c in components if c.get("is_deprecated")]
        if deprecated:
            insights.append(f"{len(deprecated)} component(s) are marked as deprecated and should be reviewed for removal or refactoring.")

        if type_breakdown.get("test", 0) == 0 and total > 5:
            insights.append("No test components detected. Consider adding test coverage for the project's components.")

        ml_components = [c for c in components if c.get("type") == "ml"]
        if ml_components:
            insights.append(f"ML/AI capabilities are present across {len(ml_components)} component(s), suggesting data-driven functionality.")

        api_components = [c for c in components if c.get("type") == "api"]
        if api_components:
            non_api_services = len(services)
            ratio = len(api_components) / max(non_api_services, 1)
            if ratio > 3 and non_api_services > 0:
                insights.append("API layer has significantly more components than the service layer. Consider whether business logic is properly separated from request handling.")

        return insights

    def _analyze_from_call_graph(self, components, relationships, symbols,
                                   language_breakdown, type_breakdown, component_type_counts,
                                   file_component_map, component_map, files_analyzed,
                                   module_map, file_language_map, all_imports, all_exports,
                                   call_graph_data, workspace_path):
        nodes = call_graph_data.get("nodes", [])
        edges = call_graph_data.get("edges", [])
        file_imports_data = call_graph_data.get("file_imports", {})
        file_lang_map = call_graph_data.get("file_language_map", {})

        file_node_map = defaultdict(list)
        for node in nodes:
            fp = node.get("file_path", "")
            if fp:
                file_node_map[fp].append(node)
                if fp not in files_analyzed:
                    files_analyzed.add(fp)
                    lang = file_lang_map.get(fp, node.get("language", "unknown"))
                    file_language_map[fp] = lang
                    language_breakdown[lang] += 1
                    mod = fp.replace("/", ".").rsplit(".", 1)[0] if "." in fp else fp
                    module_map[fp] = mod

        for fp, f_nodes in file_node_map.items():
            lang = file_language_map.get(fp, "unknown")
            mod = module_map.get(fp, fp)
            fname = fp.rsplit("/", 1)[-1] if "/" in fp else fp
            file_content = call_graph_data.get("file_contents", {}).get(fp, "")
            if not file_content:
                file_path = os.path.join(workspace_path, fp)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                        file_content = fh.read()
                except (OSError, UnicodeDecodeError):
                    file_content = ""
            lines = file_content.split("\n") if file_content else []

            file_component = self._analyze_file_semantics(fp, mod, lang, fname, file_content, lines)
            if file_component:
                components.append(file_component)
                cid = file_component["id"]
                component_map[cid] = file_component
                file_component_map[fp].append(file_component)
                t = file_component.get("type", "unknown")
                type_breakdown[t] += 1
                st = file_component.get("sub_type", t)
                component_type_counts[st] += 1

            component_data = self._extract_components_from_source(fp, mod, lang, fname, file_content, lines)
            for comp in component_data:
                components.append(comp)
                cid = comp["id"]
                component_map[cid] = comp
                file_component_map[fp].append(comp)
                t = comp.get("type", "unknown")
                type_breakdown[t] += 1
                st = comp.get("sub_type", t)
                component_type_counts[st] += 1

            file_imports = file_imports_data.get(fp, [])
            all_imports[fp] = file_imports
            file_exported = call_graph_data.get("file_exports", {}).get(fp, [])
            all_exports[fp] = file_exported

            file_symbols = self._extract_symbols(fp, mod, lang, file_content, lines)
            symbols.extend(file_symbols)

    def _calculate_understanding_score(self, components, relationships, business_flows,
                                       issues, type_breakdown, language_breakdown,
                                       execution_flows) -> dict:
        total = len(components)
        if total == 0:
            return {
                "overall": 0.0, "architecture": 0.0, "business_logic": 0.0,
                "dependencies": 0.0, "code_organization": 0.0, "execution_flow": 0.0,
                "semantic_relationships": 0.0, "maintainability": 0.0, "readability": 0.0,
                "has_entry_points": False, "has_controllers": False, "has_services": False,
                "has_repositories": False, "has_ml_components": False,
                "has_forecast_components": False, "component_coverage": 0.0,
                "flow_capture_rate": 0.0, "insight_count": 0,
            }

        controllers = [c for c in components if c.get("type") == "controller"]
        services = [c for c in components if c.get("type") == "service"]
        repositories = [c for c in components if c.get("type") == "repository"]
        entry_points = [c for c in components if c.get("type") == "entry_point"]
        ml_comps = [c for c in components if c.get("type") == "ml"]
        forecast_comps = [c for c in components if c.get("name", "").lower().startswith(("forecast", "predict")) or c.get("type") == "ml" and any(kw in str(c.get("file_path", "")).lower() for kw in ["forecast", "predict"])]
        tests = [c for c in components if c.get("type") == "test"]
        models = [c for c in components if c.get("type") == "model"]
        middles = [c for c in components if c.get("type") == "middleware"]
        configs = [c for c in components if c.get("type") == "configuration"]

        arch_score = 0.0
        layers = 0
        if controllers: layers += 1
        if services: layers += 1
        if repositories: layers += 1
        if entry_points: layers += 1
        if models: layers += 1
        if middles: layers += 1
        if configs: layers += 1
        arch_score = min(1.0, layers / 6.0)
        if controllers and services and repositories:
            arch_score = min(1.0, arch_score + 0.2)
        if entry_points:
            arch_score = min(1.0, arch_score + 0.1)

        biz_score = 0.0
        verified_flows = [f for f in business_flows if f.get("verified")]
        total_flows = len(business_flows)
        if total_flows >= 5:
            biz_score = 0.9
        elif total_flows >= 3:
            biz_score = 0.7
        elif total_flows >= 1:
            biz_score = 0.5
        biz_components = services + controllers + repositories + ml_comps
        if biz_components:
            biz_score = min(1.0, biz_score + 0.1 * min(len(biz_components) / 10.0, 1.0))
        if verified_flows:
            biz_score = min(1.0, biz_score + 0.1)

        dep_score = 0.1
        num_langs = len(language_breakdown)
        if num_langs >= 2:
            dep_score += 0.15
        if len(relationships) > 0:
            dep_score += 0.15
        dep_score = max(0.1, min(1.0, dep_score + len(relationships) / max(total * 2, 1) * 0.5))

        org_score = 0.0
        components_with_path = [c for c in components if c.get("file_path", "").count("/") >= 1]
        if components_with_path:
            dirs = set(c["file_path"].rsplit("/", 1)[0] for c in components_with_path)
            org_ratio = min(1.0, len(dirs) / max(len(components_with_path), 1) * 2.0)
            org_score = 0.5 + org_ratio * 0.3
        named_components = [c for c in components if c.get("sub_type") not in ("Module", "Unknown")]
        if named_components:
            org_score = min(1.0, org_score + 0.1)
        org_score = max(0.1, min(1.0, org_score))

        flow_score = 0.0
        if execution_flows:
            ef_count = len(execution_flows)
            flow_score = min(1.0, ef_count / 10.0 * 0.8)
        if entry_points:
            flow_score = min(1.0, flow_score + 0.15)
        if total_flows > 0:
            flow_score = min(1.0, flow_score + 0.1)
        flow_score = max(0.0, min(1.0, flow_score))

        rel_score = 0.0
        num_rels = len(relationships)
        if num_rels > 0:
            rel_score = min(1.0, num_rels / max(total, 1) * 0.5)
        if num_rels > total:
            rel_score = min(1.0, rel_score + 0.2)
        rel_score = max(0.0, min(1.0, rel_score))

        maint_score = 0.7
        deprecated = [c for c in components if c.get("is_deprecated")]
        if deprecated:
            maint_score -= 0.1 * min(len(deprecated) / max(total, 1) * 5, 0.4)
        unresolved = [i for i in issues if i.get("type") in ("duplicate_logic", "unclear_classification")]
        if unresolved:
            maint_score -= 0.1 * min(len(unresolved) * 0.1, 0.3)
        if tests:
            maint_score = min(1.0, maint_score + 0.1)
        has_doc = sum(1 for c in components if c.get("has_ai_summary") or "summary" in c and c["summary"])
        if has_doc > total * 0.5:
            maint_score = min(1.0, maint_score + 0.1)
        maint_score = max(0.1, min(1.0, maint_score))

        read_score = 0.5
        named_well = [c for c in components if len(c.get("name", "")) >= 3 and not c["name"][0].isdigit()]
        if named_well:
            read_score += 0.2
        if has_doc > total * 0.3:
            read_score += 0.15
        if len(language_breakdown) <= 2:
            read_score += 0.1
        read_score = max(0.1, min(1.0, read_score))

        overall = round((arch_score + biz_score + dep_score + org_score + flow_score + rel_score + maint_score + read_score) / 8.0 * 100.0, 1)

        component_coverage = round(min(1.0, total / 20.0), 2)
        flow_capture_rate = round(min(1.0, total_flows / max(len(execution_flows), 1)), 2) if execution_flows else 0.0
        insight_count = len(business_flows) + len(issues) + len(components)

        return {
            "overall": overall,
            "architecture": round(arch_score * 100.0, 1),
            "business_logic": round(biz_score * 100.0, 1),
            "dependencies": round(dep_score * 100.0, 1),
            "code_organization": round(org_score * 100.0, 1),
            "execution_flow": round(flow_score * 100.0, 1),
            "semantic_relationships": round(rel_score * 100.0, 1),
            "maintainability": round(maint_score * 100.0, 1),
            "readability": round(read_score * 100.0, 1),
            "has_entry_points": len(entry_points) > 0,
            "has_controllers": len(controllers) > 0,
            "has_services": len(services) > 0,
            "has_repositories": len(repositories) > 0,
            "has_ml_components": len(ml_comps) > 0,
            "has_forecast_components": len(forecast_comps) > 0,
            "component_coverage": component_coverage,
            "flow_capture_rate": flow_capture_rate,
            "insight_count": insight_count,
        }

    def _build_knowledge_graph(self, components, relationships, understanding_score) -> dict:
        nodes = []
        edges = []
        seen_node_ids = set()

        for comp in components:
            cid = comp["id"]
            if cid not in seen_node_ids:
                seen_node_ids.add(cid)
                importance = comp.get("confidence", 0.5)
                if comp.get("type") in ("controller", "service", "entry_point"):
                    importance = max(importance, 0.8)
                nodes.append({
                    "id": cid,
                    "label": comp.get("name", cid),
                    "type": comp.get("type", "unknown"),
                    "sub_type": comp.get("sub_type", ""),
                    "file_path": comp.get("file_path", ""),
                    "module": comp.get("module", ""),
                    "importance": round(importance, 2),
                    "group": comp.get("type", "unknown"),
                    "details": {
                        "language": comp.get("language", ""),
                        "line": comp.get("line_number", 0),
                        "confidence": comp.get("confidence", 0),
                        "complexity": comp.get("complexity", 0),
                        "purpose": comp.get("purpose", ""),
                    },
                })

        seen_edge_keys = set()
        for rel in relationships:
            src = rel.get("source_id", "")
            tgt = rel.get("target_id", "")
            rtype = rel.get("relationship_type", "related")
            ekey = f"{src}|{tgt}|{rtype}"
            if ekey not in seen_edge_keys and src in seen_node_ids and tgt in seen_node_ids:
                seen_edge_keys.add(ekey)
                edges.append({
                    "source": src,
                    "target": tgt,
                    "relationship": rtype,
                    "weight": rel.get("strength", 1.0),
                    "description": rel.get("description", ""),
                })

        group_counts = defaultdict(int)
        for n in nodes:
            group_counts[n["group"]] += 1

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def _detect_business_components(self, components, all_imports, file_component_map,
                                     call_graph_data) -> list[dict]:
        business_components = []
        seen_bc = set()

        bc_patterns = [
            ("Forecast Engine", "forecast", ["forecast", "predict", "projection", "estimate", "time_series"]),
            ("Prediction Engine", "prediction", ["predict", "inference", "classifier", "regression"]),
            ("Model Training Pipeline", "ml_training", ["train", "training", "fit", "learn"]),
            ("Model Evaluation", "ml_eval", ["evaluate", "eval", "accuracy", "metric", "score"]),
            ("Data Pipeline", "pipeline", ["pipeline", "etl", "process", "transform", "extract"]),
            ("Data Processing Engine", "data_processing", ["pandas", "numpy", "dataframe", "series"]),
            ("Authentication System", "auth", ["auth", "login", "jwt", "oauth", "password"]),
            ("API Gateway", "api_gateway", ["api", "route", "endpoint", "request"]),
            ("Notification Service", "notification", ["notify", "notification", "alert", "email"]),
            ("Cache Manager", "cache", ["cache", "redis", "memcached", "ttl"]),
            ("Database Repository Layer", "repository", ["repository", "dao", "crud", "persist"]),
            ("Background Job Scheduler", "scheduler", ["scheduler", "cron", "celery", "worker", "job"]),
            ("Report Generator", "reporting", ["report", "generate_report", "export"]),
            ("File Upload Handler", "upload", ["upload", "import", "ingest", "file_handler"]),
            ("Configuration Manager", "config", ["config", "setting", "env", "environment"]),
            ("Middleware Pipeline", "middleware", ["middleware", "pipe", "interceptor", "filter"]),
            ("Search Engine", "search", ["search", "index", "query", "lookup", "retrieve"]),
            ("Validation Layer", "validation", ["validate", "sanitize", "check", "verify"]),
        ]

        for comp in components:
            comp_name = comp.get("name", "")
            comp_path = comp.get("file_path", "")
            comp_type = comp.get("type", "")
            imports = all_imports.get(comp_path, [])
            import_text = " ".join(imports).lower()
            search_text = f"{comp_name.lower()} {comp_path.lower()} {import_text}"

            for bc_name, bc_type, keywords in bc_patterns:
                if any(kw in search_text for kw in keywords):
                    bc_key = f"{bc_name}|{comp.get('id', '')}"
                    if bc_key not in seen_bc:
                        seen_bc.add(bc_key)
                        business_components.append({
                            "id": comp["id"],
                            "name": bc_name,
                            "type": bc_type,
                            "file_path": comp_path,
                            "module": comp.get("module", ""),
                            "confidence": comp.get("confidence", 0.7),
                            "description": f"{bc_name} detected in {comp_name} ({comp_path})",
                            "related_components": [],
                        })

        return business_components
