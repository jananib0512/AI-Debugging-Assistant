import { useEffect, useRef, useState, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Bug,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronsUpDown,
  FileCode,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { getSyntaxDetection } from "@/lib/project-analyzer";
import type { SyntaxDetectionResponse, SyntaxErrorInfo } from "@/types/project-analyzer";
import { Card, CardContent } from "@/components/ui/card";

const severityColor = (s: string) => {
  switch (s) {
    case "Critical": return "text-white bg-[#DC2626]";
    case "High": return "text-white bg-[#EA580C]";
    case "Medium": return "text-[#111827] bg-[#F59E0B]";
    default: return "text-[#111827] bg-[#F3F4F6]";
  }
};

export function SyntaxDetectionResults() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<SyntaxDetectionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [languageFilter, setLanguageFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [selectedBug, setSelectedBug] = useState<SyntaxErrorInfo | null>(null);
  const [sortField, setSortField] = useState<string>("severity");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const fetchedRef = useRef(false);

  const fetchData = () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    getSyntaxDetection(Number(projectId))
      .then((res) => {
        setData(res);
        fetchedRef.current = true;
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to load syntax detection results";
        setError(msg);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId]);

  const allBugs = useMemo(() => {
    if (!data) return [];
    const bugs: SyntaxErrorInfo[] = [];
    for (const r of data.results) {
      for (const e of r.errors) {
        bugs.push(e);
      }
    }
    return bugs;
  }, [data]);

  const languages = useMemo(() => {
    const s = new Set(allBugs.map((b) => b.language));
    return Array.from(s).sort();
  }, [allBugs]);

  const types = useMemo(() => {
    const s = new Set(allBugs.map((b) => b.error_type));
    return Array.from(s).sort();
  }, [allBugs]);

  const filteredBugs = useMemo(() => {
    let bugs = [...allBugs];

    if (search) {
      const q = search.toLowerCase();
      bugs = bugs.filter(
        (b) =>
          b.bug_title.toLowerCase().includes(q) ||
          b.affected_file.toLowerCase().includes(q) ||
          b.language.toLowerCase().includes(q) ||
          b.severity.toLowerCase().includes(q) ||
          b.description.toLowerCase().includes(q),
      );
    }

    if (severityFilter !== "all") {
      bugs = bugs.filter((b) => b.severity === severityFilter);
    }
    if (languageFilter !== "all") {
      bugs = bugs.filter((b) => b.language === languageFilter);
    }
    if (typeFilter !== "all") {
      bugs = bugs.filter((b) => b.error_type === typeFilter);
    }

    bugs.sort((a, b) => {
      const sevOrder: Record<string, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };
      let cmp = (sevOrder[a.severity] ?? 0) - (sevOrder[b.severity] ?? 0);
      if (sortField === "file") cmp = a.affected_file.localeCompare(b.affected_file);
      if (sortField === "bug") cmp = a.bug_title.localeCompare(b.bug_title);
      if (sortField === "language") cmp = a.language.localeCompare(b.language);
      return sortDir === "desc" ? -cmp : cmp;
    });

    return bugs;
  }, [allBugs, search, severityFilter, languageFilter, typeFilter, sortField, sortDir]);

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir(field === "severity" ? "desc" : "asc");
    }
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (sortField !== field) return <ChevronsUpDown className="ml-1 h-3 w-3" />;
    return sortDir === "asc" ? <ChevronUp className="ml-1 h-3 w-3" /> : <ChevronDown className="ml-1 h-3 w-3" />;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative mb-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        </div>
        <p className="text-sm font-medium text-[#111827]">Running Syntax Analysis...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Inspecting source files for syntax and compilation issues.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
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
      <div className="flex flex-col items-center justify-center py-20">
        <Bug className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No data available</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run bug detection first to see syntax analysis results.</p>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto max-w-6xl space-y-6">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#111827]">Syntax & Compilation Analysis</h1>
          <p className="mt-1 text-sm text-[#6B7280]">
            {data.project_name} — {data.scanned_languages.join(", ") || data.language}
          </p>
        </div>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB] transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Re-run
        </button>
      </div>

      {/* ── AI Summary ── */}
      <Card hover={false}>
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">AI Summary</p>
              <p className="text-sm leading-relaxed text-[#374151]">{data.summary}</p>
            </div>
            <div className="flex items-center gap-3 shrink-0 ml-6">
              <div className="text-center">
                <p className="text-lg font-bold text-[#111827]">{data.total_files_scanned}</p>
                <p className="text-[10px] text-[#6B7280]">Files Scanned</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-[#111827]">{data.files_with_errors}</p>
                <p className="text-[10px] text-[#6B7280]">Files with Issues</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-[#111827]">{data.total_errors}</p>
                <p className="text-[10px] text-[#6B7280]">Total Issues</p>
              </div>
            </div>
          </div>
          {data.total_errors > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {data.critical_count > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-[#FEF2F2] px-3 py-1 text-xs font-medium text-[#DC2626]">
                  <span className="h-2 w-2 rounded-full bg-[#DC2626]" /> {data.critical_count} Critical
                </span>
              )}
              {data.high_count > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-[#FFF7ED] px-3 py-1 text-xs font-medium text-[#EA580C]">
                  <span className="h-2 w-2 rounded-full bg-[#EA580C]" /> {data.high_count} High
                </span>
              )}
              {data.medium_count > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-[#FFFBEB] px-3 py-1 text-xs font-medium text-[#D97706]">
                  <span className="h-2 w-2 rounded-full bg-[#F59E0B]" /> {data.medium_count} Medium
                </span>
              )}
              {data.low_count > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-[#F3F4F6] px-3 py-1 text-xs font-medium text-[#6B7280]">
                  <span className="h-2 w-2 rounded-full bg-[#9CA3AF]" /> {data.low_count} Low
                </span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Search & Filters ── */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[240px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Search by bug, file, language, severity..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-[#E5E7EB] bg-white py-2 pl-9 pr-8 text-xs text-[#111827] placeholder-[#9CA3AF] outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
          />
          {search && (
            <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280]">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs text-[#374151] outline-none focus:border-[#2563EB]"
        >
          <option value="all">All Severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <select
          value={languageFilter}
          onChange={(e) => setLanguageFilter(e.target.value)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs text-[#374151] outline-none focus:border-[#2563EB]"
        >
          <option value="all">All Languages</option>
          {languages.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs text-[#374151] outline-none focus:border-[#2563EB]"
        >
          <option value="all">All Types</option>
          {types.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* ── Bug List Table ── */}
      <div className="overflow-hidden rounded-lg border border-[#E5E7EB]">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-[#F9FAFB] text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">
              <th className="px-4 py-3 cursor-pointer select-none hover:text-[#111827]" onClick={() => toggleSort("severity")}>
                <span className="inline-flex items-center">Severity <SortIcon field="severity" /></span>
              </th>
              <th className="px-4 py-3 cursor-pointer select-none hover:text-[#111827]" onClick={() => toggleSort("bug")}>
                <span className="inline-flex items-center">Bug <SortIcon field="bug" /></span>
              </th>
              <th className="px-4 py-3 cursor-pointer select-none hover:text-[#111827]" onClick={() => toggleSort("file")}>
                <span className="inline-flex items-center">File <SortIcon field="file" /></span>
              </th>
              <th className="px-4 py-3">Line</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredBugs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-xs text-[#6B7280]">
                  {search || severityFilter !== "all" || languageFilter !== "all" || typeFilter !== "all"
                    ? "No issues match your filters."
                    : "No syntax issues detected. Your project looks clean."}
                </td>
              </tr>
            ) : (
              filteredBugs.map((bug, idx) => (
                <tr
                  key={`${bug.affected_file}-${bug.line_number}-${bug.column_number}-${idx}`}
                  className="border-t border-[#E5E7EB] transition-colors hover:bg-[#F9FAFB]"
                >
                  <td className="px-4 py-3">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${severityColor(bug.severity)}`}>
                      {bug.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-xs font-medium text-[#111827]">{bug.bug_title}</p>
                    <p className="text-[10px] text-[#6B7280] truncate max-w-[280px]">{bug.description}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 text-xs text-[#6B7280]">
                      <FileCode className="h-3 w-3" />
                      {bug.affected_file}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-[#6B7280]">{bug.line_number}:{bug.column_number}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-[#DC2626]">Unresolved</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setSelectedBug(selectedBug === bug ? null : bug)}
                      className="rounded-md border border-[#E5E7EB] bg-white px-3 py-1.5 text-[10px] font-medium text-[#2563EB] hover:bg-[#EFF6FF] transition-colors"
                    >
                      {selectedBug === bug ? "Close" : "View Details"}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Bug Detail ── */}
      {selectedBug && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <Card hover={false}>
            <CardContent className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${severityColor(selectedBug.severity)}`}>
                      {selectedBug.severity}
                    </span>
                    <span className="text-xs text-[#6B7280]">{selectedBug.language}</span>
                    <span className="text-xs text-[#6B7280]">·</span>
                    <span className="text-xs text-[#6B7280]">{selectedBug.affected_file}:{selectedBug.line_number}</span>
                    <span className="text-xs text-[#6B7280]">·</span>
                    <span className="text-xs text-[#6B7280]">Confidence: {selectedBug.confidence}%</span>
                  </div>
                  <h3 className="mt-2 text-base font-semibold text-[#111827]">{selectedBug.bug_title}</h3>
                  <p className="mt-1 text-sm text-[#6B7280]">{selectedBug.description}</p>
                </div>
                <button
                  onClick={() => setSelectedBug(null)}
                  className="rounded-lg border border-[#E5E7EB] bg-white p-1.5 text-[#9CA3AF] hover:text-[#6B7280] transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">AI Explanation</p>
                  <div className="rounded-lg bg-[#F9FAFB] p-3">
                    <p className="text-xs leading-relaxed text-[#374151]">{selectedBug.ai_explanation}</p>
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Suggested Fix</p>
                  <div className="rounded-lg bg-[#EFF6FF] p-3">
                    <p className="text-xs leading-relaxed text-[#2563EB]">{selectedBug.suggested_fix}</p>
                  </div>
                </div>
              </div>

              {selectedBug.code_snippet && (
                <div className="mt-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Source Code</p>
                  <pre className="overflow-x-auto rounded-lg bg-[#111827] p-3 text-xs leading-relaxed text-[#E5E7EB]">
                    <code>{selectedBug.code_snippet}</code>
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Navigation ── */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={() => navigate(`/projects/${projectId}/bug-detection`)}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-[#6B7280] hover:text-[#111827] transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous: Bug Detection
        </button>
        <span className="text-xs text-[#9CA3AF]">Syntax & Compilation Analysis</span>
        <button
          disabled
          className="inline-flex items-center gap-1.5 rounded-lg bg-[#E5E7EB] px-5 py-2.5 text-sm font-medium text-[#9CA3AF] cursor-not-allowed"
        >
          Next: Static Code Analysis
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

    </motion.div>
  );
}
