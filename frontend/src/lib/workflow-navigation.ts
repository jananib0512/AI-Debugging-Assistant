import type { WorkflowStep } from "@/components/workflow/WorkflowTracker";

export interface StepNavInfo {
  id: WorkflowStep;
  label: string;
  number: number;
  route: string;
}

const stepRoutes: Record<WorkflowStep, string> = {
  "upload": "/upload",
  "overview": "/projects/:projectId/overview",
  "analysis": "/projects/:projectId/analyzer",
  "bug-detection": "/projects/:projectId/bug-detection",
  "root-cause": "/projects/:projectId/root-cause",
  "code-repair": "/projects/:projectId/code-repair",
  "testing": "/projects/:projectId/testing",
  "download": "/projects/:projectId/download",
};

const stepLabels: Record<WorkflowStep, string> = {
  "upload": "Upload Project",
  "overview": "Overview & Validation",
  "analysis": "Project Analysis",
  "bug-detection": "AI Bug Detection",
  "root-cause": "AI Root Cause Analysis",
  "code-repair": "AI Code Repair",
  "testing": "Testing & Validation",
  "download": "Download Fixed Project",
};

const stepNumbers: Record<WorkflowStep, number> = {
  "upload": 1,
  "overview": 2,
  "analysis": 3,
  "bug-detection": 4,
  "root-cause": 5,
  "code-repair": 6,
  "testing": 7,
  "download": 8,
};

const stepOrder: WorkflowStep[] = [
  "upload",
  "overview",
  "analysis",
  "bug-detection",
  "root-cause",
  "code-repair",
  "testing",
  "download",
];

function resolveRoute(routePattern: string, projectId: string | number): string {
  return routePattern.replace(":projectId", String(projectId));
}

export interface WorkflowNavigation {
  current: StepNavInfo;
  previous: StepNavInfo | null;
  next: StepNavInfo | null;
  totalSteps: number;
}

export function getWorkflowNavigation(
  currentStep: WorkflowStep,
  projectId: string | number,
): WorkflowNavigation {
  const currentIndex = stepOrder.indexOf(currentStep);

  const current: StepNavInfo = {
    id: currentStep,
    label: stepLabels[currentStep],
    number: stepNumbers[currentStep],
    route: resolveRoute(stepRoutes[currentStep], projectId),
  };

  const prevStep: WorkflowStep | undefined = currentIndex > 0 ? stepOrder[currentIndex - 1] : undefined;
  const previous: StepNavInfo | null = prevStep
    ? {
        id: prevStep,
        label: stepLabels[prevStep],
        number: stepNumbers[prevStep],
        route: resolveRoute(stepRoutes[prevStep], projectId),
      }
    : null;

  const nextStep: WorkflowStep | undefined = currentIndex < stepOrder.length - 1 ? stepOrder[currentIndex + 1] : undefined;
  const next: StepNavInfo | null = nextStep
    ? {
        id: nextStep,
        label: stepLabels[nextStep],
        number: stepNumbers[nextStep],
        route: resolveRoute(stepRoutes[nextStep], projectId),
      }
    : null;

  return {
    current,
    previous,
    next,
    totalSteps: stepOrder.length,
  };
}
