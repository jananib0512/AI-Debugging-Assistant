import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

export function TechnologyStack() {
  const navigate = useNavigate();
  const { frameworks, loading } = useAnalysis();
  const { projectId } = useParams();

  if (loading || !frameworks) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
      </div>
    );
  }

  const tech = frameworks.technology_stack;

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
        <h1 className="mt-0.5 text-xl font-bold text-[#111827]">Technology Stack</h1>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Languages</p>
          <div className="mt-1 space-y-0.5">
            {tech.languages.map((l, i) => (
              <span key={i} className="text-sm font-medium text-[#111827]">{l.name}{l.version ? ` v${l.version}` : ""}</span>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Runtimes</p>
          <div className="mt-1 space-y-0.5">
            {tech.runtimes.map((r, i) => (
              <span key={i} className="text-sm font-medium text-[#111827]">{r.name}{r.version ? ` v${r.version}` : ""}</span>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Databases</p>
          <div className="mt-1 space-y-0.5">
            {tech.databases.map((d, i) => (
              <span key={i} className="text-sm font-medium text-[#111827]">{d.name}{d.version ? ` v${d.version}` : ""}</span>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Package Managers</p>
          <div className="mt-1 space-y-0.5">
            {tech.package_managers.map((pm, i) => (
              <span key={i} className="text-sm font-medium text-[#111827]">{pm.name}{pm.version ? ` v${pm.version}` : ""}</span>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Build Tools</p>
          <div className="mt-1 space-y-0.5">
            {tech.build_tools.map((bt, i) => (
              <span key={i} className="text-sm font-medium text-[#111827]">{bt.name}{bt.version ? ` v${bt.version}` : ""}</span>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Containers</p>
          <div className="mt-1 space-y-0.5">
            {tech.containers.map((c, i) => (
              <span key={i} className="text-sm font-medium text-[#111827]">{c.name}{c.version ? ` v${c.version}` : ""}</span>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Frameworks</p>
          <div className="mt-1 space-y-0.5">
            {tech.frameworks.map((f, i) => (
              <span key={i} className="text-sm font-medium text-[#111827]">{f.name}{f.version ? ` v${f.version}` : ""}</span>
            ))}
          </div>
        </div>
      </div>

      {tech.categorized && Object.keys(tech.categorized).length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Categorized Technologies</p>
          <div className="space-y-3">
            {Object.entries(tech.categorized).map(([category, items]) => (
              <div key={category}>
                <p className="text-xs font-semibold text-[#6B7280] uppercase mb-1">{category.replace(/_/g, " ")}</p>
                <div className="flex flex-wrap gap-1">
                  {items.map((t, j) => (
                    <span key={j} className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#374151]">{t.name}{t.version ? ` v${t.version}` : ""}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {projectId && <RelatedAnalysisNav projectId={projectId} currentPage="technology" />}

    </motion.div>
  );
}
