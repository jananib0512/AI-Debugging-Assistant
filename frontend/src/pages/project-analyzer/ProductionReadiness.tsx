import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Award,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Cpu,
  Database,
  FileText,
  RefreshCw,
  Server,
  Shield,
  Zap,
} from "lucide-react";
import { getProductionReadiness } from "@/lib/project-analyzer";
import type { ProductionReadinessResponse } from "@/types/project-analyzer";

const severityColors: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]",
  high: "bg-[#FFF7ED] text-[#9A3412] border-[#FED7AA]",
  medium: "bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]",
  low: "bg-[#F3F4F6] text-[#374151] border-[#E5E7EB]",
};

const severityBg: Record<string, string> = {
  critical: "bg-[#DC2626]",
  high: "bg-[#EA580C]",
  medium: "bg-[#D97706]",
  low: "bg-[#6B7280]",
};

function scoreColor(score: number): string {
  if (score >= 80) return "text-[#059669]";
  if (score >= 60) return "text-[#D97706]";
  if (score >= 40) return "text-[#EA580C]";
  return "text-[#DC2626]";
}

function scoreBg(score: number): string {
  if (score >= 80) return "bg-[#ECFDF5]";
  if (score >= 60) return "bg-[#FFFBEB]";
  if (score >= 40) return "bg-[#FFF7ED]";
  return "bg-[#FEF2F2]";
}

function classificationColor(cls: string): string {
  if (cls === "Production Ready") return "text-[#059669]";
  if (cls === "Nearly Ready") return "text-[#D97706]";
  if (cls === "Needs Improvement") return "text-[#EA580C]";
  if (cls === "High Risk") return "text-[#DC2626]";
  return "text-[#6B7280]";
}

function classificationBg(cls: string): string {
  if (cls === "Production Ready") return "bg-[#ECFDF5]";
  if (cls === "Nearly Ready") return "bg-[#FFFBEB]";
  if (cls === "Needs Improvement") return "bg-[#FFF7ED]";
  if (cls === "High Risk") return "bg-[#FEF2F2]";
  return "bg-[#F3F4F6]";
}

const catLabels: Record<string, string> = {
  architecture_readiness: "Architecture",
  security_readiness: "Security",
  performance_readiness: "Performance",
  dependency_health: "Dependency Health",
  configuration_health: "Configuration",
  environment_configuration: "Environment Config",
  logging_configuration: "Logging",
  monitoring_support: "Monitoring",
  error_handling: "Error Handling",
  exception_handling: "Exception Handling",
  documentation_readiness: "Documentation",
  testing_readiness: "Testing",
  cicd_readiness: "CI/CD",
};

export function ProductionReadiness() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState<ProductionReadinessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef(false);

  const filterCategory = searchParams.get("category") || "";
  const filterSeverity = searchParams.get("severity") || "";
  const filterReadiness = searchParams.get("readiness") || "";
  const [expandedFinding, setExpandedFinding] = useState<string | null>(null);

  const fetchData = () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    getProductionReadiness(Number(projectId))
      .then((res) => {
        setData(res);
        fetchedRef.current = true;
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to load production readiness";
        setError(msg);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (projectId && !fetchedRef.current) {
      fetchData();
    }
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative mb-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        </div>
        <p className="text-sm font-medium text-[#111827]">Evaluating production readiness...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Analyzing deployment, configuration, and operational readiness.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Evaluation failed</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button
          onClick={fetchData}
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Server className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No readiness data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run project analysis to evaluate production readiness.</p>
      </div>
    );
  }

  const { production_score, category_scores, findings, deployment, config_validation, release_readiness, observability, summary } = data;

  const filteredFindings = findings.filter((f) => {
    if (filterCategory && f.category !== filterCategory) return false;
    if (filterSeverity && f.severity !== filterSeverity) return false;
    return true;
  });

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next, { replace: true });
  };

  const uniqueCategories = [...new Set(findings.map((f) => f.category).filter(Boolean))];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-[#93C5FD]">Phase 3C.8</p>
            <h1 className="mt-1 text-2xl font-bold">Production Readiness</h1>
            <p className="mt-1 text-sm text-[#BFDBFE]">
              Enterprise-grade assessment of production deployment readiness
            </p>
          </div>
          <button
            onClick={fetchData}
            className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm transition-colors hover:bg-white/30"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Production Score */}
      <div className="grid gap-4 md:grid-cols-5">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5 md:col-span-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Overall Production Score</p>
          <div className="mt-3 flex items-baseline gap-2">
            <span className={`text-5xl font-bold ${scoreColor(production_score.overall_production_score)}`}>
              {production_score.overall_production_score}
            </span>
            <span className="text-sm text-[#6B7280]">/ 100</span>
          </div>
          <div className="mt-2">
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${classificationBg(summary.classification)} ${classificationColor(summary.classification)}`}>
              {summary.classification}
            </span>
          </div>
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#6B7280]">Deployment Readiness</span>
              <span className={`font-semibold ${scoreColor(production_score.deployment_readiness)}`}>
                {production_score.deployment_readiness}%
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#6B7280]">Operational Readiness</span>
              <span className={`font-semibold ${scoreColor(production_score.operational_readiness)}`}>
                {production_score.operational_readiness}%
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#6B7280]">Maintainability Readiness</span>
              <span className={`font-semibold ${scoreColor(production_score.maintainability_readiness)}`}>
                {production_score.maintainability_readiness}%
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#6B7280]">AI Confidence</span>
              <span className={`font-semibold ${scoreColor(production_score.ai_confidence)}`}>
                {production_score.ai_confidence}%
              </span>
            </div>
          </div>
        </div>

        {/* Category Scores Grid */}
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5 md:col-span-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Category Scores</p>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
            {Object.entries(catLabels).map(([key, label]) => {
              const val = (category_scores as unknown as Record<string, number>)[key] ?? 0;
              return (
                <div key={key} className={`rounded-lg ${scoreBg(val)} px-3 py-2`}>
                  <p className="text-[10px] font-medium text-[#6B7280]">{label}</p>
                  <p className={`mt-0.5 text-sm font-bold ${scoreColor(val)}`}>{val}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* AI Summary */}
      <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <div className="flex items-center gap-2">
          <Award className="h-4 w-4 text-[#2563EB]" />
          <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">AI Production Summary</p>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-[#374151]">{summary.summary_text}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="rounded bg-[#FEF2F2] px-2 py-0.5 text-[10px] font-medium text-[#991B1B]">{summary.critical_count} Critical</span>
          <span className="rounded bg-[#FFF7ED] px-2 py-0.5 text-[10px] font-medium text-[#9A3412]">{summary.high_count} High</span>
          <span className="rounded bg-[#FFFBEB] px-2 py-0.5 text-[10px] font-medium text-[#92400E]">{summary.medium_count} Medium</span>
          <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#374151]">{summary.low_count} Low</span>
          <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[10px] font-medium text-[#1E40AF]">{summary.total_findings} Total</span>
        </div>
      </div>

      {/* Deployment Validation */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-[#2563EB]" />
            <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Deployment & CI/CD</p>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {[
              { key: "has_dockerfile", label: "Dockerfile" },
              { key: "has_docker_compose", label: "Docker Compose" },
              { key: "has_kubernetes", label: "Kubernetes" },
              { key: "has_helm_charts", label: "Helm Charts" },
              { key: "has_github_actions", label: "GitHub Actions" },
              { key: "has_gitlab_ci", label: "GitLab CI" },
              { key: "has_azure_pipelines", label: "Azure Pipelines" },
              { key: "has_jenkins", label: "Jenkins" },
              { key: "has_render_config", label: "Render" },
              { key: "has_railway_config", label: "Railway" },
              { key: "has_vercel_config", label: "Vercel" },
              { key: "has_netlify_config", label: "Netlify" },
              { key: "has_deployment_scripts", label: "Deployment Scripts" },
            ].map(({ key, label }) => {
              const val = (deployment as unknown as Record<string, boolean>)[key] ?? false;
              return (
                <div key={key} className="flex items-center gap-2 rounded-lg bg-[#F9FAFB] px-3 py-2">
                  {val ? (
                    <CheckCircle className="h-3.5 w-3.5 shrink-0 text-[#059669]" />
                  ) : (
                    <div className="h-3.5 w-3.5 shrink-0 rounded-full border border-[#D1D5DB]" />
                  )}
                  <span className="text-xs text-[#374151]">{label}</span>
                </div>
              );
            })}
          </div>
          {deployment.detected_platforms.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              <span className="text-[10px] font-medium text-[#6B7280]">Detected:</span>
              {deployment.detected_platforms.map((p) => (
                <span key={p} className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[10px] font-medium text-[#1E40AF]">
                  {p}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          {/* Config Validation */}
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-[#2563EB]" />
              <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Configuration</p>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {[
                { key: "has_environment_variables", label: "Environment Variables" },
                { key: "has_env_file", label: ".env File" },
                { key: "has_production_config", label: "Production Config" },
                { key: "has_development_config", label: "Development Config" },
                { key: "has_secret_management", label: "Secret Management" },
                { key: "has_database_config", label: "Database Config" },
                { key: "has_cache_config", label: "Cache Config" },
              ].map(({ key, label }) => {
                const val = (config_validation as unknown as Record<string, boolean>)[key] ?? false;
                return (
                  <div key={key} className="flex items-center gap-2 rounded-lg bg-[#F9FAFB] px-3 py-2">
                    {val ? (
                      <CheckCircle className="h-3.5 w-3.5 shrink-0 text-[#059669]" />
                    ) : (
                      <div className="h-3.5 w-3.5 shrink-0 rounded-full border border-[#D1D5DB]" />
                    )}
                    <span className="text-xs text-[#374151]">{label}</span>
                  </div>
                );
              })}
            </div>
            {config_validation.env_var_count > 0 && (
              <p className="mt-2 text-[10px] text-[#6B7280]">{config_validation.env_var_count} environment variables detected</p>
            )}
          </div>

          {/* Release Readiness */}
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-[#2563EB]" />
              <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Release Readiness</p>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {[
                { key: "has_versioning", label: "Versioning" },
                { key: "has_release_notes", label: "Release Notes" },
                { key: "has_build_scripts", label: "Build Scripts" },
                { key: "has_startup_scripts", label: "Startup Scripts" },
                { key: "has_shutdown_handling", label: "Shutdown Handling" },
                { key: "has_health_checks", label: "Health Checks" },
              ].map(({ key, label }) => {
                const val = (release_readiness as unknown as Record<string, boolean>)[key] ?? false;
                return (
                  <div key={key} className="flex items-center gap-2 rounded-lg bg-[#F9FAFB] px-3 py-2">
                    {val ? (
                      <CheckCircle className="h-3.5 w-3.5 shrink-0 text-[#059669]" />
                    ) : (
                      <div className="h-3.5 w-3.5 shrink-0 rounded-full border border-[#D1D5DB]" />
                    )}
                    <span className="text-xs text-[#374151]">{label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Observability */}
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-[#2563EB]" />
              <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Observability</p>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {[
                { key: "has_logging", label: "Logging" },
                { key: "has_monitoring", label: "Monitoring" },
                { key: "has_metrics", label: "Metrics" },
                { key: "has_tracing", label: "Tracing" },
                { key: "has_health_endpoints", label: "Health Endpoints" },
              ].map(({ key, label }) => {
                const val = (observability as unknown as Record<string, boolean>)[key] ?? false;
                return (
                  <div key={key} className="flex items-center gap-2 rounded-lg bg-[#F9FAFB] px-3 py-2">
                    {val ? (
                      <CheckCircle className="h-3.5 w-3.5 shrink-0 text-[#059669]" />
                    ) : (
                      <div className="h-3.5 w-3.5 shrink-0 rounded-full border border-[#D1D5DB]" />
                    )}
                    <span className="text-xs text-[#374151]">{label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Filters:</p>
        <select
          value={filterCategory}
          onChange={(e) => setFilter("category", e.target.value)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1.5 text-xs text-[#374151]"
        >
          <option value="">All Categories</option>
          {uniqueCategories.map((c) => (
            <option key={c} value={c}>{catLabels[c as keyof typeof catLabels] || c}</option>
          ))}
        </select>
        <select
          value={filterSeverity}
          onChange={(e) => setFilter("severity", e.target.value)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1.5 text-xs text-[#374151]"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={filterReadiness}
          onChange={(e) => setFilter("readiness", e.target.value)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1.5 text-xs text-[#374151]"
        >
          <option value="">All Classifications</option>
          <option value="Production Ready">Production Ready</option>
          <option value="Nearly Ready">Nearly Ready</option>
          <option value="Needs Improvement">Needs Improvement</option>
          <option value="High Risk">High Risk</option>
          <option value="Not Ready">Not Ready</option>
        </select>
        {(filterCategory || filterSeverity || filterReadiness) && (
          <button
            onClick={() => setSearchParams({}, { replace: true })}
            className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1.5 text-xs text-[#6B7280] hover:bg-[#F9FAFB]"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Findings */}
      {filteredFindings.length === 0 ? (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-8 text-center">
          <CheckCircle className="mx-auto mb-2 h-8 w-8 text-[#059669]" />
          <p className="text-sm font-medium text-[#111827]">No findings match the current filters</p>
          <p className="mt-1 text-xs text-[#6B7280]">
            {findings.length === 0 ? "All production readiness checks passed." : "Try adjusting your filter criteria."}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Findings ({filteredFindings.length})
          </p>
          {filteredFindings.map((f, i) => {
            const isExpanded = expandedFinding === `${f.category}-${i}`;
            return (
              <div
                key={`${f.category}-${i}`}
                className="rounded-xl border border-[#E5E7EB] bg-white transition-all hover:shadow-sm"
              >
                <button
                  onClick={() => setExpandedFinding(isExpanded ? null : `${f.category}-${i}`)}
                  className="flex w-full items-center justify-between px-5 py-3 text-left"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`h-2 w-2 shrink-0 rounded-full ${severityBg[f.severity] || "bg-[#6B7280]"}`} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-[#111827] truncate">{f.name}</p>
                      <p className="text-[10px] text-[#6B7280]">
                        {catLabels[f.category as keyof typeof catLabels] || f.category}
                        {f.affected_files.length > 0 && ` · ${f.affected_files.length} file(s)`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`rounded border px-2 py-0.5 text-[10px] font-medium ${severityColors[f.severity] || severityColors.low}`}>
                      {f.severity.toUpperCase()}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="h-3.5 w-3.5 text-[#9CA3AF]" />
                    ) : (
                      <ChevronDown className="h-3.5 w-3.5 text-[#9CA3AF]" />
                    )}
                  </div>
                </button>
                {isExpanded && (
                  <div className="border-t border-[#E5E7EB] px-5 py-4 space-y-3">
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Description</p>
                      <p className="mt-1 text-sm text-[#374151]">{f.detail}</p>
                    </div>
                    {f.affected_files.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Files</p>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {f.affected_files.map((file, fi) => (
                            <span key={fi} className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-mono text-[#374151]">
                              {file}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {f.affected_components.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Components</p>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {f.affected_components.map((comp, ci) => (
                            <span key={ci} className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[10px] font-medium text-[#1E40AF]">
                              {comp}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="grid gap-3 sm:grid-cols-2">
                      {f.deployment_impact && (
                        <div className="rounded-lg bg-[#F9FAFB] px-3 py-2">
                          <p className="text-[10px] font-semibold text-[#6B7280]">Deployment Impact</p>
                          <p className="mt-0.5 text-xs text-[#374151]">{f.deployment_impact}</p>
                        </div>
                      )}
                      {f.business_impact && (
                        <div className="rounded-lg bg-[#F9FAFB] px-3 py-2">
                          <p className="text-[10px] font-semibold text-[#6B7280]">Business Impact</p>
                          <p className="mt-0.5 text-xs text-[#374151]">{f.business_impact}</p>
                        </div>
                      )}
                    </div>
                    {f.ai_recommendation && (
                      <div className="rounded-lg bg-[#EFF6FF] px-3 py-2">
                        <div className="flex items-center gap-1.5">
                          <Shield className="h-3 w-3 text-[#2563EB]" />
                          <p className="text-[10px] font-semibold text-[#2563EB]">AI Recommendation</p>
                        </div>
                        <p className="mt-0.5 text-xs text-[#374151]">{f.ai_recommendation}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Recommendations */}
      {summary.prioritized_recommendations.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-[#2563EB]" />
            <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Prioritized Recommendations</p>
          </div>
          <div className="mt-3 space-y-2">
            {summary.prioritized_recommendations.map((rec, i) => {
              const sevMatch = rec.match(/^\[(CRITICAL|HIGH|MEDIUM|LOW)\]/);
              const sev = sevMatch?.[1]?.toLowerCase() ?? "info";
              return (
                <div key={i} className="flex items-start gap-2 rounded-lg bg-[#F9FAFB] px-3 py-2">
                  <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${severityBg[sev] || "bg-[#6B7280]"}`} />
                  <p className="text-xs text-[#374151]">{rec}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </motion.div>
  );
}
