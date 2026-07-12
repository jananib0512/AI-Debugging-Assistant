import { useEffect, useRef, useState, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Loader2,
  XCircle,
} from "lucide-react";
import { getProject } from "@/lib/projects";
import { getBugPrioritization } from "@/lib/project-analyzer";
import { Card, CardContent } from "@/components/ui/card";
import { getWorkflowNavigation } from "@/lib/workflow-navigation";
import type { Project } from "@/types/project";
import type { PrioritizationResponse } from "@/types/project-analyzer";

type LoadState = "loading" | "loaded" | "error";

interface Verifications {
  projectExists: boolean;
  bugDetectionCompleted: boolean;
  analysisCacheExists: boolean;
  workspaceReady: boolean;
  requiredMetadataExists: boolean;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" },
  },
};

function initialVerifications(): Verifications {
  return {
    projectExists: false,
    bugDetectionCompleted: false,
    analysisCacheExists: false,
    workspaceReady: false,
    requiredMetadataExists: false,
  };
}

function statusRow(label: string, ok: boolean) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-[#6B7280]">{label}</span>
      {ok ? (
        <span className="flex items-center gap-1 text-sm font-medium text-[#059669]">
          <CheckCircle className="h-3.5 w-3.5" /> Ready
        </span>
      ) : (
        <span className="flex items-center gap-1 text-sm font-medium text-[#DC2626]">
          <XCircle className="h-3.5 w-3.5" /> Pending
        </span>
      )}
    </div>
  );
}

export function RootCauseWorkspace() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [prioritization, setPrioritization] = useState<PrioritizationResponse | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [verifications, setVerifications] = useState<Verifications>(initialVerifications);
  const fetchedRef = useRef(false);

  const allReady = useMemo(
    () => Object.values(verifications).every((v) => v),
    [verifications],
  );

  useEffect(() => {
    if (!projectId || fetchedRef.current) return;
    fetchedRef.current = true;

    const pid = Number(projectId);

    const load = async () => {
      const [proj, prior] = await Promise.all([
        getProject(pid),
        getBugPrioritization(pid),
      ]);

      const v: Verifications = {
        projectExists: !!proj,
        bugDetectionCompleted: !!prior && prior.prioritized_issues.length > 0,
        analysisCacheExists: !!prior,
        workspaceReady: !!proj?.workspace_path,
        requiredMetadataExists: !!(proj?.language && proj?.framework),
      };

      setProject(proj);
      setPrioritization(prior);
      setVerifications(v);
      setLoadState("loaded");

      if (!v.projectExists) {
        setErrorMessage("Project not found or could not be loaded.");
      }
    };

    load().catch(() => {
      setLoadState("error");
      setErrorMessage("Failed to load project data. Please try again.");
    });
  }, [projectId]);

  if (loadState === "loading") {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="mb-4 h-8 w-8 animate-spin text-[#2563EB]" />
        <p className="text-sm font-medium text-[#111827]">Preparing Root Cause Analysis...</p>
        <p className="mt-1 text-xs text-[#6B7280]">Loading project data and bug detection results.</p>
      </div>
    );
  }

  if (loadState === "error") {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="max-w-md rounded-lg border border-[#E5E7EB] bg-white px-6 py-8 text-center shadow-sm">
          <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-[#DC2626]" />
          <h2 className="text-lg font-semibold text-[#111827]">Failed to Load</h2>
          <p className="mt-2 text-sm text-[#6B7280]">{errorMessage || "An unexpected error occurred."}</p>
          <button
            onClick={() => { fetchedRef.current = false; window.location.reload(); }}
            className="mt-4 rounded-lg bg-[#2563EB] px-4 py-2 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const severityCounts = prioritization
    ? {
        total: prioritization.total_issues,
        critical: prioritization.critical_count,
        high: prioritization.high_count,
        medium: prioritization.medium_count,
        low: prioritization.low_count,
      }
    : { total: 0, critical: 0, high: 0, medium: 0, low: 0 };

  const projectHealth = prioritization
    ? (() => {
        const score = Math.max(
          0,
          100 -
            (prioritization.critical_count * 10 +
              prioritization.high_count * 5 +
              prioritization.medium_count * 2 +
              prioritization.low_count * 1) /
              Math.max(prioritization.total_issues, 1) *
              8,
        );
        if (score >= 90) return "Excellent";
        if (score >= 70) return "Good";
        if (score >= 50) return "Fair";
        return "Poor";
      })()
    : "Unknown";

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* ── AI Summary ── */}
      <motion.div variants={itemVariants}>
        <Card className="border border-[#E5E7EB] bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full bg-[#EFF6FF]">
                <CheckCircle className="h-4 w-4 text-[#2563EB]" />
              </div>
              <div className="flex-1 space-y-1">
                <h3 className="text-sm font-semibold text-[#111827]">AI Summary</h3>
                <p className="text-sm leading-relaxed text-[#4B5563]">
                  The AI Software Engineer has completed bug detection successfully.
                  The project is now ready for Root Cause Analysis.
                  The next step is to determine why each issue occurred before generating automatic code repairs.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ── Project Summary ── */}
      <motion.div variants={itemVariants}>
        <Card className="border border-[#E5E7EB] bg-white shadow-sm">
          <CardContent className="p-5">
            <h3 className="mb-3 text-sm font-semibold text-[#111827]">Project Summary</h3>
            <div className="grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-3 lg:grid-cols-4">
              <div>
                <p className="text-xs text-[#9CA3AF]">Project Name</p>
                <p className="text-sm font-medium text-[#111827]">{project?.project_name || "-"}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">Project Type</p>
                <p className="text-sm font-medium text-[#111827]">{prioritization?.language || project?.language || "-"}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">Language</p>
                <p className="text-sm font-medium text-[#111827]">{prioritization?.language || project?.language || "-"}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">Framework</p>
                <p className="text-sm font-medium text-[#111827]">{project?.framework || "None"}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">Total Bugs</p>
                <p className="text-sm font-medium text-[#111827]">{severityCounts.total}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">Critical Bugs</p>
                <p className="text-sm font-medium text-[#DC2626]">{severityCounts.critical}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">High Bugs</p>
                <p className="text-sm font-medium text-[#EA580C]">{severityCounts.high}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">Medium Bugs</p>
                <p className="text-sm font-medium text-[#D97706]">{severityCounts.medium}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">Low Bugs</p>
                <p className="text-sm font-medium text-[#6B7280]">{severityCounts.low}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">Project Health</p>
                <p className="text-sm font-medium text-[#111827]">{projectHealth}</p>
              </div>
              <div>
                <p className="text-xs text-[#9CA3AF]">AI Confidence</p>
                <p className="text-sm font-medium text-[#111827]">
                  {prioritization?.prioritized_issues.length
                    ? `${Math.round(prioritization.prioritized_issues.reduce((s, i) => s + i.confidence, 0) / prioritization.prioritized_issues.length)}%`
                    : "-"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ── Root Cause Status ── */}
      <motion.div variants={itemVariants}>
        <Card className="border border-[#E5E7EB] bg-white shadow-sm">
          <CardContent className="p-5">
            <h3 className="mb-3 text-sm font-semibold text-[#111827]">Root Cause Status</h3>
            <div className="grid grid-cols-1 gap-1 sm:grid-cols-2 lg:grid-cols-3">
              {statusRow("Workspace Ready", verifications.projectExists)}
              {statusRow("Reasoning Ready", verifications.analysisCacheExists)}
              {statusRow("Bug Mapping Ready", verifications.bugDetectionCompleted)}
              {statusRow("Dependency Context Ready", verifications.workspaceReady)}
              {statusRow("Execution Context Ready", verifications.requiredMetadataExists)}
              {statusRow("AI Ready", allReady)}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ── Start Button ── */}
      <motion.div variants={itemVariants}>
        <div className="flex justify-center pt-2">
          <button
            disabled={!allReady}
            onClick={() => navigate(`/projects/${projectId}/root-cause`)}
            className="inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-6 py-3 text-sm font-medium text-white hover:bg-[#1D4ED8] disabled:cursor-not-allowed disabled:bg-[#9CA3AF] transition-colors"
          >
            {allReady ? (
              <>
                Start Root Cause Analysis
                <ChevronRight className="h-4 w-4" />
              </>
            ) : (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Initializing...
              </>
            )}
          </button>
        </div>
      </motion.div>

      {/* ── Error message when project not found ── */}
      {!verifications.projectExists && (
        <motion.div variants={itemVariants}>
          <Card className="border border-[#FCA5A5] bg-[#FEF2F2] shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-[#DC2626]" />
                <p className="text-sm text-[#991B1B]">{errorMessage || "Project not found."}</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Warning when bug detection not completed ── */}
      {verifications.projectExists && !verifications.bugDetectionCompleted && (
        <motion.div variants={itemVariants}>
          <Card className="border border-[#FDE68A] bg-[#FFFBEB] shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-[#D97706]" />
                <p className="text-sm text-[#92400E]">
                  Bug detection has not been completed for this project.
                  Please run AI Bug Detection first.
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Navigation ── */}
      {(() => {
        const nav = getWorkflowNavigation("root-cause", projectId!);
        const prev = nav.previous;
        const nxt = nav.next;
        return (
          <motion.div
            variants={itemVariants}
            className="flex items-center justify-between pt-2"
          >
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
              <button
                disabled
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#E5E7EB] px-5 py-2.5 text-sm font-medium text-[#9CA3AF] cursor-not-allowed"
              >
                Next: {nxt.label}
                <ChevronRight className="h-4 w-4" />
              </button>
            ) : (
              <div />
            )}
          </motion.div>
        );
      })()}
    </motion.div>
  );
}
