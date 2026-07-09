from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


DEPLOYMENT_FILES = {
    "dockerfile": re.compile(r"^Dockerfile$", re.IGNORECASE),
    "docker_compose": re.compile(r"docker-compose\.(yml|yaml)$", re.IGNORECASE),
    "kubernetes": re.compile(r"^k8s/|kubernetes|\.k8s\.", re.IGNORECASE),
    "helm_chart": re.compile(r"Chart\.yaml$", re.IGNORECASE),
    "github_actions": re.compile(r"\.github/workflows/"),
    "gitlab_ci": re.compile(r"\.gitlab-ci\.yml$", re.IGNORECASE),
    "azure_pipelines": re.compile(r"azure-pipelines\.yml$", re.IGNORECASE),
    "jenkins": re.compile(r"Jenkinsfile$", re.IGNORECASE),
    "render": re.compile(r"render\.yaml$", re.IGNORECASE),
    "railway": re.compile(r"railway\.(json|toml)$", re.IGNORECASE),
    "vercel": re.compile(r"vercel\.(json|toml)$", re.IGNORECASE),
    "netlify": re.compile(r"netlify\.toml$", re.IGNORECASE),
    "deployment_script": re.compile(r"(deploy|release|publish)\.(sh|py|js|yml|yaml)$", re.IGNORECASE),
}

CONFIG_FILES = {
    "env": re.compile(r"\.env$"),
    "env_example": re.compile(r"\.env\.example$"),
    "production_config": re.compile(r"(prod|production)\.(env|json|yml|yaml|config|conf)$", re.IGNORECASE),
    "development_config": re.compile(r"(dev|development)\.(env|json|yml|yaml|config|conf)$", re.IGNORECASE),
    "database_config": re.compile(r"(database|db|datasource)\.(yml|yaml|json|xml|conf|config)$", re.IGNORECASE),
    "cache_config": re.compile(r"(cache|redis|memcache)\.(yml|yaml|json|conf|config)$", re.IGNORECASE),
}

RELEASE_FILES = {
    "versioning": re.compile(r"(version|VERSION|\.version)"),
    "release_notes": re.compile(r"(CHANGELOG|RELEASE|HISTORY|CHANGES)\.(md|txt|rst)$", re.IGNORECASE),
    "build_script": re.compile(r"(build|Makefile|gradlew|mvnw|run-build)\.(sh|js|py)?$", re.IGNORECASE),
    "startup_script": re.compile(r"(start|run|entrypoint|boot)\.(sh|js|py)$", re.IGNORECASE),
    "shutdown_script": re.compile(r"(stop|shutdown|graceful|terminate)\.(sh|js|py)$", re.IGNORECASE),
    "health_check": re.compile(r"(health|healthcheck|healthz|readyz|livez)\.(py|js|go|sh)$", re.IGNORECASE),
}

OBSERVABILITY_PATTERNS = {
    "logging": re.compile(r"(import logging|from logging|Logger|log\.(info|error|warn|debug)|console\.log|winston|pino|log4j|logback)", re.IGNORECASE),
    "monitoring": re.compile(r"(prometheus|grafana|datadog|newrelic|cloudwatch|statsd|metrics)", re.IGNORECASE),
    "metrics": re.compile(r"(metrics|meter|Counter|Histogram|Gauge|metric\.(inc|set|observe)|@Timed|timed\()", re.IGNORECASE),
    "tracing": re.compile(r"(opentelemetry|jaeger|zipkin|datadog.*trace|trace\.(start|end|span))", re.IGNORECASE),
    "health_endpoint": re.compile(r"(/health|/healthz|/readyz|/livez|health_check|healthcheck)", re.IGNORECASE),
}

ENV_VAR_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*\s*=")

ERROR_HANDLING_PATTERNS = [
    ("try_catch", re.compile(r"try\s*\{|except\s+\w+"), "Try-catch / try-except blocks"),
    ("error_middleware", re.compile(r"(error.?handler|error.?middleware|exception.?handler|app\.error_handler|@app\.exception_handler)"), "Error handling middleware"),
    ("validation", re.compile(r"@validated|validate|joi\.|zod\.|pydantic|marshmallow|serializers\."), "Input validation"),
    ("custom_errors", re.compile(r"class\s+\w+(Error|Exception)\s*[:\(]"), "Custom exception classes"),
]

SECRET_MANAGEMENT_PATTERNS = [
    re.compile(r"(vault|secretsmanager|secret.?manager|keyvault|aws\.secretsmanager)", re.IGNORECASE),
    re.compile(r"(dotenv|python-dotenv|load_dotenv|environs|decouple)", re.IGNORECASE),
    re.compile(r"(crypt|encrypt|decrypt|cipher|ciphertext)", re.IGNORECASE),
]


class ProductionReadinessEngine:

    def analyze(
        self,
        workspace_path: Path | None = None,
        project_analysis: dict | None = None,
        code_intel: dict | None = None,
        code_quality: dict | None = None,
        file_analysis: dict | None = None,
        dep_analysis: dict | None = None,
        call_graph: dict | None = None,
        semantic: dict | None = None,
        config_intel: dict | None = None,
        recommendations: dict | None = None,
        security_intel: dict | None = None,
        performance_intel: dict | None = None,
        maintainability_intel: dict | None = None,
        documentation_intel: dict | None = None,
        test_intel: dict | None = None,
    ) -> dict:
        findings: list[dict] = []

        deployment = self._detect_deployment(workspace_path)
        config_val = self._analyze_config(workspace_path, config_intel)
        release = self._detect_release_readiness(workspace_path)
        observability = self._detect_observability(workspace_path)

        findings.extend(self._evaluate_architecture(project_analysis, semantic))
        findings.extend(self._eval_security(security_intel))
        findings.extend(self._eval_performance(performance_intel))
        findings.extend(self._eval_dependency_health(dep_analysis))
        findings.extend(self._eval_config_health(config_intel, config_val))
        findings.extend(self._eval_environment(config_intel, config_val))
        findings.extend(self._eval_logging(observability))
        findings.extend(self._eval_monitoring(observability))
        findings.extend(self._eval_error_handling(workspace_path, code_intel))
        findings.extend(self._eval_exception_handling(workspace_path, code_intel))
        findings.extend(self._eval_documentation(documentation_intel, workspace_path))
        findings.extend(self._eval_testing(test_intel))
        findings.extend(self._eval_cicd(deployment))

        category_scores = self._compute_category_scores(findings)
        overall_score = self._compute_overall_score(
            category_scores, deployment, config_val, release, observability
        )
        summary = self._generate_summary(findings, overall_score, category_scores)

        return {
            "production_score": overall_score,
            "category_scores": category_scores,
            "findings": findings,
            "deployment": deployment,
            "config_validation": config_val,
            "release_readiness": release,
            "observability": observability,
            "summary": summary,
        }

    def _detect_deployment(self, workspace_path: Path | None) -> dict:
        result = {
            "has_dockerfile": False,
            "has_docker_compose": False,
            "has_kubernetes": False,
            "has_helm_charts": False,
            "has_github_actions": False,
            "has_gitlab_ci": False,
            "has_azure_pipelines": False,
            "has_jenkins": False,
            "has_render_config": False,
            "has_railway_config": False,
            "has_vercel_config": False,
            "has_netlify_config": False,
            "has_deployment_scripts": False,
            "detected_platforms": [],
        }
        if not workspace_path or not workspace_path.exists():
            return result

        platforms = []
        for root, _dirs, files in os.walk(workspace_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, workspace_path)
                for key, pattern in DEPLOYMENT_FILES.items():
                    if pattern.search(rel):
                        if key == "dockerfile":
                            result["has_dockerfile"] = True
                        elif key == "docker_compose":
                            result["has_docker_compose"] = True
                        elif key == "kubernetes":
                            result["has_kubernetes"] = True
                        elif key == "helm_chart":
                            result["has_helm_charts"] = True
                        elif key == "github_actions":
                            result["has_github_actions"] = True
                        elif key == "gitlab_ci":
                            result["has_gitlab_ci"] = True
                        elif key == "azure_pipelines":
                            result["has_azure_pipelines"] = True
                        elif key == "jenkins":
                            result["has_jenkins"] = True
                        elif key == "render":
                            result["has_render_config"] = True
                        elif key == "railway":
                            result["has_railway_config"] = True
                        elif key == "vercel":
                            result["has_vercel_config"] = True
                        elif key == "netlify":
                            result["has_netlify_config"] = True
                        elif key == "deployment_script":
                            result["has_deployment_scripts"] = True

        platform_map = [
            ("has_dockerfile", "Docker"),
            ("has_docker_compose", "Docker Compose"),
            ("has_kubernetes", "Kubernetes"),
            ("has_helm_charts", "Helm Charts"),
            ("has_github_actions", "GitHub Actions"),
            ("has_gitlab_ci", "GitLab CI"),
            ("has_azure_pipelines", "Azure Pipelines"),
            ("has_jenkins", "Jenkins"),
            ("has_render_config", "Render"),
            ("has_railway_config", "Railway"),
            ("has_vercel_config", "Vercel"),
            ("has_netlify_config", "Netlify"),
        ]
        for key, label in platform_map:
            if result[key]:
                platforms.append(label)
        result["detected_platforms"] = platforms
        return result

    def _analyze_config(self, workspace_path: Path | None, config_intel: dict | None) -> dict:
        result = {
            "has_environment_variables": False,
            "has_env_file": False,
            "has_production_config": False,
            "has_development_config": False,
            "has_secret_management": False,
            "has_database_config": False,
            "has_cache_config": False,
            "env_var_count": 0,
        }
        if workspace_path and workspace_path.exists():
            for root, _dirs, files in os.walk(workspace_path):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    rel = os.path.relpath(fpath, workspace_path)
                    for key, pattern in CONFIG_FILES.items():
                        if pattern.search(rel):
                            if key == "env":
                                result["has_env_file"] = True
                                self._count_env_vars(fpath, result)
                            elif key == "env_example":
                                result["has_environment_variables"] = True
                            elif key == "production_config":
                                result["has_production_config"] = True
                            elif key == "development_config":
                                result["has_development_config"] = True
                            elif key == "database_config":
                                result["has_database_config"] = True
                            elif key == "cache_config":
                                result["has_cache_config"] = True

        if config_intel:
            env = config_intel.get("env_analysis", config_intel.get("environment", {}))
            if isinstance(env, dict):
                vars_list = env.get("variables", env.get("vars", []))
                if isinstance(vars_list, list) and vars_list:
                    result["has_environment_variables"] = True
                    result["env_var_count"] = max(result["env_var_count"], len(vars_list))

            config_files = config_intel.get("files", [])
            if isinstance(config_files, list):
                for cf in config_files:
                    if isinstance(cf, dict):
                        name = cf.get("name", cf.get("file", ""))
                        if re.search(r"\.env$", name):
                            result["has_env_file"] = True

            sec_analysis = config_intel.get("security_analysis", config_intel.get("secrets", {}))
            if isinstance(sec_analysis, dict):
                has_secrets = sec_analysis.get("has_secrets", sec_analysis.get("findings", []))
                if has_secrets:
                    result["has_secret_management"] = True

        result["has_secret_management"] = (result["has_env_file"] or result["has_environment_variables"])
        if workspace_path and workspace_path.exists():
            for root, _dirs, files in os.walk(workspace_path):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                            for pat in SECRET_MANAGEMENT_PATTERNS:
                                if pat.search(content):
                                    result["has_secret_management"] = True
                                    break
                    except Exception:
                        pass

        return result

    def _count_env_vars(self, fpath: str, result: dict) -> None:
        try:
            with open(fpath, "r", errors="ignore") as f:
                for line in f:
                    if ENV_VAR_PATTERN.match(line):
                        result["env_var_count"] += 1
                        result["has_environment_variables"] = True
        except Exception:
            pass

    def _detect_release_readiness(self, workspace_path: Path | None) -> dict:
        result = {
            "has_versioning": False,
            "has_release_notes": False,
            "has_build_scripts": False,
            "has_startup_scripts": False,
            "has_shutdown_handling": False,
            "has_health_checks": False,
        }
        if not workspace_path or not workspace_path.exists():
            return result

        for root, _dirs, files in os.walk(workspace_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, workspace_path)
                for key, pattern in RELEASE_FILES.items():
                    if pattern.search(rel):
                        if key == "versioning":
                            result["has_versioning"] = True
                        elif key == "release_notes":
                            result["has_release_notes"] = True
                        elif key == "build_script":
                            result["has_build_scripts"] = True
                        elif key == "startup_script":
                            result["has_startup_scripts"] = True
                        elif key == "shutdown_script":
                            result["has_shutdown_handling"] = True
                        elif key == "health_check":
                            result["has_health_checks"] = True

        if result["has_startup_scripts"]:
            pass
        pkg_files = ["package.json", "pyproject.toml", "Cargo.toml", "build.gradle", "pom.xml"]
        if workspace_path:
            for pf in pkg_files:
                if (workspace_path / pf).exists():
                    result["has_build_scripts"] = True
                    break

        return result

    def _detect_observability(self, workspace_path: Path | None) -> dict:
        result = {
            "has_logging": False,
            "has_monitoring": False,
            "has_metrics": False,
            "has_tracing": False,
            "has_health_endpoints": False,
        }
        if not workspace_path or not workspace_path.exists():
            return result

        for root, _dirs, files in os.walk(workspace_path):
            for fname in files:
                if not any(fname.endswith(ext) for ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb", ".php")):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                        for key, pattern in OBSERVABILITY_PATTERNS.items():
                            if pattern.search(content):
                                if key == "logging":
                                    result["has_logging"] = True
                                elif key == "monitoring":
                                    result["has_monitoring"] = True
                                elif key == "metrics":
                                    result["has_metrics"] = True
                                elif key == "tracing":
                                    result["has_tracing"] = True
                                elif key == "health_endpoint":
                                    result["has_health_endpoints"] = True
                except Exception:
                    pass

        return result

    def _evaluate_architecture(
        self, project_analysis: dict | None, semantic: dict | None
    ) -> list[dict]:
        findings: list[dict] = []
        if not project_analysis:
            findings.append(self._make_finding(
                "Architecture Not Analyzed", "architecture", "high",
                detail="No architecture analysis available - cannot assess architectural readiness",
                deployment_impact="Architecture issues may cause deployment failures at scale",
                business_impact="Unclear architecture increases risk of production incidents",
                recommendation="Run architecture analysis to identify potential production risks"
            ))
            return findings

        arch = project_analysis.get("architecture", "")
        if arch and arch.lower() in ("unknown", "none", "monolithic"):
            findings.append(self._make_finding(
                "Monolithic Architecture Detected", "architecture", "medium",
                detail=f"Project architecture identified as '{arch}' which may limit scalability",
                deployment_impact="Scaling monolithic applications requires vertical scaling",
                business_impact="May increase deployment complexity and downtime risk",
                recommendation="Consider microservices or modular architecture for better scalability"
            ))

        eps = project_analysis.get("entry_points", [])
        if isinstance(eps, list) and len(eps) > 0:
            if any(e.get("type") in ("api", "web") for e in eps if isinstance(e, dict)):
                pass
        else:
            findings.append(self._make_finding(
                "No Entry Points Detected", "architecture", "high",
                detail="Application entry points could not be identified",
                deployment_impact="Deployment configuration may be incorrect without known entry points",
                business_impact="Application may not start correctly in production",
                recommendation="Define clear entry points for production deployment"
            ))

        return findings

    def _eval_security(self, security_intel: dict | None) -> list[dict]:
        findings: list[dict] = []
        if not security_intel:
            findings.append(self._make_finding(
                "Security Analysis Missing", "security", "critical",
                detail="No security intelligence available to assess production security readiness",
                deployment_impact="Security vulnerabilities could be exploited in production",
                business_impact="Data breaches can lead to regulatory fines and reputational damage",
                recommendation="Run security intelligence analysis before production deployment"
            ))
            return findings

        score = security_intel.get("security_score", {})
        if isinstance(score, dict):
            overall = score.get("overall_security_score", 0)
            risk = score.get("risk_level", "unknown")
            if overall < 40:
                findings.append(self._make_finding(
                    "Critical Security Risk", "security", "critical",
                    detail=f"Security score is {overall}/100 (risk: {risk}) - immediate remediation required",
                    deployment_impact="Security vulnerabilities may be exploited immediately upon deployment",
                    business_impact="High risk of data breach, compliance violation, and financial loss",
                    recommendation="Remediate all critical and high security findings before deployment"
                ))
            elif overall < 70:
                findings.append(self._make_finding(
                    "Moderate Security Concerns", "security", "high",
                    detail=f"Security score is {overall}/100 (risk: {risk}) - improvements needed",
                    deployment_impact="Security gaps may be exploited in production environment",
                    business_impact="Increased risk of security incidents",
                    recommendation="Address high-severity security findings before production deployment"
                ))

        s_findings = security_intel.get("findings", [])
        if isinstance(s_findings, list):
            critical = [f for f in s_findings if isinstance(f, dict) and f.get("severity") == "critical"]
            high = [f for f in s_findings if isinstance(f, dict) and f.get("severity") == "high"]
            if len(critical) > 0:
                findings.append(self._make_finding(
                    f"{len(critical)} Critical Security Findings", "security", "critical",
                    affected_files=[f.get("affected_files", []) for f in critical[:3] if isinstance(f.get("affected_files"), list)][0] if critical else [],
                    detail=f"{len(critical)} critical security issues must be resolved before production",
                    deployment_impact="Critical vulnerabilities are exploitable in production",
                    business_impact="Immediate security risk requiring remediation",
                    recommendation="Fix all critical security findings before deploying to production"
                ))
            if len(high) > 0:
                findings.append(self._make_finding(
                    f"{len(high)} High-Risk Security Findings", "security", "high",
                    detail=f"{len(high)} high-severity security issues should be addressed",
                    deployment_impact="Security vulnerabilities may be exploited",
                    business_impact="Potential for security incidents in production",
                    recommendation="Address high-severity findings as part of pre-deployment checklist"
                ))

        dep_issues = security_intel.get("dependency_issues", [])
        if isinstance(dep_issues, list):
            vuln_deps = [d for d in dep_issues if isinstance(d, dict) and d.get("severity") in ("critical", "high")]
            if vuln_deps:
                findings.append(self._make_finding(
                    f"{len(vuln_deps)} Vulnerable Dependencies", "security", "high",
                    detail=f"Dependencies with known vulnerabilities detected",
                    deployment_impact="Vulnerable dependencies can be exploited in production",
                    business_impact="Supply chain security risk",
                    recommendation="Update or replace vulnerable dependencies before deployment"
                ))

        return findings

    def _eval_performance(self, performance_intel: dict | None) -> list[dict]:
        findings: list[dict] = []
        if not performance_intel:
            findings.append(self._make_finding(
                "Performance Analysis Missing", "performance", "medium",
                detail="No performance intelligence available to assess production performance readiness",
                deployment_impact="Performance bottlenecks may cause production outages under load",
                business_impact="Poor performance leads to user dissatisfaction and revenue loss",
                recommendation="Run performance intelligence analysis to identify bottlenecks"
            ))
            return findings

        score = performance_intel.get("performance_score", {})
        if isinstance(score, dict):
            overall = score.get("overall_performance_score", score.get("performance_score", 0))
            if overall < 40:
                findings.append(self._make_finding(
                    "Critical Performance Issues", "performance", "high",
                    detail=f"Performance score is {overall}/100 - significant bottlenecks detected",
                    deployment_impact="Application may fail under production load",
                    business_impact="Poor user experience and potential revenue impact",
                    recommendation="Address critical performance bottlenecks before deployment"
                ))
            elif overall < 70:
                findings.append(self._make_finding(
                    "Moderate Performance Concerns", "performance", "medium",
                    detail=f"Performance score is {overall}/100 - optimization recommended",
                    deployment_impact="Performance may degrade under production traffic",
                    business_impact="May not meet SLA requirements",
                    recommendation="Optimize performance bottlenecks identified by the analysis"
                ))

        p_findings = performance_intel.get("findings", performance_intel.get("bottlenecks", []))
        if isinstance(p_findings, list):
            critical = [f for f in p_findings if isinstance(f, dict) and f.get("severity") in ("critical", "high")]
            if len(critical) > 3:
                findings.append(self._make_finding(
                    f"Multiple Performance Bottlenecks ({len(critical)})", "performance", "high",
                    detail=f"{len(critical)} critical or high-severity performance issues identified",
                    deployment_impact="Multiple bottlenecks may cause cascading failures in production",
                    business_impact="System may not meet performance requirements",
                    recommendation="Address top performance bottlenecks before production deployment"
                ))

        return findings

    def _eval_dependency_health(self, dep_analysis: dict | None) -> list[dict]:
        findings: list[dict] = []
        if not dep_analysis:
            findings.append(self._make_finding(
                "Dependency Analysis Missing", "dependency", "high",
                detail="No dependency analysis available to assess dependency health",
                deployment_impact="Unhealthy dependencies can cause production failures",
                business_impact="Supply chain and stability risks",
                recommendation="Run dependency analysis to identify potential issues"
            ))
            return findings

        metrics = dep_analysis.get("metrics", dep_analysis.get("summary", {}))
        if isinstance(metrics, dict):
            broken = metrics.get("broken_dependencies", metrics.get("broken", 0))
            circular = metrics.get("circular_dependencies", metrics.get("circular", 0))
            unused = metrics.get("unused_imports", metrics.get("unused", 0))
            coupling = metrics.get("coupling_score", metrics.get("coupling", 0))
            total_deps = metrics.get("total_imports", metrics.get("total", 0))

            if isinstance(broken, (int, float)) and broken > 0:
                findings.append(self._make_finding(
                    f"Broken Dependencies ({broken})", "dependency", "critical",
                    detail=f"{broken} broken import(s) detected - application may fail to build or run",
                    deployment_impact="Build failures in production CI/CD pipeline",
                    business_impact="Deployment blocked until dependencies are resolved",
                    recommendation=f"Fix all {broken} broken import(s) before production deployment"
                ))

            if isinstance(circular, (int, float)) and circular > 0:
                findings.append(self._make_finding(
                    f"Circular Dependencies ({circular})", "dependency", "high",
                    detail=f"{circular} circular dependenc{'y' if circular == 1 else 'ies'} detected",
                    deployment_impact="May cause runtime errors and memory issues in production",
                    business_impact="Increased maintenance complexity and potential production issues",
                    recommendation="Refactor to remove circular dependencies"
                ))

            if isinstance(unused, (int, float)) and unused > 0:
                findings.append(self._make_finding(
                    f"Unused Dependencies ({unused})", "dependency", "medium",
                    detail=f"{unused} unused import(s) increase attack surface and build size",
                    deployment_impact="Unnecessary dependencies increase deployment size and attack surface",
                    business_impact="Increased security risk and maintenance burden",
                    recommendation="Remove unused dependencies"
                ))

            if isinstance(coupling, (int, float)) and coupling > 70:
                findings.append(self._make_finding(
                    f"High Module Coupling ({coupling}%)", "dependency", "medium",
                    detail=f"Module coupling score of {coupling}% indicates tight interdependence",
                    deployment_impact="Changes in one module may cause unexpected failures in production",
                    business_impact="Increased regression risk and maintenance cost",
                    recommendation="Reduce module coupling through refactoring"
                ))

            if isinstance(total_deps, (int, float)) and total_deps > 100:
                findings.append(self._make_finding(
                    f"Large Dependency Footprint ({total_deps})", "dependency", "low",
                    detail=f"Project has {total_deps} total imports - consider optimization",
                    deployment_impact="Larger deployment artifacts and longer build times",
                    business_impact="Increased maintenance overhead",
                    recommendation="Audit and reduce dependency footprint"
                ))

        dep_files = dep_analysis.get("files", [])
        if isinstance(dep_files, list):
            outdated = [d for d in dep_files if isinstance(d, dict) and d.get("outdated")]
            deprecated = [d for d in dep_files if isinstance(d, dict) and d.get("deprecated")]
            if outdated:
                findings.append(self._make_finding(
                    f"Outdated Packages ({len(outdated)})", "dependency", "medium",
                    detail=f"{len(outdated)} package(s) are outdated and may have unpatched issues",
                    deployment_impact="Outdated packages may have known vulnerabilities",
                    business_impact="Security and stability risks from outdated code",
                    recommendation="Update outdated packages to latest stable versions"
                ))
            if deprecated:
                findings.append(self._make_finding(
                    f"Deprecated Packages ({len(deprecated)})", "dependency", "high",
                    detail=f"{len(deprecated)} package(s) are deprecated and should be replaced",
                    deployment_impact="Deprecated packages may stop working or have unpatched vulnerabilities",
                    business_impact="Long-term maintenance and security risks",
                    recommendation="Replace deprecated packages with actively maintained alternatives"
                ))

        return findings

    def _eval_config_health(self, config_intel: dict | None, config_val: dict) -> list[dict]:
        findings: list[dict] = []
        if not config_intel:
            findings.append(self._make_finding(
                "Configuration Analysis Missing", "configuration", "high",
                detail="No configuration intelligence available to assess configuration health",
                deployment_impact="Misconfigured settings can cause production failures",
                business_impact="Configuration-related downtime and security risks",
                recommendation="Run configuration intelligence analysis"
            ))
            return findings

        health = config_intel.get("health", {})
        if isinstance(health, dict):
            score = health.get("score", health.get("overall", 0))
            if isinstance(score, (int, float)):
                if score < 40:
                    findings.append(self._make_finding(
                        "Critical Configuration Issues", "configuration", "high",
                        detail=f"Configuration health score is {score}/100 - significant issues detected",
                        deployment_impact="Misconfiguration may cause production outages",
                        business_impact="Increased operational risk and potential security incidents",
                        recommendation="Address all configuration issues before production deployment"
                    ))
                elif score < 70:
                    findings.append(self._make_finding(
                        "Configuration Improvements Needed", "configuration", "medium",
                        detail=f"Configuration health score is {score}/100 - some issues found",
                        deployment_impact="Configuration gaps may cause issues in production",
                        business_impact="Operational inefficiencies and potential incidents",
                        recommendation="Review and address configuration findings"
                    ))

        if not config_val.get("has_production_config"):
            findings.append(self._make_finding(
                "Production Configuration Missing", "configuration", "high",
                detail="No production-specific configuration detected",
                deployment_impact="Application may use development settings in production",
                business_impact="Security and stability risks from inappropriate production settings",
                recommendation="Create production-specific configuration for all environments"
            ))

        if not config_val.get("has_database_config"):
            findings.append(self._make_finding(
                "Database Configuration Missing", "configuration", "high",
                detail="No database configuration file detected",
                deployment_impact="Database connection settings may not be production-ready",
                business_impact="Risk of database connectivity issues in production",
                recommendation="Configure database connection pooling, timeouts, and failover"
            ))

        return findings

    def _eval_environment(self, config_intel: dict | None, config_val: dict) -> list[dict]:
        findings: list[dict] = []
        if not config_val.get("has_environment_variables"):
            findings.append(self._make_finding(
                "Environment Variables Not Configured", "environment", "high",
                detail="No environment variables detected - application may use hardcoded values",
                deployment_impact="Production requires environment-specific configuration",
                business_impact="Cannot deploy to multiple environments without env vars",
                recommendation="Implement environment variable management for all environments"
            ))
        else:
            count = config_val.get("env_var_count", 0)
            if count > 0 and count < 5:
                findings.append(self._make_finding(
                    f"Limited Environment Variables ({count})", "environment", "medium",
                    detail=f"Only {count} environment variable(s) detected - configuration may be incomplete",
                    deployment_impact="Missing environment variables may cause runtime failures",
                    business_impact="Incomplete configuration for production deployment",
                    recommendation="Review and complete environment variable configuration"
                ))

        if not config_val.get("has_env_file") and not config_val.get("has_environment_variables"):
            findings.append(self._make_finding(
                "Missing .env Configuration", "environment", "high",
                detail="No .env file or environment variable management detected",
                deployment_impact="Sensitive configuration values may be hardcoded",
                business_impact="Security and deployment flexibility concerns",
                recommendation="Create .env.example and implement environment variable management"
            ))

        if config_val.get("has_env_file") and not config_val.get("has_secret_management"):
            findings.append(self._make_finding(
                "Basic Secret Management Only", "environment", "medium",
                detail="Environment files detected but no advanced secret management",
                deployment_impact="Secrets may not be properly managed in production",
                business_impact="Risk of credential exposure",
                recommendation="Implement proper secret management (vault, secrets manager, etc.)"
            ))

        return findings

    def _eval_logging(self, observability: dict) -> list[dict]:
        findings: list[dict] = []
        if not observability.get("has_logging"):
            findings.append(self._make_finding(
                "Logging Not Detected", "logging", "high",
                detail="No logging framework detected - production debugging will be difficult",
                deployment_impact="Cannot diagnose production issues without logs",
                business_impact="Increased mean time to resolution for production incidents",
                recommendation="Implement structured logging across the application"
            ))
        else:
            pass
        return findings

    def _eval_monitoring(self, observability: dict) -> list[dict]:
        findings: list[dict] = []
        if not observability.get("has_monitoring"):
            findings.append(self._make_finding(
                "Monitoring Not Detected", "monitoring", "high",
                detail="No monitoring solution detected - production visibility is limited",
                deployment_impact="Cannot detect production issues proactively",
                business_impact="Increased downtime and slower incident response",
                recommendation="Implement monitoring with alerting for production systems"
            ))
        if not observability.get("has_metrics"):
            findings.append(self._make_finding(
                "Application Metrics Not Detected", "monitoring", "medium",
                detail="No metrics collection detected - performance visibility is limited",
                deployment_impact="Cannot identify performance trends or anomalies",
                business_impact="Reactive rather than proactive operations",
                recommendation="Implement metrics collection (Prometheus, statsd, etc.)"
            ))
        if not observability.get("has_tracing"):
            findings.append(self._make_finding(
                "Distributed Tracing Not Detected", "monitoring", "medium",
                detail="No distributed tracing detected - request flow visibility is limited",
                deployment_impact="Difficult to debug performance issues across services",
                business_impact="Slower root cause analysis for production issues",
                recommendation="Consider implementing distributed tracing for complex deployments"
            ))
        if not observability.get("has_health_endpoints"):
            findings.append(self._make_finding(
                "Health Check Endpoints Missing", "monitoring", "high",
                detail="No health check endpoints detected - orchestration platforms cannot verify app health",
                deployment_impact="Load balancers and orchestrators cannot perform health checks",
                business_impact="Increased risk of serving traffic to unhealthy instances",
                recommendation="Implement /health, /readyz, and /livez endpoints"
            ))
        return findings

    def _eval_error_handling(self, workspace_path: Path | None, code_intel: dict | None) -> list[dict]:
        findings: list[dict] = []
        found_any = False
        if workspace_path and workspace_path.exists():
            for root, _dirs, files in os.walk(workspace_path):
                for fname in files:
                    if not any(fname.endswith(ext) for ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs")):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                            for _name, pattern, _label in ERROR_HANDLING_PATTERNS:
                                if pattern.search(content):
                                    found_any = True
                                    break
                    except Exception:
                        pass
                    if found_any:
                        break
                if found_any:
                    break

        if not found_any:
            findings.append(self._make_finding(
                "Error Handling Not Detected", "error_handling", "high",
                detail="No try-catch or error handling patterns detected in source code",
                deployment_impact="Unhandled errors will cause production crashes",
                business_impact="Increased application downtime and poor user experience",
                recommendation="Implement comprehensive error handling across all application layers"
            ))

        return findings

    def _eval_exception_handling(self, workspace_path: Path | None, code_intel: dict | None) -> list[dict]:
        findings: list[dict] = []
        found_custom = False
        if workspace_path and workspace_path.exists():
            for root, _dirs, files in os.walk(workspace_path):
                for fname in files:
                    if not any(fname.endswith(ext) for ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".java")):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                            if re.search(r"class\s+\w+(Error|Exception)\s*[:\(]", content):
                                found_custom = True
                                break
                    except Exception:
                        pass
                if found_custom:
                    break

        if not found_custom:
            findings.append(self._make_finding(
                "Custom Exception Classes Missing", "exception_handling", "medium",
                detail="No custom exception classes detected - using generic exceptions",
                deployment_impact="Difficult to distinguish and handle specific error conditions in production",
                business_impact="Slower debugging and incident response",
                recommendation="Define custom exception classes for different error scenarios"
            ))

        return findings

    def _eval_documentation(self, documentation_intel: dict | None, workspace_path: Path | None) -> list[dict]:
        findings: list[dict] = []
        if not documentation_intel:
            has_readme = False
            if workspace_path and workspace_path.exists():
                for root, _dirs, files in os.walk(workspace_path):
                    for fname in files:
                        if re.match(r"^README\.(md|rst|txt)$", fname, re.IGNORECASE):
                            has_readme = True
                            break
                    if has_readme:
                        break
            if not has_readme:
                findings.append(self._make_finding(
                    "README Not Found", "documentation", "high",
                    detail="No README file detected - essential documentation is missing",
                    deployment_impact="Operations team lacks deployment and operational documentation",
                    business_impact="Slower onboarding and incident response",
                    recommendation="Create comprehensive README with setup, deployment, and operations guide"
                ))
            findings.append(self._make_finding(
                "Documentation Analysis Missing", "documentation", "medium",
                detail="No documentation intelligence available for detailed assessment",
                deployment_impact="Missing API docs and deployment guides",
                business_impact="Knowledge gaps for production operations",
                recommendation="Run documentation intelligence analysis to identify gaps"
            ))
            return findings

        score = documentation_intel.get("documentation_score", documentation_intel.get("score", {}))
        if isinstance(score, dict):
            overall = score.get("overall_documentation_score", score.get("overall", 0))
            if overall < 40:
                findings.append(self._make_finding(
                    "Insufficient Documentation", "documentation", "high",
                    detail=f"Documentation score is {overall}/100 - critical documentation gaps",
                    deployment_impact="Missing operational documentation for production deployment",
                    business_impact="Operational knowledge gaps increase incident risk",
                    recommendation="Create deployment guides, API docs, and operational runbooks"
                ))
            elif overall < 70:
                findings.append(self._make_finding(
                    "Documentation Gaps Detected", "documentation", "medium",
                    detail=f"Documentation score is {overall}/100 - improvements needed",
                    deployment_impact="Some operational procedures may be undocumented",
                    business_impact="Efficiency loss during operations",
                    recommendation="Fill documentation gaps identified by the analysis"
                ))

        summary = documentation_intel.get("summary", {})
        if isinstance(summary, dict):
            pct = summary.get("documented_percentage", summary.get("coverage", 0))
            if isinstance(pct, (int, float)) and pct < 50:
                findings.append(self._make_finding(
                    f"Low Documentation Coverage ({pct}%)", "documentation", "medium",
                    detail=f"Only {pct}% of code is documented",
                    deployment_impact="Unclear codebase for operations and maintenance team",
                    business_impact="Higher maintenance costs and onboarding time",
                    recommendation="Improve documentation coverage for all critical modules"
                ))

        return findings

    def _eval_testing(self, test_intel: dict | None) -> list[dict]:
        findings: list[dict] = []
        if not test_intel:
            findings.append(self._make_finding(
                "Test Analysis Missing", "testing", "high",
                detail="No test intelligence available to assess testing readiness",
                deployment_impact="Untested code may fail in production",
                business_impact="Increased risk of production defects",
                recommendation="Run test intelligence analysis and implement comprehensive testing"
            ))
            return findings

        score = test_intel.get("test_score", {})
        if isinstance(score, dict):
            overall = score.get("overall_test_score", score.get("test_score", 0))
            coverage = score.get("test_coverage", 0)
            if overall < 30:
                findings.append(self._make_finding(
                    "Critical Testing Gaps", "testing", "critical",
                    detail=f"Test score is {overall}/100 with {coverage}% coverage",
                    deployment_impact="High risk of undetected defects in production",
                    business_impact="Frequent production incidents and hotfixes",
                    recommendation="Implement unit, integration, and API tests before production deployment"
                ))
            elif overall < 60:
                findings.append(self._make_finding(
                    "Testing Improvements Needed", "testing", "high",
                    detail=f"Test score is {overall}/100 with {coverage}% coverage",
                    deployment_impact="Moderate risk of undetected defects",
                    business_impact="Quality concerns for production release",
                    recommendation="Increase test coverage to at least 70% before production deployment"
                ))
            elif overall < 80:
                findings.append(self._make_finding(
                    "Adequate but Limited Testing", "testing", "medium",
                    detail=f"Test score is {overall}/100 with {coverage}% coverage",
                    deployment_impact="Some risk remaining for edge cases",
                    business_impact="Generally acceptable for production with monitoring",
                    recommendation="Consider adding integration and E2E tests for critical paths"
                ))

        summary = test_intel.get("summary", {})
        if isinstance(summary, dict):
            untested_files = summary.get("untested_files", 0)
            if isinstance(untested_files, (int, float)) and untested_files > 10:
                findings.append(self._make_finding(
                    f"Many Untested Files ({untested_files})", "testing", "high",
                    detail=f"{untested_files} files have no test coverage",
                    deployment_impact="Untested code paths may fail in production",
                    business_impact="Higher defect rate in production",
                    recommendation=f"Add tests for {untested_files} uncovered files before deployment"
                ))

            missing_cases = summary.get("missing_test_cases", test_intel.get("missing_test_cases", []))
            if isinstance(missing_cases, list) and len(missing_cases) > 5:
                findings.append(self._make_finding(
                    f"Missing Test Cases ({len(missing_cases)})", "testing", "medium",
                    detail=f"{len(missing_cases)} missing test cases identified",
                    deployment_impact="Edge cases may not be covered",
                    business_impact="Potential regression risks",
                    recommendation="Address high-priority missing test cases before production deployment"
                ))

        return findings

    def _eval_cicd(self, deployment: dict) -> list[dict]:
        findings: list[dict] = []
        platforms = deployment.get("detected_platforms", [])
        if not platforms:
            findings.append(self._make_finding(
                "CI/CD Not Configured", "cicd", "high",
                detail="No CI/CD configuration detected - deployments will require manual processes",
                deployment_impact="Manual deployments are error-prone and time-consuming",
                business_impact="Slower release cycles and higher risk of deployment errors",
                recommendation="Implement CI/CD pipeline using GitHub Actions, GitLab CI, or similar"
            ))
        else:
            has_ci = any(p in platforms for p in ("GitHub Actions", "GitLab CI", "Azure Pipelines", "Jenkins"))
            has_cd = any(p in platforms for p in ("Docker", "Docker Compose", "Kubernetes", "Render", "Railway", "Vercel", "Netlify"))
            if not has_ci:
                findings.append(self._make_finding(
                    "CI Pipeline Missing", "cicd", "high",
                    detail=f"Deployment platforms detected ({', '.join(platforms)}) but no CI pipeline found",
                    deployment_impact="No automated testing before deployment",
                    business_impact="Quality issues may reach production",
                    recommendation="Add CI pipeline to automatically test before deployment"
                ))
            if not has_cd:
                findings.append(self._make_finding(
                    "CD Pipeline Incomplete", "cicd", "medium",
                    detail=f"CI detected but no containerization or platform deployment config",
                    deployment_impact="Deployments require manual intervention",
                    business_impact="Slower time-to-deployment",
                    recommendation="Implement automated deployment pipeline"
                ))

        if not deployment.get("has_dockerfile"):
            findings.append(self._make_finding(
                "Dockerfile Not Found", "cicd", "medium",
                detail="No Dockerfile detected - containerization is recommended for production",
                deployment_impact="Inconsistent environments between development and production",
                business_impact="Configuration drift and deployment issues",
                recommendation="Containerize the application with Docker for consistent deployments"
            ))

        if not deployment.get("has_health_checks") and not deployment.get("has_docker_compose"):
            pass

        return findings

    def _compute_category_scores(self, findings: list[dict]) -> dict:
        categories = {
            "architecture_readiness": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "security_readiness": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "performance_readiness": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "dependency_health": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "configuration_health": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "environment_configuration": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "logging_configuration": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "monitoring_support": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "error_handling": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "exception_handling": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "documentation_readiness": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "testing_readiness": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "cicd_readiness": {"weight": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
        }

        cat_map = {
            "architecture": "architecture_readiness",
            "security": "security_readiness",
            "performance": "performance_readiness",
            "dependency": "dependency_health",
            "configuration": "configuration_health",
            "environment": "environment_configuration",
            "logging": "logging_configuration",
            "monitoring": "monitoring_support",
            "error_handling": "error_handling",
            "exception_handling": "exception_handling",
            "documentation": "documentation_readiness",
            "testing": "testing_readiness",
            "cicd": "cicd_readiness",
        }

        for f in findings:
            cat = f.get("category", "")
            key = cat_map.get(cat)
            if key and key in categories:
                sev = f.get("severity", "low")
                categories[key]["weight"] += 1
                if sev in categories[key]:
                    categories[key][sev] += 1

        result = {}
        for key, data in categories.items():
            score = 100.0
            if data["weight"] > 0:
                penalty = (data["critical"] * 25 + data["high"] * 15 + data["medium"] * 8 + data["low"] * 3)
                score = max(0, 100 - penalty)
            result[key] = round(score, 1)

        return result

    def _compute_overall_score(
        self,
        category_scores: dict,
        deployment: dict,
        config_val: dict,
        release: dict,
        observability: dict,
    ) -> dict:
        cat_values = [v for v in category_scores.values() if isinstance(v, (int, float))]
        avg_cat = sum(cat_values) / max(len(cat_values), 1)

        deployment_bonus = 0
        platforms = deployment.get("detected_platforms", [])
        if len(platforms) >= 2:
            deployment_bonus = 10
        elif len(platforms) == 1:
            deployment_bonus = 5
        if deployment.get("has_dockerfile"):
            deployment_bonus += 5

        config_bonus = 0
        if config_val.get("has_secret_management"):
            config_bonus += 5
        if config_val.get("has_production_config"):
            config_bonus += 5
        if config_val.get("has_environment_variables"):
            config_bonus += 3

        release_bonus = 0
        if release.get("has_release_notes"):
            release_bonus += 3
        if release.get("has_build_scripts"):
            release_bonus += 3
        if release.get("has_health_checks"):
            release_bonus += 4
        if release.get("has_startup_scripts"):
            release_bonus += 3

        observability_bonus = 0
        if observability.get("has_logging"):
            observability_bonus += 4
        if observability.get("has_monitoring"):
            observability_bonus += 4
        if observability.get("has_health_endpoints"):
            observability_bonus += 4

        total_bonus = min(deployment_bonus + config_bonus + release_bonus + observability_bonus, 30)
        overall = min(100, avg_cat + total_bonus)

        deployment_readiness = min(100, (avg_cat + deployment_bonus)) if category_scores.get("cicd_readiness", 0) > 0 else min(100, (avg_cat * 0.7 + deployment_bonus))
        operational = min(100, (avg_cat + observability_bonus + config_bonus))
        maint_readiness = min(100, (category_scores.get("documentation_readiness", 0) + category_scores.get("testing_readiness", 0)) / 2 + 10)

        return {
            "overall_production_score": round(overall, 1),
            "deployment_readiness": round(deployment_readiness, 1),
            "operational_readiness": round(operational, 1),
            "maintainability_readiness": round(maint_readiness, 1),
            "ai_confidence": round(min(95, avg_cat * 0.9 + 10), 1),
        }

    def _generate_summary(
        self, findings: list[dict], score: dict, category_scores: dict
    ) -> dict:
        overall = score.get("overall_production_score", 0)
        critical = [f for f in findings if f.get("severity") == "critical"]
        high = [f for f in findings if f.get("severity") == "high"]
        medium = [f for f in findings if f.get("severity") == "medium"]
        low = [f for f in findings if f.get("severity") == "low"]

        if overall >= 85 and len(critical) == 0 and len(high) == 0:
            classification = "Production Ready"
        elif overall >= 65 and len(critical) == 0:
            classification = "Nearly Ready"
        elif overall >= 40:
            classification = "Needs Improvement"
        elif overall >= 20:
            classification = "High Risk"
        else:
            classification = "Not Ready"

        lines = []
        if classification == "Production Ready":
            lines.append("Project is deployment ready. All production readiness criteria are met.")
        elif classification == "Nearly Ready":
            lines.append("Project is nearly ready for production. Address remaining high-severity items.")
        elif classification == "Needs Improvement":
            lines.append("Project requires significant improvements before production deployment.")
        elif classification == "High Risk":
            lines.append("Project is at high risk for production deployment. Critical issues must be resolved.")
        else:
            lines.append("Project is not ready for production deployment. Major gaps identified.")

        if critical:
            lines.append(f"{len(critical)} critical blocker(s) preventing production deployment identified.")
        if high:
            lines.append(f"{len(high)} high-severity issue(s) should be addressed before deployment.")

        cat_map = {
            "architecture_readiness": "Architecture",
            "security_readiness": "Security",
            "performance_readiness": "Performance",
            "dependency_health": "Dependencies",
            "configuration_health": "Configuration",
            "environment_configuration": "Environment Config",
            "logging_configuration": "Logging",
            "monitoring_support": "Monitoring",
            "error_handling": "Error Handling",
            "exception_handling": "Exception Handling",
            "documentation_readiness": "Documentation",
            "testing_readiness": "Testing",
            "cicd_readiness": "CI/CD",
        }
        low_cats = [cat_map.get(k, k) for k, v in category_scores.items() if isinstance(v, (int, float)) and v < 40]
        if low_cats:
            lines.append(f"Areas needing improvement: {', '.join(low_cats)}.")
        med_cats = [cat_map.get(k, k) for k, v in category_scores.items() if isinstance(v, (int, float)) and 40 <= v < 70]
        if med_cats:
            lines.append(f"Areas with moderate readiness: {', '.join(med_cats)}.")

        prioritized = []
        for f in sorted(
            findings,
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 4),
        ):
            rec = f.get("ai_recommendation", "")
            if rec:
                prioritized.append(f"[{f['severity'].upper()}] {f['name']}: {rec}")

        return {
            "classification": classification,
            "total_findings": len(findings),
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "low_count": len(low),
            "summary_text": " ".join(lines),
            "prioritized_recommendations": prioritized[:20],
        }

    def _make_finding(
        self,
        name: str,
        category: str = "",
        severity: str = "medium",
        affected_files: list[str] | None = None,
        affected_components: list[str] | None = None,
        detail: str = "",
        deployment_impact: str = "",
        business_impact: str = "",
        recommendation: str = "",
    ) -> dict:
        return {
            "name": name,
            "category": category,
            "severity": severity,
            "affected_files": affected_files or [],
            "affected_components": affected_components or [],
            "detail": detail,
            "deployment_impact": deployment_impact,
            "business_impact": business_impact,
            "ai_recommendation": recommendation,
        }
