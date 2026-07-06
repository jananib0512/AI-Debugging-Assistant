import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, FileText, Shield, AlertTriangle, CheckCircle } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";

export function ConfigurationIntelligence() {
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

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
      </button>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Analyzer</p>
        <h1 className="mt-0.5 text-xl font-bold text-[#111827]">Configuration Intelligence</h1>
      </div>

      {configIntel.health && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-sm font-semibold text-[#111827]">Configuration Health</p>
          <div className="mt-3 flex items-center gap-3">
            <span className="text-2xl font-bold text-[#111827]">{configIntel.health.score}</span>
            <span className="text-xs text-[#6B7280]">{configIntel.health.label}</span>
          </div>
        </div>
      )}

      <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Detected Files</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{configIntel.detected_files?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Missing Files</p>
          <p className="mt-1 text-lg font-bold text-[#DC2626]">{configIntel.missing_files?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Dependency Issues</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{configIntel.dependency_validation?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Security Checks</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{configIntel.security_checks?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Env Validations</p>
          <p className="mt-1 text-lg font-bold text-[#111827]">{configIntel.environment_validation?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Warnings</p>
          <p className="mt-1 text-lg font-bold text-[#D97706]">{configIntel.warnings?.length || 0}</p>
        </div>
      </div>

      {configIntel.detected_files && configIntel.detected_files.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white">
          <div className="border-b border-[#E5E7EB] px-5 py-3">
            <p className="text-sm font-semibold text-[#111827]">Detected Configuration Files</p>
          </div>
          <div className="divide-y divide-[#F3F4F6]">
            {configIntel.detected_files.map((file, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-[#6B7280]" />
                  <div>
                    <p className="text-sm text-[#374151]">{file.file_name}</p>
                    {file.purpose && <p className="text-xs text-[#6B7280]">{file.purpose}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-[#6B7280]">{file.category}</span>
                  {file.status === "valid" ? <CheckCircle className="h-4 w-4 text-[#059669]" /> :
                   file.status === "missing" ? <AlertTriangle className="h-4 w-4 text-[#DC2626]" /> :
                   <Shield className="h-4 w-4 text-[#6B7280]" />}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {configIntel.missing_files && configIntel.missing_files.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Missing Files</p>
          <div className="space-y-2">
            {configIntel.missing_files.map((file, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <AlertTriangle className="h-4 w-4 shrink-0 text-[#D97706]" />
                <span className="text-[#374151]">{file.file_name}</span>
                {file.purpose && <span className="text-xs text-[#6B7280]">— {file.purpose}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {configIntel.warnings && configIntel.warnings.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Warnings</p>
          <div className="space-y-2">
            {configIntel.warnings.map((w, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#D97706]" />
                <span className="text-[#374151]">{w.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {configIntel.security_checks && configIntel.security_checks.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Security Checks</p>
          <div className="space-y-2">
            {configIntel.security_checks.map((s, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <Shield className="mt-0.5 h-4 w-4 shrink-0 text-[#2563EB]" />
                <span className="text-[#374151]">{s.detail}</span>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  s.severity === "high" ? "bg-[#FEF2F2] text-[#991B1B]" :
                  s.severity === "medium" ? "bg-[#FFFBEB] text-[#92400E]" :
                  "bg-[#F3F4F6] text-[#374151]"
                }`}>{s.severity}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {configIntel.recommendations && configIntel.recommendations.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Recommendations</p>
          <div className="space-y-2">
            {configIntel.recommendations.map((r, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#2563EB]" />
                <span className="text-[#374151]">{r}</span>
              </div>
            ))}
          </div>
        </div>
      )}

    </motion.div>
  );
}
