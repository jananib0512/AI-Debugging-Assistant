import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Cpu,
  Server,
  FolderKanban,
  Box,
  Building2,
  GitBranch,
  Settings,
  Package,
  Shield,
  FileSearch,
  RefreshCw,
} from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";

function formatSize(bytes: number) {
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + " GB";
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
  if (bytes >= 1024) return (bytes / 1024).toFixed(0) + " KB";
  return bytes + " B";
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

const categoryItems = [
  { path: "framework", label: "Framework Intelligence", icon: Cpu, desc: "Detected frameworks, versions, confidence scores, and compatibility analysis." },
  { path: "technology", label: "Technology Stack", icon: Server, desc: "Languages, databases, package managers, ORMs, and build tools identified in the project." },
  { path: "folders", label: "Folder Structure", icon: FolderKanban, desc: "Directory classification, folder purpose detection, and file type distribution." },
  { path: "modules", label: "Module Detection", icon: Box, desc: "Standard, core, and optional modules detected across the project workspace." },
  { path: "architecture", label: "Architecture Detection", icon: Building2, desc: "Architecture pattern identification, layer analysis, health scores, and recommendations." },
  { path: "entry-points", label: "Entry Point Detection", icon: GitBranch, desc: "Application entry points, alternative endpoints, and framework-specific starters." },
  { path: "configuration", label: "Configuration Intelligence", icon: Settings, desc: "Config file detection, validation, security checks, and environment setup." },
  { path: "dependencies", label: "Dependency Analysis", icon: Package, desc: "Dependency validation, version checks, deprecated packages, and health scoring." },
  { path: "recommendations", label: "AI Recommendations", icon: Shield, desc: "Project health, risks, scalability, performance, security insights, and readiness scores." },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.04 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

export function Overview() {
  const navigate = useNavigate();
  const analysis = useAnalysis();
  const { data, loading, error, analyzing, refresh } = analysis;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative mb-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        </div>
        <p className="text-sm font-medium text-[#111827]">Analyzing project...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Gathering intelligence across all modules.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Analysis failed</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button
          onClick={() => refresh(true)}
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <FileSearch className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No analysis data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Upload and extract a project to begin analysis.</p>
      </div>
    );
  }

  const tech = data.technology_stack;
  const entry = analysis.entryPoints?.primary_entry_point;
  const arch = analysis.architecture?.primary_architecture;
  const fw = analysis.frameworks?.primary_framework;
  const mods = analysis.modules?.summary;
  const insights = analysis.projectInsights;
  const validation = analysis.validationResult;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">

      {/* Hero */}
      <motion.div variants={itemVariants} className="rounded-xl border border-[#E5E7EB] bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-[#93C5FD]">Project Analyzer</p>
            <h1 className="mt-1 text-2xl font-bold">{data.project_name}</h1>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="inline-flex items-center rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-medium backdrop-blur-sm">{data.project_type}</span>
              <span className="inline-flex items-center rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-medium backdrop-blur-sm">{data.workspace_status}</span>
              <span className="inline-flex items-center rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-medium backdrop-blur-sm">{data.total_files} files</span>
              <span className="inline-flex items-center rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-medium backdrop-blur-sm">{data.total_folders} folders</span>
            </div>
          </div>
          <button
            onClick={() => refresh(true)}
            disabled={analyzing}
            className="inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white backdrop-blur-sm transition-colors hover:bg-white/30 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${analyzing ? "animate-spin" : ""}`} />
            {analyzing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </motion.div>

      {/* Summary Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Type</p>
          <p className="mt-1 text-sm font-semibold text-[#111827] capitalize">{data.project_type}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Framework</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{fw?.name || "—"}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Architecture</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{arch?.architecture || "—"}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Languages</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{tech?.languages?.length ? tech.languages.join(", ") : "—"}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Database</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{tech?.databases?.length ? tech.databases.join(", ") : "—"}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Entry Point</p>
          <p className="mt-1 text-sm font-semibold text-[#111827] truncate">{entry?.entry_file || "—"}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Modules</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{mods?.detected_count ?? 0}/{mods?.total_modules ?? 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Readiness</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{insights?.health_score?.score ?? "—"}%</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Config Health</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{analysis.configIntel?.health?.score ?? "—"}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Consistency</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{validation?.consistency_score ?? "—"}%</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Workspace</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">{formatSize(data.workspace_size)}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Analyzed</p>
          <p className="mt-1 text-xs font-medium text-[#111827]">{formatDate(data.analyzed_at)}</p>
        </div>
      </motion.div>

      {/* Category Cards */}
      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        {categoryItems.map((cat) => {
          const Icon = cat.icon;
          return (
            <div
              key={cat.path}
              className="group cursor-pointer rounded-xl border border-[#E5E7EB] bg-white p-5 transition-all hover:border-[#2563EB] hover:shadow-md"
              onClick={() => navigate(cat.path)}
            >
              <div className="flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#EFF6FF]">
                  <Icon className="h-5 w-5 text-[#2563EB]" />
                </div>
                <span className="inline-flex items-center rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#6B7280]">View Details →</span>
              </div>
              <h3 className="mt-4 text-sm font-semibold text-[#111827]">{cat.label}</h3>
              <p className="mt-1 text-xs leading-relaxed text-[#6B7280]">{cat.desc}</p>
            </div>
          );
        })}
      </motion.div>

      {/* Quick Stats Footer */}
      <motion.div variants={itemVariants} className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Summary</p>
        <p className="mt-1 text-sm leading-relaxed text-[#374151]">{data.workspace_summary}</p>
      </motion.div>

    </motion.div>
  );
}
