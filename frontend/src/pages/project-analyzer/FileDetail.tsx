import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  FileCode,
  RefreshCw,
} from "lucide-react";
import { getFileAnalysis } from "@/lib/project-analyzer";
import type { FileAnalysisDetail } from "@/types/project-analyzer";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const healthColor: Record<string, string> = {
  Excellent: "bg-[#ECFDF5] text-[#065F46]",
  Good: "bg-[#EFF6FF] text-[#1E40AF]",
  Fair: "bg-[#FFFBEB] text-[#92400E]",
  "Needs Improvement": "bg-[#FFF7ED] text-[#9A3412]",
  Poor: "bg-[#FEF2F2] text-[#991B1B]",
};

const severityDot: Record<string, string> = {
  critical: "bg-[#DC2626]",
  high: "bg-[#EA580C]",
  medium: "bg-[#D97706]",
  low: "bg-[#6B7280]",
};

const issueBadgeBg: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B]",
  high: "bg-[#FFF7ED] text-[#9A3412]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
};

const priorityBg: Record<string, string> = {
  high: "bg-[#FEF2F2] text-[#991B1B]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
};

export function FileDetail() {
  const { projectId, filePath } = useParams<{ projectId: string; filePath: string }>();
  const navigate = useNavigate();
  const decodedPath = filePath ? decodeURIComponent(filePath) : "";
  const [file, setFile] = useState<FileAnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set());
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getFileAnalysis(Number(projectId));
      const found = result.files.find((f) => f.path === decodedPath);
      if (found) {
        setFile(found);
      } else {
        setError(`File "${decodedPath}" not found in analysis results.`);
      }
      fetchedRef.current = true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load file analysis");
    } finally {
      setLoading(false);
    }
  }, [projectId, decodedPath]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const toggleIssue = (idx: number) => {
    setExpandedIssues((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Loading file details...</p>
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

  if (!file) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <FileCode className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">File not found</p>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer/file-analysis`)}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to File Analysis
          </button>
          <p className="mt-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">File Detail</p>
          <h1 className="mt-0.5 text-xl font-bold text-[#111827]">{file.file_name}</h1>
        </div>
      </div>

      {/* File metadata */}
      <div className={sectionClass + " p-5"}>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Path</p><p className="text-xs text-[#374151] break-all">{file.path}</p></div>
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Language</p><p className="text-xs font-medium text-[#374151]">{file.language}</p></div>
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Extension</p><p className="text-xs text-[#374151]">{file.extension}</p></div>
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Size</p><p className="text-xs text-[#374151]">{(file.size / 1024).toFixed(1)} KB</p></div>
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Health</p><span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${healthColor[file.health] || "bg-[#F3F4F6] text-[#374151]"}`}>{file.health}</span></div>
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Tags</p><div className="flex flex-wrap gap-1">{file.tags.map((t) => <span key={t} className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#6B7280]">{t}</span>)}</div></div>
        </div>
      </div>

      {/* Score gauges */}
      <div className={sectionClass + " p-5"}>
        <p className="mb-3 text-sm font-semibold text-[#111827]">Quality Scores</p>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-6">
          {(["overall", "maintainability", "complexity", "readability", "documentation", "security"] as const).map((k) => {
            const val = file.scores[k];
            const color = val >= 80 ? "#059669" : val >= 60 ? "#D97706" : val >= 40 ? "#EA580C" : "#DC2626";
            return (
              <div key={k} className="flex flex-col items-center rounded-lg border border-[#E5E7EB] bg-white p-3">
                <svg width={72} height={72} className="-rotate-90">
                  <circle cx={36} cy={36} r={30} fill="none" stroke="#F3F4F6" strokeWidth={5} />
                  <circle cx={36} cy={36} r={30} fill="none" stroke={color} strokeWidth={5}
                    strokeDasharray={2 * Math.PI * 30} strokeDashoffset={2 * Math.PI * 30 * (1 - val / 100)}
                    strokeLinecap="round" className="transition-all duration-700" />
                </svg>
                <span className="mt-1 text-sm font-bold text-[#111827]">{Math.round(val)}</span>
                <span className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF] text-center">{k}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Metrics */}
      <div className={sectionClass + " p-5"}>
        <p className="mb-3 text-sm font-semibold text-[#111827]">Metrics</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Total Lines</p><p className="text-sm font-bold text-[#111827]">{file.total_lines}</p></div>
          <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Code Lines</p><p className="text-sm font-bold text-[#111827]">{file.code_lines}</p></div>
          <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Blank Lines</p><p className="text-sm font-bold text-[#111827]">{file.blank_lines}</p></div>
          <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Comment Lines</p><p className="text-sm font-bold text-[#111827]">{file.comment_lines}</p></div>
          <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Functions</p><p className="text-sm font-bold text-[#111827]">{file.functions}</p></div>
          <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Classes</p><p className="text-sm font-bold text-[#111827]">{file.classes}</p></div>
          <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Imports</p><p className="text-sm font-bold text-[#111827]">{file.imports}</p></div>
          <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Cyclomatic Complexity</p><p className="text-sm font-bold text-[#111827]">{file.complexity}</p></div>
        </div>
      </div>

      {/* AI Summary */}
      <div className={sectionClass + " p-5"}>
        <p className="mb-2 text-sm font-semibold text-[#111827]">AI Summary</p>
        <p className="text-sm text-[#374151] leading-relaxed">{file.ai_summary}</p>
      </div>

      {/* Issues */}
      <div className={sectionClass + " overflow-hidden"}>
        <div className="border-b border-[#E5E7EB] px-5 py-3">
          <p className="text-sm font-semibold text-[#111827]">Detected Issues ({file.issues.length})</p>
        </div>
        {file.issues.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-[#6B7280]">No issues detected in this file.</div>
        ) : (
          <div className="divide-y divide-[#F3F4F6]">
            {file.issues.map((iss, idx) => {
              const isExpanded = expandedIssues.has(idx);
              return (
                <div key={idx}>
                  <button onClick={() => toggleIssue(idx)}
                    className="w-full flex items-center gap-3 px-5 py-2.5 text-left hover:bg-[#F9FAFB]">
                    <span className={`h-2 w-2 shrink-0 rounded-full ${severityDot[iss.severity] || "bg-[#6B7280]"}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-[#111827]">{iss.description}</p>
                      <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[10px] text-[#6B7280]">
                        <span className={`rounded-full px-1.5 py-0.5 font-medium ${issueBadgeBg[iss.severity] || "bg-[#F3F4F6] text-[#374151]"}`}>{iss.severity}</span>
                        {iss.line && <span>Line {iss.line}</span>}
                      </div>
                    </div>
                    {isExpanded ? <ChevronDown className="h-3.5 w-3.5 text-[#9CA3AF]" /> : <ChevronRight className="h-3.5 w-3.5 text-[#9CA3AF]" />}
                  </button>
                  {isExpanded && (
                    <div className="border-t border-[#F3F4F6] bg-[#FAFAFA] px-5 py-3 pl-10">
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Reason</p>
                          <p className="mt-1 text-xs text-[#374151]">{iss.reason}</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#059669]">Suggested Fix</p>
                          <p className="mt-1 text-xs text-[#059669]">{iss.suggested_fix}</p>
                        </div>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${priorityBg[iss.priority] || "bg-[#F3F4F6] text-[#374151]"}`}>Priority: {iss.priority}</span>
                        <span className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#374151]">Type: {iss.type}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

    </motion.div>
  );
}
