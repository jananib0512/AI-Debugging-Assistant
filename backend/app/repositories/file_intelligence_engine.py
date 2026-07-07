import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from app.repositories.source_code_intelligence_engine import (
    EXTENSION_LANGUAGE_MAP,
    IGNORED_DIRS,
    IGNORED_FILES,
    SUPPORTED_EXTENSIONS,
)


def _compute_complexity(lines: list[str], language: str) -> int:
    complexity = 1
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        if re.search(r"\b(if|else if|elif)\b", lower):
            complexity += 1
        if re.search(r"\b(for|while)\b", lower):
            complexity += 1
        if re.search(r"\bcase\b", lower) and ":" in stripped:
            complexity += 1
        if re.search(r"\bcatch\b", lower):
            complexity += 1
        if re.search(r"\b&&\b|\b\|\|\b", lower):
            complexity += 1
        if language == "Python" and re.search(r"\bexcept\b", lower):
            complexity += 1
    return complexity


def _count_comments_blanks(lines: list[str], language: str) -> tuple[int, int, int]:
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_block = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
            continue
        if in_block:
            comment_lines += 1
            if "*/" in stripped:
                in_block = False
            continue
        is_comment = False
        if language == "Python":
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                comment_lines += 1
                is_comment = True
                if stripped.startswith('"""') and stripped.count('"""') == 1:
                    in_block = True
                elif stripped.startswith("'''") and stripped.count("'''") == 1:
                    in_block = True
        elif language in ("HTML",):
            if stripped.startswith("<!--"):
                comment_lines += 1
                is_comment = True
                if "-->" not in stripped:
                    in_block = True
        elif language in ("CSS",):
            if stripped.startswith("/*"):
                comment_lines += 1
                is_comment = True
                if "*/" not in stripped:
                    in_block = True
        else:
            if stripped.startswith("//"):
                comment_lines += 1
                is_comment = True
            elif stripped.startswith("/*"):
                comment_lines += 1
                is_comment = True
                if "*/" not in stripped:
                    in_block = True
            elif stripped.startswith("#"):
                comment_lines += 1
                is_comment = True
        if not is_comment:
            code_lines += 1
    return code_lines, comment_lines, blank_lines


def _classify_file(file_name: str, rel_path: str, language: str, content: str) -> str:
    lower_name = file_name.lower()
    path_lower = rel_path.lower()

    test_patterns = ["test_", "_test", ".spec.", ".test.", "__tests__", "tests/", "spec/"]
    for p in test_patterns:
        if p in path_lower:
            return "Testing"

    if lower_name in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
        return "Configuration"
    if lower_name in (".gitignore", ".env.example", ".editorconfig", ".prettierrc"):
        return "Configuration"

    if language in ("JSON", "YAML", "TOML", "INI", "XML"):
        return "Configuration"

    if lower_name.endswith(".md") or lower_name.endswith(".markdown") or lower_name.endswith(".rst"):
        return "Documentation"

    if path_lower.startswith("docs/") or "/docs/" in path_lower:
        return "Documentation"

    if path_lower.startswith("assets/") or "/assets/" in path_lower or path_lower.startswith("static/"):
        return "Assets"

    if path_lower.startswith("scripts/") or "/scripts/" in path_lower:
        return "Scripts"

    if language in ("JavaScript", "TypeScript", "JSX", "TSX"):
        if "/components/" in path_lower or "components/" in path_lower:
            return "Frontend"
        if "/pages/" in path_lower or "/views/" in path_lower or "/screens/" in path_lower:
            return "Frontend"
        if "/api/" in path_lower or "/services/" in path_lower:
            return "API"
        if "/utils/" in path_lower or "/helpers/" in path_lower or "/lib/" in path_lower:
            return "Utility"
        if "/hooks/" in path_lower:
            return "Frontend"
        if "/store/" in path_lower or "/redux/" in path_lower or "/state/" in path_lower:
            return "Frontend"
        return "Frontend"

    if language == "Python":
        if "/models/" in path_lower or "models.py" in lower_name:
            return "Model"
        if "/views/" in path_lower or "views.py" in lower_name:
            return "Frontend"
        if "/controllers/" in path_lower or "controller" in lower_name:
            return "Controller"
        if "/services/" in path_lower or "service" in lower_name:
            return "Service"
        if "/api/" in path_lower or "/routes/" in path_lower:
            return "API"
        if "/utils/" in path_lower or "/helpers/" in path_lower:
            return "Utility"
        if "/config/" in path_lower:
            return "Configuration"
        if "/db/" in path_lower or "/database/" in path_lower:
            return "Database"
        if "/ml/" in path_lower or "/ai/" in path_lower or "/model/" in path_lower:
            return "Machine Learning"
        if "/tests/" in path_lower:
            return "Testing"
        return "Backend"

    if language in ("Java", "Kotlin"):
        if "controller" in lower_name:
            return "Controller"
        if "service" in lower_name:
            return "Service"
        if "model" in lower_name or "entity" in lower_name or "domain" in lower_name:
            return "Model"
        if "repository" in lower_name or "dao" in lower_name:
            return "Database"
        if "config" in lower_name:
            return "Configuration"
        if "util" in lower_name:
            return "Utility"
        if "application" in lower_name or "main" in lower_name:
            return "Backend"
        return "Backend"

    if language in ("Go", "Rust"):
        if "/api/" in path_lower:
            return "API"
        if "/cmd/" in path_lower:
            return "Backend"
        if "/pkg/" in path_lower:
            return "Utility"
        if "/internal/" in path_lower:
            return "Backend"
        return "Backend"

    if language in ("C", "C++", "C#"):
        if path_lower.endswith(".h") or path_lower.endswith(".hpp") or path_lower.endswith(".hxx"):
            return "Utility"
        return "Backend"

    if language == "HTML":
        return "Frontend"

    if language == "CSS":
        return "Frontend"

    return "Backend"


def _generate_tags(file_name: str, rel_path: str, language: str, content: str) -> list[str]:
    tags: list[str] = []
    path_lower = rel_path.lower()
    content_lower = content.lower()

    if "auth" in path_lower or "login" in path_lower or "oauth" in path_lower:
        tags.append("Authentication")
    if "config" in path_lower:
        tags.append("Configuration")
    if "util" in path_lower or "helper" in path_lower:
        tags.append("Utilities")
    if "test" in path_lower:
        tags.append("Testing")
    if "model" in path_lower or "entity" in path_lower:
        tags.append("Data")
    if "api" in path_lower or "route" in path_lower or "endpoint" in path_lower:
        tags.append("API")
    if "db" in path_lower or "database" in path_lower or "sql" in path_lower or "migration" in path_lower:
        tags.append("Database")
    if "ml" in path_lower or "model" in path_lower or "train" in path_lower or "predict" in path_lower:
        tags.append("Machine Learning")
    if "middleware" in path_lower:
        tags.append("Middleware")
    if "docker" in path_lower:
        tags.append("Container")
    if "deploy" in path_lower:
        tags.append("Deployment")
    if "security" in path_lower or "crypto" in path_lower:
        tags.append("Security")
    if "cache" in path_lower:
        tags.append("Caching")
    if "queue" in path_lower or "kafka" in path_lower or "rabbit" in path_lower:
        tags.append("Messaging")
    if "logging" in path_lower or "log" in path_lower:
        tags.append("Logging")
    if "email" in path_lower or "mail" in path_lower:
        tags.append("Email")
    if "notification" in path_lower:
        tags.append("Notifications")
    if "scheduler" in path_lower or "cron" in path_lower:
        tags.append("Scheduling")
    if "graphql" in content_lower or path_lower == "graphql":
        tags.append("GraphQL")
    if "rest" in content_lower:
        tags.append("REST")
    if "schema" in path_lower:
        tags.append("Schema")
    if "validation" in path_lower or "validate" in path_lower:
        tags.append("Validation")

    if "forecast" in content_lower or "forecasting" in path_lower:
        if "Machine Learning" not in tags:
            tags.append("Forecasting")
    if "visual" in path_lower or "chart" in path_lower or "plot" in path_lower:
        tags.append("Visualization")
    if "prediction" in content_lower or "predict" in content_lower:
        tags.append("Prediction")

    if not tags:
        tags.append(language)

    return tags


def _detect_issues(
    file_name: str,
    rel_path: str,
    total_lines: int,
    code_lines: int,
    blank_lines: int,
    comment_lines: int,
    complexity: int,
    maintainability: float,
    content_hash: str,
    all_hashes: dict[str, list[str]],
) -> list[dict]:
    issues: list[dict] = []

    if total_lines > 500:
        issues.append({
            "type": "large_file",
            "severity": "medium",
            "description": f"File is large ({total_lines} lines). Consider splitting into smaller modules.",
            "reason": "Large files are harder to maintain and understand.",
            "suggested_fix": "Split the file into multiple smaller files based on logical boundaries.",
        })

    if total_lines == 0:
        issues.append({
            "type": "empty_file",
            "severity": "low",
            "description": "File is empty.",
            "reason": "Empty files serve no purpose and clutter the codebase.",
            "suggested_fix": "Remove the file or add content.",
        })
    elif code_lines == 0:
        issues.append({
            "type": "no_code",
            "severity": "low",
            "description": "File contains no executable code.",
            "reason": "Files without code may be unintended or unnecessary.",
            "suggested_fix": "Verify the file is needed and add code or remove it.",
        })

    if total_lines > 0 and comment_lines == 0:
        issues.append({
            "type": "missing_documentation",
            "severity": "low",
            "description": "File has no comments or documentation.",
            "reason": "Undocumented code is harder to understand and maintain.",
            "suggested_fix": "Add docstrings, comments, or inline documentation.",
        })

    if complexity > 30:
        issues.append({
            "type": "high_complexity",
            "severity": "high",
            "description": f"Cyclomatic complexity is very high ({complexity}).",
            "reason": "High complexity makes code difficult to test and maintain.",
            "suggested_fix": "Refactor complex functions into smaller, simpler units.",
        })
    elif complexity > 15:
        issues.append({
            "type": "high_complexity",
            "severity": "medium",
            "description": f"Cyclomatic complexity is elevated ({complexity}).",
            "reason": "Moderate complexity can still pose maintainability challenges.",
            "suggested_fix": "Consider simplifying conditional logic and extracting functions.",
        })

    if maintainability < 30:
        issues.append({
            "type": "low_maintainability",
            "severity": "high",
            "description": f"Maintainability score is very low ({maintainability:.0f}/100).",
            "reason": "Low maintainability indicates the code is hard to modify and extend.",
            "suggested_fix": "Refactor complex sections, improve naming, and add documentation.",
        })
    elif maintainability < 60:
        issues.append({
            "type": "low_maintainability",
            "severity": "medium",
            "description": f"Maintainability score is moderate ({maintainability:.0f}/100).",
            "reason": "Room for improvement in code structure and documentation.",
            "suggested_fix": "Add comments, simplify complex logic, and improve naming.",
        })

    lower_name = file_name.lower()
    if re.search(r"[^a-z0-9_.\-]", lower_name) and not lower_name.startswith("."):
        issues.append({
            "type": "naming_issue",
            "severity": "low",
            "description": f"File name '{file_name}' contains unusual characters.",
            "reason": "Consistent naming improves project navigation and discoverability.",
            "suggested_fix": "Use only alphanumeric characters, hyphens, underscores, and dots.",
        })

    if len(all_hashes.get(content_hash, [])) > 1:
        duplicates = [p for p in all_hashes[content_hash] if p != rel_path]
        if duplicates:
            issues.append({
                "type": "duplicate_file",
                "severity": "medium",
                "description": f"File is a duplicate of: {', '.join(duplicates[:3])}",
                "reason": "Duplicate files create maintenance overhead and inconsistency risks.",
                "suggested_fix": "Consolidate into a single source and reference it from other locations.",
            })

    name_lower = file_name.lower()
    bad_names = {"temp", "tmp", "untitled", "newfile", "test", "example", "dummy", "sample"}
    name_stem = os.path.splitext(name_lower)[0]
    if name_stem in bad_names:
        issues.append({
            "type": "temporary_file",
            "severity": "low",
            "description": f"File name '{file_name}' suggests this may be a temporary or scratch file.",
            "reason": "Temporary files should not be committed to the codebase.",
            "suggested_fix": "Rename the file with a meaningful name or remove if not needed.",
        })

    return issues


def _generate_ai_summary(
    file_name: str,
    total_lines: int,
    code_lines: int,
    comment_lines: int,
    complexity: int,
    maintainability: float,
    classification: str,
    tags: list[str],
    issues: list[dict],
) -> str:
    parts: list[str] = []

    if classification:
        parts.append(f"This {classification.lower()} file")
    elif tags:
        parts.append(f"This {tags[0].lower()} file")
    else:
        parts.append("This file")

    if total_lines > 500:
        parts.append("is large")
    elif total_lines < 10:
        parts.append("is small")
    else:
        parts.append("is moderately sized")

    has_issues = len(issues) > 0
    high_issues = [i for i in issues if i.get("severity") == "high"]
    medium_issues = [i for i in issues if i.get("severity") == "medium"]

    if high_issues:
        parts.append(f"and has {len(high_issues)} high-severity issue{'s' if len(high_issues) > 1 else ''}")
    elif medium_issues:
        parts.append(f"and has {len(medium_issues)} medium-severity issue{'s' if len(medium_issues) > 1 else ''}")
    elif has_issues:
        parts.append("and has some minor issues")
    else:
        parts.append("and is well organized with no significant issues")

    if maintainability >= 80:
        parts.append("with excellent maintainability.")
    elif maintainability >= 60:
        parts.append("with good maintainability.")
    elif maintainability >= 40:
        parts.append("with fair maintainability.")
    else:
        parts.append("with poor maintainability that needs attention.")

    complexity_desc = "very high" if complexity > 30 else "high" if complexity > 15 else "moderate" if complexity > 5 else "low"
    if complexity > 5:
        parts.append(f"Complexity is {complexity_desc} ({complexity}).")

    comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
    if comment_ratio > 0.3:
        parts.append("Code is well-documented.")
    elif comment_ratio < 0.05 and total_lines > 30:
        parts.append("Documentation is sparse and could be improved.")

    return " ".join(parts)


class FileIntelligenceEngine:
    def analyze(self, workspace_path: Path) -> dict:
        all_files: list[dict] = []
        content_hashes: dict[str, list[str]] = {}
        language_counts: dict[str, int] = {}
        classification_counts: dict[str, int] = {}
        health_distribution: dict[str, int] = {
            "excellent": 0, "good": 0, "fair": 0, "poor": 0,
        }
        total_classes = 0
        total_functions = 0
        total_imports = 0
        total_lines_all = 0
        total_code_lines_all = 0
        total_blank_lines_all = 0
        total_comment_lines_all = 0
        all_complexities: list[int] = []
        all_maintainabilities: list[float] = []
        all_issues_count = 0
        large_file_count = 0
        empty_file_count = 0

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
                rel_path = os.path.relpath(file_path, workspace_path)

                try:
                    stat_info = os.stat(file_path)
                    file_size = stat_info.st_size
                    last_modified_dt = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
                    last_modified = last_modified_dt.isoformat()
                except OSError:
                    file_size = 0
                    last_modified = ""

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                    encoding = "utf-8"
                except (OSError, UnicodeDecodeError):
                    try:
                        with open(file_path, "r", encoding="latin-1", errors="replace") as fh:
                            content = fh.read()
                        encoding = "latin-1"
                    except OSError:
                        continue

                lines = content.split("\n")
                total_lines = len(lines)

                code_lines, comment_lines, blank_lines = _count_comments_blanks(
                    lines, language
                )
                complexity = _compute_complexity(lines, language)
                maintainability = max(
                    0.0,
                    min(100.0, 100.0 - (complexity * 1.5) - max(0, (1.0 - (comment_lines / max(total_lines, 1)) * 40.0))),
                )

                # Health scores
                doc_score = min(100.0, (comment_lines / max(total_lines, 1)) * 200.0)
                sec_score = 100.0  # Default high; could be refined
                readability = min(
                    100.0,
                    100.0
                    - max(0, (complexity * 2.0))
                    + max(0, (blank_lines / max(total_lines, 1)) * 50.0),
                )
                readability = max(0.0, min(100.0, readability))
                overall = (
                    maintainability * 0.3
                    + max(0, 100.0 - complexity) * 0.25
                    + doc_score * 0.15
                    + sec_score * 0.15
                    + readability * 0.15
                )
                overall = max(0.0, min(100.0, overall))

                # Content hash for duplicate detection
                content_hash = hashlib.md5(
                    content.encode("utf-8", errors="replace")
                ).hexdigest()
                if content_hash not in content_hashes:
                    content_hashes[content_hash] = []
                content_hashes[content_hash].append(rel_path)

                classification = _classify_file(f, rel_path, language, content)
                tags = _generate_tags(f, rel_path, language, content)
                issues = _detect_issues(
                    f,
                    rel_path,
                    total_lines,
                    code_lines,
                    blank_lines,
                    comment_lines,
                    complexity,
                    maintainability,
                    content_hash,
                    content_hashes,
                )
                ai_summary = _generate_ai_summary(
                    f,
                    total_lines,
                    code_lines,
                    comment_lines,
                    complexity,
                    maintainability,
                    classification,
                    tags,
                    issues,
                )

                file_record = {
                    "file_name": f,
                    "path": rel_path,
                    "extension": ext,
                    "language": language,
                    "encoding": encoding,
                    "size": file_size,
                    "last_modified": last_modified,
                    "total_lines": total_lines,
                    "code_lines": code_lines,
                    "blank_lines": blank_lines,
                    "comment_lines": comment_lines,
                    "functions": 0,
                    "classes": 0,
                    "imports": 0,
                    "complexity": complexity,
                    "health": {
                        "overall": round(overall, 1),
                        "maintainability": round(maintainability, 1),
                        "complexity": max(0.0, min(100.0, 100.0 - complexity * 3.0)),
                        "documentation": round(doc_score, 1),
                        "security": round(sec_score, 1),
                        "readability": round(readability, 1),
                    },
                    "classification": classification,
                    "tags": tags,
                    "issues": issues,
                    "ai_summary": ai_summary,
                }
                all_files.append(file_record)

                language_counts[language] = language_counts.get(language, 0) + 1
                classification_counts[classification] = (
                    classification_counts.get(classification, 0) + 1
                )

                if overall >= 80:
                    health_distribution["excellent"] += 1
                elif overall >= 60:
                    health_distribution["good"] += 1
                elif overall >= 40:
                    health_distribution["fair"] += 1
                else:
                    health_distribution["poor"] += 1

                total_lines_all += total_lines
                total_code_lines_all += code_lines
                total_blank_lines_all += blank_lines
                total_comment_lines_all += comment_lines
                all_complexities.append(complexity)
                all_maintainabilities.append(maintainability)
                all_issues_count += len(issues)

                if total_lines > 500:
                    large_file_count += 1
                if total_lines == 0:
                    empty_file_count += 1

        all_files.sort(key=lambda f: f["path"])

        duplicate_file_count = sum(
            len(v) - 1 for v in content_hashes.values() if len(v) > 1
        )

        avg_complexity = (
            round(sum(all_complexities) / len(all_complexities), 1)
            if all_complexities
            else 0.0
        )
        avg_maintainability = (
            round(sum(all_maintainabilities) / len(all_maintainabilities), 1)
            if all_maintainabilities
            else 0.0
        )

        return {
            "files": all_files,
            "stats": {
                "total_files": len(all_files),
                "total_classes": total_classes,
                "total_functions": total_functions,
                "total_imports": total_imports,
                "total_lines": total_lines_all,
                "total_code_lines": total_code_lines_all,
                "total_blank_lines": total_blank_lines_all,
                "total_comment_lines": total_comment_lines_all,
                "language_counts": language_counts,
                "classification_counts": classification_counts,
                "health_distribution": health_distribution,
                "average_complexity": avg_complexity,
                "average_maintainability": avg_maintainability,
                "total_issues": all_issues_count,
                "large_files": large_file_count,
                "empty_files": empty_file_count,
                "duplicate_files": duplicate_file_count,
            },
        }
