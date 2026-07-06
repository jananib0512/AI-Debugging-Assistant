import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, CheckCircle2, AlertTriangle, Info } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";

export function FrameworkIntelligence() {
  const navigate = useNavigate();
  const { frameworks, loading, projectId } = useAnalysis();

  if (loading || !frameworks) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
      </div>
    );
  }

  const fws = frameworks.frameworks || [];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
      </button>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Analyzer</p>
        <h1 className="mt-0.5 text-xl font-bold text-[#111827]">Framework Intelligence</h1>
      </div>

      {frameworks.primary_framework && (
        <div className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] p-5 text-white">
          <p className="text-xs font-medium uppercase tracking-wider text-[#93C5FD]">Primary Framework</p>
          <p className="mt-1 text-lg font-bold">{frameworks.primary_framework.name}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs backdrop-blur-sm">Confidence: {frameworks.primary_framework.confidence}%</span>
            <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs backdrop-blur-sm">{frameworks.primary_framework.reason}</span>
          </div>
        </div>
      )}

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-3 xl:grid-cols-5 2xl:grid-cols-6">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Detected Frameworks</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{fws.length}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Languages</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{frameworks.technology_stack?.languages?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Features Detected</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{frameworks.features?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Compatibility Checks</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{frameworks.compatibility?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Evidence Items</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{frameworks.evidence?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Dependency Layers</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{frameworks.dependency_graph?.length || 0}</p>
        </div>
      </div>

      {fws.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white">
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Detected Frameworks</p>
          </div>
          <div className="divide-y divide-[#F3F4F6]">
            {fws.map((fw, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="text-sm font-medium text-[#111827]">{fw.name}</p>
                  <p className="text-xs text-[#6B7280]">{fw.category}{fw.version ? ` v${fw.version}` : ""}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[#6B7280]">{fw.detection_source}</span>
                  <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2 py-0.5 text-[10px] font-medium text-[#1E40AF]">{fw.confidence}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {frameworks.compatibility && frameworks.compatibility.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Compatibility</p>
          <div className="space-y-2">
            {frameworks.compatibility.map((c, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                {c.status === "compatible" ? <CheckCircle2 className="h-4 w-4 text-[#059669]" /> : <AlertTriangle className="h-4 w-4 text-[#D97706]" />}
                <span className="text-[#374151]">{c.framework} + {c.other_framework}</span>
                <span className="text-xs text-[#6B7280]">{c.note}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {frameworks.evidence && frameworks.evidence.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Detection Evidence</p>
          <div className="space-y-2">
            {frameworks.evidence.map((e, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <Info className="h-3.5 w-3.5 text-[#2563EB]" />
                <span className="font-medium text-[#111827]">{e.name}</span>
                <span className="text-[#6B7280]">({e.source})</span>
                <span className="text-[#6B7280]">{e.confidence}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {frameworks.dependency_graph && frameworks.dependency_graph.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Dependency Graph</p>
          <div className="space-y-3">
            {frameworks.dependency_graph.map((layer, i) => (
              <div key={i}>
                <p className="text-xs font-semibold text-[#6B7280] uppercase">{layer.layer}: {layer.label}</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {layer.technologies.map((t, j) => (
                    <span key={j} className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#374151]">{t}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </motion.div>
  );
}
