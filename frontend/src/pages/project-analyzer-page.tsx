import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  Box,
  Building2,
  CheckCircle2,
  ChevronDown,
  Code,
  ListChecks,
  Cpu,
  FileCode,
  FileSearch,
  FileText,
  FolderKanban,
  GitBranch,
  Grid3X3,
  HardDrive,
  Info,
  Layers,
  Lightbulb,
  Monitor,
  Package,
  RefreshCw,
  Search,
  Server,
  Settings,
  Shield,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { getAnalyzerValidation, getArchitecture, getCodeIntelligence, getConfiguration, getEntryPoints, getFrameworks, getModules, getProjectAnalyzer, getProjectInsights, getProjectIntelligence } from "@/lib/project-analyzer";
import type {
  AnalyzerResponse,
  AnalyzerValidationResponse,
  ArchitectureDetectionResponse,
  ConfigurationIntelligenceResponse,
  EntryPointDetectionResponse,
  FrameworkIntelligenceResponse,
  ModuleDetectionResponse,
  ProjectInsightsResponse,
  ProjectIntelligenceResponse,
  SourceCodeIntelligenceResponse,
} from "@/types/project-analyzer";

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

function TechRow({ tech: t }: { tech: { name: string; version: string | null; confidence: number; reason: string } }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-[#111827]">{t.name}</p>
          <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2 py-0.5 text-xs font-medium text-[#1E40AF]">
            {t.confidence}%
          </span>
          {t.version && (
            <span className="text-xs text-[#6B7280]">v{t.version}</span>
          )}
        </div>
        <p className="truncate text-xs text-[#9CA3AF]" title={t.reason}>{t.reason}</p>
      </div>
      <CheckCircle2 className="ml-2 h-4 w-4 shrink-0 text-[#059669]" />
    </div>
  );
}

function CategorizedTechRow({ tech: t, colorClass }: { tech: { name: string; version: string | null; confidence: number; reason: string; detection_source: string }; colorClass: string }) {
  return (
    <div className={`flex items-center justify-between rounded-lg border border-[#E5E7EB] border-l-4 px-4 py-3 ${colorClass}`}>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-[#111827]">{t.name}</p>
          <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2 py-0.5 text-xs font-medium text-[#1E40AF]">
            {t.confidence}%
          </span>
          {t.version && (
            <span className="text-xs text-[#6B7280]">v{t.version}</span>
          )}
        </div>
        <p className="truncate text-xs text-[#9CA3AF]" title={t.reason}>
          {t.detection_source}
        </p>
      </div>
      <CheckCircle2 className="ml-2 h-4 w-4 shrink-0 text-[#059669]" />
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

const EP_LOADING_STAGES = [
  "Detecting Entry Points...",
  "Scanning Project Structure...",
  "Checking Configuration Files...",
  "Ranking Candidates...",
];

const ARCH_LOADING_STAGES = [
  "Analyzing Architecture...",
  "Scanning Directory Layout...",
  "Identifying Layers...",
  "Ranking Architectural Patterns...",
];

const MOD_LOADING_STAGES = [
  "Scanning Project Modules...",
  "Inspecting Folder Structure...",
  "Generating Module Summary...",
];

const FW_LOADING_STAGES = [
  "Detecting Technology Stack...",
  "Reading Configuration Files...",
  "Identifying Frameworks...",
  "Generating Framework Summary...",
];

const CI_LOADING_STAGES = [
  "Inspecting Configuration...",
  "Checking Project Files...",
  "Evaluating Environment...",
  "Generating Configuration Summary...",
];

const PI_LOADING_STAGES = [
  "Computing Code Metrics...",
  "Analyzing Complexity...",
  "Detecting Code Issues...",
  "Generating Recommendations...",
];

const INSIGHTS_LOADING_STAGES = [
  "Analyzing Project Health...",
  "Evaluating Architecture...",
  "Assessing Risks...",
  "Generating Insights...",
];

const VALIDATION_LOADING_STAGES = [
  "Checking Framework Consistency...",
  "Validating Architecture...",
  "Scanning for Contradictions...",
  "Generating Validation Report...",
];

const CODE_INTEL_LOADING_STAGES = [
  "Discovering Source Files...",
  "Parsing Classes & Functions...",
  "Analyzing Imports...",
  "Building Code Index...",
];

export function ProjectAnalyzerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<AnalyzerResponse | null>(null);
  const [entryPoints, setEntryPoints] = useState<EntryPointDetectionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [epLoading, setEpLoading] = useState(true);
  const [epStage, setEpStage] = useState(0);
  const epStartRef = useRef(Date.now());
  const [architecture, setArchitecture] = useState<ArchitectureDetectionResponse | null>(null);
  const [archLoading, setArchLoading] = useState(true);
  const [archStage, setArchStage] = useState(0);
  const archStartRef = useRef(Date.now());
  const [modules, setModules] = useState<ModuleDetectionResponse | null>(null);
  const [modLoading, setModLoading] = useState(true);
  const [modStage, setModStage] = useState(0);
  const modStartRef = useRef(Date.now());
  const [frameworks, setFrameworks] = useState<FrameworkIntelligenceResponse | null>(null);
  const [fwLoading, setFwLoading] = useState(true);
  const [fwStage, setFwStage] = useState(0);
  const fwStartRef = useRef(Date.now());
  const [configIntel, setConfigIntel] = useState<ConfigurationIntelligenceResponse | null>(null);
  const [ciLoading, setCiLoading] = useState(true);
  const [ciStage, setCiStage] = useState(0);
  const ciStartRef = useRef(Date.now());
  const [projectIntel, setProjectIntel] = useState<ProjectIntelligenceResponse | null>(null);
  const [piLoading, setPiLoading] = useState(true);
  const [piStage, setPiStage] = useState(0);
  const piStartRef = useRef(Date.now());
  const [projectInsights, setProjectInsights] = useState<ProjectInsightsResponse | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(true);
  const [insightsStage, setInsightsStage] = useState(0);
  const insightsStartRef = useRef(Date.now());
  const [validationResult, setValidationResult] = useState<AnalyzerValidationResponse | null>(null);
  const [validationLoading, setValidationLoading] = useState(true);
  const [validationStage, setValidationStage] = useState(0);
  const validationStartRef = useRef(Date.now());
  const [codeIntel, setCodeIntel] = useState<SourceCodeIntelligenceResponse | null>(null);
  const [codeIntelLoading, setCodeIntelLoading] = useState(true);
  const [codeIntelStage, setCodeIntelStage] = useState(0);
  const codeIntelStartRef = useRef(Date.now());
  const [ciSearch, setCiSearch] = useState("");

  const fetchAnalysis = useCallback(async (isRefresh = false) => {
    if (!projectId) return;
    if (isRefresh) setAnalyzing(true);
    else setLoading(true);
    setError(null);
    setEpLoading(true);
    epStartRef.current = Date.now();
    setArchLoading(true);
    archStartRef.current = Date.now();
    setModLoading(true);
    modStartRef.current = Date.now();
    setFwLoading(true);
    fwStartRef.current = Date.now();
    setCodeIntelLoading(true);
    codeIntelStartRef.current = Date.now();
    setValidationLoading(true);
    validationStartRef.current = Date.now();
    setInsightsLoading(true);
    insightsStartRef.current = Date.now();
    setPiLoading(true);
    piStartRef.current = Date.now();
    setCiLoading(true);
    ciStartRef.current = Date.now();
    try {
      const [result, epResult, archResult, modResult, fwResult, ciResult, piResult, insightsResult, validationResultData, codeIntelResult] = await Promise.all([
        getProjectAnalyzer(Number(projectId)),
        getEntryPoints(Number(projectId)),
        getArchitecture(Number(projectId)),
        getModules(Number(projectId)),
        getFrameworks(Number(projectId)),
        getConfiguration(Number(projectId)),
        getProjectIntelligence(Number(projectId)),
        getProjectInsights(Number(projectId)),
        getAnalyzerValidation(Number(projectId)),
        getCodeIntelligence(Number(projectId)),
      ]);
      setData(result);
      setEntryPoints(epResult);
      setArchitecture(archResult);
      setModules(modResult);
      setFrameworks(fwResult);
      setConfigIntel(ciResult);
      setProjectIntel(piResult);
      setProjectInsights(insightsResult);
      setValidationResult(validationResultData);
      setCodeIntel(codeIntelResult);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze project";
      setError(msg);
    } finally {
      setLoading(false);
      setAnalyzing(false);
      setEpLoading(false);
      setArchLoading(false);
      setModLoading(false);
      setFwLoading(false);
      setPiLoading(false);
      setInsightsLoading(false);
      setCiLoading(false);
      setCodeIntelLoading(false);
      setValidationLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  useEffect(() => {
    if (!epLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - epStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        EP_LOADING_STAGES.length - 1,
      );
      setEpStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [epLoading]);

  useEffect(() => {
    if (!archLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - archStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        ARCH_LOADING_STAGES.length - 1,
      );
      setArchStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [archLoading]);

  useEffect(() => {
    if (!modLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - modStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        MOD_LOADING_STAGES.length - 1,
      );
      setModStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [modLoading]);

  useEffect(() => {
    if (!fwLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - fwStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        FW_LOADING_STAGES.length - 1,
      );
      setFwStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [fwLoading]);

  useEffect(() => {
    if (!ciLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - ciStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        CI_LOADING_STAGES.length - 1,
      );
      setCiStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [ciLoading]);

  useEffect(() => {
    if (!piLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - piStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        PI_LOADING_STAGES.length - 1,
      );
      setPiStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [piLoading]);

  useEffect(() => {
    if (!insightsLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - insightsStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        INSIGHTS_LOADING_STAGES.length - 1,
      );
      setInsightsStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [insightsLoading]);

  useEffect(() => {
    if (!validationLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - validationStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        VALIDATION_LOADING_STAGES.length - 1,
      );
      setValidationStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [validationLoading]);

  useEffect(() => {
    if (!codeIntelLoading) return;
    const interval = setInterval(() => {
      const elapsed = Date.now() - codeIntelStartRef.current;
      const idx = Math.min(
        Math.floor(elapsed / 2500),
        CODE_INTEL_LOADING_STAGES.length - 1,
      );
      setCodeIntelStage(idx);
    }, 400);
    return () => clearInterval(interval);
  }, [codeIntelLoading]);

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

          {/* Card 6: Entry Point Detection */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={FileSearch} title="Entry Point Detection" />
              <div className="p-6">
                {epLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">
                      {EP_LOADING_STAGES[epStage]}
                    </p>
                    <div className="mt-3 flex gap-1">
                      {EP_LOADING_STAGES.map((_, i) => (
                        <div
                          key={i}
                          className={`h-1 w-12 rounded-full transition-colors duration-500 ${
                            i <= epStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                ) : !entryPoints || entryPoints.total_entry_points === 0 ? (
                  <div className="py-6 text-center">
                    <FileSearch className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">
                      No standard application entry point could be identified.
                    </p>
                    <p className="mt-1 text-xs text-[#9CA3AF]">
                      The project structure does not match known entry point patterns.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Primary Entry Point */}
                    {entryPoints.primary_entry_point && (
                      <div className="rounded-lg border border-[#2563EB] bg-[#EFF6FF] p-5">
                        <div className="mb-3 flex items-center gap-2">
                          <span className="inline-flex items-center rounded-full bg-[#2563EB] px-2.5 py-0.5 text-xs font-semibold text-white">
                            PRIMARY
                          </span>
                          <span className="text-xs font-medium text-[#6B7280]">Entry Point</span>
                        </div>
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                          <div>
                            <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Entry File</p>
                            <p className="mt-0.5 text-sm font-semibold text-[#111827]">
                              {entryPoints.primary_entry_point.entry_file}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Framework</p>
                            <p className="mt-0.5 text-sm font-medium text-[#111827]">
                              {entryPoints.primary_entry_point.framework}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Project Type</p>
                            <p className="mt-0.5 text-sm font-medium text-[#111827]">
                              {entryPoints.primary_entry_point.project_type}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Confidence</p>
                            <p className="mt-0.5 text-sm font-semibold text-[#059669]">
                              {entryPoints.primary_entry_point.confidence}%
                            </p>
                          </div>
                        </div>
                        <div className="mt-3 rounded-md bg-white px-3 py-2">
                          <p className="text-xs font-medium text-[#6B7280]">Detection Reason</p>
                          <p className="mt-0.5 text-sm text-[#4B5563]">
                            {entryPoints.primary_entry_point.reason}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Alternative Entry Points */}
                    {entryPoints.alternative_entry_points.length > 0 && (
                      <div>
                        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#6B7280]">
                          Alternative Entry Points ({entryPoints.alternative_entry_points.length})
                        </p>
                        <div className="space-y-2">
                          {entryPoints.alternative_entry_points.map((ep, i) => (
                            <div
                              key={i}
                              className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-3"
                            >
                              <div className="flex items-center gap-3">
                                <FileCode className="h-4 w-4 text-[#2563EB] shrink-0" />
                                <div>
                                  <p className="text-sm font-medium text-[#111827]">{ep.entry_file}</p>
                                  <p className="text-xs text-[#6B7280]">{ep.framework} &middot; {ep.project_type}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-4">
                                <span className="text-xs text-[#6B7280]">{ep.confidence}%</span>
                                <span className="hidden max-w-[200px] truncate text-xs text-[#9CA3AF] sm:block" title={ep.reason}>
                                  {ep.reason}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Card 7: Architecture Detection */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Building2} title="Architecture Detection" />
              <div className="p-6">
                {archLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">
                      {ARCH_LOADING_STAGES[archStage]}
                    </p>
                    <div className="mt-3 flex gap-1">
                      {ARCH_LOADING_STAGES.map((_, i) => (
                        <div
                          key={i}
                          className={`h-1 w-12 rounded-full transition-colors duration-500 ${
                            i <= archStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                ) : !architecture || !architecture.primary_architecture ? (
                  <div className="py-6 text-center">
                    <Building2 className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">
                      No architectural pattern could be identified.
                    </p>
                    <p className="mt-1 text-xs text-[#9CA3AF]">
                      The project structure does not match known architectural patterns.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Primary Architecture */}
                    <div className="rounded-lg border border-[#2563EB] bg-[#EFF6FF] p-5">
                      <div className="mb-3 flex items-center gap-2">
                        <span className="inline-flex items-center rounded-full bg-[#2563EB] px-2.5 py-0.5 text-xs font-semibold text-white">
                          PRIMARY
                        </span>
                        <span className="text-xs font-medium text-[#6B7280]">Architecture</span>
                      </div>
                      <div className="mb-3">
                        <p className="text-sm font-semibold text-[#111827]">
                          {architecture.primary_architecture.architecture}
                        </p>
                      </div>
                      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Confidence</p>
                          <p className="mt-0.5 text-sm font-semibold text-[#059669]">
                            {architecture.primary_architecture.confidence}%
                          </p>
                        </div>
                        <div className="sm:col-span-2 lg:col-span-2">
                          <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Reason</p>
                          <p className="mt-0.5 text-sm text-[#4B5563]">
                            {architecture.primary_architecture.reason}
                          </p>
                        </div>
                      </div>
                      {architecture.primary_architecture.evidence.length > 0 && (
                        <div className="mt-3 rounded-md bg-white px-3 py-2">
                          <p className="mb-1.5 text-xs font-medium text-[#6B7280]">Evidence</p>
                          <ul className="space-y-0.5">
                            {architecture.primary_architecture.evidence.map((e, i) => (
                              <li key={i} className="flex items-center gap-2 text-xs text-[#4B5563]">
                                <span className="h-1 w-1 shrink-0 rounded-full bg-[#2563EB]" />
                                {e}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Alternative Architectures */}
                    {architecture.alternative_architectures.length > 0 && (
                      <div>
                        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#6B7280]">
                          Alternative Architectures ({architecture.alternative_architectures.length})
                        </p>
                        <div className="space-y-2">
                          {architecture.alternative_architectures.map((arch, i) => (
                            <div
                              key={i}
                              className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-3"
                            >
                              <div className="flex items-center gap-3">
                                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#DBEAFE]">
                                  <Building2 className="h-4 w-4 text-[#2563EB]" />
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-[#111827]">{arch.architecture}</p>
                                  <p className="text-xs text-[#6B7280]">{arch.reason}</p>
                                </div>
                              </div>
                              <span className="text-xs text-[#6B7280]">{arch.confidence}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Detected Layers */}
                    {architecture.detected_layers.length > 0 && (
                      <div>
                        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#6B7280]">
                          Detected Layers ({architecture.detected_layers.length})
                        </p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {architecture.detected_layers.map((layer, i) => (
                            <div
                              key={i}
                              className="rounded-lg border border-[#E5E7EB] px-4 py-3"
                            >
                              <p className="text-sm font-semibold text-[#111827]">{layer.name}</p>
                              <div className="mt-1 flex flex-wrap gap-1">
                                {layer.directories.map((d, j) => (
                                  <span
                                    key={j}
                                    className="inline-flex items-center rounded-md bg-[#F3F4F6] px-2 py-0.5 text-xs font-medium text-[#4B5563]"
                                  >
                                    {d}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Card 9: Framework Intelligence */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Monitor} title="Framework Intelligence" />
              <div className="p-6">
                {fwLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">
                      {FW_LOADING_STAGES[fwStage]}
                    </p>
                    <div className="mt-3 flex gap-1">
                      {FW_LOADING_STAGES.map((_, i) => (
                        <div
                          key={i}
                          className={`h-1 w-16 rounded-full transition-colors duration-500 ${
                            i <= fwStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                  ) : !frameworks || (
                  frameworks.technology_stack.languages.length === 0 &&
                  Object.keys(frameworks.technology_stack.categorized || {}).length === 0 &&
                  frameworks.technology_stack.runtimes.length === 0 &&
                  frameworks.technology_stack.package_managers.length === 0 &&
                  frameworks.technology_stack.build_tools.length === 0 &&
                  frameworks.technology_stack.databases.length === 0 &&
                  frameworks.technology_stack.containers.length === 0
                ) ? (
                  <div className="py-6 text-center">
                    <Monitor className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">
                      No recognizable framework detected.
                    </p>
                    <p className="mt-1 text-xs text-[#9CA3AF]">
                      The project structure does not match known technology stack patterns.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-5">
                    {/* Primary Info */}
                    <div className="flex flex-wrap items-center gap-4">
                      {frameworks.primary_language && (
                        <div className="flex items-center gap-2 rounded-lg border border-[#2563EB] bg-[#EFF6FF] px-4 py-2">
                          <span className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Language</span>
                          <span className="text-sm font-semibold text-[#111827]">
                            {frameworks.primary_language.name}
                          </span>
                          <span className="text-xs text-[#2563EB]">{frameworks.primary_language.confidence}%</span>
                        </div>
                      )}
                      {frameworks.primary_framework && (
                        <div className="flex items-center gap-2 rounded-lg border border-[#2563EB] bg-[#EFF6FF] px-4 py-2">
                          <span className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Framework</span>
                          <span className="text-sm font-semibold text-[#111827]">
                            {frameworks.primary_framework.name}
                          </span>
                          <span className="text-xs text-[#2563EB]">{frameworks.primary_framework.confidence}%</span>
                        </div>
                      )}
                    </div>

                    {/* Section: Languages */}
                    {frameworks.technology_stack.languages.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Languages</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {frameworks.technology_stack.languages.map((t, i) => (
                            <TechRow key={i} tech={t} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Categorized Technologies */}
                    {(() => {
                      const cat = frameworks.technology_stack.categorized || {};
                      const categoryOrder = [
                        "Application Framework",
                        "ORM",
                        "Database",
                        "Deep Learning",
                        "Machine Learning",
                        "Data Science",
                        "Visualization",
                        "API",
                        "Testing",
                        "Authentication",
                        "Task Queue",
                        "Package Manager",
                      ];
                      const categoryColors: Record<string, string> = {
                        "Application Framework": "border-l-[#2563EB]",
                        "ORM": "border-l-[#7C3AED]",
                        "Database": "border-l-[#059669]",
                        "Deep Learning": "border-l-[#DC2626]",
                        "Machine Learning": "border-l-[#EA580C]",
                        "Data Science": "border-l-[#CA8A04]",
                        "Visualization": "border-l-[#0891B2]",
                        "API": "border-l-[#4F46E5]",
                        "Testing": "border-l-[#65A30D]",
                        "Authentication": "border-l-[#DB2777]",
                        "Task Queue": "border-l-[#0D9488]",
                        "Package Manager": "border-l-[#6B7280]",
                      };
                      return categoryOrder.map((category) => {
                        const techs = cat[category];
                        if (!techs || techs.length === 0) return null;
                        return (
                          <div key={category}>
                            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">
                              {category}
                            </p>
                            <div className="grid gap-2 sm:grid-cols-2">
                              {techs.map((t, i) => (
                                <CategorizedTechRow key={i} tech={t} colorClass={categoryColors[category] || "border-l-[#6B7280]"} />
                              ))}
                            </div>
                          </div>
                        );
                      });
                    })()}

                    {/* Section: Runtimes */}
                    {frameworks.technology_stack.runtimes.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Runtimes</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {frameworks.technology_stack.runtimes.map((t, i) => (
                            <TechRow key={i} tech={t} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Section: Package Managers */}
                    {frameworks.technology_stack.package_managers.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Package Managers</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {frameworks.technology_stack.package_managers.map((t, i) => (
                            <TechRow key={i} tech={t} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Section: Build Tools */}
                    {frameworks.technology_stack.build_tools.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Build Tools</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {frameworks.technology_stack.build_tools.map((t, i) => (
                            <TechRow key={i} tech={t} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Section: Databases */}
                    {frameworks.technology_stack.databases.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Databases</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {frameworks.technology_stack.databases.map((t, i) => (
                            <TechRow key={i} tech={t} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Section: Containers */}
                    {frameworks.technology_stack.containers.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Containers</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {frameworks.technology_stack.containers.map((t, i) => (
                            <TechRow key={i} tech={t} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Section: Framework Health */}
                    {frameworks.frameworks.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Framework Health</p>
                        <div className="grid gap-3 sm:grid-cols-2">
                          {frameworks.frameworks.map((fw, i) => {
                            const health = fw.health;
                            if (!health) return null;
                            const healthColor =
                              health.label === "Excellent" ? "text-[#059669] border-[#059669]" :
                              health.label === "Good" ? "text-[#2563EB] border-[#2563EB]" :
                              health.label === "Fair" ? "text-[#D97706] border-[#D97706]" :
                              "text-[#DC2626] border-[#DC2626]";
                            const healthBg =
                              health.label === "Excellent" ? "bg-[#D1FAE5]" :
                              health.label === "Good" ? "bg-[#DBEAFE]" :
                              health.label === "Fair" ? "bg-[#FEF3C7]" :
                              "bg-[#FEE2E2]";
                            const healthText =
                              health.label === "Excellent" ? "text-[#065F46]" :
                              health.label === "Good" ? "text-[#1E40AF]" :
                              health.label === "Fair" ? "text-[#92400E]" :
                              "text-[#991B1B]";
                            return (
                              <div key={i} className={`rounded-lg border-2 px-4 py-3 ${healthColor}`}>
                                <div className="flex items-center justify-between">
                                  <p className="text-sm font-semibold text-[#111827]">{fw.name}</p>
                                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${healthBg} ${healthText}`}>
                                    {health.label}
                                  </span>
                                </div>
                                <div className="mt-2 flex items-center gap-3">
                                  <span className="text-2xl font-bold">{health.score}</span>
                                  <span className="text-xs text-[#6B7280]">/ 100</span>
                                  <div className="h-2 flex-1 rounded-full bg-[#E5E7EB]">
                                    <div
                                      className="h-2 rounded-full transition-all duration-700"
                                      style={{ width: `${health.score}%`, backgroundColor: health.label === "Excellent" ? "#059669" : health.label === "Good" ? "#2563EB" : health.label === "Fair" ? "#D97706" : "#DC2626" }}
                                    />
                                  </div>
                                </div>
                                {fw.version && (
                                  <p className="mt-1 text-xs text-[#6B7280]">v{fw.version}</p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Section: Compatibility */}
                    {frameworks.compatibility.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Compatibility</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {frameworks.compatibility.map((c, i) => (
                            <div
                              key={i}
                              className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${
                                c.status === "compatible"
                                  ? "border-[#D1FAE5] bg-[#F0FDF4]"
                                  : "border-[#FEE2E2] bg-[#FFF5F5]"
                              }`}
                            >
                              {c.status === "compatible" ? (
                                <CheckCircle2 className="h-4 w-4 shrink-0 text-[#059669]" />
                              ) : (
                                <XCircle className="h-4 w-4 shrink-0 text-[#DC2626]" />
                              )}
                              <div>
                                <p className="text-sm font-medium text-[#111827]">
                                  {c.framework} + {c.other_framework}
                                </p>
                                <p className="text-xs text-[#6B7280]">{c.note}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Section: Features */}
                    {frameworks.features.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Features</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {frameworks.features.map((f, i) => (
                            <div
                              key={i}
                              className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-3"
                            >
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2">
                                  <p className="text-sm font-medium text-[#111827]">{f.name}</p>
                                  <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2 py-0.5 text-xs font-medium text-[#1E40AF]">
                                    {f.confidence}%
                                  </span>
                                </div>
                                {f.evidence.length > 0 && (
                                  <p className="mt-0.5 truncate text-xs text-[#9CA3AF]" title={f.evidence.join(", ")}>
                                    {f.evidence.slice(0, 2).join(", ")}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Section: Dependency Graph */}
                    {frameworks.dependency_graph.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Dependency Graph</p>
                        <div className="space-y-2">
                          {frameworks.dependency_graph.map((layer, i) => (
                            <div
                              key={i}
                              className="rounded-lg border border-[#E5E7EB] px-4 py-3"
                            >
                              <div className="flex items-center gap-2">
                                <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2.5 py-0.5 text-xs font-semibold text-[#1E40AF]">
                                  {layer.label}
                                </span>
                              </div>
                              <div className="mt-2 flex flex-wrap gap-1.5">
                                {layer.technologies.map((t, j) => (
                                  <span
                                    key={j}
                                    className="inline-flex items-center rounded-md bg-[#F3F4F6] px-2.5 py-0.5 text-xs font-medium text-[#4B5563]"
                                  >
                                    {t}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Section: Detection Evidence */}
                    {frameworks.evidence.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Detection Evidence</p>
                        <div className="space-y-1.5">
                          {frameworks.evidence.map((e, i) => (
                            <div
                              key={i}
                              className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-2.5"
                            >
                              <div className="flex items-center gap-2">
                                <Search className="h-4 w-4 text-[#2563EB]" />
                                <p className="text-sm font-medium text-[#111827]">{e.name}</p>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="text-xs text-[#6B7280]">{e.source}</span>
                                <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2 py-0.5 text-xs font-medium text-[#1E40AF]">
                                  {e.confidence}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Card 10: Configuration Intelligence */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Settings} title="Configuration Intelligence" />
              <div className="p-6">
                {ciLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">
                      {CI_LOADING_STAGES[ciStage]}
                    </p>
                    <div className="mt-3 flex gap-1">
                      {CI_LOADING_STAGES.map((_, i) => (
                        <div
                          key={i}
                          className={`h-1 w-16 rounded-full transition-colors duration-500 ${
                            i <= ciStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                ) : !configIntel || configIntel.detected_files.length === 0 ? (
                  <div className="py-6 text-center">
                    <Settings className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">
                      No configuration files detected.
                    </p>
                    <p className="mt-1 text-xs text-[#9CA3AF]">
                      The project does not appear to contain configuration files.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-5">
                    {/* Scores */}
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      <div className="rounded-lg border border-[#E5E7EB] p-4">
                        <p className="mb-1 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Config Health</p>
                        <div className="flex items-center gap-2">
                          <span className={`text-2xl font-bold ${
                            configIntel.health.label === "Excellent" ? "text-[#059669]" :
                            configIntel.health.label === "Good" ? "text-[#2563EB]" :
                            configIntel.health.label === "Average" ? "text-[#D97706]" :
                            "text-[#DC2626]"
                          }`}>
                            {configIntel.health.score}
                          </span>
                          <span className="text-xs text-[#6B7280]">/100</span>
                        </div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] p-4">
                        <p className="mb-1 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Readiness</p>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold text-[#2563EB]">{configIntel.scores.readiness}</span>
                          <span className="text-xs text-[#6B7280]">/100</span>
                        </div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] p-4">
                        <p className="mb-1 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Security</p>
                        <div className="flex items-center gap-2">
                          <span className={`text-2xl font-bold ${
                            configIntel.scores.security >= 80 ? "text-[#059669]" :
                            configIntel.scores.security >= 60 ? "text-[#D97706]" :
                            "text-[#DC2626]"
                          }`}>
                            {configIntel.scores.security}
                          </span>
                          <span className="text-xs text-[#6B7280]">/100</span>
                        </div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] p-4">
                        <p className="mb-1 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Maintainability</p>
                        <div className="flex items-center gap-2">
                          <span className={`text-2xl font-bold ${
                            configIntel.scores.maintainability >= 80 ? "text-[#059669]" :
                            configIntel.scores.maintainability >= 60 ? "text-[#D97706]" :
                            "text-[#DC2626]"
                          }`}>
                            {configIntel.scores.maintainability}
                          </span>
                          <span className="text-xs text-[#6B7280]">/100</span>
                        </div>
                      </div>
                    </div>

                    {/* Stats row */}
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <p className="text-2xl font-bold text-[#059669]">{configIntel.detected_files.length}</p>
                        <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Detected Files</p>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <p className="text-2xl font-bold text-[#D97706]">{configIntel.missing_files.length}</p>
                        <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Missing Files</p>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <p className="text-2xl font-bold text-[#2563EB]">{configIntel.warnings.length}</p>
                        <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Warnings</p>
                      </div>
                    </div>

                    {/* Detected Files */}
                    {configIntel.detected_files.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Detected Files</p>
                        <div className="grid gap-1.5">
                          {configIntel.detected_files.map((f, i) => (
                            <div key={i} className="flex items-center gap-3 rounded-lg border border-[#E5E7EB] px-4 py-2.5">
                              <CheckCircle2 className="h-4 w-4 shrink-0 text-[#059669]" />
                              <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-[#111827]">{f.file_name}</p>
                                <p className="text-xs text-[#6B7280]">{f.category}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Files */}
                    {configIntel.missing_files.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Missing Files</p>
                        <div className="grid gap-1.5">
                          {configIntel.missing_files.map((f, i) => (
                            <div key={i} className="flex items-center gap-3 rounded-lg border border-[#FEE2E2] bg-[#FFF5F5] px-4 py-2.5">
                              <XCircle className="h-4 w-4 shrink-0 text-[#DC2626]" />
                              <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-[#111827]">{f.file_name}</p>
                                <p className="text-xs text-[#6B7280]">{f.category}</p>
                              </div>
                              {f.recommendation && (
                                <p className="hidden max-w-[200px] text-xs text-[#6B7280] sm:block" title={f.recommendation}>
                                  {f.recommendation}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Warnings */}
                    {configIntel.warnings.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Warnings</p>
                        <div className="space-y-1.5">
                          {configIntel.warnings.map((w, i) => (
                            <div
                              key={i}
                              className={`flex items-start gap-2.5 rounded-lg border px-4 py-2.5 ${
                                w.severity === "warning"
                                  ? "border-[#FEF3C7] bg-[#FFFBEB]"
                                  : "border-[#DBEAFE] bg-[#EFF6FF]"
                              }`}
                            >
                              <AlertTriangle className={`mt-0.5 h-4 w-4 shrink-0 ${
                                w.severity === "warning" ? "text-[#D97706]" : "text-[#2563EB]"
                              }`} />
                              <div>
                                <p className="text-sm text-[#4B5563]">{w.message}</p>
                                {w.file_name && (
                                  <p className="text-xs text-[#6B7280]">File: {w.file_name}</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {configIntel.recommendations.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Recommendations</p>
                        <div className="space-y-1.5">
                          {configIntel.recommendations.map((r, i) => (
                            <div key={i} className="flex items-start gap-2.5 rounded-lg border border-[#DBEAFE] bg-[#EFF6FF] px-4 py-2.5">
                              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#2563EB]" />
                              <p className="text-sm text-[#4B5563]">{r}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Dependency Validation */}
                    {configIntel.dependency_validation.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Dependency Validation</p>
                        <div className="space-y-1.5">
                          {configIntel.dependency_validation.map((d, i) => (
                            <div
                              key={i}
                              className={`flex items-start gap-2.5 rounded-lg border px-4 py-2.5 ${
                                d.severity === "error"
                                  ? "border-[#FEE2E2] bg-[#FFF5F5]"
                                  : d.severity === "warning"
                                  ? "border-[#FEF3C7] bg-[#FFFBEB]"
                                  : "border-[#DBEAFE] bg-[#EFF6FF]"
                              }`}
                            >
                              {d.severity === "error" ? (
                                <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#DC2626]" />
                              ) : d.severity === "warning" ? (
                                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#D97706]" />
                              ) : (
                                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#2563EB]" />
                              )}
                              <div>
                                <p className="text-sm font-medium text-[#111827]">[{d.type}] {d.package}</p>
                                <p className="text-xs text-[#6B7280]">{d.detail}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Environment Validation */}
                    {configIntel.environment_validation.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Environment Validation</p>
                        <div className="space-y-1.5">
                          {configIntel.environment_validation.map((e, i) => (
                            <div
                              key={i}
                              className={`flex items-start gap-2.5 rounded-lg border px-4 py-2.5 ${
                                e.severity === "error"
                                  ? "border-[#FEE2E2] bg-[#FFF5F5]"
                                  : "border-[#FEF3C7] bg-[#FFFBEB]"
                              }`}
                            >
                              {e.severity === "error" ? (
                                <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#DC2626]" />
                              ) : (
                                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#D97706]" />
                              )}
                              <div>
                                <p className="text-sm font-medium text-[#111827]">{e.type}</p>
                                <p className="text-xs text-[#6B7280]">{e.detail}</p>
                                {e.file && (
                                  <p className="text-xs text-[#9CA3AF]">File: {e.file}</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Docker Support */}
                    <div>
                      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Docker Support</p>
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        <div className={`rounded-lg border px-4 py-3 text-center ${
                          configIntel.docker_validation.has_dockerfile
                            ? "border-[#D1FAE5] bg-[#F0FDF4]"
                            : "border-[#E5E7EB] bg-[#F9FAFB]"
                        }`}>
                          {configIntel.docker_validation.has_dockerfile ? (
                            <CheckCircle2 className="mx-auto h-5 w-5 text-[#059669]" />
                          ) : (
                            <XCircle className="mx-auto h-5 w-5 text-[#9CA3AF]" />
                          )}
                          <p className="mt-1 text-xs font-medium text-[#6B7280]">Dockerfile</p>
                        </div>
                        <div className={`rounded-lg border px-4 py-3 text-center ${
                          configIntel.docker_validation.has_docker_compose
                            ? "border-[#D1FAE5] bg-[#F0FDF4]"
                            : "border-[#E5E7EB] bg-[#F9FAFB]"
                        }`}>
                          {configIntel.docker_validation.has_docker_compose ? (
                            <CheckCircle2 className="mx-auto h-5 w-5 text-[#059669]" />
                          ) : (
                            <XCircle className="mx-auto h-5 w-5 text-[#9CA3AF]" />
                          )}
                          <p className="mt-1 text-xs font-medium text-[#6B7280]">Compose</p>
                        </div>
                        <div className={`rounded-lg border px-4 py-3 text-center ${
                          configIntel.docker_validation.multi_stage_build
                            ? "border-[#D1FAE5] bg-[#F0FDF4]"
                            : "border-[#E5E7EB] bg-[#F9FAFB]"
                        }`}>
                          {configIntel.docker_validation.multi_stage_build ? (
                            <CheckCircle2 className="mx-auto h-5 w-5 text-[#059669]" />
                          ) : (
                            <XCircle className="mx-auto h-5 w-5 text-[#9CA3AF]" />
                          )}
                          <p className="mt-1 text-xs font-medium text-[#6B7280]">Multi-Stage</p>
                        </div>
                        <div className={`rounded-lg border px-4 py-3 text-center ${
                          configIntel.docker_validation.production_ready
                            ? "border-[#D1FAE5] bg-[#F0FDF4]"
                            : "border-[#E5E7EB] bg-[#F9FAFB]"
                        }`}>
                          {configIntel.docker_validation.production_ready ? (
                            <CheckCircle2 className="mx-auto h-5 w-5 text-[#059669]" />
                          ) : (
                            <XCircle className="mx-auto h-5 w-5 text-[#9CA3AF]" />
                          )}
                          <p className="mt-1 text-xs font-medium text-[#6B7280]">Prod Ready</p>
                        </div>
                      </div>
                      {configIntel.docker_validation.detail && (
                        <p className="mt-2 text-xs text-[#6B7280]">{configIntel.docker_validation.detail}</p>
                      )}
                    </div>

                    {/* CI/CD Status */}
                    <div>
                      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">CI/CD Status</p>
                      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                        {configIntel.cicd.map((c, i) => (
                          <div
                            key={i}
                            className={`flex items-center gap-2.5 rounded-lg border px-4 py-2.5 ${
                              c.configured
                                ? "border-[#D1FAE5] bg-[#F0FDF4]"
                                : "border-[#E5E7EB] bg-[#F9FAFB]"
                            }`}
                          >
                            {c.configured ? (
                              <CheckCircle2 className="h-4 w-4 shrink-0 text-[#059669]" />
                            ) : (
                              <XCircle className="h-4 w-4 shrink-0 text-[#9CA3AF]" />
                            )}
                            <div>
                              <p className={`text-sm font-medium ${
                                c.configured ? "text-[#111827]" : "text-[#6B7280]"
                              }`}>{c.platform}</p>
                              {c.file && (
                                <p className="text-xs text-[#9CA3AF]">{c.file}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Security Checks */}
                    {configIntel.security_checks.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Security Checks</p>
                        <div className="space-y-1.5">
                          {configIntel.security_checks.map((s, i) => (
                            <div
                              key={i}
                              className={`flex items-start gap-2.5 rounded-lg border px-4 py-2.5 ${
                                s.severity === "error"
                                  ? "border-[#FEE2E2] bg-[#FFF5F5]"
                                  : s.severity === "warning"
                                  ? "border-[#FEF3C7] bg-[#FFFBEB]"
                                  : "border-[#DBEAFE] bg-[#EFF6FF]"
                              }`}
                            >
                              {s.severity === "error" ? (
                                <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#DC2626]" />
                              ) : s.severity === "warning" ? (
                                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#D97706]" />
                              ) : (
                                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#2563EB]" />
                              )}
                              <div>
                                <p className="text-sm font-medium text-[#111827]">{s.type}</p>
                                <p className="text-xs text-[#6B7280]">{s.detail}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Card: Dependency Health */}
          {configIntel && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Package} title="Dependency Health" />
              <div className="p-6">
                {(() => {
                  const dv = configIntel.dependency_validation || [];
                  const totalPkgs = dv.length;
                  const deprecated = dv.filter(d => d.type === "Deprecated package").length;
                  const duplicates = dv.filter(d => d.type === "Duplicate dependency").length;
                  const versionIssues = dv.filter(d => d.type === "Invalid version syntax").length;
                  const issues = deprecated + duplicates + versionIssues;
                  const score = totalPkgs === 0 ? 100 : Math.max(0, 100 - Math.round((issues / Math.max(totalPkgs, 1)) * 100));
                  const label = score >= 90 ? "Healthy" : score >= 70 ? "Warning" : "Critical";
                  const labelColor = score >= 90 ? "bg-[#D1FAE5] text-[#065F46]" : score >= 70 ? "bg-[#FEF3C7] text-[#92400E]" : "bg-[#FEE2E2] text-[#991B1B]";
                  const barColor = score >= 90 ? "bg-[#059669]" : score >= 70 ? "bg-[#D97706]" : "bg-[#DC2626]";
                  return (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl font-bold text-[#111827]">{score}</span>
                          <span className="text-xs text-[#6B7280]">/ 100</span>
                        </div>
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${labelColor}`}>{label}</span>
                      </div>
                      <div className="h-2 rounded-full bg-[#E5E7EB]">
                        <div className={`h-2 rounded-full transition-all duration-700 ${barColor}`} style={{ width: `${score}%` }} />
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                          <p className="text-lg font-bold text-[#111827]">{totalPkgs}</p>
                          <p className="text-xs text-[#6B7280]">Total Packages</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                          <p className="text-lg font-bold text-[#059669]">{totalPkgs - issues}</p>
                          <p className="text-xs text-[#6B7280]">Healthy</p>
                        </div>
                        <div className="rounded-lg border border-[#FEF3C7] bg-[#FFFBEB] p-3 text-center">
                          <p className="text-lg font-bold text-[#D97706]">{deprecated + duplicates + versionIssues}</p>
                          <p className="text-xs text-[#6B7280]">Issues</p>
                        </div>
                        <div className="rounded-lg border border-[#FEE2E2] bg-[#FFF5F5] p-3 text-center">
                          <p className="text-lg font-bold text-[#DC2626]">{deprecated}</p>
                          <p className="text-xs text-[#6B7280]">Deprecated</p>
                        </div>
                      </div>
                      {duplicates > 0 && <p className="text-xs text-[#D97706]">Duplicate packages: {duplicates}</p>}
                      {versionIssues > 0 && <p className="text-xs text-[#D97706]">Version conflicts: {versionIssues}</p>}
                    </div>
                  );
                })()}
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card: Environment Validation */}
          {configIntel && configIntel.environment_validation.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Shield} title="Environment Validation" />
              <div className="p-6">
                <div className="grid gap-3 sm:grid-cols-2">
                  {(() => {
                    const env = configIntel.environment_validation;
                    const hasEnvExample = !env.some(e => e.type === "Missing .env.example");
                    const hasHardcoded = env.some(e => e.type === "Hardcoded secret" || e.type === "Hardcoded database credential");
                    const safeCount = env.filter(e => e.severity !== "error" && e.severity !== "warning").length;
                    const warnCount = env.filter(e => e.severity === "warning").length;
                    const critCount = env.filter(e => e.severity === "error").length;
                    return (
                      <>
                        <div className="flex items-center gap-3 rounded-lg border border-[#D1FAE5] bg-[#F0FDF4] px-4 py-3">
                          <CheckCircle2 className="h-5 w-5 text-[#059669]" />
                          <div>
                            <p className="text-sm font-medium text-[#111827]">Environment File</p>
                            <p className="text-xs text-[#6B7280]">{hasEnvExample ? ".env.example present" : "No .env.example"}</p>
                          </div>
                        </div>
                        <div className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${hasHardcoded ? "border-[#FEE2E2] bg-[#FFF5F5]" : "border-[#D1FAE5] bg-[#F0FDF4]"}`}>
                          {hasHardcoded ? <XCircle className="h-5 w-5 text-[#DC2626]" /> : <CheckCircle2 className="h-5 w-5 text-[#059669]" />}
                          <div>
                            <p className="text-sm font-medium text-[#111827]">Hardcoded Secrets</p>
                            <p className="text-xs text-[#6B7280]">{hasHardcoded ? "Secrets detected" : "No secrets found"}</p>
                          </div>
                        </div>
                        <div className="col-span-full grid grid-cols-3 gap-2">
                          <div className="rounded-lg border border-[#D1FAE5] bg-[#F0FDF4] p-3 text-center">
                            <CheckCircle2 className="mx-auto h-4 w-4 text-[#059669]" />
                            <p className="mt-1 text-lg font-bold text-[#059669]">{safeCount}</p>
                            <p className="text-xs text-[#6B7280]">Safe</p>
                          </div>
                          <div className="rounded-lg border border-[#FEF3C7] bg-[#FFFBEB] p-3 text-center">
                            <AlertTriangle className="mx-auto h-4 w-4 text-[#D97706]" />
                            <p className="mt-1 text-lg font-bold text-[#D97706]">{warnCount}</p>
                            <p className="text-xs text-[#6B7280]">Warning</p>
                          </div>
                          <div className="rounded-lg border border-[#FEE2E2] bg-[#FFF5F5] p-3 text-center">
                            <XCircle className="mx-auto h-4 w-4 text-[#DC2626]" />
                            <p className="mt-1 text-lg font-bold text-[#DC2626]">{critCount}</p>
                            <p className="text-xs text-[#6B7280]">Critical</p>
                          </div>
                        </div>
                        {env.map((e, i) => (
                          <div key={i} className={`col-span-full flex items-start gap-2.5 rounded-lg border px-4 py-2.5 ${e.severity === "error" ? "border-[#FEE2E2] bg-[#FFF5F5]" : "border-[#FEF3C7] bg-[#FFFBEB]"}`}>
                            {e.severity === "error" ? <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#DC2626]" /> : <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#D97706]" />}
                            <div>
                              <p className="text-sm font-medium text-[#111827]">{e.type}</p>
                              <p className="text-xs text-[#6B7280]">{e.detail}</p>
                              {e.file && <p className="text-xs text-[#9CA3AF]">File: {e.file}</p>}
                            </div>
                          </div>
                        ))}
                      </>
                    );
                  })()}
                </div>
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card: Docker Support */}
          {configIntel && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Box} title="Docker Support" />
              <div className="p-6">
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                  <div className={`rounded-lg border px-4 py-3 text-center ${configIntel.docker_validation.has_dockerfile ? "border-[#D1FAE5] bg-[#F0FDF4]" : "border-[#E5E7EB] bg-[#F9FAFB]"}`}>
                    {configIntel.docker_validation.has_dockerfile ? <CheckCircle2 className="mx-auto h-5 w-5 text-[#059669]" /> : <XCircle className="mx-auto h-5 w-5 text-[#9CA3AF]" />}
                    <p className={`mt-1 text-xs font-medium ${configIntel.docker_validation.has_dockerfile ? "text-[#111827]" : "text-[#6B7280]"}`}>Dockerfile</p>
                  </div>
                  <div className={`rounded-lg border px-4 py-3 text-center ${configIntel.docker_validation.has_docker_compose ? "border-[#D1FAE5] bg-[#F0FDF4]" : "border-[#E5E7EB] bg-[#F9FAFB]"}`}>
                    {configIntel.docker_validation.has_docker_compose ? <CheckCircle2 className="mx-auto h-5 w-5 text-[#059669]" /> : <XCircle className="mx-auto h-5 w-5 text-[#9CA3AF]" />}
                    <p className={`mt-1 text-xs font-medium ${configIntel.docker_validation.has_docker_compose ? "text-[#111827]" : "text-[#6B7280]"}`}>Compose</p>
                  </div>
                  <div className={`rounded-lg border px-4 py-3 text-center ${configIntel.docker_validation.multi_stage_build ? "border-[#D1FAE5] bg-[#F0FDF4]" : "border-[#E5E7EB] bg-[#F9FAFB]"}`}>
                    {configIntel.docker_validation.multi_stage_build ? <CheckCircle2 className="mx-auto h-5 w-5 text-[#059669]" /> : <XCircle className="mx-auto h-5 w-5 text-[#9CA3AF]" />}
                    <p className={`mt-1 text-xs font-medium ${configIntel.docker_validation.multi_stage_build ? "text-[#111827]" : "text-[#6B7280]"}`}>Multi-Stage</p>
                  </div>
                  <div className={`rounded-lg border px-4 py-3 text-center ${configIntel.docker_validation.production_ready ? "border-[#D1FAE5] bg-[#F0FDF4]" : "border-[#E5E7EB] bg-[#F9FAFB]"}`}>
                    {configIntel.docker_validation.production_ready ? <CheckCircle2 className="mx-auto h-5 w-5 text-[#059669]" /> : <XCircle className="mx-auto h-5 w-5 text-[#9CA3AF]" />}
                    <p className={`mt-1 text-xs font-medium ${configIntel.docker_validation.production_ready ? "text-[#111827]" : "text-[#6B7280]"}`}>Prod Ready</p>
                  </div>
                  <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] px-4 py-3 text-center">
                    <Info className="mx-auto h-5 w-5 text-[#2563EB]" />
                    <p className="mt-1 text-xs font-medium text-[#6B7280]">
                      {configIntel.docker_validation.has_dockerfile ? "Optimize size" : "Not available"}
                    </p>
                  </div>
                </div>
                {configIntel.docker_validation.detail && (
                  <p className="mt-3 text-xs text-[#6B7280]">{configIntel.docker_validation.detail}</p>
                )}
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card: CI/CD Status */}
          {configIntel && configIntel.cicd.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={GitBranch} title="CI/CD Status" />
              <div className="p-6">
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {configIntel.cicd.map((c, i) => (
                    <div key={i} className={`flex items-center gap-2.5 rounded-lg border px-4 py-3 ${c.configured ? "border-[#D1FAE5] bg-[#F0FDF4]" : "border-[#E5E7EB] bg-[#F9FAFB]"}`}>
                      {c.configured ? <CheckCircle2 className="h-4 w-4 shrink-0 text-[#059669]" /> : <XCircle className="h-4 w-4 shrink-0 text-[#9CA3AF]" />}
                      <div>
                        <p className={`text-sm font-medium ${c.configured ? "text-[#111827]" : "text-[#6B7280]"}`}>{c.platform}</p>
                        <p className="text-xs text-[#9CA3AF]">{c.configured ? "Configured" : "Not Configured"}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card: Configuration Score */}
          {configIntel && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={BarChart3} title="Configuration Score" />
              <div className="p-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  {[
                    { label: "Configuration Health", value: configIntel.scores.configuration_health, color: "#059669" },
                    { label: "Project Readiness", value: configIntel.scores.readiness, color: "#2563EB" },
                    { label: "Security", value: configIntel.scores.security, color: "#D97706" },
                    { label: "Maintainability", value: configIntel.scores.maintainability, color: "#7C3AED" },
                  ].map((item) => (
                    <div key={item.label} className="rounded-lg border border-[#E5E7EB] p-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">{item.label}</p>
                        <span className="text-lg font-bold" style={{ color: item.color }}>{item.value}%</span>
                      </div>
                      <div className="h-2.5 rounded-full bg-[#E5E7EB]">
                        <div className="h-2.5 rounded-full transition-all duration-700" style={{ width: `${item.value}%`, backgroundColor: item.color }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card: AI Recommendations */}
          {configIntel && configIntel.recommendations.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Lightbulb} title="AI Recommendations" />
              <div className="p-6">
                <div className="space-y-1.5">
                  {configIntel.recommendations.map((r, i) => (
                    <div key={i} className="flex items-start gap-2.5 rounded-lg border border-[#DBEAFE] bg-[#EFF6FF] px-4 py-2.5">
                      <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-[#2563EB]" />
                      <p className="text-sm text-[#4B5563]">{r}</p>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card: Configuration Insights */}
          {configIntel && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Info} title="Configuration Insights" />
              <div className="p-6">
                <div className="space-y-2">
                  {(() => {
                    const insights: { icon: typeof CheckCircle2; label: string; color: string }[] = [];
                    const df = configIntel.detected_files.map(f => f.file_name.toLowerCase());
                    if (df.some(f => f.includes("requirements") || f.includes("pyproject"))) insights.push({ icon: CheckCircle2, label: "Python dependencies configured", color: "text-[#059669]" });
                    if (df.some(f => f.includes("package.json"))) insights.push({ icon: CheckCircle2, label: "Node.js dependencies configured", color: "text-[#059669]" });
                    if (df.some(f => f.includes("dockerfile"))) insights.push({ icon: CheckCircle2, label: "Docker support enabled", color: "text-[#059669]" });
                    if (df.some(f => f.includes(".env.example") || f.includes(".env"))) insights.push({ icon: CheckCircle2, label: "Environment configured", color: "text-[#059669]" });
                    if (df.some(f => f.includes(".gitignore"))) insights.push({ icon: CheckCircle2, label: "Git ignore configured", color: "text-[#059669]" });
                    if (df.some(f => f.includes("readme"))) insights.push({ icon: CheckCircle2, label: "Documentation (README) present", color: "text-[#059669]" });
                    if (df.some(f => f.includes("license"))) insights.push({ icon: CheckCircle2, label: "License file present", color: "text-[#059669]" });
                    if (df.some(f => f.includes("jest") || f.includes("pytest") || f.includes("tox"))) insights.push({ icon: CheckCircle2, label: "Test configuration present", color: "text-[#059669]" });
                    if (df.some(f => f.includes("prettier") || f.includes("eslint") || f.includes("editorconfig") || f.includes("flake8") || f.includes("ruff"))) insights.push({ icon: CheckCircle2, label: "Code formatter configured", color: "text-[#059669]" });
                    if (df.some(f => f.includes(".github") || f.includes("gitlab") || f.includes("jenkinsfile") || f.includes("azure-pipelines"))) insights.push({ icon: CheckCircle2, label: "CI/CD pipeline configured", color: "text-[#059669]" });
                    if (configIntel.dependency_validation.length === 0) insights.push({ icon: CheckCircle2, label: "No dependency conflicts detected", color: "text-[#059669]" });
                    if (configIntel.environment_validation.length === 0) insights.push({ icon: CheckCircle2, label: "Environment configuration valid", color: "text-[#059669]" });
                    if (insights.length === 0) insights.push({ icon: Info, label: "Basic project structure detected", color: "text-[#2563EB]" });
                    return insights.map((insight, i) => (
                      <div key={i} className="flex items-center gap-2.5 rounded-lg border border-[#E5E7EB] px-4 py-2.5">
                        <insight.icon className={`h-4 w-4 shrink-0 ${insight.color}`} />
                        <p className="text-sm text-[#4B5563]">{insight.label}</p>
                      </div>
                    ));
                  })()}
                </div>
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card: Dependency Graph */}
          {frameworks && frameworks.dependency_graph && frameworks.dependency_graph.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Layers} title="Dependency Graph" />
              <div className="p-6">
                <div className="space-y-1">
                  {frameworks.dependency_graph.map((layer, i) => (
                    <div key={i}>
                      <div className="flex items-center gap-3 rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] px-4 py-2.5">
                        <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2.5 py-0.5 text-xs font-semibold text-[#1E40AF]">{layer.label}</span>
                        <div className="flex flex-wrap gap-1">
                          {layer.technologies.map((t, j) => (
                            <span key={j} className="inline-flex items-center rounded-md bg-[#F3F4F6] px-2 py-0.5 text-xs font-medium text-[#4B5563]">{t}</span>
                          ))}
                        </div>
                      </div>
                      {i < frameworks.dependency_graph.length - 1 && (
                        <div className="flex justify-center py-1">
                          <ChevronDown className="h-4 w-4 text-[#9CA3AF]" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card: Configuration Summary */}
          {configIntel && (
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={FileText} title="Configuration Summary" />
              <div className="p-6">
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {(() => {
                    const df = configIntel.detected_files;
                    const mf = configIntel.missing_files;
                    const required = df.filter(f => f.category === "Required").length + mf.filter(f => f.category === "Required").length;
                    const optional = df.filter(f => f.category === "Optional").length + mf.filter(f => f.category === "Optional").length;
                    const securityFiles = df.filter(f => f.file_name.toLowerCase().includes("env") || f.file_name.toLowerCase().includes("docker") || f.file_name.toLowerCase().includes("gitignore")).length;
                    const devFiles = df.filter(f => f.file_name.toLowerCase().includes("jest") || f.file_name.toLowerCase().includes("pytest") || f.file_name.toLowerCase().includes("tox") || f.file_name.toLowerCase().includes("prettier") || f.file_name.toLowerCase().includes("eslint")).length;
                    return (
                      <>
                        <div className="rounded-lg border border-[#059669] bg-[#F0FDF4] p-4 text-center">
                          <p className="text-2xl font-bold text-[#059669]">{df.length}</p>
                          <p className="text-xs font-medium text-[#065F46]">Files Detected</p>
                        </div>
                        <div className="rounded-lg border border-[#DC2626] bg-[#FFF5F5] p-4 text-center">
                          <p className="text-2xl font-bold text-[#DC2626]">{mf.length}</p>
                          <p className="text-xs font-medium text-[#991B1B]">Files Missing</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#6B7280]">{required}</p>
                          <p className="text-xs font-medium text-[#6B7280]">Required Files</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#6B7280]">{optional}</p>
                          <p className="text-xs font-medium text-[#6B7280]">Optional Files</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#2563EB]">{securityFiles}</p>
                          <p className="text-xs font-medium text-[#6B7280]">Security Files</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#7C3AED]">{devFiles}</p>
                          <p className="text-xs font-medium text-[#6B7280]">Development Files</p>
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            </Card>
          </motion.div>
          )}

          {/* Sticky Final Summary Card */}
          {configIntel && (
          <motion.div variants={itemVariants} className="sticky bottom-4 z-10">
            <Card className="overflow-hidden border-2 border-[#2563EB] shadow-lg">
              <div className="bg-[#2563EB] px-6 py-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-white" />
                  <h2 className="text-base font-semibold text-white">Overall Configuration</h2>
                </div>
              </div>
              <div className="p-6">
                <div className="grid gap-4 sm:grid-cols-5">
                  <div className="text-center">
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Config Health</p>
                    <p className={`text-lg font-bold ${configIntel.scores.configuration_health >= 80 ? "text-[#059669]" : configIntel.scores.configuration_health >= 60 ? "text-[#D97706]" : "text-[#DC2626]"}`}>{configIntel.scores.configuration_health}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Security</p>
                    <p className={`text-lg font-bold ${configIntel.scores.security >= 80 ? "text-[#059669]" : configIntel.scores.security >= 60 ? "text-[#D97706]" : "text-[#DC2626]"}`}>{configIntel.scores.security}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Readiness</p>
                    <p className={`text-lg font-bold ${configIntel.scores.readiness >= 80 ? "text-[#059669]" : configIntel.scores.readiness >= 60 ? "text-[#D97706]" : "text-[#DC2626]"}`}>{configIntel.scores.readiness}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Maintainability</p>
                    <p className={`text-lg font-bold ${configIntel.scores.maintainability >= 80 ? "text-[#059669]" : configIntel.scores.maintainability >= 60 ? "text-[#D97706]" : "text-[#DC2626]"}`}>{configIntel.scores.maintainability}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-medium uppercase tracking-wider text-[#6B7280]">Status</p>
                    {(() => {
                      const avg = (configIntel.scores.configuration_health + configIntel.scores.security + configIntel.scores.readiness + configIntel.scores.maintainability) / 4;
                      const label = avg >= 80 ? "Ready for AI Analysis" : avg >= 60 ? "Needs Configuration" : "Needs Configuration";
                      const labelColor = avg >= 80 ? "bg-[#D1FAE5] text-[#065F46]" : avg >= 60 ? "bg-[#FEF3C7] text-[#92400E]" : "bg-[#FEE2E2] text-[#991B1B]";
                      return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${labelColor}`}>{label}</span>;
                    })()}
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
          )}

          {/* Card 8: Module Detection */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Grid3X3} title="Module Detection" />
              <div className="p-6">
                {modLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">
                      {MOD_LOADING_STAGES[modStage]}
                    </p>
                    <div className="mt-3 flex gap-1">
                      {MOD_LOADING_STAGES.map((_, i) => (
                        <div
                          key={i}
                          className={`h-1 w-16 rounded-full transition-colors duration-500 ${
                            i <= modStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                ) : !modules || modules.summary.detected_count === 0 ? (
                  <div className="py-6 text-center">
                    <Grid3X3 className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">
                      No standard modules detected.
                    </p>
                    <p className="mt-1 text-xs text-[#9CA3AF]">
                      The project structure does not match known module patterns.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Module Summary cards */}
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <p className="text-2xl font-bold text-[#2563EB]">{modules.summary.detected_count}</p>
                        <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Detected</p>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <p className="text-2xl font-bold text-[#9CA3AF]">{modules.summary.missing_count}</p>
                        <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Missing</p>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <p className="text-2xl font-bold text-[#059669]">{modules.summary.core_detected}/{modules.summary.core_total}</p>
                        <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Core Modules</p>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <p className="text-2xl font-bold text-[#7C3AED]">{modules.summary.optional_detected}/{modules.summary.optional_total}</p>
                        <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Optional Modules</p>
                      </div>
                    </div>

                    {/* Module List */}
                    <div className="grid gap-2">
                      {modules.modules.map((mod, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-3 transition-colors hover:bg-[#F9FAFB]"
                        >
                          <div className="flex min-w-0 items-center gap-3">
                            <div className={`flex h-7 w-7 items-center justify-center rounded-md shrink-0 ${
                              mod.status === "Detected" ? "bg-[#D1FAE5]" : "bg-[#F3F4F6]"
                            }`}>
                              {mod.status === "Detected" ? (
                                <CheckCircle2 className="h-4 w-4 text-[#059669]" />
                              ) : (
                                <XCircle className="h-4 w-4 text-[#9CA3AF]" />
                              )}
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-medium text-[#111827]">{mod.module_name}</p>
                                {mod.status === "Detected" && (
                                  <span className="inline-flex items-center rounded-full bg-[#D1FAE5] px-2 py-0.5 text-xs font-medium text-[#065F46]">
                                    {mod.confidence}%
                                  </span>
                                )}
                              </div>
                              {mod.status === "Detected" && mod.detected_folder && (
                                <p className="truncate text-xs text-[#6B7280]">
                                  Folder: {mod.detected_folder}
                                </p>
                              )}
                            </div>
                          </div>
                          <p className="ml-2 max-w-[240px] shrink-0 truncate text-xs text-[#9CA3AF]" title={mod.reason}>
                            {mod.reason}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Card 9: Project Intelligence */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={BarChart3} title="Project Intelligence" />
              <div className="p-6">
                {piLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">
                      {PI_LOADING_STAGES[piStage]}
                    </p>
                    <div className="mt-3 flex gap-1">
                      {PI_LOADING_STAGES.map((_, i) => (
                        <div key={i} className={`h-1 w-16 rounded-full transition-colors duration-500 ${i <= piStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"}`} />
                      ))}
                    </div>
                  </div>
                ) : !projectIntel ? (
                  <div className="py-6 text-center">
                    <BarChart3 className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">Project intelligence unavailable.</p>
                  </div>
                ) : (
                  <div className="space-y-6">

                    {/* Row 1: Code Metrics */}
                    <div>
                      <h4 className="mb-3 text-sm font-semibold text-[#111827]">Code Metrics</h4>
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#2563EB]">{projectIntel.code_metrics.total_lines.toLocaleString()}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Total Lines of Code</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#2563EB]">{projectIntel.code_metrics.code_files}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Code Files</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#6B7280]">{projectIntel.code_metrics.blank_lines.toLocaleString()}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Blank Lines</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#059669]">{projectIntel.code_metrics.comment_lines.toLocaleString()}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Comment Lines</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#7C3AED]">{projectIntel.code_metrics.comment_ratio}%</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Comment Ratio</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#2563EB]">{formatSize(projectIntel.code_metrics.avg_file_size)}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Avg File Size</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#D97706]">{formatSize(projectIntel.code_metrics.largest_file_size)}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Largest File</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#6B7280]">{formatSize(projectIntel.code_metrics.smallest_file_size)}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Smallest File</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#2563EB]">{projectIntel.code_metrics.avg_function_length}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Avg Function Length</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#2563EB]">{projectIntel.code_metrics.avg_class_size}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Avg Class Size</p>
                        </div>
                      </div>
                    </div>

                    {/* Row 2: Complexity */}
                    <div>
                      <h4 className="mb-3 text-sm font-semibold text-[#111827]">Complexity</h4>
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#2563EB]">{projectIntel.complexity.total_functions}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Total Functions</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#2563EB]">{projectIntel.complexity.total_classes}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Total Classes</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#D97706]">{projectIntel.complexity.avg_cyclomatic_complexity}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Avg Cyclomatic Complexity</p>
                        </div>
                        <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                          <p className="text-2xl font-bold text-[#EF4444]">{projectIntel.complexity.max_complexity}</p>
                          <p className="mt-0.5 text-xs font-medium text-[#6B7280]">Maximum Complexity</p>
                        </div>
                      </div>
                      {/* Complexity Distribution */}
                      <div className="mt-4 grid gap-2 sm:grid-cols-4">
                        {projectIntel.complexity_distribution.map((d) => (
                          <div key={d.label} className="rounded-lg border border-[#E5E7EB] p-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-medium text-[#6B7280]">{d.label}</span>
                              <span className="text-xs font-semibold text-[#111827]">{d.count}</span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                              <div className="h-full rounded-full bg-[#2563EB]" style={{ width: `${d.percentage}%` }} />
                            </div>
                            <p className="mt-1 text-right text-[10px] text-[#9CA3AF]">{d.percentage}%</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Row 3: Maintainability */}
                    <div>
                      <h4 className="mb-3 text-sm font-semibold text-[#111827]">Maintainability</h4>
                      <div className="flex items-center gap-6 rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-6">
                        <div className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-[#2563EB]">
                          <span className="text-2xl font-bold text-[#2563EB]">{projectIntel.maintainability.score}</span>
                        </div>
                        <div>
                          <div className="flex items-center gap-3">
                            <span className={`inline-flex items-center rounded-full px-3 py-1 text-lg font-bold ${
                              projectIntel.maintainability.grade === "A" ? "bg-[#D1FAE5] text-[#065F46]" :
                              projectIntel.maintainability.grade === "B" ? "bg-[#DBEAFE] text-[#1E40AF]" :
                              projectIntel.maintainability.grade === "C" ? "bg-[#FEF3C7] text-[#92400E]" :
                              projectIntel.maintainability.grade === "D" ? "bg-[#FEE2E2] text-[#991B1B]" :
                              "bg-[#FEE2E2] text-[#991B1B]"
                            }`}>{projectIntel.maintainability.grade}</span>
                            <span className={`text-sm font-medium ${
                              projectIntel.maintainability.score >= 80 ? "text-[#059669]" :
                              projectIntel.maintainability.score >= 65 ? "text-[#D97706]" :
                              "text-[#EF4444]"
                            }`}>
                              {projectIntel.maintainability.score >= 80 ? "Good" :
                               projectIntel.maintainability.score >= 65 ? "Fair" :
                               projectIntel.maintainability.score >= 50 ? "Poor" : "Needs Work"}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-[#6B7280]">
                            Based on comment ratio, complexity, file sizes, and function-to-class balance
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Row 4: Code Organization */}
                    {projectIntel.code_organization.length > 0 && (
                      <div>
                        <h4 className="mb-3 text-sm font-semibold text-[#111827]">Code Organization</h4>
                        <div className="grid gap-2">
                          {projectIntel.code_organization.map((issue, i) => (
                            <div key={i} className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-3">
                              <div className="flex items-center gap-3 min-w-0">
                                <div className={`flex h-6 w-6 items-center justify-center rounded-full shrink-0 ${
                                  issue.severity === "warning" ? "bg-[#FEF3C7]" : "bg-[#DBEAFE]"
                                }`}>
                                  <AlertTriangle className={`h-3.5 w-3.5 ${issue.severity === "warning" ? "text-[#D97706]" : "text-[#2563EB]"}`} />
                                </div>
                                <div className="min-w-0">
                                  <p className="text-sm font-medium text-[#111827] capitalize">{issue.type.replace(/_/g, " ")}</p>
                                  <p className="truncate text-xs text-[#6B7280]">{issue.detail}</p>
                                </div>
                              </div>
                              <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                                issue.severity === "warning" ? "bg-[#FEF3C7] text-[#92400E]" : "bg-[#DBEAFE] text-[#1E40AF]"
                              }`}>{issue.severity}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Row 5: Code Style */}
                    {projectIntel.code_style.length > 0 && (
                      <div>
                        <h4 className="mb-3 text-sm font-semibold text-[#111827]">Code Style</h4>
                        <div className="grid gap-2">
                          {projectIntel.code_style.map((issue, i) => (
                            <div key={i} className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-3">
                              <div className="flex items-center gap-3 min-w-0">
                                <div className={`flex h-6 w-6 items-center justify-center rounded-full shrink-0 ${
                                  issue.severity === "warning" ? "bg-[#FEF3C7]" : "bg-[#DBEAFE]"
                                }`}>
                                  <AlertTriangle className={`h-3.5 w-3.5 ${issue.severity === "warning" ? "text-[#D97706]" : "text-[#2563EB]"}`} />
                                </div>
                                <div className="min-w-0">
                                  <p className="text-sm font-medium text-[#111827] capitalize">{issue.type.replace(/_/g, " ")}</p>
                                  <p className="truncate text-xs text-[#6B7280]">{issue.detail}</p>
                                </div>
                              </div>
                              <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                                issue.severity === "warning" ? "bg-[#FEF3C7] text-[#92400E]" : "bg-[#DBEAFE] text-[#1E40AF]"
                              }`}>{issue.severity}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Row 6: Project Statistics */}
                    <div>
                      <h4 className="mb-3 text-sm font-semibold text-[#111827]">Project Statistics</h4>
                      <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
                        {projectIntel.project_stats.python_files > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#2563EB]">{projectIntel.project_stats.python_files}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">Python</p>
                          </div>
                        )}
                        {projectIntel.project_stats.javascript_files > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#D97706]">{projectIntel.project_stats.javascript_files}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">JavaScript/TypeScript</p>
                          </div>
                        )}
                        {projectIntel.project_stats.html_files > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#7C3AED]">{projectIntel.project_stats.html_files}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">HTML</p>
                          </div>
                        )}
                        {projectIntel.project_stats.css_files > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#059669]">{projectIntel.project_stats.css_files}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">CSS/SCSS</p>
                          </div>
                        )}
                        {projectIntel.project_stats.json_files > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#6B7280]">{projectIntel.project_stats.json_files}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">JSON</p>
                          </div>
                        )}
                        {projectIntel.project_stats.markdown_files > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#6B7280]">{projectIntel.project_stats.markdown_files}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">Markdown</p>
                          </div>
                        )}
                        {projectIntel.project_stats.images > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#6B7280]">{projectIntel.project_stats.images}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">Images</p>
                          </div>
                        )}
                        {projectIntel.project_stats.videos > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#6B7280]">{projectIntel.project_stats.videos}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">Videos</p>
                          </div>
                        )}
                        {projectIntel.project_stats.other_assets > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-center">
                            <p className="text-lg font-bold text-[#6B7280]">{projectIntel.project_stats.other_assets}</p>
                            <p className="text-[10px] font-medium text-[#6B7280]">Other Assets</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Row 7: Charts - Language Distribution & LOC per Language */}
                    {projectIntel.language_distribution.length > 0 && (
                      <div className="grid gap-6 lg:grid-cols-2">
                        <div>
                          <h4 className="mb-3 text-sm font-semibold text-[#111827]">Language Distribution</h4>
                          <div className="space-y-2 rounded-lg border border-[#E5E7EB] p-4">
                            {projectIntel.language_distribution.map((lang, i) => {
                              const colors = ["#2563EB", "#D97706", "#7C3AED", "#059669", "#DC2626", "#0891B2", "#6B7280"];
                              return (
                                <div key={lang.language} className="flex items-center gap-3">
                                  <span className="w-24 text-right text-xs font-medium text-[#6B7280] truncate" title={lang.language}>{lang.language}</span>
                                  <div className="flex-1">
                                    <div className="h-5 rounded-full bg-[#F3F4F6] overflow-hidden">
                                      <div className="h-full rounded-full transition-all duration-700 flex items-center justify-end pr-2" style={{ width: `${lang.percentage}%`, backgroundColor: colors[i % colors.length] }}>
                                        {lang.percentage > 10 && <span className="text-[10px] font-bold text-white">{lang.percentage}%</span>}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                        <div>
                          <h4 className="mb-3 text-sm font-semibold text-[#111827]">Lines of Code per Language</h4>
                          <div className="space-y-2 rounded-lg border border-[#E5E7EB] p-4">
                            {projectIntel.language_loc.slice(0, 8).map((lang, i) => {
                              const maxLoc = projectIntel.language_loc[0]?.lines || 1;
                              const pct = (lang.lines / maxLoc) * 100;
                              const colors = ["#2563EB", "#D97706", "#7C3AED", "#059669", "#DC2626", "#0891B2", "#6B7280"];
                              return (
                                <div key={lang.language} className="flex items-center gap-3">
                                  <span className="w-24 text-right text-xs font-medium text-[#6B7280] truncate" title={lang.language}>{lang.language}</span>
                                  <div className="flex-1">
                                    <div className="h-5 rounded-full bg-[#F3F4F6] overflow-hidden">
                                      <div className="h-full rounded-full transition-all duration-700 flex items-center justify-end pr-2" style={{ width: `${pct}%`, backgroundColor: colors[i % colors.length] }}>
                                        {pct > 15 && <span className="text-[10px] font-bold text-white">{lang.lines.toLocaleString()}</span>}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Row 8: Largest Directories & Largest Files */}
                    <div className="grid gap-6 lg:grid-cols-2">
                      <div>
                        <h4 className="mb-3 text-sm font-semibold text-[#111827]">Largest Directories</h4>
                        <div className="space-y-1.5 rounded-lg border border-[#E5E7EB] p-4">
                          {projectIntel.largest_directories.length === 0 ? (
                            <p className="py-4 text-center text-sm text-[#6B7280]">No directory data available.</p>
                          ) : (
                            projectIntel.largest_directories.slice(0, 8).map((dir, _i) => {
                              const maxSize = projectIntel.largest_directories[0]?.size || 1;
                              const pct = (dir.size / maxSize) * 100;
                              return (
                                <div key={dir.path} className="flex items-center gap-3">
                                  <span className="w-32 text-right text-xs font-medium text-[#6B7280] truncate" title={dir.path}>{dir.path}</span>
                                  <div className="flex-1">
                                    <div className="h-5 rounded-full bg-[#F3F4F6] overflow-hidden">
                                      <div className="h-full rounded-full bg-[#2563EB] transition-all duration-700 flex items-center justify-end pr-2" style={{ width: `${pct}%` }}>
                                        {pct > 15 && <span className="text-[10px] font-bold text-white">{formatSize(dir.size)}</span>}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              );
                            })
                          )}
                        </div>
                      </div>
                      <div>
                        <h4 className="mb-3 text-sm font-semibold text-[#111827]">Largest Files</h4>
                        <div className="space-y-1.5 rounded-lg border border-[#E5E7EB] p-4">
                          {projectIntel.largest_files.length === 0 ? (
                            <p className="py-4 text-center text-sm text-[#6B7280]">No file data available.</p>
                          ) : (
                            projectIntel.largest_files.slice(0, 8).map((f, _i) => {
                              const maxSize = projectIntel.largest_files[0]?.size || 1;
                              const pct = (f.size / maxSize) * 100;
                              return (
                                <div key={f.path} className="flex items-center gap-3">
                                  <span className="w-32 text-right text-xs font-medium text-[#6B7280] truncate" title={f.path}>{f.path}</span>
                                  <div className="flex-1">
                                    <div className="h-5 rounded-full bg-[#F3F4F6] overflow-hidden">
                                      <div className="h-full rounded-full bg-[#D97706] transition-all duration-700 flex items-center justify-end pr-2" style={{ width: `${pct}%` }}>
                                        {pct > 15 && <span className="text-[10px] font-bold text-white">{formatSize(f.size)}</span>}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              );
                            })
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Row 9: Recommendations */}
                    {projectIntel.recommendations.length > 0 && (
                      <div>
                        <h4 className="mb-3 text-sm font-semibold text-[#111827]">Recommendations</h4>
                        <div className="grid gap-2">
                          {projectIntel.recommendations.map((rec, i) => {
                            const iconColors: Record<string, string> = {
                              maintainability: "bg-[#FEF3C7] text-[#D97706]",
                              complexity: "bg-[#FEE2E2] text-[#DC2626]",
                              documentation: "bg-[#DBEAFE] text-[#2563EB]",
                              duplication: "bg-[#F3E8FF] text-[#7C3AED]",
                              refactoring: "bg-[#FEF3C7] text-[#D97706]",
                              modularization: "bg-[#DBEAFE] text-[#2563EB]",
                              organization: "bg-[#DBEAFE] text-[#2563EB]",
                              good_job: "bg-[#D1FAE5] text-[#059669]",
                            };
                            const colors = iconColors[rec.type] || "bg-[#F3F4F6] text-[#6B7280]";
                            return (
                              <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                                <div className={`flex h-6 w-6 items-center justify-center rounded-full shrink-0 mt-0.5 ${colors}`}>
                                  <Lightbulb className="h-3.5 w-3.5" />
                                </div>
                                <p className="text-sm text-[#374151]">{rec.detail}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Card 10: AI Project Insights */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Lightbulb} title="AI Project Insights" />
              <div className="p-6">
                {insightsLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">{INSIGHTS_LOADING_STAGES[insightsStage]}</p>
                    <div className="mt-3 flex gap-1">
                      {INSIGHTS_LOADING_STAGES.map((_, i) => (
                        <div key={i} className={`h-1 w-16 rounded-full transition-colors duration-500 ${i <= insightsStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"}`} />
                      ))}
                    </div>
                  </div>
                ) : !projectInsights ? (
                  <div className="py-6 text-center">
                    <Lightbulb className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">Project insights unavailable.</p>
                  </div>
                ) : (
                  <div className="space-y-6">

                    {/* Health Score */}
                    <div className="flex flex-col items-center rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-6">
                      <div className="flex items-center gap-6">
                        <div className={`flex h-24 w-24 items-center justify-center rounded-full border-4 ${
                          projectInsights.health_score.score >= 85 ? "border-[#059669]" :
                          projectInsights.health_score.score >= 70 ? "border-[#2563EB]" :
                          projectInsights.health_score.score >= 50 ? "border-[#D97706]" :
                          projectInsights.health_score.score >= 30 ? "border-[#DC2626]" :
                          "border-[#7F1D1D]"
                        }`}>
                          <span className={`text-3xl font-bold ${
                            projectInsights.health_score.score >= 85 ? "text-[#059669]" :
                            projectInsights.health_score.score >= 70 ? "text-[#2563EB]" :
                            projectInsights.health_score.score >= 50 ? "text-[#D97706]" :
                            "text-[#DC2626]"
                          }`}>{projectInsights.health_score.score}</span>
                        </div>
                        <div>
                          <p className="text-lg font-semibold text-[#111827]">Overall Project Health</p>
                          <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold mt-1 ${
                            projectInsights.health_score.classification === "Excellent" ? "bg-[#D1FAE5] text-[#065F46]" :
                            projectInsights.health_score.classification === "Good" ? "bg-[#DBEAFE] text-[#1E40AF]" :
                            projectInsights.health_score.classification === "Average" ? "bg-[#FEF3C7] text-[#92400E]" :
                            projectInsights.health_score.classification === "Needs Improvement" ? "bg-[#FEE2E2] text-[#991B1B]" :
                            "bg-[#FEE2E2] text-[#7F1D1D]"
                          }`}>{projectInsights.health_score.classification}</span>
                        </div>
                      </div>
                    </div>

                    {/* AI Summary */}
                    {projectInsights.ai_summary.length > 0 && (
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-5">
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <FileText className="h-4 w-4 text-[#2563EB]" />
                          AI Summary
                        </h4>
                        <ul className="space-y-1.5">
                          {projectInsights.ai_summary.map((s, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm leading-relaxed text-[#374151]">
                              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#2563EB]" />
                              {s}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Strengths & Weaknesses */}
                    <div className="grid gap-6 lg:grid-cols-2">
                      <div>
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <CheckCircle2 className="h-4 w-4 text-[#059669]" />
                          Strengths
                        </h4>
                        {projectInsights.strengths.length === 0 ? (
                          <p className="text-sm text-[#6B7280]">No specific strengths identified.</p>
                        ) : (
                          <div className="space-y-2">
                            {projectInsights.strengths.map((s, i) => (
                              <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#D1FAE5] shrink-0 mt-0.5">
                                  <CheckCircle2 className="h-3.5 w-3.5 text-[#059669]" />
                                </div>
                                <div className="min-w-0">
                                  <p className="text-xs font-semibold text-[#059669] uppercase tracking-wide">{s.category}</p>
                                  <p className="text-sm text-[#374151]">{s.detail}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      <div>
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <AlertTriangle className="h-4 w-4 text-[#D97706]" />
                          Weaknesses
                        </h4>
                        {projectInsights.weaknesses.length === 0 ? (
                          <p className="text-sm text-[#6B7280]">No significant weaknesses detected.</p>
                        ) : (
                          <div className="space-y-2">
                            {projectInsights.weaknesses.map((w, i) => (
                              <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#FEF3C7] shrink-0 mt-0.5">
                                  <AlertTriangle className="h-3.5 w-3.5 text-[#D97706]" />
                                </div>
                                <div className="min-w-0">
                                  <p className="text-xs font-semibold text-[#92400E] uppercase tracking-wide">{w.category}</p>
                                  <p className="text-sm text-[#374151]">{w.detail}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Risk & Scalability */}
                    <div className="grid gap-6 lg:grid-cols-2">
                      <div className="rounded-lg border border-[#E5E7EB] p-5">
                        <h4 className="mb-3 text-sm font-semibold text-[#111827]">Risk Analysis</h4>
                        <div className="flex items-center gap-4">
                          <div className={`flex h-16 w-16 items-center justify-center rounded-full border-4 ${
                            projectInsights.risk_analysis.level === "Low" ? "border-[#059669]" :
                            projectInsights.risk_analysis.level === "Medium" ? "border-[#D97706]" :
                            projectInsights.risk_analysis.level === "High" ? "border-[#DC2626]" :
                            "border-[#7F1D1D]"
                          }`}>
                            <span className={`text-lg font-bold ${
                              projectInsights.risk_analysis.level === "Low" ? "text-[#059669]" :
                              projectInsights.risk_analysis.level === "Medium" ? "text-[#D97706]" :
                              "text-[#DC2626]"
                            }`}>{projectInsights.risk_analysis.score}</span>
                          </div>
                          <div className="flex-1">
                            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                              projectInsights.risk_analysis.level === "Low" ? "bg-[#D1FAE5] text-[#065F46]" :
                              projectInsights.risk_analysis.level === "Medium" ? "bg-[#FEF3C7] text-[#92400E]" :
                              projectInsights.risk_analysis.level === "High" ? "bg-[#FEE2E2] text-[#991B1B]" :
                              "bg-[#FEE2E2] text-[#7F1D1D]"
                            }`}>{projectInsights.risk_analysis.level} Risk</span>
                            <p className="mt-1.5 text-sm text-[#6B7280]">{projectInsights.risk_analysis.explanation}</p>
                          </div>
                        </div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] p-5">
                        <h4 className="mb-3 text-sm font-semibold text-[#111827]">Scalability</h4>
                        <div className="flex items-center gap-4">
                          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#DBEAFE] border-4 border-[#2563EB]">
                            <span className="text-lg font-bold text-[#2563EB]">
                              {projectInsights.scalability.level === "Small" ? "S" :
                               projectInsights.scalability.level === "Medium" ? "M" :
                               projectInsights.scalability.level === "Large" ? "L" : "E"}
                            </span>
                          </div>
                          <div className="flex-1">
                            <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2.5 py-0.5 text-xs font-semibold text-[#1E40AF]">
                              {projectInsights.scalability.level}
                            </span>
                            <p className="mt-1.5 text-sm text-[#6B7280]">{projectInsights.scalability.reason}</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Performance Insights */}
                    {projectInsights.performance_insights.length > 0 && (
                      <div>
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <Monitor className="h-4 w-4 text-[#2563EB]" />
                          Performance Analysis
                        </h4>
                        <div className="grid gap-2">
                          {projectInsights.performance_insights.map((p, i) => (
                            <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#DBEAFE] shrink-0 mt-0.5">
                                <Info className="h-3.5 w-3.5 text-[#2563EB]" />
                              </div>
                              <p className="text-sm text-[#374151]">{p.detail}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Security Insights */}
                    {projectInsights.security_insights.length > 0 && (
                      <div>
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <Shield className="h-4 w-4 text-[#DC2626]" />
                          Security Insights
                        </h4>
                        <div className="grid gap-2">
                          {projectInsights.security_insights.map((s, i) => (
                            <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                              <div className={`flex h-6 w-6 items-center justify-center rounded-full shrink-0 mt-0.5 ${
                                s.severity === "critical" || s.severity === "high" ? "bg-[#FEE2E2]" : s.severity === "warning" ? "bg-[#FEF3C7]" : "bg-[#DBEAFE]"
                              }`}>
                                <Shield className={`h-3.5 w-3.5 ${
                                  s.severity === "critical" || s.severity === "high" ? "text-[#DC2626]" : s.severity === "warning" ? "text-[#D97706]" : "text-[#2563EB]"
                                }`} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-[#374151]">{s.detail}</p>
                              </div>
                              <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                                s.severity === "critical" || s.severity === "high" ? "bg-[#FEE2E2] text-[#991B1B]" :
                                s.severity === "warning" ? "bg-[#FEF3C7] text-[#92400E]" : "bg-[#DBEAFE] text-[#1E40AF]"
                              }`}>{s.severity}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Code Quality Insights */}
                    {projectInsights.code_quality_insights.length > 0 && (
                      <div>
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <Code className="h-4 w-4 text-[#7C3AED]" />
                          Code Quality Insights
                        </h4>
                        <div className="grid gap-2">
                          {projectInsights.code_quality_insights.map((q, i) => (
                            <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                              <div className={`flex h-6 w-6 items-center justify-center rounded-full shrink-0 mt-0.5 ${
                                q.type === "clean" ? "bg-[#D1FAE5]" : "bg-[#F3E8FF]"
                              }`}>
                                <Info className={`h-3.5 w-3.5 ${q.type === "clean" ? "text-[#059669]" : "text-[#7C3AED]"}`} />
                              </div>
                              <p className="text-sm text-[#374151]">{q.detail}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Readiness Scores */}
                    <div>
                      <h4 className="mb-3 text-sm font-semibold text-[#111827]">Readiness Scores</h4>
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        {projectInsights.readiness_scores.map((r) => (
                          <div key={r.category} className="rounded-lg border border-[#E5E7EB] p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-medium text-[#6B7280]">{r.category}</span>
                              <span className={`text-sm font-bold ${
                                r.score >= 80 ? "text-[#059669]" : r.score >= 60 ? "text-[#2563EB]" :
                                r.score >= 40 ? "text-[#D97706]" : "text-[#DC2626]"
                              }`}>{r.score}%</span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                              <div className="h-full rounded-full transition-all duration-700" style={{
                                width: `${r.score}%`,
                                backgroundColor: r.score >= 80 ? "#059669" : r.score >= 60 ? "#2563EB" :
                                  r.score >= 40 ? "#D97706" : "#DC2626"
                              }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Recommended Actions */}
                    {projectInsights.recommended_actions.length > 0 && (
                      <div>
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <ListChecks className="h-4 w-4 text-[#2563EB]" />
                          Recommended Next Actions
                        </h4>
                        <div className="space-y-2">
                          {projectInsights.recommended_actions.map((action, i) => (
                            <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                              <div className={`flex h-6 w-6 items-center justify-center rounded-full shrink-0 mt-0.5 ${
                                action.priority === "high" ? "bg-[#FEE2E2]" : action.priority === "medium" ? "bg-[#FEF3C7]" : "bg-[#DBEAFE]"
                              }`}>
                                <span className={`text-[10px] font-bold ${
                                  action.priority === "high" ? "text-[#DC2626]" : action.priority === "medium" ? "text-[#D97706]" : "text-[#2563EB]"
                                }`}>{i + 1}</span>
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-[#374151]">{action.action}</p>
                              </div>
                              <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                                action.priority === "high" ? "bg-[#FEE2E2] text-[#991B1B]" :
                                action.priority === "medium" ? "bg-[#FEF3C7] text-[#92400E]" : "bg-[#DBEAFE] text-[#1E40AF]"
                              }`}>{action.priority} Priority</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Maintainability */}
                    <div className="rounded-lg border border-[#E5E7EB] p-5">
                      <h4 className="mb-3 text-sm font-semibold text-[#111827]">Maintainability Analysis</h4>
                      <div className="flex items-center gap-4">
                        <div className={`flex h-16 w-16 items-center justify-center rounded-full border-4 ${
                          projectInsights.maintainability.grade === "A" ? "border-[#059669]" :
                          projectInsights.maintainability.grade === "B" ? "border-[#2563EB]" :
                          projectInsights.maintainability.grade === "C" ? "border-[#D97706]" :
                          "border-[#DC2626]"
                        }`}>
                          <span className={`text-xl font-bold ${
                            projectInsights.maintainability.grade === "A" ? "text-[#059669]" :
                            projectInsights.maintainability.grade === "B" ? "text-[#2563EB]" :
                            projectInsights.maintainability.grade === "C" ? "text-[#D97706]" :
                            "text-[#DC2626]"
                          }`}>{projectInsights.maintainability.grade}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <span className="text-lg font-semibold text-[#111827]">Grade {projectInsights.maintainability.grade}</span>
                            <span className="text-sm text-[#6B7280]">({projectInsights.maintainability.score}/100)</span>
                          </div>
                          <p className="mt-1 text-sm text-[#6B7280]">{projectInsights.maintainability_explanation}</p>
                        </div>
                      </div>
                    </div>

                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Card 11: Analyzer Validation */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={CheckCircle2} title="Analyzer Validation" />
              <div className="p-6">
                {validationLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">{VALIDATION_LOADING_STAGES[validationStage]}</p>
                    <div className="mt-3 flex gap-1">
                      {VALIDATION_LOADING_STAGES.map((_, i) => (
                        <div key={i} className={`h-1 w-16 rounded-full transition-colors duration-500 ${i <= validationStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"}`} />
                      ))}
                    </div>
                  </div>
                ) : !validationResult ? (
                  <div className="py-6 text-center">
                    <CheckCircle2 className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">Validation results unavailable.</p>
                  </div>
                ) : (
                  <div className="space-y-5">

                    {/* Summary Stats */}
                    <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <div className="text-2xl font-bold text-[#111827]">{validationResult.consistency_score}</div>
                        <div className="mt-1 text-xs font-medium text-[#6B7280]">Consistency Score</div>
                        <span className={`mt-1 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          validationResult.classification === "Excellent" ? "bg-[#D1FAE5] text-[#065F46]" :
                          validationResult.classification === "Good" ? "bg-[#DBEAFE] text-[#1E40AF]" :
                          validationResult.classification === "Average" ? "bg-[#FEF3C7] text-[#92400E]" :
                          "bg-[#FEE2E2] text-[#991B1B]"
                        }`}>{validationResult.classification}</span>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <div className="text-2xl font-bold text-[#059669]">{validationResult.passed_checks}</div>
                        <div className="mt-1 text-xs font-medium text-[#6B7280]">Passed</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <div className="text-2xl font-bold text-[#DC2626]">{validationResult.failed_checks}</div>
                        <div className="mt-1 text-xs font-medium text-[#6B7280]">Failed</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <div className="text-2xl font-bold text-[#D97706]">{validationResult.warnings}</div>
                        <div className="mt-1 text-xs font-medium text-[#6B7280]">Warnings</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-center">
                        <div className="text-2xl font-bold text-[#7F1D1D]">{validationResult.critical_errors}</div>
                        <div className="mt-1 text-xs font-medium text-[#6B7280]">Critical</div>
                      </div>
                    </div>

                    {/* Individual Checks */}
                    <div>
                      <h4 className="mb-3 text-sm font-semibold text-[#111827]">Consistency Checks</h4>
                      <div className="space-y-2">
                        {validationResult.checks.map((check, i) => (
                          <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                            <div className={`flex h-6 w-6 items-center justify-center rounded-full shrink-0 mt-0.5 ${
                              check.status === "passed" ? "bg-[#D1FAE5]" :
                              check.status === "warning" ? "bg-[#FEF3C7]" :
                              "bg-[#FEE2E2]"
                            }`}>
                              {check.status === "passed" ? (
                                <CheckCircle2 className="h-3.5 w-3.5 text-[#059669]" />
                              ) : check.status === "warning" ? (
                                <AlertTriangle className="h-3.5 w-3.5 text-[#D97706]" />
                              ) : (
                                <XCircle className="h-3.5 w-3.5 text-[#DC2626]" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-[#111827]">{check.check_name}</p>
                              <p className="mt-0.5 text-xs text-[#6B7280]">{check.detail}</p>
                              {check.modules_involved.length > 0 && (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {check.modules_involved.map((mod, j) => (
                                    <span key={j} className="inline-flex items-center rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#6B7280]">{mod}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                            <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                              check.status === "passed" ? "bg-[#D1FAE5] text-[#065F46]" :
                              check.status === "warning" ? "bg-[#FEF3C7] text-[#92400E]" :
                              "bg-[#FEE2E2] text-[#991B1B]"
                            }`}>{check.status}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Validation Report */}
                    <div>
                      <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                        <FileText className="h-4 w-4 text-[#2563EB]" />
                        Validation Report
                      </h4>
                      <div className="space-y-3">
                        {validationResult.validation_report.map((report, i) => (
                          <details key={i} className="group rounded-lg border border-[#E5E7EB]">
                            <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-medium text-[#111827] hover:bg-[#F9FAFB]">
                              <div className="flex items-center gap-2">
                                <span className={`h-2 w-2 rounded-full ${
                                  report.status === "passed" ? "bg-[#059669]" :
                                  report.status === "warning" ? "bg-[#D97706]" :
                                  "bg-[#DC2626]"
                                }`} />
                                {report.category}
                              </div>
                              <span className="text-xs text-[#6B7280]">
                                {report.checks.filter(c => c.status === "passed").length}/{report.checks.length} passed
                              </span>
                            </summary>
                            <div className="border-t border-[#E5E7EB] px-4 py-3">
                              <div className="space-y-2">
                                {report.checks.map((check, j) => (
                                  <div key={j} className="flex items-start gap-2 text-xs">
                                    <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                                      check.status === "passed" ? "bg-[#059669]" :
                                      check.status === "warning" ? "bg-[#D97706]" :
                                      "bg-[#DC2626]"
                                    }`} />
                                    <div className="min-w-0">
                                      <p className="font-medium text-[#374151]">{check.check_name}</p>
                                      <p className="text-[#6B7280]">{check.detail}</p>
                                    </div>
                                    <span className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] capitalize ${
                                      check.status === "passed" ? "bg-[#D1FAE5] text-[#065F46]" :
                                      check.status === "warning" ? "bg-[#FEF3C7] text-[#92400E]" :
                                      "bg-[#FEE2E2] text-[#991B1B]"
                                    }`}>{check.status}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </details>
                        ))}
                      </div>
                    </div>

                    {/* Self-Healing Actions */}
                    {validationResult.self_healing.length > 0 && (
                      <div>
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <RefreshCw className="h-4 w-4 text-[#7C3AED]" />
                          Self-Healing Actions
                        </h4>
                        <div className="space-y-2">
                          {validationResult.self_healing.map((action, i) => (
                            <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#F3E8FF] shrink-0 mt-0.5">
                                <RefreshCw className="h-3.5 w-3.5 text-[#7C3AED]" />
                              </div>
                              <div className="min-w-0">
                                <p className="text-xs font-semibold uppercase tracking-wide text-[#7C3AED]">{action.check_name}</p>
                                <p className="text-sm text-[#374151]">{action.detail}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {validationResult.recommendations.length > 0 && (
                      <div>
                        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#111827]">
                          <Lightbulb className="h-4 w-4 text-[#2563EB]" />
                          Recommendations
                        </h4>
                        <div className="space-y-2">
                          {validationResult.recommendations.map((rec, i) => (
                            <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3">
                              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#DBEAFE] shrink-0 mt-0.5">
                                <span className="text-[10px] font-bold text-[#2563EB]">{i + 1}</span>
                              </div>
                              <p className="text-sm text-[#374151]">{rec}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Card 12: Code Intelligence */}
          <motion.div variants={itemVariants}>
            <Card className="mb-6 overflow-hidden">
              <SectionHeader icon={Code} title="Code Intelligence" />
              <div className="p-6">
                {codeIntelLoading ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="relative mb-4">
                      <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                    <p className="text-sm font-medium text-[#111827]">{CODE_INTEL_LOADING_STAGES[codeIntelStage]}</p>
                    <div className="mt-3 flex gap-1">
                      {CODE_INTEL_LOADING_STAGES.map((_, i) => (
                        <div key={i} className={`h-1 w-16 rounded-full transition-colors duration-500 ${i <= codeIntelStage ? "bg-[#2563EB]" : "bg-[#E5E7EB]"}`} />
                      ))}
                    </div>
                  </div>
                ) : !codeIntel ? (
                  <div className="py-6 text-center">
                    <Code className="mx-auto h-10 w-10 text-[#9CA3AF]" />
                    <p className="mt-3 text-sm font-medium text-[#6B7280]">Code intelligence unavailable.</p>
                  </div>
                ) : (
                  <div className="space-y-5">

                    {/* Summary */}
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_files}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Source Files</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_classes}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Classes</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_functions}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Functions</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_imports}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Imports</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_external_imports}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">External</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_enums}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Enums</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_interfaces}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Interfaces</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_variables}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Variables</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.total_modules}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Modules</div>
                      </div>
                      <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-center">
                        <div className="text-xl font-bold text-[#111827]">{codeIntel.summary.languages.length}</div>
                        <div className="mt-0.5 text-[10px] font-medium text-[#6B7280]">Languages</div>
                      </div>
                    </div>

                    {/* Search */}
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9CA3AF]" />
                      <input
                        type="text"
                        value={ciSearch}
                        onChange={(e) => setCiSearch(e.target.value)}
                        placeholder="Search by class, function, file, or module..."
                        className="w-full rounded-lg border border-[#E5E7EB] py-2.5 pl-10 pr-4 text-sm text-[#111827] placeholder:text-[#9CA3AF] focus:border-[#2563EB] focus:outline-none"
                      />
                    </div>

                    {/* Filtered Results */}
                    {ciSearch && (() => {
                      const q = ciSearch.toLowerCase();
                      const matchedClasses = codeIntel.classes.filter(c => c.name.toLowerCase().includes(q));
                      const matchedFunctions = codeIntel.functions.filter(f => f.name.toLowerCase().includes(q));
                      const matchedFiles = codeIntel.files.filter(f => f.path.toLowerCase().includes(q));
                      const matchedModules = codeIntel.modules.filter(m => m.name.toLowerCase().includes(q));
                      return (
                        <div className="rounded-lg border border-[#2563EB] bg-[#EFF6FF] p-4">
                          <p className="mb-2 text-xs font-semibold text-[#2563EB] uppercase tracking-wide">Search Results</p>
                          {matchedClasses.length > 0 && <p className="text-xs text-[#374151]">Classes: {matchedClasses.map(c => c.name).join(", ")}</p>}
                          {matchedFunctions.length > 0 && <p className="text-xs text-[#374151]">Functions: {matchedFunctions.map(f => f.name).join(", ")}</p>}
                          {matchedFiles.length > 0 && <p className="text-xs text-[#374151]">Files: {matchedFiles.map(f => f.path.split("/").pop()).join(", ")}</p>}
                          {matchedModules.length > 0 && <p className="text-xs text-[#374151]">Modules: {matchedModules.map(m => m.name).join(", ")}</p>}
                          {matchedClasses.length + matchedFunctions.length + matchedFiles.length + matchedModules.length === 0 && (
                            <p className="text-xs text-[#6B7280]">No matches found.</p>
                          )}
                        </div>
                      );
                    })()}

                    {/* Source Files */}
                    <details className="group rounded-lg border border-[#E5E7EB]" open>
                      <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-medium text-[#111827] hover:bg-[#F9FAFB]">
                        <div className="flex items-center gap-2">
                          <FileCode className="h-4 w-4 text-[#2563EB]" />
                          Source Files ({codeIntel.files.length})
                        </div>
                        <ChevronDown className="h-4 w-4 text-[#6B7280] transition-transform group-open:rotate-180" />
                      </summary>
                      <div className="border-t border-[#E5E7EB]">
                        <div className="max-h-80 overflow-y-auto">
                          {codeIntel.files.map((file, i) => (
                            <div key={i} className="flex items-center gap-3 border-b border-[#F3F4F6] px-4 py-2.5 text-xs hover:bg-[#F9FAFB]">
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-[#111827] truncate">{file.path}</p>
                                <span className="inline-flex items-center rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#6B7280]">{file.language}</span>
                              </div>
                              <span className="shrink-0 text-[#6B7280]">{file.lines_of_code} LOC</span>
                              <span className="shrink-0 text-[#6B7280]">{file.functions} fn</span>
                              <span className="shrink-0 text-[#6B7280]">{file.classes} cls</span>
                              <span className="shrink-0 text-[#6B7280]">{file.imports} imp</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </details>

                    {/* Classes */}
                    {codeIntel.classes.length > 0 && (
                      <details className="group rounded-lg border border-[#E5E7EB]">
                        <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-medium text-[#111827] hover:bg-[#F9FAFB]">
                          <div className="flex items-center gap-2">
                            <Box className="h-4 w-4 text-[#7C3AED]" />
                            Classes ({codeIntel.classes.length})
                          </div>
                          <ChevronDown className="h-4 w-4 text-[#6B7280] transition-transform group-open:rotate-180" />
                        </summary>
                        <div className="border-t border-[#E5E7EB]">
                          <div className="max-h-96 overflow-y-auto">
                            {codeIntel.classes.map((cls, i) => (
                              <details key={i} className="border-b border-[#F3F4F6]">
                                <summary className="flex cursor-pointer items-center gap-3 px-4 py-2.5 text-xs hover:bg-[#F9FAFB]">
                                  <span className={`h-2 w-2 rounded-full ${cls.is_abstract ? "bg-[#D97706]" : "bg-[#7C3AED]"}`} />
                                  <span className="font-medium text-[#111827]">{cls.name}</span>
                                  <span className="text-[#6B7280]">{cls.file_path}</span>
                                  {cls.is_abstract && <span className="rounded-full bg-[#FEF3C7] px-1.5 py-0.5 text-[10px] font-medium text-[#92400E]">abstract</span>}
                                  {cls.visibility !== "public" && <span className="rounded-full bg-[#F3F4F6] px-1.5 py-0.5 text-[10px] text-[#6B7280]">{cls.visibility}</span>}
                                </summary>
                                <div className="border-t border-[#F3F4F6] bg-[#F9FAFB] px-4 py-3">
                                  {cls.base_classes.length > 0 && (
                                    <p className="mb-1 text-[10px] text-[#6B7280]">extends: {cls.base_classes.join(", ")}</p>
                                  )}
                                  {cls.properties.length > 0 && (
                                    <div className="mb-2">
                                      <p className="mb-0.5 text-[10px] font-semibold text-[#6B7280] uppercase">Properties</p>
                                      {cls.properties.map((p, j) => (
                                        <span key={j} className="mr-1 inline-flex items-center rounded-full bg-white px-2 py-0.5 text-[10px] text-[#374151] border border-[#E5E7EB]">{p.visibility === "public" ? "" : p.visibility + " "}{p.name}{p.type ? `: ${p.type}` : ""}</span>
                                      ))}
                                    </div>
                                  )}
                                  {cls.methods.length > 0 && (
                                    <div>
                                      <p className="mb-0.5 text-[10px] font-semibold text-[#6B7280] uppercase">Methods</p>
                                      {cls.methods.map((m, j) => (
                                        <div key={j} className="mb-1 flex items-center gap-2 rounded bg-white px-2 py-1 text-[10px] text-[#374151] border border-[#E5E7EB]">
                                          {m.visibility !== "public" && <span className="text-[#9CA3AF]">{m.visibility}</span>}
                                          {m.is_static && <span className="text-[#9CA3AF]">static</span>}
                                          {m.is_async && <span className="text-[#2563EB]">async</span>}
                                          <span className="font-medium">{m.name}</span>
                                          <span className="text-[#9CA3AF]">({m.parameters.map(p => p.name).join(", ")})</span>
                                          {m.return_type && <span className="text-[#059669]">→ {m.return_type}</span>}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </details>
                            ))}
                          </div>
                        </div>
                      </details>
                    )}

                    {/* Functions */}
                    {codeIntel.functions.length > 0 && (
                      <details className="group rounded-lg border border-[#E5E7EB]">
                        <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-medium text-[#111827] hover:bg-[#F9FAFB]">
                          <div className="flex items-center gap-2">
                            <GitBranch className="h-4 w-4 text-[#059669]" />
                            Functions ({codeIntel.functions.length})
                          </div>
                          <ChevronDown className="h-4 w-4 text-[#6B7280] transition-transform group-open:rotate-180" />
                        </summary>
                        <div className="border-t border-[#E5E7EB]">
                          <div className="max-h-96 overflow-y-auto">
                            {codeIntel.functions.slice(0, 200).map((fn, i) => (
                              <div key={i} className="flex items-center gap-3 border-b border-[#F3F4F6] px-4 py-2 text-xs hover:bg-[#F9FAFB]">
                                <div className="flex items-center gap-1.5 min-w-0 flex-1">
                                  {fn.is_async && <span className="text-[#2563EB]">async</span>}
                                  {fn.is_static && <span className="text-[#D97706]">static</span>}
                                  {fn.is_generator && <span className="text-[#7C3AED]">gen</span>}
                                  <span className="font-medium text-[#111827]">{fn.name}</span>
                                  <span className="text-[#9CA3AF]">({fn.parameters.map(p => p.name).join(", ")})</span>
                                  {fn.return_type && <span className="text-[#059669]">: {fn.return_type}</span>}
                                </div>
                                <span className="shrink-0 text-[#9CA3AF]">{fn.file_path}:{fn.line_start}</span>
                                {fn.parent_class && <span className="shrink-0 rounded-full bg-[#F3E8FF] px-1.5 py-0.5 text-[10px] text-[#7C3AED]">{fn.parent_class}</span>}
                              </div>
                            ))}
                            {codeIntel.functions.length > 200 && (
                              <p className="px-4 py-2 text-[10px] text-[#6B7280]">Showing first 200 of {codeIntel.functions.length} functions.</p>
                            )}
                          </div>
                        </div>
                      </details>
                    )}

                    {/* Imports */}
                    {codeIntel.imports.length > 0 && (
                      <details className="group rounded-lg border border-[#E5E7EB]">
                        <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-medium text-[#111827] hover:bg-[#F9FAFB]">
                          <div className="flex items-center gap-2">
                            <Package className="h-4 w-4 text-[#D97706]" />
                            Imports ({codeIntel.imports.length})
                          </div>
                          <ChevronDown className="h-4 w-4 text-[#6B7280] transition-transform group-open:rotate-180" />
                        </summary>
                        <div className="border-t border-[#E5E7EB]">
                          <div className="max-h-80 overflow-y-auto">
                            {codeIntel.imports.slice(0, 200).map((imp, i) => (
                              <div key={i} className="flex items-center gap-3 border-b border-[#F3F4F6] px-4 py-2 text-xs hover:bg-[#F9FAFB]">
                                <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${imp.is_external ? "bg-[#D97706]" : "bg-[#2563EB]"}`} />
                                <span className="font-medium text-[#111827]">{imp.source || "(direct)"}</span>
                                {imp.names.length > 0 && <span className="text-[#6B7280]">— {imp.names.join(", ")}</span>}
                                {imp.is_external && <span className="rounded-full bg-[#FEF3C7] px-1.5 py-0.5 text-[10px] text-[#92400E]">external</span>}
                                {imp.is_duplicate && <span className="rounded-full bg-[#FEE2E2] px-1.5 py-0.5 text-[10px] text-[#991B1B]">duplicate</span>}
                              </div>
                            ))}
                            {codeIntel.imports.length > 200 && (
                              <p className="px-4 py-2 text-[10px] text-[#6B7280]">Showing first 200 of {codeIntel.imports.length} imports.</p>
                            )}
                          </div>
                        </div>
                      </details>
                    )}

                    {/* Enums & Interfaces */}
                    {(codeIntel.enums.length > 0 || codeIntel.interfaces.length > 0) && (
                      <div className="grid gap-4 lg:grid-cols-2">
                        {codeIntel.enums.length > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] p-4">
                            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#6B7280]">Enums ({codeIntel.enums.length})</h4>
                            <div className="space-y-1.5">
                              {codeIntel.enums.map((e, i) => (
                                <div key={i} className="flex items-center gap-2 rounded bg-[#F9FAFB] px-3 py-1.5 text-xs">
                                  <span className="font-medium text-[#111827]">{e.name}</span>
                                  <span className="text-[#9CA3AF]">({e.values.slice(0, 8).join(", ")}{e.values.length > 8 ? ", ..." : ""})</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {codeIntel.interfaces.length > 0 && (
                          <div className="rounded-lg border border-[#E5E7EB] p-4">
                            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#6B7280]">Interfaces ({codeIntel.interfaces.length})</h4>
                            <div className="space-y-1.5">
                              {codeIntel.interfaces.map((inf, i) => (
                                <div key={i} className="flex items-center gap-2 rounded bg-[#F9FAFB] px-3 py-1.5 text-xs">
                                  <span className="font-medium text-[#111827]">{inf.name}</span>
                                  <span className="text-[#9CA3AF]">{inf.properties.length} props, {inf.methods.length} methods</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Modules */}
                    {codeIntel.modules.length > 0 && (
                      <details className="group rounded-lg border border-[#E5E7EB]">
                        <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-medium text-[#111827] hover:bg-[#F9FAFB]">
                          <div className="flex items-center gap-2">
                            <FolderKanban className="h-4 w-4 text-[#2563EB]" />
                            Modules ({codeIntel.modules.length})
                          </div>
                          <ChevronDown className="h-4 w-4 text-[#6B7280] transition-transform group-open:rotate-180" />
                        </summary>
                        <div className="border-t border-[#E5E7EB]">
                          <div className="max-h-80 overflow-y-auto">
                            {codeIntel.modules.map((mod, i) => (
                              <div key={i} className="flex items-start gap-3 border-b border-[#F3F4F6] px-4 py-2.5 text-xs hover:bg-[#F9FAFB]">
                                <div className="min-w-0 flex-1">
                                  <p className="font-medium text-[#111827]">{mod.name === "." ? "(root)" : mod.name}</p>
                                  <div className="mt-0.5 flex flex-wrap gap-1">
                                    {mod.files.length > 0 && <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-1.5 py-0.5 text-[10px] text-[#1E40AF]">{mod.files.length} files</span>}
                                    {mod.classes.length > 0 && <span className="inline-flex items-center rounded-full bg-[#F3E8FF] px-1.5 py-0.5 text-[10px] text-[#7C3AED]">{mod.classes.length} classes</span>}
                                    {mod.submodules.length > 0 && <span className="inline-flex items-center rounded-full bg-[#D1FAE5] px-1.5 py-0.5 text-[10px] text-[#065F46]">{mod.submodules.length} submodules</span>}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </details>
                    )}

                  </div>
                )}
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
