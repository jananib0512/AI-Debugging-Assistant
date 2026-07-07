import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  AlertCircle,
  ArrowUpDown,
  Box,
  ChevronDown,
  ChevronRight,
  Filter,
  FlaskConical,
  GitBranch,
  Package,
  RefreshCw,
  Search,
  Shield,
  X,
} from "lucide-react";
import { getImportDependencyAnalysis } from "@/lib/project-analyzer";
import type { ImportDependencyResponse, ImportRecord, FileDependency } from "@/types/project-analyzer";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityBadge: Record<string, string> = {
  high: "bg-[#FEF2F2] text-[#991B1B]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
};

type TabType = "imports" | "dependencies" | "circular" | "graph" | "insights";

export function ImportDependencyAnalysis() {
  const { projectId } = useParams<{ projectId: string }>();
  const [data, setData] = useState<ImportDependencyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabType>("imports");
  const [search, setSearch] = useState("");
  const [langFilter, setLangFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("module");
  const [sortAsc, setSortAsc] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const fetchedRef = useRef(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getImportDependencyAnalysis(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load import & dependency analysis");
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
    return Array.from(new Set(data.imports.map((i) => i.language))).sort();
  }, [data]);

  const filteredImports = useMemo(() => {
    if (!data) return [];
    let items = [...data.imports];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (i) =>
          i.module.toLowerCase().includes(q) ||
          i.symbol.toLowerCase().includes(q) ||
          i.source_file.toLowerCase().includes(q),
      );
    }
    if (langFilter) items = items.filter((i) => i.language === langFilter);
    if (typeFilter) items = items.filter((i) => i.import_type === typeFilter);
    if (statusFilter === "broken") items = items.filter((i) => i.is_broken);
    else if (statusFilter === "unused") items = items.filter((i) => i.is_unused);
    else if (statusFilter === "duplicate") items = items.filter((i) => i.is_duplicate);
    else if (statusFilter === "resolved") items = items.filter((i) => i.resolved && !i.is_broken && !i.is_unused);
    items.sort((a, b) => {
      let cmp = 0;
      if (sortBy === "module") cmp = a.module.localeCompare(b.module);
      else if (sortBy === "file") cmp = a.source_file.localeCompare(b.source_file);
      else if (sortBy === "language") cmp = a.language.localeCompare(b.language);
      return sortAsc ? cmp : -cmp;
    });
    return items;
  }, [data, search, langFilter, typeFilter, statusFilter, sortBy, sortAsc]);

  const filteredDeps = useMemo(() => {
    if (!data) return [];
    let items = [...data.dependencies];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (d) =>
          d.source_file.toLowerCase().includes(q) ||
          (d.target_file || "").toLowerCase().includes(q) ||
          d.target_module.toLowerCase().includes(q),
      );
    }
    if (langFilter) items = items.filter((d) => d.language === langFilter);
    if (typeFilter) items = items.filter((d) => d.dependency_type === typeFilter);
    if (statusFilter === "broken") items = items.filter((d) => d.is_broken);
    else if (statusFilter === "unused") items = items.filter((d) => d.is_unused);
    else if (statusFilter === "circular") items = items.filter((d) => d.is_circular);
    else if (statusFilter === "external") items = items.filter((d) => d.is_external);
    items.sort((a, b) => {
      let cmp = 0;
      if (sortBy === "module") cmp = a.target_module.localeCompare(b.target_module);
      else if (sortBy === "file") cmp = a.source_file.localeCompare(b.source_file);
      else if (sortBy === "language") cmp = a.language.localeCompare(b.language);
      return sortAsc ? cmp : -cmp;
    });
    return items;
  }, [data, search, langFilter, typeFilter, statusFilter, sortBy, sortAsc]);

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
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Analyzing imports and dependencies...</p>
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
        <Package className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No analysis data</p>
      </div>
    );
  }

  const m = data.metrics;

  const renderImportRow = (imp: ImportRecord, idx: number) => {
    const key = `${imp.source_file}:${imp.module}:${imp.symbol}:${idx}`;
    const isExpanded = expandedItems.has(key);
    return (
      <div key={key}>
        <button onClick={() => toggleItem(key)}
          className="w-full flex items-center gap-3 px-5 py-2 text-left hover:bg-[#F9FAFB] text-xs">
          <Package className="h-3 w-3 shrink-0 text-[#6B7280]" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-medium text-[#111827]">{imp.module}</span>
              {imp.symbol && <span className="text-[#6B7280]">::{imp.symbol}</span>}
              {imp.is_broken && <span className="rounded bg-[#FEF2F2] px-1 py-0.5 text-[9px] text-[#DC2626]">broken</span>}
              {imp.is_unused && <span className="rounded bg-[#FFFBEB] px-1 py-0.5 text-[9px] text-[#D97706]">unused</span>}
              {imp.is_duplicate && <span className="rounded bg-[#F3F4F6] px-1 py-0.5 text-[9px] text-[#6B7280]">duplicate</span>}
              {imp.is_dynamic && <span className="rounded bg-[#EFF6FF] px-1 py-0.5 text-[9px] text-[#1E40AF]">dynamic</span>}
              {imp.is_wildcard && <span className="rounded bg-[#F3E8FF] px-1 py-0.5 text-[9px] text-[#6D28D9]">wildcard</span>}
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[9px] text-[#9CA3AF]">
              <span>{imp.source_file}</span>
              <span>·</span>
              <span>{imp.language}</span>
              <span>·</span>
              <span>{imp.import_type}</span>
              {imp.line_number && <><span>·</span><span>Line {imp.line_number}</span></>}
            </div>
          </div>
          {isExpanded ? <ChevronDown className="h-3 w-3 text-[#9CA3AF]" /> : <ChevronRight className="h-3 w-3 text-[#9CA3AF]" />}
        </button>
        {isExpanded && (
          <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-5 py-2.5 pl-10">
            <div className="grid grid-cols-2 gap-x-6 gap-y-0.5 text-[10px] text-[#374151]">
              <span>Source: <strong>{imp.source_file}</strong></span>
              <span>Target: <strong>{imp.target_file || "—"}</strong></span>
              <span>Alias: <strong>{imp.alias || "—"}</strong></span>
              <span>Type: <strong>{imp.import_type}</strong></span>
              <span>Relative: <strong>{imp.is_relative ? "Yes" : "No"}</strong></span>
              <span>Resolved: <strong className={imp.resolved ? "text-[#059669]" : "text-[#DC2626]"}>
                {imp.resolved ? "Yes" : "No"}
              </strong></span>
              <span>Confidence: <strong>{(imp.confidence * 100).toFixed(0)}%</strong></span>
            </div>
            {imp.is_broken && <p className="mt-1 text-[10px] text-[#059669]">Fix: Correct the import path or install the missing package.</p>}
            {imp.is_unused && <p className="mt-1 text-[10px] text-[#D97706]">Recommendation: Remove this unused import.</p>}
          </div>
        )}
      </div>
    );
  };

  const renderDepRow = (dep: FileDependency, idx: number) => {
    const key = `dep:${dep.source_file}:${dep.target_module}:${idx}`;
    const isExpanded = expandedItems.has(key);
    return (
      <div key={key}>
        <button onClick={() => toggleItem(key)}
          className="w-full flex items-center gap-3 px-5 py-2 text-left hover:bg-[#F9FAFB] text-xs">
          <GitBranch className="h-3 w-3 shrink-0 text-[#6B7280]" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-medium text-[#111827]">{dep.source_file.split("/").pop()}</span>
              <span className="text-[#9CA3AF]">→</span>
              <span className="font-medium text-[#2563EB]">{dep.target_module}</span>
              {dep.is_broken && <span className="rounded bg-[#FEF2F2] px-1 py-0.5 text-[9px] text-[#DC2626]">broken</span>}
              {dep.is_unused && <span className="rounded bg-[#FFFBEB] px-1 py-0.5 text-[9px] text-[#D97706]">unused</span>}
              {dep.is_circular && <span className="rounded bg-[#FEF2F2] px-1 py-0.5 text-[9px] text-[#DC2626]">circular</span>}
              {dep.is_external && <span className="rounded bg-[#EFF6FF] px-1 py-0.5 text-[9px] text-[#1E40AF]">external</span>}
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[9px] text-[#9CA3AF]">
              <span>{dep.source_file}</span>
              <span>·</span>
              <span>{dep.language}</span>
              <span>·</span>
              <span>{dep.dependency_type}</span>
              <span>·</span>
              <span>{dep.import_count} import(s)</span>
            </div>
          </div>
          {isExpanded ? <ChevronDown className="h-3 w-3 text-[#9CA3AF]" /> : <ChevronRight className="h-3 w-3 text-[#9CA3AF]" />}
        </button>
        {isExpanded && (
          <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-5 py-2.5 pl-10">
            <div className="grid grid-cols-2 gap-x-6 gap-y-0.5 text-[10px] text-[#374151]">
              <span>Source: <strong>{dep.source_file}</strong></span>
              <span>Target: <strong>{dep.target_file || "—"}</strong></span>
              <span>Module: <strong>{dep.target_module}</strong></span>
              <span>Type: <strong>{dep.dependency_type}</strong></span>
              <span>External: <strong>{dep.is_external ? "Yes" : "No"}</strong></span>
              <span>Circular: <strong>{dep.is_circular ? "Yes" : "No"}</strong></span>
              <span>Broken: <strong>{dep.is_broken ? "Yes" : "No"}</strong></span>
              <span>Import count: <strong>{dep.import_count}</strong></span>
            </div>
            <div className="mt-1.5 flex flex-wrap gap-2 text-[10px]">
              {dep.is_broken && <span className="rounded bg-[#FEF2F2] px-2 py-0.5 text-[#DC2626]">1 issue: Broken import — fix the path or install the package</span>}
              {dep.is_unused && <span className="rounded bg-[#FFFBEB] px-2 py-0.5 text-[#D97706]">1 issue: Unused dependency — remove if not needed</span>}
              {dep.is_circular && <span className="rounded bg-[#FEF2F2] px-2 py-0.5 text-[#DC2626]">1 issue: Circular dependency — restructure to break the cycle</span>}
              {!dep.is_broken && !dep.is_unused && !dep.is_circular && (
                <span className="text-[#059669]">No issues</span>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderGraph = () => {
    const nodes = data.graph.nodes;
    const edges = data.graph.edges;
    const maxWeight = Math.max(1, ...edges.map((e) => e.weight));

    return (
      <div className={sectionClass + " p-5"}>
        <p className="mb-3 text-sm font-semibold text-[#111827]">Dependency Graph ({nodes.length} modules, {edges.length} connections)</p>
        <div className="relative overflow-auto max-h-[500px] rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] p-4">
          <svg width={Math.max(800, nodes.length * 40)} height={Math.max(500, nodes.length * 30)}
            className="min-w-full">
            {/* Edges */}
            {edges.map((edge, i) => {
              const srcIdx = nodes.findIndex((n) => n.id === edge.source);
              const tgtIdx = nodes.findIndex((n) => n.id === edge.target);
              if (srcIdx === -1 || tgtIdx === -1) return null;
              const x1 = 60;
              const y1 = srcIdx * 28 + 20;
              const x2 = Math.max(120, (tgtIdx - srcIdx) * 40 + 60);
              const y2 = tgtIdx * 28 + 20;
              const opacity = 0.2 + (edge.weight / maxWeight) * 0.8;
              return (
                <g key={i}>
                  <line x1={x1} y1={y1} x2={x2} y2={y2}
                    stroke={edge.type === "import" ? "#2563EB" : "#7C3AED"}
                    strokeWidth={Math.max(1, edge.weight)} opacity={opacity} />
                  <circle cx={x2} cy={y2} r={2} fill={edge.type === "import" ? "#2563EB" : "#7C3AED"} opacity={opacity} />
                </g>
              );
            })}
            {/* Nodes */}
            {nodes.map((node, i) => {
              const x = 55;
              const y = i * 28 + 20;
              const isSelected = selectedNode === node.id;
              return (
                <g key={node.id} onClick={() => setSelectedNode(node.id === selectedNode ? null : node.id)}
                  className="cursor-pointer">
                  <rect x={x - 4} y={y - 8} width={node.type === "external" ? 80 : 10}
                    height={6} rx={3}
                    fill={node.type === "external" ? "#FEF3C7" : isSelected ? "#DBEAFE" : "#F3F4F6"}
                    stroke={isSelected ? "#2563EB" : "transparent"} strokeWidth={1} />
                  {node.type === "external" ? (
                    <text x={x + 8} y={y + 3} fontSize={8} fill="#92400E">{node.label}</text>
                  ) : (
                    <>
                      <text x={x + 14} y={y + 3} fontSize={8} fill="#374151"
                        fontWeight={isSelected ? "bold" : "normal"}>{node.label}</text>
                      <text x={x + 14} y={y + 12} fontSize={6} fill="#9CA3AF">{node.language}</text>
                    </>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
        <div className="mt-3 flex items-center gap-4 text-[10px] text-[#6B7280]">
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#F3F4F6]" /> Internal module</span>
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#FEF3C7]" /> External package</span>
          <span className="flex items-center gap-1"><span className="h-0.5 w-3 bg-[#2563EB]" /> Import edge</span>
        </div>
      </div>
    );
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">

      {/* Hero */}
      <div className="overflow-hidden rounded-xl bg-gradient-to-br from-[#059669] to-[#2563EB]">
        <div className="px-6 py-8 text-white">
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
            <GitBranch className="h-3.5 w-3.5" /> Import & Dependency Intelligence
          </div>
          <p className="mt-1 text-2xl font-bold">Dependency Analysis</p>
          <p className="mt-1 text-sm text-white/80">Complete analysis of imports, dependencies, circular refs, and module coupling.</p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
        {[
          { label: "Total Imports", value: m.total_imports, icon: Package, color: "text-[#2563EB]" },
          { label: "Dependencies", value: m.total_dependencies, icon: GitBranch, color: "text-[#059669]" },
          { label: "External", value: m.external_libraries, icon: Box, color: "text-[#7C3AED]" },
          { label: "Broken", value: m.broken_dependencies, icon: AlertTriangle, color: "text-[#DC2626]" },
          { label: "Unused", value: m.unused_imports, icon: X, color: "text-[#D97706]" },
          { label: "Circular", value: m.circular_dependencies, icon: RefreshCw, color: "text-[#DC2626]" },
          { label: "Coupling", value: `${m.coupling_score}%`, icon: FlaskConical, color: "text-[#059669]" },
          { label: "Avg Depth", value: m.average_dependency_depth.toFixed(1), icon: ArrowUpDown, color: "text-[#6B7280]" },
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
      <div className="flex items-center gap-0.5 rounded-lg bg-[#F3F4F6] p-0.5 overflow-x-auto">
        {[
          { key: "imports" as TabType, label: `Imports (${m.total_imports})`, icon: Package },
          { key: "dependencies" as TabType, label: `Dependencies (${m.total_dependencies})`, icon: GitBranch },
          { key: "circular" as TabType, label: `Circular (${data.circular_dependencies.length})`, icon: RefreshCw },
          { key: "graph" as TabType, label: "Graph", icon: Box },
          { key: "insights" as TabType, label: "Insights", icon: FlaskConical },
        ].map((t) => (
          <button key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex shrink-0 items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              tab === t.key ? "bg-white text-[#111827] shadow-sm" : "text-[#6B7280] hover:text-[#111827]"
            }`}>
            <t.icon className="h-3.5 w-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Filters (for imports/deps tabs) */}
      {(tab === "imports" || tab === "dependencies") && (
        <div className={sectionClass + " p-3"}>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-[#9CA3AF]" />
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
                placeholder="Search..."
                className="w-full rounded-lg border border-[#E5E7EB] py-1.5 pl-8 pr-2 text-xs text-[#111827] placeholder-[#9CA3AF] outline-none focus:border-[#2563EB]" />
              {search && (
                <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2">
                  <X className="h-3 w-3 text-[#9CA3AF]" />
                </button>
              )}
            </div>
            <button onClick={() => setShowFilters(!showFilters)}
              className={`inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-medium ${
                showFilters ? "border-[#2563EB] text-[#2563EB]" : "border-[#E5E7EB] text-[#6B7280]"
              }`}>
              <Filter className="h-3 w-3" /> Filters
            </button>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}
              className="rounded-lg border border-[#E5E7EB] px-2 py-1.5 text-xs text-[#374151] outline-none">
              <option value="module">Module</option>
              <option value="file">File</option>
              <option value="language">Language</option>
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
                <label className="mr-1 text-[10px] text-[#6B7280]">Type</label>
                <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
                  className="rounded border border-[#E5E7EB] px-2 py-1 text-[10px] text-[#374151] outline-none">
                  <option value="">All</option>
                  <option value="internal">Internal</option>
                  <option value="external">External</option>
                </select>
              </div>
              <div>
                <label className="mr-1 text-[10px] text-[#6B7280]">Status</label>
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded border border-[#E5E7EB] px-2 py-1 text-[10px] text-[#374151] outline-none">
                  <option value="">All</option>
                  <option value="resolved">Resolved</option>
                  <option value="broken">Broken</option>
                  <option value="unused">Unused</option>
                  <option value="duplicate">Duplicate</option>
                  {tab === "dependencies" && <option value="circular">Circular</option>}
                  {tab === "dependencies" && <option value="external">External</option>}
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab content */}
      {tab === "imports" && (
        <div className={sectionClass + " overflow-hidden"}>
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">All Imports ({filteredImports.length})</p>
          </div>
          {filteredImports.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No imports match filters.</div>
          ) : (
            <div className="divide-y divide-[#F3F4F6]">{filteredImports.map(renderImportRow)}</div>
          )}
        </div>
      )}

      {tab === "dependencies" && (
        <div className={sectionClass + " overflow-hidden"}>
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">File Dependencies ({filteredDeps.length})</p>
          </div>
          {filteredDeps.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No dependencies match filters.</div>
          ) : (
            <div className="divide-y divide-[#F3F4F6]">{filteredDeps.map(renderDepRow)}</div>
          )}
        </div>
      )}

      {tab === "circular" && (
        <div className={sectionClass + " overflow-hidden"}>
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Circular Dependencies ({data.circular_dependencies.length})</p>
          </div>
          {data.circular_dependencies.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No circular dependencies found.</div>
          ) : (
            <div className="divide-y divide-[#F3F4F6]">
              {data.circular_dependencies.map((cd, i) => (
                <div key={i} className="px-5 py-3">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertCircle className="h-3.5 w-3.5 text-[#DC2626]" />
                    <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${severityBadge[cd.severity] || "bg-[#F3F4F6] text-[#374151]"}`}>{cd.severity}</span>
                    <span className="text-xs font-medium text-[#111827]">Cycle with {cd.files.length} files</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-1 text-[10px] text-[#6B7280]">
                    {cd.chain.map((f, j) => (
                      <span key={j} className="flex items-center gap-1">
                        <span className="rounded bg-[#FEF2F2] px-1.5 py-0.5 text-[#DC2626]">{f.split("/").pop()}</span>
                        {j < cd.chain.length - 1 && <span className="text-[#9CA3AF]">→</span>}
                      </span>
                    ))}
                  </div>
                  <p className="mt-1 text-[10px] text-[#059669]">{cd.suggested_resolution}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "graph" && renderGraph()}

      {tab === "insights" && (
        <div className="space-y-4">
          <div className={sectionClass + " p-5"}>
            <p className="mb-3 text-sm font-semibold text-[#111827]">AI Insights</p>
            {data.insights.length === 0 ? (
              <p className="text-sm text-[#6B7280]">No insights generated.</p>
            ) : (
              <ul className="space-y-2">
                {data.insights.map((insight, i) => (
                  <li key={i} className="flex items-start gap-2 rounded-lg bg-[#F9FAFB] px-4 py-2.5">
                    <FlaskConical className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#059669]" />
                    <span className="text-xs text-[#374151] leading-relaxed">{insight}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className={sectionClass + " p-5"}>
            <p className="mb-3 text-sm font-semibold text-[#111827]">Recommendations</p>
            {data.recommendations.length === 0 ? (
              <p className="text-sm text-[#6B7280]">No recommendations.</p>
            ) : (
              <ul className="space-y-2">
                {data.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2.5">
                    <Shield className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#2563EB]" />
                    <span className="text-xs text-[#374151] leading-relaxed">{rec}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

    </motion.div>
  );
}
