import re


class ProjectValidationEngine:
    def validate(
        self,
        analyzer_data: dict | None = None,
        ep_data: dict | None = None,
        arch_data: dict | None = None,
        mod_data: dict | None = None,
        fw_data: dict | None = None,
        ci_data: dict | None = None,
        pi_data: dict | None = None,
        insights_data: dict | None = None,
    ) -> dict:
        merged = self._merge(
            analyzer_data or {},
            ep_data or {},
            arch_data or {},
            mod_data or {},
            fw_data or {},
            ci_data or {},
            pi_data or {},
            insights_data or {},
        )

        checks: list[dict] = []

        checks.append(self._check_framework_entrypoint(merged))
        checks.append(self._check_framework_language(merged))
        checks.append(self._check_readme_consistency(merged))
        checks.append(self._check_frontend_tech(merged))
        checks.append(self._check_database_orm(merged))
        checks.append(self._check_package_manager_deps(merged))
        checks.append(self._check_routes_api_modules(merged))
        checks.append(self._check_templates_frontend(merged))
        checks.append(self._check_docker_support(merged))
        checks.append(self._check_architecture_folders(merged))
        checks.append(self._check_modules_folders(merged))
        checks.append(self._check_config_deps(merged))
        checks.append(self._check_languages_folders(merged))
        checks.append(self._check_project_type_tech(merged))
        checks.append(self._check_entry_point_confidence(merged))

        self_healing = self._run_self_healing(merged, checks)
        report = self._build_report(checks)
        score_data = self._calc_consistency_score(checks)
        recommendations = self._gen_recommendations(checks, score_data)

        passed = sum(1 for c in checks if c["status"] == "passed")
        failed = sum(1 for c in checks if c["status"] == "failed")
        warns = sum(1 for c in checks if c["status"] == "warning")
        crits = sum(1 for c in checks if c["status"] == "error")

        return {
            "consistency_score": score_data["score"],
            "classification": score_data["classification"],
            "passed_checks": passed,
            "failed_checks": failed,
            "warnings": warns,
            "critical_errors": crits,
            "checks": checks,
            "validation_report": report,
            "self_healing": self_healing,
            "recommendations": recommendations,
        }

    @staticmethod
    def _merge(
        analyzer: dict,
        ep: dict,
        arch: dict,
        mod: dict,
        fw: dict,
        ci: dict,
        pi: dict,
        insights: dict,
    ) -> dict:
        result: dict = {}
        result.update(analyzer)
        result.update(ep)
        result.update(arch)
        result.update(mod)
        result.update(fw)
        result.update(ci)
        result.update(pi)
        result.update(insights)
        return result

    @staticmethod
    def _check_framework_entrypoint(data: dict) -> dict:
        modules_involved = ["Framework Intelligence", "Entry Point Detection"]
        fw_data = data.get("technology_stack", {})
        if not fw_data:
            fw_data = data.get("frameworks", [])

        frameworks = []
        if isinstance(fw_data, dict):
            frameworks = [t.get("name", "").lower() for t in fw_data.get("frameworks", [])]
        elif isinstance(fw_data, list):
            frameworks = [f.lower() if isinstance(f, str) else f.get("name", "").lower() for f in fw_data]

        if not frameworks:
            return {
                "check_name": "Framework & Entry Point Consistency",
                "status": "passed",
                "detail": "No frameworks detected — skipping check.",
                "modules_involved": modules_involved,
            }

        tech_stack = data.get("technology_stack", {})
        if isinstance(tech_stack, dict):
            all_frameworks = [t.get("name", "").lower() for t in tech_stack.get("frameworks", [])]
            all_languages = [t.get("name", "").lower() for t in tech_stack.get("languages", [])]
        else:
            all_frameworks = []
            all_languages = []

        ep = data.get("primary_entry_point", {})
        ep_file = (ep.get("entry_file") or "").lower() if isinstance(ep, dict) else ""

        flask_fw = any("flask" in f for f in frameworks) or any("flask" in f for f in all_frameworks)
        django_fw = any("django" in f for f in frameworks) or any("django" in f for f in all_frameworks)
        fastapi_fw = any("fastapi" in f for f in frameworks) or any("fastapi" in f for f in all_frameworks)
        has_python = any("python" in l for l in all_languages)

        if flask_fw and ep_file:
            if "app.py" in ep_file or "wsgi.py" in ep_file or "run.py" in ep_file:
                return {
                    "check_name": "Framework & Entry Point Consistency",
                    "status": "passed",
                    "detail": f"Flask detected with matching entry point ({ep_file}).",
                    "modules_involved": modules_involved,
                }
            return {
                "check_name": "Framework & Entry Point Consistency",
                "status": "warning",
                "detail": f"Flask framework detected but entry point is '{ep_file}'. Expected app.py, wsgi.py, or run.py.",
                "modules_involved": modules_involved,
            }

        if django_fw and ep_file:
            if "manage.py" in ep_file or "wsgi.py" in ep_file:
                return {
                    "check_name": "Framework & Entry Point Consistency",
                    "status": "passed",
                    "detail": f"Django detected with matching entry point ({ep_file}).",
                    "modules_involved": modules_involved,
                }
            return {
                "check_name": "Framework & Entry Point Consistency",
                "status": "warning",
                "detail": f"Django framework detected but entry point is '{ep_file}'. Expected manage.py or wsgi.py.",
                "modules_involved": modules_involved,
            }

        if fastapi_fw or any("fastapi" in f for f in all_frameworks):
            if ep_file and ("main.py" in ep_file or "app.py" in ep_file or "api.py" in ep_file):
                return {
                    "check_name": "Framework & Entry Point Consistency",
                    "status": "passed",
                    "detail": f"FastAPI detected with matching entry point ({ep_file}).",
                    "modules_involved": modules_involved,
                }
            return {
                "check_name": "Framework & Entry Point Consistency",
                "status": "warning",
                "detail": f"FastAPI detected but entry point '{ep_file}' may not be standard.",
                "modules_involved": modules_involved,
            }

        if has_python and not ep_file:
            return {
                "check_name": "Framework & Entry Point Consistency",
                "status": "passed",
                "detail": "Python project detected with no explicit entry point — OK for libraries.",
                "modules_involved": modules_involved,
            }

        if frameworks and not ep_file:
            return {
                "check_name": "Framework & Entry Point Consistency",
                "status": "failed",
                "detail": f"Framework(s) {', '.join(frameworks[:3])} detected but no entry point found.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Framework & Entry Point Consistency",
            "status": "passed",
            "detail": "Framework and entry point are consistent.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_framework_language(data: dict) -> dict:
        modules_involved = ["Framework Intelligence", "Project Summary"]
        tech_stack = data.get("technology_stack", {})
        if isinstance(tech_stack, dict):
            languages = [t.get("name", "").lower() for t in tech_stack.get("languages", [])]
            frameworks = [t.get("name", "").lower() for t in tech_stack.get("frameworks", [])]
        else:
            languages = []
            frameworks = []

        if not frameworks:
            return {
                "check_name": "Framework & Language Alignment",
                "status": "passed",
                "detail": "No frameworks to validate against languages.",
                "modules_involved": modules_involved,
            }

        language_map = {
            "flask": "python",
            "django": "python",
            "fastapi": "python",
            "express": "javascript",
            "react": "javascript",
            "vue": "javascript",
            "angular": "typescript",
            "spring": "java",
            "laravel": "php",
            "rails": "ruby",
            "next": "javascript",
            "nuxt": "javascript",
            "svelte": "javascript",
            "jquery": "javascript",
            "bootstrap": "css",
            "tailwind": "css",
            "asp.net": "csharp",
        }

        mismatches: list[str] = []
        for fw in frameworks:
            expected_lang = None
            for fw_key, lang in language_map.items():
                if fw_key in fw:
                    expected_lang = lang
                    break
            if expected_lang and expected_lang not in languages:
                mismatches.append(f"{fw} expects {expected_lang}")

        if mismatches:
            return {
                "check_name": "Framework & Language Alignment",
                "status": "warning",
                "detail": "; ".join(mismatches),
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Framework & Language Alignment",
            "status": "passed",
            "detail": "All frameworks match detected languages.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_readme_consistency(data: dict) -> dict:
        modules_involved = ["Configuration Intelligence", "Project Summary"]
        config = data.get("config_summary", {})
        has_readme_config = config.get("has_readme", False) if isinstance(config, dict) else False

        insight_readme = False
        ai_summary = data.get("ai_summary", [])
        if ai_summary:
            for line in ai_summary:
                if "readme" in line.lower():
                    insight_readme = True

        if has_readme_config and insight_readme:
            return {
                "check_name": "README Consistency",
                "status": "passed",
                "detail": "README detected consistently across analyzer modules.",
                "modules_involved": modules_involved,
            }

        if has_readme_config:
            return {
                "check_name": "README Consistency",
                "status": "passed",
                "detail": "README file detected in configuration scan.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "README Consistency",
            "status": "passed",
            "detail": "No README detected — this is informational.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_frontend_tech(data: dict) -> dict:
        modules_involved = ["Project Summary", "Framework Intelligence"]
        tech = data.get("technology_stack", {})
        if isinstance(tech, dict):
            languages = [t.get("name", "").lower() for t in tech.get("languages", [])]
            frameworks = [t.get("name", "").lower() for t in tech.get("frameworks", [])]
        else:
            languages = []
            frameworks = []

        folder = data.get("folder_summary", {})
        frontend_count = folder.get("frontend", 0) if isinstance(folder, dict) else 0

        has_html = "html" in languages
        has_css = "css" in languages
        has_js = "javascript" in languages or "typescript" in languages
        has_ts = "typescript" in languages
        has_frontend_fw = any(
            f in str(frameworks) for f in ["react", "vue", "angular", "svelte", "next", "nuxt"]
        )

        if has_html and not has_frontend_fw and frontend_count == 0:
            return {
                "check_name": "Frontend Technology Consistency",
                "status": "warning",
                "detail": "HTML detected but no frontend framework identified and no frontend folders found.",
                "modules_involved": modules_involved,
            }

        if (has_html or has_css or has_js or has_ts) and frontend_count == 0 and not has_frontend_fw:
            lang_names = []
            if has_html: lang_names.append("HTML")
            if has_css: lang_names.append("CSS")
            if has_js: lang_names.append("JavaScript")
            if has_ts: lang_names.append("TypeScript")
            return {
                "check_name": "Frontend Technology Consistency",
                "status": "warning",
                "detail": f"{', '.join(lang_names)} detected but frontend folder count is 0.",
                "modules_involved": modules_involved,
            }

        if frontend_count > 0 and not has_html and not has_css and not has_js:
            return {
                "check_name": "Frontend Technology Consistency",
                "status": "warning",
                "detail": f"Frontend folders found ({frontend_count}) but no frontend languages detected.",
                "modules_involved": modules_involved,
            }

        if has_ts and not has_js:
            return {
                "check_name": "Frontend Technology Consistency",
                "status": "passed",
                "detail": "TypeScript detected as primary frontend language.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Frontend Technology Consistency",
            "status": "passed",
            "detail": "Frontend technologies are consistent.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_database_orm(data: dict) -> dict:
        modules_involved = ["Project Summary", "Framework Intelligence"]
        tech = data.get("technology_stack", {})
        if isinstance(tech, dict):
            databases = [t.get("name", "").lower() for t in tech.get("databases", [])]
        else:
            databases = []

        fw_data = data.get("technology_stack", {})
        orms = []
        if isinstance(fw_data, dict):
            orm_list = fw_data.get("orms", [])
            if orm_list:
                if isinstance(orm_list[0], dict):
                    orms = [o.get("name", "").lower() for o in orm_list]
                elif isinstance(orm_list[0], str):
                    orms = [o.lower() for o in orm_list]

        if not databases and not orms:
            return {
                "check_name": "Database & ORM Consistency",
                "status": "passed",
                "detail": "No database or ORM detected.",
                "modules_involved": modules_involved,
            }

        db_set = set(databases)
        orm_set = set(orms)
        sql_databases = {"sqlite", "mysql", "postgresql", "mariadb", "mssql"}
        orm_to_db = {
            "sqlalchemy": "sqlite",
            "sqlalchemy": "postgresql",
            "sqlalchemy": "mysql",
            "django orm": "sqlite",
            "django orm": "postgresql",
            "django orm": "mysql",
            "prisma": "postgresql",
            "prisma": "mysql",
            "mongoose": "mongodb",
            "typeorm": "postgresql",
            "typeorm": "mysql",
            "entity framework": "mssql",
            "sequelize": "mysql",
            "sequelize": "postgresql",
        }

        if db_set & sql_databases and not orm_set:
            return {
                "check_name": "Database & ORM Consistency",
                "status": "warning",
                "detail": f"Database(s) {', '.join(db_set & sql_databases)} detected but no ORM found.",
                "modules_involved": modules_involved,
            }

        if orm_set and not (db_set & sql_databases):
            if not any(m in str(databases).lower() for m in ["mongodb", "sqlite", "mysql", "postgres"]):
                return {
                    "check_name": "Database & ORM Consistency",
                    "status": "warning",
                    "detail": f"ORM(s) {', '.join(orm_set)} detected but no matching database found.",
                    "modules_involved": modules_involved,
                }

        return {
            "check_name": "Database & ORM Consistency",
            "status": "passed",
            "detail": f"Database(s) and ORM(s) are consistent.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_package_manager_deps(data: dict) -> dict:
        modules_involved = ["Configuration Intelligence", "Project Summary"]
        config = data.get("config_summary", {})
        has_requirements = config.get("has_requirements_txt", False) if isinstance(config, dict) else False
        has_package_json = config.get("has_package_json", False) if isinstance(config, dict) else False
        has_pyproject = config.get("has_pyproject_toml", False) if isinstance(config, dict) else False

        tech = data.get("technology_stack", {})
        pkg_managers = []
        if isinstance(tech, dict):
            pkg_managers = [p.get("name", "").lower() for p in tech.get("package_managers", [])]

        if not pkg_managers and (has_requirements or has_package_json or has_pyproject):
            detail_parts = []
            if has_requirements: detail_parts.append("requirements.txt")
            if has_package_json: detail_parts.append("package.json")
            if has_pyproject: detail_parts.append("pyproject.toml")
            return {
                "check_name": "Package Manager Consistency",
                "status": "failed",
                "detail": f"Dependency file(s) {', '.join(detail_parts)} detected but no package manager identified.",
                "modules_involved": modules_involved,
            }

        if pkg_managers and not has_requirements and not has_package_json and not has_pyproject:
            return {
                "check_name": "Package Manager Consistency",
                "status": "warning",
                "detail": f"Package manager(s) {', '.join(pkg_managers)} detected but no standard dependency files found.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Package Manager Consistency",
            "status": "passed",
            "detail": "Package manager(s) match dependency files.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_routes_api_modules(data: dict) -> dict:
        modules_involved = ["Module Detection", "Framework Intelligence"]
        mod_data = data.get("modules", [])
        if isinstance(mod_data, list):
            module_names = [m.get("module_name", "").lower() if isinstance(m, dict) else str(m).lower() for m in mod_data]
        elif isinstance(mod_data, dict):
            module_names = []
            for m in mod_data.get("modules", []):
                if isinstance(m, dict):
                    module_names.append(m.get("module_name", "").lower())
                elif isinstance(m, str):
                    module_names.append(m.lower())

        fw_frameworks = data.get("frameworks", [])
        if isinstance(fw_frameworks, list):
            fw_names = [f.get("name", "").lower() if isinstance(f, dict) else str(f).lower() for f in fw_frameworks]
        else:
            fw_names = []

        has_router = any("router" in m or "route" in m or "api" in m for m in module_names)
        has_fw_with_routes = any("flask" in f or "fastapi" in f or "express" in f or "django" in f for f in fw_names)

        if has_fw_with_routes and not has_router:
            return {
                "check_name": "Routes & API Modules Consistency",
                "status": "warning",
                "detail": "Framework with routing support detected but no router/api module found.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Routes & API Modules Consistency",
            "status": "passed",
            "detail": "Routes and API modules are consistent.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_templates_frontend(data: dict) -> dict:
        modules_involved = ["Project Summary", "Module Detection"]
        folder = data.get("folder_summary", {})
        frontend_count = folder.get("frontend", 0) if isinstance(folder, dict) else 0

        tech = data.get("technology_stack", {})
        languages = []
        if isinstance(tech, dict):
            languages = [t.get("name", "").lower() for t in tech.get("languages", [])]

        has_template_lang = "html" in languages or "jade" in languages or "handlebars" in languages or "jinja" in languages

        if has_template_lang and frontend_count == 0:
            return {
                "check_name": "Templates & Frontend Consistency",
                "status": "warning",
                "detail": "Template languages detected but no frontend folders found.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Templates & Frontend Consistency",
            "status": "passed",
            "detail": "Templates and frontend are consistent.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_docker_support(data: dict) -> dict:
        modules_involved = ["Configuration Intelligence", "Project Summary"]
        config = data.get("config_summary", {})
        has_dockerfile = config.get("has_dockerfile", False) if isinstance(config, dict) else False
        has_docker_compose = config.get("has_docker_compose", False) if isinstance(config, dict) else False

        docker_val = data.get("docker_validation", {})
        docker_configured = docker_val.get("has_dockerfile", False) if isinstance(docker_val, dict) else False

        if has_dockerfile and not docker_configured:
            return {
                "check_name": "Docker Support Consistency",
                "status": "warning",
                "detail": "Dockerfile detected in config scan but Docker validation shows no support.",
                "modules_involved": modules_involved,
            }

        if has_dockerfile != docker_configured:
            return {
                "check_name": "Docker Support Consistency",
                "status": "warning",
                "detail": "Inconsistent Docker detection across analyzer modules.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Docker Support Consistency",
            "status": "passed",
            "detail": "Docker support is consistent across analyzer modules.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_architecture_folders(data: dict) -> dict:
        modules_involved = ["Architecture Detection", "Project Summary"]
        primary_arch = data.get("primary_architecture", {})
        architecture = (primary_arch.get("architecture") or "").lower() if isinstance(primary_arch, dict) else ""

        folder = data.get("folder_summary", {})
        if not isinstance(folder, dict):
            return {"check_name": "Architecture & Folder Structure Consistency", "status": "passed", "detail": "Skipped — no folder data.", "modules_involved": modules_involved}

        expected_patterns: dict[str, list[str]] = {
            "layered": ["backend", "frontend", "api", "db", "database"],
            "mvc": ["controllers", "models", "views", "templates"],
            "microservices": ["services", "service", "gateway", "api"],
            "clean": ["domain", "application", "infrastructure", "interface"],
            "hexagonal": ["domain", "port", "adapter", "adapters"],
            "monolithic": ["src", "app", "lib", "core", "utils"],
        }

        matched = []
        if architecture:
            patterns = expected_patterns.get(architecture, [])
            folder_keys = [k for k, v in folder.items() if isinstance(v, (int, float)) and v > 0]
            for p in patterns:
                if p in folder_keys:
                    matched.append(p)

            if not matched:
                return {
                    "check_name": "Architecture & Folder Structure Consistency",
                    "status": "warning",
                    "detail": f"Architecture '{architecture}' detected but no matching directories found.",
                    "modules_involved": modules_involved,
                }

        return {
            "check_name": "Architecture & Folder Structure Consistency",
            "status": "passed",
            "detail": "Architecture matches detected folder structure." + (f" (matched: {', '.join(matched)})" if matched else ""),
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_modules_folders(data: dict) -> dict:
        modules_involved = ["Module Detection", "Project Summary"]
        mod_data = data.get("modules", [])
        if isinstance(mod_data, list):
            module_folders = []
            for m in mod_data:
                if isinstance(m, dict):
                    folder_path = m.get("detected_folder", "")
                    if folder_path:
                        module_folders.append(folder_path)
        elif isinstance(mod_data, dict):
            module_folders = []
            for m in mod_data.get("modules", []):
                if isinstance(m, dict):
                    folder_path = m.get("detected_folder", "")
                    if folder_path:
                        module_folders.append(folder_path)
        else:
            module_folders = []

        folder = data.get("folder_summary", {})
        if not isinstance(folder, dict):
            folder = {}

        folder_keys_with_content = [k for k, v in folder.items() if isinstance(v, (int, float)) and v > 0]
        module_based_folders = set()
        for mf in module_folders:
            parts = mf.strip("/").split("/")
            if parts:
                first_part = parts[0].lower()
                for fk in folder_keys_with_content:
                    if re.search(first_part, fk):
                        module_based_folders.add(fk)

        if module_folders and not module_based_folders:
            return {
                "check_name": "Module Detection & Folder Structure Consistency",
                "status": "passed",
                "detail": "Modules detected with folder references but not directly matching summary categories — likely subdirectory structure.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Module Detection & Folder Structure Consistency",
            "status": "passed",
            "detail": "Module detection is consistent with folder structure.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_config_deps(data: dict) -> dict:
        modules_involved = ["Configuration Intelligence", "Project Summary"]

        config = data.get("config_summary", {})
        has_requirements = config.get("has_requirements_txt", False) if isinstance(config, dict) else False
        has_package_json = config.get("has_package_json", False) if isinstance(config, dict) else False
        has_pyproject = config.get("has_pyproject_toml", False) if isinstance(config, dict) else False
        has_gitignore = config.get("has_gitignore", False) if isinstance(config, dict) else False
        has_env = config.get("has_env_example", False) if isinstance(config, dict) else False

        dep_val = data.get("dependency_validation", [])
        if isinstance(dep_val, list) and dep_val:
            high_sev = sum(1 for d in dep_val if isinstance(d, dict) and d.get("severity") == "high")
            if high_sev > 0:
                return {
                    "check_name": "Configuration & Dependency Health",
                    "status": "warning",
                    "detail": f"{high_sev} high-severity dependency issues found in configuration.",
                    "modules_involved": modules_involved,
                }

        if (has_requirements or has_package_json or has_pyproject) and not has_gitignore:
            return {
                "check_name": "Configuration & Dependency Health",
                "status": "warning",
                "detail": "Dependency files exist but .gitignore is missing.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Configuration & Dependency Health",
            "status": "passed",
            "detail": "Configuration and dependencies are consistent.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_languages_folders(data: dict) -> dict:
        modules_involved = ["Project Summary", "Framework Intelligence"]
        tech = data.get("technology_stack", {})
        languages = []
        if isinstance(tech, dict):
            languages = [t.get("name", "").lower() for t in tech.get("languages", [])]

        folder = data.get("folder_summary", {})
        if not isinstance(folder, dict):
            folder = {}

        lang_folder_map = {
            "python": "backend",
            "javascript": "frontend",
            "typescript": "frontend",
            "html": "frontend",
            "css": "frontend",
            "java": "backend",
            "kotlin": "backend",
            "swift": "frontend",
            "go": "backend",
            "rust": "backend",
            "ruby": "backend",
            "php": "backend",
            "csharp": "backend",
            "cpp": "backend",
            "c": "backend",
        }

        mismatches: list[str] = []
        for lang in languages:
            expected_folder = lang_folder_map.get(lang)
            if expected_folder:
                folder_count = folder.get(expected_folder, 0)
                if folder_count == 0:
                    mismatches.append(f"{lang} → expected {expected_folder} folder")

        if len(mismatches) > min(len(languages), 2):
            return {
                "check_name": "Languages & Folder Structure",
                "status": "passed",
                "detail": "Languages found without matching standard folders — likely flat structure.",
                "modules_involved": modules_involved,
            }

        if mismatches:
            return {
                "check_name": "Languages & Folder Structure",
                "status": "warning",
                "detail": "; ".join(mismatches[:3]),
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Languages & Folder Structure",
            "status": "passed",
            "detail": "All languages have matching folder structure.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_project_type_tech(data: dict) -> dict:
        modules_involved = ["Project Summary", "Framework Intelligence"]
        project_type = (data.get("project_type") or "").lower()
        tech = data.get("technology_stack", {})
        languages = []
        if isinstance(tech, dict):
            languages = [t.get("name", "").lower() for t in tech.get("languages", [])]

        type_lang_map = {
            "web": ["html", "javascript", "typescript", "css", "python", "php", "ruby", "java"],
            "api": ["python", "javascript", "typescript", "go", "rust", "java", "kotlin"],
            "library": ["python", "javascript", "typescript", "java", "rust", "go"],
            "cli": ["python", "go", "rust", "javascript", "ruby"],
            "mobile": ["swift", "kotlin", "dart", "javascript", "typescript"],
            "data": ["python", "r", "sql", "julia"],
            "desktop": ["csharp", "cpp", "c", "rust", "java", "python", "swift"],
        }

        expected_langs = type_lang_map.get(project_type, [])
        if expected_langs:
            has_match = any(lang in expected_langs for lang in languages)
            if not has_match:
                return {
                    "check_name": "Project Type & Technology Consistency",
                    "status": "warning",
                    "detail": f"Project classified as '{project_type}' but no matching languages found among {', '.join(languages[:5])}.",
                    "modules_involved": modules_involved,
                }

        return {
            "check_name": "Project Type & Technology Consistency",
            "status": "passed",
            "detail": "Project type aligns with detected technologies.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _check_entry_point_confidence(data: dict) -> dict:
        modules_involved = ["Entry Point Detection", "Framework Intelligence"]
        ep = data.get("primary_entry_point", {})
        if not isinstance(ep, dict) or not ep.get("entry_file"):
            return {
                "check_name": "Entry Point Confidence Validation",
                "status": "passed",
                "detail": "No primary entry point to validate.",
                "modules_involved": modules_involved,
            }

        confidence = ep.get("confidence", 0)
        if confidence < 50:
            return {
                "check_name": "Entry Point Confidence Validation",
                "status": "warning",
                "detail": f"Entry point confidence is low ({confidence}/100). May require manual review.",
                "modules_involved": modules_involved,
            }

        return {
            "check_name": "Entry Point Confidence Validation",
            "status": "passed",
            "detail": f"Entry point confidence is {confidence}/100.",
            "modules_involved": modules_involved,
        }

    @staticmethod
    def _run_self_healing(data: dict, checks: list[dict]) -> list[dict]:
        actions: list[dict] = []
        failed = [c for c in checks if c["status"] == "failed"]
        for check in failed:
            name = check["check_name"]
            if "Package Manager" in name:
                actions.append({
                    "check_name": name,
                    "action": "reconcile",
                    "detail": "Cross-referencing project dependency files against detected package managers.",
                })
            if "Architecture & Folder" in name:
                actions.append({
                    "check_name": name,
                    "action": "reconcile",
                    "detail": "Re-analyzing folder structure against detected architecture patterns.",
                })
            if "Frontend" in name:
                actions.append({
                    "check_name": name,
                    "action": "reconcile",
                    "detail": "Combining language detection and folder analysis to improve frontend detection.",
                })
            if "Database" in name:
                actions.append({
                    "check_name": name,
                    "action": "reconcile",
                    "detail": "Cross-referencing database files and connection strings against ORM detection.",
                })
            if "Docker" in name:
                actions.append({
                    "check_name": name,
                    "action": "reconcile",
                    "detail": "Verifying Dockerfile presence across file scan and Docker validation modules.",
                })
        return actions

    @staticmethod
    def _build_report(checks: list[dict]) -> list[dict]:
        categories: dict[str, list[dict]] = {}
        category_map = {
            "Framework & Entry Point Consistency": "Framework & Entry Points",
            "Framework & Language Alignment": "Framework & Languages",
            "README Consistency": "Documentation",
            "Frontend Technology Consistency": "Frontend Stack",
            "Database & ORM Consistency": "Database & ORM",
            "Package Manager Consistency": "Dependencies",
            "Routes & API Modules Consistency": "Modules & Routes",
            "Templates & Frontend Consistency": "Templates & Frontend",
            "Docker Support Consistency": "Containerization",
            "Architecture & Folder Structure Consistency": "Architecture & Structure",
            "Module Detection & Folder Structure Consistency": "Modules & Structure",
            "Configuration & Dependency Health": "Configuration",
            "Languages & Folder Structure": "Languages & Structure",
            "Project Type & Technology Consistency": "Project Classification",
            "Entry Point Confidence Validation": "Entry Points",
        }

        for check in checks:
            name = check["check_name"]
            cat = category_map.get(name, "General")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(check)

        report = []
        for cat, cat_checks in sorted(categories.items()):
            statuses = [c["status"] for c in cat_checks]
            if "error" in statuses:
                cat_status = "error"
            elif "failed" in statuses:
                cat_status = "failed"
            elif "warning" in statuses:
                cat_status = "warning"
            else:
                cat_status = "passed"
            report.append({
                "category": cat,
                "status": cat_status,
                "checks": cat_checks,
            })
        return report

    @staticmethod
    def _calc_consistency_score(checks: list[dict]) -> dict:
        total = len(checks)
        if total == 0:
            return {"score": 100, "classification": "Excellent"}

        passed = sum(1 for c in checks if c["status"] == "passed")
        warns = sum(1 for c in checks if c["status"] == "warning")
        failed = sum(1 for c in checks if c["status"] == "failed")
        errors = sum(1 for c in checks if c["status"] == "error")

        base = (passed / total) * 100
        penalty = (failed * 20) + (errors * 30) + (warns * 5)
        score = max(0, min(100, int(base - penalty)))

        if score >= 90:
            classification = "Excellent"
        elif score >= 75:
            classification = "Good"
        elif score >= 50:
            classification = "Average"
        else:
            classification = "Poor"

        return {"score": score, "classification": classification}

    @staticmethod
    def _gen_recommendations(checks: list[dict], score_data: dict) -> list[str]:
        recs: list[str] = []
        failed = [c for c in checks if c["status"] == "failed"]
        warns = [c for c in checks if c["status"] == "warning"]
        errors = [c for c in checks if c["status"] == "error"]

        if errors:
            recs.append(f"Resolve {len(errors)} critical error(s) in analyzer consistency.")
        if failed:
            recs.append(f"Fix {len(failed)} failed consistency check(s) to improve analyzer reliability.")
        if warns:
            recs.append(f"Review {len(warns)} warning(s) for potential inconsistencies.")

        for check in failed:
            if "Package Manager" in check["check_name"]:
                recs.append("Ensure package manager is properly detected from dependency files.")
            elif "Architecture" in check["check_name"]:
                recs.append("Verify architecture detection matches the actual project folder layout.")
            elif "Frontend" in check["check_name"]:
                recs.append("Review frontend technology detection — files may be in non-standard locations.")
            elif "Database" in check["check_name"]:
                recs.append("Cross-check database detection against ORM/framework configuration.")

        for check in warns:
            if "confiden" in check["check_name"].lower():
                recs.append("Low entry point confidence — consider adding explicit entry point markers.")
            elif "Docker" in check["check_name"]:
                recs.append("Docker detection is inconsistent — verify Dockerfile and docker-compose placement.")
            elif "README" in check["check_name"]:
                recs.append("Consider adding a README.md for better project documentation.")
            elif "Configuration" in check["check_name"] and "Dep" in check["check_name"]:
                recs.append("Add .gitignore to track dependency files safely.")

        if score_data["score"] < 90:
            recs.append("Run individual analyzer modules again to refresh detection results.")

        return recs[:8]
