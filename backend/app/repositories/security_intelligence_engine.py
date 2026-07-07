import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


SECRET_PATTERNS: list[tuple[str, str, str]] = [
    ("api_key", r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?', "Hardcoded API Key"),
    ("password", r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?[^"\'\s]{4,}["\']?', "Hardcoded Password"),
    ("token", r'(?i)(token|secret|auth_token|access_token|bearer)\s*[:=]\s*["\']?[A-Za-z0-9_\-\.]{8,}["\']?', "Hardcoded Token/Secret"),
    ("aws_key", r'(?i)(AKIA[0-9A-Z]{16})', "AWS Access Key"),
    ("private_key", r'-----BEGIN\s?(RSA|DSA|EC|OPENSSH|PGP)?\s?PRIVATE KEY-----', "Private Key Embedded"),
    ("connection_string", r'(?i)(mongodb|postgresql|mysql|redis)://[^@\s]+:[^@\s]+@', "Database Connection String with Credentials"),
    ("jwt_secret", r'(?i)(jwt[_-]?secret|jwt_secret_key)\s*[:=]\s*["\']?[^"\'\s]{4,}["\']?', "JWT Secret"),
    ("npm_token", r'(?i)(npm_token|npm_auth_token)\s*[:=]\s*["\']?[^"\'\s]+["\']?', "NPM Auth Token"),
    ("ssh_key_path", r'(?i)(identityfile|ssh[_-]?key[_-]?path)\s*[:=]\s*["\']?[^"\'\s]+["\']?', "SSH Key Reference"),
]


INSECURE_PATTERNS: list[tuple[str, str, str]] = [
    ("eval_usage", r'\beval\s*\(', "Unsafe eval() Usage"),
    ("exec_usage", r'\bexec\s*\(', "Unsafe exec() Usage"),
    ("shell_injection", r'(os\.system|subprocess\.(call|Popen|run)|child_process\.exec)\s*\(', "Potential Command Injection"),
    ("sql_injection", r'(execute\s*\(\s*["\']|raw\(|raw_query|cursor\.execute\s*\(\s*f["\']|\.query\s*\(\s*["\'])', "Potential SQL Injection"),
    ("xss_risk", r'(innerHTML\s*=|outerHTML\s*=|dangerouslySetInnerHTML|v-html|__html)', "Potential XSS Risk"),
    ("path_traversal", r'(\.\./|\.\.\\|os\.path\.join\s*\(\s*[^,]+,\s*[^)]*\.\.)', "Potential Path Traversal"),
    ("insecure_deserialization", r'(pickle\.loads|JSON\.parse|yaml\.load\s*\([^)]*Loader)', "Unsafe Deserialization"),
    ("debug_enabled", r'(debug\s*=\s*True|DEBUG\s*=\s*True|debug\s*:\s*true|NODE_ENV\s*=\s*development)', "Debug Mode Enabled"),
]


ENV_SECRET_PATTERNS: list[tuple[str, str, str]] = [
    ("password_env", r'(?i)^(PASSWORD|PASSWD|DB_PASSWORD|DB_PASS|MYSQL_PASSWORD|POSTGRES_PASSWORD|REDIS_PASSWORD)\s*=', "Sensitive Env Variable: password"),
    ("secret_env", r'(?i)^(SECRET|SECRET_KEY|SECRET_TOKEN|API_SECRET|APP_SECRET|JWT_SECRET|SESSION_SECRET)\s*=', "Sensitive Env Variable: secret"),
    ("key_env", r'(?i)^(API_KEY|ACCESS_KEY|PRIVATE_KEY|SSH_KEY|TOKEN|AUTH_TOKEN|BEARER_TOKEN)\s*=', "Sensitive Env Variable: key/token"),
    ("connection_string_env", r'(?i)^(DATABASE_URL|MONGODB_URI|REDIS_URL|CELERY_BROKER|AMQP_URL)\s*=', "Connection String Env Variable"),
]


class SecurityIntelligenceEngine:

    def analyze(self, workspace_path: Path | None = None,
                project_analysis: dict | None = None,
                code_intel: dict | None = None,
                code_quality: dict | None = None,
                file_analysis: dict | None = None,
                dep_analysis: dict | None = None,
                call_graph: dict | None = None,
                semantic: dict | None = None,
                config_intel: dict | None = None,
                recommendations: dict | None = None) -> dict:
        findings, dep_issues = self._detect_all(workspace_path, project_analysis,
                                                 code_intel, code_quality,
                                                 file_analysis, dep_analysis,
                                                 call_graph, semantic,
                                                 config_intel, recommendations)
        score = self._compute_score(findings, dep_issues)
        summary = self._generate_summary(findings, dep_issues, score)
        return {
            "security_score": score,
            "findings": findings,
            "dependency_issues": dep_issues,
            "summary": summary,
        }

    def _detect_all(self, workspace_path, project_analysis, code_intel,
                     code_quality, file_analysis, dep_analysis,
                     call_graph, semantic, config_intel,
                     recommendations) -> tuple[list[dict], list[dict]]:
        findings: list[dict] = []
        dep_issues: list[dict] = []

        self._scan_source_secrets(workspace_path, code_intel, findings)
        self._scan_insecure_patterns(workspace_path, code_intel, findings)
        self._analyze_config_security(config_intel, findings)
        self._analyze_dependency_security(dep_analysis, dep_issues)
        self._analyze_semantic_security(semantic, findings)
        self._analyze_project_security(project_analysis, findings)
        self._analyze_call_graph_security(call_graph, findings)
        self._analyze_quality_security(code_quality, recommendations, findings)

        return findings, dep_issues

    def _get_source_files(self, workspace_path, code_intel) -> dict[str, str]:
        files: dict[str, str] = {}
        if code_intel and isinstance(code_intel, dict):
            raw = code_intel.get("files", code_intel.get("raw_files", []))
            if isinstance(raw, list):
                for f in raw:
                    path = f.get("path", f.get("file", ""))
                    content = f.get("content", f.get("source", ""))
                    if path and content:
                        files[path] = content
        if workspace_path and not files:
            for root, _, filenames in os.walk(workspace_path):
                for fn in filenames:
                    if any(fn.endswith(ext) for ext in
                           (".py", ".js", ".ts", ".jsx", ".tsx", ".java",
                            ".yml", ".yaml", ".json", ".env", ".env.*",
                            ".ini", ".cfg", ".conf", ".xml", ".toml")):
                        fpath = os.path.join(root, fn)
                        try:
                            with open(fpath, "r", errors="ignore") as fh:
                                files[fpath] = fh.read()
                        except Exception:
                            pass
        return files

    def _scan_source_secrets(self, workspace_path, code_intel, findings):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            for stype, pattern, label in SECRET_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    findings.append(self._make_finding(
                        label, stype, "critical",
                        [rel], [],
                        detail=f"Found in {rel} — {len(matches)} occurrence(s)",
                        business="Hardcoded secrets can lead to data breaches and unauthorized access in production",
                        technical="Secret exposed in source code; version control history may contain the plaintext value",
                        fix="Move to environment variables or a secrets manager; rotate the exposed secret immediately"
                    ))

    def _scan_insecure_patterns(self, workspace_path, code_intel, findings):
        files = self._get_source_files(workspace_path, code_intel)
        for fpath, content in files.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath
            for stype, pattern, label in INSECURE_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    sev = "critical" if "sql_injection" in stype or "shell_injection" in stype else "high"
                    findings.append(self._make_finding(
                        label, stype, sev,
                        [rel], [],
                        detail=f"Found in {rel} — {len(matches)} usage(s)",
                        business="Exploitable security weakness may allow attackers to compromise the application",
                        technical=f"Pattern '{pattern}' detected in source code",
                        fix=self._fix_for_type(stype)
                    ))

    def _analyze_config_security(self, config_intel, findings):
        if not config_intel:
            return
        issues = config_intel.get("issues", []) if isinstance(config_intel, dict) else []
        if isinstance(issues, list):
            for iss in issues:
                name = iss if isinstance(iss, str) else iss.get("name", iss.get("file", "Unknown"))
                sev = "medium" if isinstance(iss, str) else iss.get("severity", "medium")
                f = iss if isinstance(iss, str) else iss.get("file", "")
                findings.append(self._make_finding(
                    f"Configuration Security: {name}", "insecure-configuration", sev if sev in ("critical", "high", "medium", "low") else "medium",
                    [f] if f else [],
                    detail=f"Security issue in configuration: {name}",
                    business="Misconfigured settings can lead to security gaps in production",
                    technical="Configuration file contains insecure settings",
                    fix="Review and apply security best practices for configuration files"
                ))

        env = config_intel.get("env_analysis", config_intel.get("environment", {}))
        if isinstance(env, dict):
            env_vars = env.get("variables", env.get("vars", []))
            if isinstance(env_vars, list):
                for var in env_vars:
                    name = var if isinstance(var, str) else var.get("name", "")
                    if isinstance(var, str):
                        for pname, pattern, label in ENV_SECRET_PATTERNS:
                            if re.match(pattern, var):
                                findings.append(self._make_finding(
                                    label, "insecure-env", "medium",
                                    detail=f"Environment variable '{var}' may expose sensitive data",
                                    business="Sensitive environment variables can leak via error pages or logs",
                                    technical="Sensitive data stored in environment without encryption",
                                    fix=f"Ensure '{var}' is properly secured and not exposed in logs"
                                ))

        config_files = config_intel.get("files", []) if isinstance(config_intel, dict) else []
        if isinstance(config_files, list):
            for cf in config_files:
                if isinstance(cf, dict):
                    name = cf.get("name", cf.get("file", ""))
                    if re.search(r'\.env', name):
                        findings.append(self._make_finding(
                            f"Environment File: {name}", "env-file", "low",
                            [name], [],
                            detail="Environment file detected — ensure it is in .gitignore",
                            business="Exposed env files can reveal credentials",
                            technical="Environment file committed to version control",
                            fix="Add to .gitignore and use .env.example for documentation"
                        ))

    def _analyze_dependency_security(self, dep_analysis, dep_issues):
        if not dep_analysis:
            return
        dep_files = dep_analysis.get("files", []) if isinstance(dep_analysis, dict) else []
        if isinstance(dep_files, list):
            for df in dep_files:
                if isinstance(df, dict):
                    name = df.get("name", df.get("package", ""))
                    version = df.get("version", "")
                    if df.get("outdated", False):
                        dep_issues.append(self._make_dep_issue(
                            name, "high" if df.get("severity") == "high" else "medium",
                            f"Outdated package {name}@{version} — newer version available",
                            f"Update {name} to the latest stable version"
                        ))
                    if df.get("deprecated", False):
                        dep_issues.append(self._make_dep_issue(
                            name, "high",
                            f"Deprecated package {name}@{version} — may have unpatched vulnerabilities",
                            f"Replace {name} with actively maintained alternative"
                        ))
                    if df.get("vulnerable", False):
                        dep_issues.append(self._make_dep_issue(
                            name, "critical",
                            f"Known vulnerable dependency {name}@{version}",
                            f"Update {name} immediately to patch known CVEs"
                        ))
                    if df.get("unused", False):
                        dep_issues.append(self._make_dep_issue(
                            name, "low",
                            f"Unused dependency {name} — increases attack surface",
                            f"Remove {name} from dependencies"
                        ))

        total_deps = dep_analysis.get("total_dependencies", dep_analysis.get("total", 0))
        if isinstance(total_deps, (int, float)) and total_deps > 50:
            dep_issues.append(self._make_dep_issue(
                "Large Dependency Footprint", "medium",
                f"Project has {total_deps} dependencies — larger attack surface",
                "Audit dependencies and remove unused packages"
            ))

    def _analyze_semantic_security(self, semantic, findings):
        if not semantic:
            return
        score = semantic.get("understanding_score", {})
        if isinstance(score, dict):
            sc = score.get("security", 50)
            if isinstance(sc, (int, float)):
                if sc < 30:
                    findings.append(self._make_finding(
                        "Security Understanding Gap", "missing-authentication", "high",
                        detail=f"Security understanding score is {sc}% — auth/validation may be missing",
                        business="Incomplete authentication can lead to unauthorized access",
                        technical="Semantic engine detected low security awareness in codebase",
                        fix="Audit authentication, authorization, and input validation across all endpoints"
                    ))
                elif sc < 60:
                    findings.append(self._make_finding(
                        "Moderate Security Understanding", "weak-authentication", "medium",
                        detail=f"Security understanding score is {sc}% — some patterns may be weak",
                        business="Weak authentication increases risk of account compromise",
                        technical="Security patterns are partially implemented",
                        fix="Review authentication flows and harden security controls"
                    ))

    def _analyze_project_security(self, project_analysis, findings):
        if not project_analysis:
            return
        has_https = project_analysis.get("has_https", project_analysis.get("has_ssl", False))
        if not has_https:
            findings.append(self._make_finding(
                "Missing HTTPS Configuration", "missing-https", "high",
                detail="No HTTPS/SSL configuration detected — traffic may be unencrypted",
                business="Unencrypted traffic can be intercepted, leading to data breaches",
                technical="Application should enforce HTTPS for all communications",
                fix="Configure TLS/SSL certificates and enforce HTTPS redirect"
            ))

        has_auth = project_analysis.get("has_authentication", project_analysis.get("has_auth", None))
        if has_auth is False:
            findings.append(self._make_finding(
                "No Authentication Detected", "missing-authentication", "critical",
                detail="Project appears to have no authentication mechanism",
                business="Applications without authentication are publicly accessible",
                technical="No login, token, or API key authentication pattern found",
                fix="Implement authentication (JWT, OAuth, session-based) before production deployment"
            ))

        eps = project_analysis.get("entry_points", [])
        public_eps = [e for e in eps if isinstance(e, dict) and e.get("type") in ("api", "web", "public")]
        if len(public_eps) > 10:
            findings.append(self._make_finding(
                "Many Public Endpoints", "missing-input-validation", "medium",
                [e.get("path", "") for e in public_eps[:5]],
                detail=f"Project has {len(public_eps)} public-facing endpoints — ensure all have input validation",
                business="Unvalidated endpoints are vulnerable to injection attacks",
                technical=f"{len(public_eps)} API/web entry points may lack input sanitization",
                fix="Implement input validation and output encoding on all public endpoints"
            ))

    def _analyze_call_graph_security(self, call_graph, findings):
        if not call_graph:
            return
        issues = call_graph.get("issues", []) if isinstance(call_graph, dict) else []
        if isinstance(issues, list):
            sec_issues = [i for i in issues if isinstance(i, dict) and
                          any(kw in str(i.get("name", "")).lower() or
                              kw in str(i.get("type", "")).lower()
                              for kw in ("auth", "security", "injection", "xss", "csrf"))]
            for iss in sec_issues[:10]:
                name = iss.get("name", "Security Call Graph Issue")
                sev = iss.get("severity", "high")
                desc = iss.get("detail", iss.get("description", ""))
                aff = iss.get("affected_files", iss.get("files", []))
                findings.append(self._make_finding(
                    f"Call Graph Security: {name}", "call-graph-security", sev,
                    aff if isinstance(aff, list) else [],
                    detail=desc or "Security-relevant issue detected in call graph analysis",
                    business="Security issue in execution flow may allow exploitation",
                    technical="Call graph analysis detected a security-relevant pattern",
                    fix="Review the affected execution path and apply security controls"
                ))

    def _analyze_quality_security(self, code_quality, recommendations, findings):
        if code_quality and isinstance(code_quality, dict):
            issues = code_quality.get("issues", [])
            if isinstance(issues, list):
                sec_issues = [i for i in issues if isinstance(i, dict) and
                              i.get("type", "") in ("security", "vulnerability", "secret", "auth")]
                for iss in sec_issues[:15]:
                    findings.append(self._make_finding(
                        iss.get("name", iss.get("title", "Security Quality Issue")),
                        "quality-security",
                        iss.get("severity", "high"),
                        iss.get("files", []) if isinstance(iss.get("files"), list) else [],
                        detail=iss.get("description", iss.get("detail", "")),
                        business="Code quality security issues indicate potential vulnerabilities",
                        technical="Security-related code quality issue detected",
                        fix=iss.get("suggestion", iss.get("recommendation", "Review and fix the security issue"))
                    ))

        if recommendations and isinstance(recommendations, dict):
            recs = recommendations.get("recommendations", [])
            if isinstance(recs, list):
                sec_recs = [r for r in recs if isinstance(r, dict) and
                            r.get("category", r.get("type", "")) in ("security", "vulnerability")]
                for r in sec_recs[:10]:
                    findings.append(self._make_finding(
                        r.get("title", r.get("name", "Security Recommendation")),
                        "quality-security",
                        r.get("severity", r.get("priority", "high")),
                        r.get("affected_files", []),
                        detail=r.get("description", r.get("detail", "")),
                        business="Security recommendation from project insights",
                        technical="AI-generated security recommendation",
                        fix=r.get("suggestion", r.get("recommendation", ""))
                    ))

    def _make_finding(self, name: str, ftype: str, severity: str = "medium",
                      files: list[str] | None = None,
                      functions: list[str] | None = None,
                      detail: str = "",
                      business: str = "",
                      technical: str = "",
                      fix: str = "") -> dict:
        return {
            "name": name,
            "type": ftype,
            "severity": severity,
            "affected_files": files or [],
            "affected_functions": functions or [],
            "detail": detail,
            "business_impact": business,
            "technical_impact": technical,
            "recommended_fix": fix,
        }

    def _make_dep_issue(self, name: str, severity: str = "medium",
                        detail: str = "", recommendation: str = "") -> dict:
        return {
            "name": name,
            "severity": severity,
            "detail": detail,
            "recommendation": recommendation,
        }

    def _fix_for_type(self, stype: str) -> str:
        fixes = {
            "eval_usage": "Replace eval() with safer alternatives like JSON.parse or Function constructor",
            "exec_usage": "Remove exec() usage; use safer language features instead",
            "shell_injection": "Use subprocess with argument lists instead of shell=True; validate all inputs",
            "sql_injection": "Use parameterized queries or an ORM; never concatenate user input into SQL",
            "xss_risk": "Use safe DOM APIs (textContent, innerText) or framework-sanitized templates",
            "path_traversal": "Validate and sanitize file paths; use allow-lists for permitted directories",
            "insecure_deserialization": "Avoid pickle/yaml.load; use safe alternatives with schema validation",
            "debug_enabled": "Disable debug mode in production; use environment-specific configurations",
        }
        return fixes.get(stype, "Review and apply security best practices for the affected code")

    def _compute_score(self, findings, dep_issues) -> dict:
        total = len(findings) + len(dep_issues)
        sev_weights = {"critical": 10, "high": 7, "medium": 4, "low": 2, "informational": 1}
        weighted = sum(sev_weights.get(f.get("severity", "low"), 1) for f in findings)
        weighted += sum(sev_weights.get(d.get("severity", "low"), 1) for d in dep_issues)
        max_possible = total * 10 if total > 0 else 1
        raw_risk = min(weighted / max_possible * 100, 100) if total > 0 else 0

        overall = round(100 - raw_risk, 1)
        health = round(max(0, overall - 10), 1)
        confidence = round(min(len(findings) * 3 + len(dep_issues) * 2, 90), 1)
        readiness = round(max(0, 100 - raw_risk * 0.8), 1)

        if raw_risk >= 60:
            level = "critical"
        elif raw_risk >= 40:
            level = "high"
        elif raw_risk >= 20:
            level = "medium"
        elif raw_risk >= 10:
            level = "low"
        else:
            level = "informational"

        return {
            "overall_security_score": overall,
            "security_health": health,
            "security_confidence": confidence,
            "security_readiness": readiness,
            "risk_level": level,
        }

    def _generate_summary(self, findings, dep_issues, score) -> dict:
        critical = [f for f in findings if f["severity"] == "critical"]
        high = [f for f in findings if f["severity"] == "high"]
        medium = [f for f in findings if f["severity"] == "medium"]
        low = [f for f in findings if f["severity"] == "low"]
        dep_crit = [d for d in dep_issues if d["severity"] == "critical"]
        dep_high = [d for d in dep_issues if d["severity"] == "high"]

        lines = []
        tc = len(critical) + len(dep_crit)
        th = len(high) + len(dep_high)
        if tc > 0:
            lines.append(f"Found {tc} critical security issue(s) requiring immediate remediation.")
        if th > 0:
            lines.append(f"{th} high-risk security finding(s) identified for the next patch cycle.")
        if len(medium) > 0:
            lines.append(f"{len(medium)} medium-risk finding(s) should be addressed in upcoming sprints.")

        if findings:
            by_type: dict[str, int] = {}
            for f in findings:
                by_type[f["type"]] = by_type.get(f["type"], 0) + 1
            if by_type:
                top_type = max(by_type, key=by_type.get)
                lines.append(f"Most common security issue: {top_type.replace('-', ' ').title()} ({by_type[top_type]} occurrence(s)).")

        if dep_issues:
            lines.append(f"Dependency security: {len(dep_issues)} issue(s) found in project dependencies.")

        score_val = score.get("overall_security_score", 0)
        level = score.get("risk_level", "unknown")
        lines.append(f"Overall security score: {score_val}/100 (risk level: {level}).")

        if score_val < 40:
            lines.append("Immediate security audit recommended before any production deployment.")
        elif score_val < 70:
            lines.append("Security improvements recommended as part of regular development cycle.")

        prioritized = []
        for f in sorted(findings + dep_issues, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 4)):
            fix = f.get("recommended_fix", f.get("recommendation", ""))
            prioritized.append(f"[{f['severity'].upper()}] {f['name']}: {fix}")

        return {
            "critical_count": tc,
            "high_count": th,
            "medium_count": len(medium),
            "low_count": len(low),
            "summary_text": " ".join(lines),
            "prioritized_recommendations": prioritized[:25],
        }
