import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  FileCode,
  Filter,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { getFileAnalysis } from "@/lib/project-analyzer";
import type { FileAnalysisDetail } from "@/types/project-analyzer";

type SortKey = "score" | "complexity" | "issues" | "maintainability" | "loc" | "name";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.03 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

const healthColor: Record<string, string> = {
  Excellent: "bg-[#ECFDF5] text-[#065F46]",
  Good: "bg-[#EFF6FF] text-[#1E40AF]",
  Fair: "bg-[#FFFBEB] text-[#92400E]",
  "Needs Improvement": "bg-[#FFF7ED] text-[#9A3412]",
  Poor: "bg-[#FEF2F2] text-[#991B1B]",
};

export function FileAnalysis() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<FileAnalysisDetail[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortAsc, setSortAsc] = useState(false);
  const [langFilter, setLangFilter] = useState<string>("all");
  const [healthFilter, setHealthFilter] = useState<string>("all");
  const [tagFilter, setTagFilter] = useState<string>("all");
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getFileAnalysis(Number(projectId));
      setData(result.files);
      fetchedRef.current = true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load file analysis");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const languages = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.map((f) => f.language).filter(Boolean))].sort();
  }, [data]);

  const allTags = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.flatMap((f) => f.tags).filter(Boolean))].sort();
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    let result = [...data];
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (f) =>
          f.path.toLowerCase().includes(q) ||
          f.file_name.toLowerCase().includes(q) ||
          f.language.toLowerCase().includes(q) ||
          f.tags.some((t) => t.toLowerCase().includes(q)),
      );
    }
    if (langFilter !== "all") result = result.filter((f) => f.language === langFilter);
    if (healthFilter !== "all") result = result.filter((f) => f.health === healthFilter);
    if (tagFilter !== "all") result = result.filter((f) => f.tags.includes(tagFilter));
    result.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "score": cmp = b.scores.overall - a.scores.overall; break;
        case "complexity": cmp = b.complexity - a.complexity; break;
        case "issues": cmp = b.issues.length - a.issues.length; break;
        case "maintainability": cmp = b.scores.maintainability - a.scores.maintainability; break;
        case "loc": cmp = b.total_lines - a.total_lines; break;
        case "name": cmp = a.path.localeCompare(b.path); break;
      }
      return sortAsc ? -cmp : cmp;
    });
    return result;
  }, [data, search, langFilter, healthFilter, tagFilter, sortKey, sortAsc]);

  const stats = useMemo(() => {
    if (!data) return null;
    const total = data.length;
    const totalIssues = data.reduce((s, f) => s + f.issues.length, 0);
    const avgScore = data.reduce((s, f) => s + f.scores.overall, 0) / Math.max(total, 1);
    const excellent = data.filter((f) => f.health === "Excellent").length;
    const poor = data.filter((f) => f.health === "Poor" || f.health === "Needs Improvement").length;
    return { total, totalIssues, avgScore, excellent, poor };
  }, [data]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Analyzing files...</p>
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

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <FileCode className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No source files found</p>
        <p className="mt-1 text-xs text-[#6B7280]">Upload and extract a project with supported source files to begin analysis.</p>
      </div>
    );
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">

      {/* Hero */}
      <motion.div variants={itemVariants} className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#059669] to-[#047857] p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-[#A7F3D0]">File-wise Deep Analysis</p>
            <h1 className="mt-1 text-2xl font-bold">File Analysis</h1>
            <p className="mt-1 text-sm text-[#A7F3D0]">{stats?.total ?? 0} files · ∅ {(stats?.avgScore ?? 0).toFixed(0)}/100</p>
          </div>
          <button onClick={fetchData} className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm hover:bg-white/30">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        </div>
      </motion.div>

      {/* Stats cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Files</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{stats?.total ?? 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Issues</p>
          <p className="mt-1 text-lg font-bold text-[#DC2626]">{stats?.totalIssues ?? 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Excellent</p>
          <p className="mt-1 text-lg font-bold text-[#059669]">{stats?.excellent ?? 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Needs Improvement</p>
          <p className="mt-1 text-lg font-bold text-[#DC2626]">{stats?.poor ?? 0}</p>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div variants={itemVariants} className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Search by name, path, language, or tag..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-3 text-xs text-[#111827] placeholder:text-[#9CA3AF] focus:border-[#059669] focus:outline-none"
          />
          {search && <X className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9CA3AF] cursor-pointer hover:text-[#6B7280]" onClick={() => setSearch("")} />}
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#9CA3AF]" />
          <select value={langFilter} onChange={(e) => setLangFilter(e.target.value)}
            className="appearance-none rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-7 text-xs text-[#374151] focus:border-[#059669] focus:outline-none">
            <option value="all">All Languages</option>
            {languages.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#9CA3AF]" />
          <select value={healthFilter} onChange={(e) => setHealthFilter(e.target.value)}
            className="appearance-none rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-7 text-xs text-[#374151] focus:border-[#059669] focus:outline-none">
            <option value="all">All Health</option>
            <option value="Excellent">Excellent</option>
            <option value="Good">Good</option>
            <option value="Fair">Fair</option>
            <option value="Needs Improvement">Needs Improvement</option>
            <option value="Poor">Poor</option>
          </select>
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#9CA3AF]" />
          <select value={tagFilter} onChange={(e) => setTagFilter(e.target.value)}
            className="appearance-none rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-7 text-xs text-[#374151] focus:border-[#059669] focus:outline-none">
            <option value="all">All Tags</option>
            {allTags.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#9CA3AF]" />
          <select value={sortKey} onChange={(e) => setSortKey(e.target.value as SortKey)}
            className="appearance-none rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-7 text-xs text-[#374151] focus:border-[#059669] focus:outline-none">
            <option value="score">Sort by Score</option>
            <option value="complexity">Sort by Complexity</option>
            <option value="issues">Sort by Issues</option>
            <option value="maintainability">Sort by Maintainability</option>
            <option value="loc">Sort by LOC</option>
            <option value="name">Sort by Name</option>
          </select>
        </div>
        <button onClick={() => setSortAsc(!sortAsc)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          {sortAsc ? "↑ Asc" : "↓ Desc"}
        </button>
      </motion.div>

      {/* File table */}
      <motion.div variants={itemVariants} className={sectionClass + " overflow-hidden"}>
        <div className="border-b border-[#E5E7EB] px-5 py-3 flex items-center justify-between">
          <p className="text-sm font-semibold text-[#111827]">Files ({filtered.length})</p>
        </div>
        <div className="divide-y divide-[#F3F4F6]">
          {filtered.map((file) => {
            const isExpanded = expandedFiles.has(file.path);
            return (
              <div key={file.path}>
                {/* File row */}
                <div
                  className="flex items-center gap-3 px-5 py-3 hover:bg-[#F9FAFB] cursor-pointer"
                  onClick={() => {
                    setExpandedFiles((prev) => {
                      const next = new Set(prev);
                      if (next.has(file.path)) next.delete(file.path);
                      else next.add(file.path);
                      return next;
                    });
                  }}
                >
                  <FileCode className="h-4 w-4 shrink-0 text-[#6B7280]" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-medium text-[#111827] truncate">{file.path}</p>
                      <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${healthColor[file.health] || "bg-[#F3F4F6] text-[#374151]"}`}>
                        {file.health}
                      </span>
                    </div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px] text-[#6B7280]">
                      <span>{file.language}</span>
                      <span>{file.total_lines} lines</span>
                      <span>Score {Math.round(file.scores.overall)}</span>
                      <span>{file.issues.length} issues</span>
                      <span>Complexity {file.complexity}</span>
                      {file.tags.slice(0, 3).map((t) => (
                        <span key={t} className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px]">{t}</span>
                      ))}
                    </div>
                  </div>
                  <div className="shrink-0 flex items-center gap-3">
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/projects/${projectId}/analyzer/file-analysis/${encodeURIComponent(file.path)}`); }}
                      className="rounded-lg border border-[#E5E7EB] bg-white px-2.5 py-1 text-[10px] font-medium text-[#374151] hover:bg-[#F3F4F6]"
                    >
                      Details
                    </button>
                    {isExpanded ? <ChevronDown className="h-4 w-4 text-[#9CA3AF]" /> : <ChevronRight className="h-4 w-4 text-[#9CA3AF]" />}
                  </div>
                </div>
                {/* Expanded: scores + AI summary + top issues */}
                {isExpanded && (
                  <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-5 py-4 pl-12">
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-6 mb-3">
                      {(["overall", "maintainability", "complexity", "readability", "documentation", "security"] as const).map((k) => (
                        <div key={k} className="rounded-lg bg-white border border-[#E5E7EB] px-3 py-2">
                          <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF]">{k}</p>
                          <p className="text-sm font-bold text-[#111827]">{Math.round(file.scores[k])}</p>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-[#374151] leading-relaxed mb-2">{file.ai_summary}</p>
                    {file.issues.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-[10px] font-semibold text-[#6B7280]">Top Issues ({file.issues.length})</p>
                        {file.issues.slice(0, 5).map((iss, j) => (
                          <div key={j} className="flex items-start gap-2 text-[10px]">
                            <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                              iss.severity === "critical" || iss.severity === "high" ? "bg-[#DC2626]" :
                              iss.severity === "medium" ? "bg-[#D97706]" : "bg-[#6B7280]"
                            }`} />
                            <span className="text-[#374151]">{iss.description}</span>
                            {iss.line && <span className="shrink-0 text-[#9CA3AF]">L{iss.line}</span>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No files match your filter criteria.</div>
          )}
        </div>
      </motion.div>

    </motion.div>
  );
}
