from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class UnifiedIntelligenceEngine:

    def analyze(self, workspace_path: Path, project_analysis: dict | None = None,
                code_intel: dict | None = None, code_quality: dict | None = None,
                file_analysis: dict | None = None, func_class: dict | None = None,
                dep_analysis: dict | None = None, call_graph: dict | None = None,
                semantic: dict | None = None, config_intel: dict | None = None,
                recommendations: dict | None = None) -> dict:
        health = self._compute_health(project_analysis, code_quality, dep_analysis,
                                       file_analysis, semantic, config_intel, call_graph)
        scores = self._compute_scores(project_analysis, code_quality, dep_analysis,
                                       file_analysis, func_class, config_intel, semantic)
        insights = self._generate_insights(project_analysis, code_intel, code_quality,
                                            file_analysis, func_class, dep_analysis,
                                            call_graph, semantic, config_intel)
        executive_summary = self._generate_executive_summary(
            project_analysis, semantic, code_quality, dep_analysis, call_graph,
            config_intel, recommendations, code_intel
        )
        knowledge_hub = self._build_knowledge_hub(project_analysis, code_intel,
                                                   file_analysis, func_class,
                                                   dep_analysis, call_graph,
                                                   semantic, config_intel)
        health_map = self._build_health_map(file_analysis, code_quality, semantic,
                                             call_graph, dep_analysis)
        timeline = self._build_timeline(project_analysis, code_intel, dep_analysis,
                                         file_analysis, func_class, call_graph,
                                         semantic, code_quality, recommendations)

        return {
            "health": health,
            "scores": scores,
            "insights": insights,
            "executive_summary": executive_summary,
            "knowledge_hub": knowledge_hub,
            "health_map": health_map,
            "timeline": timeline,
            "search_results": {},
        }

    def _compute_health(self, project_analysis, code_quality, dep_analysis,
                         file_analysis, semantic, config_intel, call_graph) -> dict:
        q_score = None
        if code_quality:
            q_score = code_quality.get("overall_score", {}).get("score", 0)
        overall = 50.0
        if q_score is not None:
            overall = q_score
        if semantic:
            us = semantic.get("understanding_score", {})
            if us and us.get("overall"):
                overall = (overall + us["overall"]) / 2

        arch = 50.0
        if project_analysis and project_analysis.get("architecture"):
            arch = 60.0
        if project_analysis and project_analysis.get("entry_points"):
            arch = min(100, arch + 10)

        dep_health = 50.0
        if dep_analysis:
            m = dep_analysis.get("metrics", {})
            coupling = m.get("coupling_score", 50)
            dep_health = 100 - coupling
            circular = m.get("circular_dependencies", 0)
            broken = m.get("broken_dependencies", 0)
            dep_health -= circular * 5 + broken * 5
            dep_health = max(0, min(100, dep_health))

        sec_health = 70.0
        if config_intel:
            sec_checks = config_intel.get("security_checks", [])
            if sec_checks:
                failed = sum(1 for s in sec_checks if s.get("status") == "fail")
                sec_health = max(0, 100 - failed * 15)

        perf = 65.0
        if file_analysis:
            files = file_analysis.get("files", [])
            if files:
                total_size = sum(f.get("size", 0) for f in files)
                perf = 100 if total_size < 1048576 else (80 if total_size < 10485760 else (60 if total_size < 52428800 else 40))

        maint = 60.0
        if code_quality:
            maint_val = code_quality.get("maintainability", {}).get("score")
            if maint_val is not None:
                maint = maint_val
        if semantic:
            us = semantic.get("understanding_score", {})
            if us:
                maint = (maint + us.get("maintainability", 50)) / 2

        readiness = 50.0
        if code_quality:
            readiness = overall
        if dep_analysis:
            if dep_analysis.get("metrics", {}).get("circular_dependencies", 0) == 0:
                readiness = min(100, readiness + 5)

        debt = 100 - maint
        ai_conf = 70.0
        if semantic:
            us = semantic.get("understanding_score", {})
            if us:
                ai_conf = us.get("overall", 70)

        return {
            "overall_health": round(overall, 1),
            "overall_quality": round(overall, 1),
            "architecture_health": round(arch, 1),
            "dependency_health": round(dep_health, 1),
            "security_health": round(sec_health, 1),
            "performance_health": round(perf, 1),
            "maintainability": round(maint, 1),
            "readiness": round(readiness, 1),
            "technical_debt": round(debt, 1),
            "ai_confidence": round(ai_conf, 1),
        }

    def _compute_scores(self, project_analysis, code_quality, dep_analysis,
                         file_analysis, func_class, config_intel, semantic) -> dict:
        overall = 50.0
        arch_score = 50.0
        code_q = 50.0
        dep_score = 50.0
        sec_score = 70.0
        file_q = 50.0
        func_q = 50.0
        config_score = 50.0
        semantic_score = 50.0

        if code_quality:
            q = code_quality.get("overall_score", {})
            code_q = q.get("score", 50)
            overall = code_q

        if project_analysis:
            has_arch = bool(project_analysis.get("architecture"))
            has_entry = bool(project_analysis.get("entry_points"))
            arch_score = 60 + (20 if has_arch else 0) + (20 if has_entry else 0)
            arch_score = min(100, arch_score)

        if dep_analysis:
            m = dep_analysis.get("metrics", {})
            coupling = m.get("coupling_score", 50)
            dep_score = 100 - coupling
            circular = m.get("circular_dependencies", 0)
            broken = m.get("broken_dependencies", 0)
            dep_score -= circular * 5 + broken * 5
            dep_score = max(0, min(100, dep_score))

        if config_intel:
            health = config_intel.get("health", {})
            config_score = health.get("score", 50)

        if file_analysis:
            files = file_analysis.get("files", [])
            if files:
                avg_health = sum(f.get("scores", {}).get("overall", 50) for f in files) / len(files)
                file_q = avg_health

        if func_class:
            stats = func_class.get("stats", {})
            total_fns = stats.get("total_functions", 0)
            total_cls = stats.get("total_classes", 0)
            if total_fns > 0:
                avg_complexity = sum(f.get("complexity", 0) for f in func_class.get("functions", [])) / total_fns
                func_q = max(0, 100 - avg_complexity * 5)
            func_q = min(100, max(10, func_q))

        if semantic:
            us = semantic.get("understanding_score", {})
            if us:
                semantic_score = us.get("overall", 50)
                overall = (overall + semantic_score) / 2

        overall = (arch_score + code_q + dep_score + sec_score + file_q + func_q + config_score + semantic_score) / 8

        return {
            "overall_score": round(overall, 1),
            "architecture_score": round(arch_score, 1),
            "code_quality_score": round(code_q, 1),
            "dependency_score": round(dep_score, 1),
            "security_score": round(sec_score, 1),
            "file_quality_score": round(file_q, 1),
            "function_quality_score": round(func_q, 1),
            "configuration_score": round(config_score, 1),
            "semantic_score": round(semantic_score, 1),
        }

    def _generate_insights(self, project_analysis, code_intel, code_quality,
                            file_analysis, func_class, dep_analysis,
                            call_graph, semantic, config_intel) -> list[dict]:
        insights = []

        if code_intel:
            summary = code_intel.get("summary", {})
            langs = summary.get("languages", [])
            if langs:
                insights.append({
                    "type": "technology", "label": "Most Used Language",
                    "value": f"{langs[0]}",
                    "severity": "info", "source": "code-intelligence",
                    "detail": "Language distribution across project files"
                })
            files = summary.get("total_files", 0)
            loc = summary.get("total_lines_of_code", 0)
            if loc > 0:
                avg_loc = loc / max(files, 1)
                if avg_loc > 200:
                    insights.append({
                        "type": "complexity", "label": "Most Complex Module",
                        "value": f"Avg {round(avg_loc)} LOC/file across {files} files",
                        "severity": "warning", "source": "code-intelligence",
                        "detail": "Files have high average line count"
                    })

        if dep_analysis:
            m = dep_analysis.get("metrics", {})
            if m.get("circular_dependencies", 0) > 0:
                insights.append({
                    "type": "dependency", "label": "Largest Dependency Chain",
                    "value": f"{m['circular_dependencies']} circular dependenc{'ies' if m['circular_dependencies'] > 1 else 'y'}",
                    "severity": "critical", "source": "dependencies",
                    "detail": "Circular dependencies may cause maintenance issues"
                })
            if m.get("broken_dependencies", 0) > 0:
                insights.append({
                    "type": "dependency", "label": "Broken Dependencies",
                    "value": f"{m['broken_dependencies']} broken import{'s' if m['broken_dependencies'] > 1 else ''}",
                    "severity": "critical", "source": "dependencies",
                    "detail": "Missing or unresolvable imports detected"
                })
            coupling = m.get("coupling_score", 0)
            if coupling > 50:
                insights.append({
                    "type": "structure", "label": "Weakest Layer",
                    "value": f"High coupling ({coupling}%)",
                    "severity": "warning", "source": "dependencies",
                    "detail": "Modules are tightly coupled"
                })

        if semantic:
            us = semantic.get("understanding_score", {})
            if us:
                biz_logic = us.get("business_logic", 0)
                if biz_logic >= 70:
                    insights.append({
                        "type": "structure", "label": "Best Structured Module",
                        "value": f"Business logic score: {biz_logic}%",
                        "severity": "info", "source": "semantic-intelligence",
                        "detail": "Business logic is well-organized"
                    })
            bc = semantic.get("business_components", [])
            if bc:
                max_bc = max(bc, key=lambda x: x.get("confidence", 0))
                insights.append({
                    "type": "business", "label": "Largest Business Flow",
                    "value": f"{max_bc.get('name', 'N/A')} ({round(max_bc.get('confidence', 0) * 100)}% confidence)",
                    "severity": "info", "source": "semantic-intelligence",
                    "detail": "Primary business component identified"
                })

        if call_graph:
            cg_nodes = call_graph.get("nodes", [])
            if cg_nodes:
                insights.append({
                    "type": "structure", "label": "Most Critical File",
                    "value": cg_nodes[0].get("name", "N/A"),
                    "severity": "info", "source": "call-graph",
                    "detail": "Most referenced file in call graph"
                })

        if code_quality:
            crit = code_quality.get("severity_counts", {}).get("critical", 0)
            high = code_quality.get("severity_counts", {}).get("high", 0)
            if crit > 0 or high > 0:
                insights.append({
                    "type": "quality", "label": "Highest Technical Debt",
                    "value": f"{crit} critical, {high} high issues",
                    "severity": "critical" if crit > 0 else "warning",
                    "source": "code-quality",
                    "detail": "Significant quality issues to address"
                })

        if config_intel:
            health = config_intel.get("health", {})
            score = health.get("score", 0)
            if score >= 80:
                insights.append({
                    "type": "configuration", "label": "Highest Maintainability",
                    "value": f"Config health: {score}%",
                    "severity": "info", "source": "configuration",
                    "detail": "Project configuration is clean and well-maintained"
                })

        return insights

    def _generate_executive_summary(self, project_analysis, semantic, code_quality,
                                     dep_analysis, call_graph, config_intel,
                                     recommendations, code_intel) -> dict:
        proj_type = (project_analysis or {}).get("project_type", "Unknown")
        arch = (project_analysis or {}).get("architecture", "Not detected")

        p_summary = f"This is a {proj_type} project with {arch} architecture."
        if code_intel:
            s = code_intel.get("summary", {})
            p_summary += f" It contains {s.get('total_files', 0)} files ({s.get('total_lines_of_code', 0):,} lines of code) across {len(s.get('languages', []))} language(s)."

        a_summary = f"Architecture is identified as {arch}. "
        if project_analysis:
            eps = project_analysis.get("entry_points", [])
            if eps:
                a_summary += f"Found {len(eps)} entry point(s). "

        biz_summary = "Business logic is "
        if semantic:
            us = semantic.get("understanding_score", {})
            if us:
                bl = us.get("business_logic", 0)
                biz_summary += f"scored at {bl}% with {len(semantic.get('business_flows', []))} detected flow(s)."
            else:
                biz_summary += "detected but not fully mapped."
        else:
            biz_summary += "not analyzed."

        risks = []
        risk_summary = ""
        if dep_analysis:
            m = dep_analysis.get("metrics", {})
            if m.get("circular_dependencies", 0) > 0:
                risks.append(f"{m['circular_dependencies']} circular dependenc{'ies' if m['circular_dependencies'] > 1 else 'y'}")
            if m.get("broken_dependencies", 0) > 0:
                risks.append(f"{m['broken_dependencies']} broken import{'s' if m['broken_dependencies'] > 1 else ''}")
        if code_quality:
            crit = code_quality.get("severity_counts", {}).get("critical", 0)
            if crit > 0:
                risks.append(f"{crit} critical issue{'s' if crit > 1 else ''}")
        if risks:
            risk_summary = f"Key risks: {', '.join(risks)}."
        else:
            risk_summary = "No significant risks detected."

        sec_summary = "Security posture is "
        if config_intel:
            sec_checks = config_intel.get("security_checks", [])
            failed = sum(1 for s in sec_checks if s.get("status") == "fail")
            sec_summary += f"{'weak' if failed > 0 else 'good'} ({failed} failed check{'s' if failed != 1 else ''})."
        else:
            sec_summary += "not assessed."

        rec_summary = ""
        if recommendations:
            recs = recommendations.get("recommendations", [])
            if recs:
                rec_summary = f"{len(recs)} recommendation{'s' if len(recs) > 1 else ''} available."
            else:
                rec_summary = "No specific recommendations."

        future = []
        if semantic and not semantic.get("understanding_score"):
            future.append("Complete semantic intelligence analysis for deeper insights")
        if dep_analysis:
            m = dep_analysis.get("metrics", {})
            if m.get("circular_dependencies", 0) > 0:
                future.append("Refactor circular dependencies to improve maintainability")
            if m.get("unused_imports", 0) > 0:
                future.append("Remove unused imports to reduce technical debt")
        if recommendations:
            for r in (recommendations.get("recommendations", []) or [])[:3]:
                if isinstance(r, dict) and r.get("suggestion"):
                    future.append(r["suggestion"])
        if call_graph:
            cg_issues = call_graph.get("issues", [])
            if cg_issues:
                future.append("Review call graph issues for potential refactoring")
        future = future[:5]

        return {
            "project_summary": p_summary,
            "architecture_summary": a_summary,
            "business_logic_summary": biz_summary,
            "risk_summary": risk_summary,
            "security_summary": sec_summary,
            "recommendation_summary": rec_summary,
            "future_improvements": future,
        }

    def _build_knowledge_hub(self, project_analysis, code_intel, file_analysis,
                              func_class, dep_analysis, call_graph,
                              semantic, config_intel) -> list[dict]:
        hub = []

        if project_analysis:
            hub.append({
                "category": "architecture", "label": "Framework",
                "value": project_analysis.get("project_type", "Unknown"),
                "link": "framework", "count": 1
            })
            hub.append({
                "category": "architecture", "label": "Architecture",
                "value": project_analysis.get("architecture", "Unknown"),
                "link": "architecture", "count": 1
            })
            hub.append({
                "category": "architecture", "label": "Modules",
                "value": f"{len(project_analysis.get('detected_modules', []))} modules",
                "link": "modules", "count": len(project_analysis.get('detected_modules', []))
            })

        if semantic:
            bc = semantic.get("business_components", [])
            hub.append({
                "category": "business", "label": "Business Components",
                "value": f"{len(bc)} components",
                "link": "semantic-intelligence", "count": len(bc)
            })
            ef = semantic.get("business_flows", [])
            hub.append({
                "category": "business", "label": "Execution Flows",
                "value": f"{len(ef)} flows",
                "link": "semantic-intelligence", "count": len(ef)
            })
            comps = semantic.get("components", [])
            hub.append({
                "category": "business", "label": "Semantic Components",
                "value": f"{len(comps)} components",
                "link": "semantic-intelligence", "count": len(comps)
            })

        if code_intel:
            s = code_intel.get("summary", {})
            hub.append({
                "category": "code", "label": "Files",
                "value": f"{s.get('total_files', 0)} files, {s.get('total_lines_of_code', 0):,} LOC",
                "link": "file-analysis", "count": s.get('total_files', 0)
            })

        if func_class:
            stats = func_class.get("stats", {})
            fns = stats.get("total_functions", 0)
            cls = stats.get("total_classes", 0)
            if fns > 0:
                hub.append({
                    "category": "code", "label": "Functions",
                    "value": f"{fns} functions",
                    "link": "function-class-intelligence", "count": fns
                })
            if cls > 0:
                hub.append({
                    "category": "code", "label": "Classes",
                    "value": f"{cls} classes",
                    "link": "function-class-intelligence", "count": cls
                })

        if dep_analysis:
            m = dep_analysis.get("metrics", {})
            total_imports = m.get("total_imports", 0)
            hub.append({
                "category": "dependencies", "label": "Dependencies",
                "value": f"{total_imports} imports, {m.get('external_libraries', 0)} external",
                "link": "dependencies", "count": total_imports
            })

        if call_graph:
            cg_nodes = call_graph.get("nodes", [])
            cg_edges = call_graph.get("edges", [])
            cg_flows = call_graph.get("execution_flows", [])
            hub.append({
                "category": "execution", "label": "Call Graph",
                "value": f"{len(cg_nodes)} nodes, {len(cg_edges)} edges",
                "link": "call-graph", "count": len(cg_nodes)
            })
            hub.append({
                "category": "execution", "label": "Execution Flows",
                "value": f"{len(cg_flows)} flows",
                "link": "call-graph", "count": len(cg_flows)
            })

        if config_intel:
            hub.append({
                "category": "configuration", "label": "Config Files",
                "value": f"{config_intel.get('total_files', 0)} files",
                "link": "configuration", "count": config_intel.get('total_files', 0)
            })

        return hub

    def _build_health_map(self, file_analysis, code_quality, semantic,
                           call_graph, dep_analysis) -> list[dict]:
        modules = []

        if file_analysis:
            files = file_analysis.get("files", [])
            dir_groups = defaultdict(list)
            for f in files:
                parts = f.get("file_path", "").split("/")
                root_dir = parts[0] if parts else "root"
                dir_groups[root_dir].append(f)
            for dir_name, dir_files in dir_groups.items():
                avg_score = sum(f.get("scores", {}).get("overall", 50) for f in dir_files) / len(dir_files)
                issues = sum(len(f.get("issues", [])) for f in dir_files)
                status = "healthy" if avg_score >= 70 else ("warning" if avg_score >= 40 else "critical")
                modules.append({
                    "name": dir_name,
                    "path": dir_name,
                    "status": status,
                    "issues": issues,
                    "score": round(avg_score, 1),
                })

        if semantic:
            us = semantic.get("understanding_score", {})
            if us and us.get("has_entry_points"):
                modules.append({
                    "name": "entry-points",
                    "path": "",
                    "status": "healthy",
                    "issues": 0,
                    "score": 90.0,
                })

        if dep_analysis:
            m = dep_analysis.get("metrics", {})
            if m.get("broken_dependencies", 0) > 0:
                modules.append({
                    "name": "broken-imports",
                    "path": "",
                    "status": "critical",
                    "issues": m["broken_dependencies"],
                    "score": 20.0,
                })

        return modules

    def _build_timeline(self, project_analysis, code_intel, dep_analysis,
                         file_analysis, func_class, call_graph,
                         semantic, code_quality, recommendations) -> list[dict]:
        stages = [
            ("upload", "Project Upload", "completed" if any([project_analysis]) else "pending",
             "Project uploaded and extracted", 100),
            ("detection", "Framework Detection", "completed" if project_analysis and project_analysis.get("project_type") else "pending",
             f"Detected: {project_analysis.get('project_type', 'N/A')}" if project_analysis else "Waiting", 90 if project_analysis else 0),
            ("architecture", "Architecture Analysis", "completed" if project_analysis and project_analysis.get("architecture") else "pending",
             f"Architecture: {project_analysis.get('architecture', 'N/A')}" if project_analysis else "Waiting", 85 if project_analysis and project_analysis.get("architecture") else 0),
            ("dependencies", "Dependency Analysis", "completed" if dep_analysis else "pending",
             f"{dep_analysis.get('metrics', {}).get('total_imports', 0)} imports analyzed" if dep_analysis else "Waiting",
             80 if dep_analysis else 0),
            ("code-intelligence", "Code Intelligence", "completed" if code_intel else "pending",
             f"{code_intel.get('summary', {}).get('total_files', 0)} files scanned" if code_intel else "Waiting",
             75 if code_intel else 0),
            ("file-analysis", "File Analysis", "completed" if file_analysis else "pending",
             f"{len(file_analysis.get('files', []))} files analyzed" if file_analysis else "Waiting",
             70 if file_analysis else 0),
            ("function-class", "Function & Class Analysis", "completed" if func_class else "pending",
             f"{func_class.get('stats', {}).get('total_functions', 0)} functions, {func_class.get('stats', {}).get('total_classes', 0)} classes" if func_class else "Waiting",
             65 if func_class else 0),
            ("call-graph", "Call Graph Analysis", "completed" if call_graph else "pending",
             f"{len(call_graph.get('nodes', []))} nodes, {len(call_graph.get('edges', []))} edges" if call_graph else "Waiting",
             60 if call_graph else 0),
            ("semantic-intelligence", "Semantic Intelligence", "completed" if semantic else "pending",
             f"Score: {semantic.get('understanding_score', {}).get('overall', 0)}%" if semantic and semantic.get('understanding_score') else "Waiting",
             55 if semantic else 0),
            ("recommendations", "AI Recommendations", "completed" if recommendations else "pending",
             f"{len(recommendations.get('recommendations', []))} recommendations" if recommendations else "Waiting",
             50 if recommendations else 0),
        ]

        return [
            {
                "stage": s[0], "label": s[1], "status": s[2],
                "details": s[3], "score": s[4],
            }
            for s in stages
        ]
