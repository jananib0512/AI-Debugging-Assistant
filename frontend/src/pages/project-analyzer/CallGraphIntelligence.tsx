import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpDown,
  BarChart3,
  FileSearch,
  Filter,
  FlaskConical,
  GitBranch,
  RefreshCw,
  Search,
  Share2,
  Shield,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { getCallGraph } from "@/lib/project-analyzer";
import type {
  CallGraphIssue,
  CallGraphNode,
  CallGraphResponse,
  ExecutionFlow,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityBadge: Record<string, string> = {
  high: "bg-[#FEF2F2] text-[#991B1B]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
};

const typeColors: Record<string, string> = {
  function: "#2563EB",
  method: "#059669",
  class: "#7C3AED",
  entry_point: "#D97706",
  route: "#DC2626",
  controller: "#1E40AF",
  service: "#065F46",
  repository: "#5B21B6",
  library: "#9CA3AF",
};

const typeBgColors: Record<string, string> = {
  function: "bg-[#EFF6FF] text-[#1E40AF]",
  method: "bg-[#ECFDF5] text-[#065F46]",
  class: "bg-[#F5F3FF] text-[#5B21B6]",
  entry_point: "bg-[#FFFBEB] text-[#92400E]",
  route: "bg-[#FEF2F2] text-[#991B1B]",
  controller: "bg-[#EFF6FF] text-[#1E40AF]",
  service: "bg-[#ECFDF5] text-[#065F46]",
  repository: "bg-[#F5F3FF] text-[#5B21B6]",
  library: "bg-[#F3F4F6] text-[#374151]",
};

const flowTypeColors: Record<string, string> = {
  api: "bg-[#EFF6FF] text-[#1E40AF]",
  cli: "bg-[#F5F3FF] text-[#5B21B6]",
  main: "bg-[#ECFDF5] text-[#065F46]",
  background: "bg-[#FFFBEB] text-[#92400E]",
  framework: "bg-[#FEF2F2] text-[#991B1B]",
  request: "bg-[#F3F4F6] text-[#374151]",
  controller: "bg-[#EFF6FF] text-[#1E40AF]",
  service: "bg-[#ECFDF5] text-[#065F46]",
  repository: "bg-[#F5F3FF] text-[#5B21B6]",
  forecast: "bg-[#FEF2F2] text-[#991B1B]",
  forecast_generation: "bg-[#FEF2F2] text-[#991B1B]",
  pipeline: "bg-[#F5F3FF] text-[#5B21B6]",
  ml: "bg-[#F5F3FF] text-[#7C3AED]",
  eda: "bg-[#FFFBEB] text-[#92400E]",
  preprocessing: "bg-[#ECFDF5] text-[#0D9488]",
  authentication: "bg-[#FEF2F2] text-[#991B1B]",
  authorization: "bg-[#FEF2F2] text-[#991B1B]",
  upload: "bg-[#EFF6FF] text-[#1E40AF]",
  validation: "bg-[#FFFBEB] text-[#92400E]",
  report: "bg-[#F3F4F6] text-[#374151]",
  comparison: "bg-[#F5F3FF] text-[#5B21B6]",
  database: "bg-[#ECFDF5] text-[#065F46]",
  scheduled: "bg-[#FFFBEB] text-[#92400E]",
  response: "bg-[#F3F4F6] text-[#374151]",
};

function truncateLabel(label: string, maxLen = 20) {
  if (label.length <= maxLen) return label;
  return label.slice(0, maxLen - 3) + "...";
}

export function CallGraphIntelligence() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<CallGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [langFilter, setLangFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("name");
  const [sortAsc, setSortAsc] = useState(true);
  const [activeTab, setActiveTab] = useState<string>("graph");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedNode, setSelectedNode] = useState<CallGraphNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const fetchedRef = useRef(false);
  const svgRef = useRef<SVGSVGElement>(null);
  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const [highlightedEdges, setHighlightedEdges] = useState<Set<string>>(new Set());
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getCallGraph(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load call graph intelligence",
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

  const nodeTypes = useMemo(() => {
    if (!data) return [];
    return Object.keys(data.stats.node_type_counts).sort();
  }, [data]);

  const filteredNodes = useMemo(() => {
    if (!data) return [];
    let items = [...data.nodes];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (n) =>
          n.name.toLowerCase().includes(q) ||
          n.id.toLowerCase().includes(q) ||
          n.module.toLowerCase().includes(q) ||
          n.file_path.toLowerCase().includes(q) ||
          n.type.toLowerCase().includes(q),
      );
    }
    if (typeFilter) items = items.filter((n) => n.type === typeFilter);
    if (langFilter) items = items.filter((n) => n.language === langFilter);
    items.sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "complexity":
          cmp = a.complexity - b.complexity;
          break;
        case "depth":
          cmp = a.call_depth - b.call_depth;
          break;
        case "type":
          cmp = a.type.localeCompare(b.type);
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
    let items = [...data.execution_flows];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (f) =>
          f.name.toLowerCase().includes(q) ||
          f.flow_type.toLowerCase().includes(q) ||
          f.description.toLowerCase().includes(q),
      );
    }
    if (typeFilter) items = items.filter((f) => f.flow_type === typeFilter);
    items.sort((a, b) => b.depth - a.depth);
    return items;
  }, [data, search, typeFilter]);

  const nodeMap = useMemo(() => {
    if (!data) return new Map<string, CallGraphNode>();
    return new Map(data.nodes.map((n) => [n.id, n]));
  }, [data]);

  const handleNodeClick = (node: CallGraphNode) => {
    setSelectedNode(node);
    setFocusedNodeId(node.id);
    const connected = new Set<string>();
    const edgeKeys = new Set<string>();
    if (data) {
      for (const edge of data.edges) {
        if (edge.source === node.id) {
          connected.add(edge.target);
          edgeKeys.add(`${edge.source}->${edge.target}`);
        }
        if (edge.target === node.id) {
          connected.add(edge.source);
          edgeKeys.add(`${edge.source}->${edge.target}`);
        }
      }
      connected.add(node.id);
    }
    setHighlightedNodes(connected);
    setHighlightedEdges(edgeKeys);
  };

  const clearSelection = () => {
    setSelectedNode(null);
    setFocusedNodeId(null);
    setHighlightedNodes(new Set());
    setHighlightedEdges(new Set());
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.max(0.2, Math.min(5, z * delta)));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === svgRef.current || (e.target as SVGElement).tagName === "svg") {
      isDragging.current = true;
      dragStart.current = { x: e.clientX - panOffset.x, y: e.clientY - panOffset.y };
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging.current) {
      setPanOffset({ x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y });
    }
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const graphLayout = useMemo(() => {
    if (!data || data.nodes.length === 0) return { nodes: [], edges: [] };

    const nodePositions = new Map<string, { x: number; y: number }>();
    const nodeList = data.nodes;

    const entryNodes = nodeList.filter((n) => n.is_entry_point);
    const otherNodes = nodeList.filter((n) => !n.is_entry_point);

    const sortedNodes = [...entryNodes, ...otherNodes];
    const cols = Math.ceil(Math.sqrt(sortedNodes.length));
    const nodeWidth = 140;
    const nodeHeight = 40;
    const hGap = 20;
    const vGap = 15;

    sortedNodes.forEach((node, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      nodePositions.set(node.id, {
        x: col * (nodeWidth + hGap) + nodeWidth / 2,
        y: row * (nodeHeight + vGap) + nodeHeight / 2,
      });
    });

    const visibleEdges = data.edges.filter((e) =>
      nodePositions.has(e.source) && nodePositions.has(e.target),
    );

    return {
      nodes: sortedNodes.map((n) => ({
        ...n,
        x: nodePositions.get(n.id)?.x ?? 0,
        y: nodePositions.get(n.id)?.y ?? 0,
      })),
      edges: visibleEdges.map((e) => ({
        ...e,
        sourceX: nodePositions.get(e.source)?.x ?? 0,
        sourceY: nodePositions.get(e.source)?.y ?? 0,
        targetX: nodePositions.get(e.target)?.x ?? 0,
        targetY: nodePositions.get(e.target)?.y ?? 0,
      })),
    };
  }, [data]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">
          Building call graph...
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
        <Share2 className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No call graph data</p>
        <p className="mt-1 text-xs text-[#6B7280]">
          Run project analysis to generate call graph intelligence.
        </p>
      </div>
    );
  }

  const s = data.stats;

  const renderFlowRow = (flow: ExecutionFlow) => {
    const flowKey = flow.id;
    const pathNames = flow.path.map(
      (pid) => nodeMap.get(pid)?.name ?? pid,
    );
    return (
      <div key={flowKey} className="border-b border-[#F3F4F6] px-4 py-2.5 last:border-b-0">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`rounded px-1.5 py-0.5 text-[9px] font-medium ${
              flowTypeColors[flow.flow_type] || flowTypeColors.request
            }`}
          >
            {flow.flow_type.toUpperCase()}
          </span>
          <span className="text-xs font-medium text-[#111827]">{flow.name}</span>
          <span className="text-[10px] text-[#6B7280]">depth: {flow.depth}</span>
          {!flow.is_complete && (
            <span className="rounded bg-[#FFFBEB] px-1.5 py-0.5 text-[9px] text-[#92400E]">Incomplete</span>
          )}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-1 text-[9px] text-[#6B7280]">
              {pathNames.map((pn, idx) => {
                const pathId = flow.path[idx];
                return (
                  <span key={idx}>
                    {idx > 0 && <span className="mx-0.5 text-[#9CA3AF]">→</span>}
                    <button
                      onClick={() => {
                        const n = pathId ? nodeMap.get(pathId) : undefined;
                        if (n) handleNodeClick(n);
                        setActiveTab("graph");
                      }}
                      className="hover:text-[#2563EB] hover:underline"
                    >
                      {truncateLabel(pn, 25)}
                    </button>
                  </span>
                );
              })}
        </div>
        {flow.issues.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {flow.issues.map((iss, idx) => (
              <span key={idx} className="rounded bg-[#FEF2F2] px-1 py-0.5 text-[8px] text-[#DC2626]">{iss}</span>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderIssueRow = (issue: CallGraphIssue) => {
    return (
      <div key={issue.type + issue.nodes.join(",")} className="border-b border-[#F3F4F6] px-4 py-2.5 last:border-b-0">
        <div className="flex items-start gap-3">
          <span
            className={`mt-0.5 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${
              severityBadge[issue.severity] || severityBadge.low
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
            {issue.nodes.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {issue.nodes.map((nid) => {
                  const node = nodeMap.get(nid);
                  return (
                    <button
                      key={nid}
                      onClick={() => {
                        if (node) handleNodeClick(node);
                        setActiveTab("graph");
                      }}
                      className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[9px] text-[#1E40AF] hover:underline"
                    >
                      {node?.name ?? nid}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

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
            <Share2 className="h-3.5 w-3.5" /> Call Graph & Execution Flow Engine
          </div>
          <p className="mt-1 text-2xl font-bold">Call Graph Intelligence</p>
          <p className="mt-1 text-sm text-white/80">
            Interactive visualization of function calls, execution flows, entry points, and call chain analysis.
          </p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {[
          { label: "Total Nodes", value: s.total_nodes, icon: Share2, color: "text-[#2563EB]" },
          { label: "Call Edges", value: s.total_edges, icon: GitBranch, color: "text-[#059669]" },
          { label: "Entry Points", value: s.total_entry_points, icon: BarChart3, color: "text-[#7C3AED]" },
          { label: "Exec Flows", value: s.total_execution_flows, icon: FlaskConical, color: "text-[#D97706]" },
          { label: "Total Issues", value: s.total_issues, icon: AlertTriangle, color: "text-[#DC2626]" },
          { label: "Max Depth", value: s.max_call_depth, icon: ArrowUpDown, color: "text-[#6B7280]" },
          { label: "Unused", value: s.total_unused, icon: Shield, color: "text-[#6B7280]" },
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
            placeholder="Search nodes, flows, entry points, or issues..."
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
                  {nodeTypes.map((t) => (
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
                  <option value="complexity">Complexity</option>
                  <option value="depth">Depth</option>
                  <option value="type">Type</option>
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
            { id: "graph", label: "Call Graph", count: s.total_nodes },
            { id: "flows", label: "Execution Flows", count: s.total_execution_flows },
            { id: "entry-points", label: "Entry Points", count: s.total_entry_points },
            { id: "issues", label: "Issues", count: s.total_issues },
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

        {/* Graph Tab */}
        {activeTab === "graph" && (
          <div className="flex">
            {/* Node list sidebar */}
            <div className="w-1/3 border-r border-[#F3F4F6] max-h-[600px] overflow-y-auto">
              <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] border-b border-[#F3F4F6]">
                Nodes ({filteredNodes.length})
              </div>
              {filteredNodes.length > 0 ? (
                filteredNodes.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => handleNodeClick(node)}
                    className={`w-full flex items-center gap-2 px-3 py-1.5 text-left text-[10px] transition-colors hover:bg-[#F9FAFB] ${
                      focusedNodeId === node.id ? "bg-[#EFF6FF]" : ""
                    } ${highlightedNodes.has(node.id) ? "bg-[#FFFBEB]" : ""}`}
                  >
                    <span
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: typeColors[node.type] || "#9CA3AF" }}
                    />
                    <span className="flex-1 truncate font-medium text-[#111827]">{node.name}</span>
                    <span className="shrink-0 text-[#9CA3AF]">{node.type}</span>
                    <span
                      className={`shrink-0 rounded px-1 py-0.5 text-[8px] ${
                        node.is_dead ? "bg-[#FEF2F2] text-[#DC2626]" : "bg-[#ECFDF5] text-[#065F46]"
                      }`}
                    >
                      {node.is_dead ? "dead" : "active"}
                    </span>
                  </button>
                ))
              ) : (
                <div className="flex flex-col items-center py-8 text-xs text-[#9CA3AF]">
                  <FileSearch className="mb-2 h-5 w-5" />
                  No nodes match filters.
                </div>
              )}
            </div>
            {/* Graph canvas */}
            <div className="flex-1 relative">
              <div className="absolute top-2 right-2 z-10 flex items-center gap-1">
                <button
                  onClick={() => setZoom((z) => Math.min(5, z * 1.2))}
                  className="rounded border border-[#E5E7EB] bg-white p-1 hover:bg-[#F3F4F6]"
                  title="Zoom in"
                >
                  <ZoomIn className="h-3.5 w-3.5 text-[#6B7280]" />
                </button>
                <button
                  onClick={() => setZoom((z) => Math.max(0.2, z / 1.2))}
                  className="rounded border border-[#E5E7EB] bg-white p-1 hover:bg-[#F3F4F6]"
                  title="Zoom out"
                >
                  <ZoomOut className="h-3.5 w-3.5 text-[#6B7280]" />
                </button>
                <button
                  onClick={() => { setZoom(1); setPanOffset({ x: 0, y: 0 }); }}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[9px] text-[#6B7280] hover:bg-[#F3F4F6]"
                >
                  Reset
                </button>
              </div>
              {selectedNode && (
                <div className="absolute bottom-2 left-2 right-2 z-10 rounded-lg border border-[#E5E7EB] bg-white p-3 text-[10px] shadow-lg max-h-[200px] overflow-y-auto">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span
                          className="h-2 w-2 shrink-0 rounded-full"
                          style={{ backgroundColor: typeColors[selectedNode.type] || "#9CA3AF" }}
                        />
                        <p className="text-xs font-medium text-[#111827]">{selectedNode.name}</p>
                        <span className={`rounded px-1 py-0.5 text-[8px] ${typeBgColors[selectedNode.type] || "bg-[#F3F4F6] text-[#374151]"}`}>
                          {selectedNode.type}
                        </span>
                      </div>
                      <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 text-[9px] text-[#6B7280]">
                        <span>File: <strong>{selectedNode.file_path || "N/A"}</strong></span>
                        <span>Module: <strong>{selectedNode.module || "N/A"}</strong></span>
                        <span>Complexity: <strong>{selectedNode.complexity}</strong></span>
                        <span>Depth: <strong>{selectedNode.call_depth}</strong></span>
                        <span>Maintainability: <strong>{selectedNode.maintainability.toFixed(0)}%</strong></span>
                        <span>Language: <strong>{selectedNode.language}</strong></span>
                      </div>
                      {selectedNode.is_entry_point && (
                        <span className="mt-1 inline-block rounded bg-[#FFFBEB] px-1.5 py-0.5 text-[8px] text-[#92400E]">Entry Point</span>
                      )}
                      {selectedNode.is_dead && (
                        <span className="mt-1 inline-block rounded bg-[#FEF2F2] px-1.5 py-0.5 text-[8px] text-[#DC2626]">Dead Code</span>
                      )}
                    </div>
                    <button onClick={clearSelection} className="shrink-0 text-[#9CA3AF] hover:text-[#111827]">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              )}
              <svg
                ref={svgRef}
                className="w-full h-[600px] bg-[#FAFAFA] cursor-grab active:cursor-grabbing"
                onWheel={handleWheel}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              >
                <g transform={`translate(${panOffset.x}, ${panOffset.y}) scale(${zoom})`}>
                  {/* Edges */}
                  {graphLayout.edges.map((edge, idx) => {
                    const edgeKey = `${edge.source}->${edge.target}`;
                    const isHighlighted = highlightedEdges.has(edgeKey);
                    return (
                      <g key={idx}>
                        <line
                          x1={edge.sourceX}
                          y1={edge.sourceY}
                          x2={edge.targetX}
                          y2={edge.targetY}
                          stroke={isHighlighted ? "#2563EB" : edge.is_cross_file ? "#9CA3AF" : "#D1D5DB"}
                          strokeWidth={isHighlighted ? 2 : edge.is_cross_file ? 1.5 : 1}
                          strokeDasharray={edge.is_recursive ? "4,3" : "none"}
                          opacity={isHighlighted ? 1 : 0.5}
                          className="transition-all"
                        />
                        {/* Arrow */}
                        <polygon
                          points={`${edge.targetX - 4},${edge.targetY - 3} ${edge.targetX},${edge.targetY} ${edge.targetX - 4},${edge.targetY + 3}`}
                          fill={isHighlighted ? "#2563EB" : "#9CA3AF"}
                          opacity={isHighlighted ? 1 : 0.5}
                          transform={`rotate(${Math.atan2(
                            edge.targetY - edge.sourceY,
                            edge.targetX - edge.sourceX,
                          ) * 180 / Math.PI}, ${edge.targetX}, ${edge.targetY})`}
                        />
                      </g>
                    );
                  })}
                  {/* Nodes */}
                  {graphLayout.nodes.map((node) => {
                    const isSelected = focusedNodeId === node.id;
                    const isHighlighted = highlightedNodes.has(node.id) || highlightedNodes.size === 0;
                    return (
                      <g
                        key={node.id}
                        onClick={() => handleNodeClick(node)}
                        className="cursor-pointer"
                        transform={`translate(${node.x}, ${node.y})`}
                      >
                        <rect
                          x={-65}
                          y={-16}
                          width={130}
                          height={32}
                          rx={6}
                          ry={6}
                          fill={
                            isSelected
                              ? "#DBEAFE"
                              : node.is_dead
                              ? "#FEF2F2"
                              : node.is_entry_point
                              ? "#FFFBEB"
                              : "#FFFFFF"
                          }
                          stroke={
                            isSelected
                              ? "#2563EB"
                              : typeColors[node.type] || "#D1D5DB"
                          }
                          strokeWidth={isSelected ? 2 : 1.5}
                          opacity={isHighlighted ? 1 : 0.3}
                          className="transition-all"
                        />
                        <text
                          x={0}
                          y={0}
                          textAnchor="middle"
                          dominantBaseline="central"
                          fill={isSelected ? "#1E40AF" : "#374151"}
                          fontSize={8}
                          fontFamily="monospace"
                          opacity={isHighlighted ? 1 : 0.3}
                        >
                          {truncateLabel(node.name, 18)}
                        </text>
                        {node.is_entry_point && (
                          <circle cx={-58} cy={-16} r={3} fill="#D97706" />
                        )}
                        {node.is_recursive && (
                          <circle cx={58} cy={-16} r={3} fill="#DC2626" />
                        )}
                      </g>
                    );
                  })}
                </g>
              </svg>
            </div>
          </div>
        )}

        {/* Execution Flows Tab */}
        {activeTab === "flows" && (
          <div className="max-h-[600px] overflow-y-auto divide-y divide-[#F3F4F6]">
            {filteredFlows.length > 0 ? (
              filteredFlows.map(renderFlowRow)
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <FileSearch className="mb-2 h-6 w-6" />
                No execution flows match the current filters.
              </div>
            )}
          </div>
        )}

        {/* Entry Points Tab */}
        {activeTab === "entry-points" && (
          <div className="max-h-[600px] overflow-y-auto">
            <div className="px-4 py-2.5 border-b border-[#F3F4F6] text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">
              {data.entry_points.length} Entry Point{data.entry_points.length !== 1 ? "s" : ""}
            </div>
            {data.entry_points.length > 0 ? (
              data.entry_points.map((ep) => (
                <div key={ep.id} className="border-b border-[#F3F4F6] px-4 py-2.5 last:border-b-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-[#D97706]" />
                      <span className="text-xs font-medium text-[#111827]">{ep.name}</span>
                      <span className="rounded bg-[#FFFBEB] px-1.5 py-0.5 text-[9px] text-[#92400E]">
                        {ep.type}
                      </span>
                    </div>
                    <button
                      onClick={() => { handleNodeClick(ep); setActiveTab("graph"); }}
                      className="rounded px-2 py-1 text-[9px] text-[#2563EB] hover:bg-[#EFF6FF]"
                    >
                      View in Graph
                    </button>
                  </div>
                  <div className="mt-1 text-[9px] text-[#6B7280]">
                    <span className="mr-3">Module: {ep.module}</span>
                    <span>File: {ep.file_path}</span>
                    <span className="ml-3">Line: {ep.line_number}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <FileSearch className="mb-2 h-6 w-6" />
                No entry points detected.
              </div>
            )}
          </div>
        )}

        {/* Issues Tab */}
        {activeTab === "issues" && (
          <div className="max-h-[600px] overflow-y-auto divide-y divide-[#F3F4F6]">
            {data.issues.length > 0 ? (
              data.issues.map(renderIssueRow)
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <Shield className="mb-2 h-6 w-6" />
                No issues detected.
              </div>
            )}
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
                      <BarChart3 className="h-3.5 w-3.5 text-[#2563EB]" />
                    </div>
                    <p className="text-[10px] text-[#6B7280] leading-relaxed">{insight}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
                <BarChart3 className="mb-2 h-6 w-6" />
                No AI insights generated.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Related */}
      {projectId && (
        <RelatedAnalysisNav projectId={projectId} currentPage="call-graph" />
      )}
    </motion.div>
  );
}
