import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Award,
  BarChart3,
  BookOpen,
  Braces,
  Building2,
  CheckCircle2,
  Cpu,
  FileSearch,
  GitBranch,
  Globe,
  HeartPulse,
  Lightbulb,
  Radar,
  RefreshCw,
  Search,
  Shield,
  Timer,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { getUnifiedIntelligence } from "@/lib/project-analyzer";
import type { ProjectTimelineStage, UnifiedIntelligenceResponse } from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityStyles: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]",
  warning: "bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]",
  info: "bg-[#EFF6FF] text-[#1E40AF] border-[#BFDBFE]",
};

const scoreColor = (v: number) =>
  v >= 70 ? "text-[#065F46]" : v >= 40 ? "text-[#92400E]" : "text-[#DC2626]";

const scoreBg = (v: number) =>
  v >= 70 ? "bg-[#059669]" : v >= 40 ? "bg-[#D97706]" : "bg-[#DC2626]";

function ScoreBar({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-28 text-[10px] font-medium text-[#6B7280] truncate">{label}</span>
      <div className="h-2 flex-1 rounded-full bg-[#F3F4F6] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${scoreBg(value)}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className={`w-8 text-right text-[10px] font-semibold ${scoreColor(value)}`}>
        {Math.round(value)}
      </span>
    </div>
  );
}

function StageIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle2 className="h-4 w-4 text-[#059669]" />;
  if (status === "pending") return <Timer className="h-4 w-4 text-[#9CA3AF]" />;
  return <XCircle className="h-4 w-4 text-[#DC2626]" />;
}

export function UnifiedIntelligence() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<UnifiedIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getUnifiedIntelligence(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load unified intelligence",
      );
    } finally {
      setLoading(false);
      fetchedRef.current = true;
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const searchResults = useMemo(() => {
    if (!data || !searchQuery) return null;
    const q = searchQuery.toLowerCase();
    const allResults: { category: string; items: { label: string; link: string; detail: string }[] }[] = [];

    const hubItems = data.knowledge_hub.filter(
      (h) => h.label.toLowerCase().includes(q) || h.category.toLowerCase().includes(q) || h.value.toLowerCase().includes(q)
    );
    if (hubItems.length > 0) {
      allResults.push({
        category: "Knowledge Hub",
        items: hubItems.map((h) => ({ label: h.label, link: h.link, detail: h.value })),
      });
    }

    const insights = data.insights.filter(
      (i) => i.label.toLowerCase().includes(q) || i.type.toLowerCase().includes(q) || i.detail.toLowerCase().includes(q)
    );
    if (insights.length > 0) {
      allResults.push({
        category: "Insights",
        items: insights.map((i) => ({ label: i.label, link: i.source, detail: i.value })),
      });
    }

    const healthKeys: { label: string; key: keyof typeof data.health; link: string }[] = [
      { label: "Overall Health", key: "overall_health", link: "" },
      { label: "Architecture", key: "architecture_health", link: "architecture" },
      { label: "Dependencies", key: "dependency_health", link: "dependencies" },
      { label: "Security", key: "security_health", link: "configuration" },
      { label: "Performance", key: "performance_health", link: "file-analysis" },
      { label: "Maintainability", key: "maintainability", link: "code-quality" },
    ];
    const matchedHealth = healthKeys.filter((h) => h.label.toLowerCase().includes(q));
    if (matchedHealth.length > 0) {
      allResults.push({
        category: "Health Metrics",
        items: matchedHealth.map((h) => ({
          label: h.label,
          link: h.link,
          detail: `${data.health[h.key]}/100`,
        })),
      });
    }

    if (allResults.length === 0 && q.length >= 2) {
      allResults.push({
        category: "No Results",
        items: [{ label: `No matches found for "${searchQuery}"`, link: "", detail: "Try different keywords like auth, forecast, database, prediction, report, validation" }],
      });
    }

    return allResults;
  }, [data, searchQuery]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Loading unified intelligence dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Failed to load</p>
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
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Braces className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run project analysis to generate the unified dashboard.</p>
      </div>
    );
  }

  const h = data.health;
  const s = data.scores;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-5"
    >
      {projectId && (
        <button
          onClick={() => navigate(`/projects/${projectId}/analyzer`)}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]"
        >
          ← Back to Overview
        </button>
      )}

      {/* Hero */}
      <div className="overflow-hidden rounded-xl bg-gradient-to-br from-[#7C3AED] to-[#2563EB]">
        <div className="px-6 py-8 text-white">
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
            <Radar className="h-3.5 w-3.5" /> Unified AI Analyzer Dashboard
          </div>
          <p className="mt-1 text-2xl font-bold">Enterprise Intelligence Hub</p>
          <p className="mt-1 text-sm text-white/80">
            Unified health, scores, insights, knowledge graph, and cross-analyzer navigation.
          </p>
        </div>
      </div>

      {/* Global Search */}
      <div className={sectionClass}>
        <div className="flex items-center gap-2 px-4 py-2.5">
          <Search className="h-3.5 w-3.5 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Global search — try: auth, forecast, database, prediction, report, validation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 border-0 bg-transparent text-xs text-[#111827] placeholder-[#9CA3AF] outline-none"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="rounded px-2 py-1 text-[10px] font-medium text-[#DC2626] hover:bg-[#FEF2F2]"
            >
              Clear
            </button>
          )}
        </div>
        {searchQuery && searchResults && (
          <div className="border-t border-[#F3F4F6] px-4 py-3 space-y-3 max-h-60 overflow-y-auto">
            {searchResults.map((group) => (
              <div key={group.category}>
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                  {group.category} ({group.items.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {group.items.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        if (item.link) navigate(`/projects/${projectId}/analyzer/${item.link}`);
                      }}
                      className={`rounded px-2 py-1 text-[9px] font-medium transition-colors ${
                        item.link
                          ? "bg-[#EFF6FF] text-[#1E40AF] hover:bg-[#DBEAFE]"
                          : "bg-[#F3F4F6] text-[#6B7280]"
                      }`}
                      disabled={!item.link}
                    >
                      {item.label}
                      {item.detail && (
                        <span className="ml-1 text-[8px] opacity-70">— {item.detail}</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className={sectionClass}>
        <div className="flex border-b border-[#F3F4F6] overflow-x-auto">
          {[
            { id: "overview", label: "Overview" },
            { id: "health", label: "Health" },
            { id: "scores", label: "Scores" },
            { id: "insights", label: `Insights (${data.insights.length})` },
            { id: "summary", label: "Executive Summary" },
            { id: "hub", label: "Knowledge Hub" },
            { id: "timeline", label: "Timeline" },
            { id: "health-map", label: "Health Map" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-4 py-2.5 text-xs font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? "border-b-2 border-[#2563EB] text-[#2563EB]"
                  : "text-[#6B7280] hover:text-[#111827]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── Overview Tab ── */}
        {activeTab === "overview" && (
          <div className="p-4 space-y-4">
            {/* Health Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {[
                { label: "Overall Health", value: h.overall_health, icon: HeartPulse },
                { label: "Overall Quality", value: h.overall_quality, icon: Award },
                { label: "Maintainability", value: h.maintainability, icon: Cpu },
                { label: "Readiness", value: h.readiness, icon: Shield },
                { label: "AI Confidence", value: h.ai_confidence, icon: TrendingUp },
              ].map((stat) => (
                <div key={stat.label} className="rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] p-3 text-center">
                  <stat.icon className={`mx-auto h-4 w-4 ${scoreColor(stat.value)}`} />
                  <p className={`mt-1 text-lg font-bold ${scoreColor(stat.value)}`}>{Math.round(stat.value)}</p>
                  <p className="text-[9px] text-[#6B7280]">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Scores Summary */}
            <div className={sectionClass + " p-4"}>
              <p className="text-xs font-semibold text-[#374151] mb-3">Project Scores</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2">
                {[
                  { label: "Overall Score", value: s.overall_score },
                  { label: "Architecture", value: s.architecture_score },
                  { label: "Code Quality", value: s.code_quality_score },
                  { label: "Dependencies", value: s.dependency_score },
                  { label: "Security", value: s.security_score },
                  { label: "Semantic", value: s.semantic_score },
                ].map((sc) => (
                  <ScoreBar key={sc.label} label={sc.label} value={sc.value} />
                ))}
              </div>
            </div>

            {/* Quick Links */}
            <div className={sectionClass + " p-4"}>
              <p className="text-xs font-semibold text-[#374151] mb-3">Cross-Analyzer Navigation</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {[
                  { label: "Architecture", path: "architecture", icon: Building2 },
                  { label: "Dependencies", path: "dependencies", icon: GitBranch },
                  { label: "File Analysis", path: "file-analysis", icon: FileSearch },
                  { label: "Function & Class", path: "function-class-intelligence", icon: Braces },
                  { label: "Call Graph", path: "call-graph", icon: Globe },
                  { label: "Semantic Intel", path: "semantic-intelligence", icon: Radar },
                  { label: "Code Quality", path: "code-quality", icon: Award },
                  { label: "Configuration", path: "configuration", icon: Cpu },
                ].map((link) => (
                  <button
                    key={link.path}
                    onClick={() => navigate(`/projects/${projectId}/analyzer/${link.path}`)}
                    className="flex items-center gap-2 rounded-lg border border-[#E5E7EB] px-3 py-2 text-[10px] font-medium text-[#374151] hover:border-[#2563EB] hover:text-[#2563EB] transition-colors"
                  >
                    <link.icon className="h-3 w-3" />
                    {link.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Summary */}
            <div className={sectionClass + " p-4"}>
              <div className="flex items-center gap-1.5 mb-2">
                <Lightbulb className="h-3.5 w-3.5 text-[#D97706]" />
                <span className="text-xs font-semibold text-[#374151]">Executive Summary</span>
              </div>
              <p className="text-[10px] text-[#6B7280] leading-relaxed">{data.executive_summary.project_summary}</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {data.insights.slice(0, 4).map((ins, idx) => (
                  <span key={idx} className={`rounded px-1.5 py-0.5 text-[8px] font-medium ${severityStyles[ins.severity] || severityStyles.info}`}>
                    {ins.label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Health Tab ── */}
        {activeTab === "health" && (
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { label: "Overall Health", value: h.overall_health, desc: "Aggregated health across all analyzers" },
                { label: "Overall Quality", value: h.overall_quality, desc: "Overall code quality and project health" },
                { label: "Architecture Health", value: h.architecture_health, desc: "Architecture pattern, layers, and entry points" },
                { label: "Dependency Health", value: h.dependency_health, desc: "Import structure, coupling, and circular deps" },
                { label: "Security Health", value: h.security_health, desc: "Security checks and configuration posture" },
                { label: "Performance Health", value: h.performance_health, desc: "File sizes, complexity, and resource usage" },
                { label: "Maintainability", value: h.maintainability, desc: "Code clarity, duplication, and documentation" },
                { label: "Readiness", value: h.readiness, desc: "Overall project readiness assessment" },
                { label: "Technical Debt", value: h.technical_debt, desc: "Accumulated technical debt estimation" },
                { label: "AI Confidence", value: h.ai_confidence, desc: "Confidence in automated analysis results" },
              ].map((metric) => (
                <div key={metric.label} className="rounded-lg border border-[#E5E7EB] p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-[#374151]">{metric.label}</p>
                      <p className="text-[9px] text-[#9CA3AF]">{metric.desc}</p>
                    </div>
                    <span className={`text-lg font-bold ${scoreColor(metric.value)}`}>
                      {Math.round(metric.value)}
                    </span>
                  </div>
                  <div className="mt-2 h-2 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                    <div
                      className={`h-full rounded-full ${scoreBg(metric.value)}`}
                      style={{ width: `${Math.min(metric.value, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Scores Tab ── */}
        {activeTab === "scores" && (
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { label: "Overall Score", value: s.overall_score, desc: "Weighted average of all score dimensions", link: "" },
                { label: "Architecture Score", value: s.architecture_score, desc: "Architecture detection and layering", link: "architecture" },
                { label: "Code Quality Score", value: s.code_quality_score, desc: "Code quality, issues, and best practices", link: "code-quality" },
                { label: "Dependency Score", value: s.dependency_score, desc: "Dependency health and import structure", link: "dependencies" },
                { label: "Security Score", value: s.security_score, desc: "Security posture and configuration checks", link: "configuration" },
                { label: "File Quality Score", value: s.file_quality_score, desc: "File-level health and organization", link: "file-analysis" },
                { label: "Function Quality Score", value: s.function_quality_score, desc: "Function complexity and class structure", link: "function-class-intelligence" },
                { label: "Configuration Score", value: s.configuration_score, desc: "Configuration file organization and health", link: "configuration" },
                { label: "Semantic Score", value: s.semantic_score, desc: "Semantic understanding and business logic mapping", link: "semantic-intelligence" },
              ].map((sc) => (
                <button
                  key={sc.label}
                  onClick={() => sc.link && navigate(`/projects/${projectId}/analyzer/${sc.link}`)}
                  className={`rounded-lg border border-[#E5E7EB] p-4 text-left transition-colors ${sc.link ? "hover:border-[#2563EB] hover:shadow-sm cursor-pointer" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-[#374151]">{sc.label}</p>
                    <span className={`text-lg font-bold ${scoreColor(sc.value)}`}>
                      {Math.round(sc.value)}
                    </span>
                  </div>
                  <p className="mt-1 text-[9px] text-[#9CA3AF]">{sc.desc}</p>
                  <div className="mt-2 h-1.5 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                    <div
                      className={`h-full rounded-full ${scoreBg(sc.value)}`}
                      style={{ width: `${Math.min(sc.value, 100)}%` }}
                    />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Insights Tab ── */}
        {activeTab === "insights" && (
          <div className="p-4">
            {data.insights.length > 0 ? (
              <div className="grid gap-2 sm:grid-cols-2">
                {data.insights.map((insight, idx) => (
                  <div
                    key={idx}
                    className={`rounded-lg border p-3 ${severityStyles[insight.severity] || severityStyles.info}`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${
                        insight.severity === "critical" ? "bg-[#FEF2F2] text-[#991B1B]"
                        : insight.severity === "warning" ? "bg-[#FFFBEB] text-[#92400E]"
                        : "bg-[#EFF6FF] text-[#1E40AF]"
                      }`}>
                        {insight.severity}
                      </span>
                      <span className="text-[9px] font-medium text-[#6B7280]">{insight.source}</span>
                    </div>
                    <p className="mt-1 text-xs font-semibold text-[#111827]">{insight.label}</p>
                    <p className="mt-0.5 text-[10px] text-[#6B7280]">{insight.value}</p>
                    <p className="mt-0.5 text-[9px] italic opacity-70">{insight.detail}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <Lightbulb className="mb-2 h-6 w-6" />
                No global insights generated.
              </div>
            )}
          </div>
        )}

        {/* ── Executive Summary Tab ── */}
        {activeTab === "summary" && (
          <div className="p-4 space-y-3">
            {[
              { label: "Project Summary", value: data.executive_summary.project_summary },
              { label: "Architecture Summary", value: data.executive_summary.architecture_summary },
              { label: "Business Logic Summary", value: data.executive_summary.business_logic_summary },
              { label: "Risk Summary", value: data.executive_summary.risk_summary },
              { label: "Security Summary", value: data.executive_summary.security_summary },
              { label: "Recommendation Summary", value: data.executive_summary.recommendation_summary },
            ].map((section) => (
              <div key={section.label} className="rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] p-3">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">{section.label}</p>
                <p className="mt-1 text-xs text-[#374151] leading-relaxed">
                  {section.value || "No data available."}
                </p>
              </div>
            ))}
            {data.executive_summary.future_improvements.length > 0 && (
              <div className="rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] p-3">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Future Improvements</p>
                <ul className="mt-1 space-y-1">
                  {data.executive_summary.future_improvements.map((imp, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-[10px] text-[#374151]">
                      <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#2563EB]" />
                      {imp}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* ── Knowledge Hub Tab ── */}
        {activeTab === "hub" && (
          <div className="p-4">
            {data.knowledge_hub.length > 0 ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {data.knowledge_hub.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => item.link && navigate(`/projects/${projectId}/analyzer/${item.link}`)}
                    className={`rounded-lg border border-[#E5E7EB] p-3 text-left transition-colors ${
                      item.link ? "hover:border-[#2563EB] hover:shadow-sm cursor-pointer" : ""
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[8px] font-semibold uppercase text-[#1E40AF]">
                        {item.category}
                      </span>
                      {item.count > 0 && (
                        <span className="ml-auto rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] font-medium text-[#6B7280]">
                          {item.count}
                        </span>
                      )}
                    </div>
                    <p className="mt-1.5 text-xs font-semibold text-[#111827]">{item.label}</p>
                    <p className="mt-0.5 text-[9px] text-[#6B7280]">{item.value}</p>
                  </button>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <BookOpen className="mb-2 h-6 w-6" />
                No knowledge hub data available.
              </div>
            )}
          </div>
        )}

        {/* ── Timeline Tab ── */}
        {activeTab === "timeline" && (
          <div className="p-4">
            <div className="relative">
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-[#E5E7EB]" />
              <div className="space-y-4">
                {data.timeline.map((stage: ProjectTimelineStage) => (
                  <div key={stage.stage} className="relative flex items-start gap-4 pl-10">
                    <div className="absolute left-2.5 -translate-x-1/2 bg-white p-0.5 rounded-full">
                      <StageIcon status={stage.status} />
                    </div>
                    <div className="flex-1 rounded-lg border border-[#E5E7EB] p-3 hover:border-[#2563EB] transition-colors">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#111827]">{stage.label}</span>
                        <div className="flex items-center gap-2">
                          <span className={`rounded px-1.5 py-0.5 text-[8px] font-medium capitalize ${
                            stage.status === "completed" ? "bg-[#ECFDF5] text-[#065F46]"
                            : "bg-[#F3F4F6] text-[#6B7280]"
                          }`}>
                            {stage.status}
                          </span>
                          {stage.score > 0 && (
                            <span className="text-[9px] text-[#9CA3AF]">
                              Score: {Math.round(stage.score)}
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="mt-0.5 text-[9px] text-[#6B7280]">{stage.details}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Health Map Tab ── */}
        {activeTab === "health-map" && (
          <div className="p-4">
            {data.health_map.length > 0 ? (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="flex items-center gap-1 text-[9px]">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#059669]" /> Healthy
                  </span>
                  <span className="flex items-center gap-1 text-[9px]">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#D97706]" /> Warning
                  </span>
                  <span className="flex items-center gap-1 text-[9px]">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#DC2626]" /> Critical
                  </span>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {data.health_map.map((mod) => (
                    <div
                      key={mod.name}
                      className="rounded-lg border border-[#E5E7EB] p-3"
                    >
                      <div className="flex items-center gap-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${
                          mod.status === "healthy" ? "bg-[#059669]"
                          : mod.status === "warning" ? "bg-[#D97706]"
                          : "bg-[#DC2626]"
                        }`} />
                        <span className="text-xs font-medium text-[#111827]">{mod.name}</span>
                        <span className={`ml-auto rounded px-1.5 py-0.5 text-[8px] font-medium capitalize ${
                          mod.status === "healthy" ? "bg-[#ECFDF5] text-[#065F46]"
                          : mod.status === "warning" ? "bg-[#FFFBEB] text-[#92400E]"
                          : "bg-[#FEF2F2] text-[#991B1B]"
                        }`}>
                          {mod.status}
                        </span>
                      </div>
                      <div className="mt-2 flex items-center gap-3 text-[9px] text-[#6B7280]">
                        <span>Score: {mod.score}/100</span>
                        {mod.issues > 0 && <span>Issues: {mod.issues}</span>}
                      </div>
                      <div className="mt-1.5 h-1.5 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            mod.status === "healthy" ? "bg-[#059669]"
                            : mod.status === "warning" ? "bg-[#D97706]"
                            : "bg-[#DC2626]"
                          }`}
                          style={{ width: `${Math.min(mod.score, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <BarChart3 className="mb-2 h-6 w-6" />
                No health map data available.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Cross Navigation */}
      {projectId && (
        <RelatedAnalysisNav projectId={projectId} currentPage="unified-intelligence" />
      )}
    </motion.div>
  );
}

export default UnifiedIntelligence;
