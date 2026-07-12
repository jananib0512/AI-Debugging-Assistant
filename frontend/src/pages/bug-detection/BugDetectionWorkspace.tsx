import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Bug,
  CheckCircle,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Clock,
  FileCode,
  Play,
  RefreshCw,
} from "lucide-react";
import { getBugDetectionWorkspace, getSyntaxDetection, getStaticCodeAnalysis, getDependencyAnalysis, getRuntimeAnalysis, getSecurityAnalysis, getPerformanceAnalysis, getArchitectureAnalysis, getBugPrioritization } from "@/lib/project-analyzer";
import type { BugDetectionWorkspaceResponse, SyntaxDetectionResponse, StaticCodeAnalysisResponse, DependencyAnalysisResponse, RuntimeAnalysisResponse, SecurityAnalysisResponse, PerformanceAnalysisResponse, ArchitectureAnalysisResponse, PrioritizationResponse, SyntaxErrorInfo, ArchitectureIssueInfo } from "@/types/project-analyzer";
import { enhanceArchitectureBug, getModuleFromPath, getBusinessImpact, getArchitectureImpact } from "@/lib/architecture-logic-detector";
import { Card, CardContent } from "@/components/ui/card";
import { BugSummaryPanel } from "./BugSummaryPanel";
import { getWorkflowNavigation } from "@/lib/workflow-navigation";

const SEVERITY_ORDER: Record<string, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };

const severityBadge = (s: string) => {
  switch (s) {
    case "Critical": return "text-white bg-[#DC2626]";
    case "High": return "text-white bg-[#EA580C]";
    case "Medium": return "text-[#111827] bg-[#F59E0B]";
    default: return "text-[#111827] bg-[#F3F4F6]";
  }
};

interface BugCategory {
  id: string;
  name: string;
  status: "completed" | "pending";
  bugs: SyntaxErrorInfo[];
  critical: number;
  high: number;
  medium: number;
  low: number;
  total: number;
}

const PENDING_MODULES: Omit<BugCategory, "bugs">[] = [
  { id: "dependency", name: "Dependency Issues", status: "pending", critical: 0, high: 0, medium: 0, low: 0, total: 0 },
  { id: "runtime", name: "Runtime Issues", status: "pending", critical: 0, high: 0, medium: 0, low: 0, total: 0 },
  { id: "security", name: "Security Issues", status: "pending", critical: 0, high: 0, medium: 0, low: 0, total: 0 },
  { id: "performance", name: "Performance Issues", status: "pending", critical: 0, high: 0, medium: 0, low: 0, total: 0 },
  { id: "architecture", name: "Architecture & Logic Issues", status: "pending", critical: 0, high: 0, medium: 0, low: 0, total: 0 },
];

type DetectionState = "idle" | "running" | "completed";

export function BugDetectionWorkspace() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [wsData, setWsData] = useState<BugDetectionWorkspaceResponse | null>(null);
  const [syntaxData, setSyntaxData] = useState<SyntaxDetectionResponse | null>(null);
  const [staticData, setStaticData] = useState<StaticCodeAnalysisResponse | null>(null);
  const [dependencyData, setDependencyData] = useState<DependencyAnalysisResponse | null>(null);
  const [runtimeData, setRuntimeData] = useState<RuntimeAnalysisResponse | null>(null);
  const [securityData, setSecurityData] = useState<SecurityAnalysisResponse | null>(null);
  const [performanceData, setPerformanceData] = useState<PerformanceAnalysisResponse | null>(null);
  const [architectureData, setArchitectureData] = useState<ArchitectureAnalysisResponse | null>(null);
  const [prioritizationData, setPrioritizationData] = useState<PrioritizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detectionState, setDetectionState] = useState<DetectionState>("idle");
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);

  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [showAllCategory, setShowAllCategory] = useState<string | null>(null);
  const [selectedBug, setSelectedBug] = useState<SyntaxErrorInfo | null>(null);
  const fetchedRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const syntaxFetchedRef = useRef(false);
  const staticFetchedRef = useRef(false);
  const dependencyFetchedRef = useRef(false);
  const runtimeFetchedRef = useRef(false);
  const securityFetchedRef = useRef(false);
  const performanceFetchedRef = useRef(false);
  const architectureFetchedRef = useRef(false);
  const prioritizationFetchedRef = useRef(false);

  const fetchWsData = useCallback(() => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    getBugDetectionWorkspace(Number(projectId))
      .then((res) => { setWsData(res); fetchedRef.current = true; })
      .catch((err: unknown) => { setError(err instanceof Error ? err.message : "Failed to load workspace"); })
      .finally(() => setLoading(false));
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchWsData();
  }, [projectId, fetchWsData]);

  const fetchSyntaxData = useCallback(() => {
    if (!projectId || syntaxFetchedRef.current) return;
    getSyntaxDetection(Number(projectId))
      .then((res) => { setSyntaxData(res); syntaxFetchedRef.current = true; })
      .catch(() => {});
  }, [projectId]);

  const fetchStaticData = useCallback(() => {
    if (!projectId || staticFetchedRef.current) return;
    getStaticCodeAnalysis(Number(projectId))
      .then((res) => { setStaticData(res); staticFetchedRef.current = true; })
      .catch(() => {});
  }, [projectId]);

  const fetchDependencyData = useCallback(() => {
    if (!projectId || dependencyFetchedRef.current) return;
    getDependencyAnalysis(Number(projectId))
      .then((res) => { setDependencyData(res); dependencyFetchedRef.current = true; })
      .catch(() => {});
  }, [projectId]);

  const fetchRuntimeData = useCallback(() => {
    if (!projectId || runtimeFetchedRef.current) return;
    getRuntimeAnalysis(Number(projectId))
      .then((res) => { setRuntimeData(res); runtimeFetchedRef.current = true; })
      .catch(() => {});
  }, [projectId]);

  const fetchSecurityData = useCallback(() => {
    if (!projectId || securityFetchedRef.current) return;
    getSecurityAnalysis(Number(projectId))
      .then((res) => { setSecurityData(res); securityFetchedRef.current = true; })
      .catch(() => {});
  }, [projectId]);

  const fetchPerformanceData = useCallback(() => {
    if (!projectId || performanceFetchedRef.current) return;
    getPerformanceAnalysis(Number(projectId))
      .then((res) => { setPerformanceData(res); performanceFetchedRef.current = true; })
      .catch(() => {});
  }, [projectId]);

  const fetchArchitectureData = useCallback(() => {
    if (!projectId || architectureFetchedRef.current) return;
    getArchitectureAnalysis(Number(projectId))
      .then((res) => { setArchitectureData(res); architectureFetchedRef.current = true; })
      .catch(() => {});
  }, [projectId]);

  const fetchPrioritizationData = useCallback(() => {
    if (!projectId || prioritizationFetchedRef.current) return;
    getBugPrioritization(Number(projectId))
      .then((res) => { setPrioritizationData(res); prioritizationFetchedRef.current = true; })
      .catch(() => {});
  }, [projectId]);

  useEffect(() => {
    if (detectionState === "completed") {
      if (!syntaxFetchedRef.current) fetchSyntaxData();
      if (!staticFetchedRef.current) fetchStaticData();
      if (!dependencyFetchedRef.current) fetchDependencyData();
      if (!runtimeFetchedRef.current) fetchRuntimeData();
      if (!securityFetchedRef.current) fetchSecurityData();
      if (!performanceFetchedRef.current) fetchPerformanceData();
      if (!architectureFetchedRef.current) fetchArchitectureData();
      if (!prioritizationFetchedRef.current) fetchPrioritizationData();
    }
  }, [detectionState, fetchSyntaxData, fetchStaticData, fetchDependencyData, fetchRuntimeData, fetchSecurityData, fetchPerformanceData, fetchArchitectureData, fetchPrioritizationData]);

  useEffect(() => {
    if (detectionState !== "running") return;
    const moduleKeys = wsData?.detection_modules.map((m) => m.name) ?? [];
    let currentIdx = 0;
    timerRef.current = setInterval(() => {
      if (currentIdx >= moduleKeys.length) {
        if (timerRef.current) clearInterval(timerRef.current);
        setDetectionState("completed");
        setProgress(100);
        setCurrentStage(moduleKeys.length - 1);
        return;
      }
      setCurrentStage(currentIdx);
      setProgress(Math.round((currentIdx / moduleKeys.length) * 100));
      let elapsed = 0;
      const idx = currentIdx;
      const moduleTimer = setInterval(() => {
        elapsed += 100;
        if (elapsed >= 1400) {
          clearInterval(moduleTimer);
          setProgress(Math.round(((idx + 1) / moduleKeys.length) * 100));
          currentIdx++;
        }
      }, 100);
    }, 1600);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [detectionState, wsData]);

  const startDetection = () => {
    setDetectionState("running");
    setProgress(0);
    setCurrentStage(0);
    setSelectedBug(null);
  };

  // ── Architecture-specific derived data ──

  const architectureBugsAll = useMemo(() => {
    return (architectureData?.results.flatMap((r) => r.errors) ?? []) as ArchitectureIssueInfo[];
  }, [architectureData]);

  const enhancedArchitectureBugs = useMemo(() => {
    return architectureBugsAll.map(enhanceArchitectureBug);
  }, [architectureBugsAll]);

  // ── Build categories from data ──

  const categories = useMemo((): BugCategory[] => {
    const cats: BugCategory[] = [];
    const syntaxBugs = syntaxData?.results.flatMap((r) => r.errors) ?? [];
    const staticBugs = staticData?.results.flatMap((r) => r.errors) ?? [];
    const dependencyBugs = dependencyData?.results.flatMap((r) => r.errors) ?? [];
    const runtimeBugs = runtimeData?.results.flatMap((r) => r.errors) ?? [];
    const securityBugs = securityData?.results.flatMap((r) => r.errors) ?? [];
    const performanceBugs = performanceData?.results.flatMap((r) => r.errors) ?? [];
    const architectureBugs = enhancedArchitectureBugs;

    const sevCounts = (bugs: SyntaxErrorInfo[]) => ({
      critical: bugs.filter((b) => b.severity === "Critical").length,
      high: bugs.filter((b) => b.severity === "High").length,
      medium: bugs.filter((b) => b.severity === "Medium").length,
      low: bugs.filter((b) => b.severity === "Low").length,
    });

    const sc = sevCounts(syntaxBugs);
    cats.push({
      id: "syntax",
      name: "Syntax Errors",
      status: "completed",
      bugs: syntaxBugs,
      total: syntaxBugs.length,
      ...sc,
    });

    const stc = sevCounts(staticBugs);
    cats.push({
      id: "static",
      name: "Static Code Issues",
      status: "completed",
      bugs: staticBugs,
      total: staticBugs.length,
      ...stc,
    });

    const dc = sevCounts(dependencyBugs);
    cats.push({
      id: "dependency",
      name: "Dependency Issues",
      status: "completed",
      bugs: dependencyBugs,
      total: dependencyBugs.length,
      ...dc,
    });

    const rc = sevCounts(runtimeBugs);
    cats.push({
      id: "runtime",
      name: "Runtime Risks",
      status: "completed",
      bugs: runtimeBugs,
      total: runtimeBugs.length,
      ...rc,
    });

    const sec = sevCounts(securityBugs);
    cats.push({
      id: "security",
      name: "Security Issues",
      status: "completed",
      bugs: securityBugs,
      total: securityBugs.length,
      ...sec,
    });

    const pc = sevCounts(performanceBugs);
    cats.push({
      id: "performance",
      name: "Performance Issues",
      status: "completed",
      bugs: performanceBugs,
      total: performanceBugs.length,
      ...pc,
    });

    const ac = sevCounts(architectureBugs);
    cats.push({
      id: "architecture",
      name: "Architecture & Logic Issues",
      status: "completed",
      bugs: architectureBugs,
      total: architectureBugs.length,
      ...ac,
    });

    for (const m of PENDING_MODULES) {
      if (m.id === "dependency" || m.id === "runtime" || m.id === "security" || m.id === "performance" || m.id === "architecture") continue;
      cats.push({ ...m, bugs: [] });
    }

    return cats;
  }, [syntaxData, staticData, dependencyData, runtimeData, securityData, performanceData, architectureData, enhancedArchitectureBugs]);

  // ── Search + Filter ──

  const allBugs = useMemo(() => categories.flatMap((c) => c.bugs), [categories]);

  const filteredBugs = useMemo(() => {
    const bugs = [...allBugs];
    bugs.sort((a, b) => (SEVERITY_ORDER[b.severity] ?? 0) - (SEVERITY_ORDER[a.severity] ?? 0));
    return bugs;
  }, [allBugs]);

  const hasFilters = false;
  const isCompleted = detectionState === "completed";

  // ── Render ──

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative mb-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        </div>
        <p className="text-sm font-medium text-[#111827]">Preparing AI Bug Detection...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Loading project data.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Unable to load workspace</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button onClick={fetchWsData} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  if (!wsData) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Bug className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No project data available</p>
        <p className="mt-1 text-xs text-[#6B7280]">Upload and analyze a project to begin bug detection.</p>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto max-w-5xl space-y-8">

      {/* ── Header ── */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-[#111827]">AI Bug Detection</h1>
        <p className="mt-2 text-sm leading-relaxed text-[#6B7280]">
          The AI Software Engineer is now ready to inspect your uploaded project and detect software issues.
        </p>
      </div>

      {/* ── Project Summary ── */}
      <section>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Summary</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Card><CardContent className="p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Name</p>
            <p className="mt-1 text-sm font-semibold text-[#111827]">{wsData.project_name || "—"}</p>
          </CardContent></Card>
          <Card><CardContent className="p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Type</p>
            <p className="mt-1 text-sm font-semibold text-[#111827]">{wsData.project_type || "—"}</p>
          </CardContent></Card>
          <Card><CardContent className="p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Language</p>
            <p className="mt-1 text-sm font-semibold text-[#111827]">{wsData.language || "—"}</p>
          </CardContent></Card>
          <Card><CardContent className="p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Files</p>
            <p className="mt-1 text-sm font-semibold text-[#111827]">{wsData.total_files}</p>
          </CardContent></Card>
        </div>
      </section>

      {/* ── Detection Progress ── */}
      {!isCompleted && (
        <section>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Detection Progress</p>
          {detectionState === "idle" && (
            <Card hover={false}>
              <CardContent className="p-5 text-center">
                <p className="text-sm text-[#6B7280]">Click "Start AI Bug Detection" to begin inspecting your project.</p>
              </CardContent>
            </Card>
          )}
          {detectionState === "running" && (
            <Card hover={false}>
              <CardContent className="p-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#EFF6FF]">
                    <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-[#111827]">Running Detection</p>
                    <p className="text-xs text-[#6B7280]">{detectionStages[currentStage] ?? "Processing..."}</p>
                  </div>
                  <span className="text-xs font-medium text-[#2563EB]">{Math.round(progress)}%</span>
                </div>
                <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-[#F3F4F6]">
                  <motion.div className="h-full rounded-full bg-[#2563EB]" initial={{ width: 0 }} animate={{ width: `${progress}%` }} />
                </div>
              </CardContent>
            </Card>
          )}
        </section>
      )}

      {/* ── Bug Summary Panel (after completion) ── */}
      {isCompleted && (
        <>
          {prioritizationData && (
            <BugSummaryPanel
              prioritizationData={prioritizationData}
              securityData={securityData}
              performanceData={performanceData}
              staticData={staticData}
            />
          )}

          {/* ── Category Cards ── */}
          <div className="space-y-4">
            {categories.map((cat) => {
              const isExpanded = expandedCategory === cat.id;
              const showAll = showAllCategory === cat.id;
              const bugsForCat = catFilteredBugs(cat, filteredBugs);
              const visibleBugs = showAll ? bugsForCat : bugsForCat.slice(0, 5);

              // Skip empty pending categories when no filters active
              if (cat.status === "pending" && cat.total === 0 && !hasFilters && !isExpanded) return null;

              return (
                <Card key={cat.id}>
                  <CardContent className="p-0">
                    {/* Header Row */}
                    <button
                      onClick={() => setExpandedCategory(isExpanded ? null : cat.id)}
                      className="flex w-full items-center justify-between p-4 hover:bg-[#F9FAFB] transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${cat.status === "completed" ? "bg-[#ECFDF5]" : "bg-[#F3F4F6]"}`}>
                          {cat.status === "completed" ? (
                            <CheckCircle className="h-4 w-4 text-[#059669]" />
                          ) : (
                            <Clock className="h-4 w-4 text-[#9CA3AF]" />
                          )}
                        </div>
                        <div className="text-left">
                          <p className="text-sm font-semibold text-[#111827]">{cat.name}</p>
                          <p className="text-xs text-[#6B7280]">
                            {cat.status === "completed"
                              ? `${cat.total} ${cat.total === 1 ? "bug" : "bugs"} detected`
                              : "Not yet analyzed"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {cat.total > 0 && (
                          <div className="hidden items-center gap-2 sm:flex">
                            {cat.critical > 0 && <span className="rounded-full bg-[#FEF2F2] px-2 py-0.5 text-[10px] font-medium text-[#DC2626]">{cat.critical} Critical</span>}
                            {cat.high > 0 && <span className="rounded-full bg-[#FFF7ED] px-2 py-0.5 text-[10px] font-medium text-[#EA580C]">{cat.high} High</span>}
                            {cat.medium > 0 && <span className="rounded-full bg-[#FFFBEB] px-2 py-0.5 text-[10px] font-medium text-[#D97706]">{cat.medium} Medium</span>}
                          </div>
                        )}
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${cat.status === "completed" ? "bg-[#ECFDF5] text-[#059669]" : "bg-[#F3F4F6] text-[#6B7280]"}`}>
                          {cat.status === "completed" ? "Completed" : "Pending"}
                        </span>
                        {isExpanded ? <ChevronUp className="h-4 w-4 text-[#9CA3AF]" /> : <ChevronDown className="h-4 w-4 text-[#9CA3AF]" />}
                      </div>
                    </button>

                    {/* Expanded Bugs */}
                    {isExpanded && (
                      <div className="border-t border-[#E5E7EB] px-4 pb-4">
                        {bugsForCat.length === 0 ? (
                          <p className="py-4 text-center text-xs text-[#6B7280]">
                            {cat.status === "pending"
                              ? "This module has not been analyzed yet."
                              : "No issues detected in this category."}
                          </p>
                        ) : (
                          <>
                            {/* Table Header */}
                            <div className="hidden border-b border-[#E5E7EB] py-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] sm:grid sm:grid-cols-[100px_1fr_1fr_60px_100px]">
                              <span>Severity</span>
                              <span>Bug</span>
                              <span>File</span>
                              <span>Line</span>
                              <span className="text-right">Action</span>
                            </div>

                            {visibleBugs.map((bug, idx) => {
                              const isSelected = selectedBug === bug;
                              return (
                                <div key={`${bug.affected_file}-${bug.line_number}-${bug.column_number}-${idx}`}>
                                  <div className="grid gap-2 border-b border-[#E5E7EB] py-3 sm:grid-cols-[100px_1fr_1fr_60px_100px] sm:items-center">
                                    <span className={`inline-block w-fit rounded-full px-2 py-0.5 text-[10px] font-medium ${severityBadge(bug.severity)}`}>
                                      {bug.severity}
                                    </span>
                                    <div className="min-w-0">
                                      <p className="text-xs font-medium text-[#111827]">{bug.bug_title}</p>
                                      <p className="text-[10px] text-[#6B7280] truncate">{bug.description}</p>
                                    </div>
                                    <span className="inline-flex items-center gap-1 text-xs text-[#6B7280]">
                                      <FileCode className="h-3 w-3 shrink-0" />
                                      <span className="truncate">{bug.affected_file}</span>
                                    </span>
                                    <span className="text-xs text-[#6B7280]">{bug.line_number}:{bug.column_number}</span>
                                    <div className="text-right">
                                      <button
                                        onClick={() => setSelectedBug(isSelected ? null : bug)}
                                        className="rounded-md border border-[#E5E7EB] bg-white px-3 py-1.5 text-[10px] font-medium text-[#2563EB] hover:bg-[#EFF6FF] transition-colors"
                                      >
                                        {isSelected ? "Close" : "View Details"}
                                      </button>
                                    </div>
                                  </div>
                                  {/* Detail */}
                                  {isSelected && (
                                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="border-b border-[#E5E7EB] bg-[#F9FAFB] p-4">
                                      <div className="flex items-center gap-2 mb-3 flex-wrap">
                                        {bug.language && <span className="text-xs text-[#6B7280]">{bug.language}</span>}
                                        {bug.function_name && <span className="text-xs text-[#2563EB]">in {bug.function_name}()</span>}
                                        {"package_name" in bug && (bug as any).package_name && (
                                          <>
                                            <span className="text-xs text-[#D1D5DB]">·</span>
                                            <span className="text-xs font-medium text-[#059669]">{(bug as any).package_name}</span>
                                            {(bug as any).current_version && <span className="text-xs text-[#6B7280]">v{(bug as any).current_version}</span>}
                                            {(bug as any).recommended_version && <span className="text-xs text-[#2563EB]">→ v{(bug as any).recommended_version}</span>}
                                          </>
                                        )}
                                        <span className="text-xs text-[#D1D5DB]">·</span>
                                        <span className="text-xs text-[#6B7280]">Confidence: {bug.confidence}%</span>
                                        <span className="text-xs text-[#D1D5DB]">·</span>
                                        <span className="text-xs text-[#6B7280]">Status: Unresolved</span>
                                      </div>

                                      {/* ── Architecture-specific enhanced detail ── */}
                                      {"architecture_category" in bug && (
                                        <div className="mb-3 rounded-lg border border-[#E5E7EB] bg-white p-3">
                                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#6B7280] mb-2">Architecture & Logic Details</p>
                                          <div className="grid gap-2 sm:grid-cols-2">
                                            <div>
                                              <span className="text-[10px] font-medium text-[#9CA3AF]">Issue Type</span>
                                              <p className="text-xs font-medium text-[#111827]">{(bug as ArchitectureIssueInfo).architecture_category?.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</p>
                                            </div>
                                            <div>
                                              <span className="text-[10px] font-medium text-[#9CA3AF]">Affected Module</span>
                                              <p className="text-xs font-medium text-[#111827]">{getModuleFromPath(bug.affected_file)}</p>
                                            </div>
                                            <div>
                                              <span className="text-[10px] font-medium text-[#9CA3AF]">Business Impact</span>
                                              <p className="text-xs text-[#374151]">{getBusinessImpact((bug as ArchitectureIssueInfo).architecture_category)}</p>
                                            </div>
                                            <div>
                                              <span className="text-[10px] font-medium text-[#9CA3AF]">Architecture Impact</span>
                                              <p className="text-xs text-[#374151]">{(bug as ArchitectureIssueInfo).impact_scope || getArchitectureImpact((bug as ArchitectureIssueInfo).architecture_category)}</p>
                                            </div>
                                          </div>
                                        </div>
                                      )}

                                      <div className="grid gap-3 md:grid-cols-2">
                                        <div>
                                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">AI Explanation</p>
                                          <div className="rounded-lg bg-white p-3 border border-[#E5E7EB]">
                                            <p className="text-xs leading-relaxed text-[#374151]">{bug.ai_explanation}</p>
                                          </div>
                                        </div>
                                        <div>
                                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Suggested Fix</p>
                                          <div className="rounded-lg bg-[#EFF6FF] p-3 border border-[#BFDBFE]">
                                            <p className="text-xs leading-relaxed text-[#2563EB]">{bug.suggested_fix}</p>
                                          </div>
                                        </div>
                                      </div>
                                      {bug.code_snippet && (
                                        <div className="mt-3">
                                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Source Code</p>
                                          <pre className="overflow-x-auto rounded-lg bg-[#111827] p-3 text-xs leading-relaxed text-[#E5E7EB]">
                                            <code>{bug.code_snippet}</code>
                                          </pre>
                                        </div>
                                      )}
                                    </motion.div>
                                  )}
                                </div>
                              );
                            })}
                          </>
                        )}

                        {/* Show More / Show Less */}
                        {bugsForCat.length > 5 && (
                          <button
                            onClick={() => setShowAllCategory(showAll ? null : cat.id)}
                            className="mt-2 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
                          >
                            {showAll ? "Show Less" : `Show More (${bugsForCat.length - 5} more)`}
                          </button>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

        </>
      )}

      {/* ── Start Button (idle) ── */}
      {detectionState === "idle" && (
        <div className="text-center">
          <button
            onClick={startDetection}
            className="inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-6 py-3 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
          >
            <Play className="h-4 w-4" /> Start AI Bug Detection
          </button>
        </div>
      )}

      {/* ── Running State ── */}
      {detectionState === "running" && (
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-lg bg-[#EFF6FF] px-6 py-3 text-sm font-medium text-[#2563EB]">
            <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
            Detection in Progress...
          </div>
        </div>
      )}

      {/* ── Navigation ── */}
      {(() => {
        const nav = getWorkflowNavigation("bug-detection", projectId!);
        const prev = nav.previous;
        const nxt = nav.next;
        return (
          <div className="flex items-center justify-between pt-2">
            {prev ? (
              <button
                onClick={() => navigate(prev.route)}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-[#6B7280] hover:text-[#111827] transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous: {prev.label}
              </button>
            ) : (
              <div />
            )}
            <span className="text-xs text-[#9CA3AF]">Step {nav.current.number} of {nav.totalSteps}</span>
            {nxt ? (
              isCompleted ? (
                <button
                  onClick={() => navigate(nxt.route)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[#2563EB] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
                >
                  Next: {nxt.label}
                  <ChevronRight className="h-4 w-4" />
                </button>
              ) : (
                <button
                  disabled
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[#E5E7EB] px-5 py-2.5 text-sm font-medium text-[#9CA3AF] cursor-not-allowed"
                >
                  Next: {nxt.label}
                  <ChevronRight className="h-4 w-4" />
                </button>
              )
            ) : (
              <div />
            )}
          </div>
        );
      })()}

    </motion.div>
  );
}

const detectionStages = [
  "Scanning source files for syntax errors...",
  "Analyzing code structure and quality...",
  "Checking dependencies for conflicts...",
  "Inspecting runtime behavior patterns...",
  "Scanning for security vulnerabilities...",
  "Evaluating performance bottlenecks...",
  "Reviewing architecture and logic...",
  "Prioritizing detected issues...",
];

function catFilteredBugs(cat: BugCategory, filteredBugs: SyntaxErrorInfo[]): SyntaxErrorInfo[] {
  if (cat.total === 0) return [];
  const catBugs = new Set(cat.bugs);
  return filteredBugs.filter((b) => catBugs.has(b));
}
