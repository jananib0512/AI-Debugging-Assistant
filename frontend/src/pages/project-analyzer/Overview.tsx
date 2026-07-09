import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  FileText,
  FunctionSquare,
  Box,
  RefreshCw,
} from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";
import {
  getCodeQuality,
  getFileAnalysis,
  getFunctionClassAnalysis,
  getProductionReadiness,
  getAiEngineeringReadiness,
} from "@/lib/project-analyzer";
import type {
  CodeQualityResponse,
  FileAnalysisResponse,
  FunctionClassResponse,
  ProductionReadinessResponse,
  AiEngineeringReadinessResponse,
} from "@/types/project-analyzer";
import { Card, CardContent } from "@/components/ui/card";

function formatSize(bytes: number) {
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + " GB";
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
  if (bytes >= 1024) return (bytes / 1024).toFixed(0) + " KB";
  return bytes + " B";
}

function scoreColor(score: number) {
  if (score >= 80) return "text-[#059669]";
  if (score >= 60) return "text-[#D97706]";
  if (score >= 40) return "text-[#EA580C]";
  return "text-[#DC2626]";
}

function scoreBg(score: number) {
  if (score >= 80) return "bg-[#ECFDF5] text-[#065F46]";
  if (score >= 60) return "bg-[#FFFBEB] text-[#92400E]";
  if (score >= 40) return "bg-[#FFF7ED] text-[#9A3412]";
  return "bg-[#FEF2F2] text-[#991B1B]";
}

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

  const [showAllFiles, setShowAllFiles] = useState(false);
  const [showAllFunctions, setShowAllFunctions] = useState(false);
  const [showAllClasses, setShowAllClasses] = useState(false);
  const [showAdvancedDetails, setShowAdvancedDetails] = useState(false);

  const [codeQualityData, setCodeQualityData] = useState<CodeQualityResponse | null>(null);
  const codeQualityFetchedRef = useRef(false);

  const [fileAnalysisData, setFileAnalysisData] = useState<FileAnalysisResponse | null>(null);
  const fileAnalysisFetchedRef = useRef(false);

  const [funcClassData, setFuncClassData] = useState<FunctionClassResponse | null>(null);
  const funcClassFetchedRef = useRef(false);

  const [productionData, setProductionData] = useState<ProductionReadinessResponse | null>(null);
  const productionFetchedRef = useRef(false);

  const [aiEngData, setAiEngData] = useState<AiEngineeringReadinessResponse | null>(null);
  const aiEngFetchedRef = useRef(false);

  useEffect(() => {
    if (!projectId || codeQualityFetchedRef.current) return;
    getCodeQuality(Number(projectId))
      .then(setCodeQualityData)
      .catch(() => {})
      .finally(() => { codeQualityFetchedRef.current = true; });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || fileAnalysisFetchedRef.current) return;
    getFileAnalysis(Number(projectId))
      .then(setFileAnalysisData)
      .catch(() => {})
      .finally(() => { fileAnalysisFetchedRef.current = true; });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || funcClassFetchedRef.current) return;
    getFunctionClassAnalysis(Number(projectId))
      .then(setFuncClassData)
      .catch(() => {})
      .finally(() => { funcClassFetchedRef.current = true; });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || productionFetchedRef.current) return;
    getProductionReadiness(Number(projectId))
      .then(setProductionData)
      .catch(() => {})
      .finally(() => { productionFetchedRef.current = true; });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || aiEngFetchedRef.current) return;
    getAiEngineeringReadiness(Number(projectId))
      .then(setAiEngData)
      .catch(() => {})
      .finally(() => { aiEngFetchedRef.current = true; });
  }, [projectId]);

  const healthScore = analysis.projectInsights?.health_score?.score ?? null;
  const tech = data?.technology_stack;
  const fw = analysis.frameworks?.primary_framework;
  const arch = analysis.architecture?.primary_architecture;
  const mods = analysis.modules?.summary;
  const qualityScore = codeQualityData?.overall_score.score ?? null;
  const productionScore = productionData?.production_score.overall_production_score ?? null;
  const aiEngScore = aiEngData?.engineering_score.overall_engineering_score ?? null;

  const files = fileAnalysisData?.files ?? [];
  const functions = funcClassData?.functions ?? [];
  const classes = funcClassData?.classes ?? [];
  const displayedFiles = showAllFiles ? files : files.slice(0, 10);
  const displayedFunctions = showAllFunctions ? functions : functions.slice(0, 10);
  const displayedClasses = showAllClasses ? classes : classes.slice(0, 10);

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="relative mb-4">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
          </div>
          <p className="text-sm font-medium text-[#111827]">Analyzing project...</p>
          <p className="mt-1 text-xs text-[#6B7280]">Gathering project information.</p>
        </div>
      )}

      {error && (
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
      )}

      {!loading && !error && !data && (
        <div className="flex flex-col items-center justify-center py-20">
          <p className="text-sm font-medium text-[#111827]">No analysis data</p>
          <p className="mt-1 text-xs text-[#6B7280]">Upload and extract a project to begin analysis.</p>
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* Header */}
          <motion.div variants={itemVariants} className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-[#111827]">{data.project_name}</h1>
              <div className="mt-1 flex flex-wrap gap-2">
                <span className="inline-flex items-center rounded-full bg-[#F3F4F6] px-2.5 py-0.5 text-xs font-medium text-[#374151] capitalize">
                  {data.project_type}
                </span>
                <span className="inline-flex items-center rounded-full bg-[#EFF6FF] px-2.5 py-0.5 text-xs font-medium text-[#2563EB]">
                  {data.total_files} files
                </span>
                <span className="inline-flex items-center rounded-full bg-[#F3F4F6] px-2.5 py-0.5 text-xs font-medium text-[#374151]">
                  {data.total_folders} folders
                </span>
                <span className="inline-flex items-center rounded-full bg-[#F3F4F6] px-2.5 py-0.5 text-xs font-medium text-[#374151]">
                  {formatSize(data.workspace_size)}
                </span>
              </div>
            </div>
            <button
              onClick={() => refresh(true)}
              disabled={analyzing}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs font-medium text-[#374151] transition-colors hover:bg-[#F9FAFB] disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${analyzing ? "animate-spin" : ""}`} />
              {analyzing ? "Refreshing..." : "Refresh"}
            </button>
          </motion.div>

          {/* AI Summary */}
          <motion.div variants={itemVariants}>
            <Card hover={false}>
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF] mb-2">Analysis Summary</p>
                <p className="text-sm leading-relaxed text-[#374151]">
                  {data.workspace_summary}
                  {fw?.name && ` A ${fw.name} frontend was detected.`}
                  {tech?.languages?.length && ` The project uses ${tech.languages.join(", ")}.`}
                  {healthScore !== null && healthScore >= 70
                    ? " The project is healthy and ready for AI Bug Detection."
                    : healthScore !== null && healthScore >= 40
                    ? " The project has some areas needing attention before AI Bug Detection."
                    : healthScore !== null
                    ? " The project needs significant improvements before AI Bug Detection."
                    : ""}
                </p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Health Cards */}
          <motion.div variants={itemVariants} className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Health</p>
                <p className={`mt-1 text-lg font-bold ${healthScore !== null ? scoreColor(healthScore) : "text-[#9CA3AF]"}`}>
                  {healthScore !== null ? `${healthScore}%` : "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Code Quality</p>
                <p className={`mt-1 text-lg font-bold ${qualityScore !== null ? scoreColor(qualityScore) : "text-[#9CA3AF]"}`}>
                  {qualityScore !== null ? `${qualityScore}%` : "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Security</p>
                <p className={`mt-1 text-lg font-bold ${qualityScore !== null ? (qualityScore >= 70 ? "text-[#059669]" : qualityScore >= 40 ? "text-[#D97706]" : "text-[#DC2626]") : "text-[#9CA3AF]"}`}>
                  {qualityScore !== null ? (qualityScore >= 70 ? "Good" : qualityScore >= 40 ? "Fair" : "Needs Work") : "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Performance</p>
                <p className={`mt-1 text-lg font-bold ${qualityScore !== null ? (qualityScore >= 70 ? "text-[#059669]" : qualityScore >= 40 ? "text-[#D97706]" : "text-[#DC2626]") : "text-[#9CA3AF]"}`}>
                  {qualityScore !== null ? (qualityScore >= 70 ? "Good" : qualityScore >= 40 ? "Fair" : "Needs Work") : "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Production Readiness</p>
                <p className={`mt-1 text-lg font-bold ${productionScore !== null ? scoreColor(productionScore) : "text-[#9CA3AF]"}`}>
                  {productionScore !== null ? `${productionScore}%` : "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Risk Level</p>
                <p className={`mt-1 text-lg font-bold ${qualityScore !== null ? (qualityScore >= 70 ? "text-[#059669]" : qualityScore >= 40 ? "text-[#D97706]" : "text-[#DC2626]") : "text-[#9CA3AF]"}`}>
                  {qualityScore !== null ? (qualityScore >= 70 ? "Low" : qualityScore >= 40 ? "Medium" : "High") : "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Maintainability</p>
                <p className={`mt-1 text-lg font-bold ${qualityScore !== null ? (qualityScore >= 70 ? "text-[#059669]" : qualityScore >= 40 ? "text-[#D97706]" : "text-[#DC2626]") : "text-[#9CA3AF]"}`}>
                  {qualityScore !== null ? (qualityScore >= 70 ? "Good" : qualityScore >= 40 ? "Fair" : "Needs Work") : "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Testing</p>
                <p className={`mt-1 text-lg font-bold ${qualityScore !== null ? (qualityScore >= 70 ? "text-[#059669]" : qualityScore >= 40 ? "text-[#D97706]" : "text-[#DC2626]") : "text-[#9CA3AF]"}`}>
                  {qualityScore !== null ? (qualityScore >= 70 ? "Good" : qualityScore >= 40 ? "Fair" : "Needs Work") : "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">AI Confidence</p>
                <p className={`mt-1 text-lg font-bold ${aiEngScore !== null ? scoreColor(aiEngScore) : "text-[#9CA3AF]"}`}>
                  {aiEngScore !== null ? `${aiEngScore}%` : "—"}
                </p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Project Information Cards */}
          <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Type</p>
                <p className="mt-1 text-sm font-semibold text-[#111827] capitalize">{data.project_type}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Frontend</p>
                <p className="mt-1 text-sm font-semibold text-[#111827]">{fw?.name || "—"}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Backend</p>
                <p className="mt-1 text-sm font-semibold text-[#111827]">{tech?.languages?.length ? tech.languages[0] : "—"}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Architecture</p>
                <p className="mt-1 text-sm font-semibold text-[#111827]">{arch?.architecture || "—"}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Languages</p>
                <p className="mt-1 text-sm font-semibold text-[#111827]">{tech?.languages?.length ? tech.languages.join(", ") : "—"}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Database</p>
                <p className="mt-1 text-sm font-semibold text-[#111827]">{tech?.databases?.length ? tech.databases.join(", ") : "—"}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Files</p>
                <p className="mt-1 text-sm font-semibold text-[#111827]">{data.total_files}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Modules</p>
                <p className="mt-1 text-sm font-semibold text-[#111827]">{mods?.detected_count ?? "—"}/{mods?.total_modules ?? "—"}</p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Top 10 Files */}
          {files.length > 0 && (
            <motion.div variants={itemVariants}>
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Files <span className="text-[#6B7280]">(Top {showAllFiles ? files.length : 10} of {files.length})</span></p>
                    {files.length > 10 && (
                      <button
                        onClick={() => setShowAllFiles(!showAllFiles)}
                        className="inline-flex items-center gap-1 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]"
                      >
                        {showAllFiles ? "Show Less" : "View All Files"}
                        {showAllFiles ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      </button>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    {displayedFiles.map((file, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <FileText className="h-3.5 w-3.5 shrink-0 text-[#6B7280]" />
                          <span className="truncate text-xs font-medium text-[#374151]">{file.file_name}</span>
                        </div>
                        <div className="flex items-center gap-3 shrink-0 ml-3">
                          <span className="text-[10px] text-[#6B7280]">{formatSize(file.size)}</span>
                          <span className={`text-[10px] font-medium ${scoreBg(file.scores.overall)}`}>{file.scores.overall}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Top 10 Functions & Classes */}
          {(functions.length > 0 || classes.length > 0) && (
            <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2">
              {functions.length > 0 && (
                <Card>
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Functions <span className="text-[#6B7280]">(Top {showAllFunctions ? functions.length : 10} of {functions.length})</span></p>
                      {functions.length > 10 && (
                        <button
                          onClick={() => setShowAllFunctions(!showAllFunctions)}
                          className="inline-flex items-center gap-1 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]"
                        >
                          {showAllFunctions ? "Show Less" : "View All"}
                          {showAllFunctions ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                        </button>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      {displayedFunctions.map((fn, i) => (
                        <div key={i} className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                          <div className="flex items-center gap-2 min-w-0">
                            <FunctionSquare className="h-3.5 w-3.5 shrink-0 text-[#6B7280]" />
                            <span className="truncate text-xs font-medium text-[#374151]">{fn.name}</span>
                          </div>
                          <span className="shrink-0 ml-3 text-[10px] text-[#6B7280]">{fn.lines_of_code} LOC</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
              {classes.length > 0 && (
                <Card>
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Classes <span className="text-[#6B7280]">(Top {showAllClasses ? classes.length : 10} of {classes.length})</span></p>
                      {classes.length > 10 && (
                        <button
                          onClick={() => setShowAllClasses(!showAllClasses)}
                          className="inline-flex items-center gap-1 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]"
                        >
                          {showAllClasses ? "Show Less" : "View All"}
                          {showAllClasses ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                        </button>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      {displayedClasses.map((cls, i) => (
                        <div key={i} className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                          <div className="flex items-center gap-2 min-w-0">
                            <Box className="h-3.5 w-3.5 shrink-0 text-[#6B7280]" />
                            <span className="truncate text-xs font-medium text-[#374151]">{cls.name}</span>
                          </div>
                          <span className="shrink-0 ml-3 text-[10px] text-[#6B7280]">{cls.lines_of_code} LOC</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </motion.div>
          )}

          {/* Advanced Details Section (hidden behind toggle) */}
          <motion.div variants={itemVariants}>
            <Card hover={false}>
              <CardContent className="p-4">
                <button
                  onClick={() => setShowAdvancedDetails(!showAdvancedDetails)}
                  className="flex w-full items-center justify-between"
                >
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Advanced Details</span>
                  {showAdvancedDetails ? <ChevronUp className="h-4 w-4 text-[#6B7280]" /> : <ChevronDown className="h-4 w-4 text-[#6B7280]" />}
                </button>
                {showAdvancedDetails && (
                  <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <button
                      onClick={() => navigate("framework")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Framework Details <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("technology")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Technology Stack <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("modules")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Project Structure <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("dependencies")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Dependencies <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("code-quality")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Code Quality <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("file-analysis")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      File Analysis <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("function-class")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Functions & Classes <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("architecture")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Architecture <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("risk-intelligence")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Project Risks <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("security-intelligence")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Security <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("performance-intelligence")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Performance <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("maintainability-intelligence")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Maintainability <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("documentation-intelligence")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Documentation <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("test-intelligence")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Testing <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("production-readiness")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Production Readiness <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("recommendations")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Recommendations <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("call-graph")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Call Graph <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("semantic-intelligence")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Semantic Analysis <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("unified-intelligence")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      Unified Dashboard <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                    <button
                      onClick={() => navigate("ai-engineering-readiness")}
                      className="flex items-center justify-between rounded-lg border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 text-left text-xs font-medium text-[#374151] hover:border-[#2563EB] transition-colors"
                    >
                      AI Readiness <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
                    </button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Next Step Navigation */}
          <motion.div variants={itemVariants} className="flex items-center justify-between pt-2">
            <button
              onClick={() => navigate(`/projects/${projectId}/overview`)}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-[#6B7280] hover:text-[#111827] transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous: Overview
            </button>
            <button
              onClick={() => navigate(`/projects/${projectId}/bug-detection`)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-[#2563EB] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
            >
              Next: AI Bug Detection
              <ChevronRight className="h-4 w-4" />
            </button>
          </motion.div>
        </>
      )}
    </motion.div>
  );
}
