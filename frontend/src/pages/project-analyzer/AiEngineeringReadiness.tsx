import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Award,
  BarChart3,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Cpu,
  CpuIcon,
  FileCode,
  FileSearch,
  FlaskConical,
  RefreshCw,
  Shield,
  TrendingUp,
  Zap,
} from "lucide-react";
import { getAiEngineeringReadiness } from "@/lib/project-analyzer";
import type { AiEngineeringReadinessResponse } from "@/types/project-analyzer";

const severityColors: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]",
  high: "bg-[#FFF7ED] text-[#9A3412] border-[#FED7AA]",
  medium: "bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]",
  low: "bg-[#F3F4F6] text-[#374151] border-[#E5E7EB]",
};

function scoreColor(v: number): string {
  if (v >= 70) return "text-[#059669]";
  if (v >= 40) return "text-[#D97706]";
  return "text-[#DC2626]";
}

function scoreBg(v: number): string {
  if (v >= 70) return "bg-[#059669]";
  if (v >= 40) return "bg-[#D97706]";
  return "bg-[#DC2626]";
}

function statusColor(status: string): string {
  if (status === "ready") return "text-[#059669] bg-[#ECFDF5]";
  if (status === "needs-work") return "text-[#D97706] bg-[#FFFBEB]";
  if (status === "not-ready") return "text-[#DC2626] bg-[#FEF2F2]";
  return "text-[#6B7280] bg-[#F3F4F6]";
}

const healthKeys: { key: keyof AiEngineeringReadinessResponse["project_health"]; label: string; icon: typeof BarChart3 }[] = [
  { key: "architecture_health", label: "Architecture", icon: Cpu },
  { key: "code_health", label: "Code", icon: FileCode },
  { key: "dependency_health", label: "Dependencies", icon: BarChart3 },
  { key: "security_health", label: "Security", icon: Shield },
  { key: "performance_health", label: "Performance", icon: Zap },
  { key: "maintainability_health", label: "Maintainability", icon: TrendingUp },
  { key: "documentation_health", label: "Documentation", icon: FileSearch },
  { key: "testing_health", label: "Testing", icon: FlaskConical },
  { key: "production_health", label: "Production", icon: CpuIcon },
];

export function AiEngineeringReadiness() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState<AiEngineeringReadinessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef(false);

  const filterSeverity = searchParams.get("severity") || "";
  const filterModule = searchParams.get("module") || "";
  const [expandedFinding, setExpandedFinding] = useState<string | null>(null);

  const fetchData = () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    getAiEngineeringReadiness(Number(projectId))
      .then((res) => {
        setData(res);
        fetchedRef.current = true;
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to load AI engineering readiness";
        setError(msg);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative mb-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        </div>
        <p className="text-sm font-medium text-[#111827]">Evaluating AI Software Engineering Readiness...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Combining all intelligence engines into a unified assessment.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Evaluation failed</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button onClick={fetchData} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Cpu className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No readiness data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run project analysis to evaluate AI engineering readiness.</p>
      </div>
    );
  }

  const { engineering_score, capabilities, project_health, findings, repair_readiness, roadmap, summary } = data;

  const filteredFindings = findings.filter((f) => {
    if (filterSeverity && f.severity !== filterSeverity) return false;
    if (filterModule && !f.affected_modules.includes(filterModule)) return false;
    return true;
  });

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next, { replace: true });
  };

  const allModules = [...new Set(findings.flatMap((f) => f.affected_modules))];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#7C3AED] to-[#2563EB] p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-[#A78BFA]">Phase 3C.9</p>
            <h1 className="mt-1 text-2xl font-bold">AI Readiness</h1>
            <p className="mt-1 text-sm text-[#C4B5FD]">
              Final decision engine — determines readiness for automated bug detection, AI repair, and project regeneration
            </p>
          </div>
          <button onClick={fetchData} className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm transition-colors hover:bg-white/30">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        </div>
      </div>

      {/* Engineering Score */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Engineering Score</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-5xl font-bold ${scoreColor(engineering_score.overall_engineering_score)}`}>
              {engineering_score.overall_engineering_score}
            </span>
            <span className="text-sm text-[#6B7280]">/ 100</span>
          </div>
          <div className="mt-4 space-y-1.5">
            <div className="flex items-center justify-between text-xs"><span className="text-[#6B7280]">Engineering Readiness</span><span className={`font-semibold ${scoreColor(engineering_score.engineering_readiness)}`}>{engineering_score.engineering_readiness}%</span></div>
            <div className="flex items-center justify-between text-xs"><span className="text-[#6B7280]">AI Confidence</span><span className={`font-semibold ${scoreColor(engineering_score.ai_confidence)}`}>{engineering_score.ai_confidence}%</span></div>
            <div className="flex items-center justify-between text-xs"><span className="text-[#6B7280]">Repair Readiness</span><span className={`font-semibold ${scoreColor(engineering_score.repair_readiness)}`}>{engineering_score.repair_readiness}%</span></div>
            <div className="flex items-center justify-between text-xs"><span className="text-[#6B7280]">Automation Readiness</span><span className={`font-semibold ${scoreColor(engineering_score.automation_readiness)}`}>{engineering_score.automation_readiness}%</span></div>
            <div className="flex items-center justify-between text-xs"><span className="text-[#6B7280]">Project Stability</span><span className={`font-semibold ${scoreColor(engineering_score.project_stability)}`}>{engineering_score.project_stability}%</span></div>
          </div>
        </div>

        {/* Capabilities */}
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5 md:col-span-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Engineering Capabilities</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {capabilities.map((cap) => (
              <div key={cap.name} className="rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-[#111827]">{cap.name.replace(" Readiness", "")}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[9px] font-medium ${statusColor(cap.status)}`}>
                    {cap.status.replace("-", " ")}
                  </span>
                </div>
                <div className="mt-1.5 flex items-center gap-2">
                  <div className="h-1.5 flex-1 rounded-full bg-[#F3F4F6] overflow-hidden">
                    <div className={`h-full rounded-full ${scoreBg(cap.score)}`} style={{ width: `${Math.min(cap.score, 100)}%` }} />
                  </div>
                  <span className={`text-[10px] font-semibold ${scoreColor(cap.score)}`}>{Math.round(cap.score)}</span>
                </div>
                {cap.requirements.length > 0 && (
                  <p className="mt-1 text-[9px] text-[#6B7280] truncate" title={cap.requirements[0]}>
                    {cap.requirements[0]}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Summary */}
      <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <div className="flex items-center gap-2">
          <Award className="h-4 w-4 text-[#7C3AED]" />
          <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">AI Software Engineer Summary</p>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-[#374151]">{summary.summary_text}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="rounded bg-[#ECFDF5] px-2 py-0.5 text-[10px] font-medium text-[#065F46]">{summary.capabilities_ready}/{summary.capabilities_total} capabilities ready</span>
          <span className="rounded bg-[#FEF2F2] px-2 py-0.5 text-[10px] font-medium text-[#991B1B]">{summary.critical_findings} critical</span>
          <span className="rounded bg-[#FFF7ED] px-2 py-0.5 text-[10px] font-medium text-[#9A3412]">{summary.high_findings} high</span>
        </div>
      </div>

      {/* Project Health */}
      <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Health</p>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {healthKeys.map(({ key, label, icon: Icon }) => {
            const val = project_health[key] ?? 50;
            return (
              <div key={key} className="rounded-lg border border-[#E5E7EB] p-3">
                <div className="flex items-center gap-1.5">
                  <Icon className={`h-3 w-3 ${scoreColor(val)}`} />
                  <span className="text-[10px] font-medium text-[#6B7280]">{label}</span>
                </div>
                <p className={`mt-1 text-lg font-bold ${scoreColor(val)}`}>{Math.round(val)}</p>
                <div className="mt-1 h-1.5 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                  <div className={`h-full rounded-full ${scoreBg(val)}`} style={{ width: `${Math.min(val, 100)}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Repair Readiness */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-[#7C3AED]" />
            <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Automated Repair Readiness</p>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <div className="rounded-lg bg-[#ECFDF5] px-3 py-2">
              <p className="text-[10px] font-medium text-[#065F46]">Safe to Modify</p>
              <p className="text-lg font-bold text-[#065F46]">{repair_readiness.files_safe_to_modify}</p>
            </div>
            <div className="rounded-lg bg-[#FEF2F2] px-3 py-2">
              <p className="text-[10px] font-medium text-[#991B1B]">High Risk</p>
              <p className="text-lg font-bold text-[#991B1B]">{repair_readiness.high_risk_files}</p>
            </div>
            <div className="rounded-lg bg-[#F3F4F6] px-3 py-2">
              <p className="text-[10px] font-medium text-[#374151]">Protected Files</p>
              <p className="text-lg font-bold text-[#374151]">{repair_readiness.protected_files}</p>
            </div>
            <div className="rounded-lg bg-[#FFFBEB] px-3 py-2">
              <p className="text-[10px] font-medium text-[#92400E]">Config Files</p>
              <p className="text-lg font-bold text-[#92400E]">{repair_readiness.configuration_files}</p>
            </div>
            <div className="rounded-lg bg-[#EFF6FF] px-3 py-2">
              <p className="text-[10px] font-medium text-[#1E40AF]">Core Modules</p>
              <p className="text-lg font-bold text-[#1E40AF]">{repair_readiness.core_modules}</p>
            </div>
            <div className="rounded-lg bg-[#F5F3FF] px-3 py-2">
              <p className="text-[10px] font-medium text-[#5B21B6]">Utility Modules</p>
              <p className="text-lg font-bold text-[#5B21B6]">{repair_readiness.utility_modules}</p>
            </div>
          </div>
        </div>

        {/* Engineering Roadmap */}
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-[#7C3AED]" />
            <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Engineering Roadmap</p>
          </div>
          <div className="mt-3 space-y-2">
            {roadmap.map((stage) => (
              <div key={stage.step} className="flex items-center gap-3 rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-3 py-2">
                <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white ${stage.status === "ready" ? "bg-[#059669]" : stage.status === "needs-work" ? "bg-[#D97706]" : "bg-[#9CA3AF]"}`}>
                  {stage.step}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-[#111827]">{stage.name}</p>
                  <p className="text-[9px] text-[#6B7280] truncate">{stage.detail}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`rounded-full px-1.5 py-0.5 text-[8px] font-medium ${statusColor(stage.status)}`}>
                    {stage.status.replace("-", " ")}
                  </span>
                  <span className={`text-[9px] font-semibold ${scoreColor(stage.readiness)}`}>
                    {Math.round(stage.readiness)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Filters:</p>
        <select value={filterSeverity} onChange={(e) => setFilter("severity", e.target.value)} className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1.5 text-xs text-[#374151]">
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={filterModule} onChange={(e) => setFilter("module", e.target.value)} className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1.5 text-xs text-[#374151]">
          <option value="">All Modules</option>
          {allModules.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        {(filterSeverity || filterModule) && (
          <button onClick={() => setSearchParams({}, { replace: true })} className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1.5 text-xs text-[#6B7280] hover:bg-[#F9FAFB]">
            Clear Filters
          </button>
        )}
      </div>

      {/* Findings */}
      {filteredFindings.length === 0 ? (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-8 text-center">
          <CheckCircle className="mx-auto mb-2 h-8 w-8 text-[#059669]" />
          <p className="text-sm font-medium text-[#111827]">No findings match the current filters</p>
          <p className="mt-1 text-xs text-[#6B7280]">{findings.length === 0 ? "All readiness checks passed." : "Try adjusting your filter criteria."}</p>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Findings ({filteredFindings.length})</p>
          {filteredFindings.map((f, i) => {
            const isExpanded = expandedFinding === `${f.category}-${i}`;
            return (
              <div key={`${f.category}-${i}`} className="rounded-xl border border-[#E5E7EB] bg-white transition-all hover:shadow-sm">
                <button onClick={() => setExpandedFinding(isExpanded ? null : `${f.category}-${i}`)} className="flex w-full items-center justify-between px-5 py-3 text-left">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`h-2 w-2 shrink-0 rounded-full ${f.severity === "critical" ? "bg-[#DC2626]" : f.severity === "high" ? "bg-[#EA580C]" : f.severity === "medium" ? "bg-[#D97706]" : "bg-[#6B7280]"}`} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-[#111827] truncate">{f.name}</p>
                      <p className="text-[10px] text-[#6B7280] capitalize">{f.category}{f.affected_modules.length > 0 && ` · ${f.affected_modules.length} module(s)`}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`rounded border px-2 py-0.5 text-[10px] font-medium ${severityColors[f.severity] || severityColors.low}`}>{f.severity.toUpperCase()}</span>
                    {isExpanded ? <ChevronUp className="h-3.5 w-3.5 text-[#9CA3AF]" /> : <ChevronDown className="h-3.5 w-3.5 text-[#9CA3AF]" />}
                  </div>
                </button>
                {isExpanded && (
                  <div className="border-t border-[#E5E7EB] px-5 py-4 space-y-3">
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Description</p>
                      <p className="mt-1 text-sm text-[#374151]">{f.detail}</p>
                    </div>
                    {f.affected_modules.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Modules</p>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {f.affected_modules.map((m, mi) => (
                            <span key={mi} className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-mono text-[#374151]">{m}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="rounded-lg bg-[#F9FAFB] px-3 py-2">
                      <p className="text-[10px] font-semibold text-[#6B7280]">Impact</p>
                      <p className="mt-0.5 text-xs text-[#374151]">{f.impact}</p>
                    </div>
                    <div className="rounded-lg bg-[#EFF6FF] px-3 py-2">
                      <div className="flex items-center gap-1.5">
                        <Shield className="h-3 w-3 text-[#2563EB]" />
                        <p className="text-[10px] font-semibold text-[#2563EB]">AI Recommendation</p>
                      </div>
                      <p className="mt-0.5 text-xs text-[#374151]">{f.recommendation}</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Prioritized Recommendations */}
      {summary.prioritized_recommendations.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Prioritized Recommendations</p>
          <div className="mt-3 space-y-2">
            {summary.prioritized_recommendations.map((rec, i) => {
              const sevMatch = rec.match(/^\[(CRITICAL|HIGH|MEDIUM|LOW)\]/);
              const sev = sevMatch?.[1]?.toLowerCase() ?? "info";
              return (
                <div key={i} className="flex items-start gap-2 rounded-lg bg-[#F9FAFB] px-3 py-2">
                  <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${sev === "critical" ? "bg-[#DC2626]" : sev === "high" ? "bg-[#EA580C]" : sev === "medium" ? "bg-[#D97706]" : "bg-[#6B7280]"}`} />
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
