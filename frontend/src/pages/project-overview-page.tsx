import { motion } from "framer-motion";
import {
  ArrowLeft,
  Braces,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Container,
  Database,
  FileCode,
  FileCog,
  FileJson,
  FileText,
  FolderKanban,
  Globe,
  HardDrive,
  Layers,
  Package,
  RefreshCw,
  Server,
  Shield,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { getProjectMetadata } from "@/lib/project-metadata";
import { getProject } from "@/lib/projects";
import type { ProjectMetadata } from "@/types/project-metadata";
import type { Project } from "@/types/project";

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
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
    <div
      className={`animate-pulse rounded-lg bg-[#E5E7EB] ${className}`}
    />
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-xl border border-[#E5E7EB] bg-white p-6">
      <Skeleton className="mb-3 h-4 w-28" />
      <div className="space-y-2">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof HardDrive;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#F3F4F6] shrink-0">
        <Icon className="h-5 w-5 text-[#6B7280]" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-[#6B7280]">{label}</p>
        <p className="text-sm font-semibold text-[#111827]">{value}</p>
      </div>
    </div>
  );
}

function TechBadge({
  icon: Icon,
  label,
}: {
  icon?: typeof Braces;
  label: string;
}) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 py-1.5 text-xs font-medium text-[#374151] shadow-sm">
      {Icon && <Icon className="h-3.5 w-3.5 text-[#6B7280]" />}
      {label}
    </span>
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

export function ProjectOverviewPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [metadata, setMetadata] = useState<ProjectMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAll = useCallback(async (isRefresh = false) => {
    if (!projectId) return;
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const [proj, meta] = await Promise.all([
        getProject(Number(projectId)),
        getProjectMetadata(Number(projectId)),
      ]);
      setProject(proj);
      setMetadata(meta);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to load project overview";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const healthChecks = useMemo(() => {
    if (!project || !metadata) return [];
    const wsReady = !!project.workspace_path;
    const metaDone = !!metadata.primary_language;
    const uploadDone = project.upload_status === "completed";
    const extractDone = project.extraction_status === "completed";
    const allGood = wsReady && metaDone && uploadDone && extractDone;
    return [
      { label: "Workspace Ready", ok: wsReady },
      { label: "Metadata Generated", ok: metaDone },
      { label: "Upload Complete", ok: uploadDone },
      { label: "Extraction Complete", ok: extractDone },
      { label: "Ready for Analysis", ok: allGood },
    ];
  }, [project, metadata]);

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
            <Skeleton className="h-5 w-36" />
            <Skeleton className="mt-1.5 h-3 w-52" />
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonCard />
          <SkeletonCard />
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
            <h2 className="text-lg font-semibold text-[#111827]">
              Project Overview
            </h2>
            <p className="text-sm text-[#6B7280]">Error loading overview</p>
          </div>
        </div>
        <Card>
          <div className="flex flex-col items-center justify-center py-24">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50 mb-4">
              <Layers className="h-7 w-7 text-[#EF4444]" />
            </div>
            <h3 className="text-lg font-medium text-[#111827]">
              Failed to load project overview
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

  if (!metadata) {
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
            <h2 className="text-lg font-semibold text-[#111827]">
              Project Overview
            </h2>
            <p className="text-sm text-[#6B7280]">
              Project Summary & Technology Information
            </p>
          </div>
        </div>
        <Card>
          <div className="flex flex-col items-center justify-center py-24">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#F3F4F6] mb-4">
              <FileCog className="h-7 w-7 text-[#6B7280]" />
            </div>
            <h3 className="text-lg font-medium text-[#111827]">
              No metadata available
            </h3>
            <p className="mt-1 text-sm text-[#6B7280] text-center max-w-sm">
              Project metadata has not been generated yet. Click refresh to scan
              the workspace.
            </p>
            <button
              onClick={() => fetchAll()}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-4 py-2 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </Card>
      </div>
    );
  }

  const statCards = [
    {
      icon: Layers,
      label: "Total Files",
      value: metadata.statistics.total_files.toLocaleString(),
    },
    {
      icon: FolderKanban,
      label: "Total Folders",
      value: metadata.statistics.total_folders.toLocaleString(),
    },
    {
      icon: FileCode,
      label: "Source Files",
      value: metadata.statistics.source_files.toLocaleString(),
    },
    {
      icon: FileJson,
      label: "Configuration Files",
      value: metadata.statistics.config_files_count.toLocaleString(),
    },
    {
      icon: FileText,
      label: "Documentation Files",
      value: metadata.statistics.documentation_files.toLocaleString(),
    },
    {
      icon: Globe,
      label: "Assets",
      value: (
        metadata.statistics.image_files +
        metadata.statistics.video_files +
        metadata.statistics.asset_files
      ).toLocaleString(),
    },
    {
      icon: HardDrive,
      label: "Workspace Size",
      value: formatSize(metadata.statistics.total_size_bytes),
    },
  ];

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
              {project?.project_name || "Project Overview"}
            </h2>
            <p className="text-sm text-[#6B7280]">
              Project Summary & Technology Information
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(`/projects/${projectId}/validation`)}
            className="inline-flex items-center gap-2 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-sm font-medium text-[#374151] hover:bg-[#F9FAFB] transition-colors"
          >
            <ClipboardCheck className="h-4 w-4" />
            Validation
          </button>
          <button
            onClick={() => fetchAll(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-sm font-medium text-[#374151] hover:bg-[#F9FAFB] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </motion.div>

      {/* Section 1 - Project Information */}
      <motion.div variants={itemVariants}>
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-semibold text-[#111827] mb-5 flex items-center gap-2">
              <Layers className="h-4 w-4 text-[#6B7280]" />
              Project Information
            </h3>
            <div className="grid gap-x-8 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <p className="text-xs text-[#6B7280]">Project Name</p>
                <p className="text-sm font-medium text-[#111827] mt-0.5">
                  {project?.project_name || "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-[#6B7280]">Project ID</p>
                <p className="text-sm font-medium text-[#111827] mt-0.5">
                  #{project?.id ?? "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-[#6B7280]">Project Type</p>
                <p className="text-sm font-medium text-[#111827] mt-0.5">
                  {metadata.project_type || "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-[#6B7280]">Upload Date</p>
                <p className="text-sm font-medium text-[#111827] mt-0.5">
                  {formatDate(project?.uploaded_at ?? null)}
                </p>
              </div>
              <div>
                <p className="text-xs text-[#6B7280]">Last Scan</p>
                <p className="text-sm font-medium text-[#111827] mt-0.5">
                  {formatDate(metadata.last_scanned_at)}
                </p>
              </div>
              <div>
                <p className="text-xs text-[#6B7280]">Workspace Status</p>
                <p className="text-sm font-medium mt-0.5 capitalize">
                  {project?.extraction_status === "completed" ? (
                    <span className="text-[#059669]">Ready</span>
                  ) : project?.extraction_status === "failed" ? (
                    <span className="text-[#DC2626]">Failed</span>
                  ) : (
                    <span className="text-[#6B7280]">Pending</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Section 2 - Technology Stack */}
      <motion.div variants={itemVariants}>
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-semibold text-[#111827] mb-5 flex items-center gap-2">
              <Braces className="h-4 w-4 text-[#6B7280]" />
              Technology Stack
            </h3>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {/* Primary Language */}
              <div>
                <p className="text-xs text-[#6B7280] mb-2">Primary Language</p>
                {metadata.primary_language ? (
                  <TechBadge icon={FileCode} label={metadata.primary_language} />
                ) : (
                  <span className="text-sm text-[#9CA3AF]">Not detected</span>
                )}
              </div>

              {/* Secondary Languages */}
              <div>
                <p className="text-xs text-[#6B7280] mb-2">
                  Secondary Languages
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {metadata.secondary_languages.length > 0 ? (
                    metadata.secondary_languages.map((lang) => (
                      <TechBadge key={lang} label={lang} />
                    ))
                  ) : (
                    <span className="text-sm text-[#9CA3AF]">None</span>
                  )}
                </div>
              </div>

              {/* Framework */}
              <div>
                <p className="text-xs text-[#6B7280] mb-2">Framework</p>
                {metadata.frameworks.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {metadata.frameworks.map((fw) => (
                      <TechBadge key={fw} icon={Braces} label={fw} />
                    ))}
                  </div>
                ) : (
                  <span className="text-sm text-[#9CA3AF]">Not detected</span>
                )}
              </div>

              {/* Package Manager */}
              <div>
                <p className="text-xs text-[#6B7280] mb-2">Package Manager</p>
                {metadata.package_manager ? (
                  <TechBadge
                    icon={Package}
                    label={metadata.package_manager}
                  />
                ) : (
                  <span className="text-sm text-[#9CA3AF]">Not detected</span>
                )}
              </div>

              {/* Databases */}
              <div>
                <p className="text-xs text-[#6B7280] mb-2">Databases</p>
                <div className="flex flex-wrap gap-1.5">
                  {metadata.databases.length > 0 ? (
                    metadata.databases.map((db) => (
                      <TechBadge key={db} icon={Database} label={db} />
                    ))
                  ) : (
                    <span className="text-sm text-[#9CA3AF]">None detected</span>
                  )}
                </div>
              </div>

              {/* CI/CD */}
              <div>
                <p className="text-xs text-[#6B7280] mb-2">CI/CD</p>
                <div className="flex flex-wrap gap-1.5">
                  {metadata.devops.ci_cd.length > 0 ? (
                    metadata.devops.ci_cd.map((ci) => (
                      <TechBadge key={ci} icon={Shield} label={ci} />
                    ))
                  ) : (
                    <span className="text-sm text-[#9CA3AF]">None detected</span>
                  )}
                </div>
              </div>
            </div>

            {/* Docker row */}
            <div className="mt-5 pt-5 border-t border-[#E5E7EB]">
              <p className="text-xs text-[#6B7280] mb-2">Container & Orchestration</p>
              <div className="flex flex-wrap gap-2">
                {metadata.devops.docker ? (
                  <TechBadge icon={Container} label="Docker" />
                ) : (
                  <span className="text-xs text-[#9CA3AF]">No Docker</span>
                )}
                {metadata.devops.docker_compose && (
                  <TechBadge icon={Container} label="Docker Compose" />
                )}
                {metadata.devops.kubernetes && (
                  <TechBadge icon={Server} label="Kubernetes" />
                )}
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Section 3 - Project Statistics */}
      <motion.div variants={itemVariants}>
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-semibold text-[#111827] mb-5 flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-[#6B7280]" />
              Project Statistics
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7">
              {statCards.map((card) => (
                <StatCard key={card.label} {...card} />
              ))}
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Section 4 - Configuration Files + Language Breakdown */}
      <motion.div
        variants={itemVariants}
        className="grid gap-6 lg:grid-cols-2"
      >
        {/* Config Files */}
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-semibold text-[#111827] mb-5 flex items-center gap-2">
              <FileCog className="h-4 w-4 text-[#6B7280]" />
              Configuration Files
            </h3>
            {metadata.config_files.length > 0 ? (
              <div className="space-y-1">
                {metadata.config_files.map((file) => (
                  <div
                    key={file}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#374151] hover:bg-[#F9FAFB] transition-colors"
                  >
                    <FileCode className="h-4 w-4 text-[#6B7280] shrink-0" />
                    <span className="truncate font-mono text-xs">{file}</span>
                    <ChevronRight className="h-3 w-3 text-[#9CA3AF] ml-auto shrink-0" />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[#9CA3AF]">
                No configuration files detected
              </p>
            )}
          </div>
        </Card>

        {/* Language Breakdown */}
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-semibold text-[#111827] mb-5 flex items-center gap-2">
              <Globe className="h-4 w-4 text-[#6B7280]" />
              Languages Breakdown
            </h3>
            {Object.keys(metadata.languages).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(metadata.languages)
                  .sort(([, a], [, b]) => b - a)
                  .map(([lang, count]) => {
                    const maxCount = Object.values(metadata.languages).reduce(
                      (max, c) => Math.max(max, c),
                      0,
                    );
                    const pct = Math.round((count / maxCount) * 100);
                    return (
                      <div key={lang}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-[#374151] font-medium">
                            {lang}
                          </span>
                          <span className="text-[#6B7280] text-xs">
                            {count} file{count !== 1 ? "s" : ""}
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-[#F3F4F6]">
                          <div
                            className="h-2 rounded-full bg-[#2563EB] transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            ) : (
              <p className="text-sm text-[#9CA3AF]">
                No languages detected
              </p>
            )}
          </div>
        </Card>
      </motion.div>

      {/* Section 5 - Project Health Summary */}
      <motion.div variants={itemVariants}>
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-semibold text-[#111827] mb-5 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#6B7280]" />
              Project Health Summary
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {healthChecks.map((check) => (
                <div
                  key={check.label}
                  className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${
                    check.ok
                      ? "border-[#D1FAE5] bg-[#F0FDF4]"
                      : "border-[#E5E7EB] bg-white"
                  }`}
                >
                  <CheckCircle2
                    className={`h-5 w-5 shrink-0 ${
                      check.ok ? "text-[#059669]" : "text-[#9CA3AF]"
                    }`}
                  />
                  <span
                    className={`text-sm font-medium ${
                      check.ok ? "text-[#065F46]" : "text-[#6B7280]"
                    }`}
                  >
                    {check.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
