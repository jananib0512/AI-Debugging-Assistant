import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  BookOpen,
  Box,
  CheckCircle2,
  CircuitBoard,
  Clock,
  ClipboardCheck,
  Cpu,
  FileCode,
  FileText,
  FolderKanban,
  Globe,
  HardDrive,
  Layers,
  Library,
  Loader2,
  Lock,
  Monitor,
  Play,
  RefreshCw,
  Search,
  Server,
  Shield,
  Terminal,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { getProject } from "@/lib/projects";
import { getProjectMetadata } from "@/lib/project-metadata";
import { getWorkspaceValidation } from "@/lib/workspace-validation";
import type { Project } from "@/types/project";
import type { ProjectMetadata } from "@/types/project-metadata";
import type { WorkspaceValidation } from "@/types/workspace-validation";

const ANALYSIS_SCOPE_ITEMS = [
  { icon: FolderKanban, label: "Project Structure", desc: "Analyze folder hierarchy and workspace layout" },
  { icon: FileCode, label: "Entry Points", desc: "Locate main application entry files" },
  { icon: Layers, label: "Architecture Pattern", desc: "Identify MVC, Layered, Clean, or other architecture" },
  { icon: Search, label: "Important Directories", desc: "Detect src, app, api, controllers, services, and more" },
  { icon: Box, label: "Module Organization", desc: "Map detected modules and their relationships" },
];

const PROJECT_TYPE_ICON: Record<string, typeof Globe> = {
  "Full Stack": Globe,
  Frontend: Monitor,
  Backend: Server,
  API: Server,
  Microservice: CircuitBoard,
  Monolith: HardDrive,
  Desktop: Monitor,
  CLI: Terminal,
  Library: Library,
  Monorepo: Box,
  Unknown: Search,
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-lg bg-[#E5E7EB] ${className}`} />
  );
}

function ReadinessRow({ label, status }: { label: string; status: "ready" | "completed" | "passed" | "not_ready" | "failed" | "pending" }) {
  const getConfig = (s: typeof status) => {
    switch (s) {
      case "ready": return { icon: CheckCircle2, color: "text-[#059669]", label: "Ready" };
      case "completed": return { icon: CheckCircle2, color: "text-[#059669]", label: "Completed" };
      case "passed": return { icon: CheckCircle2, color: "text-[#059669]", label: "Passed" };
      case "not_ready": return { icon: AlertTriangle, color: "text-[#DC2626]", label: "Not Ready" };
      case "failed": return { icon: AlertTriangle, color: "text-[#DC2626]", label: "Failed" };
      default: return { icon: Clock, color: "text-[#9CA3AF]", label: "Pending" };
    }
  };
  const { icon: Icon, color, label: statusLabel } = getConfig(status);
  return (
    <div className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-3">
      <span className="text-sm font-medium text-[#374151]">{label}</span>
      <span className={`inline-flex items-center gap-1.5 text-sm font-semibold ${color}`}>
        <Icon className="h-4 w-4" />
        {statusLabel}
      </span>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-[#F3F4F6] py-2.5 last:border-0">
      <span className="text-sm text-[#6B7280]">{label}</span>
      <span className="text-sm font-medium text-[#111827]">{value}</span>
    </div>
  );
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

function estimateComplexity(sourceFiles: number | null): string {
  if (!sourceFiles || sourceFiles < 50) return "Low";
  if (sourceFiles < 200) return "Medium";
  return "High";
}

function estimateTime(sizeBytes: number | null, sourceFiles: number | null): string {
  if (!sizeBytes || !sourceFiles) return "10\u201320 seconds";
  if (sizeBytes < 5 * 1024 * 1024 && sourceFiles < 50) return "5\u201310 seconds";
  if (sizeBytes < 50 * 1024 * 1024 && sourceFiles < 200) return "10\u201320 seconds";
  if (sizeBytes < 200 * 1024 * 1024) return "20\u201340 seconds";
  return "40\u201360 seconds";
}

function estimateProjectSize(sizeBytes: number | null): string {
  if (!sizeBytes) return "Unknown";
  if (sizeBytes < 5 * 1024 * 1024) return "Small";
  if (sizeBytes < 50 * 1024 * 1024) return "Medium";
  if (sizeBytes < 200 * 1024 * 1024) return "Large";
  return "Very Large";
}

export function AnalysisReadinessPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [metadata, setMetadata] = useState<ProjectMetadata | null>(null);
  const [validation, setValidation] = useState<WorkspaceValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [preparing, setPreparing] = useState(false);
  const [prepareMsg, setPrepareMsg] = useState("");
  const prepareStartRef = useRef(0);

  const fetchAll = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const [proj, meta, val] = await Promise.all([
        getProject(Number(projectId)),
        getProjectMetadata(Number(projectId)),
        getWorkspaceValidation(Number(projectId)),
      ]);
      setProject(proj);
      setMetadata(meta);
      setValidation(val);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load project data";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const checks = {
    projectExists: project !== null,
    workspaceExtracted: project?.extraction_status === "extracted",
    metadataReady: metadata !== null && metadata.last_scanned_at !== null,
    validationExists: validation !== null,
    validationReady: validation?.ready_for_analysis === true,
  };
  const allChecksPass = Object.values(checks).every(Boolean);
  const failedChecks: string[] = [];
  if (!checks.projectExists) failedChecks.push("Project not found.");
  if (!checks.workspaceExtracted) failedChecks.push("Project has not been extracted.");
  if (!checks.metadataReady) failedChecks.push("Metadata has not been generated.");
  if (!checks.validationExists) failedChecks.push("Workspace validation has not completed.");
  if (!checks.validationReady) failedChecks.push("Workspace validation did not pass.");

  const handleStartAnalysis = () => {
    if (!allChecksPass) return;
    if (!projectId) return;
    setPreparing(true);
    setPrepareMsg("Checking workspace...");
    prepareStartRef.current = Date.now();

    const steps = [
      { msg: "Checking workspace...", at: 0 },
      { msg: "Checking metadata...", at: 800 },
      { msg: "Preparing project...", at: 1600 },
    ];
    let current = 0;
    const tick = () => {
      const elapsed = Date.now() - prepareStartRef.current;
      while (current < steps.length - 1 && elapsed >= steps[current + 1]!.at) {
        current++;
        setPrepareMsg(steps[current]!.msg);
      }
      if (elapsed < 2400) {
        requestAnimationFrame(tick);
      } else {
        navigate(`/projects/${projectId}/analyzer`);
      }
    };
    requestAnimationFrame(tick);
  };

  if (loading) {
    return (
      <div className="px-6 lg:px-8 pb-6 lg:pb-8">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>
          <Skeleton className="h-44 w-full" />
          <div className="grid gap-6 lg:grid-cols-2">
            <Skeleton className="h-52 w-full" />
            <Skeleton className="h-52 w-full" />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Skeleton className="h-52 w-full" />
            <Skeleton className="h-52 w-full" />
          </div>
          <Skeleton className="h-44 w-full" />
          <Skeleton className="h-36 w-full" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-6 lg:px-8 pb-6 lg:pb-8">
        <div className="mx-auto max-w-4xl">
          <Card className="p-12 text-center">
            <XCircle className="mx-auto h-12 w-12 text-[#DC2626]" />
            <h2 className="mt-4 text-lg font-semibold text-[#111827]">Failed to Load Readiness Data</h2>
            <p className="mt-2 text-sm text-[#6B7280]">{error}</p>
            <button
              onClick={fetchAll}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#1D4ED8]"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </button>
          </Card>
        </div>
      </div>
    );
  }

  const stats = metadata?.statistics;
  const sourceFiles = stats?.source_files ?? null;
  const sizeBytes = stats?.total_size_bytes ?? null;
  const projType = metadata?.project_type ?? (validation?.project_structure.has_backend === true && validation?.project_structure.has_frontend === true ? "Full Stack" : "Unknown");
  const TypeIcon = PROJECT_TYPE_ICON[projType] ?? Search;

  if (!allChecksPass) {
    return (
      <div className="px-6 lg:px-8 pb-6 lg:pb-8">
        <div className="mx-auto max-w-4xl">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div variants={itemVariants} className="mb-8">
              <button
                onClick={() => navigate(`/projects/${projectId}/validation`)}
                className="mb-4 inline-flex items-center gap-1.5 text-sm text-[#6B7280] transition-colors hover:text-[#111827]"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Validation
              </button>
            </motion.div>
            <motion.div variants={itemVariants}>
              <Card className="p-12 text-center">
                <Lock className="mx-auto h-12 w-12 text-[#9CA3AF]" />
                <h2 className="mt-4 text-lg font-semibold text-[#111827]">Project Not Ready for Analysis</h2>
                <div className="mx-auto mt-4 max-w-md space-y-2 text-left">
                  {failedChecks.map((msg, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-[#DC2626]">
                      <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
                      <span>{msg}</span>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-sm text-[#6B7280]">
                  Resolve the issues above before proceeding with project analysis.
                </p>
                <button
                  onClick={() => navigate(`/projects/${projectId}/validation`)}
                  className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#1D4ED8]"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Complete Workspace Validation
                </button>
              </Card>
            </motion.div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-6 lg:px-8 pb-6 lg:pb-8">
      <div className="mx-auto max-w-4xl">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Header */}
          <motion.div variants={itemVariants} className="mb-8">
            <button
              onClick={() => navigate(`/projects/${projectId}/validation`)}
              className="mb-4 inline-flex items-center gap-1.5 text-sm text-[#6B7280] transition-colors hover:text-[#111827]"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Validation
            </button>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#DBEAFE]">
                <ClipboardCheck className="h-5 w-5 text-[#2563EB]" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[#111827]">Project Ready for Analysis</h1>
                <p className="mt-0.5 text-sm text-[#6B7280]">
                  Your project has been successfully prepared and is ready for structural analysis.
                </p>
              </div>
            </div>
          </motion.div>

          {/* Section 1: Project Summary */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6">
              <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-6 py-4">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-[#2563EB]" />
                  <h2 className="text-base font-semibold text-[#111827]">Project Summary</h2>
                </div>
              </div>
              <div className="p-6">
                <div className="grid gap-x-8 gap-y-1 sm:grid-cols-2">
                  <InfoRow label="Project Name" value={project?.project_name ?? "—"} />
                  <InfoRow label="Project ID" value={project ? `#${project.id}` : "—"} />
                  <InfoRow
                    label="Project Type"
                    value={
                      <span className="inline-flex items-center gap-1.5">
                        <TypeIcon className="h-3.5 w-3.5 text-[#2563EB]" />
                        {projType}
                      </span>
                    }
                  />
                  <InfoRow
                    label="Workspace Status"
                    value={
                      <span className="inline-flex items-center gap-1 text-[#059669]">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Extracted
                      </span>
                    }
                  />
                  <InfoRow label="Upload Date" value={formatDate(project?.uploaded_at ?? null)} />
                  <InfoRow label="Last Validation" value="Just now" />
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Section 2: Technology Summary */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6">
              <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-6 py-4">
                <div className="flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-[#2563EB]" />
                  <h2 className="text-base font-semibold text-[#111827]">Technology Summary</h2>
                </div>
              </div>
              <div className="p-6">
                <div className="grid gap-x-8 gap-y-1 sm:grid-cols-2">
                  <InfoRow label="Primary Language" value={metadata?.primary_language ?? "—"} />
                  <InfoRow
                    label="Frameworks"
                    value={
                      metadata?.frameworks?.length
                        ? metadata.frameworks.join(", ")
                        : "—"
                    }
                  />
                  <InfoRow label="Package Manager" value={metadata?.package_manager ?? "—"} />
                  <InfoRow label="Databases" value={metadata?.databases?.length ? metadata.databases.join(", ") : "None detected"} />
                  <InfoRow label="Docker" value={metadata?.devops?.docker ? "Configured" : "Not configured"} />
                  <InfoRow label="Config Files Found" value={metadata?.config_files?.length ? `${metadata.config_files.length} file${metadata.config_files.length > 1 ? "s" : ""}` : "None"} />
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Section 3: Project Statistics */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6">
              <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-6 py-4">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-[#2563EB]" />
                  <h2 className="text-base font-semibold text-[#111827]">Project Statistics</h2>
                </div>
              </div>
              <div className="p-6">
                <div className="grid gap-x-8 gap-y-1 sm:grid-cols-2">
                  <InfoRow label="Total Files" value={stats?.total_files != null ? String(stats.total_files) : "—"} />
                  <InfoRow label="Total Folders" value={stats?.total_folders != null ? String(stats.total_folders) : "—"} />
                  <InfoRow label="Source Files" value={stats?.source_files != null ? String(stats.source_files) : "—"} />
                  <InfoRow label="Configuration Files" value={stats?.config_files_count != null ? String(stats.config_files_count) : "—"} />
                  <InfoRow label="Documentation Files" value={stats?.documentation_files != null ? String(stats.documentation_files) : "—"} />
                  <InfoRow label="Workspace Size" value={sizeBytes != null ? formatBytes(sizeBytes) : "—"} />
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Section 4: Analysis Scope */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6">
              <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-6 py-4">
                <div className="flex items-center gap-2">
                  <Layers className="h-5 w-5 text-[#2563EB]" />
                  <h2 className="text-base font-semibold text-[#111827]">Analysis Scope</h2>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {ANALYSIS_SCOPE_ITEMS.map((item, i) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] bg-white px-4 py-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[#DBEAFE]">
                        <item.icon className="h-4 w-4 text-[#2563EB]" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-[#111827]">{item.label}</p>
                        <p className="text-xs text-[#6B7280]">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Section 5: Readiness Status */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6">
              <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-6 py-4">
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-[#2563EB]" />
                  <h2 className="text-base font-semibold text-[#111827]">Readiness Status</h2>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  <ReadinessRow
                    label="Workspace"
                    status={checks.workspaceExtracted ? "ready" : "not_ready"}
                  />
                  <ReadinessRow
                    label="Metadata"
                    status={checks.metadataReady ? "completed" : "pending"}
                  />
                  <ReadinessRow
                    label="Validation"
                    status={checks.validationReady ? "passed" : "failed"}
                  />
                  <ReadinessRow
                    label="Project"
                    status={allChecksPass ? "ready" : "not_ready"}
                  />
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Section 6: Estimated Analysis */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6">
              <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-6 py-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-[#2563EB]" />
                  <h2 className="text-base font-semibold text-[#111827]">Estimated Analysis</h2>
                </div>
              </div>
              <div className="p-6">
                <div className="grid gap-x-8 gap-y-1 sm:grid-cols-3">
                  <div className="border-b border-[#F3F4F6] py-2.5 sm:border-0">
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Estimated Time</p>
                    <p className="mt-1 text-sm font-semibold text-[#111827]">{estimateTime(sizeBytes, sourceFiles)}</p>
                  </div>
                  <div className="border-b border-[#F3F4F6] py-2.5 sm:border-0">
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Project Complexity</p>
                    <p className="mt-1 text-sm font-semibold text-[#111827]">{estimateComplexity(sourceFiles)}</p>
                  </div>
                  <div className="py-2.5">
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Project Size</p>
                    <p className="mt-1 text-sm font-semibold text-[#111827]">{estimateProjectSize(sizeBytes)}</p>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Section 7: Analysis Notes */}
          <motion.div variants={itemVariants}>
            <Card className="mb-8 border-[#DBEAFE] bg-[#EFF6FF]">
              <div className="p-6">
                <div className="flex items-start gap-3">
                  <BookOpen className="h-5 w-5 text-[#2563EB] shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-semibold text-[#1E40AF]">Analysis Notes</h3>
                    <div className="mt-2 space-y-1.5 text-sm text-[#1E40AF]/80">
                      <p>The upcoming Project Analyzer will inspect the project structure.</p>
                      <p>It will <strong>not</strong> modify your project.</p>
                      <p>It will <strong>not</strong> execute project code.</p>
                      <p>It will <strong>not</strong> send project files outside the system.</p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Actions */}
          <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-center gap-4 pb-8">
            <button
              onClick={() => navigate(`/projects/${projectId}/overview`)}
              disabled={preparing}
              className="inline-flex items-center gap-2 rounded-lg border border-[#E5E7EB] bg-white px-5 py-2.5 text-sm font-medium text-[#374151] transition-colors hover:bg-[#F9FAFB] disabled:opacity-50"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Project Overview
            </button>
            <button
              onClick={handleStartAnalysis}
              disabled={!allChecksPass || preparing}
              className={`inline-flex items-center gap-2 rounded-lg px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-colors ${
                preparing
                  ? "bg-[#60A5FA] cursor-wait"
                  : allChecksPass
                    ? "bg-[#2563EB] hover:bg-[#1D4ED8]"
                    : "bg-[#9CA3AF] cursor-not-allowed"
              }`}
            >
              {preparing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {preparing ? prepareMsg : "Start Project Analysis"}
            </button>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
