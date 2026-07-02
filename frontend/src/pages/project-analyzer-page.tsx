import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Cpu,
  FileCode,
  FileText,
  FolderKanban,
  HardDrive,
  Layers,
  Package,
  RefreshCw,
  Search,
  Server,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { getProjectAnalyzer } from "@/lib/project-analyzer";
import type { AnalyzerResponse } from "@/types/project-analyzer";

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

function formatSize(bytes: number) {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(1)} GB`;
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)} KB`;
  return `${bytes} B`;
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

const LOADING_STAGES = [
  { label: "Preparing Analyzer...", desc: "Initializing project analysis engine" },
  { label: "Scanning Workspace...", desc: "Walking through project directories and files" },
  { label: "Reading Project Structure...", desc: "Analyzing folder organization and configuration" },
  { label: "Generating Summary...", desc: "Compiling analysis results and metrics" },
];

function LoadingSkeleton() {
  const [stage, setStage] = useState(0);
  const startRef = useRef(Date.now());

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Date.now() - startRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        LOADING_STAGES.length - 1,
      );
      setStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, []);

  const currentStage = LOADING_STAGES[Math.min(stage, LOADING_STAGES.length - 1)]!;

  return (
    <div className="flex flex-col items-center justify-center py-24">
      <div className="relative mb-8">
        <div className="h-16 w-16 animate-spin rounded-full border-4 border-[#E5E7EB] border-t-[#2563EB]" />
        <Cpu className="absolute left-1/2 top-1/2 h-6 w-6 -translate-x-1/2 -translate-y-1/2 text-[#2563EB]" />
      </div>
      <p className="text-lg font-semibold text-[#111827]">
        {currentStage.label}
      </p>
      <p className="mt-1 text-sm text-[#6B7280]">
        {currentStage.desc}
      </p>
      <div className="mt-6 flex gap-1.5">
        {LOADING_STAGES.map((_, i) => (
          <div
            key={i}
            className={`h-1.5 w-20 rounded-full transition-colors duration-500 ${
              i <= stage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

function SectionHeader({ icon: Icon, title }: { icon: typeof FileCode; title: string }) {
  return (
    <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-6 py-4">
      <div className="flex items-center gap-2">
        <Icon className="h-5 w-5 text-[#2563EB]" />
        <h2 className="text-base font-semibold text-[#111827]">{title}</h2>
      </div>
    </div>
  );
}

const PROJECT_TYPE_ICON: Record<string, typeof Server> = {
  "Full Stack": Layers,
  Frontend: FileCode,
  Backend: Server,
  API: Server,
  Microservice: Cpu,
  Monolith: HardDrive,
};

function TypeBadge({ type }: { type: string }) {
  const Icon = PROJECT_TYPE_ICON[type] ?? Search;
  const colors: Record<string, string> = {
    "Full Stack": "bg-[#DBEAFE] text-[#1E40AF]",
    Frontend: "bg-[#DBEAFE] text-[#1E40AF]",
    Backend: "bg-[#D1FAE5] text-[#065F46]",
    API: "bg-[#D1FAE5] text-[#065F46]",
    Microservice: "bg-[#FEF3C7] text-[#92400E]",
    Monolith: "bg-[#F3E8FF] text-[#6B21A8]",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${colors[type] ?? "bg-[#F3F4F6] text-[#6B7280]"}`}>
      <Icon className="h-3.5 w-3.5" />
      {type}
    </span>
  );
}

function Tag({ label, variant = "default" }: { label: string; variant?: "default" | "blue" | "green" | "amber" | "purple" }) {
  const styles: Record<string, string> = {
    default: "bg-[#F3F4F6] text-[#4B5563]",
    blue: "bg-[#DBEAFE] text-[#1E40AF]",
    green: "bg-[#D1FAE5] text-[#065F46]",
    amber: "bg-[#FEF3C7] text-[#92400E]",
    purple: "bg-[#F3E8FF] text-[#6B21A8]",
  };
  return (
    <span className={`inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-medium ${styles[variant]}`}>
      {label}
    </span>
  );
}

function FolderBar({ label, count, max, color }: { label: string; count: number; max: number; color: string }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 text-right text-xs font-medium text-[#6B7280]">{label}</span>
      <div className="flex-1">
        <div className="h-2.5 rounded-full bg-[#E5E7EB]">
          <div
            className="h-2.5 rounded-full transition-all duration-700"
            style={{ width: `${pct}%`, backgroundColor: color }}
          />
        </div>
      </div>
      <span className="w-8 text-right text-xs font-semibold text-[#111827]">{count}</span>
    </div>
  );
}

function ConfigRow({ label, present }: { label: string; present: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      {present ? (
        <CheckCircle2 className="h-4 w-4 shrink-0 text-[#059669]" />
      ) : (
        <XCircle className="h-4 w-4 shrink-0 text-[#9CA3AF]" />
      )}
      <span className={`text-sm ${present ? "font-medium text-[#111827]" : "text-[#6B7280]"}`}>
        {label}
      </span>
    </div>
  );
}

export function ProjectAnalyzerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<AnalyzerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const fetchAnalysis = useCallback(async (isRefresh = false) => {
    if (!projectId) return;
    if (isRefresh) setAnalyzing(true);
    else setLoading(true);
    setError(null);
    try {
      const result = await getProjectAnalyzer(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze project";
      setError(msg);
    } finally {
      setLoading(false);
      setAnalyzing(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  if (loading && !data) {
    return (
      <div className="px-6 lg:px-8 pb-6 lg:pb-8">
        <div className="mx-auto max-w-5xl">
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-6 lg:px-8 pb-6 lg:pb-8">
        <div className="mx-auto max-w-5xl">
          <Card className="p-12 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-[#DC2626]" />
            <h2 className="mt-4 text-lg font-semibold text-[#111827]">Analysis Failed</h2>
            <p className="mt-2 text-sm text-[#6B7280]">{error}</p>
            <button
              onClick={() => fetchAnalysis(true)}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#1D4ED8]"
            >
              <RefreshCw className="h-4 w-4" />
              Retry Analysis
            </button>
          </Card>
        </div>
      </div>
    );
  }

  const d = data!;
  type FolderKey = keyof AnalyzerResponse["folder_summary"];
  const folderKeys: FolderKey[] = [
    "frontend", "backend", "source", "config", "assets", "docs", "tests", "scripts", "other",
  ];
  const folderLabels: Record<FolderKey, string> = {
    frontend: "Frontend", backend: "Backend", source: "Source", config: "Config",
    assets: "Assets", docs: "Docs", tests: "Tests", scripts: "Scripts", other: "Other",
  };
  const folderColors: Record<FolderKey, string> = {
    frontend: "#2563EB", backend: "#059669", source: "#7C3AED", config: "#D97706",
    assets: "#EC4899", docs: "#06B6D4", tests: "#8B5CF6", scripts: "#F59E0B", other: "#9CA3AF",
  };
  const maxFolderCount = Math.max(
    ...folderKeys.map((k) => d.folder_summary[k] ?? 0),
    1,
  );

  type ConfigKey = keyof AnalyzerResponse["config_summary"];
  const configRows: { label: string; key: ConfigKey }[] = [
    { label: "package.json", key: "has_package_json" },
    { label: "requirements.txt", key: "has_requirements_txt" },
    { label: "Dockerfile", key: "has_dockerfile" },
    { label: "Docker Compose", key: "has_docker_compose" },
    { label: "README", key: "has_readme" },
    { label: "pyproject.toml", key: "has_pyproject_toml" },
    { label: ".env.example", key: "has_env_example" },
    { label: ".gitignore", key: "has_gitignore" },
  ];

  return (
    <div className="px-6 lg:px-8 pb-6 lg:pb-8">
      <div className="mx-auto max-w-5xl">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Header */}
          <motion.div variants={itemVariants} className="mb-8">
            <button
              onClick={() => navigate(`/projects/${projectId}/ready`)}
              className="mb-4 inline-flex items-center gap-1.5 text-sm text-[#6B7280] transition-colors hover:text-[#111827]"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Readiness
            </button>
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-[#111827]">
                Project Analyzer
              </h1>
              <TypeBadge type={d.project_type} />
            </div>
            <p className="mt-1 text-sm text-[#6B7280]">
              {d.project_name} &middot; Analyzed {formatDate(d.analyzed_at)}
            </p>
          </motion.div>

          {/* Card 1: Project Summary */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={HardDrive} title="Project Summary" />
              <div className="p-6">
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Project Name</p>
                    <p className="mt-1 text-sm font-medium text-[#111827]">{d.project_name}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Project Type</p>
                    <p className="mt-1 text-sm font-medium text-[#111827]">{d.project_type}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Workspace Status</p>
                    <p className="mt-1 text-sm font-medium text-[#111827]">{d.workspace_status}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Analyzed At</p>
                    <p className="mt-1 text-sm font-medium text-[#111827]">{formatDate(d.analyzed_at)}</p>
                  </div>
                </div>
                <div className="mt-6 grid gap-6 sm:grid-cols-3">
                  <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                    <p className="text-2xl font-bold text-[#2563EB]">{d.total_files.toLocaleString()}</p>
                    <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Total Files</p>
                  </div>
                  <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                    <p className="text-2xl font-bold text-[#059669]">{d.total_folders.toLocaleString()}</p>
                    <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Total Folders</p>
                  </div>
                  <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                    <p className="text-2xl font-bold text-[#7C3AED]">{formatSize(d.workspace_size)}</p>
                    <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Workspace Size</p>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Card 2: Folder Structure */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={FolderKanban} title="Folder Structure" />
              <div className="p-6">
                <div className="space-y-2.5">
                  {folderKeys.map((k) => (
                    <FolderBar
                      key={k}
                      label={folderLabels[k]}
                      count={d.folder_summary[k]}
                      max={maxFolderCount}
                      color={folderColors[k]}
                    />
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Card 3: Technology Stack */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Cpu} title="Technology Stack" />
              <div className="p-6">
                <div className="grid gap-6 sm:grid-cols-3">
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Languages</p>
                    {d.technology_stack.languages.length === 0 ? (
                      <p className="text-sm text-[#9CA3AF]">None detected</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {d.technology_stack.languages.map((l, i) => (
                          <Tag key={i} label={l} variant="blue" />
                        ))}
                      </div>
                    )}
                  </div>
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Frameworks</p>
                    {d.technology_stack.frameworks.length === 0 ? (
                      <p className="text-sm text-[#9CA3AF]">None detected</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {d.technology_stack.frameworks.map((f, i) => (
                          <Tag key={i} label={f} variant="green" />
                        ))}
                      </div>
                    )}
                  </div>
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Databases</p>
                    {d.technology_stack.databases.length === 0 ? (
                      <p className="text-sm text-[#9CA3AF]">None detected</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {d.technology_stack.databases.map((db, i) => (
                          <Tag key={i} label={db} variant="purple" />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Card 4: Configuration */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Package} title="Configuration" />
              <div className="p-6">
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {configRows.map((row) => (
                    <ConfigRow
                      key={row.key}
                      label={row.label}
                      present={d.config_summary[row.key] ?? false}
                    />
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Card 5: Workspace Summary */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={FileText} title="Workspace Summary" />
              <div className="p-6">
                <p className="text-sm text-[#4B5563] leading-relaxed">{d.workspace_summary}</p>
              </div>
            </Card>
          </motion.div>

          {/* Action */}
          <motion.div variants={itemVariants} className="mt-8 text-center">
            <button
              onClick={() => fetchAnalysis(true)}
              disabled={analyzing}
              className="inline-flex items-center gap-2 rounded-lg border border-[#E5E7EB] bg-white px-5 py-2.5 text-sm font-medium text-[#374151] transition-colors hover:bg-[#F9FAFB] disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${analyzing ? "animate-spin" : ""}`} />
              {analyzing ? "Re-analyzing..." : "Re-run Analysis"}
            </button>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
