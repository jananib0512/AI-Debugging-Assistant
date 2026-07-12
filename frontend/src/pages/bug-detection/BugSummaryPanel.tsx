import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileCode,
  FileText,
  Search,
  Terminal,
  TrendingUp,
  ArrowRight,
  X,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type {
  PrioritizationResponse,
  SecurityAnalysisResponse,
  PerformanceAnalysisResponse,
  StaticCodeAnalysisResponse,
} from "@/types/project-analyzer";
import {
  computeBugStats,
  computeHealthScores,
  getTopIssues,
  computeCategoryDistribution,
  computeAffectedModulesDistribution,
  computeAffectedFilesDistribution,
  generateExecutiveSummary,
  generateRecommendations,
  generateExportData,
  generateBugReportText,
} from "@/lib/bug-summary";

interface BugSummaryPanelProps {
  prioritizationData: PrioritizationResponse;
  securityData?: SecurityAnalysisResponse | null;
  performanceData?: PerformanceAnalysisResponse | null;
  staticData?: StaticCodeAnalysisResponse | null;
}

export function BugSummaryPanel({
  prioritizationData,
  securityData,
  performanceData,
  staticData,
}: BugSummaryPanelProps) {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const stats = useMemo(
    () => computeBugStats(prioritizationData.prioritized_issues),
    [prioritizationData],
  );

  const health = useMemo(
    () => computeHealthScores(prioritizationData.prioritized_issues, stats, securityData, performanceData, staticData),
    [prioritizationData, stats, securityData, performanceData, staticData],
  );

  const topIssues = useMemo(
    () => getTopIssues(prioritizationData.prioritized_issues, 10),
    [prioritizationData],
  );

  const categoryDist = useMemo(
    () => computeCategoryDistribution(prioritizationData.prioritized_issues),
    [prioritizationData],
  );

  const moduleChart = useMemo(
    () => computeAffectedModulesDistribution(prioritizationData.prioritized_issues),
    [prioritizationData],
  );

  const fileChart = useMemo(
    () => computeAffectedFilesDistribution(prioritizationData.prioritized_issues),
    [prioritizationData],
  );

  const executiveSummary = useMemo(
    () => generateExecutiveSummary(stats, health, prioritizationData),
    [stats, health, prioritizationData],
  );

  const recommendations = useMemo(
    () => generateRecommendations(stats, health, prioritizationData),
    [stats, health, prioritizationData],
  );

  const filteredIssues = useMemo(() => {
    let issues = [...prioritizationData.prioritized_issues];
    if (search) {
      const q = search.toLowerCase();
      issues = issues.filter(
        (i) =>
          i.bug_title.toLowerCase().includes(q) ||
          i.affected_file.toLowerCase().includes(q) ||
          i.severity.toLowerCase().includes(q) ||
          i.description.toLowerCase().includes(q) ||
          i.function_name.toLowerCase().includes(q),
      );
    }
    if (severityFilter !== "all") {
      issues = issues.filter((i) => i.severity === severityFilter);
    }
    if (categoryFilter !== "all") {
      issues = issues.filter((i) => (i.source_engine || "") === categoryFilter);
    }
    return issues;
  }, [prioritizationData, search, severityFilter, categoryFilter]);

  const hasIssues = stats.total_issues > 0;

  const categoryEngineNames: Record<string, string> = {
    syntax: "Syntax",
    static: "Static",
    dependency: "Dependency",
    runtime: "Runtime",
    security: "Security",
    performance: "Performance",
    architecture: "Architecture",
  };

  function handleExportJSON() {
    const data = generateExportData(stats, health, prioritizationData);
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    downloadBlob(blob, "bug-detection-summary.json");
  }

  function handleExportText() {
    const text = generateBugReportText(stats, health, prioritizationData);
    const blob = new Blob([text], { type: "text/plain" });
    downloadBlob(blob, "bug-detection-report.txt");
  }

  function handleExportPDF() {
    const text = generateBugReportText(stats, health, prioritizationData);
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Bug Detection Report</title><style>body{font-family:system-ui,sans-serif;padding:2rem;color:#111827;font-size:12px;line-height:1.5}pre{white-space:pre-wrap;font-family:monospace;background:#f9fafb;padding:1rem;border-radius:8px;border:1px solid #e5e7eb}</style></head><body><pre>${text}</pre></body></html>`;
    const blob = new Blob([html], { type: "text/html" });
    downloadBlob(blob, "bug-detection-report.html");
  }

  function downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  const severityColors: Record<string, string> = {
    Critical: "#DC2626",
    High: "#EA580C",
    Medium: "#F59E0B",
    Low: "#9CA3AF",
  };

  const healthColor = (val: number) => {
    if (val >= 80) return "#059669";
    if (val >= 60) return "#F59E0B";
    return "#DC2626";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      {/* --- Executive Summary --- */}
      <Card hover={false}>
        <CardContent className="p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#EFF6FF]">
              <Terminal className="h-4 w-4 text-[#2563EB]" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
                AI Executive Summary
              </p>
              <p className="mt-1 text-sm leading-relaxed text-[#374151]">
                {executiveSummary.summary}
              </p>
              <p className="mt-1 text-xs leading-relaxed text-[#6B7280]">
                {executiveSummary.detail}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* --- Bug Statistics --- */}
      <section>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
          Bug Statistics
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
          <Card><CardContent className="p-4 text-center">
            <p className="text-lg font-bold text-[#111827]">{stats.total_issues}</p>
            <p className="text-[10px] text-[#6B7280]">Total Bugs</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-lg font-bold text-[#DC2626]">{stats.critical_count}</p>
            <p className="text-[10px] text-[#6B7280]">Critical</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-lg font-bold text-[#EA580C]">{stats.high_count}</p>
            <p className="text-[10px] text-[#6B7280]">High</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-lg font-bold text-[#D97706]">{stats.medium_count}</p>
            <p className="text-[10px] text-[#6B7280]">Medium</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-lg font-bold text-[#6B7280]">{stats.low_count}</p>
            <p className="text-[10px] text-[#6B7280]">Low</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-lg font-bold text-[#111827]">{stats.files_affected}</p>
            <p className="text-[10px] text-[#6B7280]">Files</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-lg font-bold text-[#111827]">{stats.functions_affected}</p>
            <p className="text-[10px] text-[#6B7280]">Functions</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-lg font-bold text-[#111827]">{stats.modules_affected}</p>
            <p className="text-[10px] text-[#6B7280]">Modules</p>
          </CardContent></Card>
        </div>
      </section>

      {/* --- Project Health --- */}
      <section>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
          Project Health
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Card><CardContent className="p-4 text-center">
            <div className="relative mx-auto mb-1 flex h-12 w-12 items-center justify-center">
              <svg className="h-12 w-12 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#F3F4F6" strokeWidth="3" />
                <circle
                  cx="18" cy="18" r="15.5" fill="none"
                  stroke={healthColor(health.overall_bug_score)}
                  strokeWidth="3"
                  strokeDasharray={`${(health.overall_bug_score / 100) * 97.4} 97.4`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute text-xs font-bold text-[#111827]">
                {health.overall_bug_score}
              </span>
            </div>
            <p className="text-[10px] text-[#6B7280]">Bug Score</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="mb-1 flex h-12 w-12 items-center justify-center rounded-full bg-[#F3F4F6] mx-auto">
              {health.project_health === "Excellent" ? (
                <CheckCircle2 className="h-6 w-6 text-[#059669]" />
              ) : health.project_health === "Good" || health.project_health === "Fair" ? (
                <AlertTriangle className="h-6 w-6 text-[#F59E0B]" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-[#DC2626]" />
              )}
            </div>
            <p className="text-[10px] text-[#6B7280]">Project Health</p>
            <p className="text-xs font-semibold text-[#111827]">{health.project_health}</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="relative mx-auto mb-1 flex h-12 w-12 items-center justify-center">
              <svg className="h-12 w-12 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#F3F4F6" strokeWidth="3" />
                <circle
                  cx="18" cy="18" r="15.5" fill="none"
                  stroke={healthColor(health.security_health)}
                  strokeWidth="3"
                  strokeDasharray={`${(health.security_health / 100) * 97.4} 97.4`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute text-xs font-bold text-[#111827]">{health.security_health}</span>
            </div>
            <p className="text-[10px] text-[#6B7280]">Security</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="relative mx-auto mb-1 flex h-12 w-12 items-center justify-center">
              <svg className="h-12 w-12 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#F3F4F6" strokeWidth="3" />
                <circle
                  cx="18" cy="18" r="15.5" fill="none"
                  stroke={healthColor(health.performance_health)}
                  strokeWidth="3"
                  strokeDasharray={`${(health.performance_health / 100) * 97.4} 97.4`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute text-xs font-bold text-[#111827]">{health.performance_health}</span>
            </div>
            <p className="text-[10px] text-[#6B7280]">Performance</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="relative mx-auto mb-1 flex h-12 w-12 items-center justify-center">
              <svg className="h-12 w-12 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#F3F4F6" strokeWidth="3" />
                <circle
                  cx="18" cy="18" r="15.5" fill="none"
                  stroke={healthColor(health.maintainability_health)}
                  strokeWidth="3"
                  strokeDasharray={`${(health.maintainability_health / 100) * 97.4} 97.4`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute text-xs font-bold text-[#111827]">{health.maintainability_health}</span>
            </div>
            <p className="text-[10px] text-[#6B7280]">Maintainability</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="mb-1 flex h-12 w-12 items-center justify-center rounded-full bg-[#F3F4F6] mx-auto">
              {health.overall_readiness === "Ready" ? (
                <CheckCircle2 className="h-6 w-6 text-[#059669]" />
              ) : health.overall_readiness === "Conditional" ? (
                <AlertTriangle className="h-6 w-6 text-[#F59E0B]" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-[#DC2626]" />
              )}
            </div>
            <p className="text-[10px] text-[#6B7280]">Readiness</p>
            <p className="text-xs font-semibold text-[#111827]">{health.overall_readiness}</p>
          </CardContent></Card>
        </div>
      </section>

      {/* --- Top 10 Priority Issues --- */}
      {hasIssues && (
        <section>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Top Priority Issues
          </p>
          <div className="space-y-2">
            {topIssues.map((issue, i) => (
              <Card key={i} hover={false}>
                <CardContent className="flex items-start gap-3 p-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#F3F4F6] text-[10px] font-bold text-[#6B7280]">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium"
                        style={{
                          backgroundColor: `${severityColors[issue.severity] || "#F3F4F6"}18`,
                          color: severityColors[issue.severity] || "#6B7280",
                        }}
                      >
                        {issue.severity}
                      </span>
                      <span className="text-xs font-semibold text-[#111827]">
                        {issue.bug_title}
                      </span>
                    </div>
                    <p className="mt-0.5 text-[10px] text-[#6B7280]">
                      {issue.affected_file}
                      {issue.function_name ? ` → ${issue.function_name}` : ""}
                    </p>
                    <p className="mt-0.5 text-[10px] leading-relaxed text-[#374151]">
                      {issue.description}
                    </p>
                    {issue.suggested_action && (
                      <p className="mt-0.5 text-[10px] text-[#2563EB]">
                        Action: {issue.suggested_action}
                      </p>
                    )}
                    <span className="mt-1 inline-flex items-center gap-1 rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#6B7280]">
                      {issue.confidence}% AI Confidence
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* --- Charts Row --- */}
      <div className="grid gap-6 sm:grid-cols-2">
        {/* Severity Distribution */}
        <Card hover={false}>
          <CardContent className="p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
              Severity Distribution
            </p>
            {hasIssues ? (
              <div className="space-y-2">
                {[
                  {
                    label: "Critical",
                    count: stats.critical_count,
                    color: "#DC2626",
                  },
                  { label: "High", count: stats.high_count, color: "#EA580C" },
                  { label: "Medium", count: stats.medium_count, color: "#F59E0B" },
                  { label: "Low", count: stats.low_count, color: "#9CA3AF" },
                ]
                  .filter((s) => s.count > 0)
                  .map((s) => (
                    <div key={s.label}>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[#374151]">{s.label}</span>
                        <span className="font-medium text-[#111827]">{s.count}</span>
                      </div>
                      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[#F3F4F6]">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{
                            width: `${(s.count / stats.total_issues) * 100}%`,
                          }}
                          className="h-full rounded-full"
                          style={{ backgroundColor: s.color }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-xs text-[#6B7280]">No issues detected</p>
            )}
          </CardContent>
        </Card>

        {/* Category Distribution */}
        <Card hover={false}>
          <CardContent className="p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
              Bug Category Distribution
            </p>
            {categoryDist.length > 0 ? (
              <div className="space-y-2">
                {categoryDist.map((c) => (
                  <div key={c.name}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[#374151]">{c.name}</span>
                      <span className="font-medium text-[#111827]">
                        {c.count} ({c.percentage}%)
                      </span>
                    </div>
                    <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[#F3F4F6]">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${c.percentage}%` }}
                        className="h-full rounded-full bg-[#2563EB]"
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#6B7280]">No issues detected</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* --- Affected Modules + Files --- */}
      <div className="grid gap-6 sm:grid-cols-2">
        <Card hover={false}>
          <CardContent className="p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
              Affected Modules
            </p>
            {moduleChart.length > 0 ? (
              <div className="space-y-2">
                {moduleChart.map((m) => (
                  <div key={m.label}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="truncate text-[#374151]">{m.label}</span>
                      <span className="ml-2 shrink-0 font-medium text-[#111827]">
                        {m.value}
                      </span>
                    </div>
                    <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[#F3F4F6]">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{
                          width: `${(m.value / Math.max(...moduleChart.map((x) => x.value))) * 100}%`,
                        }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: m.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#6B7280]">No modules affected</p>
            )}
          </CardContent>
        </Card>

        <Card hover={false}>
          <CardContent className="p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
              Affected Files
            </p>
            {fileChart.length > 0 ? (
              <div className="space-y-2">
                {fileChart.map((f) => (
                  <div key={f.label}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="truncate text-[#374151]">{f.label}</span>
                      <span className="ml-2 shrink-0 font-medium text-[#111827]">
                        {f.value}
                      </span>
                    </div>
                    <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[#F3F4F6]">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{
                          width: `${(f.value / Math.max(...fileChart.map((x) => x.value))) * 100}%`,
                        }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: f.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#6B7280]">No files affected</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* --- AI Recommendations --- */}
      <Card hover={false}>
        <CardContent className="p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#EFF6FF]">
              <TrendingUp className="h-4 w-4 text-[#2563EB]" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
                AI Recommendations
              </p>

              {/* Immediate Fixes */}
              {recommendations.immediate.length > 0 && (
                <div className="mb-3">
                  <p className="mb-1 text-xs font-semibold text-[#DC2626]">
                    Immediate Fixes
                  </p>
                  <ul className="space-y-1">
                    {recommendations.immediate.map((r, i) => (
                      <li
                        key={i}
                        className="flex gap-2 text-xs text-[#374151]"
                      >
                        <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#DC2626]" />
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* High Priority */}
              {recommendations.highPriority.length > 0 && (
                <div className="mb-3">
                  <p className="mb-1 text-xs font-semibold text-[#EA580C]">
                    High Priority Fixes
                  </p>
                  <ul className="space-y-1">
                    {recommendations.highPriority.map((r, i) => (
                      <li
                        key={i}
                        className="flex gap-2 text-xs text-[#374151]"
                      >
                        <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#EA580C]" />
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommended Order */}
              <div className="mb-3">
                <p className="mb-1 text-xs font-semibold text-[#2563EB]">
                  Recommended Order
                </p>
                <ul className="space-y-1">
                  {recommendations.recommendedOrder.map((r, i) => (
                    <li
                      key={i}
                      className="flex gap-2 text-xs text-[#374151]"
                    >
                      <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#2563EB]" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Overall */}
              <div className="rounded-lg bg-[#F9FAFB] p-3">
                <div className="flex items-center gap-4 text-xs">
                  <div>
                    <span className="text-[#6B7280]">Repair Complexity: </span>
                    <span className="font-medium text-[#111827]">
                      {recommendations.estimatedComplexity}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#6B7280]">Estimated Time: </span>
                    <span className="font-medium text-[#111827]">
                      {recommendations.estimatedTime}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* --- Search + Filter + Export Row --- */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[200px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Search bugs, files, functions..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-8 text-xs text-[#111827] placeholder-[#9CA3AF] outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs text-[#374151] outline-none focus:border-[#2563EB]"
        >
          <option value="all">All Severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs text-[#374151] outline-none focus:border-[#2563EB]"
        >
          <option value="all">All Categories</option>
          {categoryDist.map((c) => (
            <option key={c.name} value={c.name.toLowerCase()}>
              {c.name}
            </option>
          ))}
        </select>

        <div className="flex items-center gap-1.5 border-l border-[#E5E7EB] pl-3">
          <button
            onClick={handleExportJSON}
            className="inline-flex items-center gap-1 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[10px] font-medium text-[#374151] hover:bg-[#F9FAFB]"
          >
            <FileCode className="h-3 w-3" /> JSON
          </button>
          <button
            onClick={handleExportText}
            className="inline-flex items-center gap-1 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[10px] font-medium text-[#374151] hover:bg-[#F9FAFB]"
          >
            <FileText className="h-3 w-3" /> Report
          </button>
          <button
            onClick={handleExportPDF}
            className="inline-flex items-center gap-1 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[10px] font-medium text-[#374151] hover:bg-[#F9FAFB]"
          >
            <Download className="h-3 w-3" /> PDF
          </button>
        </div>
      </div>

      {/* --- Search Results Table --- */}
      {hasIssues && (search || severityFilter !== "all" || categoryFilter !== "all") && (
        <Card hover={false}>
          <CardContent className="p-0">
            <div className="max-h-60 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b border-[#E5E7EB]">
                    <th className="p-3 text-left font-medium text-[#6B7280]">Severity</th>
                    <th className="p-3 text-left font-medium text-[#6B7280]">Bug</th>
                    <th className="p-3 text-left font-medium text-[#6B7280]">File</th>
                    <th className="p-3 text-left font-medium text-[#6B7280]">Category</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIssues.slice(0, 50).map((issue, i) => (
                    <tr key={i} className="border-b border-[#F9FAFB] hover:bg-[#F9FAFB]">
                      <td className="p-3">
                        <span
                          className="inline-flex items-center rounded-full px-2 py-0.5 text-[9px] font-medium"
                          style={{
                            backgroundColor: `${severityColors[issue.severity] || "#F3F4F6"}18`,
                            color: severityColors[issue.severity] || "#6B7280",
                          }}
                        >
                          {issue.severity}
                        </span>
                      </td>
                      <td className="max-w-[200px] truncate p-3 text-[#111827]">
                        {issue.bug_title}
                      </td>
                      <td className="max-w-[150px] truncate p-3 text-[#6B7280]">
                        {issue.affected_file}
                      </td>
                      <td className="p-3 text-[#6B7280]">
                        {categoryEngineNames[issue.source_engine] || issue.source_engine}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredIssues.length > 50 && (
                <p className="p-3 text-center text-[10px] text-[#9CA3AF]">
                  Showing 50 of {filteredIssues.length} results
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* --- Continue to Root Cause Analysis --- */}
      <div className="text-center">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="inline-flex items-center gap-2 rounded-xl bg-[#2563EB] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[#2563EB]/20 hover:bg-[#1D4ED8]"
          onClick={() => navigate(`/projects/${projectId}/root-cause`)}
        >
          Continue to Root Cause Analysis
          <ArrowRight className="h-4 w-4" />
        </motion.button>
        <p className="mt-2 text-[10px] text-[#6B7280]">
          Phase 5 — Root cause analysis will investigate the detected issues.
        </p>
      </div>
    </motion.div>
  );
}
