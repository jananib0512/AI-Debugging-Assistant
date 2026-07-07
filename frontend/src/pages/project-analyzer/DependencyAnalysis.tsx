import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Package } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

export function DependencyAnalysis() {
  const navigate = useNavigate();
  const { configIntel, loading } = useAnalysis();
  const { projectId } = useParams();

  if (loading || !configIntel) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
      </div>
    );
  }

  const depValidation = configIntel.dependency_validation || [];

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
        <h1 className="mt-0.5 text-xl font-bold text-[#111827]">Dependency Analysis</h1>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Validation Issues</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{depValidation.length}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Health Score</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{configIntel.health?.score ?? "—"}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Readiness Score</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{configIntel.readiness_score ?? "—"}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">CICD Platforms</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{configIntel.cicd?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Has Docker</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{configIntel.docker_validation?.has_dockerfile ? "Yes" : "No"}</p>
        </div>
      </div>

      {depValidation.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white">
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Dependency Validations</p>
          </div>
          <div className="divide-y divide-[#F3F4F6]">
            {depValidation.map((dv, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  <Package className="h-4 w-4 text-[#6B7280]" />
                  <div>
                    <p className="text-sm font-medium text-[#111827]">{dv.package}</p>
                    <p className="text-xs text-[#6B7280]">{dv.detail}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-[#6B7280]">{dv.type}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    dv.severity === "high" || dv.severity === "error" ? "bg-[#FEF2F2] text-[#991B1B]" :
                    dv.severity === "medium" || dv.severity === "warning" ? "bg-[#FFFBEB] text-[#92400E]" :
                    "bg-[#F3F4F6] text-[#374151]"
                  }`}>{dv.severity}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {depValidation.length === 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-8 text-center">
          <Package className="mx-auto mb-2 h-8 w-8 text-[#9CA3AF]" />
          <p className="text-sm text-[#6B7280]">No dependency validation issues found.</p>
        </div>
      )}

      {projectId && <RelatedAnalysisNav projectId={projectId} currentPage="dependencies" />}

    </motion.div>
  );
}
