class ProjectInsightsEngine:
    def analyze(
        self,
        analyzer_data: dict | None,
        ep_data: dict | None,
        arch_data: dict | None,
        mod_data: dict | None,
        fw_data: dict | None,
        ci_data: dict | None,
        pi_data: dict | None,
    ) -> dict:
        merged = self._merge(
            analyzer_data or {},
            ep_data or {},
            arch_data or {},
            mod_data or {},
            fw_data or {},
            ci_data or {},
            pi_data or {},
        )

        health_score_val, classification = self._calc_health_score(merged)
        ai_summary = self._gen_summary(merged)
        strengths = self._gen_strengths(merged)
        weaknesses = self._gen_weaknesses(merged)
        risk_level, risk_score, risk_explanation = self._calc_risk(merged)
        maint_score, maint_grade, maint_expl = self._calc_maintainability(merged)
        scal_level, scal_reason = self._calc_scalability(merged)
        perf_insights = self._gen_performance_insights(merged)
        sec_insights = self._gen_security_insights(merged)
        cq_insights = self._gen_code_quality_insights(merged)
        actions = self._gen_recommended_actions(merged)
        readiness = self._calc_readiness_scores(merged)

        return {
            "health_score": {"score": health_score_val, "classification": classification},
            "ai_summary": ai_summary[:8],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "risk_analysis": {"level": risk_level, "score": risk_score, "explanation": risk_explanation},
            "maintainability": {"score": maint_score, "grade": maint_grade},
            "maintainability_explanation": maint_expl,
            "scalability": {"level": scal_level, "reason": scal_reason},
            "performance_insights": perf_insights,
            "security_insights": sec_insights,
            "code_quality_insights": cq_insights,
            "recommended_actions": actions[:10],
            "readiness_scores": readiness,
        }

    @staticmethod
    def _merge(
        analyzer: dict, ep: dict, arch: dict, mod: dict,
        fw: dict, ci: dict, pi: dict,
    ) -> dict:
        return {
            "project_name": analyzer.get("project_name", ""),
            "project_type": analyzer.get("project_type", "Unknown"),
            "total_files": analyzer.get("total_files", 0),
            "total_folders": analyzer.get("total_folders", 0),
            "workspace_size": analyzer.get("workspace_size", 0),
            "folder_summary": analyzer.get("folder_summary", {}),
            "config_summary": analyzer.get("config_summary", {}),
            "technology_stack": analyzer.get("technology_stack", {}),
            "workspace_summary": analyzer.get("workspace_summary", ""),
            "entry_points": ep.get("primary_entry_point", {}),
            "primary_entry": ep.get("primary_entry_point", {}),
            "architecture": arch.get("primary_architecture", {}),
            "arch_health": arch.get("health", {}),
            "arch_recommendations": arch.get("recommendations", []),
            "modules": mod.get("modules", []),
            "module_summary": mod.get("summary", {}),
            "frameworks": fw.get("frameworks", []),
            "fw_tech_stack": fw.get("technology_stack", {}),
            "fw_compatibility": fw.get("compatibility", []),
            "fw_features": fw.get("features", []),
            "fw_evidence": fw.get("evidence", []),
            "config_detected": ci.get("detected_files", []),
            "config_missing": ci.get("missing_files", []),
            "config_scores": ci.get("scores", {}),
            "config_health": ci.get("health", {}),
            "config_warnings": ci.get("warnings", []),
            "config_recommendations": ci.get("recommendations", []),
            "dependency_validation": ci.get("dependency_validation", []),
            "environment_validation": ci.get("environment_validation", []),
            "docker_validation": ci.get("docker_validation", {}),
            "cicd": ci.get("cicd", []),
            "security_checks": ci.get("security_checks", []),
            "code_metrics": pi.get("code_metrics", {}),
            "complexity": pi.get("complexity", {}),
            "maintainability": pi.get("maintainability", {}),
            "code_organization": pi.get("code_organization", []),
            "code_style": pi.get("code_style", []),
            "project_stats": pi.get("project_stats", {}),
            "recommendations": pi.get("recommendations", []),
            "largest_files": pi.get("largest_files", []),
            "largest_directories": pi.get("largest_directories", []),
        }

    @staticmethod
    def _calc_health_score(data: dict) -> tuple[int, str]:
        config_scores = data.get("config_scores", {})
        config_health = config_scores.get("configuration_health", 0) if config_scores else 0
        pi_maint = data.get("maintainability", {})
        maint_score = pi_maint.get("score", 0) if pi_maint else 0
        arch_health = data.get("arch_health", {})
        arch_score = arch_health.get("score", 50) if arch_health else 50
        fw_frameworks = data.get("frameworks", [])
        fw_conf_sum = sum(f.get("confidence", 0) for f in fw_frameworks)
        fw_avg_conf = fw_conf_sum / len(fw_frameworks) if fw_frameworks else 50
        org_issues = data.get("code_organization", [])
        style_issues = data.get("code_style", [])
        issue_penalty = min(len(org_issues) * 3 + len(style_issues) * 3, 30)

        score = int(
            config_health * 0.25
            + maint_score * 0.25
            + arch_score * 0.15
            + fw_avg_conf * 0.10
            + (100 - issue_penalty) * 0.25
        )
        score = max(0, min(100, score))

        if score >= 85:
            classification = "Excellent"
        elif score >= 70:
            classification = "Good"
        elif score >= 50:
            classification = "Average"
        elif score >= 30:
            classification = "Needs Improvement"
        else:
            classification = "Critical"

        return score, classification

    @staticmethod
    def _gen_summary(data: dict) -> list[str]:
        lines: list[str] = []
        project_type = data.get("project_type", "Unknown")
        lines.append(f"This is a {project_type} project named \"{data.get('project_name', 'Unknown')}\".")

        arch = data.get("architecture", {})
        arch_name = arch.get("architecture", "Unknown") if arch else "Unknown"
        arch_conf = arch.get("confidence", 0) if arch else 0
        lines.append(f"Architecture detected as {arch_name} ({arch_conf}% confidence).")

        fw_frameworks = data.get("frameworks", [])
        if fw_frameworks:
            top_fw = sorted(fw_frameworks, key=lambda f: f.get("confidence", 0), reverse=True)
            fw_names = [f.get("name", "") for f in top_fw[:3] if f.get("name")]
            if fw_names:
                lines.append(f"Primary technologies: {', '.join(fw_names)}.")
        else:
            tech_stack = data.get("technology_stack", {})
            langs = tech_stack.get("languages", [])
            if langs:
                lines.append(f"Written in {', '.join(langs[:3])}.")

        total_files = data.get("total_files", 0)
        total_folders = data.get("total_folders", 0)
        lines.append(f"Codebase contains {total_files} files across {total_folders} directories.")

        folder_summary = data.get("folder_summary", {})
        source = folder_summary.get("source", 0) if folder_summary else 0
        tests = folder_summary.get("tests", 0) if folder_summary else 0
        if tests > 0:
            lines.append(f"Project has {tests} test directories ({tests / max(source + tests, 1) * 100:.0f}% of source).")
        else:
            lines.append("No dedicated test directories detected.")

        pi_maint = data.get("maintainability", {})
        maint_grade = pi_maint.get("grade", "N/A") if pi_maint else "N/A"
        maint_score = pi_maint.get("score", 0) if pi_maint else 0
        lines.append(f"Maintainability grade is {maint_grade} (score: {maint_score}/100).")

        config_detected = data.get("config_detected", [])
        config_missing = data.get("config_missing", [])
        if config_missing:
            lines.append(f"Configuration is incomplete — {len(config_missing)} required files missing.")
        elif config_detected:
            lines.append(f"Configuration is well maintained with {len(config_detected)} detected files.")

        org_issues = data.get("code_organization", [])
        style_issues = data.get("code_style", [])
        total_issues = len(org_issues) + len(style_issues)
        if total_issues > 10:
            lines.append(f"Code quality needs attention — {total_issues} issues detected (organization: {len(org_issues)}, style: {len(style_issues)}).")
        elif total_issues > 0:
            lines.append(f"Code quality is reasonable — {total_issues} minor issues detected.")
        else:
            lines.append("Code quality metrics look clean with no significant issues.")

        health = data.get("health_score", {})
        health_val = health.get("score", 0) if isinstance(health, dict) else 0
        lines.append(f"Overall project readiness score is {health_val}/100.")

        return lines

    @staticmethod
    def _gen_strengths(data: dict) -> list[dict]:
        strengths: list[dict] = []

        arch = data.get("architecture", {})
        arch_name = arch.get("architecture", "") if arch else ""
        arch_conf = arch.get("confidence", 0) if arch else 0
        if arch_conf >= 70:
            strengths.append({"category": "Architecture", "detail": f"Clear {arch_name} architecture detected with {arch_conf}% confidence."})

        fw_frameworks = data.get("frameworks", [])
        high_conf = [f for f in fw_frameworks if f.get("confidence", 0) >= 80]
        if high_conf:
            names = [f.get("name", "") for f in high_conf[:3]]
            strengths.append({"category": "Frameworks", "detail": f"Frameworks correctly configured: {', '.join(names)}."})

        mod_data = data.get("modules", [])
        detected_mods = [m for m in mod_data if m.get("status") == "Detected"]
        mod_summary = data.get("module_summary", {})
        mod_total = mod_summary.get("total_modules", 0) if mod_summary else 0
        if mod_total > 0 and len(detected_mods) >= mod_total * 0.7:
            strengths.append({"category": "Modularity", "detail": f"Good module separation — {len(detected_mods)}/{mod_total} standard modules detected."})

        config_scores = data.get("config_scores", {})
        config_health_val = config_scores.get("configuration_health", 0) if config_scores else 0
        if config_health_val >= 70:
            strengths.append({"category": "Configuration", "detail": f"Clean configuration with health score of {config_health_val}/100."})

        folder_summary = data.get("folder_summary", {})
        if folder_summary:
            if folder_summary.get("source", 0) > 0 and folder_summary.get("tests", 0) > 0:
                strengths.append({"category": "Testing", "detail": f"Test infrastructure present with {folder_summary.get('tests', 0)} test directories."})
            if folder_summary.get("docs", 0) > 0:
                strengths.append({"category": "Documentation", "detail": "Documentation directories found in project structure."})
            if folder_summary.get("scripts", 0) > 0:
                strengths.append({"category": "DevOps", "detail": "Build/script directories present for automation."})

        ci_data_list = data.get("cicd", [])
        configured_ci = [c for c in ci_data_list if c.get("configured")]
        if configured_ci:
            platforms = [c.get("platform", "") for c in configured_ci]
            strengths.append({"category": "CI/CD", "detail": f"CI/CD configured: {', '.join(platforms)}."})

        dep_val = data.get("dependency_validation", [])
        clean_deps = all(d.get("severity") != "error" for d in dep_val)
        if clean_deps and dep_val:
            strengths.append({"category": "Dependencies", "detail": "Dependency management appears clean with no critical issues."})

        if data.get("docker_validation", {}).get("has_dockerfile"):
            dv = data.get("docker_validation", {})
            docker_detail = "Docker support configured"
            if dv.get("multi_stage_build"):
                docker_detail += " with multi-stage builds"
            if dv.get("production_ready"):
                docker_detail += " and production readiness"
            strengths.append({"category": "Containerization", "detail": docker_detail + "."})

        if not strengths:
            strengths.append({"category": "General", "detail": "Project compiles and is structured as a valid software project."})

        return strengths

    @staticmethod
    def _gen_weaknesses(data: dict) -> list[dict]:
        weaknesses: list[dict] = []

        pi_maint = data.get("maintainability", {})
        maint_grade = pi_maint.get("grade", "") if pi_maint else ""
        if maint_grade in ("D", "F"):
            weaknesses.append({"category": "Maintainability", "detail": f"Low maintainability grade ({maint_grade}). Code may be difficult to maintain."})

        arch_recommendations = data.get("arch_recommendations", [])
        if arch_recommendations:
            for rec in arch_recommendations[:2]:
                weaknesses.append({"category": "Architecture", "detail": rec})

        config_missing = data.get("config_missing", [])
        if config_missing:
            missing_names = [c.get("file_name", "") for c in config_missing[:5]]
            weaknesses.append({"category": "Configuration", "detail": f"Missing {len(config_missing)} configuration files: {', '.join(missing_names)}."})

        config_warnings = data.get("config_warnings", [])
        high_warnings = [w for w in config_warnings if w.get("severity") in ("high", "critical")]
        if high_warnings:
            for w in high_warnings[:3]:
                weaknesses.append({"category": "Configuration", "detail": w.get("message", "Configuration warning.")})

        org_issues = data.get("code_organization", [])
        for issue in org_issues:
            itype = issue.get("type", "")
            detail = issue.get("detail", "")
            if itype == "duplicate_filename":
                weaknesses.append({"category": "Duplication", "detail": f"Duplicate filenames: {detail}."})
            elif itype == "duplicate_module":
                weaknesses.append({"category": "Duplication", "detail": f"Duplicate modules: {detail}."})
            elif itype == "empty_folder":
                weaknesses.append({"category": "Organization", "detail": f"Empty folders: {detail}."})
            elif itype == "large_file":
                weaknesses.append({"category": "File Size", "detail": f"Large files: {detail}."})

        style_issues = data.get("code_style", [])
        for issue in style_issues:
            itype = issue.get("type", "")
            detail = issue.get("detail", "")
            if itype == "long_function":
                weaknesses.append({"category": "Code Style", "detail": f"Long functions: {detail}."})
            elif itype == "long_class":
                weaknesses.append({"category": "Code Style", "detail": f"Large classes: {detail}."})
            elif itype == "mixed_naming":
                weaknesses.append({"category": "Code Style", "detail": f"Mixed naming conventions: {detail}."})
            elif itype == "large_imports":
                weaknesses.append({"category": "Code Style", "detail": f"Large imports: {detail}."})

        dep_val = data.get("dependency_validation", [])
        for d in dep_val:
            if d.get("severity") in ("error", "warning"):
                weaknesses.append({"category": "Dependencies", "detail": d.get("detail", "Dependency issue.")})

        sec_checks = data.get("security_checks", [])
        for s in sec_checks[:3]:
            weaknesses.append({"category": "Security", "detail": s.get("detail", "Security concern.")})

        env_val = data.get("environment_validation", [])
        for e in env_val[:3]:
            weaknesses.append({"category": "Environment", "detail": e.get("detail", "Environment concern.")})

        env_val_critical = [e for e in env_val if e.get("severity") in ("high", "critical")]
        if env_val_critical:
            weaknesses.append({"category": "Environment", "detail": f"{len(env_val_critical)} critical environment configuration issues found."})

        folder_summary = data.get("folder_summary", {})
        if folder_summary and folder_summary.get("tests", 0) == 0:
            weaknesses.append({"category": "Testing", "detail": "No test directories detected in project structure."})

        return weaknesses[:10]

    @staticmethod
    def _calc_risk(data: dict) -> tuple[str, int, str]:
        risk_score = 0
        factors: list[str] = []

        pi_maint = data.get("maintainability", {})
        maint_grade = pi_maint.get("grade", "") if pi_maint else ""
        if maint_grade == "F":
            risk_score += 25
            factors.append("critical maintainability grade")
        elif maint_grade == "D":
            risk_score += 15
            factors.append("low maintainability")
        elif maint_grade == "C":
            risk_score += 5

        config_missing = data.get("config_missing", [])
        if len(config_missing) > 5:
            risk_score += 15
            factors.append(f"{len(config_missing)} missing configuration files")
        elif len(config_missing) > 2:
            risk_score += 8
            factors.append(f"{len(config_missing)} missing configuration files")

        sec_checks = data.get("security_checks", [])
        high_sec = [s for s in sec_checks if s.get("severity") in ("high", "critical")]
        if high_sec:
            risk_score += min(len(high_sec) * 10, 25)
            factors.append(f"{len(high_sec)} security issues detected")

        complexity_data = data.get("complexity", {})
        max_cmplx = complexity_data.get("max_complexity", 0) if complexity_data else 0
        avg_cmplx = complexity_data.get("avg_cyclomatic_complexity", 0) if complexity_data else 0
        if max_cmplx > 50:
            risk_score += 15
            factors.append("very high cyclomatic complexity")
        elif max_cmplx > 20:
            risk_score += 8
            factors.append("high cyclomatic complexity")
        if avg_cmplx > 10:
            risk_score += 5

        env_val = data.get("environment_validation", [])
        critical_env = [e for e in env_val if e.get("severity") in ("high", "critical")]
        if critical_env:
            risk_score += 10
            factors.append(f"{len(critical_env)} critical environment issues")

        arch_health = data.get("arch_health", {})
        arch_score = arch_health.get("score", 100) if arch_health else 100
        if arch_score < 40:
            risk_score += 10
            factors.append("poor architecture health")

        risk_score = min(risk_score, 100)

        if risk_score >= 60:
            level = "Critical"
        elif risk_score >= 40:
            level = "High"
        elif risk_score >= 20:
            level = "Medium"
        else:
            level = "Low"

        explanation = f"Overall risk level is {level} (score: {risk_score}/100)."
        if factors:
            explanation += f" Contributing factors: {'; '.join(factors)}."
        else:
            explanation += " No significant risk factors identified."

        return level, risk_score, explanation

    @staticmethod
    def _calc_maintainability(data: dict) -> tuple[int, str, str]:
        pi_maint = data.get("maintainability", {})
        score = pi_maint.get("score", 50) if pi_maint else 50
        grade = pi_maint.get("grade", "C") if pi_maint else "C"

        cm_data = data.get("code_metrics", {})
        comment_ratio = cm_data.get("comment_ratio", 0) if cm_data else 0
        cx_data = data.get("complexity", {})
        avg_cx = cx_data.get("avg_cyclomatic_complexity", 0) if cx_data else 0
        org_issues = len(data.get("code_organization", []))
        style_issues = len(data.get("code_style", []))

        parts: list[str] = []
        if comment_ratio < 5:
            parts.append("very low documentation ({comment_ratio}%)")
        elif comment_ratio > 25:
            parts.append(f"good documentation ({comment_ratio}%)")
        if avg_cx > 10:
            parts.append(f"high average complexity ({avg_cx})")
        elif avg_cx <= 3:
            parts.append(f"low complexity ({avg_cx})")
        if org_issues > 0:
            parts.append(f"{org_issues} organization issues")
        if style_issues > 0:
            parts.append(f"{style_issues} style issues")
        if not parts:
            parts.append("all metrics within acceptable ranges")

        explanation = f"Maintainability grade {grade} (score: {score}/100). {'; '.join(parts)}."

        return score, grade, explanation

    @staticmethod
    def _calc_scalability(data: dict) -> tuple[str, str]:
        total_files = data.get("total_files", 0)
        total_folders = data.get("total_folders", 0)
        folder_summary = data.get("folder_summary", {})
        source = folder_summary.get("source", 0) if folder_summary else 0
        projects_stats = data.get("project_stats", {})
        total_source = sum(v for k, v in projects_stats.items() if isinstance(v, int)) if projects_stats else 0
        cx_data = data.get("complexity", {})
        avg_cx = cx_data.get("avg_cyclomatic_complexity", 0) if cx_data else 0
        arch = data.get("architecture", {})
        arch_name = arch.get("architecture", "") if arch else ""

        if total_files > 10000 and total_folders > 500:
            level = "Enterprise Ready"
            reason = f"Large-scale project ({total_files} files, {total_folders} dirs) with enterprise-level codebase size."
        elif total_files > 2000 or total_folders > 100:
            level = "Large"
            reason = f"Substantial project ({total_files} files, {total_folders} dirs) with room for modular growth."
        elif total_files > 300 or total_folders > 30:
            level = "Medium"
            reason = f"Moderate-sized project ({total_files} files, {total_folders} dirs). "
            if avg_cx <= 5:
                reason += "Complexity is well-managed for scaling."
            else:
                reason += "Reducing complexity would improve scalability."
        else:
            level = "Small"
            reason = f"Compact project ({total_files} files, {total_folders} dirs). "
            if arch_name:
                reason += f"Architecture ({arch_name}) supports future growth."
            else:
                reason += "Well-suited for rapid development and iteration."

        return level, reason

    @staticmethod
    def _gen_performance_insights(data: dict) -> list[dict]:
        insights: list[dict] = []

        largest_dirs = data.get("largest_directories", [])
        if largest_dirs:
            top_dir = largest_dirs[0]
            insights.append({"type": "heavy_folder", "detail": f"Largest directory: {top_dir.get('path', 'N/A')} ({top_dir.get('file_count', 0)} files, {top_dir.get('size', 0) / 1024:.0f} KB)."})
        if len(largest_dirs) >= 2:
            insights.append({"type": "heavy_folder", "detail": f"Top 3 directories contain significant portions of the codebase."})

        largest_files = data.get("largest_files", [])
        for lf in largest_files[:2]:
            size = lf.get("size", 0)
            lines = lf.get("lines", 0)
            if size > 500 * 1024 or lines > 2000:
                insights.append({"type": "large_asset", "detail": f"Large file: {lf.get('path', 'N/A')} ({lines} lines, {size / 1024:.0f} KB)."})

        cx_data = data.get("complexity", {})
        avg_cx = cx_data.get("avg_cyclomatic_complexity", 0) if cx_data else 0
        max_cx = cx_data.get("max_complexity", 0) if cx_data else 0
        if avg_cx > 8:
            insights.append({"type": "expensive_module", "detail": f"High average complexity ({avg_cx}) suggests expensive modules."})
        if max_cx > 30:
            insights.append({"type": "expensive_module", "detail": f"Maximum complexity of {max_cx} indicates a particularly expensive function."})

        org_issues = data.get("code_organization", [])
        deep_nests = [i for i in org_issues if i.get("type") == "deep_nesting"]
        for dn in deep_nests[:2]:
            insights.append({"type": "deep_nesting", "detail": dn.get("detail", "Deep directory nesting detected.")})

        dep_val = data.get("dependency_validation", [])
        deprecated_deps = [d for d in dep_val if d.get("type") == "deprecated"]
        if deprecated_deps:
            insights.append({"type": "heavy_dependency", "detail": f"{len(deprecated_deps)} deprecated dependencies may impact performance and security."})

        total_files = data.get("total_files", 0)
        if total_files > 5000:
            insights.append({"type": "heavy_folder", "detail": f"Large codebase ({total_files} files) may impact IDE performance and build times."})

        return insights[:6]

    @staticmethod
    def _gen_security_insights(data: dict) -> list[dict]:
        insights: list[dict] = []

        sec_checks = data.get("security_checks", [])
        for sc in sec_checks:
            insights.append({
                "type": sc.get("type", "security"),
                "severity": sc.get("severity", "info"),
                "detail": sc.get("detail", "Security issue."),
            })

        env_val = data.get("environment_validation", [])
        for ev in env_val:
            sev = ev.get("severity", "info")
            dtl = ev.get("detail", "")
            if "secret" in dtl.lower() or "password" in dtl.lower() or "key" in dtl.lower():
                insights.append({
                    "type": "secret_detected",
                    "severity": sev,
                    "detail": dtl,
                })
            elif "debug" in dtl.lower():
                insights.append({
                    "type": "debug_mode",
                    "severity": sev,
                    "detail": dtl,
                })
            elif "env" in dtl.lower():
                insights.append({
                    "type": "env_config",
                    "severity": sev,
                    "detail": dtl,
                })

        config_scores_data = data.get("config_scores", {})
        sec_score = config_scores_data.get("security", 0) if config_scores_data else 0
        if sec_score < 50:
            insights.append({
                "type": "weak_config",
                "severity": "warning",
                "detail": f"Configuration security score is low ({sec_score}/100). Review security settings.",
            })

        dep_val = data.get("dependency_validation", [])
        unsafe_deps = [d for d in dep_val if d.get("severity") in ("error", "critical")]
        if unsafe_deps:
            for d in unsafe_deps[:3]:
                insights.append({
                    "type": "unsafe_dependency",
                    "severity": d.get("severity", "warning"),
                    "detail": d.get("detail", "Unsafe dependency version detected."),
                })

        config_detected = data.get("config_detected", [])
        detected_names = [c.get("file_name", "").lower() for c in config_detected]
        has_env = any(".env" in n for n in detected_names)
        has_env_example = any("env.example" in n or "env.sample" in n for n in detected_names)
        if not has_env and not has_env_example:
            insights.append({
                "type": "env_config",
                "severity": "warning",
                "detail": "No .env or .env.example file found. Environment configuration may be insecure.",
            })

        return insights[:8]

    @staticmethod
    def _gen_code_quality_insights(data: dict) -> list[dict]:
        insights: list[dict] = []

        org_issues = data.get("code_organization", [])
        for oi in org_issues:
            itype = oi.get("type", "")
            if itype == "duplicate_filename":
                insights.append({"type": "duplicate_module", "detail": oi.get("detail", "")})
            elif itype == "empty_folder":
                insights.append({"type": "dead_code", "detail": f"Empty folders: {oi.get('detail', '')}."})

        style_issues = data.get("code_style", [])
        for si in style_issues:
            itype = si.get("type", "")
            if itype == "long_class":
                insights.append({"type": "large_class", "detail": si.get("detail", "")})
            elif itype == "long_function":
                insights.append({"type": "large_function", "detail": si.get("detail", "")})
            elif itype == "mixed_naming":
                insights.append({"type": "naming_inconsistency", "detail": si.get("detail", "")})

        cx_data = data.get("complexity", {})
        high_count = cx_data.get("high_count", 0) if cx_data else 0
        critical_count = cx_data.get("critical_count", 0) if cx_data else 0
        if high_count > 0 or critical_count > 0:
            insights.append({"type": "large_function", "detail": f"{high_count} functions with high complexity and {critical_count} with critical complexity."})

        if not insights:
            insights.append({"type": "clean", "detail": "No significant code quality issues detected."})

        return insights[:8]

    @staticmethod
    def _gen_recommended_actions(data: dict) -> list[dict]:
        actions: list[dict] = []
        seen: set[str] = set()

        def add_action(action: str, priority: str):
            key = action.lower().strip()
            if key not in seen:
                seen.add(key)
                actions.append({"action": action, "priority": priority})

        pi_maint = data.get("maintainability", {})
        maint_grade = pi_maint.get("grade", "") if pi_maint else ""
        if maint_grade in ("D", "F"):
            add_action("Improve code maintainability by reducing complexity and increasing documentation coverage", "high")
        elif maint_grade == "C":
            add_action("Address code organization issues to improve maintainability from C grade", "medium")

        config_missing = data.get("config_missing", [])
        if config_missing:
            missing_names = [c.get("file_name", "") for c in config_missing[:5]]
            add_action(f"Add missing configuration files: {', '.join(missing_names)}", "high")

        sec_checks = data.get("security_checks", [])
        high_sec = [s for s in sec_checks if s.get("severity") in ("high", "critical")]
        if high_sec:
            add_action(f"Address {len(high_sec)} critical security issues found in configuration", "high")

        org_issues = data.get("code_organization", [])
        for oi in org_issues:
            if oi.get("type") == "duplicate_filename":
                add_action("Rename duplicate files to avoid confusion and potential build conflicts", "medium")
            elif oi.get("type") == "empty_folder":
                add_action("Remove or populate empty directories to keep the project structure clean", "low")
            elif oi.get("type") == "large_file":
                add_action(f"Split large files into smaller modules: {oi.get('detail', '')}", "medium")

        style_issues = data.get("code_style", [])
        for si in style_issues:
            if si.get("type") == "long_function":
                add_action("Refactor long functions into smaller, focused helper functions", "medium")
            elif si.get("type") == "long_class":
                add_action("Split large classes following single responsibility principle", "medium")
            elif si.get("type") == "mixed_naming":
                add_action("Standardize naming conventions across the codebase", "low")

        cx_data = data.get("complexity", {})
        high_cx = cx_data.get("high_count", 0) if cx_data else 0
        critical_cx = cx_data.get("critical_count", 0) if cx_data else 0
        if high_cx > 5 or critical_cx > 0:
            add_action(f"Reduce cyclomatic complexity in {high_cx} high-complexity and {critical_cx} critical-complexity functions", "high")

        env_val = data.get("environment_validation", [])
        critical_env = [e for e in env_val if e.get("severity") in ("high", "critical")]
        if critical_env:
            add_action(f"Resolve {len(critical_env)} critical environment configuration issues", "high")

        arch_recommendations = data.get("arch_recommendations", [])
        for rec in arch_recommendations[:2]:
            add_action(rec, "medium")

        dep_val = data.get("dependency_validation", [])
        deprecated_deps = [d for d in dep_val if d.get("type") == "deprecated"]
        if deprecated_deps:
            add_action(f"Update {len(deprecated_deps)} deprecated dependencies to supported versions", "medium")

        if not actions:
            add_action("Project is in good shape. Continue maintaining current standards", "low")

        return actions[:10]

    @staticmethod
    def _calc_readiness_scores(data: dict) -> list[dict]:
        scores: list[dict] = []

        config_scores_data = data.get("config_scores", {})
        config_health = config_scores_data.get("configuration_health", 0) if config_scores_data else 0
        config_readiness = config_scores_data.get("readiness", 0) if config_scores_data else 0
        config_security = config_scores_data.get("security", 0) if config_scores_data else 0
        config_maint = config_scores_data.get("maintainability", 0) if config_scores_data else 0

        scores.append({"category": "Deployment Readiness", "score": config_readiness})
        scores.append({"category": "Production Readiness", "score": config_readiness})

        pi_maint = data.get("maintainability", {})
        maint_score = pi_maint.get("score", 0) if pi_maint else 0
        scores.append({"category": "Maintainability", "score": maint_score})

        scores.append({"category": "Security", "score": config_security})

        sec_checks = data.get("security_checks", [])
        env_val = data.get("environment_validation", [])
        perf_penalty = min(len(sec_checks) * 5 + len(env_val) * 3, 30)
        perf_score = max(0, 100 - perf_penalty)
        scores.append({"category": "Performance", "score": perf_score})

        arch_health = data.get("arch_health", {})
        arch_score = arch_health.get("score", 50) if arch_health else 50
        scores.append({"category": "Architecture", "score": arch_score})

        config_summary = data.get("config_summary", {})
        has_readme = config_summary.get("has_readme", False) if config_summary else False
        doc_score = 30 if has_readme else 0
        folder_summary = data.get("folder_summary", {})
        if folder_summary and folder_summary.get("docs", 0) > 0:
            doc_score += 40
        config_missing = data.get("config_missing", [])
        if config_missing:
            doc_score -= len([c for c in config_missing if "readme" in c.get("file_name", "").lower()]) * 10
        doc_score = max(0, min(100, doc_score))
        scores.append({"category": "Documentation", "score": doc_score})

        test_score = 0
        if folder_summary and folder_summary.get("tests", 0) > 0:
            test_score = 60
            source_count = folder_summary.get("source", 0)
            test_count = folder_summary.get("tests", 0)
            test_ratio_pts = int((test_count / max(source_count + test_count, 1)) * 40)
            test_score = min(100, test_score + test_ratio_pts)
        scores.append({"category": "Testing", "score": test_score})

        return scores[:8]
