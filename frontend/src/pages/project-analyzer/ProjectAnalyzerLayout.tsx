import { useParams, Outlet } from "react-router-dom";
import { AnalysisProvider } from "@/contexts/AnalysisContext";
import { WorkflowTracker } from "@/components/workflow/WorkflowTracker";

export function ProjectAnalyzerLayout() {
  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-[#6B7280]">Project ID is required.</p>
      </div>
    );
  }

  return (
    <AnalysisProvider projectId={projectId}>
      <div className="mx-auto max-w-7xl px-6 py-6">
        <WorkflowTracker currentStep="analysis" />
        <div className="mt-6">
          <Outlet />
        </div>
      </div>
    </AnalysisProvider>
  );
}
