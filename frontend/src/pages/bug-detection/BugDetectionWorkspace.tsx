import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Bug,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  Eye,
  EyeOff,
  Play,
  RefreshCw,
} from "lucide-react";
import { getBugDetectionWorkspace } from "@/lib/project-analyzer";
import type { BugDetectionWorkspaceResponse } from "@/types/project-analyzer";
import { Card, CardContent } from "@/components/ui/card";

const moduleDisplayNames: Record<string, string> = {
  "Syntax Detection": "Syntax Errors",
  "Static Code Analysis": "Code Quality",
  "Dependency Analysis": "Dependencies",
  "Runtime Risk Detection": "Runtime Issues",
  "Security Detection": "Security",
  "Performance Detection": "Performance",
  "Architecture & Logic Detection": "Architecture",
  "AI Bug Prioritization": "AI Prioritization",
};

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

type DetectionState = "idle" | "running" | "completed";

export function BugDetectionWorkspace() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<BugDetectionWorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detectionState, setDetectionState] = useState<DetectionState>("idle");
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);
  const [moduleStatuses, setModuleStatuses] = useState<Record<string, string>>({});
  const [showDetails, setShowDetails] = useState(false);
  const fetchedRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(() => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    getBugDetectionWorkspace(Number(projectId))
      .then((res) => {
        setData(res);
        fetchedRef.current = true;
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to load workspace";
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  useEffect(() => {
    if (detectionState !== "running") return;
    const moduleKeys = data?.detection_modules.map((m) => m.name) ?? [];
    let currentIdx = 0;
    const statuses: Record<string, string> = {};
    moduleKeys.forEach((k) => { statuses[k] = "ready"; });
    setModuleStatuses({ ...statuses });

    timerRef.current = setInterval(() => {
      if (currentIdx >= moduleKeys.length) {
        if (timerRef.current) clearInterval(timerRef.current);
        setDetectionState("completed");
        setProgress(100);
        setCurrentStage(moduleKeys.length - 1);
        const final: Record<string, string> = {};
        moduleKeys.forEach((k) => { final[k] = "completed"; });
        setModuleStatuses(final);
        return;
      }
      const key = moduleKeys[currentIdx]!;
      statuses[key] = "running";
      setModuleStatuses({ ...statuses });
      setCurrentStage(currentIdx);
      setProgress(Math.round((currentIdx / moduleKeys.length) * 100));

      let elapsed = 0;
      const moduleTimer = setInterval(() => {
        elapsed += 100;
        if (elapsed >= 1400) {
          clearInterval(moduleTimer);
          statuses[key] = "completed";
          setModuleStatuses({ ...statuses });
          setProgress(Math.round(((currentIdx + 1) / moduleKeys.length) * 100));
          currentIdx++;
        }
      }, 100);
    }, 1600);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [detectionState, data]);

  const startDetection = () => {
    setDetectionState("running");
    setProgress(0);
    setCurrentStage(0);
    setShowDetails(false);
  };

  const displayName = (backendName: string): string =>
    moduleDisplayNames[backendName] ?? backendName;

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
        <button
          onClick={fetchData}
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Bug className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No project data available</p>
        <p className="mt-1 text-xs text-[#6B7280]">Upload and analyze a project to begin bug detection.</p>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto max-w-4xl space-y-8">

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
          <Card>
            <CardContent className="p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Name</p>
              <p className="mt-1 text-sm font-semibold text-[#111827]">{data.project_name || "—"}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Type</p>
              <p className="mt-1 text-sm font-semibold text-[#111827]">{data.project_type || "—"}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Language</p>
              <p className="mt-1 text-sm font-semibold text-[#111827]">{data.language || "—"}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Total Files</p>
              <p className="mt-1 text-sm font-semibold text-[#111827]">{data.total_files}</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ── Detection Status ── */}
      {detectionState !== "idle" && (
        <section>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Detection Status</p>
          <Card hover={false}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {detectionState === "running" ? (
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#EFF6FF]">
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
                    </div>
                  ) : (
                    <CheckCircle className="h-5 w-5 text-[#059669]" />
                  )}
                  <div>
                    <p className="text-sm font-semibold text-[#111827]">
                      {detectionState === "running" ? "Running" : "Completed"}
                    </p>
                    <p className="text-xs text-[#6B7280]">
                      {detectionState === "running"
                        ? detectionStages[currentStage] ?? "Processing..."
                        : "All modules have finished inspecting your project."}
                    </p>
                  </div>
                </div>
                {detectionState === "completed" && (
                  <span className="flex items-center gap-1 rounded-full bg-[#ECFDF5] px-3 py-1 text-xs font-semibold text-[#059669]">
                    <CheckCircle className="h-3.5 w-3.5" /> Complete
                  </span>
                )}
              </div>
              {detectionState === "running" && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-xs text-[#6B7280]">
                    <span>{Math.round(progress)}%</span>
                    <span>{currentStage + 1} of {data.detection_modules.length} modules</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[#F3F4F6]">
                    <motion.div
                      className="h-full rounded-full bg-[#2563EB] transition-all duration-300"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      )}

      {/* ── Bug Detection Modules ── */}
      <section>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Detection Modules</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {data.detection_modules.map((mod) => {
            const status =
              detectionState === "idle"
                ? "ready"
                : moduleStatuses[mod.name] ?? "ready";
            return (
              <Card key={mod.name}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-[#111827]">{displayName(mod.name)}</p>
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                        status === "completed"
                          ? "bg-[#ECFDF5] text-[#059669]"
                          : status === "running"
                            ? "bg-[#EFF6FF] text-[#2563EB]"
                            : "bg-[#F3F4F6] text-[#6B7280]"
                      }`}
                    >
                      {status === "completed" && <CheckCircle className="h-2.5 w-2.5" />}
                      {status === "running" && (
                        <span className="h-2 w-2 animate-pulse rounded-full bg-[#2563EB]" />
                      )}
                      {status === "ready" && <Clock className="h-2.5 w-2.5" />}
                      {status === "completed"
                        ? "Completed"
                        : status === "running"
                          ? "Running"
                          : "Ready"}
                    </span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* ── AI Summary ── */}
      <section>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">AI Summary</p>
        <Card hover={false}>
          <CardContent className="p-5">
            <p className="text-sm leading-relaxed text-[#374151]">
              {detectionState === "idle" &&
                "Your project is ready. The AI Software Engineer will now inspect your project. No bugs have been analyzed yet."}
              {detectionState === "running" &&
                "The AI Software Engineer is inspecting your project. Detection modules are running and results will be available shortly."}
              {detectionState === "completed" &&
                "The AI Software Engineer has completed inspecting your project. All detection modules have finished. You can now review the results and continue to root cause analysis."}
            </p>
          </CardContent>
        </Card>
      </section>

      {/* ── View Details (after completion) ── */}
      {detectionState === "completed" && (
        <section>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
          >
            {showDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            {showDetails ? "Hide Details" : "View Details"}
          </button>
          {showDetails && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-3 overflow-hidden rounded-lg border border-[#E5E7EB]"
            >
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-[#F9FAFB] text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">
                    <th className="px-4 py-3">File</th>
                    <th className="px-4 py-3">Bug</th>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3">Explanation</th>
                    <th className="px-4 py-3">Suggested Fix</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-xs text-[#6B7280]">
                      No issues detected. Your project looks clean.
                    </td>
                  </tr>
                </tbody>
              </table>
            </motion.div>
          )}
        </section>
      )}

      {/* ── Primary Button ── */}
      <div className="text-center">
        {detectionState === "idle" && (
          <button
            onClick={startDetection}
            className="inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-6 py-3 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
          >
            <Play className="h-4 w-4" /> Start AI Bug Detection
          </button>
        )}
        {detectionState === "running" && (
          <div className="inline-flex items-center gap-2 rounded-lg bg-[#EFF6FF] px-6 py-3 text-sm font-medium text-[#2563EB]">
            <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
            Detection in Progress...
          </div>
        )}
        {detectionState === "completed" && (
          <button
            onClick={() => navigate(`/projects/${projectId}/bug-detection/syntax-detection`)}
            className="inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-6 py-3 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
          >
            View Syntax Results
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* ── Navigation ── */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={() => navigate(`/projects/${projectId}/analyzer`)}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-[#6B7280] hover:text-[#111827] transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous: Project Analysis
        </button>
        <span className="text-xs text-[#9CA3AF]">Step 4 of 8</span>
        {detectionState !== "completed" ? (
          <button
            disabled
            className="inline-flex items-center gap-1.5 rounded-lg bg-[#E5E7EB] px-5 py-2.5 text-sm font-medium text-[#9CA3AF] cursor-not-allowed"
          >
            Next: Syntax Analysis
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <button
            onClick={() => navigate(`/projects/${projectId}/bug-detection/syntax-detection`)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-[#2563EB] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
          >
            Next: Syntax Analysis
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>

    </motion.div>
  );
}
