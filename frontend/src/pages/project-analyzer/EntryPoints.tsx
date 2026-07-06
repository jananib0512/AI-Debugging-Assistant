import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, FileCode, Terminal } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";

export function EntryPoints() {
  const navigate = useNavigate();
  const { entryPoints, loading } = useAnalysis();
  const { projectId } = useParams();

  if (loading || !entryPoints) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
      </div>
    );
  }

  const primary = entryPoints.primary_entry_point;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
      </button>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Analyzer</p>
        <h1 className="mt-0.5 text-xl font-bold text-[#111827]">Entry Point Detection</h1>
      </div>

      {primary && (
        <div className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#059669] to-[#047857] p-5 text-white">
          <div className="flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            <p className="text-xs font-medium uppercase tracking-wider text-[#A7F3D0]">Primary Entry Point</p>
          </div>
          <p className="mt-2 text-lg font-bold">{primary.entry_file}</p>
          {primary.framework && <p className="mt-1 text-sm text-[#A7F3D0]">Framework: {primary.framework}</p>}
          <p className="mt-1 text-xs text-[#A7F3D0]">Type: {primary.project_type}</p>
          {primary.confidence !== undefined && <span className="mt-2 inline-block rounded-full bg-white/20 px-2.5 py-0.5 text-xs backdrop-blur-sm">Confidence: {primary.confidence}%</span>}
        </div>
      )}

      <div className="grid gap-4 grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Alternative Entry Points</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{entryPoints.alternative_entry_points?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Entry Points</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{entryPoints.total_entry_points}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Primary Confidence</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{entryPoints.primary_entry_point?.confidence ?? "—"}%</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Framework</p>
          <p className="mt-1 text-lg font-bold text-[#111827] truncate">{entryPoints.primary_entry_point?.framework || "—"}</p>
        </div>
      </div>

      {entryPoints.alternative_entry_points && entryPoints.alternative_entry_points.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white">
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Alternative Entry Points</p>
          </div>
          <div className="divide-y divide-[#F3F4F6]">
            {entryPoints.alternative_entry_points.map((ep, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  <FileCode className="h-4 w-4 text-[#6B7280]" />
                  <div>
                    <p className="text-sm text-[#374151]">{ep.entry_file}</p>
                    <p className="text-xs text-[#6B7280]">{ep.project_type}</p>
                  </div>
                </div>
                {ep.confidence !== undefined && <span className="text-xs text-[#6B7280]">{ep.confidence}%</span>}
              </div>
            ))}
          </div>
        </div>
      )}

    </motion.div>
  );
}
