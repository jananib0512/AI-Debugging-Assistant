import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

export type WorkflowStep =
  | "upload"
  | "overview"
  | "analysis"
  | "bug-detection"
  | "root-cause"
  | "code-repair"
  | "testing"
  | "download";

const steps: { id: WorkflowStep; label: string; number: number }[] = [
  { id: "upload", label: "Upload Project", number: 1 },
  { id: "overview", label: "Overview & Validation", number: 2 },
  { id: "analysis", label: "Project Analysis", number: 3 },
  { id: "bug-detection", label: "AI Bug Detection", number: 4 },
  { id: "root-cause", label: "Root Cause Analysis", number: 5 },
  { id: "code-repair", label: "AI Code Repair", number: 6 },
  { id: "testing", label: "Testing & Validation", number: 7 },
  { id: "download", label: "Download Fixed Project", number: 8 },
];

interface WorkflowTrackerProps {
  currentStep: WorkflowStep;
}

export function WorkflowTracker({ currentStep }: WorkflowTrackerProps) {
  const currentIndex = steps.findIndex((s) => s.id === currentStep);

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex min-w-max items-center gap-0 px-2 py-3">
        {steps.map((step, i) => {
          const isCompleted = i < currentIndex;
          const isCurrent = i === currentIndex;
          const isFuture = i > currentIndex;

          return (
            <div key={step.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold transition-colors duration-200",
                    isCompleted && "bg-[#2563EB] text-white",
                    isCurrent && "border-2 border-[#2563EB] bg-white text-[#2563EB]",
                    isFuture && "border border-[#E5E7EB] bg-white text-[#9CA3AF]",
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    step.number
                  )}
                </div>
                <span
                  className={cn(
                    "mt-1.5 whitespace-nowrap text-[10px] font-medium transition-colors duration-200",
                    isCompleted && "text-[#2563EB]",
                    isCurrent && "text-[#111827]",
                    isFuture && "text-[#9CA3AF]",
                  )}
                >
                  {step.label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div
                  className={cn(
                    "mx-2 h-px w-12 transition-colors duration-200 sm:w-16 md:w-20",
                    isCompleted ? "bg-[#2563EB]" : "bg-[#E5E7EB]",
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
