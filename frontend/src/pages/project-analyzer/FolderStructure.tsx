import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";

export function FolderStructure() {
  const navigate = useNavigate();
  const { data, loading } = useAnalysis();
  const { projectId } = useParams();

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
      </div>
    );
  }

  const folderSum = data.folder_summary;
  const folderEntries = folderSum ? Object.entries(folderSum).filter(([, v]) => typeof v === "number") as [string, number][] : [];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
      </button>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Analyzer</p>
        <h1 className="mt-0.5 text-xl font-bold text-[#111827]">Folder Structure</h1>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Folders</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{data.total_folders}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Files</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{data.total_files}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Workspace Size</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">
            {data.workspace_size >= 1073741824
              ? (data.workspace_size / 1073741824).toFixed(1) + " GB"
              : data.workspace_size >= 1048576
              ? (data.workspace_size / 1048576).toFixed(1) + " MB"
              : data.workspace_size >= 1024
              ? (data.workspace_size / 1024).toFixed(0) + " KB"
              : data.workspace_size + " B"}
          </p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Folder Types</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{folderEntries.length}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Largest Category</p>
          <p className="mt-1 text-sm font-semibold text-[#111827] capitalize truncate">{folderEntries.sort(([, a], [, b]) => b - a)[0]?.[0]?.replace(/_/g, " ") || "—"}</p>
        </div>
      </div>

      {folderEntries.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Folder Summary</p>
          <div className="space-y-2">
            {folderEntries.map(([key, count], i) => {
              const maxCount = Math.max(...folderEntries.map(([, c]) => c), 1);
              const pct = (count / maxCount) * 100;
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="w-20 text-xs font-medium text-[#374151] capitalize">{key.replace(/_/g, " ")}</span>
                  <div className="flex-1 h-2 rounded-full bg-[#F3F4F6] overflow-hidden">
                    <div className="h-full rounded-full bg-[#2563EB] transition-all" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs text-[#6B7280] w-8 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <p className="mb-3 text-sm font-semibold text-[#111827]">Project Summary</p>
        <p className="text-sm leading-relaxed text-[#374151]">{data.workspace_summary}</p>
      </div>

    </motion.div>
  );
}
