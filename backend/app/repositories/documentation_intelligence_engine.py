import os
import re
from pathlib import Path
from typing import Any


DOCSTRING_PATTERN = re.compile(r'""".*?"""|\'\'\'.*?\'\'\'', re.DOTALL)
COMMENT_LINE_PATTERN = re.compile(r'^\s*#.*$', re.MULTILINE)
FUNC_DEF_PATTERN = re.compile(
    r'(?:def|async def|function|public|private|protected)\s+(\w+)\s*\(',
)
CLASS_DEF_PATTERN = re.compile(
    r'(?:class|interface|trait|abstract class)\s+(\w+)',
)
JS_DOCSTRING_PATTERN = re.compile(r'/\*\*[\s\S]*?\*/')
JS_LINE_COMMENT_PATTERN = re.compile(r'^\s*//.*$', re.MULTILINE)


class DocumentationIntelligenceEngine:

    def analyze(self, workspace_path: Path | None = None,
                project_analysis: dict | None = None,
                code_intel: dict | None = None,
                code_quality: dict | None = None,
                file_analysis: dict | None = None,
                func_class: dict | None = None,
                dep_analysis: dict | None = None,
                call_graph: dict | None = None,
                semantic: dict | None = None,
                config_intel: dict | None = None,
                recommendations: dict | None = None) -> dict:
        code_docs = self._analyze_code_documentation(workspace_path, code_intel, func_class)
        project_docs = self._analyze_project_documentation(workspace_path, project_analysis)
        findings = self._detect_findings(code_docs, project_docs)
        score = self._compute_score(code_docs, project_docs)
        summary = self._generate_summary(code_docs, project_docs, findings, score)
        return {
            "documentation_score": score,
            "code_documentation": code_docs,
            "project_docs": project_docs,
            "findings": findings,
            "summary": summary,
        }

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
                           (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php", ".rs")):
                        fpath = os.path.join(root, fn)
                        try:
                            with open(fpath, "r", errors="ignore") as fh:
                                files[fpath] = fh.read()
                        except Exception:
                            pass
        return files

    def _analyze_code_documentation(self, workspace_path, code_intel, func_class) -> list[dict]:
        items: list[dict] = []
        files_content = self._get_source_files(workspace_path, code_intel)

        analyzed_funcs: set[str] = set()
        analyzed_classes: set[str] = set()

        for fpath, content in files_content.items():
            rel = os.path.relpath(fpath, str(workspace_path)) if workspace_path else fpath

            is_python = fpath.endswith(".py")
            is_js_ts = any(fpath.endswith(ext) for ext in (".js", ".ts", ".jsx", ".tsx"))

            docstrings = set()
            line_comments = set()
            if is_python:
                for m in DOCSTRING_PATTERN.finditer(content):
                    docstrings.add(m.start())
                for m in COMMENT_LINE_PATTERN.finditer(content):
                    line_comments.add(m.start())
            elif is_js_ts:
                for m in JS_DOCSTRING_PATTERN.finditer(content):
                    docstrings.add(m.start())
                for m in JS_LINE_COMMENT_PATTERN.finditer(content):
                    line_comments.add(m.start())

            func_matches = FUNC_DEF_PATTERN.findall(content)
            for fn_name in func_matches[:50]:
                key = f"{rel}:{fn_name}"
                if key in analyzed_funcs:
                    continue
                analyzed_funcs.add(key)
                fn_pattern = re.compile(
                    r'(?:def|async def|function|public|private|protected)\s+'
                    + re.escape(fn_name) + r'\s*\(',
                )
                fn_match = fn_pattern.search(content)
                fn_line = 0
                has_doc = False
                doc_quality = "missing"
                if fn_match:
                    fn_line = content[:fn_match.start()].count("\n") + 1
                    before = content[max(0, fn_match.start() - 400):fn_match.start()]
                    has_doc = bool(DOCSTRING_PATTERN.search(before)) if is_python else bool(JS_DOCSTRING_PATTERN.search(before))
                    if has_doc:
                        doc_quality = "good"
                    elif any(cs in line_comments for cs in line_comments
                             if abs(cs - fn_match.start()) < 200):
                        has_doc = True
                        doc_quality = "average"
                items.append({
                    "type": "function",
                    "name": fn_name,
                    "file": rel,
                    "documented": has_doc,
                    "documentation_type": "docstring" if has_doc else "none",
                    "line": fn_line,
                    "quality": doc_quality,
                })

            cls_matches = CLASS_DEF_PATTERN.findall(content)
            for cls_name in cls_matches[:20]:
                key = f"{rel}:{cls_name}"
                if key in analyzed_classes:
                    continue
                analyzed_classes.add(key)
                cls_pattern = re.compile(
                    r'(?:class|interface|trait|abstract class)\s+'
                    + re.escape(cls_name),
                )
                cls_match = cls_pattern.search(content)
                cls_line = 0
                has_doc = False
                doc_quality = "missing"
                if cls_match:
                    cls_line = content[:cls_match.start()].count("\n") + 1
                    before = content[max(0, cls_match.start() - 400):cls_match.start()]
                    has_doc = bool(DOCSTRING_PATTERN.search(before)) if is_python else bool(JS_DOCSTRING_PATTERN.search(before))
                    if has_doc:
                        doc_quality = "good"
                items.append({
                    "type": "class",
                    "name": cls_name,
                    "file": rel,
                    "documented": has_doc,
                    "documentation_type": "docstring" if has_doc else "none",
                    "line": cls_line,
                    "quality": doc_quality,
                })

            comment_ratio = len(line_comments) / max(len(content.splitlines()), 1)
            items.append({
                "type": "file",
                "name": os.path.basename(rel),
                "file": rel,
                "documented": comment_ratio > 0.05,
                "documentation_type": "comment" if comment_ratio > 0.05 else "none",
                "line": 0,
                "quality": "good" if comment_ratio > 0.15 else ("average" if comment_ratio > 0.05 else "poor"),
            })

        if func_class:
            functions = func_class.get("functions", [])
            if isinstance(functions, list):
                for fn in functions:
                    fname = fn.get("name", "")
                    ffile = fn.get("file", "")
                    if ffile:
                        rel = os.path.relpath(ffile, str(workspace_path)) if workspace_path else ffile
                    else:
                        rel = ""
                    key = f"{rel}:{fname}"
                    if key not in analyzed_funcs and fname:
                        analyzed_funcs.add(key)
                        items.append({
                            "type": "function",
                            "name": fname,
                            "file": rel,
                            "documented": bool(fn.get("has_documentation", fn.get("has_doc", False))),
                            "documentation_type": "docstring" if fn.get("has_documentation", fn.get("has_doc", False)) else "none",
                            "line": fn.get("start_line", 0),
                            "quality": "good" if fn.get("has_documentation", fn.get("has_doc", False)) else "missing",
                        })

        return items

    def _assess_doc_quality(self, fpath: str) -> tuple[str, str]:
        try:
            with open(fpath, "r", errors="ignore") as fh:
                content = fh.read()
            lines = content.splitlines()
            if len(lines) > 20:
                return "good", "comprehensive"
            elif len(lines) > 5:
                return "average", "partial"
            else:
                return "poor", "minimal"
        except Exception:
            return "found", "unknown"

    def _analyze_project_documentation(self, workspace_path, project_analysis) -> list[dict]:
        docs: list[dict] = []
        if not workspace_path:
            return docs

        file_specs: list[tuple[str, str, list[str]]] = [
            ("README", "readme", [r"^readme(\..+)?$"]),
            ("LICENSE", "license", [r"^license(\..+)?$"]),
            ("COPYING", "license", [r"^copying(\..+)?$"]),
            ("NOTICE", "notice", [r"^notice(\..+)?$"]),
            ("CHANGELOG", "changelog", [r"^changelog(\..+)?$"]),
            ("HISTORY", "changelog", [r"^history(\..+)?$"]),
            ("CONTRIBUTING", "contributing", [r"^contributing(\..+)?$"]),
            ("CODE_OF_CONDUCT", "code_of_conduct", [r"^code_of_conduct(\..+)?$"]),
            ("SECURITY", "security", [r"^security(\..+)?$"]),
            ("INSTALL", "setup", [r"^install(\..+)?$"]),
            ("SETUP", "setup", [r"^setup(\..+)?$"]),
            ("DEPLOYMENT", "deployment", [r"^deployment(\..+)?$"]),
            ("ARCHITECTURE", "architecture", [r"^architecture(\..+)?$"]),
            ("API", "api", [r"^api(\..+)?$"]),
        ]

        all_files: list[dict] = []
        for root, dirs, filenames in os.walk(str(workspace_path)):
            for fn in filenames:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, str(workspace_path))
                try:
                    st = os.stat(full)
                    size = st.st_size
                except Exception:
                    size = 0
                all_files.append({
                    "rel": rel,
                    "name": fn,
                    "lower": fn.lower(),
                    "size": size,
                    "root_level": root == str(workspace_path),
                })

        seen_names: set[str] = set()
        for display_name, doc_type, patterns in file_specs:
            key = f"{display_name}|{doc_type}"
            if key in seen_names:
                continue
            seen_names.add(key)

            matches: list[dict] = []
            for f in all_files:
                for pat in patterns:
                    if re.match(pat, f["lower"]):
                        matches.append(f)
                        break

            if matches:
                matches.sort(key=lambda m: (not m["root_level"], m["rel"]))
                best = matches[0]
                fpath = os.path.join(str(workspace_path), best["rel"])
                quality, completeness = self._assess_doc_quality(fpath)
                docs.append({
                    "name": display_name,
                    "path": best["rel"],
                    "doc_type": doc_type,
                    "present": True,
                    "quality": quality,
                    "size": best["size"],
                    "completeness": completeness,
                })
            else:
                docs.append({
                    "name": display_name,
                    "path": "",
                    "doc_type": doc_type,
                    "present": False,
                    "quality": "missing",
                    "size": 0,
                    "completeness": "missing",
                })

        doc_dir_names = ["docs", "documentation", "architecture", "wiki"]
        for dirname in doc_dir_names:
            dir_path = os.path.join(str(workspace_path), dirname)
            if os.path.isdir(dir_path):
                md_files: list[str] = []
                total_size = 0
                for root, _, filenames in os.walk(dir_path):
                    for fn in filenames:
                        if fn.lower().endswith(".md"):
                            fp = os.path.join(root, fn)
                            md_files.append(fp)
                            try:
                                total_size += os.path.getsize(fp)
                            except Exception:
                                pass
                if md_files:
                    docs.append({
                        "name": f"{dirname}/ Directory",
                        "path": f"{dirname}/",
                        "doc_type": "docs_directory",
                        "present": True,
                        "quality": "good" if len(md_files) > 3 else "average",
                        "size": total_size,
                        "completeness": "comprehensive" if len(md_files) > 5 else "partial",
                    })

        if not any(d["present"] for d in docs):
            docs.append({
                "name": "Project Documentation",
                "path": "",
                "doc_type": "general",
                "present": False,
                "quality": "missing",
                "size": 0,
                "completeness": "missing",
            })

        return docs

    def _detect_findings(self, code_docs, project_docs) -> list[dict]:
        findings: list[dict] = []

        undocumented_funcs = [d for d in code_docs if d["type"] == "function" and not d["documented"]]
        undocumented_classes = [d for d in code_docs if d["type"] == "class" and not d["documented"]]
        undocumented_files = [d for d in code_docs if d["type"] == "file" and not d["documented"]]

        if undocumented_funcs:
            aff_files = list({d["file"] for d in undocumented_funcs if d["file"]})
            aff_fns = [d["name"] for d in undocumented_funcs[:8]]
            findings.append({
                "name": f"Undocumented Functions ({len(undocumented_funcs)})",
                "type": "missing-function-docs",
                "severity": "high" if len(undocumented_funcs) > 20 else "medium",
                "affected_files": aff_files,
                "affected_functions": aff_fns,
                "affected_classes": [],
                "description": f"{len(undocumented_funcs)} functions lack documentation comments or docstrings.",
                "recommendation": "Add docstrings to all public functions explaining purpose, parameters, and return values.",
                "estimated_improvement": f"+{min(len(undocumented_funcs) * 2, 30)}% coverage",
            })

        if undocumented_classes:
            aff_files = list({d["file"] for d in undocumented_classes if d["file"]})
            aff_cls = [d["name"] for d in undocumented_classes[:8]]
            findings.append({
                "name": f"Undocumented Classes ({len(undocumented_classes)})",
                "type": "missing-class-docs",
                "severity": "high" if len(undocumented_classes) > 10 else "medium",
                "affected_files": aff_files,
                "affected_functions": [],
                "affected_classes": aff_cls,
                "description": f"{len(undocumented_classes)} classes lack class-level documentation.",
                "recommendation": "Add class docstrings describing responsibility, usage, and relationships.",
                "estimated_improvement": f"+{min(len(undocumented_classes) * 3, 25)}% quality",
            })

        if undocumented_files:
            aff_files = [d["file"] for d in undocumented_files[:8] if d["file"]]
            findings.append({
                "name": f"Files with Low Comment Ratio ({len(undocumented_files)})",
                "type": "missing-file-comments",
                "severity": "low",
                "affected_files": aff_files,
                "affected_functions": [],
                "affected_classes": [],
                "description": f"{len(undocumented_files)} files have less than 5% comment ratio.",
                "recommendation": "Add inline comments for complex logic and file-level header comments.",
                "estimated_improvement": "+5-10% readability",
            })

        missing_project_docs = [d for d in project_docs if not d["present"]]
        for pd in missing_project_docs:
            findings.append({
                "name": f"Missing {pd['name']}",
                "type": "missing-project-doc",
                "severity": "medium" if pd["doc_type"] in ("readme", "license") else "low",
                "affected_files": [],
                "affected_functions": [],
                "affected_classes": [],
                "description": f"Project does not include a {pd['name']} file.",
                "recommendation": self._recommendation_for_missing_doc(pd["doc_type"]),
                "estimated_improvement": "+5-15% documentation completeness",
            })

        return findings

    def _recommendation_for_missing_doc(self, doc_type: str) -> str:
        recs = {
            "readme": "Create a README.md with project description, setup instructions, usage examples, and architecture overview.",
            "license": "Add a LICENSE file to specify the project's open-source license and terms of use.",
            "contributing": "Create a CONTRIBUTING.md guide outlining how others can contribute to the project.",
            "changelog": "Maintain a CHANGELOG.md to track version history and notable changes.",
            "architecture": "Document the project architecture including component relationships, data flow, and design decisions.",
            "setup": "Provide setup/installation instructions for new developers to get started.",
            "deployment": "Document deployment procedures, environment requirements, and release process.",
            "api": "Document API endpoints, request/response formats, and authentication requirements.",
            "code_of_conduct": "Add a CODE_OF_CONDUCT.md to establish community guidelines.",
        }
        return recs.get(doc_type, f"Add missing {doc_type} documentation.")

    def _compute_score(self, code_docs, project_docs) -> dict:
        total_funcs = len([d for d in code_docs if d["type"] == "function"])
        doc_funcs = len([d for d in code_docs if d["type"] == "function" and d["documented"]])
        total_classes = len([d for d in code_docs if d["type"] == "class"])
        doc_classes = len([d for d in code_docs if d["type"] == "class" and d["documented"]])
        total_files_docs = len([d for d in code_docs if d["type"] == "file"])
        doc_files = len([d for d in code_docs if d["type"] == "file" and d["documented"]])

        func_coverage = (doc_funcs / max(total_funcs, 1)) * 100
        class_coverage = (doc_classes / max(total_classes, 1)) * 100
        file_coverage = (doc_files / max(total_files_docs, 1)) * 100

        present_project_docs = len([d for d in project_docs if d["present"]])
        total_project_docs = len(project_docs)
        project_doc_coverage = (present_project_docs / max(total_project_docs, 1)) * 100

        coverage = (func_coverage * 0.35 + class_coverage * 0.25 + file_coverage * 0.15 + project_doc_coverage * 0.25)

        quality_items = [d for d in code_docs if d["quality"] in ("good", "excellent")]
        quality_score = (len(quality_items) / max(len(code_docs), 1)) * 100 if code_docs else 0

        overall = round(max(0, min(coverage * 0.6 + quality_score * 0.4, 100)), 1)
        developer_readiness = round(max(0, min(project_doc_coverage * 0.5 + coverage * 0.3 + quality_score * 0.2, 100)), 1)
        confidence = round(min(total_funcs * 2 + total_classes * 3, 90), 1)

        if overall < 30:
            level = "critical"
        elif overall < 50:
            level = "high"
        elif overall < 70:
            level = "medium"
        elif overall < 85:
            level = "low"
        else:
            level = "informational"

        return {
            "overall_documentation_score": overall,
            "documentation_coverage": round(coverage, 1),
            "documentation_quality": round(quality_score, 1),
            "developer_readiness": developer_readiness,
            "ai_confidence": confidence,
            "risk_level": level,
        }

    def _generate_summary(self, code_docs, project_docs, findings, score) -> dict:
        lines = []
        total_funcs = len([d for d in code_docs if d["type"] == "function"])
        doc_funcs = len([d for d in code_docs if d["type"] == "function" and d["documented"]])
        total_classes = len([d for d in code_docs if d["type"] == "class"])
        doc_classes = len([d for d in code_docs if d["type"] == "class" and d["documented"]])
        undoc_funcs = total_funcs - doc_funcs
        undoc_classes = total_classes - doc_classes

        present_docs = [d for d in project_docs if d["present"]]
        missing_docs = [d for d in project_docs if not d["present"]]

        if present_docs:
            doc_names = [d["name"] for d in present_docs]
            lines.append(f"Project contains {', '.join(doc_names[:4])}{' and more' if len(doc_names) > 4 else ''}.")
        if missing_docs:
            missing_names = [d["name"] for d in missing_docs]
            lines.append(f"Missing: {', '.join(missing_names[:4])}{' and more' if len(missing_names) > 4 else ''}.")

        if total_funcs > 0:
            pct = round(doc_funcs / total_funcs * 100, 1)
            lines.append(f"Function documentation: {doc_funcs}/{total_funcs} ({pct}%) documented.")
        if total_classes > 0:
            pct = round(doc_classes / total_classes * 100, 1)
            lines.append(f"Class documentation: {doc_classes}/{total_classes} ({pct}%) documented.")
        if undoc_funcs > 0:
            lines.append(f"{undoc_funcs} function(s) and {undoc_classes} class(es) require documentation.")
        if score.get("overall_documentation_score", 0) < 50:
            lines.append("Documentation coverage is low — prioritize adding docstrings and project docs.")
        elif score.get("overall_documentation_score", 0) < 75:
            lines.append("Documentation is adequate but improvements are recommended for completeness.")

        prioritized = []
        for f in sorted(findings, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 5)):
            prioritized.append(f"[{f['severity'].upper()}] {f['name']}: {f.get('recommendation', '')[:120]}")

        return {
            "missing_readme": not any(d["doc_type"] == "readme" and d["present"] for d in project_docs),
            "missing_license": not any(d["doc_type"] == "license" and d["present"] for d in project_docs),
            "missing_contributing": not any(d["doc_type"] == "contributing" and d["present"] for d in project_docs),
            "missing_changelog": not any(d["doc_type"] == "changelog" and d["present"] for d in project_docs),
            "missing_architecture_docs": not any(d["doc_type"] == "architecture" and d["present"] for d in project_docs),
            "coverage_percentage": score.get("documentation_coverage", 0),
            "documented_functions": doc_funcs,
            "undocumented_functions": undoc_funcs,
            "documented_classes": doc_classes,
            "undocumented_classes": undoc_classes,
            "files_with_comments": len([d for d in code_docs if d["type"] == "file"]),
            "files_without_comments": len([d for d in code_docs if d["type"] == "file" and not d["documented"]]),
            "summary_text": " ".join(lines),
            "prioritized_recommendations": prioritized[:20],
        }
