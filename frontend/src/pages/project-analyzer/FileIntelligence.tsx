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
  Copy,
  FileCode,
  FileSearch,
  Filter,
  FlaskConical,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { getFileIntelligence } from "@/lib/project-analyzer";
import type {
  FileIntelligenceDetail,
  FileIntelligenceResponse,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityBadge: Record<string, string> = {
  high: "bg-[#FEF2F2] text-[#991B1B]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
};

const classificationColors: Record<string, string> = {
  Controller: "bg-[#EFF6FF] text-[#1E40AF]",
  Service: "bg-[#ECFDF5] text-[#065F46]",
  Model: "bg-[#FEF3C7] text-[#92400E]",
  Utility: "bg-[#F3F4F6] text-[#374151]",
  Configuration: "bg-[#F5F3FF] text-[#5B21B6]",
  Database: "bg-[#FEF2F2] text-[#991B1B]",
  API: "bg-[#E0E7FF] text-[#3730A3]",
  Frontend: "bg-[#FFE4E6] text-[#9F1239]",
  Backend: "bg-[#EFF6FF] text-[#1E40AF]",
  Testing: "bg-[#F0FDF4] text-[#166534]",
  Documentation: "bg-[#F8FAFC] text-[#475569]",
  Assets: "bg-[#F5F5F4] text-[#44403C]",
  Scripts: "bg-[#FAF5FF] text-[#6B21A8]",
};

function formatSize(bytes: number) {
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + " GB";
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
  if (bytes >= 1024) return (bytes / 1024).toFixed(0) + " KB";
  return bytes + " B";
}

function truncatePath(path: string, maxLen = 50) {
  if (path.length <= maxLen) return path;
  const start = path.lastIndexOf("/", maxLen);
  return "..." + path.slice(start);
}

export function FileIntelligence() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<FileIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [langFilter, setLangFilter] = useState<string>("");
  const [classFilter, setClassFilter] = useState<string>("");
  const [healthFilter, setHealthFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("path");
  const [sortAsc, setSortAsc] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getFileIntelligence(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load file intelligence",
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
    return Object.keys(data.stats.language_counts).sort();
  }, [data]);

  const classifications = useMemo(() => {
    if (!data) return [];
    return Object.keys(data.stats.classification_counts).sort();
  }, [data]);

  const filteredFiles = useMemo(() => {
    if (!data) return [];
    let items = [...data.files];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (f) =>
          f.file_name.toLowerCase().includes(q) ||
          f.path.toLowerCase().includes(q) ||
          f.language.toLowerCase().includes(q) ||
          f.classification.toLowerCase().includes(q) ||
          f.tags.some((t) => t.toLowerCase().includes(q)),
      );
    }
    if (langFilter) items = items.filter((f) => f.language === langFilter);
    if (classFilter)
      items = items.filter((f) => f.classification === classFilter);
    if (healthFilter === "excellent")
      items = items.filter((f) => f.health.overall >= 80);
    else if (healthFilter === "good")
      items = items.filter(
        (f) => f.health.overall >= 60 && f.health.overall < 80,
      );
    else if (healthFilter === "fair")
      items = items.filter(
        (f) => f.health.overall >= 40 && f.health.overall < 60,
      );
    else if (healthFilter === "poor")
      items = items.filter((f) => f.health.overall < 40);
    items.sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case "name":
          cmp = a.file_name.localeCompare(b.file_name);
          break;
        case "size":
          cmp = a.size - b.size;
          break;
        case "complexity":
          cmp = a.complexity - b.complexity;
          break;
        case "maintainability":
          cmp = a.health.maintainability - b.health.maintainability;
          break;
        case "quality":
          cmp = a.health.overall - b.health.overall;
          break;
        case "issues":
          cmp = a.issues.length - b.issues.length;
          break;
        case "modified":
          cmp = a.last_modified.localeCompare(b.last_modified);
          break;
        default:
          cmp = a.path.localeCompare(b.path);
      }
      return sortAsc ? cmp : -cmp;
    });
    return items;
  }, [data, search, langFilter, classFilter, healthFilter, sortBy, sortAsc]);

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
          Analyzing files...
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
        <FileSearch className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No file data</p>
        <p className="mt-1 text-xs text-[#6B7280]">
          Run project analysis to generate file intelligence.
        </p>
      </div>
    );
  }

  const s = data.stats;

  const renderDetailRow = (file: FileIntelligenceDetail) => {
    const key = file.path;
    const isExpanded = expandedItems.has(key);
    return (
      <div key={key} className="border-b border-[#F3F4F6] last:border-b-0">
        {/* Summary row */}
        <button
          onClick={() => toggleItem(key)}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-[#F9FAFB] text-xs"
        >
          <FileCode className="h-3.5 w-3.5 shrink-0 text-[#6B7280]" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-medium text-[#111827]">
                {file.file_name}
              </span>
              <span
                className={
                  classificationColors[file.classification] ||
                  "rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#374151]"
                }
              >
                {file.classification}
              </span>
              <span className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[9px] text-[#1E40AF]">
                {file.language}
              </span>
              {file.issues.length > 0 && (
                <span
                  className={`rounded px-1.5 py-0.5 text-[9px] ${
                    file.issues.some((i) => i.severity === "high")
                      ? "bg-[#FEF2F2] text-[#DC2626]"
                      : "bg-[#FFFBEB] text-[#92400E]"
                  }`}
                >
                  {file.issues.length} issue{file.issues.length > 1 ? "s" : ""}
                </span>
              )}
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[9px] text-[#9CA3AF]">
              <span className="truncate max-w-[200px]">
                {truncatePath(file.path)}
              </span>
              <span>·</span>
              <span>{file.total_lines} lines</span>
              <span>·</span>
              <span>{formatSize(file.size)}</span>
              <span>·</span>
              <span>Score: {file.health.overall}%</span>
            </div>
          </div>
          {isExpanded ? (
            <ChevronDown className="h-3 w-3 shrink-0 text-[#9CA3AF]" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 text-[#9CA3AF]" />
          )}
        </button>
        {/* Expanded detail */}
        {isExpanded && (
          <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-4 py-3 pl-10">
            {/* AI summary */}
            {file.ai_summary && (
              <div className="mb-3 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[10px] leading-relaxed text-[#374151]">
                <span className="font-medium text-[#6B7280]">AI Summary:</span>{" "}
                {file.ai_summary}
              </div>
            )}
            {/* Scores */}
            <div className="mb-2 grid grid-cols-3 gap-2 sm:grid-cols-6">
              {[
                { label: "Overall", value: file.health.overall },
                { label: "Maintainability", value: file.health.maintainability },
                { label: "Complexity", value: file.health.complexity },
                { label: "Documentation", value: file.health.documentation },
                { label: "Readability", value: file.health.readability },
                { label: "Security", value: file.health.security },
              ].map((m) => (
                <div
                  key={m.label}
                  className="rounded bg-white border border-[#E5E7EB] px-2 py-1.5 text-center"
                >
                  <p className="text-xs font-bold text-[#111827]">
                    {m.value.toFixed(0)}
                  </p>
                  <p className="text-[9px] text-[#6B7280]">{m.label}</p>
                </div>
              ))}
            </div>
            {/* Metadata */}
            <div className="mb-2 grid grid-cols-2 gap-x-4 gap-y-0.5 text-[10px] text-[#374151]">
              <span>
                Path: <strong className="break-all">{file.path}</strong>
              </span>
              <span>
                Extension: <strong>{file.extension}</strong>
              </span>
              <span>
                Encoding: <strong>{file.encoding}</strong>
              </span>
              <span>
                Size: <strong>{formatSize(file.size)}</strong>
              </span>
              <span>
                Lines: <strong>{file.total_lines}</strong> (code:{" "}
                <strong>{file.code_lines}</strong>, blank:{" "}
                <strong>{file.blank_lines}</strong>, comments:{" "}
                <strong>{file.comment_lines}</strong>)
              </span>
              <span>
                Complexity: <strong>{file.complexity}</strong>
              </span>
              <span>
                Functions: <strong>{file.functions}</strong>
              </span>
              <span>
                Classes: <strong>{file.classes}</strong>
              </span>
              <span>
                Imports: <strong>{file.imports}</strong>
              </span>
            </div>
            {/* Tags */}
            {file.tags.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-1">
                {file.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#374151]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
            {/* Issues */}
            {file.issues.length > 0 && (
              <div className="space-y-1">
                <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF]">
                  Issues
                </p>
                {file.issues.map((issue, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2 rounded bg-white border border-[#E5E7EB] px-2 py-1.5"
                  >
                    <span
                      className={`rounded px-1 py-0.5 text-[8px] font-medium uppercase ${
                        severityBadge[issue.severity] ||
                        severityBadge.low
                      }`}
                    >
                      {issue.severity}
                    </span>
                    <div className="min-w-0">
                      <p className="text-[9px] font-medium text-[#111827]">
                        {issue.description}
                      </p>
                      {issue.suggested_fix && (
                        <p className="mt-0.5 text-[8px] text-[#059669]">
                          Fix: {issue.suggested_fix}
                        </p>
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
            <FileCode className="h-3.5 w-3.5" /> File Intelligence Engine
          </div>
          <p className="mt-1 text-2xl font-bold">File Intelligence</p>
          <p className="mt-1 text-sm text-white/80">
            Detailed analysis of every source file including health scores,
            classification, issues, and AI summaries.
          </p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {[
          { label: "Total Files", value: s.total_files, icon: FileCode, color: "text-[#2563EB]" },
          { label: "Total Lines", value: s.total_lines.toLocaleString(), icon: BarChart3, color: "text-[#059669]" },
          { label: "Code Lines", value: s.total_code_lines.toLocaleString(), icon: Code2, color: "text-[#7C3AED]" },
          { label: "Total Issues", value: s.total_issues, icon: AlertTriangle, color: "text-[#DC2626]" },
          { label: "Large Files", value: s.large_files, icon: ArrowUpDown, color: "text-[#D97706]" },
          { label: "Duplicates", value: s.duplicate_files, icon: Copy, color: "text-[#6B7280]" },
          { label: "Avg Complexity", value: s.average_complexity.toFixed(1), icon: FlaskConical, color: "text-[#6B7280]" },
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
            placeholder="Search files by name, path, language, classification, or tag..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 border-0 bg-transparent text-xs text-[#111827] placeholder-[#9CA3AF] outline-none"
          />
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium transition-colors ${
              showFilters ||
              langFilter ||
              classFilter ||
              healthFilter ||
              sortBy !== "path"
                ? "bg-[#EFF6FF] text-[#1E40AF]"
                : "text-[#6B7280] hover:bg-[#F3F4F6]"
            }`}
          >
            <Filter className="h-3 w-3" />
            Filters
          </button>
          {(langFilter || classFilter || healthFilter || search) && (
            <button
              onClick={() => {
                setSearch("");
                setLangFilter("");
                setClassFilter("");
                setHealthFilter("");
                setSortBy("path");
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
              {/* Language filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-medium text-[#6B7280]">
                  Language:
                </span>
                <select
                  value={langFilter}
                  onChange={(e) => setLangFilter(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="">All</option>
                  {languages.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
              {/* Classification filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-medium text-[#6B7280]">
                  Classification:
                </span>
                <select
                  value={classFilter}
                  onChange={(e) => setClassFilter(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="">All</option>
                  {classifications.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              {/* Health filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-medium text-[#6B7280]">
                  Health:
                </span>
                <select
                  value={healthFilter}
                  onChange={(e) => setHealthFilter(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="">All</option>
                  <option value="excellent">Excellent (80+)</option>
                  <option value="good">Good (60-79)</option>
                  <option value="fair">Fair (40-59)</option>
                  <option value="poor">Poor (&lt;40)</option>
                </select>
              </div>
              {/* Sort */}
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-medium text-[#6B7280]">
                  Sort:
                </span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[10px] text-[#374151] outline-none"
                >
                  <option value="path">Path</option>
                  <option value="name">Name</option>
                  <option value="size">Size</option>
                  <option value="complexity">Complexity</option>
                  <option value="maintainability">Maintainability</option>
                  <option value="quality">Quality</option>
                  <option value="issues">Issue Count</option>
                  <option value="modified">Last Modified</option>
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

      {/* File list */}
      <div className={sectionClass}>
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#F3F4F6]">
          <p className="text-xs font-semibold text-[#111827]">
            {filteredFiles.length} file{filteredFiles.length !== 1 ? "s" : ""}
            {filteredFiles.length !== s.total_files &&
              ` (filtered from ${s.total_files})`}
          </p>
          <div className="flex items-center gap-2 text-[10px] text-[#6B7280]">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded bg-[#EFF6FF]" /> Excellent
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded bg-[#ECFDF5]" /> Good
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded bg-[#FFFBEB]" /> Fair
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded bg-[#FEF2F2]" /> Poor
            </span>
          </div>
        </div>
        <div className="divide-y divide-[#F3F4F6] max-h-[600px] overflow-y-auto">
          {filteredFiles.length > 0 ? (
            filteredFiles.map((file) => renderDetailRow(file))
          ) : (
            <div className="flex flex-col items-center py-10 text-xs text-[#9CA3AF]">
              <FileSearch className="mb-2 h-6 w-6" />
              No files match the current filters.
            </div>
          )}
        </div>
      </div>

      {/* AI Insights */}
      {filteredFiles
        .filter((f) => f.ai_summary)
        .slice(0, 6)
        .length > 0 && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            File AI Summaries
          </p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {filteredFiles
              .filter((f) => f.ai_summary)
              .slice(0, 6)
              .map((file) => (
                <div
                  key={file.path}
                  className="flex gap-3 rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3"
                >
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[#EFF6FF]">
                    <FileCode className="h-3.5 w-3.5 text-[#2563EB]" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-[#111827]">
                      {file.file_name}
                    </p>
                    <p className="mt-0.5 text-[10px] text-[#6B7280]">
                      {file.ai_summary}
                    </p>
                    <div className="mt-1 flex gap-1">
                      <span
                        className={
                          classificationColors[file.classification] ||
                          "rounded bg-[#F3F4F6] px-1 py-0.5 text-[8px] text-[#374151]"
                        }
                      >
                        {file.classification}
                      </span>
                      {file.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="rounded bg-[#F3F4F6] px-1 py-0.5 text-[8px] text-[#374151]"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Issue Summary */}
      {s.total_issues > 0 && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Issue Summary
          </p>
          <div className="grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3">
              <p className="text-lg font-bold text-[#111827]">
                {s.large_files}
              </p>
              <p className="text-[10px] text-[#6B7280]">Large Files (&gt;500 lines)</p>
            </div>
            <div className="rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3">
              <p className="text-lg font-bold text-[#111827]">
                {s.empty_files}
              </p>
              <p className="text-[10px] text-[#6B7280]">Empty Files</p>
            </div>
            <div className="rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3">
              <p className="text-lg font-bold text-[#111827]">
                {s.duplicate_files}
              </p>
              <p className="text-[10px] text-[#6B7280]">Duplicate Files</p>
            </div>
            <div className="rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3">
              <p className="text-lg font-bold text-[#111827]">
                {s.total_issues}
              </p>
              <p className="text-[10px] text-[#6B7280]">Total Issues Across All Files</p>
            </div>
          </div>
        </div>
      )}

      {/* Related */}
      {projectId && (
        <RelatedAnalysisNav projectId={projectId} currentPage="file-intelligence" />
      )}
    </motion.div>
  );
}
