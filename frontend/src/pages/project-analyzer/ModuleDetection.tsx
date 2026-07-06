import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";

export function ModuleDetection() {
  const navigate = useNavigate();
  const { modules, loading } = useAnalysis();
  const { projectId } = useParams();

  if (loading || !modules) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
      </div>
    );
  }

  const summary = modules.summary;
  const moduleList = modules.modules || [];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
      </button>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Analyzer</p>
        <h1 className="mt-0.5 text-xl font-bold text-[#111827]">Module Detection</h1>
      </div>

      {summary && (
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Modules</p>
            <p className="mt-1 text-lg font-bold text-[#111827]">{summary.total_modules}</p>
          </div>
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Detected</p>
            <p className="mt-1 text-lg font-bold text-[#059669]">{summary.detected_count}</p>
          </div>
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Missing</p>
            <p className="mt-1 text-lg font-bold text-[#DC2626]">{summary.total_modules - summary.detected_count}</p>
          </div>
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Core</p>
            <p className="mt-1 text-lg font-bold text-[#111827]">{summary.core_detected}/{summary.core_total}</p>
          </div>
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Optional</p>
            <p className="mt-1 text-lg font-bold text-[#111827]">{summary.optional_detected}/{summary.optional_total}</p>
          </div>
        </div>
      )}

      {moduleList.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white">
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Modules</p>
          </div>
          <div className="divide-y divide-[#F3F4F6]">
            {moduleList.map((m, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  {m.status === "detected" ? <CheckCircle className="h-4 w-4 text-[#059669]" /> :
                   m.status === "missing" ? <XCircle className="h-4 w-4 text-[#9CA3AF]" /> :
                   <AlertCircle className="h-4 w-4 text-[#D97706]" />}
                  <div>
                    <p className="text-sm font-medium text-[#111827]">{m.module_name}</p>
                    {m.detected_folder && <p className="text-xs text-[#6B7280]">{m.detected_folder}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[#6B7280]">{m.confidence}%</span>
                  <span className="text-[10px] text-[#6B7280] hidden md:inline max-w-xs truncate">{m.reason}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </motion.div>
  );
}
