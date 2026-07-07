import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Award,
  BarChart3,
  BookOpen,
  Bug,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Code,
  Download,
  FileCode,
  FileText,
  Filter,
  Flag,
  GitBranch,
  RefreshCw,
  Scale,
  Search,
  Shield,
  ShieldAlert,
  Trophy,
  X,
} from "lucide-react";
import { getCodeQuality } from "@/lib/project-analyzer";
import type {
  CodeQualityResponse,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

type SeverityFilter = string | "all";
type SentimentFilter = string | "all";
type CheckFilter = string | "all";
type PriorityFilter = string | "all";
type RecCategoryFilter = string | "all";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.03 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityColor: Record<string, string> = {
  critical: "#DC2626",
  high: "#EA580C",
  medium: "#D97706",
  low: "#6B7280",
};

const severityBg: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B]",
  high: "bg-[#FFF7ED] text-[#9A3412]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
};

function ScoreGauge({ score, label, size = "md" }: { score: number; label: string; size?: "sm" | "md" | "lg" }) {
  const circumference = size === "lg" ? 2 * Math.PI * 60 : size === "sm" ? 2 * Math.PI * 28 : 2 * Math.PI * 42;
  const offset = circumference - (score / 100) * circumference;
  const strokeColor = score >= 80 ? "#059669" : score >= 60 ? "#D97706" : score >= 40 ? "#EA580C" : "#DC2626";
  const dim = size === "lg" ? 140 : size === "sm" ? 72 : 100;
  const strokeW = size === "lg" ? 8 : size === "sm" ? 5 : 6;
  const fontSize = size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-lg";
  return (
    <div className="flex flex-col items-center">
      <svg width={dim} height={dim} className="-rotate-90">
        <circle cx={dim / 2} cy={dim / 2} r={dim / 2 - strokeW} fill="none" stroke="#F3F4F6" strokeWidth={strokeW} />
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={dim / 2 - strokeW}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeW}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <span className={`${fontSize} font-bold text-[#111827] mt-1`}>{Math.round(score)}</span>
      <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] text-center leading-tight">{label}</span>
    </div>
  );
}

function StatCard({ label, value, sub, icon: Icon, color }: { label: string; value: string | number; sub?: string; icon?: React.ElementType; color?: string }) {
  return (
    <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">{label}</p>
        {Icon && <Icon className="h-4 w-4" style={{ color: color || "#9CA3AF" }} />}
      </div>
      <p className="mt-1 text-lg font-bold text-[#111827]">{value}</p>
      {sub && <p className="text-xs text-[#6B7280]">{sub}</p>}
    </div>
  );
}

function IssueBadge({ severity }: { severity: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${severityBg[severity] || "bg-[#F3F4F6] text-[#374151]"}`}>
      {severity}
    </span>
  );
}

export function CodeQualityPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<CodeQualityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const [sentimentFilter, setSentimentFilter] = useState<SentimentFilter>("all");
  const [checkFilter, setCheckFilter] = useState<CheckFilter>("all");
  const [expandedChecks, setExpandedChecks] = useState<Set<string>>(new Set());
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set());
  const [recPriorityFilter, setRecPriorityFilter] = useState<PriorityFilter>("all");
  const [recCategoryFilter, setRecCategoryFilter] = useState<RecCategoryFilter>("all");
  const [recSearchQuery, setRecSearchQuery] = useState("");
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getCodeQuality(Number(projectId));
      setData(result);
      fetchedRef.current = true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load code quality data");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const scores = useMemo(() => data ? [
    { key: "overall_score" as const, label: "Overall", icon: Award, color: "#2563EB" },
    { key: "maintainability_score" as const, label: "Maintainability", icon: Scale, color: "#059669" },
    { key: "readability_score" as const, label: "Readability", icon: BookOpen, color: "#7C3AED" },
    { key: "complexity_score" as const, label: "Complexity", icon: GitBranch, color: "#D97706" },
    { key: "documentation_score" as const, label: "Documentation", icon: FileText, color: "#0891B2" },
    { key: "security_score" as const, label: "Security", icon: Shield, color: "#DC2626" },
    { key: "technical_debt_score" as const, label: "Technical Debt", icon: Bug, color: "#EA580C" },
  ] : [], [data]);

  const filteredInsights = useMemo(() => {
    if (!data) return [];
    let result = [...data.insights];
    if (sentimentFilter !== "all") {
      result = result.filter((i) => i.sentiment === sentimentFilter);
    }
    return result;
  }, [data, sentimentFilter]);

  const filteredRecommendations = useMemo(() => {
    if (!data) return [];
    let result = [...data.recommendations];
    if (recPriorityFilter !== "all") {
      result = result.filter((r) => r.priority === recPriorityFilter);
    }
    if (recCategoryFilter !== "all") {
      result = result.filter((r) => r.category === recCategoryFilter);
    }
    if (recSearchQuery) {
      const q = recSearchQuery.toLowerCase();
      result = result.filter(
        (r) =>
          r.action.toLowerCase().includes(q) ||
          r.detail.toLowerCase().includes(q) ||
          r.affected_files.some((f) => f.toLowerCase().includes(q)),
      );
    }
    return result;
  }, [data, recPriorityFilter, recCategoryFilter, recSearchQuery]);

  const recommendationCategories = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.recommendations.map((r) => r.category).filter(Boolean))];
  }, [data]);

  const groupedRecommendations = useMemo(() => {
    const groups: Record<string, typeof filteredRecommendations> = {};
    for (const r of filteredRecommendations) {
      const p = r.priority || "medium";
      if (!groups[p]) groups[p] = [];
      groups[p].push(r);
    }
    return groups;
  }, [filteredRecommendations]);

  const filteredChecks = useMemo(() => {
    if (!data) return [];
    let result = [...data.checks];
    if (checkFilter !== "all") {
      result = result.filter((c) => c.severity === checkFilter);
    }
    return result;
  }, [data, checkFilter]);

  const toggleCheck = (name: string) => {
    setExpandedChecks((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const toggleIssue = (idx: number) => {
    setExpandedIssues((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const exportCSV = useCallback(() => {
    if (!data) return;
    const headers = ["Type", "Severity", "Description", "Reason", "Suggested Fix", "Priority", "Affected File", "Affected Function", "Line"];
    const rows = data.checks.flatMap((c) => c.issues).map((i) =>
      [i.type, i.severity, `"${i.description.replace(/"/g, '""')}"`, `"${i.reason.replace(/"/g, '""')}"`, `"${i.suggested_fix.replace(/"/g, '""')}"`, i.priority, i.affected_file, i.affected_function || "", i.line ?? ""].join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `code-quality-${projectId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data, projectId]);

  const exportJSON = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `code-quality-${projectId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data, projectId]);

  const exportPDF = useCallback(() => {
    exportCSV();
  }, [exportCSV]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#111827]">Analyzing code quality...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Evaluating complexity, readability, and maintainability.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Analysis failed</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button onClick={fetchData} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <FileCode className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No code quality data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Upload and extract a project to begin analysis.</p>
      </div>
    );
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">

      {projectId && (
        <div className="flex items-center gap-2">
          <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
            ← Back to Overview
          </button>
          <span className="text-[#D1D5DB]">|</span>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]">
            Back to Unified Dashboard
          </button>
        </div>
      )}
      {/* Hero */}
      <motion.div variants={itemVariants} className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#7C3AED] to-[#4F46E5] p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-[#C4B5FD]">Code Quality & AI Insights</p>
            <h1 className="mt-1 text-2xl font-bold">Quality Assessment</h1>
            <p className="mt-1 text-sm text-[#C4B5FD]">{data.total_issues} issues · Score {Math.round(data.overall_score.score)}/100</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={exportPDF} className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm hover:bg-white/30">
              <Download className="h-3.5 w-3.5" /> Export
            </button>
            <button onClick={fetchData} className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm hover:bg-white/30">
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
          </div>
        </div>
      </motion.div>

      {/* AI Summary */}
      {data.ai_summary && (
        <motion.div variants={itemVariants} className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-sm font-semibold text-[#111827]">AI Summary</p>
          <p className="mt-2 text-sm text-[#374151] leading-relaxed">{data.ai_summary.summary}</p>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#059669]">Strengths</p>
              <ul className="mt-1.5 space-y-1">
                {data.ai_summary.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-[#374151]">
                    <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#059669]" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#DC2626]">Weaknesses</p>
              <ul className="mt-1.5 space-y-1">
                {data.ai_summary.weaknesses.map((w, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-[#374151]">
                    <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#DC2626]" />
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            <span className="rounded-full bg-[#F3F4F6] px-2.5 py-1 text-[10px] font-medium text-[#374151]">
              Architecture: {data.ai_summary.architecture}
            </span>
            <span className="rounded-full bg-[#F3F4F6] px-2.5 py-1 text-[10px] font-medium text-[#374151]">
              Focus: {data.ai_summary.recommended_focus}
            </span>
          </div>
        </motion.div>
      )}

      {/* Score Gauges */}
      <motion.div variants={itemVariants}>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Quality Scores</p>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7">
          {scores.map((s) => (
            <div key={s.key} className="rounded-xl border border-[#E5E7EB] bg-white p-4 flex items-center justify-center">
              <ScoreGauge score={data[s.key].score} label={s.label} size="sm" />
            </div>
          ))}
        </div>
      </motion.div>

      {/* Summary Stat Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-7 2xl:grid-cols-9">
        <StatCard label="Total Issues" value={data.total_issues} icon={Bug} color="#DC2626" />
        <StatCard label="Critical" value={data.severity_counts.critical} icon={ShieldAlert} color="#DC2626" />
        <StatCard label="High" value={data.severity_counts.high} icon={AlertTriangle} color="#EA580C" />
        <StatCard label="Medium" value={data.severity_counts.medium} icon={Flag} color="#D97706" />
        <StatCard label="Low" value={data.severity_counts.low} icon={CheckCircle} color="#6B7280" />
        <StatCard label="Insights" value={data.insights.length} icon={BarChart3} color="#7C3AED" />
        <StatCard label="Recommendations" value={data.recommendations.length} icon={Trophy} color="#059669" />
        <StatCard label="Checks Passed" value={data.checks.filter((c) => c.status === "pass").length} sub={`of ${data.checks.length}`} icon={CheckCircle} color="#059669" />
        <StatCard label="Checks Failed" value={data.checks.filter((c) => c.status === "fail").length} sub={`of ${data.checks.length}`} icon={AlertTriangle} color="#DC2626" />
      </motion.div>

      {/* Severity Distribution Bar Chart */}
      {(() => {
        const severityKeys = ["critical", "high", "medium", "low"] as const;
        const counts = severityKeys.map((k) => data.severity_counts[k]);
        const maxCount = Math.max(...counts, 1);
        const total = counts.reduce((a, b) => a + b, 0);

        if (total === 0) {
          return (
            <motion.div variants={itemVariants} className={sectionClass + " p-5"}>
              <p className="mb-3 text-sm font-semibold text-[#111827]">Severity Distribution</p>
              <div className="flex items-center justify-center h-32 text-sm text-[#6B7280]">No issues detected.</div>
            </motion.div>
          );
        }

        const margin = { top: 20, right: 12, bottom: 28, left: 48 };
        const width = 600;
        const height = 200;
        const innerW = width - margin.left - margin.right;
        const innerH = height - margin.top - margin.bottom;
        const barW = Math.max(innerW / severityKeys.length * 0.55, 32);

        return (
          <motion.div variants={itemVariants} className={sectionClass + " p-4 sm:p-5 overflow-hidden"}>
            <p className="mb-1 text-sm font-semibold text-[#111827]">Severity Distribution</p>
            <div className="w-full overflow-visible">
              <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: height, minHeight: height }} preserveAspectRatio="xMidYMid meet">
                {/* Y-axis grid lines + labels */}
                {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
                  const y = margin.top + innerH * (1 - frac);
                  const val = Math.round(frac * maxCount);
                  return (
                    <g key={frac}>
                      <line x1={margin.left} y1={y} x2={width - margin.right} y2={y} stroke="#F3F4F6" strokeWidth={1} />
                      <text x={margin.left - 8} y={y + 4} textAnchor="end" className="text-[10px]" fill="#9CA3AF" fontSize="10">{val}</text>
                    </g>
                  );
                })}

                {/* Bars */}
                {severityKeys.map((sev, i) => {
                  const count = data.severity_counts[sev];
                  const barH = maxCount > 0 ? (count / maxCount) * innerH : 0;
                  const x = margin.left + (innerW / severityKeys.length) * i + (innerW / severityKeys.length - barW) / 2;
                  const y = margin.top + innerH - barH;
                  const pct = total > 0 ? ((count / total) * 100).toFixed(1) : "0.0";
                  return (
                    <g key={sev}>
                      <rect
                        x={x} y={y} width={barW} height={barH || 2} rx={4} ry={4}
                        fill={severityColor[sev]}
                        className="transition-all duration-500 hover:opacity-80"
                      />
                      {/* Value on top of bar */}
                      <text x={x + barW / 2} y={y - 6} textAnchor="middle" className="text-xs font-medium" fill="#374151" fontSize="11">
                        {count.toLocaleString()}
                      </text>
                      {/* X-axis label */}
                      <text x={x + barW / 2} y={margin.top + innerH + 18} textAnchor="middle" className="text-[10px] font-medium capitalize" fill="#6B7280" fontSize="10">
                        {sev}
                      </text>
                      {/* Tooltip trigger area (invisible wider rect for hover) */}
                      <rect
                        x={x - 4} y={margin.top} width={barW + 8} height={innerH} fill="transparent"
                        className="cursor-pointer"
                      >
                        <title>{`${sev.charAt(0).toUpperCase() + sev.slice(1)}\n${count.toLocaleString()} Issues\n${pct}% of total`}</title>
                      </rect>
                    </g>
                  );
                })}
              </svg>
            </div>
            <div className="mt-1 flex items-center justify-center gap-4 text-[10px] text-[#6B7280]">
              <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: severityColor.critical }} /> Critical</span>
              <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: severityColor.high }} /> High</span>
              <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: severityColor.medium }} /> Medium</span>
              <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: severityColor.low }} /> Low</span>
            </div>
          </motion.div>
        );
      })()}

      {/* Top Problematic & Clean Files */}
      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2">
        {data.top_problematic_files.length > 0 && (
          <div className={sectionClass}>
            <div className="border-b border-[#E5E7EB] px-5 py-3">
              <p className="text-sm font-semibold text-[#111827]">Top Problematic Files</p>
            </div>
            <div className="divide-y divide-[#F3F4F6]">
              {data.top_problematic_files.map((f, i) => (
                <div key={i} className="flex items-center justify-between px-5 py-2.5 hover:bg-[#F9FAFB]">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-[#111827] truncate">{f.path}</p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-[#DC2626]">{f.issue_count} issues</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${f.score >= 80 ? "bg-[#ECFDF5] text-[#065F46]" : f.score >= 60 ? "bg-[#FFFBEB] text-[#92400E]" : "bg-[#FEF2F2] text-[#991B1B]"}`}>
                      {Math.round(f.score)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        {data.top_clean_files.length > 0 && (
          <div className={sectionClass}>
            <div className="border-b border-[#E5E7EB] px-5 py-3">
              <p className="text-sm font-semibold text-[#111827]">Top Clean Files</p>
            </div>
            <div className="divide-y divide-[#F3F4F6]">
              {data.top_clean_files.map((f, i) => (
                <div key={i} className="flex items-center justify-between px-5 py-2.5 hover:bg-[#F9FAFB]">
                  <p className="text-xs font-medium text-[#111827] truncate">{f.path}</p>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-[#059669]">{f.issue_count} issues</span>
                    <span className="rounded-full bg-[#ECFDF5] px-2 py-0.5 text-[10px] font-medium text-[#065F46]">{Math.round(f.score)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      {/* Language Breakdown */}
      {data.language_breakdown.length > 0 && (
        <motion.div variants={itemVariants} className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">Language Breakdown</p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {data.language_breakdown.map((lang) => {
              const maxCount = Math.max(...data.language_breakdown.map((l) => l.file_count), 1);
              const pct = (lang.file_count / maxCount) * 100;
              return (
                <div key={lang.language} className="flex items-center gap-3 rounded-lg border border-[#E5E7EB] bg-white px-4 py-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[#111827]">{lang.language}</p>
                    <div className="mt-1 h-2 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                      <div className="h-full rounded-full bg-gradient-to-r from-[#7C3AED] to-[#4F46E5]" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs font-medium text-[#374151]">{lang.file_count} files</p>
                    <p className="text-[10px] text-[#6B7280]">{lang.issue_count} issues · ∅{lang.avg_complexity}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* AI Insights */}
      {filteredInsights.length > 0 && (
        <motion.div variants={itemVariants} className={sectionClass}>
          <div className="border-b border-[#E5E7EB] px-5 py-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-[#111827]">AI Insights ({data.insights.length})</p>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#9CA3AF]" />
              <select
                value={sentimentFilter}
                onChange={(e) => setSentimentFilter(e.target.value)}
                className="appearance-none rounded-lg border border-[#E5E7EB] bg-white py-1.5 pl-9 pr-7 text-xs text-[#374151] focus:border-[#7C3AED] focus:outline-none"
              >
                <option value="all">All Sentiments</option>
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="negative">Negative</option>
              </select>
            </div>
          </div>
          <div className="divide-y divide-[#F3F4F6] max-h-[500px] overflow-y-auto">
            {filteredInsights.map((insight, i) => (
              <div key={i} className="px-5 py-3 flex items-start gap-3 hover:bg-[#F9FAFB]">
                <div className={`mt-0.5 rounded-full p-1 shrink-0 ${
                  insight.sentiment === "positive" ? "bg-[#ECFDF5]" :
                  insight.sentiment === "negative" ? "bg-[#FEF2F2]" :
                  "bg-[#F3F4F6]"
                }`}>
                  {insight.sentiment === "positive" ? (
                    <Trophy className="h-3.5 w-3.5 text-[#059669]" />
                  ) : insight.sentiment === "negative" ? (
                    <AlertTriangle className="h-3.5 w-3.5 text-[#DC2626]" />
                  ) : (
                    <BarChart3 className="h-3.5 w-3.5 text-[#6B7280]" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-[#374151]">{insight.message}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium capitalize ${
                      insight.sentiment === "positive" ? "bg-[#ECFDF5] text-[#065F46]" :
                      insight.sentiment === "negative" ? "bg-[#FEF2F2] text-[#991B1B]" :
                      "bg-[#F3F4F6] text-[#374151]"
                    }`}>{insight.sentiment}</span>
                    <span className="text-[10px] text-[#7C3AED]">{insight.category}</span>
                    {insight.module && (
                      <span className="text-[10px] text-[#6B7280]">Module: {insight.module}</span>
                    )}
                    {insight.files.length > 0 && (
                      <span className="text-[10px] text-[#6B7280]">
                        Files: {insight.files.slice(0, 3).join(", ")}{insight.files.length > 3 ? ` +${insight.files.length - 3} more` : ""}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Smart Recommendations */}
      {data.recommendations.length > 0 && (
        <motion.div variants={itemVariants} className={sectionClass}>
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Smart Recommendations ({data.recommendations.length})</p>
          </div>
          {/* Recommendation filters */}
          <div className="border-b border-[#E5E7EB] bg-[#FAFAFA] px-5 py-2.5 flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-[#9CA3AF]" />
              <input
                type="text"
                placeholder="Search recommendations..."
                value={recSearchQuery}
                onChange={(e) => setRecSearchQuery(e.target.value)}
                className="w-44 rounded-lg border border-[#E5E7EB] bg-white py-1.5 pl-8 pr-2 text-[10px] text-[#111827] placeholder:text-[#9CA3AF] focus:border-[#7C3AED] focus:outline-none"
              />
            </div>
            <select
              value={recPriorityFilter}
              onChange={(e) => setRecPriorityFilter(e.target.value)}
              className="rounded-lg border border-[#E5E7EB] bg-white py-1.5 px-2.5 text-[10px] text-[#374151] focus:border-[#7C3AED] focus:outline-none"
            >
              <option value="all">All Priorities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={recCategoryFilter}
              onChange={(e) => setRecCategoryFilter(e.target.value)}
              className="rounded-lg border border-[#E5E7EB] bg-white py-1.5 px-2.5 text-[10px] text-[#374151] focus:border-[#7C3AED] focus:outline-none"
            >
              <option value="all">All Categories</option>
              {recommendationCategories.map((cat) => (
                <option key={cat} value={cat}>{cat.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div className="divide-y divide-[#F3F4F6]">
            {(["high", "medium", "low"] as const).map((priority) => {
              const items = groupedRecommendations[priority];
              if (!items || items.length === 0) return null;
              const priorityLabel = priority === "high" ? "High Priority" : priority === "medium" ? "Medium Priority" : "Low Priority";
              const priorityColor = priority === "high" ? "bg-[#FEF2F2] text-[#991B1B]" : priority === "medium" ? "bg-[#FFFBEB] text-[#92400E]" : "bg-[#F3F4F6] text-[#374151]";
              return (
                <div key={priority}>
                  <div className={`px-5 py-2 flex items-center gap-2 ${priority === "high" ? "bg-[#FEF2F2]" : priority === "medium" ? "bg-[#FFFBEB]" : "bg-[#F9FAFB]"}`}>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${priorityColor}`}>{priorityLabel}</span>
                    <span className="text-[10px] text-[#6B7280]">{items.length} recommendation{items.length !== 1 ? "s" : ""}</span>
                  </div>
                  {items.map((rec, i) => (
                    <div key={i} className="px-5 py-3 hover:bg-[#F9FAFB]">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-medium text-[#111827]">{rec.action}</p>
                            {rec.estimated_improvement && (
                              <span className="rounded-full bg-[#ECFDF5] px-1.5 py-0.5 text-[10px] font-medium text-[#065F46] shrink-0">
                                +{rec.estimated_improvement.replace(/^\+/, '')}
                              </span>
                            )}
                          </div>
                          <p className="mt-0.5 text-xs text-[#6B7280]">{rec.detail}</p>
                          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
                            <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium capitalize ${
                              rec.impact === "high" ? "bg-[#FEF2F2] text-[#991B1B]" :
                              rec.impact === "medium" ? "bg-[#FFFBEB] text-[#92400E]" :
                              "bg-[#F3F4F6] text-[#374151]"
                            }`}>Impact: {rec.impact}</span>
                            <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium capitalize ${
                              rec.effort === "high" ? "bg-[#FEF2F2] text-[#991B1B]" :
                              rec.effort === "medium" ? "bg-[#FFFBEB] text-[#92400E]" :
                              "bg-[#ECFDF5] text-[#065F46]"
                            }`}>Effort: {rec.effort}</span>
                            {rec.affected_file_count > 0 && (
                              <span className="text-[10px] text-[#6B7280]">{rec.affected_file_count} file{rec.affected_file_count !== 1 ? "s" : ""} affected</span>
                            )}
                            {rec.category && (
                              <span className="text-[10px] text-[#7C3AED]">{rec.category}</span>
                            )}
                          </div>
                          {rec.affected_files.length > 0 && (
                            <div className="mt-1.5 flex flex-wrap gap-1">
                              {rec.affected_files.slice(0, 5).map((af, j) => (
                                <span key={j} className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#6B7280]">
                                  {af}
                                </span>
                              ))}
                              {rec.affected_files.length > 5 && (
                                <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#6B7280]">
                                  +{rec.affected_files.length - 5} more
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
            {filteredRecommendations.length === 0 && (
              <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No recommendations match your filter criteria.</div>
            )}
          </div>
        </motion.div>
      )}

      {/* Filter bar for Checks & Issues */}
      <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9CA3AF]" />
            <input
              type="text"
              placeholder="Search issues by file, function, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-3 text-xs text-[#111827] placeholder:text-[#9CA3AF] focus:border-[#7C3AED] focus:outline-none"
            />
            {searchQuery && <X className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9CA3AF] cursor-pointer hover:text-[#6B7280]" onClick={() => setSearchQuery("")} />}
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9CA3AF]" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="appearance-none rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-7 text-xs text-[#374151] focus:border-[#7C3AED] focus:outline-none"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9CA3AF]" />
            <select
              value={checkFilter}
              onChange={(e) => setCheckFilter(e.target.value)}
              className="appearance-none rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-7 text-xs text-[#374151] focus:border-[#7C3AED] focus:outline-none"
            >
              <option value="all">All Checks</option>
              {data.checks.map((c) => <option key={c.check_name} value={c.severity}>{c.check_name}</option>)}
            </select>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={exportCSV} className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 py-1.5 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
            <Download className="h-3.5 w-3.5" /> CSV
          </button>
          <button onClick={exportJSON} className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 py-1.5 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
            <Code className="h-3.5 w-3.5" /> JSON
          </button>
        </div>
      </motion.div>

      {/* Quality Checks */}
      <motion.div variants={itemVariants} className={sectionClass + " overflow-hidden"}>
        <div className="border-b border-[#E5E7EB] px-5 py-3">
          <p className="text-sm font-semibold text-[#111827]">Quality Checks ({filteredChecks.length})</p>
        </div>
        <div className="divide-y divide-[#F3F4F6]">
          {filteredChecks.map((check) => {
            const isExpanded = expandedChecks.has(check.check_name);
            return (
              <div key={check.check_name}>
                <button
                  onClick={() => toggleCheck(check.check_name)}
                  className="w-full flex items-center justify-between px-5 py-3 hover:bg-[#F9FAFB] text-left"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    {check.status === "pass" ? (
                      <CheckCircle className="h-4 w-4 text-[#059669] shrink-0" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-[#DC2626] shrink-0" />
                    )}
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-[#111827]">{check.check_name}</p>
                      <p className="text-xs text-[#6B7280]">
                        {check.count} issue{check.count !== 1 ? "s" : ""} · {check.issues.length} affected location{check.issues.length !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      check.status === "pass" ? "bg-[#ECFDF5] text-[#065F46]" : "bg-[#FEF2F2] text-[#991B1B]"
                    }`}>
                      {check.status === "pass" ? "Pass" : "Fail"}
                    </span>
                    <IssueBadge severity={check.severity} />
                    {isExpanded ? <ChevronDown className="h-4 w-4 text-[#9CA3AF]" /> : <ChevronRight className="h-4 w-4 text-[#9CA3AF]" />}
                  </div>
                </button>
                {isExpanded && check.issues.length > 0 && (
                  <div className="border-t border-[#F3F4F6] bg-[#FAFAFA]">
                    <div className="divide-y divide-[#F3F4F6] max-h-[600px] overflow-y-auto">
                      {check.issues.map((issue, idx) => {
                        const isIssueExpanded = expandedIssues.has(idx);
                        return (
                          <div key={idx}>
                            <button
                              onClick={() => toggleIssue(idx)}
                              className="w-full flex items-center justify-between px-5 py-2.5 pl-12 text-left hover:bg-white"
                            >
                              <div className="flex items-center gap-2 min-w-0 flex-1">
                                <IssueBadge severity={issue.severity} />
                                <p className="text-xs text-[#374151] truncate">{issue.description}</p>
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                <span className="text-[10px] text-[#6B7280]">{issue.affected_file.split("/").pop()}</span>
                                {issue.affected_function && <span className="text-[10px] text-[#7C3AED]">{issue.affected_function}</span>}
                                {isIssueExpanded ? <ChevronDown className="h-3 w-3 text-[#9CA3AF]" /> : <ChevronRight className="h-3 w-3 text-[#9CA3AF]" />}
                              </div>
                            </button>
                            {isIssueExpanded && (
                              <div className="px-5 py-3 pl-12 border-t border-[#F3F4F6] bg-white">
                                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                  <div>
                                    <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Reason</p>
                                    <p className="mt-1 text-xs text-[#374151]">{issue.reason}</p>
                                  </div>
                                  <div>
                                    <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Suggested Fix</p>
                                    <p className="mt-1 text-xs text-[#059669]">{issue.suggested_fix}</p>
                                  </div>
                                </div>
                                <div className="mt-2 flex flex-wrap gap-2">
                                  <span className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#374151]">
                                    File: {issue.affected_file}
                                  </span>
                                  {issue.affected_function && (
                                    <span className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#7C3AED]">
                                      Function: {issue.affected_function}
                                    </span>
                                  )}
                                  {issue.line && (
                                    <span className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#6B7280]">
                                      Line: {issue.line}
                                    </span>
                                  )}
                                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                                    issue.priority === "high" ? "bg-[#FEF2F2] text-[#991B1B]" :
                                    issue.priority === "medium" ? "bg-[#FFFBEB] text-[#92400E]" :
                                    "bg-[#F3F4F6] text-[#374151]"
                                  }`}>
                                    Priority: {issue.priority}
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
          {filteredChecks.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No checks match your filter criteria.</div>
          )}
        </div>
      </motion.div>

      {projectId && <RelatedAnalysisNav projectId={projectId} currentPage="code-quality" />}

    </motion.div>
  );
}
