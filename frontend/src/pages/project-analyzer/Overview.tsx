import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Award,
  Cpu,
  Server,
  FolderKanban,
  Box,
  Building2,
  GitBranch,
  HeartPulse,
  Settings,
  Package,
  Shield,
  ShieldAlert,
  Zap,
  Wrench,
  FileCode,
  FileSearch,
  FileText,
  FunctionSquare,
  GitCompare,
  BookOpen,
  FlaskConical,
  Radar,
  RefreshCw,
} from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";
import { getCodeQuality, getFileAnalysis, getFunctionClassAnalysis, getImportDependencyAnalysis, getSemanticIntelligence } from "@/lib/project-analyzer";
import type { CodeQualityResponse, FileAnalysisResponse, FunctionClassResponse, ImportDependencyResponse, SemanticResponse } from "@/types/project-analyzer";

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
  { path: "code-intelligence", label: "Code Intelligence", icon: FileCode, desc: "Source code analysis, function and class detection, import mapping, and code metrics." },
  { path: "code-quality", label: "Code Quality", icon: Award, desc: "Quality scores, issue detection, code smells, complexity analysis, and maintainability." },
  { path: "file-analysis", label: "File Analysis", icon: FileText, desc: "File-level metrics, size distribution, health scores, and duplicate detection." },
  { path: "function-class", label: "Function & Class", icon: FunctionSquare, desc: "Function and class detection, complexity tracking, and relationship mapping." },
  { path: "recommendations", label: "AI Recommendations", icon: Shield, desc: "Project health, risks, scalability, performance, security insights, and readiness scores." },
  { path: "semantic-intelligence", label: "Semantic Intelligence", icon: Radar, desc: "Semantic component classification, business flow detection, understanding score, and knowledge graph analysis." },
  { path: "unified-intelligence", label: "Unified Dashboard", icon: HeartPulse, desc: "Enterprise intelligence hub with global health, scores, insights, knowledge graph, and cross-analyzer navigation." },
  { path: "risk-intelligence", label: "Project Risk Intelligence", icon: ShieldAlert, desc: "Enterprise risk scoring, heatmaps, AI summaries, and prioritized recommendations." },
  { path: "security-intelligence", label: "Security Intelligence", icon: Shield, desc: "Security vulnerability detection, dependency auditing, and configuration analysis." },
  { path: "performance-intelligence", label: "Performance Intelligence", icon: Zap, desc: "Identify bottlenecks, optimize execution paths, and improve runtime efficiency." },
  { path: "maintainability-intelligence", label: "Maintainability Intelligence", icon: Wrench, desc: "Code smell detection, technical debt estimation, refactoring opportunities, and module health analysis." },
  { path: "refactoring-intelligence", label: "AI Refactoring Intelligence", icon: GitCompare, desc: "Structural improvement detection, refactoring opportunities, impact analysis, and prioritized roadmap." },
  { path: "documentation-intelligence", label: "Documentation Intelligence", icon: BookOpen, desc: "Documentation quality analysis, coverage assessment, and prioritized recommendations." },
  { path: "test-intelligence", label: "Test Intelligence", icon: FlaskConical, desc: "Test coverage analysis, quality metrics, framework detection, and gap identification." },
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
  const { projectId } = useParams<{ projectId: string }>();
  const [depData, setDepData] = useState<ImportDependencyResponse | null>(null);
  const [depLoading, setDepLoading] = useState(false);
  const depFetchedRef = useRef(false);

  const [codeQualityData, setCodeQualityData] = useState<CodeQualityResponse | null>(null);
  const [codeQualityLoading, setCodeQualityLoading] = useState(false);
  const codeQualityFetchedRef = useRef(false);

  const [fileAnalysisData, setFileAnalysisData] = useState<FileAnalysisResponse | null>(null);
  const [fileAnalysisLoading, setFileAnalysisLoading] = useState(false);
  const fileAnalysisFetchedRef = useRef(false);

  const [funcClassData, setFuncClassData] = useState<FunctionClassResponse | null>(null);
  const [funcClassLoading, setFuncClassLoading] = useState(false);
  const funcClassFetchedRef = useRef(false);

  const [semanticData, setSemanticData] = useState<SemanticResponse | null>(null);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const semanticFetchedRef = useRef(false);

  useEffect(() => {
    if (!projectId || semanticFetchedRef.current) return;
    setSemanticLoading(true);
    getSemanticIntelligence(Number(projectId))
      .then(setSemanticData)
      .catch(() => {})
      .finally(() => { setSemanticLoading(false); semanticFetchedRef.current = true; });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || depFetchedRef.current) return;
    setDepLoading(true);
    getImportDependencyAnalysis(Number(projectId))
      .then(setDepData)
      .catch(() => {})
      .finally(() => { setDepLoading(false); depFetchedRef.current = true; });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || codeQualityFetchedRef.current) return;
    setCodeQualityLoading(true);
    getCodeQuality(Number(projectId))
      .then(setCodeQualityData)
      .catch(() => {})
      .finally(() => { setCodeQualityLoading(false); codeQualityFetchedRef.current = true; });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || fileAnalysisFetchedRef.current) return;
    setFileAnalysisLoading(true);
    getFileAnalysis(Number(projectId))
      .then(setFileAnalysisData)
      .catch(() => {})
      .finally(() => { setFileAnalysisLoading(false); fileAnalysisFetchedRef.current = true; });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || funcClassFetchedRef.current) return;
    setFuncClassLoading(true);
    getFunctionClassAnalysis(Number(projectId))
      .then(setFuncClassData)
      .catch(() => {})
      .finally(() => { setFuncClassLoading(false); funcClassFetchedRef.current = true; });
  }, [projectId]);

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
      <motion.div variants={itemVariants} className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
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
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Dependency Health</p>
          <p className="mt-1 text-sm font-semibold text-[#111827]">
            {depData
              ? depData.metrics.coupling_score <= 25 ? "Good"
                : depData.metrics.coupling_score <= 50 ? "Moderate"
                : "Poor"
              : "—"}
          </p>
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
              {cat.path === "code-intelligence" && analysis.codeIntel && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{analysis.codeIntel.summary.total_files} files</span>
                  <span className="rounded bg-[#ECFDF5] px-2 py-0.5 text-[9px] font-medium text-[#065F46]">{(analysis.codeIntel.summary.average_lines_of_code * analysis.codeIntel.summary.total_files).toLocaleString()} lines</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{analysis.codeIntel.summary.average_complexity.toFixed(1)} complexity</span>
                  <span className="rounded bg-[#FFFBEB] px-2 py-0.5 text-[9px] font-medium text-[#92400E]">{analysis.codeIntel.summary.average_maintainability.toFixed(0)} maint.</span>
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{analysis.codeIntel.summary.total_classes} classes</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{analysis.codeIntel.summary.total_functions} functions</span>
                </div>
              )}
              {cat.path === "code-intelligence" && !analysis.codeIntel && (
                <p className="mt-2 text-[10px] italic text-[#9CA3AF]">Code intelligence not available.</p>
              )}
              {cat.path === "code-quality" && codeQualityData && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{codeQualityData.overall_score.score}% score</span>
                  <span className="rounded bg-[#FEF2F2] px-2 py-0.5 text-[9px] font-medium text-[#991B1B]">{codeQualityData.severity_counts.critical} critical</span>
                  <span className="rounded bg-[#FFF7ED] px-2 py-0.5 text-[9px] font-medium text-[#9A3412]">{codeQualityData.severity_counts.high} high</span>
                  <span className="rounded bg-[#FFFBEB] px-2 py-0.5 text-[9px] font-medium text-[#92400E]">{codeQualityData.severity_counts.medium} medium</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{codeQualityData.severity_counts.low} low</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{codeQualityData.total_issues} smells</span>
                </div>
              )}
              {cat.path === "code-quality" && !codeQualityData && !codeQualityLoading && (
                <p className="mt-2 text-[10px] italic text-[#9CA3AF]">Code quality not available.</p>
              )}
              {cat.path === "file-analysis" && fileAnalysisData && fileAnalysisData.files.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{fileAnalysisData.total_files} total</span>
                  <span className="rounded bg-[#ECFDF5] px-2 py-0.5 text-[9px] font-medium text-[#065F46]">{formatSize(Math.max(...fileAnalysisData.files.map(f => f.size)))} largest</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{formatSize(Math.min(...fileAnalysisData.files.map(f => f.size)))} smallest</span>
                  <span className="rounded bg-[#FFFBEB] px-2 py-0.5 text-[9px] font-medium text-[#92400E]">{formatSize(fileAnalysisData.files.reduce((s, f) => s + f.size, 0) / fileAnalysisData.total_files)} avg</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{analysis.codeIntel?.summary.total_duplicate_files ?? 0} duplicates</span>
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{(fileAnalysisData.files.reduce((s, f) => s + f.scores.overall, 0) / fileAnalysisData.total_files).toFixed(0)}% health</span>
                </div>
              )}
              {cat.path === "file-analysis" && !fileAnalysisData && !fileAnalysisLoading && (
                <p className="mt-2 text-[10px] italic text-[#9CA3AF]">File analysis not available.</p>
              )}
              {cat.path === "function-class" && funcClassData && funcClassData.functions.length > 0 && funcClassData.classes.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{funcClassData.stats.total_functions} functions</span>
                  <span className="rounded bg-[#ECFDF5] px-2 py-0.5 text-[9px] font-medium text-[#065F46]">{funcClassData.stats.total_classes} classes</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{Math.max(...funcClassData.functions.map(f => f.lines_of_code))} largest fn</span>
                  <span className="rounded bg-[#FFFBEB] px-2 py-0.5 text-[9px] font-medium text-[#92400E]">{Math.max(...funcClassData.classes.map(c => c.lines_of_code))} longest cls</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{Math.round(funcClassData.functions.reduce((s, f) => s + f.lines_of_code, 0) / funcClassData.stats.total_functions)} avg fn len</span>
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{Math.round(funcClassData.classes.reduce((s, c) => s + c.lines_of_code, 0) / funcClassData.stats.total_classes)} avg cls size</span>
                </div>
              )}
              {cat.path === "function-class" && !funcClassData && !funcClassLoading && (
                <p className="mt-2 text-[10px] italic text-[#9CA3AF]">Function & class analysis not available.</p>
              )}
              {cat.path === "dependencies" && depData && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{depData.metrics.internal_libraries} internal</span>
                  <span className="rounded bg-[#ECFDF5] px-2 py-0.5 text-[9px] font-medium text-[#065F46]">{depData.metrics.external_libraries} external</span>
                  <span className="rounded bg-[#FFF7ED] px-2 py-0.5 text-[9px] font-medium text-[#9A3412]">{depData.metrics.broken_dependencies} broken</span>
                  <span className="rounded bg-[#FEF2F2] px-2 py-0.5 text-[9px] font-medium text-[#991B1B]">{depData.metrics.circular_dependencies} circular</span>
                  <span className="rounded bg-[#FEF2F2] px-2 py-0.5 text-[9px] font-medium text-[#991B1B]">{depData.metrics.unused_imports} unused</span>
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">{depData.metrics.coupling_score <= 25 ? "Good" : depData.metrics.coupling_score <= 50 ? "Moderate" : depData.metrics.coupling_score <= 75 ? "Fair" : "Poor"} health</span>
                </div>
              )}
              {cat.path === "dependencies" && !depData && !depLoading && (
                <p className="mt-2 text-[10px] italic text-[#9CA3AF]">Dependency analysis not available.</p>
              )}
              {cat.path === "semantic-intelligence" && semanticData && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[9px] font-medium text-[#1E40AF]">{semanticData.stats.total_components} components</span>
                  <span className="rounded bg-[#ECFDF5] px-2 py-0.5 text-[9px] font-medium text-[#065F46]">{semanticData.stats.total_business_flows} flows</span>
                  {semanticData.understanding_score && (
                    <span className={`rounded px-2 py-0.5 text-[9px] font-medium ${
                      semanticData.understanding_score.overall >= 70 ? "bg-[#ECFDF5] text-[#065F46]"
                      : semanticData.understanding_score.overall >= 40 ? "bg-[#FFFBEB] text-[#92400E]"
                      : "bg-[#FEF2F2] text-[#991B1B]"
                    }`}>
                      {semanticData.understanding_score.overall}% score
                    </span>
                  )}
                  {semanticData.knowledge_graph && (
                    <span className="rounded bg-[#F5F3FF] px-2 py-0.5 text-[9px] font-medium text-[#5B21B6]">
                      {semanticData.knowledge_graph.nodes.length} KG nodes
                    </span>
                  )}
                  <span className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#374151]">
                    {semanticData.stats.total_relationships} relationships
                  </span>
                  <span className="rounded bg-[#FFFBEB] px-2 py-0.5 text-[9px] font-medium text-[#92400E]">
                    {semanticData.business_components.length} business components
                  </span>
                </div>
              )}
              {cat.path === "semantic-intelligence" && !semanticData && !semanticLoading && (
                <p className="mt-2 text-[10px] italic text-[#9CA3AF]">Semantic intelligence not available.</p>
              )}
            </div>
          );
        })}
      </motion.div>

      {/* Quick Stats Footer */}
      <motion.div variants={itemVariants} className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Summary</p>
        <p className="mt-1 text-sm leading-relaxed text-[#374151]">{data.workspace_summary}</p>
        {depData && (
          <div className="mt-2 space-y-0.5 text-xs text-[#374151]">
            <p>Detected {depData.metrics.internal_libraries} internal modules and {depData.metrics.external_libraries} external libraries.</p>
            <p>Detected {depData.metrics.total_imports} import statements across {depData.metrics.total_files} files.</p>
            {depData.metrics.circular_dependencies === 0
              ? <p>No circular dependencies detected.</p>
              : <p>{depData.metrics.circular_dependencies} circular dependenc{depData.metrics.circular_dependencies === 1 ? "y" : "ies"} detected.</p>}
            {depData.metrics.unused_imports > 0 && (
              <p>Unused imports found in {depData.metrics.unused_imports} location{depData.metrics.unused_imports === 1 ? "" : "s"}.</p>
            )}
            <p>Dependency health is {depData.metrics.coupling_score <= 25 ? "Excellent" : depData.metrics.coupling_score <= 50 ? "Good" : depData.metrics.coupling_score <= 75 ? "Moderate" : "Poor"}.</p>
          </div>
        )}
      </motion.div>

      {/* Smart Insights */}
      <motion.div variants={itemVariants} className="rounded-xl border border-[#E5E7EB] bg-white p-5">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Smart Insights</p>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {(() => {
            const insights: { icon: string; label: string; value: string; color: string }[] = [];

            const codeIntelSummary = analysis.codeIntel?.summary;
            if (codeIntelSummary) {
              insights.push({
                icon: "FILE",
                label: "Source Files",
                value: `${codeIntelSummary.total_files} files · ${(codeIntelSummary.average_lines_of_code * codeIntelSummary.total_files).toLocaleString()} LOC`,
                color: "text-[#2563EB]",
              });
              if (codeIntelSummary.total_duplicate_files > 0) {
                insights.push({
                  icon: "DUP",
                  label: "Duplicate Files",
                  value: `${codeIntelSummary.total_duplicate_files} duplicate${codeIntelSummary.total_duplicate_files > 1 ? "s" : ""} detected`,
                  color: "text-[#D97706]",
                });
              }
            }

            if (funcClassData) {
              const s = funcClassData.stats;
              if (funcClassData.functions.length > 0) {
                const maxFnLoc = Math.max(...funcClassData.functions.map(f => f.lines_of_code));
                const largestFn = funcClassData.functions.find(f => f.lines_of_code === maxFnLoc);
                insights.push({
                  icon: "FN",
                  label: "Largest Function",
                  value: `${maxFnLoc} LOC in ${largestFn?.name ?? "unknown"}`,
                  color: "text-[#7C3AED]",
                });
              } else {
                insights.push({ icon: "FN", label: "Largest Function", value: "No functions detected", color: "text-[#7C3AED]" });
              }
              if (funcClassData.classes.length > 0) {
                const maxClsLoc = Math.max(...funcClassData.classes.map(c => c.lines_of_code));
                const largestCls = funcClassData.classes.find(c => c.lines_of_code === maxClsLoc);
                insights.push({
                  icon: "CLS",
                  label: "Largest Class",
                  value: `${maxClsLoc} LOC in ${largestCls?.name ?? "unknown"}`,
                  color: "text-[#059669]",
                });
              } else {
                insights.push({ icon: "CLS", label: "Largest Class", value: "No classes detected", color: "text-[#059669]" });
              }
              if (s.average_complexity > 10) {
                insights.push({
                  icon: "CPX",
                  label: "High Avg Complexity",
                  value: `${s.average_complexity.toFixed(1)} average cyclomatic complexity across ${s.total_functions} functions`,
                  color: "text-[#DC2626]",
                });
              }
            }

            if (depData) {
              const m = depData.metrics;
              if (m.circular_dependencies > 0) {
                insights.push({
                  icon: "CIR",
                  label: "Circular Dependencies",
                  value: `${m.circular_dependencies} circular dependenc${m.circular_dependencies > 1 ? "ies" : "y"} detected across ${m.total_files} files`,
                  color: "text-[#DC2626]",
                });
              }
              if (m.broken_dependencies > 0) {
                insights.push({
                  icon: "BRK",
                  label: "Broken Imports",
                  value: `${m.broken_dependencies} broken import${m.broken_dependencies > 1 ? "s" : ""} found`,
                  color: "text-[#EA580C]",
                });
              }
              if (m.unused_imports > 0) {
                insights.push({
                  icon: "UNU",
                  label: "Unused Imports",
                  value: `${m.unused_imports} unused import${m.unused_imports > 1 ? "s" : ""} found across ${m.total_files} files`,
                  color: "text-[#D97706]",
                });
              }
              if (m.coupling_score > 50) {
                insights.push({
                  icon: "CPL",
                  label: "High Coupling",
                  value: `${m.coupling_score}% coupling score indicates tight module interdependence`,
                  color: "text-[#DC2626]",
                });
              }
            }

            const qualityScore = codeQualityData?.overall_score.score;
            if (qualityScore !== undefined) {
              if (qualityScore < 60) {
                insights.push({
                  icon: "QLT",
                  label: "Low Quality Score",
                  value: `${qualityScore}% overall quality score — significant improvements needed`,
                  color: "text-[#DC2626]",
                });
              } else if (qualityScore >= 80) {
                insights.push({
                  icon: "QLT",
                  label: "High Quality Score",
                  value: `${qualityScore}% overall quality score — project is in good shape`,
                  color: "text-[#059669]",
                });
              }
              const critCount = codeQualityData?.severity_counts.critical ?? 0;
              if (critCount > 0) {
                insights.push({
                  icon: "CRT",
                  label: "Critical Issues",
                  value: `${critCount} critical issue${critCount > 1 ? "s" : ""} requiring immediate attention`,
                  color: "text-[#DC2626]",
                });
              }
            }

            return insights.length > 0 ? insights.map((ins, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3">
                <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[#EFF6FF] ${ins.color}`}>
                  <span className="text-[9px] font-bold">{ins.icon}</span>
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-[#111827]">{ins.label}</p>
                  <p className="mt-0.5 text-[10px] text-[#6B7280]">{ins.value}</p>
                </div>
              </div>
            )) : (
              <p className="col-span-full text-sm text-[#6B7280]">Run project analysis to generate insights.</p>
            );
          })()}
        </div>
      </motion.div>

    </motion.div>
  );
}
