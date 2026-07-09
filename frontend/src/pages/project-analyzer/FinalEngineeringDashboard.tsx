import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Award,
  BarChart3,
  BrainCircuit,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Cpu,
  Download,
  FileCode,
  FileSearch,
  FlaskConical,
  RefreshCw,
  Rocket,
  Search,
  Shield,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  getAiEngineeringReadiness,
  getCodeQuality,
  getProductionReadiness,
  getProjectAnalyzer,
  getProjectInsights,
  getUnifiedIntelligence,
} from "@/lib/project-analyzer";
import type {
  AiEngineeringReadinessResponse,
  AnalyzerResponse,
  CodeQualityResponse,
  ProductionReadinessResponse,
  ProjectInsightsResponse,
  UnifiedIntelligenceResponse,
} from "@/types/project-analyzer";

interface DashboardState {
  analyzer: AnalyzerResponse | null;
  unified: UnifiedIntelligenceResponse | null;
  aiEng: AiEngineeringReadinessResponse | null;
  insights: ProjectInsightsResponse | null;
  codeQuality: CodeQualityResponse | null;
  production: ProductionReadinessResponse | null;
}

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

const healthMatrixKeys: { key: string; label: string; icon: typeof BarChart3; source: "unified" | "aiEng" | "both"; unifiedKey: string; aiEngKey: string }[] = [
  { key: "architecture_health", label: "Architecture", icon: Cpu, source: "aiEng", unifiedKey: "architecture_health", aiEngKey: "architecture_health" },
  { key: "code_health", label: "Code", icon: FileCode, source: "aiEng", unifiedKey: "overall_quality", aiEngKey: "code_health" },
  { key: "dependency_health", label: "Dependencies", icon: BarChart3, source: "both", unifiedKey: "dependency_health", aiEngKey: "dependency_health" },
  { key: "security_health", label: "Security", icon: Shield, source: "both", unifiedKey: "security_health", aiEngKey: "security_health" },
  { key: "performance_health", label: "Performance", icon: Zap, source: "both", unifiedKey: "performance_health", aiEngKey: "performance_health" },
  { key: "maintainability_health", label: "Maintainability", icon: TrendingUp, source: "both", unifiedKey: "maintainability", aiEngKey: "maintainability_health" },
  { key: "readiness", label: "Readiness", icon: Rocket, source: "unified", unifiedKey: "readiness", aiEngKey: "" },
  { key: "documentation_health", label: "Documentation", icon: FileSearch, source: "aiEng", unifiedKey: "", aiEngKey: "documentation_health" },
  { key: "testing_health", label: "Testing", icon: FlaskConical, source: "aiEng", unifiedKey: "", aiEngKey: "testing_health" },
  { key: "production_health", label: "Production", icon: Rocket, source: "aiEng", unifiedKey: "", aiEngKey: "production_health" },
];

export function FinalEngineeringDashboard() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const [dashboard, setDashboard] = useState<DashboardState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef(false);

  const searchQuery = searchParams.get("q") || "";
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const fetchAll = () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    Promise.allSettled([
      getProjectAnalyzer(Number(projectId)),
      getUnifiedIntelligence(Number(projectId)),
      getAiEngineeringReadiness(Number(projectId)),
      getProjectInsights(Number(projectId)),
      getCodeQuality(Number(projectId)),
      getProductionReadiness(Number(projectId)),
    ]).then(([analyzer, unified, aiEng, insights, codeQuality, production]) => {
      setDashboard({
        analyzer: analyzer.status === "fulfilled" ? analyzer.value : null,
        unified: unified.status === "fulfilled" ? unified.value : null,
        aiEng: aiEng.status === "fulfilled" ? aiEng.value : null,
        insights: insights.status === "fulfilled" ? insights.value : null,
        codeQuality: codeQuality.status === "fulfilled" ? codeQuality.value : null,
        production: production.status === "fulfilled" ? production.value : null,
      });
      fetchedRef.current = true;
    }).catch((err: unknown) => {
      const msg = err instanceof Error ? err.message : "Failed to load dashboard data";
      setError(msg);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchAll();
  }, [projectId]);

  const overallScore = (() => {
    if (!dashboard) return 0;
    const scores: number[] = [];
    if (dashboard.aiEng) scores.push(dashboard.aiEng.engineering_score.overall_engineering_score);
    if (dashboard.unified) scores.push(dashboard.unified.health.overall_health);
    if (dashboard.codeQuality) scores.push(dashboard.codeQuality.overall_score.score);
    if (dashboard.production) scores.push(dashboard.production.production_score.overall_production_score);
    return scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
  })();

  const allRecommendations = (() => {
    if (!dashboard) return [] as { text: string; severity: string }[];
    const recs: { text: string; severity: string }[] = [];
    if (dashboard.insights) {
      dashboard.insights.recommended_actions.forEach((a) => recs.push({ text: a.action, severity: a.priority }));
    }
    if (dashboard.aiEng) {
      dashboard.aiEng.summary.prioritized_recommendations.forEach((r) => {
        const sevMatch = r.match(/^\[(CRITICAL|HIGH|MEDIUM|LOW)\]/);
        const sev = sevMatch?.[1]?.toLowerCase() ?? "info";
        recs.push({ text: r, severity: sev });
      });
    }
    if (dashboard.production) {
      dashboard.production.summary.prioritized_recommendations.forEach((r) => {
        const sevMatch = r.match(/^\[(CRITICAL|HIGH|MEDIUM|LOW)\]/);
        const sev = sevMatch?.[1]?.toLowerCase() ?? "info";
        recs.push({ text: r, severity: sev });
      });
    }
    if (dashboard.unified) {
      dashboard.unified.insights.forEach((i) => {
        recs.push({ text: `${i.label}: ${i.detail}`, severity: i.severity });
      });
    }
    return recs;
  })();

  const filteredRecs = allRecommendations.filter((r) => {
    if (searchQuery && !r.text.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const strengths = dashboard?.insights?.strengths ?? [];
  const weaknesses = dashboard?.insights?.weaknesses ?? [];

  const filteredStrengths = strengths.filter((s) => {
    if (searchQuery && !s.detail.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const filteredWeaknesses = weaknesses.filter((w) => {
    if (searchQuery && !w.detail.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const downloadJSON = () => {
    if (!dashboard) return;
    const blob = new Blob([JSON.stringify(dashboard, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "engineering-dashboard-report.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadCSV = () => {
    if (!dashboard) return;
    const rows: string[][] = [["Metric", "Score"]];
    if (dashboard.unified) {
      const h = dashboard.unified.health;
      Object.entries(h).forEach(([k, v]) => rows.push([`Health.${k}`, String(v)]));
    }
    if (dashboard.aiEng) {
      const s = dashboard.aiEng.engineering_score;
      Object.entries(s).forEach(([k, v]) => rows.push([`Engineering.${k}`, String(v)]));
    }
    if (dashboard.codeQuality) {
      rows.push(["CodeQuality.overall_score", String(dashboard.codeQuality.overall_score.score)]);
    }
    if (dashboard.production) {
      rows.push(["Production.overall_score", String(dashboard.production.production_score.overall_production_score)]);
    }
    const csv = rows.map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "engineering-dashboard-report.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadHTML = () => {
    if (!dashboard) return;
    const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const projectName = dashboard.analyzer?.project_name ?? "Unknown";
    const score = overallScore;
    const severityClass = score >= 70 ? "#059669" : score >= 40 ? "#D97706" : "#DC2626";
    const healthRows = healthMatrixKeys.map(({ label, source, unifiedKey, aiEngKey }) => {
      const val = source === "unified" || source === "both"
        ? (dashboard.unified?.health as unknown as Record<string, number>)?.[unifiedKey] ?? null
        : null;
      const val2 = source === "aiEng" || source === "both"
        ? (dashboard.aiEng?.project_health as unknown as Record<string, number>)?.[aiEngKey] ?? null
        : null;
      const finalVal = val ?? val2 ?? 0;
      return `<tr><td>${esc(label)}</td><td>${Math.round(finalVal)}</td></tr>`;
    }).join("");

    const html = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Final Report - ${esc(projectName)}</title>
<style>
body{font-family:-apple-system,sans-serif;margin:40px;color:#111;background:#f8fafc}
h1{color:#2563eb;margin-bottom:4px}
.sub{color:#6b7280;font-size:14px;margin-bottom:24px}
.card{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:16px}
.score{font-size:48px;font-weight:bold;color:${severityClass}}
table{width:100%;border-collapse:collapse}
td,th{text-align:left;padding:8px 12px;border-bottom:1px solid #e5e7eb}
th{font-size:12px;text-transform:uppercase;color:#9ca3af}
.section-title{font-size:14px;font-weight:600;color:#374151;margin-bottom:12px}
</style>
</head>
<body>
<h1>${esc(projectName)}</h1>
<p class="sub">Final Report</p>
<div class="card"><div class="section-title">Overall Engineering Score</div><div class="score">${score}<span style="font-size:18px;color:#6b7280">/100</span></div></div>
<div class="card"><div class="section-title">Health Matrix</div>
<table><thead><tr><th>Dimension</th><th>Score</th></tr></thead><tbody>${healthRows}</tbody></table></div>
<div class="card"><div class="section-title">Summary</div><p>${esc(dashboard.aiEng?.summary.summary_text ?? dashboard.unified?.executive_summary.project_summary ?? "")}</p></div>
</body></html>`;
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `engineering-dashboard-report.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative mb-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        </div>
        <p className="text-sm font-medium text-[#111827]">Building Executive Dashboard...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Aggregating all intelligence engines into a unified report.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Dashboard failed</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button onClick={fetchAll} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <BrainCircuit className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No dashboard data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run project analysis to generate the executive dashboard.</p>
      </div>
    );
  }

  const { analyzer, unified, aiEng, insights, codeQuality, production } = dashboard;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#7C3AED] to-[#2563EB] p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-[#A78BFA]">Phase 3C.10</p>
            <h1 className="mt-1 text-2xl font-bold">Engineering Dashboard</h1>
            <p className="mt-1 text-sm text-[#C4B5FD]">
              Executive summary — aggregate of all {analyzer?.project_name ? `“${analyzer.project_name}”` : ""} intelligence engines
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative group">
              <button
                className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm transition-colors hover:bg-white/30"
              >
                <Download className="h-3.5 w-3.5" /> Download
              </button>
              <div className="absolute right-0 top-full z-50 mt-1 hidden w-36 rounded-lg border border-[#E5E7EB] bg-white shadow-lg group-hover:block">
                <button onClick={downloadJSON} className="block w-full px-4 py-2 text-left text-xs text-[#374151] hover:bg-[#F9FAFB]">JSON</button>
                <button onClick={downloadCSV} className="block w-full px-4 py-2 text-left text-xs text-[#374151] hover:bg-[#F9FAFB]">CSV</button>
                <button onClick={downloadHTML} className="block w-full px-4 py-2 text-left text-xs text-[#374151] hover:bg-[#F9FAFB]">HTML</button>
              </div>
            </div>
            <button onClick={fetchAll} className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm transition-colors hover:bg-white/30">
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Executive Score */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Overall Score</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-5xl font-bold ${scoreColor(overallScore)}`}>{overallScore}</span>
            <span className="text-sm text-[#6B7280]">/ 100</span>
          </div>
        </div>

        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Engineering</p>
          <p className={`mt-2 text-3xl font-bold ${scoreColor(aiEng?.engineering_score.overall_engineering_score ?? 0)}`}>
            {aiEng?.engineering_score.overall_engineering_score ?? "—"}
          </p>
          <p className="mt-1 text-[10px] text-[#6B7280]">AI Readiness</p>
        </div>

        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Code Quality</p>
          <p className={`mt-2 text-3xl font-bold ${scoreColor(codeQuality?.overall_score.score ?? 0)}`}>
            {codeQuality?.overall_score.score ?? "—"}
          </p>
          <p className="mt-1 text-[10px] text-[#6B7280]">{codeQuality?.severity_counts.critical ?? 0} critical issues</p>
        </div>

        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Production</p>
          <p className={`mt-2 text-3xl font-bold ${scoreColor(production?.production_score.overall_production_score ?? 0)}`}>
            {production?.production_score.overall_production_score ?? "—"}
          </p>
          <p className="mt-1 text-[10px] text-[#6B7280]">{production?.summary.classification ?? "—"}</p>
        </div>
      </div>

      {/* AI Summary */}
      {(aiEng?.summary.summary_text || unified?.executive_summary.project_summary) && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <div className="flex items-center gap-2">
            <Award className="h-4 w-4 text-[#7C3AED]" />
            <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Executive Summary</p>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-[#374151]">
            {aiEng?.summary.summary_text || unified?.executive_summary.project_summary}
          </p>
          {unified?.executive_summary.future_improvements && unified.executive_summary.future_improvements.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {unified.executive_summary.future_improvements.map((imp, i) => (
                <span key={i} className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[10px] font-medium text-[#1E40AF]">{imp}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Health Matrix */}
      <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Health Matrix</p>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {healthMatrixKeys.map(({ key: _key, label, icon: Icon, source, unifiedKey, aiEngKey }) => {
            let val: number | null = null;
            if ((source === "unified" || source === "both") && unified) {
              val = (unified.health as unknown as Record<string, number>)[unifiedKey] ?? null;
            }
            if ((source === "aiEng" || source === "both") && aiEng && val === null) {
              val = (aiEng.project_health as unknown as Record<string, number>)[aiEngKey] ?? null;
            }
            val = val ?? 50;
            return (
              <div key={_key} className="rounded-lg border border-[#E5E7EB] p-3">
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

      {/* Strengths & Weaknesses */}
      <div className="grid gap-4 md:grid-cols-2">
        {filteredStrengths.length > 0 && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-[#059669]" />
              <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Strengths</p>
            </div>
            <div className="mt-3 space-y-2">
              {filteredStrengths.map((s, i) => (
                <div key={i} className="flex items-start gap-2 rounded-lg bg-[#ECFDF5] px-3 py-2">
                  <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-[#059669]" />
                  <div className="min-w-0">
                    <p className="text-[10px] font-medium text-[#065F46] uppercase tracking-wider">{s.category}</p>
                    <p className="text-xs text-[#374151]">{s.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {filteredWeaknesses.length > 0 && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-[#DC2626]" />
              <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Weaknesses</p>
            </div>
            <div className="mt-3 space-y-2">
              {filteredWeaknesses.map((w, i) => (
                <div key={i} className="flex items-start gap-2 rounded-lg bg-[#FEF2F2] px-3 py-2">
                  <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-[#DC2626]" />
                  <div className="min-w-0">
                    <p className="text-[10px] font-medium text-[#991B1B] uppercase tracking-wider">{w.category}</p>
                    <p className="text-xs text-[#374151]">{w.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Search & Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#9CA3AF]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams);
              if (e.target.value) next.set("q", e.target.value);
              else next.delete("q");
              setSearchParams(next, { replace: true });
            }}
            placeholder="Search recommendations, strengths, weaknesses..."
            className="w-full rounded-lg border border-[#E5E7EB] bg-white py-1.5 pl-8 pr-3 text-xs text-[#374151] placeholder-[#9CA3AF] focus:border-[#2563EB] focus:outline-none"
          />
        </div>
        {searchQuery && (
          <button onClick={() => setSearchParams({}, { replace: true })} className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1.5 text-xs text-[#6B7280] hover:bg-[#F9FAFB]">
            Clear
          </button>
        )}
      </div>

      {/* Action Plan (Recommendations) */}
      {filteredRecs.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Action Plan ({filteredRecs.length})
          </p>
          <div className="mt-3 space-y-2">
            {filteredRecs.map((rec, i) => {
              const isExpanded = expandedSection === `rec-${i}`;
              return (
                <div key={i}>
                  <button
                    onClick={() => setExpandedSection(isExpanded ? null : `rec-${i}`)}
                    className="flex w-full items-center gap-2 rounded-lg bg-[#F9FAFB] px-3 py-2 text-left hover:bg-[#F3F4F6]"
                  >
                    <span className={`h-2 w-2 shrink-0 rounded-full ${rec.severity === "critical" ? "bg-[#DC2626]" : rec.severity === "high" ? "bg-[#EA580C]" : rec.severity === "medium" ? "bg-[#D97706]" : "bg-[#6B7280]"}`} />
                    <span className="flex-1 text-xs text-[#374151]">{rec.text}</span>
                    {isExpanded ? <ChevronUp className="h-3 w-3 shrink-0 text-[#9CA3AF]" /> : <ChevronDown className="h-3 w-3 shrink-0 text-[#9CA3AF]" />}
                  </button>
                  {isExpanded && (
                    <div className="px-5 py-2">
                      <p className="text-[10px] text-[#6B7280]">
                        Priority: <span className="font-medium text-[#111827]">{rec.severity.toUpperCase()}</span>
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Roadmap + Fix Readiness */}
      {aiEng && (
        <div className="grid gap-4 md:grid-cols-2">
          {/* Engineering Roadmap */}
          {aiEng.roadmap.length > 0 && (
            <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-[#7C3AED]" />
                <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Engineering Roadmap</p>
              </div>
              <div className="mt-3 space-y-2">
                {aiEng.roadmap.map((stage) => (
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
          )}

          {/* Fix Readiness */}
          {aiEng.repair_readiness && (
            <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-[#7C3AED]" />
                <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Automated Fix Readiness</p>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-[#ECFDF5] px-3 py-2">
                  <p className="text-[10px] font-medium text-[#065F46]">Safe to Modify</p>
                  <p className="text-lg font-bold text-[#065F46]">{aiEng.repair_readiness.files_safe_to_modify}</p>
                </div>
                <div className="rounded-lg bg-[#FEF2F2] px-3 py-2">
                  <p className="text-[10px] font-medium text-[#991B1B]">High Risk</p>
                  <p className="text-lg font-bold text-[#991B1B]">{aiEng.repair_readiness.high_risk_files}</p>
                </div>
                <div className="rounded-lg bg-[#F3F4F6] px-3 py-2">
                  <p className="text-[10px] font-medium text-[#374151]">Protected</p>
                  <p className="text-lg font-bold text-[#374151]">{aiEng.repair_readiness.protected_files}</p>
                </div>
                <div className="rounded-lg bg-[#FFFBEB] px-3 py-2">
                  <p className="text-[10px] font-medium text-[#92400E]">Config</p>
                  <p className="text-lg font-bold text-[#92400E]">{aiEng.repair_readiness.configuration_files}</p>
                </div>
                <div className="rounded-lg bg-[#EFF6FF] px-3 py-2">
                  <p className="text-[10px] font-medium text-[#1E40AF]">Core Modules</p>
                  <p className="text-lg font-bold text-[#1E40AF]">{aiEng.repair_readiness.core_modules}</p>
                </div>
                <div className="rounded-lg bg-[#F5F3FF] px-3 py-2">
                  <p className="text-[10px] font-medium text-[#5B21B6]">Utility Modules</p>
                  <p className="text-lg font-bold text-[#5B21B6]">{aiEng.repair_readiness.utility_modules}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Data Sources Summary */}
      <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Data Sources</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {unified && <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[10px] font-medium text-[#1E40AF]">Analysis Overview</span>}
          {aiEng && <span className="rounded bg-[#F5F3FF] px-2 py-0.5 text-[10px] font-medium text-[#5B21B6]">AI Readiness</span>}
          {codeQuality && <span className="rounded bg-[#ECFDF5] px-2 py-0.5 text-[10px] font-medium text-[#065F46]">Code Quality</span>}
          {production && <span className="rounded bg-[#FFF7ED] px-2 py-0.5 text-[10px] font-medium text-[#9A3412]">Production Readiness</span>}
          {insights && <span className="rounded bg-[#FEF2F2] px-2 py-0.5 text-[10px] font-medium text-[#991B1B]">Project Insights</span>}
          {analyzer && <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#374151]">Project Analyzer</span>}
        </div>
      </div>
    </motion.div>
  );
}
