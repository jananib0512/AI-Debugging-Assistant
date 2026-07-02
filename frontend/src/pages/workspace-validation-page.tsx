import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronRight,
  CircleSlash,
  ClipboardCheck,
  FileCode,
  FileCog,
  FolderKanban,
  Layers,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { getProject } from "@/lib/projects";
import { getWorkspaceValidation } from "@/lib/workspace-validation";
import type { Project } from "@/types/project";
import type { WorkspaceValidation } from "@/types/workspace-validation";

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-[#E5E7EB] ${className}`}
    />
  );
}

function StatusBadge({ status }: { status: string }) {
  const defaultConfig = { bg: "bg-[#FEE2E2]", text: "text-[#991B1B]", icon: XCircle, label: "Not Ready" };
  const configMap: Record<string, { bg: string; text: string; icon: typeof CheckCircle2; label: string }> = {
    ready: { bg: "bg-[#D1FAE5]", text: "text-[#065F46]", icon: CheckCircle2, label: "Ready" },
    ready_with_warnings: { bg: "bg-[#FEF3C7]", text: "text-[#92400E]", icon: AlertTriangle, label: "Ready with Warnings" },
    not_ready: defaultConfig,
  };
  const c = configMap[status] ?? defaultConfig;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${c.bg} ${c.text}`}>
      <Icon className="h-3.5 w-3.5" />
      {c.label}
    </span>
  );
}

function ConfigCheck({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className={`flex items-center gap-2.5 rounded-lg border px-3 py-2.5 ${ok ? "border-[#D1FAE5] bg-[#F0FDF4]" : "border-[#E5E7EB] bg-white"}`}>
      {ok ? (
        <CheckCircle2 className="h-4 w-4 text-[#059669] shrink-0" />
      ) : (
        <CircleSlash className="h-4 w-4 text-[#9CA3AF] shrink-0" />
      )}
      <span className="text-sm font-medium text-[#111827]">
        {label}
      </span>
    </div>
  );
}

function StructureCheck({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm">
      {ok ? (
        <CheckCircle2 className="h-4 w-4 text-[#059669] shrink-0" />
      ) : (
        <CircleSlash className="h-4 w-4 text-[#9CA3AF] shrink-0" />
      )}
      <span className="text-sm font-medium text-[#111827]">
        {label}
      </span>
    </div>
  );
}

function transformStructureNote(note: string, readmeExists: boolean): string {
  const lower = note.toLowerCase();
  if (lower === "no frontend directory detected") {
    return "Frontend directory not found.";
  }
  if (lower === "no backend directory detected") {
    return "Backend directory not found.";
  }
  if (lower === "no documentation directory detected") {
    if (readmeExists) {
      return "Documentation folder (docs/) not found. README file is available.";
    }
    return "Documentation folder (docs/) and README file not found.";
  }
  return note;
}

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

export function WorkspaceValidationPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [validation, setValidation] = useState<WorkspaceValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);

  const fetchAll = useCallback(async (isRefresh = false) => {
    if (!projectId) return;
    if (isRefresh) setValidating(true);
    else setLoading(true);
    setError(null);
    try {
      const [proj, v] = await Promise.all([
        getProject(Number(projectId)),
        getWorkspaceValidation(Number(projectId)),
      ]);
      setProject(proj);
      setValidation(v);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to validate workspace";
      setError(msg);
    } finally {
      setLoading(false);
      setValidating(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <Skeleton className="h-5 w-44" />
            <Skeleton className="mt-1.5 h-3 w-56" />
          </div>
        </div>
        <Skeleton className="h-28 rounded-xl" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-40 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h2 className="text-lg font-semibold text-[#111827]">Workspace Validation</h2>
            <p className="text-sm text-[#6B7280]">Error running validation</p>
          </div>
        </div>
        <Card>
          <div className="flex flex-col items-center justify-center py-24">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50 mb-4">
              <Layers className="h-7 w-7 text-[#EF4444]" />
            </div>
            <h3 className="text-lg font-medium text-[#111827]">
              Validation failed
            </h3>
            <p className="mt-1 text-sm text-[#6B7280] text-center max-w-sm">
              {error}
            </p>
            <button
              onClick={() => fetchAll()}
              className="mt-6 inline-flex items-center gap-2 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-sm font-medium text-[#374151] hover:bg-[#F9FAFB] transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </button>
          </div>
        </Card>
      </div>
    );
  }

  if (!validation) {
    return (
      <div className="space-y-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h2 className="text-lg font-semibold text-[#111827]">Workspace Validation</h2>
            <p className="text-sm text-[#6B7280]">
              Check workspace readiness for analysis
            </p>
          </div>
        </div>
        <Card>
          <div className="flex flex-col items-center justify-center py-24">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#F3F4F6] mb-4">
              <ClipboardCheck className="h-7 w-7 text-[#6B7280]" />
            </div>
            <h3 className="text-lg font-medium text-[#111827]">
              No validation data
            </h3>
            <p className="mt-1 text-sm text-[#6B7280] text-center max-w-sm">
              Project validation has not been run yet. Click the button below
              to validate your workspace.
            </p>
            <button
              onClick={() => fetchAll()}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-4 py-2 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Run Validation Now
            </button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h2 className="text-lg font-semibold text-[#111827]">
              Workspace Validation
            </h2>
            <p className="text-sm text-[#6B7280]">
              Check workspace readiness for analysis &middot; #
              {project?.id ?? projectId}
            </p>
          </div>
        </div>
        <button
          onClick={() => fetchAll(true)}
          disabled={validating}
          className="inline-flex items-center gap-2 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-sm font-medium text-[#374151] hover:bg-[#F9FAFB] transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${validating ? "animate-spin" : ""}`} />
          Re-validate
        </button>
      </motion.div>

      {/* Validation Summary + Readiness */}
      <motion.div variants={itemVariants}>
        <Card>
          <div className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-sm font-semibold text-[#111827]">
                    Validation Summary
                  </h3>
                  <StatusBadge status={validation.workspace_status} />
                </div>
                <p className="text-sm text-[#6B7280] leading-relaxed">
                  {validation.summary}
                </p>
              </div>
              <div className="shrink-0">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[#F3F4F6]">
                  {validation.ready_for_analysis ? (
                    <CheckCircle2 className="h-7 w-7 text-[#059669]" />
                  ) : (
                    <XCircle className="h-7 w-7 text-[#DC2626]" />
                  )}
                </div>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Errors */}
      {validation.errors.length > 0 && (
        <motion.div variants={itemVariants}>
          <Card>
            <div className="p-6">
              <h3 className="text-sm font-semibold text-[#111827] mb-4 flex items-center gap-2">
                <XCircle className="h-4 w-4 text-[#DC2626]" />
                Errors ({validation.errors.length})
              </h3>
              <div className="space-y-2">
                {validation.errors.map((err, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-xl border border-[#FEE2E2] bg-[#FEF2F2] px-4 py-3"
                  >
                    <XCircle className="h-4 w-4 text-[#DC2626] shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-[#991B1B]">
                        {err.message}
                      </p>
                      {err.detail && (
                        <p className="text-xs text-[#B91C1C] mt-0.5">
                          {err.detail}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Warnings */}
      {validation.warnings.length > 0 && (
        <motion.div variants={itemVariants}>
          <Card>
            <div className="p-6">
              <h3 className="text-sm font-semibold text-[#111827] mb-4 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-[#D97706]" />
                Warnings ({validation.warnings.length})
              </h3>
              <div className="space-y-2">
                {validation.warnings.map((warn, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-xl border border-[#FEF3C7] bg-[#FFFBEB] px-4 py-3"
                  >
                    <AlertTriangle className="h-4 w-4 text-[#D97706] shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-[#92400E]">
                        {warn.message}
                      </p>
                      {warn.detail && (
                        <p className="text-xs text-[#A16207] mt-0.5">
                          {warn.detail}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Configuration Summary + Project Structure */}
      <motion.div
        variants={itemVariants}
        className="grid gap-6 lg:grid-cols-2"
      >
        {/* Configuration Summary */}
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-semibold text-[#111827] mb-5 flex items-center gap-2">
              <FileCog className="h-4 w-4 text-[#6B7280]" />
              Configuration Summary
            </h3>
            <div className="space-y-2">
              <ConfigCheck label="package.json" ok={validation.config_files_summary.has_package_json} />
              <ConfigCheck label="requirements.txt" ok={validation.config_files_summary.has_requirements_txt} />
              <ConfigCheck label="pyproject.toml" ok={validation.config_files_summary.has_pyproject_toml} />
              <ConfigCheck label="Dockerfile" ok={validation.config_files_summary.has_dockerfile} />
              <ConfigCheck label="Docker Compose" ok={validation.config_files_summary.has_docker_compose} />
              <ConfigCheck label="README" ok={validation.config_files_summary.has_readme} />
              <ConfigCheck label=".env.example" ok={validation.config_files_summary.has_env_example} />
            </div>
            {validation.config_files_summary.files_found.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[#E5E7EB]">
                <p className="text-xs text-[#6B7280] mb-2">Files found</p>
                <div className="flex flex-wrap gap-1.5">
                  {validation.config_files_summary.files_found.map((f) => (
                    <span
                      key={f}
                      className="inline-flex items-center gap-1 rounded-md bg-[#F3F4F6] px-2 py-1 text-xs font-mono text-[#374151]"
                    >
                      <FileCode className="h-3 w-3 text-[#6B7280]" />
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Project Structure */}
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-semibold text-[#111827] mb-5 flex items-center gap-2">
              <FolderKanban className="h-4 w-4 text-[#6B7280]" />
              Project Structure
            </h3>
            <div className="space-y-0.5">
              <StructureCheck label="Frontend directory" ok={validation.project_structure.has_frontend} />
              <StructureCheck label="Backend directory" ok={validation.project_structure.has_backend} />
              <StructureCheck label="Source folders" ok={validation.project_structure.has_source_folders} />
              <StructureCheck label="Configuration folder" ok={validation.project_structure.has_config_folder} />
              <StructureCheck label="Assets folder" ok={validation.project_structure.has_assets_folder} />
              <StructureCheck label="Documentation folder" ok={validation.project_structure.has_documentation_folder} />
            </div>
            {validation.project_structure.notes.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[#E5E7EB] space-y-1.5">
                {validation.project_structure.notes.map((note, i) => {
                  const transformed = transformStructureNote(note, validation.config_files_summary.has_readme);
                  const isInfo = transformed.includes("README file is available");
                  return (
                    <p key={i} className={`text-xs flex items-start gap-1.5 ${isInfo ? "text-[#2563EB]" : "text-[#6B7280]"}`}>
                      <ChevronRight className={`h-3 w-3 shrink-0 mt-0.5 ${isInfo ? "text-[#2563EB]" : ""}`} />
                      {transformed}
                    </p>
                  );
                })}
              </div>
            )}
          </div>
        </Card>
      </motion.div>

      {/* Ready for Analysis */}
      <motion.div variants={itemVariants}>
        <Card>
          <div className="p-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${
                  validation.ready_for_analysis ? "bg-[#D1FAE5]" : "bg-[#FEE2E2]"
                }`}>
                  {validation.ready_for_analysis ? (
                    <CheckCircle2 className="h-6 w-6 text-[#059669]" />
                  ) : (
                    <XCircle className="h-6 w-6 text-[#DC2626]" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-semibold text-[#111827]">
                    {validation.ready_for_analysis
                      ? "Workspace Ready for Project Analysis"
                      : "Workspace Not Ready for Analysis"}
                  </p>
                  <p className="text-xs text-[#6B7280] mt-0.5">
                    {validation.ready_for_analysis
                      ? "All validation checks passed. You can proceed with project analysis."
                      : "Resolve the errors above before proceeding."}
                  </p>
                </div>
              </div>
              {validation.ready_for_analysis && (
                <button
                  onClick={() => navigate(`/projects/${projectId}/ready`)}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors shadow-sm shrink-0"
                >
                  Continue to Project Analysis
                  <ChevronRight className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
