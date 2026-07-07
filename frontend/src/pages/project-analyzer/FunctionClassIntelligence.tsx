import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpDown,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Code2,
  FileSearch,
  Filter,
  FlaskConical,
  FunctionSquare,
  GitBranch,
  RefreshCw,
  Search,
  Shield,
  X,
} from "lucide-react";
import { getFunctionClassIntelligence } from "@/lib/project-analyzer";
import type {
  FuncClassIntelligenceClass,
  FuncClassIntelligenceFunc,
  FuncClassIntelligenceResponse,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityBadge: Record<string, string> = {
  high: "bg-[#FEF2F2] text-[#991B1B]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
};

const healthColors: Record<string, string> = {
  Excellent: "bg-[#ECFDF5] text-[#065F46]",
  Good: "bg-[#EFF6FF] text-[#1E40AF]",
  Fair: "bg-[#FFFBEB] text-[#92400E]",
  "Needs Improvement": "bg-[#FEF3C7] text-[#92400E]",
  Poor: "bg-[#FEF2F2] text-[#991B1B]",
};

function truncatePath(path: string, maxLen = 50) {
  if (path.length <= maxLen) return path;
  const start = path.lastIndexOf("/", maxLen);
  return "..." + path.slice(start);
}

export function FunctionClassIntelligence() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<FuncClassIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [langFilter, setLangFilter] = useState<string>("");
  const [healthFilter, setHealthFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("name");
  const [sortAsc, setSortAsc] = useState(true);
  const [activeTab, setActiveTab] = useState<"functions" | "classes">("functions");
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getFunctionClassIntelligence(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load function & class intelligence",
      );
    } finally {
      setLoading(false);
      fetchedRef.current = true;
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const languages = useMemo(() => {
    if (!data) return [];
    const all = new Set<string>();
    if (activeTab === "functions") {
      for (const f of data.functions) all.add(f.language);
    } else {
      for (const c of data.classes) all.add(c.language);
    }
    return Array.from(all).sort();
  }, [data, activeTab]);

  const filteredFunctions = useMemo(() => {
    if (!data) return [];
    let items = [...data.functions];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (f) =>
          f.name.toLowerCase().includes(q) ||
          f.file_path.toLowerCase().includes(q) ||
          f.language.toLowerCase().includes(q) ||
          f.health_status.toLowerCase().includes(q),
      );
    }
    if (langFilter) items = items.filter((f) => f.language === langFilter);
    if (healthFilter === "excellent")
      items = items.filter((f) => f.health_status === "Excellent");
    else if (healthFilter === "good")
      items = items.filter((f) => f.health_status === "Good");
    else if (healthFilter === "fair")
      items = items.filter((f) => f.health_status === "Fair" || f.health_status === "Needs Improvement");
    else if (healthFilter === "poor")
      items = items.filter((f) => f.health_status === "Poor");
    items.sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "complexity":
          cmp = a.cyclomatic_complexity - b.cyclomatic_complexity;
          break;
        case "maintainability":
          cmp = a.maintainability_score - b.maintainability_score;
          break;
        case "issues":
          cmp = a.issue_count - b.issue_count;
          break;
        case "lines":
          cmp = a.lines_of_code - b.lines_of_code;
          break;
        default:
          cmp = a.name.localeCompare(b.name);
      }
      return sortAsc ? cmp : -cmp;
    });
    return items;
  }, [data, search, langFilter, healthFilter, sortBy, sortAsc]);

  const filteredClasses = useMemo(() => {
    if (!data) return [];
    let items = [...data.classes];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.file_path.toLowerCase().includes(q) ||
          c.language.toLowerCase().includes(q) ||
          c.health_status.toLowerCase().includes(q),
      );
    }
    if (langFilter) items = items.filter((c) => c.language === langFilter);
    if (healthFilter === "excellent")
      items = items.filter((c) => c.health_status === "Excellent");
    else if (healthFilter === "good")
      items = items.filter((c) => c.health_status === "Good");
    else if (healthFilter === "fair")
      items = items.filter((c) => c.health_status === "Fair" || c.health_status === "Needs Improvement");
    else if (healthFilter === "poor")
      items = items.filter((c) => c.health_status === "Poor");
    items.sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "complexity":
          cmp = a.complexity - b.complexity;
          break;
        case "maintainability":
          cmp = a.maintainability_score - b.maintainability_score;
          break;
        case "issues":
          cmp = a.issue_count - b.issue_count;
          break;
        case "lines":
          cmp = a.lines_of_code - b.lines_of_code;
          break;
        default:
          cmp = a.name.localeCompare(b.name);
      }
      return sortAsc ? cmp : -cmp;
    });
    return items;
  }, [data, search, langFilter, healthFilter, sortBy, sortAsc]);

  const toggleItem = (key: string) => {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">
          Analyzing functions & classes...
        </p>
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
        <FunctionSquare className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No function/class data</p>
        <p className="mt-1 text-xs text-[#6B7280]">
          Run project analysis to generate function & class intelligence.
        </p>
      </div>
    );
  }

  const s = data.stats;

  const renderFunctionRow = (func: FuncClassIntelligenceFunc) => {
    const key = `func:${func.file_path}:${func.name}`;
    const isExpanded = expandedItems.has(key);
    return (
      <div key={key} className="border-b border-[#F3F4F6] last:border-b-0">
        <button
          onClick={() => toggleItem(key)}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-[#F9FAFB] text-xs"
        >
          <FunctionSquare className="h-3.5 w-3.5 shrink-0 text-[#6B7280]" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-medium text-[#111827]">{func.name}</span>
              <span
                className={`rounded px-1.5 py-0.5 text-[9px] ${
                  healthColors[func.health_status] || "bg-[#F3F4F6] text-[#374151]"
                }`}
              >
                {func.health_status}
              </span>
              <span className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[9px] text-[#1E40AF]">
                {func.language}
              </span>
              {func.is_recursive && (
                <span className="rounded bg-[#FEF2F2] px-1.5 py-0.5 text-[9px] text-[#DC2626]">
                  Recursive
                </span>
              )}
              {func.is_unused && (
                <span className="rounded bg-[#FFFBEB] px-1.5 py-0.5 text-[9px] text-[#92400E]">
                  Unused
                </span>
              )}
              {func.issue_count > 0 && (
                <span className="rounded bg-[#FEF2F2] px-1.5 py-0.5 text-[9px] text-[#DC2626]">
                  {func.issue_count} issue{func.issue_count > 1 ? "s" : ""}
                </span>
              )}
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[9px] text-[#9CA3AF]">
              <span className="truncate max-w-[200px]">{truncatePath(func.file_path)}</span>
              <span>·</span>
              <span>{func.lines_of_code} lines</span>
              <span>·</span>
              <span>Complexity: {func.cyclomatic_complexity}</span>
              <span>·</span>
              <span>Score: {func.maintainability_score}%</span>
            </div>
          </div>
          {isExpanded ? (
            <ChevronDown className="h-3 w-3 shrink-0 text-[#9CA3AF]" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 text-[#9CA3AF]" />
          )}
        </button>
        {isExpanded && (
          <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-4 py-3 pl-10">
            {func.ai_insight && (
              <div className="mb-3 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[10px] leading-relaxed text-[#374151]">
                <span className="font-medium text-[#6B7280]">AI Insight:</span> {func.ai_insight}
              </div>
            )}
            <div className="mb-2 grid grid-cols-2 gap-x-4 gap-y-0.5 text-[10px] text-[#374151]">
              <span>File: <strong className="break-all">{func.file_path}</strong></span>
              <span>Lines: <strong>{func.start_line}–{func.end_line}</strong></span>
              <span>Complexity: <strong>{func.cyclomatic_complexity}</strong></span>
              <span>Nesting: <strong>{func.deepest_nesting}</strong></span>
              <span>Parameters: <strong>{func.parameters.length}</strong></span>
              <span>Return: <strong>{func.return_type || "None"}</strong></span>
              <span>Type Hints: <strong>{func.has_type_hints ? "Yes" : "No"}</strong></span>
              <span>Docs: <strong>{func.has_documentation ? "Yes" : "No"}</strong></span>
            </div>
            {func.parameters.length > 0 && (
              <div className="mb-2">
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Parameters</p>
                <div className="flex flex-wrap gap-1">
                  {func.parameters.map((p, idx) => (
                    <span key={idx} className="rounded bg-white border border-[#E5E7EB] px-1.5 py-0.5 text-[9px] text-[#374151]">
                      {p.name}{p.type ? `: ${p.type}` : ""}{p.is_optional ? "?" : ""}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {func.callers.length > 0 && (
              <div className="mb-2">
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Callers</p>
                <div className="flex flex-wrap gap-1">
                  {func.callers.slice(0, 5).map((c, idx) => (
                    <span key={idx} className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[9px] text-[#1E40AF]">{c}</span>
                  ))}
                  {func.callers.length > 5 && (
                    <span className="text-[9px] text-[#9CA3AF]">+{func.callers.length - 5} more</span>
                  )}
                </div>
              </div>
            )}
            {func.issues.length > 0 && (
              <div className="space-y-1">
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Issues</p>
                {func.issues.map((issue, idx) => (
                  <div key={idx} className="flex items-start gap-2 rounded bg-white border border-[#E5E7EB] px-2 py-1.5">
                    <span className={`rounded px-1 py-0.5 text-[8px] font-medium uppercase ${severityBadge[issue.severity] || severityBadge.low}`}>
                      {issue.severity}
                    </span>
                    <div className="min-w-0">
                      <p className="text-[9px] font-medium text-[#111827]">{issue.description}</p>
                      {issue.suggested_fix && (
                        <p className="mt-0.5 text-[8px] text-[#059669]">Fix: {issue.suggested_fix}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderClassRow = (cls: FuncClassIntelligenceClass) => {
    const key = `class:${cls.file_path}:${cls.name}`;
    const isExpanded = expandedItems.has(key);
    return (
      <div key={key} className="border-b border-[#F3F4F6] last:border-b-0">
        <button
          onClick={() => toggleItem(key)}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-[#F9FAFB] text-xs"
        >
          <Code2 className="h-3.5 w-3.5 shrink-0 text-[#6B7280]" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-medium text-[#111827]">{cls.name}</span>
              <span className={`rounded px-1.5 py-0.5 text-[9px] ${healthColors[cls.health_status] || "bg-[#F3F4F6] text-[#374151]"}`}>
                {cls.health_status}
              </span>
              <span className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[9px] text-[#1E40AF]">{cls.language}</span>
              {cls.is_abstract && (
                <span className="rounded bg-[#F5F3FF] px-1.5 py-0.5 text-[9px] text-[#5B21B6]">Abstract</span>
              )}
              {cls.has_nested_classes && (
                <span className="rounded bg-[#FFE4E6] px-1.5 py-0.5 text-[9px] text-[#9F1239]">Nested</span>
              )}
              {cls.issue_count > 0 && (
                <span className="rounded bg-[#FEF2F2] px-1.5 py-0.5 text-[9px] text-[#DC2626]">
                  {cls.issue_count} issue{cls.issue_count > 1 ? "s" : ""}
                </span>
              )}
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[9px] text-[#9CA3AF]">
              <span className="truncate max-w-[200px]">{truncatePath(cls.file_path)}</span>
              <span>·</span>
              <span>{cls.lines_of_code} lines</span>
              <span>·</span>
              <span>{cls.method_count} methods</span>
              <span>·</span>
              <span>Score: {cls.maintainability_score}%</span>
            </div>
          </div>
          {isExpanded ? (
            <ChevronDown className="h-3 w-3 shrink-0 text-[#9CA3AF]" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 text-[#9CA3AF]" />
          )}
        </button>
        {isExpanded && (
          <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-4 py-3 pl-10">
            {cls.ai_insight && (
              <div className="mb-3 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[10px] leading-relaxed text-[#374151]">
                <span className="font-medium text-[#6B7280]">AI Insight:</span> {cls.ai_insight}
              </div>
            )}
            <div className="mb-2 grid grid-cols-2 gap-x-4 gap-y-0.5 text-[10px] text-[#374151]">
              <span>File: <strong className="break-all">{cls.file_path}</strong></span>
              <span>Lines: <strong>{cls.lines_of_code}</strong></span>
              <span>Complexity: <strong>{cls.complexity}</strong></span>
              <span>Methods: <strong>{cls.method_count}</strong></span>
              <span>Properties: <strong>{cls.property_count}</strong></span>
              <span>Coupling: <strong>{cls.coupling}</strong></span>
              <span>Abstract: <strong>{cls.is_abstract ? "Yes" : "No"}</strong></span>
              <span>Docs: <strong>{cls.has_documentation ? "Yes" : "No"}</strong></span>
            </div>
            {cls.base_classes.length > 0 && (
              <div className="mb-2">
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Base Classes</p>
                <div className="flex flex-wrap gap-1">
                  {cls.base_classes.map((b, idx) => (
                    <span key={idx} className="rounded bg-[#F5F3FF] border border-[#E5E7EB] px-1.5 py-0.5 text-[9px] text-[#5B21B6]">{b}</span>
                  ))}
                </div>
              </div>
            )}
            {cls.properties.length > 0 && (
              <div className="mb-2">
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Properties</p>
                <div className="flex flex-wrap gap-1">
                  {cls.properties.map((p, idx) => (
                    <span key={idx} className="rounded bg-white border border-[#E5E7EB] px-1.5 py-0.5 text-[9px] text-[#374151]">{p}</span>
                  ))}
                </div>
              </div>
            )}
            {cls.methods.length > 0 && (
              <div className="mb-2">
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                  Methods ({cls.methods.length})
                </p>
                <div className="space-y-1">
                  {cls.methods.slice(0, 10).map((m, idx) => (
                    <div key={idx} className="flex items-center gap-2 rounded bg-white border border-[#E5E7EB] px-2 py-1.5">
                      <span className={`rounded px-1 py-0.5 text-[8px] font-medium ${healthColors[m.health_status] || "bg-[#F3F4F6] text-[#374151]"}`}>
                        {m.health_status}
                      </span>
                      <span className="text-[9px] font-medium text-[#111827]">{m.name}</span>
                      <span className="text-[8px] text-[#6B7280]">({m.lines_of_code} lines, C:{m.cyclomatic_complexity})</span>
                      {m.is_static && <span className="text-[8px] text-[#5B21B6]">static</span>}
                      {m.is_property && <span className="text-[8px] text-[#059669]">property</span>}
                      {m.is_classmethod && <span className="text-[8px] text-[#92400E]">classmethod</span>}
                    </div>
                  ))}
                  {cls.methods.length > 10 && (
                    <p className="text-[9px] text-[#9CA3AF]">+{cls.methods.length - 10} more methods</p>
                  )}
                </div>
              </div>
            )}
            {cls.issues.length > 0 && (
              <div className="space-y-1">
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Issues</p>
                {cls.issues.map((issue, idx) => (
                  <div key={idx} className="flex items-start gap-2 rounded bg-white border border-[#E5E7EB] px-2 py-1.5">
                    <span className={`rounded px-1 py-0.5 text-[8px] font-medium uppercase ${severityBadge[issue.severity] || severityBadge.low}`}>
                      {issue.severity}
                    </span>
                    <div className="min-w-0">
                      <p className="text-[9px] font-medium text-[#111827]">{issue.description}</p>
                      {issue.suggested_fix && (
                        <p className="mt-0.5 text-[8px] text-[#059669]">Fix: {issue.suggested_fix}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const currentItems = activeTab === "functions" ? filteredFunctions : filteredClasses;
  const totalItems = activeTab === "functions" ? data.functions.length : data.classes.length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-5"
    >
      {projectId && (
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(`/projects/${projectId}/analyzer`)}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]"
          >
            ← Back to Overview
          </button>
          <span className="text-[#D1D5DB]">|</span>
          <button
            onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]"
          >
            Back to Unified Dashboard
          </button>
        </div>
      )}
      {/* Hero */}
      <div className="overflow-hidden rounded-xl bg-gradient-to-br from-[#7C3AED] to-[#2563EB]">
        <div className="px-6 py-8 text-white">
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
            <FunctionSquare className="h-3.5 w-3.5" /> Function & Class Intelligence Engine
          </div>
          <p className="mt-1 text-2xl font-bold">Function & Class Intelligence</p>
          <p className="mt-1 text-sm text-white/80">
            Deep analysis of every function and class including complexity, health scores, relationships, and AI insights.
          </p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {[
          { label: "Total Functions", value: s.total_functions, icon: FunctionSquare, color: "text-[#2563EB]" },
          { label: "Total Classes", value: s.total_classes, icon: Code2, color: "text-[#059669]" },
          { label: "Total Methods", value: s.total_methods, icon: GitBranch, color: "text-[#7C3AED]" },
          { label: "Total Issues", value: s.total_issues, icon: AlertTriangle, color: "text-[#DC2626]" },
          { label: "Avg Complexity", value: s.average_complexity.toFixed(1), icon: FlaskConical, color: "text-[#D97706]" },
          { label: "Unused", value: s.unused_functions, icon: FileSearch, color: "text-[#6B7280]" },
          { label: "Undocumented", value: s.undocumented_count, icon: Shield, color: "text-[#6B7280]" },
        ].map((stat) => (
          <div
            key={stat.label}
            className={sectionClass + " flex items-center gap-3 px-4 py-3"}
          >
            <stat.icon className={`h-5 w-5 shrink-0 ${stat.color}`} />
            <div>
              <p className="text-lg font-bold text-[#111827]">{stat.value}</p>
              <p className="text-[10px] text-[#6B7280]">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Search & Filters */}
      <div className={sectionClass}>
        <div className="flex items-center gap-2 px-4 py-2.5">
          <Search className="h-3.5 w-3.5 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder={"Search " + (activeTab === "functions" ? "functions" : "classes") + " by name, path, language, or health..."}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 border-0 bg-transparent text-xs text-[#111827] placeholder-[#9CA3AF] outline-none"
          />
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium transition-colors ${
              showFilters || langFilter || healthFilter || sortBy !== "name"
                ? "bg-[#EFF6FF] text-[#1E40AF]"
                : "text-[#6B7280] hover:bg-[#F3F4F6]"
            }`}
          >
            <Filter className="h-3 w-3" />
            Filters
          </button>
          {(langFilter || healthFilter || search) && (
            <button
              onClick={() => {
                setSearch("");
                setLangFilter("");
                setHealthFilter("");
                setSortBy("name");
                setSortAsc(true);
              }}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium text-[#DC2626] hover:bg-[#FEF2F2]"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          )}
        </div>
        {showFilters && (
          <div className="border-t border-[#F3F4F6] px-4 py-2.5">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-medium text-[#6B7280]">Language:</span>
                <select
                  value={langFilter}
                  onChange={(e) => setLangFilter(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="">All</option>
                  {languages.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-medium text-[#6B7280]">Health:</span>
                <select
                  value={healthFilter}
                  onChange={(e) => setHealthFilter(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="">All</option>
                  <option value="excellent">Excellent</option>
                  <option value="good">Good</option>
                  <option value="fair">Fair</option>
                  <option value="poor">Poor</option>
                </select>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-medium text-[#6B7280]">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="name">Name</option>
                  <option value="complexity">Complexity</option>
                  <option value="maintainability">Maintainability</option>
                  <option value="issues">Issue Count</option>
                  <option value="lines">Lines of Code</option>
                </select>
                <button
                  onClick={() => setSortAsc(!sortAsc)}
                  className="rounded border border-[#E5E7EB] bg-white p-1 hover:bg-[#F3F4F6]"
                  title={sortAsc ? "Ascending" : "Descending"}
                >
                  <ArrowUpDown className="h-3 w-3 text-[#6B7280]" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className={sectionClass}>
        <div className="flex border-b border-[#F3F4F6]">
          <button
            onClick={() => {
              setActiveTab("functions");
              setExpandedItems(new Set());
            }}
            className={`flex-1 px-4 py-2.5 text-xs font-medium transition-colors ${
              activeTab === "functions"
                ? "border-b-2 border-[#2563EB] text-[#2563EB]"
                : "text-[#6B7280] hover:text-[#111827]"
            }`}
          >
            Functions ({data.functions.length})
          </button>
          <button
            onClick={() => {
              setActiveTab("classes");
              setExpandedItems(new Set());
            }}
            className={`flex-1 px-4 py-2.5 text-xs font-medium transition-colors ${
              activeTab === "classes"
                ? "border-b-2 border-[#2563EB] text-[#2563EB]"
                : "text-[#6B7280] hover:text-[#111827]"
            }`}
          >
            Classes ({data.classes.length})
          </button>
        </div>
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#F3F4F6]">
          <p className="text-xs font-semibold text-[#111827]">
            {currentItems.length} {activeTab === "functions" ? "function" : "class"}
            {currentItems.length !== 1 ? "s" : ""}
            {currentItems.length !== totalItems && ` (filtered from ${totalItems})`}
          </p>
          <div className="flex items-center gap-2 text-[10px] text-[#6B7280]">
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#ECFDF5]" /> Excellent</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#EFF6FF]" /> Good</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#FFFBEB]" /> Fair</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#FEF2F2]" /> Poor</span>
          </div>
        </div>
        <div className="divide-y divide-[#F3F4F6] max-h-[600px] overflow-y-auto">
          {currentItems.length > 0 ? (
            activeTab === "functions"
              ? filteredFunctions.map(renderFunctionRow)
              : filteredClasses.map(renderClassRow)
          ) : (
            <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
              <FileSearch className="mb-2 h-6 w-6" />
              No {activeTab === "functions" ? "functions" : "classes"} match the current filters.
            </div>
          )}
        </div>
      </div>

      {/* AI Insights */}
      {data.ai_insights.length > 0 && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            AI Insights
          </p>
          <div className="space-y-2">
            {data.ai_insights.map((insight, idx) => (
              <div key={idx} className="flex gap-3 rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[#EFF6FF]">
                  <BarChart3 className="h-3.5 w-3.5 text-[#2563EB]" />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] text-[#6B7280] leading-relaxed">{insight}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relationships */}
      {data.relationships.length > 0 && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Relationships ({data.relationships.length})
          </p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {data.relationships.slice(0, 30).map((rel, idx) => (
              <div key={idx} className="flex items-center gap-2 rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-3 py-2">
                <span className={`rounded px-1 py-0.5 text-[8px] font-medium uppercase ${
                  rel.strength === "strong"
                    ? "bg-[#ECFDF5] text-[#065F46]"
                    : rel.strength === "medium"
                    ? "bg-[#FFFBEB] text-[#92400E]"
                    : "bg-[#F3F4F6] text-[#374151]"
                }`}>
                  {rel.strength}
                </span>
                <span className="text-[9px] text-[#111827] font-medium">{rel.source}</span>
                <span className="text-[8px] text-[#9CA3AF]">{rel.type}</span>
                <span className="text-[9px] text-[#111827] font-medium">{rel.target}</span>
              </div>
            ))}
            {data.relationships.length > 30 && (
              <p className="text-[10px] text-[#9CA3AF]">+{data.relationships.length - 30} more relationships</p>
            )}
          </div>
        </div>
      )}

      {/* Related */}
      {projectId && (
        <RelatedAnalysisNav projectId={projectId} currentPage="function-class-intelligence" />
      )}
    </motion.div>
  );
}
