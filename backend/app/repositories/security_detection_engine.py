import ast
import os
import re
import uuid
from pathlib import Path

from app.detection.detector import EXTENSION_LANGUAGE_MAP
from app.repositories.syntax_detection_engine import IGNORED_DIRS, SUPPORTED_LANGUAGES


HARDCODED_PATTERNS: list[tuple[str, str, str, str]] = [
    ("API Key", r"(?i)(api[_-]?key|apikey|api_secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "High", "CWE-798"),
    ("Password", r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"\s]{4,}['\"]", "Critical", "CWE-259"),
    ("Token", r"(?i)(token|access_token|auth_token|secret_token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]", "High", "CWE-798"),
    ("Secret Key", r"(?i)(secret[_-]?key|secret_key|app_secret|consumer_secret)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", "Critical", "CWE-798"),
    ("JWT Secret", r"(?i)(jwt[_-]?secret|jwt_key)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", "Critical", "CWE-798"),
    ("Private Key", r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----", "Critical", "CWE-312"),
]

SQL_INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)execute\s*\(\s*['\"]\s*.*[+%].*request", "SQL Injection Risk", "Critical"),
    (r"(?i)execute\s*\(\s*['\"]\s*.*[+%].*input", "SQL Injection Risk", "Critical"),
    (r"(?i)\.format\(.*request.*SELECT|\.format\(.*input.*SELECT", "SQL Injection Risk", "Critical"),
]

XSS_PATTERNS: list[tuple[str, str, str]] = [
    (r"\.innerHTML\s*=", "Cross-Site Scripting (XSS) via innerHTML", "High"),
    (r"\.outerHTML\s*=", "Cross-Site Scripting (XSS) via outerHTML", "High"),
    (r"dangerouslySetInnerHTML", "Cross-Site Scripting (XSS) via dangerouslySetInnerHTML", "High"),
    (r"document\.write\s*\(", "Cross-Site Scripting (XSS) via document.write", "High"),
    (r"eval\s*\(\s*request", "Cross-Site Scripting (XSS) via eval of user input", "Critical"),
]

COMMAND_INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    (r"os\.system\s*\(", "Command Injection via os.system", "Critical"),
    (r"subprocess\.[a-z]+\s*\(.*shell\s*=\s*True", "Command Injection via subprocess with shell=True", "Critical"),
    (r"exec\s*\(", "Code Injection via exec()", "Critical"),
    (r"eval\s*\(", "Code Injection via eval()", "Critical"),
    (r"popen\s*\(.*shell\s*=\s*True", "Command Injection via popen with shell=True", "Critical"),
    (r"(?i)child_process\.exec\s*\(", "Command Injection via child_process.exec", "Critical"),
    (r"(?i)execSync\s*\(", "Command Injection via execSync", "Critical"),
]

PATH_TRAVERSAL_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)(open|read|write|delete|unlink|rename|remove)\s*\(\s*request", "Path Traversal via direct user input in file operation", "High"),
    (r"(?i)send_file\s*\(.*request", "Path Traversal via send_file with user input", "High"),
    (r"(?i)path\.join\s*\(\s*.*request", "Path Traversal via path.join with user input", "High"),
]

DEBUG_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)DEBUG\s*=\s*True", "Debug Mode Enabled in Production Configuration", "High"),
    (r"(?i)debug\s*=\s*True", "Debug Mode Enabled in Production Code", "High"),
    (r"(?i)ALLOWED_HOSTS\s*=\s*\[\s*['\"]\*['\"]\s*\]", "Permissive ALLOWED_HOSTS Configuration", "High"),
]

INSECURE_COOKIE_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)Set-Cookie\s*:.*(?:\bSecure\b|\bHttpOnly\b)(?!.*\bSecure\b.*\bHttpOnly\b)", "Incomplete Cookie Security Flags", "Medium"),
    (r"(?i)cookie\.secure\s*=\s*False", "Insecure Cookie - Secure flag disabled", "High"),
    (r"(?i)cookie\.httponly\s*=\s*False", "Insecure Cookie - HttpOnly flag disabled", "Medium"),
]

SENSITIVE_DATA_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)(logger|log|console\.log)\s*\.\s*(info|debug|warn|error|log)\s*\(.*(password|secret|token|api_key|ssn|credit_card)", "Sensitive Data Exposure via Logging", "High"),
    (r"(?i)(\.env|env\.)", "Environment Variable Usage - Check for sensitive exposure", "Low"),
]

DESERIALIZATION_PATTERNS: list[tuple[str, str, str]] = [
    (r"pickle\.loads\s*\(", "Unsafe Deserialization via pickle", "Critical"),
    (r"pickle\.load\s*\(", "Unsafe Deserialization via pickle", "Critical"),
    (r"yaml\.load\s*\(.*(?!SafeLoader)", "Unsafe Deserialization via yaml.load", "Critical"),
    (r"marshal\.loads\s*\(", "Unsafe Deserialization via marshal", "Critical"),
]

CSRF_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)@csrf_exempt", "CSRF Protection Disabled on View", "High"),
    (r"(?i)csrf_exempt", "CSRF Protection Exemption Detected", "High"),
    (r"(?i)RequestMethod\.POST.*csrf", "Potential CSRF Vulnerability in POST handler", "Medium"),
]

WEAK_AUTH_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)basic\s*=\s*['\"](\w+):(\w+)['\"]", "Weak Authentication - Basic Auth with hardcoded credentials", "High"),
    (r"(?i)\.authenticate\s*\(\s*['\"][^'\"]+['\"]\s*,\s*['\"][^'\"]+['\"]", "Weak Authentication - Hardcoded credentials in authenticate()", "High"),
]

MISSING_VALIDATION_PATTERNS: list[tuple[str, str, str]] = [
    (r"request\.(GET|POST|form|args|json)\[", "Missing Input Validation - Direct dictionary access on request data", "Medium"),
    (r"request\.(GET|POST|form|args|json)\.get\(", "Missing Input Validation - Unvalidated request data access", "Medium"),
]

UPLOAD_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)upload|file_upload|UPLOAD", "Unsafe File Upload - Potential arbitrary file upload", "Medium"),
]


class SecurityDetectionEngine:

    def analyze(self, workspace_path: Path | None = None) -> dict:
        if not workspace_path or not workspace_path.exists():
            return self._empty_result()

        language_map = self._detect_languages(workspace_path)
        scanned_languages = list(language_map.keys())
        all_results: list[dict] = []
        total_errors = 0
        files_with_errors = 0
        critical = high = medium = low = 0

        for lang, patterns in language_map.items():
            for pattern in patterns:
                for file_path in workspace_path.rglob(pattern):
                    if self._is_ignored(file_path):
                        continue
                    result = self._analyze_file(file_path, lang, workspace_path)
                    all_results.append(result)
                    fc = result["error_count"]
                    if fc > 0:
                        files_with_errors += 1
                    total_errors += fc
                    for e in result["errors"]:
                        s = e["severity"]
                        if s == "Critical":
                            critical += 1
                        elif s == "High":
                            high += 1
                        elif s == "Medium":
                            medium += 1
                        else:
                            low += 1

        security_score = self._calculate_security_score(total_errors, critical, high, medium, low)

        return {
            "session_id": uuid.uuid4().hex,
            "status": "completed",
            "total_errors": total_errors,
            "total_files_scanned": len(all_results),
            "files_with_errors": files_with_errors,
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "results": all_results,
            "scanned_languages": scanned_languages,
            "security_score": security_score,
        }

    def _detect_languages(self, workspace_path: Path) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        for ext, lang in EXTENSION_LANGUAGE_MAP.items():
            if lang not in SUPPORTED_LANGUAGES:
                continue
            matches = list(workspace_path.rglob(f"*{ext}"))
            actual = [m for m in matches if not self._is_ignored(m)]
            if actual:
                found.setdefault(lang, []).append(f"*{ext}")
        return found

    def _is_ignored(self, path: Path) -> bool:
        return any(part in IGNORED_DIRS for part in path.parts)

    def _analyze_file(self, file_path: Path, language: str, workspace: Path) -> dict:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {
                "file_path": str(file_path.relative_to(workspace)),
                "language": language,
                "errors": [], "error_count": 0, "health_score": 100.0,
            }
        rel = str(file_path.relative_to(workspace))
        lines = content.split("\n")
        errors: list[dict] = []

        self._check_hardcoded_secrets(content, rel, lines, errors)
        self._check_sql_injection(content, rel, lines, errors)
        self._check_xss(content, rel, lines, errors)
        self._check_command_injection(content, rel, lines, errors)
        self._check_path_traversal(content, rel, lines, errors)
        self._check_debug_config(content, rel, lines, errors)
        self._check_insecure_cookies(content, rel, lines, errors)
        self._check_sensitive_data(content, rel, lines, errors)
        self._check_deserialization(content, rel, lines, errors)
        self._check_csrf(content, rel, lines, errors)
        self._check_weak_auth(content, rel, lines, errors)
        self._check_missing_validation(content, rel, lines, errors)
        self._check_unsafe_upload(content, rel, lines, errors)

        if language == "Python":
            self._check_python_specific(content, rel, lines, errors)

        errors = self._deduplicate(errors)
        return {
            "file_path": rel,
            "language": language,
            "errors": errors,
            "error_count": len(errors),
            "health_score": max(0.0, 100.0 - len(errors) * 5.0),
        }

    def _check_hardcoded_secrets(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for title, pattern, severity, cwe in HARDCODED_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    f"Hardcoded {title}",
                    f"A hardcoded {title.lower()} was detected on line {line_no}. Never hardcode secrets in source code.",
                    severity, 95, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Hardcoded secrets in source code can be exposed through version control, giving attackers access to systems.",
                    f"Move the {title.lower()} to environment variables or a secure secrets manager.",
                    "security", "", "secrets", severity,
                    f"Exposed credentials may lead to unauthorized system access. ({cwe})",
                ))

    def _check_sql_injection(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in SQL_INJECTION_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Potential SQL injection on line {line_no}. User input is directly concatenated into a SQL query.",
                    severity, 90, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"SQL injection allows attackers to manipulate database queries, potentially stealing or destroying data.",
                    f"Use parameterized queries (e.g., cursor.execute('SELECT * FROM users WHERE id = %s', [user_id])) instead of string formatting.",
                    "security", "", "injection", severity,
                    "SQL injection can lead to data theft, data loss, and complete database compromise. (CWE-89)",
                ))

    def _check_xss(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in XSS_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Cross-Site Scripting vulnerability detected on line {line_no}.",
                    severity, 85, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Cross-Site Scripting (XSS) allows attackers to inject malicious scripts into web pages viewed by other users.",
                    f"Use safe APIs like textContent instead of innerHTML. Use DOMPurify to sanitize HTML. Use React's built-in XSS protection.",
                    "security", "", "xss", severity,
                    "XSS can lead to session hijacking, defacement, and theft of sensitive data. (CWE-79)",
                ))

    def _check_command_injection(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in COMMAND_INJECTION_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Command injection risk on line {line_no}. System commands are executed with shell interpretation.",
                    severity, 95, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Command injection allows attackers to execute arbitrary system commands on the server.",
                    f"Avoid shell=True. Use subprocess.run(['command', 'arg']) without shell=True. Validate and sanitize all user input.",
                    "security", "", "injection", severity,
                    "Remote code execution can lead to full server compromise. (CWE-78)",
                ))

    def _check_path_traversal(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in PATH_TRAVERSAL_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Path traversal vulnerability on line {line_no}. User input is used in file operations without sanitization.",
                    severity, 85, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Path traversal allows attackers to read/write files outside the intended directory, accessing sensitive system files.",
                    f"Validate file paths, use os.path.realpath() to resolve symlinks, and check that the resolved path is within an allowed directory.",
                    "security", "", "traversal", severity,
                    "Unauthorized file access may lead to data exposure and remote code execution. (CWE-22)",
                ))

    def _check_debug_config(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in DEBUG_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Insecure configuration on line {line_no}. Debug or permissive settings detected.",
                    severity, 90, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Debug mode exposes detailed error messages and stack traces to users, revealing application internals. Permissive ALLOWED_HOSTS allows Host Header attacks.",
                    f"Set DEBUG=False in production. Configure ALLOWED_HOSTS to specific domain names instead of '*'.",
                    "security", "", "config", severity,
                    "Information disclosure and Host Header attacks. (CWE-489)",
                ))

    def _check_insecure_cookies(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in INSECURE_COOKIE_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Insecure cookie configuration on line {line_no}.",
                    severity, 80, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Cookies without Secure and HttpOnly flags can be stolen via XSS or man-in-the-middle attacks.",
                    f"Set Secure=True and HttpOnly=True on all cookies that contain sensitive data. For session cookies, also set SameSite=Lax.",
                    "security", "", "config", severity,
                    "Session hijacking and information disclosure. (CWE-1004)",
                ))

    def _check_sensitive_data(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in SENSITIVE_DATA_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Sensitive data exposure on line {line_no}.",
                    severity, 80, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Logging sensitive information (passwords, tokens, credit cards) can expose credentials in log files.",
                    f"Never log sensitive data. Use a logging filter to redact sensitive fields before logging.",
                    "security", "", "exposure", severity,
                    "Exposure of sensitive data in logs accessible to unauthorized personnel. (CWE-532)",
                ))

    def _check_deserialization(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in DESERIALIZATION_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Unsafe deserialization on line {line_no}. Untrusted data may be deserialized.",
                    severity, 95, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Unsafe deserialization can allow attackers to execute arbitrary code by crafting malicious serialized objects.",
                    f"Use JSON or other safe serialization formats instead. If pickle is required, never deserialize untrusted data. Use yaml.safe_load() instead of yaml.load().",
                    "security", "", "deserialization", severity,
                    "Remote code execution via malicious serialized objects. (CWE-502)",
                ))

    def _check_csrf(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in CSRF_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"CSRF protection issue on line {line_no}.",
                    severity, 85, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Cross-Site Request Forgery (CSRF) allows attackers to trick authenticated users into making unintended requests.",
                    f"Ensure CSRF middleware is enabled. Use CSRF tokens in all state-changing forms. Avoid @csrf_exempt decorator.",
                    "security", "", "csrf", severity,
                    "Unauthorized state-changing requests on behalf of authenticated users. (CWE-352)",
                ))

    def _check_weak_auth(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in WEAK_AUTH_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Weak authentication detected on line {line_no}.",
                    severity, 90, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Hardcoded credentials in authentication calls can leak via version control and bypass proper authentication flows.",
                    f"Use environment variables for credentials, implement OAuth/SSO, and avoid hardcoded authentication values.",
                    "security", "", "auth", severity,
                    "Unauthorized access via exposed credentials. (CWE-287)",
                ))

    def _check_missing_validation(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in MISSING_VALIDATION_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Missing input validation on line {line_no}. Request data is used without sanitization.",
                    severity, 70, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Using unsanitized user input directly can lead to injection attacks, data corruption, and security vulnerabilities.",
                    f"Validate and sanitize all input using a schema validator (pydantic, marshmallow, zod) or explicit type casting and length checks.",
                    "security", "", "validation", severity,
                    "Input validation vulnerabilities enable injection attacks. (CWE-20)",
                ))

    def _check_unsafe_upload(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        for pattern, title, severity in UPLOAD_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[:m.start()].count("\n") + 1
                errors.append(self._make_error(
                    title,
                    f"Unsafe file upload pattern detected on line {line_no}.",
                    severity, 70, rel, line_no, m.start() - content[:m.start()].rfind("\n") - 1,
                    self._snippet_for_line(lines, line_no),
                    f"Unrestricted file upload can allow attackers to upload malicious files (e.g., web shells) that can execute code on the server.",
                    f"Validate file type by content (not extension), limit file size, rename uploaded files, store outside web root, and scan for malware.",
                    "security", "", "upload", severity,
                    "Arbitrary file upload may lead to remote code execution. (CWE-434)",
                ))

    def _check_python_specific(self, content: str, rel: str, lines: list[str], errors: list[dict]) -> None:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        errors.append(self._make_error(
                            "Command Injection via subprocess.run",
                            f"subprocess.run() with shell=True on line {node.lineno} allows shell injection.",
                            "Critical", 95, rel, node.lineno, node.col_offset or 0,
                            self._snippet_for_line(lines, node.lineno),
                            f"Using shell=True in subprocess.run() allows attackers to inject shell commands through user input.",
                            f"Use subprocess.run(['command', 'arg'], shell=False) with argument list instead of shell=True.",
                            "security", "", "injection", "Critical",
                            "Remote code execution via shell injection. (CWE-78)",
                        ))
                        break

    # ── Helpers ──

    def _calculate_security_score(self, total: int, critical: int, high: int, medium: int, low: int) -> int:
        score = 100
        score -= critical * 15
        score -= high * 8
        score -= medium * 4
        score -= low * 1
        return max(0, min(100, score))

    def _make_error(self, title: str, desc: str, severity: str, confidence: int,
                    rel: str, line: int, col: int, snippet: str,
                    explanation: str, fix: str, error_type: str, func_name: str,
                    security_category: str, sec_severity: str,
                    security_impact: str) -> dict:
        return {
            "bug_title": title,
            "description": desc,
            "severity": severity,
            "confidence": confidence,
            "language": "",
            "affected_file": rel,
            "line_number": line,
            "column_number": col,
            "code_snippet": snippet,
            "ai_explanation": explanation,
            "suggested_fix": fix,
            "error_type": error_type,
            "function_name": func_name,
            "security_category": security_category,
            "security_impact": security_impact,
        }

    def _snippet_for_line(self, lines: list[str], line_num: int) -> str:
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1][:120]
        return ""

    def _deduplicate(self, errors: list[dict]) -> list[dict]:
        seen = set()
        unique: list[dict] = []
        for e in errors:
            key = (e["bug_title"], e["line_number"], e["affected_file"])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    def _empty_result(self) -> dict:
        return {
            "session_id": uuid.uuid4().hex,
            "status": "unavailable",
            "total_errors": 0, "total_files_scanned": 0, "files_with_errors": 0,
            "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0,
            "results": [], "scanned_languages": [], "security_score": 100,
        }
