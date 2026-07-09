import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Code,
  Gauge,
  Hammer,
  Layout,
  Lightbulb,
  RefreshCw,
  Search,
  Shield,
  Wrench,
  X,
} from "lucide-react";
import { getMaintainabilityIntelligence } from "@/lib/project-analyzer";
import type {
  MaintainabilityIntelligenceResponse,
  CodeSmellItem,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityBadge: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B]",
  high: "bg-[#FFFBEB] text-[#92400E]",
  medium: "bg-[#EFF6FF] text-[#1E40AF]",
  low: "bg-[#ECFDF5] text-[#065F46]",
  informational: "bg-[#F3F4F6] text-[#6B7280]",
};

const scoreColor = (v: number) =>
  v >= 70 ? "text-[#059669]" : v >= 40 ? "text-[#D97706]" : "text-[#DC2626]";

const scoreBg = (v: number) =>
  v >= 70 ? "bg-[#059669]" : v >= 40 ? "bg-[#D97706]" : "bg-[#DC2626]";

const typeLabels: Record<string, string> = {
  "large-class": "Large Class",
  "god-class": "God Class",
  "long-function": "Long Function",
  "long-parameter-list": "Long Parameter List",
  "duplicate-code": "Duplicate Code",
  "unused-code": "Unused Code",
  "magic-number": "Magic Number",
  "high-coupling": "High Coupling",
  "low-cohesion": "Low Cohesion",
  "poor-naming": "Poor Naming",
  "missing-documentation": "Missing Documentation",
  "deep-nesting": "Deep Nesting",
  "architecture-smell": "Architecture Smell",
  "maintainability-smell": "Maintainability Smell",
};

function ScoreGauge({ value, label }: { value: number; label: string }) {
  const color = scoreColor(value);
  const bg = scoreBg(value);
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative h-20 w-20">
        <svg className="h-20 w-20 -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="34" fill="none" stroke="#F3F4F6" strokeWidth="6" />
          <circle
            cx="40" cy="40" r="34" fill="none" stroke="currentColor" strokeWidth="6"
            strokeDasharray={`${2 * Math.PI * 34}`}
            strokeDashoffset={`${2 * Math.PI * 34 * (1 - value / 100)}`}
            strokeLinecap="round" className={bg.replace("bg-", "text-")}
          />
        </svg>
        <span className={`absolute inset-0 flex items-center justify-center text-lg font-bold ${color}`}>
          {Math.round(value)}
        </span>
      </div>
      <p className="text-[9px] font-medium text-[#6B7280] text-center">{label}</p>
    </div>
  );
}

function MiniGauge({ value }: { value: number }) {
  const color = scoreColor(value);
  return (
    <div className="relative h-10 w-10 shrink-0">
      <svg className="h-10 w-10 -rotate-90" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="16" fill="none" stroke="#F3F4F6" strokeWidth="4" />
        <circle
          cx="20" cy="20" r="16" fill="none" stroke="currentColor" strokeWidth="4"
          strokeDasharray={`${2 * Math.PI * 16}`}
          strokeDashoffset={`${2 * Math.PI * 16 * (1 - value / 100)}`}
          strokeLinecap="round"
          className={color.replace("text-", "text-")}
        />
      </svg>
      <span className={`absolute inset-0 flex items-center justify-center text-[8px] font-bold ${color}`}>
        {Math.round(value)}
      </span>
    </div>
  );
}

const SMELL_CATEGORIES: { key: string; label: string; types: string[] }[] = [
  { key: "duplication", label: "Duplicate Code", types: ["duplicate-code"] },
  { key: "dead", label: "Dead Code", types: ["unused-code"] },
  { key: "long-methods", label: "Long Methods", types: ["long-function"] },
  { key: "large-classes", label: "Large Classes", types: ["large-class", "god-class"] },
  { key: "deep-nesting", label: "Deep Nesting", types: ["deep-nesting"] },
  { key: "high-coupling", label: "High Coupling", types: ["high-coupling"] },
  { key: "low-cohesion", label: "Low Cohesion", types: ["low-cohesion"] },
  { key: "magic-numbers", label: "Magic Numbers", types: ["magic-number"] },
  { key: "poor-naming", label: "Poor Naming", types: ["poor-naming"] },
  { key: "missing-docs", label: "Missing Documentation", types: ["missing-documentation"] },
  { key: "long-params", label: "Long Parameter Lists", types: ["long-parameter-list"] },
  { key: "arch-smells", label: "Architecture Smells", types: ["architecture-smell"] },
];

export function MaintainabilityIntelligence() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<MaintainabilityIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [selectedSmell, setSelectedSmell] = useState<CodeSmellItem | null>(null);
  const [selectedTab, setSelectedTab] = useState<"smells" | "debt" | "modules" | "scores">("scores");
  const [sortBy, setSortBy] = useState<"severity" | "name" | "effort">("severity");
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getMaintainabilityIntelligence(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load maintainability intelligence",
      );
    } finally {
      setLoading(false);
      fetchedRef.current = true;
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const categorySmellCounts = useMemo(() => {
    if (!data) return {};
    const counts: Record<string, { count: number; severity: string }> = {};
    for (const cat of SMELL_CATEGORIES) {
      const matching = data.code_smells.filter((s) => cat.types.includes(s.type));
      if (matching.length > 0) {
        const topSev: string = matching.reduce((max, s) => {
          const order: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1, informational: 0 };
          return (order[s.severity] || 0) > (order[max] || 0) ? s.severity : max;
        }, "low");
        counts[cat.key] = { count: matching.length, severity: topSev };
      }
    }
    return counts;
  }, [data]);

  const filteredSmells = useMemo(() => {
    if (!data) return [];
    let list = [...data.code_smells];
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.type.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q) ||
          s.affected_files.some((f) => f.toLowerCase().includes(q)) ||
          s.affected_classes.some((c) => c.toLowerCase().includes(q)) ||
          s.affected_functions.some((f) => f.toLowerCase().includes(q)),
      );
    }
    if (severityFilter !== "all") {
      list = list.filter((s) => s.severity === severityFilter);
    }
    if (typeFilter !== "all") {
      list = list.filter((s) => s.type === typeFilter);
    }
    const sortOrder: Record<string, number> = {
      critical: 0, high: 1, medium: 2, low: 3, informational: 4,
    };
    if (sortBy === "severity") {
      list.sort((a, b) => (sortOrder[a.severity] ?? 5) - (sortOrder[b.severity] ?? 5));
    } else if (sortBy === "name") {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortBy === "effort") {
      const effortVal = (e: string | undefined) => {
        const m = (e || "").match(/(\d+)/);
        return m ? parseInt(m[1] || "0") : 999;
      };
      list.sort((a, b) => effortVal(b.refactoring_effort) - effortVal(a.refactoring_effort));
    }
    return list;
  }, [data, searchQuery, severityFilter, typeFilter, sortBy]);

  const uniqueTypes = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.code_smells.map((s) => s.type))].sort();
  }, [data]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Loading maintainability intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Failed to load</p>
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
        <Wrench className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No maintainability data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run project analysis to generate maintainability intelligence.</p>
      </div>
    );
  }

  const ms = data.maintainability_score;
  const td = data.technical_debt;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-5"
    >
      <div className="flex items-center gap-2">
        {projectId && (
          <>
            <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
              ← Back to Overview
            </button>
            <span className="text-[#D1D5DB]">|</span>
            <button onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]">
              Back to Unified Dashboard
            </button>
          </>
        )}
      </div>

      {/* Hero */}
      <div className="overflow-hidden rounded-xl bg-gradient-to-br from-[#059669] to-[#064E3B]">
        <div className="px-6 py-8 text-white">
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
            <Wrench className="h-3.5 w-3.5" /> Maintainability Analysis
          </div>
          <p className="mt-1 text-2xl font-bold">Maintainability</p>
          <p className="mt-1 text-sm text-white/80">
            Evaluate long-term maintainability, technical debt, code smells and refactoring readiness.
          </p>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        <div className="rounded-lg border border-[#E5E7EB] p-2.5 text-center bg-white">
          <p className={`text-sm font-bold ${scoreColor(ms.overall_maintainability_score)}`}>{Math.round(ms.overall_maintainability_score)}</p>
          <p className="text-[8px] text-[#6B7280] font-medium">Maintainability</p>
          <span className={`mt-0.5 inline-block rounded px-1 py-0.5 text-[7px] font-semibold uppercase ${severityBadge[ms.risk_level] || severityBadge.low}`}>{ms.risk_level}</span>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-2.5 text-center bg-white">
          <p className={`text-sm font-bold ${scoreColor(ms.maintainability_health)}`}>{Math.round(ms.maintainability_health)}</p>
          <p className="text-[8px] text-[#6B7280] font-medium">Health</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-2.5 text-center bg-white">
          <p className={`text-sm font-bold ${scoreColor(ms.refactoring_readiness)}`}>{Math.round(ms.refactoring_readiness)}</p>
          <p className="text-[8px] text-[#6B7280] font-medium">Refactoring</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-2.5 text-center bg-white">
          <p className={`text-sm font-bold ${scoreColor(100 - ms.technical_debt_score)}`}>{Math.round(ms.technical_debt_score)}</p>
          <p className="text-[8px] text-[#6B7280] font-medium">Tech Debt</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-2.5 text-center bg-white">
          <p className="text-sm font-bold text-[#991B1B]">{data.summary.critical_count}</p>
          <p className="text-[8px] text-[#DC2626] font-medium">Critical</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-2.5 text-center bg-white">
          <p className="text-sm font-bold text-[#111827]">{data.summary.high_count}</p>
          <p className="text-[8px] text-[#D97706] font-medium">High</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-2.5 text-center bg-white">
          <p className="text-sm font-bold text-[#111827]">{data.summary.medium_count}</p>
          <p className="text-[8px] text-[#2563EB] font-medium">Medium</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-2.5 text-center bg-white">
          <p className="text-sm font-bold text-[#111827]">{data.summary.low_count}</p>
          <p className="text-[8px] text-[#059669] font-medium">Low</p>
        </div>
      </div>

      {/* Tab selector */}
      <div className="flex items-center gap-2 flex-wrap">
        <button onClick={() => setSelectedTab("scores")}
          className={`rounded-lg px-3 py-1.5 text-[10px] font-semibold transition-colors ${
            selectedTab === "scores" ? "bg-[#059669] text-white" : "bg-[#F3F4F6] text-[#6B7280] hover:bg-[#E5E7EB]"
          }`}>
          <Gauge className="mr-1 inline h-3 w-3" /> Score Breakdown
        </button>
        <button onClick={() => setSelectedTab("smells")}
          className={`rounded-lg px-3 py-1.5 text-[10px] font-semibold transition-colors ${
            selectedTab === "smells" ? "bg-[#059669] text-white" : "bg-[#F3F4F6] text-[#6B7280] hover:bg-[#E5E7EB]"
          }`}>
          <Code className="mr-1 inline h-3 w-3" /> Code Smells ({data.code_smells.length})
        </button>
        <button onClick={() => setSelectedTab("debt")}
          className={`rounded-lg px-3 py-1.5 text-[10px] font-semibold transition-colors ${
            selectedTab === "debt" ? "bg-[#059669] text-white" : "bg-[#F3F4F6] text-[#6B7280] hover:bg-[#E5E7EB]"
          }`}>
          <Hammer className="mr-1 inline h-3 w-3" /> Technical Debt
        </button>
        <button onClick={() => setSelectedTab("modules")}
          className={`rounded-lg px-3 py-1.5 text-[10px] font-semibold transition-colors ${
            selectedTab === "modules" ? "bg-[#059669] text-white" : "bg-[#F3F4F6] text-[#6B7280] hover:bg-[#E5E7EB]"
          }`}>
          <Layout className="mr-1 inline h-3 w-3" /> Module Health ({data.module_health.length})
        </button>
      </div>

      {/* Score Breakdown Tab */}
      {selectedTab === "scores" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className={sectionClass + " p-4"}>
            <p className="text-xs font-semibold text-[#374151] mb-3">Maintainability Score Breakdown</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
              <ScoreGauge value={ms.overall_maintainability_score} label="Overall Score" />
              <ScoreGauge value={ms.maintainability_health} label="Health" />
              <ScoreGauge value={ms.technical_debt_score} label="Technical Debt" />
              <ScoreGauge value={ms.readability} label="Readability" />
              <ScoreGauge value={ms.modularity} label="Modularity" />
              <ScoreGauge value={ms.code_organization} label="Code Organization" />
              <ScoreGauge value={ms.refactoring_readiness} label="Refactoring Readiness" />
              <ScoreGauge value={ms.long_term_stability} label="Long-Term Stability" />
              <ScoreGauge value={ms.ai_confidence} label="AI Confidence" />
            </div>
          </div>

          <div className={sectionClass + " p-4"}>
            <p className="text-xs font-semibold text-[#374151] mb-3">Technical Debt Overview</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                <span className="text-[10px] font-medium text-[#374151]">Total Debt</span>
                <span className="text-[10px] font-semibold text-[#111827]">{td.total_debt_hours}h</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                <span className="text-[10px] font-medium text-[#374151]">Debt Level</span>
                <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${severityBadge[td.debt_level] || severityBadge.low}`}>{td.debt_level}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                <span className="text-[10px] font-medium text-[#374151]">Refactoring Effort</span>
                <span className="text-[10px] font-semibold text-[#111827]">{td.estimated_refactoring_effort}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                <span className="text-[10px] font-medium text-[#374151]">Est. Maintenance Cost</span>
                <span className="text-[10px] font-semibold text-[#111827]">{td.maintenance_cost}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                <span className="text-[10px] font-medium text-[#374151]">Stability</span>
                <span className={`text-[10px] font-semibold ${scoreColor(ms.long_term_stability)}`}>{Math.round(ms.long_term_stability)}/100</span>
              </div>
            </div>

            <p className="text-xs font-semibold text-[#374151] mt-4 mb-2">Debt Distribution</p>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#DC2626]" />
                <span className="text-[10px] text-[#374151]">Critical: {td.critical_file_count} files</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#D97706]" />
                <span className="text-[10px] text-[#374151]">High: {td.high_file_count} files</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#2563EB]" />
                <span className="text-[10px] text-[#374151]">Medium: {td.medium_file_count} files</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#059669]" />
                <span className="text-[10px] text-[#374151]">Low: {td.low_file_count} files</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Code Smells Tab */}
      {selectedTab === "smells" && (
        <div className="space-y-4">
          {/* Code Smell Categories */}
          <div className={sectionClass + " p-4"}>
            <p className="text-xs font-semibold text-[#374151] mb-3">Code Smell Analysis</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {SMELL_CATEGORIES.map((cat) => {
                const info = categorySmellCounts[cat.key];
                if (!info) return null;
                return (
                  <div key={cat.key} className="flex items-center gap-2 rounded-lg bg-[#FAFAFA] px-3 py-2">
                    <span className={`h-2 w-2 shrink-0 rounded-full ${
                      info.severity === "critical" ? "bg-[#DC2626]"
                      : info.severity === "high" ? "bg-[#D97706]"
                      : info.severity === "medium" ? "bg-[#2563EB]"
                      : "bg-[#059669]"
                    }`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-[9px] font-medium text-[#374151] truncate">{cat.label}</p>
                      <p className="text-[8px] text-[#6B7280]">{info.count} issue(s)</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Search + Filters */}
          <div className={sectionClass + " p-4"}>
            <div className="flex items-center gap-2 mb-3">
              <Code className="h-3.5 w-3.5 text-[#6B7280]" />
              <p className="text-xs font-semibold text-[#374151]">Code Smells ({filteredSmells.length})</p>
              <div className="ml-auto flex items-center gap-1.5">
                <span className="text-[8px] text-[#9CA3AF]">Sort:</span>
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="rounded border border-[#E5E7EB] px-1.5 py-1 text-[9px] font-medium text-[#374151] bg-white outline-none">
                  <option value="severity">Severity</option>
                  <option value="name">Name</option>
                  <option value="effort">Effort</option>
                </select>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 mb-3">
              <div className="flex items-center gap-1.5 flex-1 min-w-[200px] rounded-lg border border-[#E5E7EB] px-2.5 py-1.5">
                <Search className="h-3 w-3 text-[#9CA3AF]" />
                <input
                  type="text"
                  placeholder="Search by file, module, class, function..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 border-0 bg-transparent text-[10px] text-[#111827] placeholder-[#9CA3AF] outline-none"
                />
                {searchQuery && (
                  <button onClick={() => setSearchQuery("")} className="text-[#9CA3AF] hover:text-[#DC2626]">
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
              <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}
                className="rounded-lg border border-[#E5E7EB] px-2.5 py-1.5 text-[10px] font-medium text-[#374151] bg-white outline-none">
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
                className="rounded-lg border border-[#E5E7EB] px-2.5 py-1.5 text-[10px] font-medium text-[#374151] bg-white outline-none">
                <option value="all">All Types</option>
                {uniqueTypes.map((t) => (
                  <option key={t} value={t}>{typeLabels[t] || t}</option>
                ))}
              </select>
            </div>

            {filteredSmells.length > 0 ? (
              <div className="space-y-1 max-h-96 overflow-y-auto">
                {filteredSmells.map((smell, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedSmell(selectedSmell === smell ? null : smell)}
                    className={`w-full flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-colors ${
                      selectedSmell === smell
                        ? "border-[#059669] bg-[#ECFDF5]"
                        : "border-[#E5E7EB] hover:bg-[#FAFAFA]"
                    }`}
                  >
                    <div className="shrink-0">
                      {selectedSmell === smell ? (
                        <ChevronDown className="h-3 w-3 text-[#6B7280]" />
                      ) : (
                        <ChevronRight className="h-3 w-3 text-[#6B7280]" />
                      )}
                    </div>
                    <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${severityBadge[smell.severity] || severityBadge.low}`}>
                      {smell.severity}
                    </span>
                    <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] font-medium text-[#6B7280]">
                      {typeLabels[smell.type] || smell.type}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[10px] font-medium text-[#111827] truncate">{smell.name}</p>
                      {smell.affected_files.length > 0 && (
                        <p className="text-[8px] text-[#6B7280] truncate">
                          {smell.affected_files.slice(0, 2).join(", ")}
                          {smell.affected_files.length > 2 && ` +${smell.affected_files.length - 2} more`}
                        </p>
                      )}
                    </div>
                    <span className="shrink-0 text-[8px] text-[#6B7280]">{smell.refactoring_effort}</span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center py-8 text-xs text-[#9CA3AF]">
                <Wrench className="mb-2 h-6 w-6" />
                {searchQuery || severityFilter !== "all" || typeFilter !== "all"
                  ? "No smells match your search/filter criteria."
                  : "No code smells detected — project has excellent maintainability."}
              </div>
            )}

            {/* Detail Panel */}
            {selectedSmell && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="mt-3 rounded-lg border border-[#059669] bg-[#ECFDF5] p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${severityBadge[selectedSmell.severity] || severityBadge.low}`}>
                        {selectedSmell.severity}
                      </span>
                      <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] font-medium text-[#6B7280]">
                        {typeLabels[selectedSmell.type] || selectedSmell.type}
                      </span>
                    </div>
                    <p className="mt-1 text-xs font-semibold text-[#111827]">{selectedSmell.name}</p>
                  </div>
                  <button onClick={() => setSelectedSmell(null)} className="rounded p-1 text-[#6B7280] hover:text-[#DC2626] hover:bg-[#FEF2F2]">
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="space-y-2 text-[10px] text-[#374151]">
                  {selectedSmell.description && (
                    <div className="rounded-lg bg-white/60 p-2.5">
                      <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Description</p>
                      <p className="leading-relaxed">{selectedSmell.description}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {selectedSmell.affected_files.length > 0 && (
                      <div className="rounded-lg bg-white/60 p-2.5">
                        <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                          Affected Files ({selectedSmell.affected_files.length})
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {selectedSmell.affected_files.map((f) => (
                            <span key={f} className="rounded bg-white/80 px-2 py-1 text-[9px] font-mono text-[#059669]">{f}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {selectedSmell.affected_classes.length > 0 && (
                      <div className="rounded-lg bg-white/60 p-2.5">
                        <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                          Affected Classes ({selectedSmell.affected_classes.length})
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {selectedSmell.affected_classes.map((c) => (
                            <span key={c} className="rounded bg-white/80 px-2 py-1 text-[9px] font-mono text-[#6B7280]">{c}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {selectedSmell.affected_functions.length > 0 && (
                    <div className="rounded-lg bg-white/60 p-2.5">
                      <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                        Affected Functions ({selectedSmell.affected_functions.length})
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {selectedSmell.affected_functions.map((fn) => (
                          <span key={fn} className="rounded bg-white/80 px-2 py-1 text-[9px] font-mono text-[#6B7280]">{fn}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedSmell.refactoring_effort && (
                    <div className="rounded-lg bg-white/60 p-2.5">
                      <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Technical Debt</p>
                      <p className="text-[10px] leading-relaxed">Estimated Refactoring Effort: {selectedSmell.refactoring_effort}</p>
                    </div>
                  )}

                  {selectedSmell.ai_suggestion && (
                    <div className="rounded-lg bg-white border border-[#A7F3D0] p-2.5">
                      <p className="text-[8px] font-semibold uppercase tracking-wider text-[#059669] mb-0.5">AI Refactoring Suggestion</p>
                      <p className="text-[10px] text-[#065F46]">{selectedSmell.ai_suggestion}</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      )}

      {/* Technical Debt Tab */}
      {selectedTab === "debt" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className={sectionClass + " p-4"}>
            <div className="flex items-center gap-2 mb-3">
              <Hammer className="h-3.5 w-3.5 text-[#6B7280]" />
              <p className="text-xs font-semibold text-[#374151]">Technical Debt Details</p>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2.5">
                <span className="text-[10px] font-medium text-[#374151]">Estimated Technical Debt</span>
                <span className="text-[11px] font-bold text-[#111827]">{td.total_debt_hours}h</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2.5">
                <span className="text-[10px] font-medium text-[#374151]">Debt Level</span>
                <span className={`rounded px-2 py-0.5 text-[9px] font-semibold uppercase ${severityBadge[td.debt_level] || severityBadge.low}`}>{td.debt_level}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2.5">
                <span className="text-[10px] font-medium text-[#374151]">Estimated Refactoring Effort</span>
                <span className="text-[10px] font-semibold text-[#111827]">{td.estimated_refactoring_effort}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2.5">
                <span className="text-[10px] font-medium text-[#374151]">Maintenance Cost</span>
                <span className="text-[10px] font-semibold text-[#111827]">{td.maintenance_cost}</span>
              </div>
            </div>
          </div>

          <div className={sectionClass + " p-4"}>
            <div className="flex items-center gap-2 mb-3">
              <Shield className="h-3.5 w-3.5 text-[#6B7280]" />
              <p className="text-xs font-semibold text-[#374151]">Debt Severity & Distribution</p>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-lg bg-[#FEF2F2] px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#DC2626]" />
                  <span className="text-[10px] font-medium text-[#991B1B]">Critical</span>
                </div>
                <span className="text-[10px] font-semibold text-[#991B1B]">{td.critical_file_count} files</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#FFFBEB] px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#D97706]" />
                  <span className="text-[10px] font-medium text-[#92400E]">High</span>
                </div>
                <span className="text-[10px] font-semibold text-[#92400E]">{td.high_file_count} files</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#EFF6FF] px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#2563EB]" />
                  <span className="text-[10px] font-medium text-[#1E40AF]">Medium</span>
                </div>
                <span className="text-[10px] font-semibold text-[#1E40AF]">{td.medium_file_count} files</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[#ECFDF5] px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#059669]" />
                  <span className="text-[10px] font-medium text-[#065F46]">Low</span>
                </div>
                <span className="text-[10px] font-semibold text-[#065F46]">{td.low_file_count} files</span>
              </div>
            </div>

            <div className="mt-4 rounded-lg bg-[#FAFAFA] p-3">
              <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-2">Expected Maintainability Improvement</p>
              <p className="text-[10px] text-[#374151] leading-relaxed">
                Addressing all {td.critical_file_count + td.high_file_count + td.medium_file_count + td.low_file_count} files with debt could improve maintainability by up to {Math.min(100 - ms.overall_maintainability_score, 60).toFixed(0)}% and reduce future maintenance costs by an estimated ${(td.total_debt_hours * 50).toFixed(0)}.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Module Health Tab */}
      {selectedTab === "modules" && (
        <div className={sectionClass + " p-4"}>
          <div className="flex items-center gap-2 mb-3">
            <Layout className="h-3.5 w-3.5 text-[#6B7280]" />
            <p className="text-xs font-semibold text-[#374151]">Module Health — {data.module_health.length} module(s) analyzed</p>
          </div>
          {data.module_health.length > 0 ? (
            <div className="space-y-1.5 max-h-96 overflow-y-auto">
              {data.module_health.map((mod, idx) => (
                <div key={idx} className="flex items-center gap-3 rounded-lg border border-[#E5E7EB] px-3 py-2">
                  <MiniGauge value={mod.score} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[10px] font-medium text-[#111827] truncate">{mod.file_name}</p>
                    <div className="flex flex-wrap gap-1 mt-0.5">
                      {mod.issues.slice(0, 3).map((iss, i2) => (
                        <span key={i2} className="rounded bg-[#F3F4F6] px-1 py-0.5 text-[7px] font-medium text-[#6B7280]">{typeLabels[iss] || iss}</span>
                      ))}
                      {mod.issues.length > 3 && (
                        <span className="text-[7px] text-[#9CA3AF]">+{mod.issues.length - 3} more</span>
                      )}
                      {mod.issues.length === 0 && (
                        <span className="text-[7px] text-[#059669] font-medium">Clean</span>
                      )}
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-[8px] text-[#6B7280]">Debt: {mod.debt_estimate}</p>
                    <p className="text-[7px] text-[#9CA3AF]">Cpx: {Math.round(mod.complexity)} Coh: {Math.round(mod.cohesion)} Cop: {Math.round(mod.coupling)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center py-8 text-xs text-[#9CA3AF]">
              <Layout className="mb-2 h-6 w-6" />
              No module health data available.
            </div>
          )}
        </div>
      )}

      {/* AI Summary + Refactoring Opportunities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className={sectionClass + " p-4"}>
          <div className="flex items-center gap-1.5 mb-2">
            <Lightbulb className="h-3.5 w-3.5 text-[#D97706]" />
            <span className="text-xs font-semibold text-[#374151]">AI Maintainability Insights</span>
          </div>
          <p className="text-[10px] text-[#6B7280] leading-relaxed">{data.summary.summary_text}</p>
        </div>

        <div className={sectionClass + " p-4"}>
          <div className="flex items-center gap-1.5 mb-2">
            <BookOpen className="h-3.5 w-3.5 text-[#2563EB]" />
            <span className="text-xs font-semibold text-[#374151]">Prioritized Refactoring Opportunities</span>
          </div>
          {data.summary.prioritized_recommendations.length > 0 ? (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {data.summary.prioritized_recommendations.slice(0, 12).map((rec, idx) => (
                <div key={idx} className="flex items-start gap-2 rounded-lg bg-[#FAFAFA] px-2.5 py-2">
                  <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                    rec.startsWith("[CRITICAL]") ? "bg-[#DC2626]"
                    : rec.startsWith("[HIGH]") ? "bg-[#D97706]"
                    : "bg-[#2563EB]"
                  }`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[9px] text-[#374151] leading-relaxed">{rec}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[10px] text-[#9CA3AF]">No refactoring opportunities identified.</p>
          )}
        </div>
      </div>

      {projectId && (
        <RelatedAnalysisNav projectId={projectId} currentPage="maintainability-intelligence" />
      )}
    </motion.div>
  );
}

export default MaintainabilityIntelligence;
