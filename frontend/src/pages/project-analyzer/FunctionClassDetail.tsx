import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  FlaskConical,
  FunctionSquare,
  RefreshCw,
} from "lucide-react";
import { getFunctionClassAnalysis } from "@/lib/project-analyzer";
import type { ClassDetail, FunctionDetail } from "@/types/project-analyzer";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const healthBadge: Record<string, string> = {
  Excellent: "bg-[#ECFDF5] text-[#065F46]",
  Good: "bg-[#EFF6FF] text-[#1E40AF]",
  Fair: "bg-[#FFFBEB] text-[#92400E]",
  "Needs Improvement": "bg-[#FFF7ED] text-[#9A3412]",
  Poor: "bg-[#FEF2F2] text-[#991B1B]",
};

const severityBadge: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B]",
  high: "bg-[#FFF7ED] text-[#9A3412]",
  medium: "bg-[#FFFBEB] text-[#92400E]",
  low: "bg-[#F3F4F6] text-[#374151]",
};

export function FunctionClassDetail() {
  const { projectId, filePath, itemName } = useParams<{ projectId: string; filePath: string; itemName: string }>();
  const navigate = useNavigate();
  const decodedPath = filePath ? decodeURIComponent(filePath) : "";
  const decodedName = itemName ? decodeURIComponent(itemName) : "";
  const [func, setFunc] = useState<FunctionDetail | null>(null);
  const [cls, setCls] = useState<ClassDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getFunctionClassAnalysis(Number(projectId));
      const foundFunc = result.functions.find(
        (f) => f.file_path === decodedPath && f.name === decodedName,
      );
      const foundClass = result.classes.find(
        (c) => c.file_path === decodedPath && c.name === decodedName,
      );
      if (foundFunc) setFunc(foundFunc);
      else if (foundClass) setCls(foundClass);
      else setError(`"${decodedName}" not found in ${decodedPath}.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load detail");
    } finally {
      setLoading(false);
      fetchedRef.current = true;
    }
  }, [projectId, decodedPath, decodedName]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Loading details...</p>
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

  if (!func && !cls) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <FunctionSquare className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">Not found</p>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">

      <div className="flex items-center justify-between">
        <div>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer/function-class`)}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Function & Class Analysis
          </button>
          <p className="mt-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">
            {func ? "Function Detail" : "Class Detail"}
          </p>
          <h1 className="mt-0.5 text-xl font-bold text-[#111827]">{decodedName}</h1>
        </div>
      </div>

      {/* Metadata */}
      <div className={sectionClass + " p-5"}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">File</p><p className="text-xs text-[#374151] break-all">{decodedPath}</p></div>
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Language</p><p className="text-xs font-medium text-[#374151]">{func ? func.language : cls!.language}</p></div>
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Module</p><p className="text-xs text-[#374151]">{func ? func.module : cls!.module || "—"}</p></div>
          <div><p className="text-[10px] font-semibold text-[#9CA3AF]">Health</p>
            <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${healthBadge[func ? func.health_status : cls!.health_status] || "bg-[#F3F4F6] text-[#374151]"}`}>
              {func ? func.health_status : cls!.health_status}
            </span>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className={sectionClass + " p-5"}>
        <p className="mb-3 text-sm font-semibold text-[#111827]">Metrics</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {func ? (
            <>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Lines of Code</p><p className="text-sm font-bold text-[#111827]">{func.lines_of_code}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Cyclomatic Complexity</p><p className="text-sm font-bold text-[#111827]">{func.cyclomatic_complexity}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Maintainability</p><p className="text-sm font-bold text-[#111827]">{func.maintainability_score.toFixed(0)}/100</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Issue Count</p><p className="text-sm font-bold text-[#111827]">{func.issue_count}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Parameters</p><p className="text-sm font-bold text-[#111827]">{func.parameters.length}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Visibility</p><p className="text-sm font-bold text-[#111827] capitalize">{func.visibility}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Has Documentation</p><p className="text-sm font-bold text-[#111827]">{func.has_documentation ? "Yes" : "No"}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Return Type</p><p className="text-sm font-bold text-[#111827]">{func.return_type || "—"}</p></div>
            </>
          ) : (
            <>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Lines of Code</p><p className="text-sm font-bold text-[#111827]">{cls!.lines_of_code}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Complexity</p><p className="text-sm font-bold text-[#111827]">{cls!.complexity}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Maintainability</p><p className="text-sm font-bold text-[#111827]">{cls!.maintainability_score.toFixed(0)}/100</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Issue Count</p><p className="text-sm font-bold text-[#111827]">{cls!.issue_count}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Methods</p><p className="text-sm font-bold text-[#111827]">{cls!.methods.length}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Properties</p><p className="text-sm font-bold text-[#111827]">{cls!.properties.length}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Is Abstract</p><p className="text-sm font-bold text-[#111827]">{cls!.is_abstract ? "Yes" : "No"}</p></div>
              <div className="rounded-lg bg-[#F9FAFB] px-4 py-3"><p className="text-[10px] text-[#9CA3AF]">Has Documentation</p><p className="text-sm font-bold text-[#111827]">{cls!.has_documentation ? "Yes" : "No"}</p></div>
            </>
          )}
        </div>
      </div>

      {/* Parameters / Base classes */}
      {func && func.parameters.length > 0 && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">Parameters</p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#E5E7EB]">
                  <th className="py-2 text-left font-medium text-[#6B7280]">Name</th>
                  <th className="py-2 text-left font-medium text-[#6B7280]">Type</th>
                  <th className="py-2 text-left font-medium text-[#6B7280]">Default</th>
                  <th className="py-2 text-left font-medium text-[#6B7280]">Optional</th>
                </tr>
              </thead>
              <tbody>
                {func.parameters.map((p) => (
                  <tr key={p.name} className="border-b border-[#F3F4F6]">
                    <td className="py-1.5 font-medium text-[#111827]">{p.name}</td>
                    <td className="py-1.5 text-[#6B7280]">{p.type || "—"}</td>
                    <td className="py-1.5 text-[#6B7280]">{p.default_value || "—"}</td>
                    <td className="py-1.5">{p.is_optional ? <span className="rounded bg-[#D1FAE5] px-1.5 py-0.5 text-[9px] text-[#065F46]">Yes</span> : <span className="text-[#9CA3AF]">No</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {cls && cls.base_classes.length > 0 && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">Base Classes & Interfaces</p>
          <div className="flex flex-wrap gap-1.5">
            {cls.base_classes.map((b) => <span key={b} className="rounded-lg bg-[#F3E8FF] px-2 py-1 text-xs text-[#6D28D9]">{b}</span>)}
            {cls.interfaces.map((i) => <span key={i} className="rounded-lg bg-[#EDE9FE] px-2 py-1 text-xs text-[#6D28D9]">{i}</span>)}
          </div>
        </div>
      )}

      {/* Decorators */}
      {(func ? func.decorators : cls!.decorators).length > 0 && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">Decorators</p>
          <div className="flex flex-wrap gap-1.5">
            {(func ? func.decorators : cls!.decorators).map((d) => (
              <span key={d} className="rounded-lg bg-[#EDE9FE] px-2 py-1 text-xs text-[#6D28D9]">@{d}</span>
            ))}
          </div>
        </div>
      )}

      {/* Flags */}
      {func && (func.is_async || func.is_generator || func.is_lambda) && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">Properties</p>
          <div className="flex flex-wrap gap-2">
            {func.is_async && <span className="rounded-full bg-[#EFF6FF] px-3 py-1 text-xs text-[#1E40AF]">Async Function</span>}
            {func.is_generator && <span className="rounded-full bg-[#FEF3C7] px-3 py-1 text-xs text-[#92400E]">Generator Function</span>}
            {func.is_lambda && <span className="rounded-full bg-[#F3F4F6] px-3 py-1 text-xs text-[#374151]">Lambda Expression</span>}
          </div>
        </div>
      )}

      {/* Class-specific: methods, properties, constructors */}
      {cls && cls.methods.length > 0 && (
        <div className={sectionClass + " overflow-hidden"}>
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Methods ({cls.methods.length})</p>
          </div>
          <div className="divide-y divide-[#F3F4F6]">
            {cls.methods.map((m) => (
              <div key={m.name} className="px-5 py-2.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-medium text-[#111827]">{m.name}</span>
                  <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${healthBadge[m.health_status] || "bg-[#F3F4F6] text-[#374151]"}`}>{m.health_status}</span>
                  {m.is_static && <span className="rounded bg-[#EFF6FF] px-1.5 py-0.5 text-[9px] text-[#1E40AF]">static</span>}
                  {m.is_property && <span className="rounded bg-[#ECFDF5] px-1.5 py-0.5 text-[9px] text-[#065F46]">property</span>}
                  {m.is_async && <span className="rounded bg-[#FEF3C7] px-1.5 py-0.5 text-[9px] text-[#92400E]">async</span>}
                </div>
                <div className="mt-0.5 text-[9px] text-[#6B7280]">
                  {m.lines_of_code} LOC · CC {m.cyclomatic_complexity} · {m.issue_count} issue(s) · {m.visibility}
                  {m.return_type && <span> · returns {m.return_type}</span>}
                </div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {m.parameters.map((p) => (
                    <span key={p.name} className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[9px] text-[#6B7280]">{p.name}{p.type ? `: ${p.type}` : ""}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {cls && cls.properties.length > 0 && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">Properties</p>
          <div className="flex flex-wrap gap-1.5">
            {cls.properties.map((prop) => (
              <span key={prop} className="rounded-lg bg-[#F3F4F6] px-2.5 py-1 text-xs text-[#374151]">{prop}</span>
            ))}
          </div>
        </div>
      )}

      {/* Issues */}
      {(func || cls) && ((func ? func.issues : cls!.issues).length > 0) && (
        <div className={sectionClass + " p-5"}>
          <p className="mb-3 text-sm font-semibold text-[#111827]">Issues ({(func ? func.issues : cls!.issues).length})</p>
          <div className="space-y-2">
            {(func ? func.issues : cls!.issues).map((iss, i) => (
              <div key={i} className="rounded-lg border border-[#F3F4F6] bg-[#FAFAFA] px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${severityBadge[iss.severity] || "bg-[#F3F4F6] text-[#374151]"}`}>{iss.severity}</span>
                  <span className="text-xs font-medium text-[#111827]">{iss.description}</span>
                  {iss.line && <span className="text-[10px] text-[#6B7280]">Line {iss.line}</span>}
                </div>
                <p className="mt-1 text-[10px] text-[#6B7280]">{iss.reason}</p>
                <p className="mt-0.5 text-[10px] text-[#059669]">Fix: {iss.suggested_fix}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Insight */}
      {(func ? func.ai_insight : cls!.ai_insight) && (
        <div className={sectionClass + " p-5"}>
          <div className="flex items-center gap-2 mb-2">
            <FlaskConical className="h-4 w-4 text-[#7C3AED]" />
            <p className="text-sm font-semibold text-[#111827]">AI Insight</p>
          </div>
          <p className="text-sm text-[#374151] leading-relaxed">
            {func ? func.ai_insight : cls!.ai_insight}
          </p>
        </div>
      )}

    </motion.div>
  );
}
