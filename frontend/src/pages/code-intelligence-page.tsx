import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Award,
  BarChart3,
  BookOpen,
  ChevronDown,
  ChevronRight,
  ChevronsUpDown,
  Code,
  Download,
  FileCode,
  FileText,
  Filter,
  FolderKanban,
  GitBranch,
  Layers,
  Package,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { getCodeIntelligence } from "@/lib/project-analyzer";
import type {
  SourceCodeIntelligenceResponse,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

type SortKey = "path" | "language" | "lines_of_code" | "total_lines" | "complexity" | "maintainability_score" | "functions" | "classes" | "imports";
type SortDir = "asc" | "desc";
type FilterLang = string | "all";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.03 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

const statCardClass = "rounded-xl border border-[#E5E7EB] bg-white p-4";
const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

function StatCard({ label, value, sub, icon: Icon, color }: { label: string; value: string | number; sub?: string; icon?: React.ElementType; color?: string }) {
  return (
    <div className={statCardClass}>
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">{label}</p>
        {Icon && <Icon className="h-4 w-4" style={{ color: color || "#9CA3AF" }} />}
      </div>
      <p className="mt-1 text-lg font-bold text-[#111827]">{value}</p>
      {sub && <p className="text-xs text-[#6B7280]">{sub}</p>}
    </div>
  );
}

function formatFileSize(lines: number, _total: number): string {
  if (lines >= 1000) return `${(lines / 1000).toFixed(1)}k`;
  return `${lines}`;
}

export function CodeIntelligencePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<SourceCodeIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("path");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [filterLang, setFilterLang] = useState<FilterLang>("all");
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getCodeIntelligence(Number(projectId));
      setData(result);
      fetchedRef.current = true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load code intelligence");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const summary = data?.summary;
  const files = data?.files || [];
  const classes = data?.classes || [];
  const functions = data?.functions || [];
  const imports = data?.imports || [];
  const enums = data?.enums || [];
  const interfaces = data?.interfaces || [];
  const modules = data?.modules || [];

  const languages = useMemo(() => {
    const set = new Set(files.map((f) => f.language));
    return Array.from(set).sort();
  }, [files]);

  const filteredFiles = useMemo(() => {
    let result = [...files];
    if (search) {
      const q = search.toLowerCase();
      result = result.filter((f) => f.path.toLowerCase().includes(q));
    }
    if (filterLang !== "all") {
      result = result.filter((f) => f.language === filterLang);
    }
    result.sort((a, b) => {
      const aVal = a[sortKey] ?? 0;
      const bVal = b[sortKey] ?? 0;
      if (typeof aVal === "string") {
        return sortDir === "asc" ? aVal.localeCompare(bVal as string) : (bVal as string).localeCompare(aVal);
      }
      return sortDir === "asc" ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });
    return result;
  }, [files, search, filterLang, sortKey, sortDir]);

  const toggleFile = (path: string) => {
    setExpandedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const exportCSV = useCallback(() => {
    const headers = ["Path", "Language", "Lines of Code", "Total Lines", "Comments", "Blank", "Functions", "Classes", "Imports", "Complexity", "Maintainability"];
    const rows = filteredFiles.map((f) =>
      [f.path, f.language, f.lines_of_code, f.total_lines, f.comment_lines, f.blank_lines, f.functions, f.classes, f.imports, f.complexity, f.maintainability_score].join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `code-intelligence-${projectId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredFiles, projectId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#111827]">Analyzing source code...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Parsing classes, functions, imports, and metrics.</p>
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

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <FileCode className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No code intelligence data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Upload and extract a project to begin analysis.</p>
      </div>
    );
  }

  const SortHeader = ({ label, sortKey: sk, className }: { label: string; sortKey: SortKey; className?: string }) => (
    <button onClick={() => toggleSort(sk)} className={`inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF] hover:text-[#6B7280] ${className || ""}`}>
      {label}
      <ChevronsUpDown className="h-3 w-3" />
    </button>
  );

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">

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
      <motion.div variants={itemVariants} className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#059669] to-[#047857] p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-[#A7F3D0]">Code Intelligence</p>
            <h1 className="mt-1 text-2xl font-bold">Source Code Analysis</h1>
            <p className="mt-1 text-sm text-[#A7F3D0]">{summary?.total_files || 0} files across {languages.length} languages</p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`/projects/${projectId}/analyzer/code-quality`}
              className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm hover:bg-white/30"
            >
              <Award className="h-3.5 w-3.5" /> View Quality
            </Link>
            <button onClick={exportCSV} className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm hover:bg-white/30">
              <Download className="h-3.5 w-3.5" /> Export CSV
            </button>
            <button onClick={fetchData} className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm hover:bg-white/30">
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
          </div>
        </div>
      </motion.div>

      {/* Summary Stat Cards */}
      <motion.div variants={itemVariants}>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Code Summary</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-7 2xl:grid-cols-9">
          <StatCard label="Total Files" value={summary?.total_files ?? 0} icon={FileCode} color="#2563EB" />
          <StatCard label="Total Classes" value={summary?.total_classes ?? 0} icon={Layers} color="#7C3AED" />
          <StatCard label="Total Functions" value={summary?.total_functions ?? 0} icon={GitBranch} color="#059669" />
          <StatCard label="Total Imports" value={summary?.total_imports ?? 0} sub={`${summary?.total_external_imports ?? 0} external`} icon={Package} color="#D97706" />
          <StatCard label="Total Enums" value={summary?.total_enums ?? 0} icon={BarChart3} color="#0891B2" />
          <StatCard label="Total Interfaces" value={summary?.total_interfaces ?? 0} icon={BookOpen} color="#DC2626" />
          <StatCard label="Total Variables" value={summary?.total_variables ?? 0} sub={`${summary?.total_constants ?? 0} constants`} icon={Code} color="#4F46E5" />
          <StatCard label="Total Modules" value={summary?.total_modules ?? 0} icon={FolderKanban} color="#EA580C" />
          <StatCard label="Languages" value={languages.length} sub={languages.slice(0, 3).join(", ")} icon={FileText} color="#6B7280" />
        </div>
      </motion.div>

      {/* Metrics Grid */}
      <motion.div variants={itemVariants}>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Code Metrics</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8">
          <StatCard label="Total Comments" value={summary?.total_comments ?? 0} icon={BookOpen} color="#2563EB" />
          <StatCard label="Blank Lines" value={summary?.total_blank_lines ?? 0} icon={Code} color="#6B7280" />
          <StatCard label="Empty Files" value={summary?.total_empty_files ?? 0} icon={FileText} color="#DC2626" />
          <StatCard label="Duplicate Files" value={summary?.total_duplicate_files ?? 0} icon={FileCode} color="#D97706" />
          <StatCard label="Avg File Size" value={summary?.average_file_size ?? 0} sub="lines/file" icon={BarChart3} color="#059669" />
          <StatCard label="Avg LOC" value={summary?.average_lines_of_code ?? 0} sub="lines of code" icon={GitBranch} color="#7C3AED" />
          <StatCard label="Avg Complexity" value={summary?.average_complexity ?? 0} sub="cyclomatic" icon={AlertTriangle} color="#EA580C" />
          <StatCard label="Avg Maintainability" value={`${summary?.average_maintainability ?? 0}%`} icon={BarChart3} color="#0891B2" />
        </div>
      </motion.div>

      {/* Largest/Smallest */}
      <motion.div variants={itemVariants} className="grid gap-4 sm:grid-cols-2">
        {summary?.largest_file && (
          <div className={sectionClass + " p-5"}>
            <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Largest File</p>
            <p className="mt-1 text-sm font-medium text-[#111827] truncate">{summary.largest_file}</p>
            <p className="text-xs text-[#6B7280]">{summary.largest_file_size} lines</p>
          </div>
        )}
        {summary?.smallest_file && (
          <div className={sectionClass + " p-5"}>
            <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Smallest File</p>
            <p className="mt-1 text-sm font-medium text-[#111827] truncate">{summary.smallest_file}</p>
            <p className="text-xs text-[#6B7280]">{summary.smallest_file_size} lines</p>
          </div>
        )}
      </motion.div>

      {/* Files Table — scrollable inside fixed-height container */}
      <motion.div variants={itemVariants} className={sectionClass + " overflow-hidden"}>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#E5E7EB] px-5 py-3">
          <p className="text-sm font-semibold text-[#111827]">Source Files</p>
          <div className="flex items-center gap-3">
            <span className="text-xs text-[#6B7280]">{filteredFiles.length} of {files.length} files</span>
            <button onClick={exportCSV} className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 py-1.5 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
              <Download className="h-3.5 w-3.5" /> CSV
            </button>
          </div>
        </div>

        {/* Search + Filter */}
        <div className="border-b border-[#E5E7EB] px-5 py-2.5">
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9CA3AF]" />
              <input
                type="text"
                placeholder="Search files..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-lg border border-[#E5E7EB] bg-white py-1.5 pl-9 pr-3 text-xs text-[#111827] placeholder:text-[#9CA3AF] focus:border-[#2563EB] focus:outline-none"
              />
              {search && <X className="absolute right-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#9CA3AF] cursor-pointer hover:text-[#6B7280]" onClick={() => setSearch("")} />}
            </div>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#9CA3AF]" />
              <select
                value={filterLang}
                onChange={(e) => setFilterLang(e.target.value as FilterLang)}
                className="appearance-none rounded-lg border border-[#E5E7EB] bg-white py-1.5 pl-9 pr-7 text-xs text-[#374151] focus:border-[#2563EB] focus:outline-none"
              >
                <option value="all">All Languages</option>
                {languages.map((lang) => <option key={lang} value={lang}>{lang}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Scrollable Table Container */}
        <div
          className="overflow-auto"
          style={{ maxHeight: 'min(70vh, 700px)' }}
        >
          <table className="w-full text-xs">
            <thead className="sticky top-0 z-20">
              <tr className="bg-[#F9FAFB]">
                <th className="sticky left-0 z-30 bg-[#F9FAFB] px-5 py-2.5 text-left w-8"></th>
                <th className="sticky left-8 z-30 bg-[#F9FAFB] px-2 py-2.5 text-left"><SortHeader label="Path" sortKey="path" /></th>
                <th className="px-2 py-2.5 text-left"><SortHeader label="Language" sortKey="language" /></th>
                <th className="px-2 py-2.5 text-right"><SortHeader label="LOC" sortKey="lines_of_code" /></th>
                <th className="px-2 py-2.5 text-right"><SortHeader label="Lines" sortKey="total_lines" /></th>
                <th className="px-2 py-2.5 text-right hidden md:table-cell"><SortHeader label="Complexity" sortKey="complexity" /></th>
                <th className="px-2 py-2.5 text-right hidden md:table-cell"><SortHeader label="Maintainability" sortKey="maintainability_score" /></th>
                <th className="px-2 py-2.5 text-right hidden lg:table-cell"><SortHeader label="Funcs" sortKey="functions" /></th>
                <th className="px-2 py-2.5 text-right hidden lg:table-cell"><SortHeader label="Classes" sortKey="classes" /></th>
                <th className="px-2 py-2.5 text-right hidden xl:table-cell"><SortHeader label="Imports" sortKey="imports" /></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F3F4F6]">
              {filteredFiles.map((file, idx) => {
                const isExpanded = expandedFiles.has(file.path);
                const fileClasses = classes.filter((c) => c.file_path === file.path);
                const fileFunctions = functions.filter((f) => f.file_path === file.path && !f.parent_class);
                const fileImports = imports.filter((i) => (i as any).file_path === file.path);
                const hasDetails = fileClasses.length > 0 || fileFunctions.length > 0 || fileImports.length > 0;
                const isEven = idx % 2 === 0;
                return (
                  <tr key={file.path} className={`group ${isEven ? 'bg-white' : 'bg-[#F9FAFB]'} hover:bg-[#EEF2FF] transition-colors`}>
                    <td className={`sticky left-0 z-10 ${isEven ? 'bg-white' : 'bg-[#F9FAFB]'} group-hover:bg-[#EEF2FF] px-5 py-3`}>
                      {hasDetails && (
                        <button onClick={() => toggleFile(file.path)} className="text-[#9CA3AF] hover:text-[#6B7280]">
                          {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                        </button>
                      )}
                    </td>
                    <td className={`sticky left-8 z-10 ${isEven ? 'bg-white' : 'bg-[#F9FAFB]'} group-hover:bg-[#EEF2FF] px-2 py-3 max-w-[300px] truncate font-medium text-[#111827]`}>{file.path}</td>
                    <td className="px-2 py-3">
                      <span className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#374151]">{file.language}</span>
                    </td>
                    <td className="px-2 py-3 text-right text-[#374151]">{file.lines_of_code}</td>
                    <td className="px-2 py-3 text-right text-[#6B7280]">{file.total_lines}</td>
                    <td className="px-2 py-3 text-right hidden md:table-cell">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                        file.complexity <= 5 ? "bg-[#ECFDF5] text-[#065F46]" :
                        file.complexity <= 15 ? "bg-[#FFFBEB] text-[#92400E]" :
                        "bg-[#FEF2F2] text-[#991B1B]"
                      }`}>{file.complexity}</span>
                    </td>
                    <td className="px-2 py-3 text-right hidden md:table-cell">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                        file.maintainability_score >= 70 ? "bg-[#ECFDF5] text-[#065F46]" :
                        file.maintainability_score >= 40 ? "bg-[#FFFBEB] text-[#92400E]" :
                        "bg-[#FEF2F2] text-[#991B1B]"
                      }`}>{file.maintainability_score}%</span>
                    </td>
                    <td className="px-2 py-3 text-right hidden lg:table-cell text-[#6B7280]">{file.functions}</td>
                    <td className="px-2 py-3 text-right hidden lg:table-cell text-[#6B7280]">{file.classes}</td>
                    <td className="px-2 py-3 text-right hidden xl:table-cell text-[#6B7280]">{file.imports}</td>
                  </tr>
                );
              })}
              {filteredFiles.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-5 py-10 text-center text-sm text-[#6B7280]">No files match your filter criteria.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Classes */}
      {classes.length > 0 && (
        <motion.div variants={itemVariants} className={sectionClass}>
          <div className="border-b border-[#E5E7EB] px-5 py-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-[#111827]">Classes ({classes.length})</p>
          </div>
          <div className="divide-y divide-[#F3F4F6] max-h-[400px] overflow-y-auto">
            {classes.map((cls, i) => (
              <div key={i} className="px-5 py-2.5 flex items-center justify-between hover:bg-[#F9FAFB]">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[10px] font-mono text-[#7C3AED]">class</span>
                  <span className="text-sm font-medium text-[#111827]">{cls.name}</span>
                  {cls.base_classes.length > 0 && <span className="text-xs text-[#6B7280]">extends {cls.base_classes.join(", ")}</span>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {cls.is_abstract && <span className="text-[10px] text-[#D97706]">abstract</span>}
                  <span className="text-[10px] text-[#6B7280]">{cls.methods.length} methods</span>
                  <span className="text-[10px] text-[#6B7280] hidden md:inline">{cls.file_path}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Functions */}
      {functions.length > 0 && (
        <motion.div variants={itemVariants} className={sectionClass}>
          <div className="border-b border-[#E5E7EB] px-5 py-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-[#111827]">Functions ({functions.length})</p>
          </div>
          <div className="divide-y divide-[#F3F4F6] max-h-[400px] overflow-y-auto">
            {functions.slice(0, 100).map((fn, i) => (
              <div key={i} className="px-5 py-2.5 flex items-center justify-between hover:bg-[#F9FAFB]">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[10px] font-mono text-[#059669]">fn</span>
                  <span className="text-sm font-medium text-[#111827]">{fn.name}</span>
                  {fn.return_type && <span className="text-xs text-[#6B7280]">→ {fn.return_type}</span>}
                  {fn.parent_class && <span className="text-xs text-[#7C3AED]">{fn.parent_class}::</span>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {fn.is_async && <span className="text-[10px] text-[#2563EB]">async</span>}
                  {fn.is_static && <span className="text-[10px] text-[#D97706]">static</span>}
                  <span className="text-[10px] text-[#6B7280]">{fn.parameters.length} params</span>
                </div>
              </div>
            ))}
            {functions.length > 100 && (
              <div className="px-5 py-3 text-center text-xs text-[#6B7280]">Showing 100 of {functions.length} functions</div>
            )}
          </div>
        </motion.div>
      )}

      {/* Imports */}
      {imports.length > 0 && (
        <motion.div variants={itemVariants} className={sectionClass}>
          <div className="border-b border-[#E5E7EB] px-5 py-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-[#111827]">Imports ({imports.length})</p>
          </div>
          <div className="divide-y divide-[#F3F4F6] max-h-[300px] overflow-y-auto">
            {imports.slice(0, 100).map((imp, i) => (
              <div key={i} className="px-5 py-2 flex items-center justify-between hover:bg-[#F9FAFB]">
                <div className="flex items-center gap-2 min-w-0">
                  <Package className="h-3.5 w-3.5 shrink-0 text-[#6B7280]" />
                  <span className="text-sm text-[#374151]">{imp.source || "(unnamed)"}</span>
                  {imp.names.length > 0 && <span className="text-xs text-[#6B7280]">→ {imp.names.slice(0, 3).join(", ")}{imp.names.length > 3 ? "..." : ""}</span>}
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {imp.is_external && <span className="rounded bg-[#FFFBEB] px-1.5 py-0.5 text-[10px] text-[#92400E]">external</span>}
                  {imp.is_duplicate && <span className="rounded bg-[#FEF2F2] px-1.5 py-0.5 text-[10px] text-[#991B1B]">duplicate</span>}
                </div>
              </div>
            ))}
            {imports.length > 100 && (
              <div className="px-5 py-3 text-center text-xs text-[#6B7280]">Showing 100 of {imports.length} imports</div>
            )}
          </div>
        </motion.div>
      )}

      {/* Enums & Interfaces */}
      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2">
        {enums.length > 0 && (
          <div className={sectionClass}>
            <div className="border-b border-[#E5E7EB] px-5 py-3">
              <p className="text-sm font-semibold text-[#111827]">Enums ({enums.length})</p>
            </div>
            <div className="divide-y divide-[#F3F4F6] max-h-[250px] overflow-y-auto">
              {enums.map((e, i) => (
                <div key={i} className="px-5 py-2 flex items-center justify-between text-sm hover:bg-[#F9FAFB]">
                  <span className="font-medium text-[#111827]">{e.name}</span>
                  <span className="text-xs text-[#6B7280]">{e.values.length} values</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {interfaces.length > 0 && (
          <div className={sectionClass}>
            <div className="border-b border-[#E5E7EB] px-5 py-3">
              <p className="text-sm font-semibold text-[#111827]">Interfaces ({interfaces.length})</p>
            </div>
            <div className="divide-y divide-[#F3F4F6] max-h-[250px] overflow-y-auto">
              {interfaces.map((inf, i) => (
                <div key={i} className="px-5 py-2 flex items-center justify-between text-sm hover:bg-[#F9FAFB]">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-medium text-[#111827]">{inf.name}</span>
                    <span className="text-xs text-[#6B7280]">{inf.properties.length} props, {inf.methods.length} methods</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      {/* Modules */}
      {modules.length > 0 && (
        <motion.div variants={itemVariants} className={sectionClass}>
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Modules ({modules.length})</p>
          </div>
          <div className="divide-y divide-[#F3F4F6] max-h-[400px] overflow-y-auto">
            {modules.map((mod, i) => (
              <div key={i} className="px-5 py-3 hover:bg-[#F9FAFB]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FolderKanban className="h-4 w-4 text-[#F59E0B]" />
                    <span className="text-sm font-medium text-[#111827]">{mod.name === "." ? "(root)" : mod.name}</span>
                  </div>
                  <span className="text-xs text-[#6B7280]">{mod.files.length} files</span>
                </div>
                {mod.submodules.length > 0 && (
                  <div className="mt-1 ml-6 flex flex-wrap gap-1">
                    {mod.submodules.map((sub, j) => <span key={j} className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[10px] text-[#374151]">{sub}</span>)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Language Distribution Bar Chart */}
      {languages.length > 0 && (
        <motion.div variants={itemVariants} className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">Language Distribution</p>
          <div className="space-y-2">
            {languages.map((lang) => {
              const langFiles = files.filter((f) => f.language === lang);
              const langLoc = langFiles.reduce((s, f) => s + f.lines_of_code, 0);
              const maxLoc = Math.max(...languages.map((l) => files.filter((f) => f.language === l).reduce((s, f) => s + f.lines_of_code, 0)), 1);
              const pct = (langLoc / maxLoc) * 100;
              return (
                <div key={lang} className="flex items-center gap-3">
                  <span className="w-24 text-xs font-medium text-[#374151]">{lang}</span>
                  <div className="flex-1 h-3 rounded-full bg-[#F3F4F6] overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-[#2563EB] to-[#7C3AED]" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="w-16 text-right text-xs text-[#6B7280]">{langFiles.length} files</span>
                  <span className="w-16 text-right text-xs text-[#6B7280]">{formatFileSize(langLoc, 0)} LOC</span>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {projectId && <RelatedAnalysisNav projectId={projectId} currentPage="code-intelligence" />}

    </motion.div>
  );
}
