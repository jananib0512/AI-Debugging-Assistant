import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpDown,
  BarChart3,
  BookOpen,
  Braces,
  FileSearch,
  Filter,
  GitBranch,
  Lightbulb,
  Radar,
  RefreshCw,
  Search,
  Share2,
  Shield,
  X,
} from "lucide-react";
import { getSemanticIntelligence } from "@/lib/project-analyzer";
import type {
  SemanticComponent,
  SemanticResponse,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityBadge: Record<string, string> = {
  high: "bg-[#FEF2F2] text-[#991B1B]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
  info: "bg-[#EFF6FF] text-[#1E40AF]",
};

const typeColors: Record<string, string> = {
  controller: "#1E40AF",
  service: "#065F46",
  repository: "#5B21B6",
  model: "#7C3AED",
  api: "#DC2626",
  middleware: "#D97706",
  configuration: "#6B7280",
  auth: "#059669",
  data: "#0D9488",
  ml: "#9333EA",
  test: "#9CA3AF",
  utility: "#6B7280",
  function: "#2563EB",
  entry_point: "#D97706",
};

const typeBgColors: Record<string, string> = {
  controller: "bg-[#EFF6FF] text-[#1E40AF]",
  service: "bg-[#ECFDF5] text-[#065F46]",
  repository: "bg-[#F5F3FF] text-[#5B21B6]",
  model: "bg-[#F5F3FF] text-[#5B21B6]",
  api: "bg-[#FEF2F2] text-[#991B1B]",
  middleware: "bg-[#FFFBEB] text-[#92400E]",
  configuration: "bg-[#F3F4F6] text-[#374151]",
  auth: "bg-[#ECFDF5] text-[#065F46]",
  data: "bg-[#ECFDF5] text-[#0D9488]",
  ml: "bg-[#F5F3FF] text-[#7C3AED]",
  test: "bg-[#F3F4F6] text-[#6B7280]",
  utility: "bg-[#F3F4F6] text-[#374151]",
  function: "bg-[#EFF6FF] text-[#1E40AF]",
  entry_point: "bg-[#FFFBEB] text-[#92400E]",
};

const flowConfidenceColors: Record<string, string> = {
  high: "bg-[#ECFDF5] text-[#065F46]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#FEF2F2] text-[#991B1B]",
};

export function SemanticIntelligence() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<SemanticResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [langFilter, setLangFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("name");
  const [sortAsc, setSortAsc] = useState(true);
  const [activeTab, setActiveTab] = useState<string>("components");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedComponent, setSelectedComponent] = useState<SemanticComponent | null>(null);
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getSemanticIntelligence(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load semantic intelligence",
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
    return Object.keys(data.stats.language_breakdown).sort();
  }, [data]);

  const componentTypes = useMemo(() => {
    if (!data) return [];
    return Object.keys(data.stats.component_type_counts).sort();
  }, [data]);

  const filteredComponents = useMemo(() => {
    if (!data) return [];
    let items = [...data.components];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.id.toLowerCase().includes(q) ||
          c.module.toLowerCase().includes(q) ||
          c.file_path.toLowerCase().includes(q) ||
          c.type.toLowerCase().includes(q) ||
          c.purpose.toLowerCase().includes(q) ||
          c.business_context.toLowerCase().includes(q) ||
          c.summary.toLowerCase().includes(q),
      );
    }
    if (typeFilter) items = items.filter((c) => c.type === typeFilter || c.sub_type === typeFilter);
    if (langFilter) items = items.filter((c) => c.language === langFilter);
    items.sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "type":
          cmp = a.type.localeCompare(b.type);
          break;
        case "complexity":
          cmp = a.complexity - b.complexity;
          break;
        case "confidence":
          cmp = a.confidence - b.confidence;
          break;
        default:
          cmp = a.name.localeCompare(b.name);
      }
      return sortAsc ? cmp : -cmp;
    });
    return items;
  }, [data, search, typeFilter, langFilter, sortBy, sortAsc]);

  const filteredFlows = useMemo(() => {
    if (!data) return [];
    let items = [...data.business_flows];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (f) =>
          f.name.toLowerCase().includes(q) ||
          f.flow_type.toLowerCase().includes(q) ||
          f.description.toLowerCase().includes(q),
      );
    }
    items.sort((a, b) => (b.verified ? 1 : 0) - (a.verified ? 1 : 0));
    return items;
  }, [data, search]);

  const filteredSimilarities = useMemo(() => {
    if (!data) return [];
    let items = [...data.similarities];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (s) =>
          s.component_a_id.toLowerCase().includes(q) ||
          s.component_b_id.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q),
      );
    }
    items.sort((a, b) => b.score - a.score);
    return items;
  }, [data, search]);

  const handleComponentClick = (comp: SemanticComponent) => {
    setSelectedComponent(comp);
  };

  const clearSelection = () => {
    setSelectedComponent(null);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">
          Analyzing semantic structure...
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
        <Braces className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No semantic data</p>
        <p className="mt-1 text-xs text-[#6B7280]">
          Run project analysis to generate semantic intelligence.
        </p>
      </div>
    );
  }

  const s = data.stats;

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
      <div className="overflow-hidden rounded-xl bg-gradient-to-br from-[#059669] to-[#2563EB]">
        <div className="px-6 py-8 text-white">
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
            <Braces className="h-3.5 w-3.5" /> Semantic Code Intelligence Engine
          </div>
          <p className="mt-1 text-2xl font-bold">Semantic Intelligence</p>
          <p className="mt-1 text-sm text-white/80">
            Understand what each component does, its role, responsibilities, and how business logic flows through the project.
          </p>
        </div>
      </div>

      {/* Understanding Score */}
      {data.understanding_score && (
        <div className={`${sectionClass} p-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radar className="h-4 w-4 text-[#2563EB]" />
              <span className="text-xs font-semibold text-[#374151]">Project Understanding Score</span>
            </div>
            <span className={`text-lg font-bold ${
              data.understanding_score.overall >= 70 ? "text-[#065F46]"
              : data.understanding_score.overall >= 40 ? "text-[#92400E]"
              : "text-[#DC2626]"
            }`}>
              {data.understanding_score.overall}/100
            </span>
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            {[
              { label: "Architecture", value: data.understanding_score.architecture },
              { label: "Business Logic", value: data.understanding_score.business_logic },
              { label: "Dependencies", value: data.understanding_score.dependencies },
              { label: "Code Org", value: data.understanding_score.code_organization },
              { label: "Execution Flow", value: data.understanding_score.execution_flow },
              { label: "Relationships", value: data.understanding_score.semantic_relationships },
              { label: "Maintainability", value: data.understanding_score.maintainability },
              { label: "Readability", value: data.understanding_score.readability },
            ].map((dim) => (
              <div key={dim.label} className="flex items-center gap-1.5">
                <span className="text-[9px] text-[#6B7280]">{dim.label}</span>
                <div className="h-1.5 w-16 rounded-full bg-[#F3F4F6] overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      dim.value >= 70 ? "bg-[#059669]"
                      : dim.value >= 40 ? "bg-[#D97706]"
                      : "bg-[#DC2626]"
                    }`}
                    style={{ width: `${dim.value}%` }}
                  />
                </div>
                <span className="text-[9px] font-medium text-[#374151]">{Math.round(dim.value)}</span>
              </div>
            ))}
          </div>
          <div className="mt-2 flex flex-wrap gap-2.5 text-[9px] text-[#9CA3AF]">
            {data.understanding_score.has_entry_points && <span>✓ Entry Points</span>}
            {data.understanding_score.has_controllers && <span>✓ Controllers</span>}
            {data.understanding_score.has_services && <span>✓ Services</span>}
            {data.understanding_score.has_repositories && <span>✓ Repositories</span>}
            {data.understanding_score.has_ml_components && <span>✓ ML Components</span>}
            {data.understanding_score.has_forecast_components && <span>✓ Forecast</span>}
            <span>Coverage: {Math.round(data.understanding_score.component_coverage * 100)}%</span>
            <span>Flow Capture: {Math.round(data.understanding_score.flow_capture_rate * 100)}%</span>
          </div>
          {data.business_components.length > 0 && (
            <div className="mt-3 border-t border-[#F3F4F6] pt-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Radar className="h-3 w-3 text-[#059669]" />
                <span className="text-[10px] font-semibold text-[#374151]">Business Components ({data.business_components.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {data.business_components.map((bc) => (
                  <span
                    key={bc.id + bc.name}
                    className="rounded bg-[#ECFDF5] px-1.5 py-0.5 text-[9px] text-[#065F46]"
                  >
                    {bc.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {[
          { label: "Components", value: s.total_components, icon: Braces, color: "text-[#2563EB]" },
          { label: "Files", value: s.total_files, icon: FileSearch, color: "text-[#059669]" },
          { label: "Classes", value: s.total_classes, icon: BookOpen, color: "text-[#7C3AED]" },
          { label: "Relationships", value: s.total_relationships, icon: GitBranch, color: "text-[#D97706]" },
          { label: "Business Flows", value: s.total_business_flows, icon: BarChart3, color: "text-[#DC2626]" },
          { label: "Verified Flows", value: s.total_verified_flows, icon: Shield, color: "text-[#065F46]" },
          { label: "Symbols", value: s.total_symbols, icon: Braces, color: "text-[#6B7280]" },
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
            placeholder="Search components, flows, similarities, or issues..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 border-0 bg-transparent text-xs text-[#111827] placeholder-[#9CA3AF] outline-none"
          />
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium transition-colors ${
              showFilters || typeFilter || langFilter || sortBy !== "name"
                ? "bg-[#EFF6FF] text-[#1E40AF]"
                : "text-[#6B7280] hover:bg-[#F3F4F6]"
            }`}
          >
            <Filter className="h-3 w-3" />
            Filters
          </button>
          {(typeFilter || langFilter || search) && (
            <button
              onClick={() => {
                setSearch("");
                setTypeFilter("");
                setLangFilter("");
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
                <span className="text-[9px] font-medium text-[#6B7280]">Type:</span>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="">All</option>
                  {componentTypes.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
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
                <span className="text-[9px] font-medium text-[#6B7280]">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="name">Name</option>
                  <option value="type">Type</option>
                  <option value="complexity">Complexity</option>
                  <option value="confidence">Confidence</option>
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
          {[
            { id: "components", label: "Components", count: s.total_components },
            { id: "relationships", label: "Relationships", count: s.total_relationships },
            { id: "flows", label: "Business Flows", count: s.total_business_flows },
            { id: "similarities", label: "Similarities", count: s.total_similarities },
            { id: "issues", label: "Issues", count: s.total_issues },
            { id: "knowledge-graph", label: "Knowledge Graph", count: data.knowledge_graph ? data.knowledge_graph.nodes.length : 0 },
            { id: "insights", label: "AI Insights", count: data.ai_insights.length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); clearSelection(); }}
              className={`flex-1 px-4 py-2.5 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? "border-b-2 border-[#2563EB] text-[#2563EB]"
                  : "text-[#6B7280] hover:text-[#111827]"
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* Components Tab */}
        {activeTab === "components" && (
          <div className="flex">
            <div className="flex-1 max-h-[600px] overflow-y-auto">
              <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] border-b border-[#F3F4F6]">
                Components ({filteredComponents.length})
              </div>
              {filteredComponents.length > 0 ? (
                filteredComponents.map((comp) => (
                  <div
                    key={comp.id}
                    className="border-b border-[#F3F4F6] px-4 py-2.5 last:border-b-0"
                  >
                    <button
                      onClick={() => handleComponentClick(comp)}
                      className="w-full text-left"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className="h-2 w-2 shrink-0 rounded-full"
                          style={{ backgroundColor: typeColors[comp.type] || "#9CA3AF" }}
                        />
                        <span className="text-xs font-medium text-[#111827]">{comp.name}</span>
                        <span className={`rounded px-1.5 py-0.5 text-[9px] ${typeBgColors[comp.type] || "bg-[#F3F4F6] text-[#374151]"}`}>
                          {comp.type}
                        </span>
                        <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] text-[#6B7280]">
                          {comp.sub_type}
                        </span>
                        <span className="text-[9px] text-[#9CA3AF] ml-auto">
                          {Math.round(comp.confidence * 100)}%
                        </span>
                      </div>
                    </button>
                    {selectedComponent?.id === comp.id && (
                      <div className="mt-2 ml-4 space-y-1.5 border-l-2 border-[#E5E7EB] pl-3">
                        <p className="text-[10px] text-[#6B7280]">
                          <span className="font-medium text-[#374151]">Purpose:</span> {comp.purpose}
                        </p>
                        <p className="text-[10px] text-[#6B7280]">
                          <span className="font-medium text-[#374151]">Role:</span> {comp.role}
                        </p>
                        <p className="text-[10px] text-[#6B7280]">
                          <span className="font-medium text-[#374151]">Responsibility:</span> {comp.responsibility}
                        </p>
                        <p className="text-[10px] text-[#6B7280]">
                          <span className="font-medium text-[#374151]">Business Context:</span> {comp.business_context}
                        </p>
                        {comp.summary && (
                          <p className="text-[10px] text-[#6B7280]">
                            <span className="font-medium text-[#374151]">Summary:</span> {comp.summary}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-1 pt-1">
                          <span className="text-[8px] text-[#9CA3AF]">
                            File: {comp.file_path || "N/A"}
                          </span>
                          <span className="text-[8px] text-[#9CA3AF]">
                            Module: {comp.module || "N/A"}
                          </span>
                          <span className="text-[8px] text-[#9CA3AF]">
                            Line: {comp.line_number}
                          </span>
                          <span className="text-[8px] text-[#9CA3AF]">
                            Complexity: {comp.complexity}
                          </span>
                          <span className="text-[8px] text-[#9CA3AF]">
                            Confidence: {Math.round(comp.confidence * 100)}%
                          </span>
                          {comp.is_entry_point && (
                            <span className="rounded bg-[#FFFBEB] px-1 py-0.5 text-[8px] text-[#92400E]">
                              Entry Point
                            </span>
                          )}
                          {comp.is_test && (
                            <span className="rounded bg-[#F3F4F6] px-1 py-0.5 text-[8px] text-[#6B7280]">
                              Test
                            </span>
                          )}
                          {comp.is_abstract && (
                            <span className="rounded bg-[#F5F3FF] px-1 py-0.5 text-[8px] text-[#5B21B6]">
                              Abstract
                            </span>
                          )}
                          {comp.is_deprecated && (
                            <span className="rounded bg-[#FEF2F2] px-1 py-0.5 text-[8px] text-[#DC2626]">
                              Deprecated
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="flex flex-col items-center py-8 text-xs text-[#9CA3AF]">
                  <FileSearch className="mb-2 h-5 w-5" />
                  No components match filters.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Relationships Tab */}
        {activeTab === "relationships" && (
          <div className="max-h-[600px] overflow-y-auto">
            <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] border-b border-[#F3F4F6]">
              Semantic Relationships ({data.relationships.length})
            </div>
            {data.relationships.length > 0 ? (
              data.relationships.map((rel, idx) => (
                <div key={idx} className="border-b border-[#F3F4F6] px-4 py-2.5 last:border-b-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-[#111827]">{rel.source_id.split(".").pop()}</span>
                    <span className={`rounded px-1.5 py-0.5 text-[8px] font-medium uppercase ${
                      rel.relationship_type === "imports" ? "bg-[#EFF6FF] text-[#1E40AF]"
                      : rel.relationship_type === "same_module" ? "bg-[#ECFDF5] text-[#065F46]"
                      : rel.relationship_type === "exported_to" ? "bg-[#F5F3FF] text-[#5B21B6]"
                      : "bg-[#F3F4F6] text-[#374151]"
                    }`}>
                      {rel.relationship_type.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs font-medium text-[#111827]">{rel.target_id.split(".").pop()}</span>
                    <span className={`ml-auto text-[9px] ${rel.is_direct ? "text-[#065F46]" : "text-[#6B7280]"}`}>
                      {rel.is_direct ? "direct" : "indirect"}
                    </span>
                  </div>
                  <div className="mt-0.5 text-[9px] text-[#6B7280]">{rel.description}</div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <GitBranch className="mb-2 h-6 w-6" />
                No semantic relationships detected.
              </div>
            )}
          </div>
        )}

        {/* Business Flows Tab */}
        {activeTab === "flows" && (
          <div className="max-h-[600px] overflow-y-auto">
            <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] border-b border-[#F3F4F6]">
              Business Flows ({filteredFlows.length})
            </div>
            {filteredFlows.length > 0 ? (
              filteredFlows.map((flow) => (
                <div key={flow.id} className="border-b border-[#F3F4F6] px-4 py-2.5 last:border-b-0">
                  <div className="flex items-center gap-2">
                    <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium ${
                      flowConfidenceColors[flow.confidence] || flowConfidenceColors.medium
                    }`}>
                      {flow.confidence.toUpperCase()}
                    </span>
                    <span className="text-xs font-medium text-[#111827]">{flow.name}</span>
                    {flow.verified && (
                      <span className="rounded bg-[#ECFDF5] px-1.5 py-0.5 text-[8px] text-[#065F46]">Verified</span>
                    )}
                  </div>
                  <div className="mt-0.5 text-[9px] text-[#6B7280]">{flow.description}</div>
                  <div className="mt-1 text-[8px] text-[#9CA3AF]">
                    <span>Type: {flow.flow_type}</span>
                    {flow.components.length > 0 && (
                      <span className="ml-3">Involved: {flow.components.length} component(s)</span>
                    )}
                  </div>
                  {flow.components.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {flow.components.slice(0, 8).map((cid) => (
                        <span key={cid} className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] text-[#6B7280]">
                          {cid.split(".").pop()}
                        </span>
                      ))}
                      {flow.components.length > 8 && (
                        <span className="text-[8px] text-[#9CA3AF]">+{flow.components.length - 8} more</span>
                      )}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <BarChart3 className="mb-2 h-6 w-6" />
                No business flows detected.
              </div>
            )}
          </div>
        )}

        {/* Similarities Tab */}
        {activeTab === "similarities" && (
          <div className="max-h-[600px] overflow-y-auto">
            <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] border-b border-[#F3F4F6]">
              Similar Components ({filteredSimilarities.length})
            </div>
            {filteredSimilarities.length > 0 ? (
              filteredSimilarities.map((sim, idx) => (
                <div key={idx} className="border-b border-[#F3F4F6] px-4 py-2.5 last:border-b-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-[#111827]">
                      {sim.component_a_id.split(".").pop()}
                    </span>
                    <span className="text-[9px] text-[#9CA3AF]">≈</span>
                    <span className="text-xs font-medium text-[#111827]">
                      {sim.component_b_id.split(".").pop()}
                    </span>
                    <span className={`ml-auto rounded px-1.5 py-0.5 text-[8px] font-medium ${
                      sim.score >= 0.6 ? "bg-[#FEF2F2] text-[#DC2626]"
                      : sim.score >= 0.4 ? "bg-[#FFFBEB] text-[#92400E]"
                      : "bg-[#EFF6FF] text-[#1E40AF]"
                    }`}>
                      {Math.round(sim.score * 100)}%
                    </span>
                  </div>
                  <div className="mt-0.5 text-[9px] text-[#6B7280]">{sim.description}</div>
                  {sim.shared_patterns.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {sim.shared_patterns.map((p, pi) => (
                        <span key={pi} className="rounded bg-[#F3F4F6] px-1 py-0.5 text-[8px] text-[#6B7280]">
                          {p}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <Share2 className="mb-2 h-6 w-6" />
                No similarities detected.
              </div>
            )}
          </div>
        )}

        {/* Issues Tab */}
        {activeTab === "issues" && (
          <div className="max-h-[600px] overflow-y-auto">
            <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] border-b border-[#F3F4F6]">
              Issues ({data.issues.length})
            </div>
            {data.issues.length > 0 ? (
              data.issues.map((issue) => (
                <div key={issue.type + issue.component_id} className="border-b border-[#F3F4F6] px-4 py-2.5 last:border-b-0">
                  <div className="flex items-start gap-3">
                    <span
                      className={`mt-0.5 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${
                        severityBadge[issue.severity] || severityBadge.info
                      }`}
                    >
                      {issue.severity}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] font-medium uppercase text-[#374151]">
                          {issue.type.replace(/_/g, " ")}
                        </span>
                        <p className="text-xs font-medium text-[#111827]">{issue.description}</p>
                      </div>
                      {issue.detail && (
                        <p className="mt-0.5 text-[10px] text-[#6B7280]">{issue.detail}</p>
                      )}
                      {issue.suggestion && (
                        <p className="mt-0.5 text-[9px] italic text-[#2563EB]">Suggestion: {issue.suggestion}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <AlertTriangle className="mb-2 h-6 w-6" />
                No semantic issues detected.
              </div>
            )}
          </div>
        )}

        {/* Knowledge Graph Tab */}
        {activeTab === "knowledge-graph" && data.knowledge_graph && (
          <div className="max-h-[600px] overflow-y-auto">
            <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] border-b border-[#F3F4F6]">
              Knowledge Graph — {data.knowledge_graph.nodes.length} nodes, {data.knowledge_graph.edges.length} edges
            </div>
            <div className="p-4">
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="rounded-lg bg-[#F9FAFB] p-3 border border-[#E5E7EB]">
                  <p className="text-[18px] font-bold text-[#111827]">{data.knowledge_graph.nodes.length}</p>
                  <p className="text-[10px] text-[#6B7280]">Graph Nodes</p>
                </div>
                <div className="rounded-lg bg-[#F9FAFB] p-3 border border-[#E5E7EB]">
                  <p className="text-[18px] font-bold text-[#111827]">{data.knowledge_graph.edges.length}</p>
                  <p className="text-[10px] text-[#6B7280]">Graph Edges</p>
                </div>
              </div>
              {/* Node types breakdown */}
              <div className="mb-4">
                <p className="text-[10px] font-semibold text-[#374151] mb-2">Node Types</p>
                <div className="flex flex-wrap gap-1.5">
                  {(() => {
                    const groups: Record<string, number> = {};
                    for (const n of data.knowledge_graph.nodes) {
                      groups[n.group] = (groups[n.group] || 0) + 1;
                    }
                    return Object.entries(groups).sort((a, b) => b[1] - a[1]).map(([g, c]) => (
                      <span
                        key={g}
                        className="rounded px-1.5 py-0.5 text-[9px] font-medium"
                        style={{
                          backgroundColor: typeColors[g] ? `${typeColors[g]}15` : "#F3F4F6",
                          color: typeColors[g] || "#374151",
                        }}
                      >
                        {g}: {c}
                      </span>
                    ));
                  })()}
                </div>
              </div>
              {/* Top nodes by importance */}
              <div>
                <p className="text-[10px] font-semibold text-[#374151] mb-2">Key Nodes (by importance)</p>
                <div className="space-y-1">
                  {[...data.knowledge_graph.nodes]
                    .sort((a, b) => b.importance - a.importance)
                    .slice(0, 15)
                    .map((node) => (
                      <div key={node.id} className="flex items-center gap-2 py-1 border-b border-[#F3F4F6] last:border-b-0">
                        <span
                          className="h-2 w-2 shrink-0 rounded-full"
                          style={{ backgroundColor: typeColors[node.type] || "#9CA3AF" }}
                        />
                        <span className="text-[10px] font-medium text-[#111827]">{node.label}</span>
                        <span className="text-[8px] text-[#9CA3AF]">{node.type}</span>
                        <span className="ml-auto rounded bg-[#F3F4F6] px-1 py-0.5 text-[8px] text-[#6B7280]">
                          {Math.round(node.importance * 100)}%
                        </span>
                      </div>
                    ))}
                </div>
              </div>
              {/* Top edges */}
              {data.knowledge_graph.edges.length > 0 && (
                <div className="mt-4">
                  <p className="text-[10px] font-semibold text-[#374151] mb-2">Top Edges</p>
                  <div className="space-y-1">
                    {[...data.knowledge_graph.edges]
                      .sort((a, b) => b.weight - a.weight)
                      .slice(0, 10)
                      .map((edge, idx) => (
                        <div key={idx} className="flex items-center gap-1.5 py-1 text-[9px] text-[#6B7280]">
                          <span className="font-medium text-[#374151]">{edge.source.split(".").pop()}</span>
                          <span className="rounded bg-[#F3F4F6] px-1 py-0.5 text-[8px]">{edge.relationship}</span>
                          <span className="font-medium text-[#374151]">{edge.target.split(".").pop()}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI Insights Tab */}
        {activeTab === "insights" && (
          <div className="p-5 max-h-[600px] overflow-y-auto">
            {data.ai_insights.length > 0 ? (
              <div className="space-y-2">
                {data.ai_insights.map((insight, idx) => (
                  <div key={idx} className="flex gap-3 rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[#EFF6FF]">
                      <Lightbulb className="h-3.5 w-3.5 text-[#2563EB]" />
                    </div>
                    <p className="text-[10px] text-[#6B7280] leading-relaxed">{insight}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <Lightbulb className="mb-2 h-6 w-6" />
                No AI insights generated.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Related */}
      {projectId && (
        <RelatedAnalysisNav projectId={projectId} currentPage="semantic-intelligence" />
      )}
    </motion.div>
  );
}
