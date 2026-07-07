import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Activity } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

export function ArchitectureDetection() {
  const navigate = useNavigate();
  const { architecture, loading } = useAnalysis();
  const { projectId } = useParams();

  if (loading || !architecture) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
      </div>
    );
  }

  const arch = architecture.primary_architecture;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div className="flex items-center gap-2">
        <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
        </button>
        <span className="text-[#D1D5DB]">|</span>
        <button onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]">
          Back to Unified Dashboard
        </button>
      </div>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Analyzer</p>
        <h1 className="mt-0.5 text-xl font-bold text-[#111827]">Architecture Detection</h1>
      </div>

      {arch && (
        <div className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#7C3AED] to-[#5B21B6] p-5 text-white">
          <p className="text-xs font-medium uppercase tracking-wider text-[#C4B5FD]">Primary Architecture</p>
          <p className="mt-1 text-lg font-bold">{arch.architecture}</p>
          <p className="mt-1 text-sm text-[#DDD6FE]">{arch.reason}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs backdrop-blur-sm">Confidence: {arch.confidence}%</span>
          </div>
          {arch.evidence && arch.evidence.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {arch.evidence.map((e, i) => (
                <span key={i} className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-[#DDD6FE]">{e}</span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid gap-4 grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Alternative Architectures</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{architecture.alternative_architectures?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Detected Layers</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{architecture.detected_layers?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Evidence Files</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{architecture.primary_architecture?.evidence?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Confidence</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{architecture.primary_architecture?.confidence ?? "—"}%</p>
        </div>
      </div>

      {architecture.alternative_architectures && architecture.alternative_architectures.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white">
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Alternative Architectures</p>
          </div>
          <div className="divide-y divide-[#F3F4F6]">
            {architecture.alternative_architectures.map((alt, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="text-sm font-medium text-[#111827]">{alt.architecture}</p>
                  <p className="text-xs text-[#6B7280]">{alt.reason}</p>
                </div>
                <span className="text-xs text-[#6B7280]">{alt.confidence}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {architecture.detected_layers && architecture.detected_layers.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Detected Layers</p>
          <div className="space-y-2">
            {architecture.detected_layers.map((layer, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-[#F9FAFB] px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-[#111827]">{layer.name}</p>
                  {layer.directories && layer.directories.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {layer.directories.map((d, j) => (
                        <span key={j} className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#374151]">{d}</span>
                      ))}
                    </div>
                  )}
                </div>
                <Activity className="h-4 w-4 text-[#059669]" />
              </div>
            ))}
          </div>
        </div>
      )}

      {projectId && <RelatedAnalysisNav projectId={projectId} currentPage="architecture" />}

    </motion.div>
  );
}
