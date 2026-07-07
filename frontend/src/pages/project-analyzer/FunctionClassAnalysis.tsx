import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpDown,
  BookOpen,
  Box,
  ChevronDown,
  ChevronRight,
  Filter,
  FlaskConical,
  FunctionSquare,
  Layers,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { getFunctionClassAnalysis } from "@/lib/project-analyzer";
import type { ClassDetail, FunctionDetail, FunctionClassResponse } from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const healthBadge: Record<string, string> = {
  Excellent: "bg-[#ECFDF5] text-[#065F46]",
  Good: "bg-[#EFF6FF] text-[#1E40AF]",
  Fair: "bg-[#FFFBEB] text-[#92400E]",
  "Needs Improvement": "bg-[#FFF7ED] text-[#9A3412]",
  Poor: "bg-[#FEF2F2] text-[#991B1B]",
};

const sortOptions = [
  { value: "name", label: "Name" },
  { value: "complexity", label: "Complexity" },
  { value: "maintainability", label: "Maintainability" },
  { value: "issues", label: "Issue Count" },
  { value: "loc", label: "Lines of Code" },
] as const;

type TabType = "functions" | "classes" | "insights";

export function FunctionClassAnalysis() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<FunctionClassResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabType>("functions");
  const [search, setSearch] = useState("");
  const [langFilter, setLangFilter] = useState<string>("");
  const [healthFilter, setHealthFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("name");
  const [sortAsc, setSortAsc] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [expandedFunc, setExpandedFunc] = useState<Set<string>>(new Set());
  const [expandedClass, setExpandedClass] = useState<Set<string>>(new Set());
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getFunctionClassAnalysis(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load function & class analysis");
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
    const l = new Set<string>();
    data.functions.forEach((f) => l.add(f.language));
    data.classes.forEach((c) => l.add(c.language));
    return Array.from(l).sort();
  }, [data]);

  const filteredFunctions = useMemo(() => {
    if (!data) return [];
    let items = [...data.functions];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (f) =>
          f.name.toLowerCase().includes(q) ||
          f.file_path.toLowerCase().includes(q) ||
          f.module.toLowerCase().includes(q),
      );
    }
    if (langFilter) items = items.filter((f) => f.language === langFilter);
    if (healthFilter) items = items.filter((f) => f.health_status === healthFilter);
    items.sort((a, b) => {
      let cmp = 0;
      if (sortBy === "name") cmp = a.name.localeCompare(b.name);
      else if (sortBy === "complexity") cmp = a.cyclomatic_complexity - b.cyclomatic_complexity;
      else if (sortBy === "maintainability") cmp = a.maintainability_score - b.maintainability_score;
      else if (sortBy === "issues") cmp = a.issue_count - b.issue_count;
      else if (sortBy === "loc") cmp = a.lines_of_code - b.lines_of_code;
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
          c.module.toLowerCase().includes(q),
      );
    }
    if (langFilter) items = items.filter((c) => c.language === langFilter);
    if (healthFilter) items = items.filter((c) => c.health_status === healthFilter);
    items.sort((a, b) => {
      let cmp = 0;
      if (sortBy === "name") cmp = a.name.localeCompare(b.name);
      else if (sortBy === "complexity") cmp = a.complexity - b.complexity;
      else if (sortBy === "maintainability") cmp = a.maintainability_score - b.maintainability_score;
      else if (sortBy === "issues") cmp = a.issue_count - b.issue_count;
      else if (sortBy === "loc") cmp = a.lines_of_code - b.lines_of_code;
      return sortAsc ? cmp : -cmp;
    });
    return items;
  }, [data, search, langFilter, healthFilter, sortBy, sortAsc]);

  const toggleFunc = (name: string) => {
    setExpandedFunc((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const toggleClass = (name: string) => {
    setExpandedClass((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Analyzing functions and classes...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Error</p>
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
        <FunctionSquare className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No analysis data available</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run a project analysis first.</p>
      </div>
    );
  }

  const s = data.stats;

  const renderParamChip = (p: { name: string; type: string | null }) => (
    <span key={p.name} className="inline-flex items-center gap-1 rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#6B7280]">
      {p.name}{p.type ? <span className="text-[#9CA3AF]">: {p.type}</span> : null}
    </span>
  );

  const renderFunctionRow = (func: FunctionDetail) => {
    const isExpanded = expandedFunc.has(func.name + func.file_path);
    return (
      <div key={func.name + func.file_path}>
        <button onClick={() => toggleFunc(func.name + func.file_path)}
          className="w-full flex items-center gap-3 px-5 py-2.5 text-left hover:bg-[#F9FAFB]">
          <FunctionSquare className="h-3.5 w-3.5 text-[#2563EB]" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-[#111827]">{func.name}</span>
              <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${healthBadge[func.health_status] || "bg-[#F3F4F6] text-[#374151]"}`}>{func.health_status}</span>
              {func.is_async && <span className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[9px] text-[#1E40AF]">async</span>}
              {func.is_generator && <span className="rounded bg-[#FEF3C7] px-1.5 py-0.5 text-[9px] text-[#92400E]">generator</span>}
              {func.is_lambda && <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#374151]">lambda</span>}
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[9px] text-[#6B7280]">
              <span>{func.file_path}</span>
              {func.module && <span>· {func.module}</span>}
              <span>· {func.lines_of_code} LOC</span>
              <span>· CC {func.cyclomatic_complexity}</span>
              <span>· {func.issue_count} issue(s)</span>
            </div>
          </div>
          <button onClick={(e) => { e.stopPropagation(); navigate(`/projects/${projectId}/analyzer/function-class/${encodeURIComponent(func.file_path)}/${encodeURIComponent(func.name)}`); }}
            className="mr-1 rounded px-2 py-1 text-[9px] font-medium text-[#2563EB] hover:bg-[#EFF6FF]">
            Detail
          </button>
          {isExpanded ? <ChevronDown className="h-3.5 w-3.5 text-[#9CA3AF]" /> : <ChevronRight className="h-3.5 w-3.5 text-[#9CA3AF]" />}
        </button>
        {isExpanded && (
          <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-5 py-3 pl-10">
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-[#374151]">
              <span>Visibility: <strong>{func.visibility}</strong></span>
              <span>Parameters: <strong>{func.parameters.length}</strong></span>
              <span>Return: <strong>{func.return_type || "—"}</strong></span>
              <span>Docs: <strong>{func.has_documentation ? "Yes" : "No"}</strong></span>
              <span>Complexity: <strong>{func.cyclomatic_complexity}</strong></span>
              <span>Maintainability: <strong>{func.maintainability_score.toFixed(0)}/100</strong></span>
            </div>
            {func.parameters.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">{func.parameters.map(renderParamChip)}</div>
            )}
            {func.decorators.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {func.decorators.map((d) => (
                  <span key={d} className="rounded bg-[#EDE9FE] px-1.5 py-0.5 text-[9px] text-[#6D28D9]">@{d}</span>
                ))}
              </div>
            )}
            {func.ai_insight && (
              <p className="mt-2 text-[10px] italic text-[#6B7280]">AI: {func.ai_insight}</p>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderClassRow = (cls: ClassDetail) => {
    const isExpanded = expandedClass.has(cls.name + cls.file_path);
    return (
      <div key={cls.name + cls.file_path}>
        <button onClick={() => toggleClass(cls.name + cls.file_path)}
          className="w-full flex items-center gap-3 px-5 py-2.5 text-left hover:bg-[#F9FAFB]">
          <Box className="h-3.5 w-3.5 text-[#7C3AED]" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-[#111827]">{cls.name}</span>
              <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${healthBadge[cls.health_status] || "bg-[#F3F4F6] text-[#374151]"}`}>{cls.health_status}</span>
              {cls.is_abstract && <span className="rounded bg-[#FEF3C7] px-1.5 py-0.5 text-[9px] text-[#92400E]">abstract</span>}
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[9px] text-[#6B7280]">
              <span>{cls.file_path}</span>
              <span>· {cls.lines_of_code} LOC</span>
              <span>· {cls.methods.length} methods</span>
              <span>· {cls.issue_count} issue(s)</span>
            </div>
          </div>
          <button onClick={(e) => { e.stopPropagation(); navigate(`/projects/${projectId}/analyzer/function-class/${encodeURIComponent(cls.file_path)}/${encodeURIComponent(cls.name)}`); }}
            className="mr-1 rounded px-2 py-1 text-[9px] font-medium text-[#7C3AED] hover:bg-[#F3E8FF]">
            Detail
          </button>
          {isExpanded ? <ChevronDown className="h-3.5 w-3.5 text-[#9CA3AF]" /> : <ChevronRight className="h-3.5 w-3.5 text-[#9CA3AF]" />}
        </button>
        {isExpanded && (
          <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-5 py-3 pl-10">
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-[#374151]">
              <span>Base classes: <strong>{cls.base_classes.length > 0 ? cls.base_classes.join(", ") : "—"}</strong></span>
              <span>Methods: <strong>{cls.methods.length}</strong></span>
              <span>Properties: <strong>{cls.properties.length}</strong></span>
              <span>Constructors: <strong>{cls.constructors.length}</strong></span>
              <span>Complexity: <strong>{cls.complexity}</strong></span>
              <span>Maintainability: <strong>{cls.maintainability_score.toFixed(0)}/100</strong></span>
            </div>
            {cls.interfaces.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {cls.interfaces.map((iface) => (
                  <span key={iface} className="rounded bg-[#F3E8FF] px-1.5 py-0.5 text-[9px] text-[#6D28D9]">{iface}</span>
                ))}
              </div>
            )}
            {cls.ai_insight && (
              <p className="mt-2 text-[10px] italic text-[#6B7280]">AI: {cls.ai_insight}</p>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">

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
      <div className="overflow-hidden rounded-xl bg-gradient-to-br from-[#1E40AF] to-[#7C3AED]">
        <div className="px-6 py-8 text-white">
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
            <FunctionSquare className="h-3.5 w-3.5" /> Function & Class Intelligence
          </div>
          <p className="mt-1 text-2xl font-bold">Code Structure Analysis</p>
          <p className="mt-1 text-sm text-white/80">Comprehensive analysis of all functions, methods, and classes across your project.</p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {[
          { label: "Functions", value: s.total_functions, icon: FunctionSquare, color: "text-[#2563EB]" },
          { label: "Classes", value: s.total_classes, icon: Box, color: "text-[#7C3AED]" },
          { label: "Methods", value: s.total_methods, icon: Layers, color: "text-[#059669]" },
          { label: "Avg Complexity", value: s.average_complexity.toFixed(1), icon: FlaskConical, color: "text-[#D97706]" },
          { label: "Avg Maintainability", value: `${s.average_maintainability.toFixed(0)}%`, icon: RefreshCw, color: "text-[#059669]" },
          { label: "Total Issues", value: s.total_issues, icon: AlertTriangle, color: "text-[#DC2626]" },
          { label: "Undocumented", value: s.undocumented_count, icon: BookOpen, color: "text-[#6B7280]" },
        ].map((stat) => (
          <div key={stat.label} className={sectionClass + " flex items-center gap-3 px-4 py-3"}>
            <stat.icon className={`h-5 w-5 shrink-0 ${stat.color}`} />
            <div>
              <p className="text-lg font-bold text-[#111827]">{stat.value}</p>
              <p className="text-[10px] text-[#6B7280]">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-0.5 rounded-lg bg-[#F3F4F6] p-0.5">
        {[
          { key: "functions" as TabType, label: `Functions (${s.total_functions})`, icon: FunctionSquare },
          { key: "classes" as TabType, label: `Classes (${s.total_classes})`, icon: Box },
          { key: "insights" as TabType, label: `AI Insights (${data.ai_insights.length})`, icon: FlaskConical },
        ].map((t) => (
          <button key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              tab === t.key ? "bg-white text-[#111827] shadow-sm" : "text-[#6B7280] hover:text-[#111827]"
            }`}>
            <t.icon className="h-3.5 w-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className={sectionClass + " p-3"}>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-[#9CA3AF]" />
            <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, file, module..."
              className="w-full rounded-lg border border-[#E5E7EB] py-1.5 pl-8 pr-2 text-xs text-[#111827] placeholder-[#9CA3AF] outline-none focus:border-[#2563EB]" />
            {search && (
              <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2">
                <X className="h-3 w-3 text-[#9CA3AF]" />
              </button>
            )}
          </div>
          <button onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-medium ${
              showFilters ? "border-[#2563EB] text-[#2563EB]" : "border-[#E5E7EB] text-[#6B7280] hover:text-[#111827]"
            }`}>
            <Filter className="h-3 w-3" /> Filters
          </button>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}
            className="rounded-lg border border-[#E5E7EB] px-2 py-1.5 text-xs text-[#374151] outline-none">
            {sortOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <button onClick={() => setSortAsc(!sortAsc)}
            className={`rounded-lg border p-1.5 ${sortAsc ? "border-[#2563EB] text-[#2563EB]" : "border-[#E5E7EB] text-[#6B7280]"}`}>
            <ArrowUpDown className="h-3.5 w-3.5" />
          </button>
        </div>
        {showFilters && (
          <div className="mt-3 flex flex-wrap gap-3 border-t border-[#F3F4F6] pt-3">
            <div>
              <label className="mr-1 text-[10px] text-[#6B7280]">Language</label>
              <select value={langFilter} onChange={(e) => setLangFilter(e.target.value)}
                className="rounded border border-[#E5E7EB] px-2 py-1 text-[10px] text-[#374151] outline-none">
                <option value="">All</option>
                {languages.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="mr-1 text-[10px] text-[#6B7280]">Health</label>
              <select value={healthFilter} onChange={(e) => setHealthFilter(e.target.value)}
                className="rounded border border-[#E5E7EB] px-2 py-1 text-[10px] text-[#374151] outline-none">
                <option value="">All</option>
                {Object.keys(healthBadge).map((h) => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Tab content */}
      {tab === "functions" && (
        <div className={sectionClass + " overflow-hidden"}>
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Functions ({filteredFunctions.length})</p>
          </div>
          {filteredFunctions.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No functions match the current filters.</div>
          ) : (
            <div className="divide-y divide-[#F3F4F6]">{filteredFunctions.map(renderFunctionRow)}</div>
          )}
        </div>
      )}

      {tab === "classes" && (
        <div className={sectionClass + " overflow-hidden"}>
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Classes ({filteredClasses.length})</p>
          </div>
          {filteredClasses.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No classes match the current filters.</div>
          ) : (
            <div className="divide-y divide-[#F3F4F6]">{filteredClasses.map(renderClassRow)}</div>
          )}
        </div>
      )}

      {tab === "insights" && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">AI Insights</p>
          {data.ai_insights.length === 0 ? (
            <p className="text-sm text-[#6B7280]">No insights generated.</p>
          ) : (
            <ul className="space-y-2">
              {data.ai_insights.map((insight, i) => (
                <li key={i} className="flex items-start gap-2 rounded-lg bg-[#F9FAFB] px-4 py-2.5">
                  <FlaskConical className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#7C3AED]" />
                  <span className="text-xs text-[#374151] leading-relaxed">{insight}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {projectId && <RelatedAnalysisNav projectId={projectId} currentPage="function-class" />}

    </motion.div>
  );
}
