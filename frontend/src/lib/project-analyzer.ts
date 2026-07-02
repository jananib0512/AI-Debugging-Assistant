import { api } from "@/lib/api";
import type { AnalyzerResponse, ProjectAnalysis } from "@/types/project-analyzer";

export async function getProjectAnalysis(
  projectId: number,
): Promise<ProjectAnalysis> {
  const res = await api.get<ProjectAnalysis>(
    `/projects/${projectId}/analysis`,
  );
  return res.data;
}

export async function getProjectAnalyzer(
  projectId: number,
): Promise<AnalyzerResponse> {
  const res = await api.get<AnalyzerResponse>(
    `/projects/${projectId}/analyzer`,
  );
  return res.data;
}
