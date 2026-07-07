import { api } from "@/lib/api";
import type {
  AnalyzerResponse,
  AnalyzerValidationResponse,
  ArchitectureDetectionResponse,
  CodeQualityResponse,
  ConfigurationIntelligenceResponse,
  EntryPointDetectionResponse,
  FileAnalysisResponse,
  FrameworkIntelligenceResponse,
  FunctionClassResponse,
  ImportDependencyResponse,
  ModuleDetectionResponse,
  ProjectAnalysis,
  ProjectInsightsResponse,
  ProjectIntelligenceResponse,
  SourceCodeIntelligenceResponse,
} from "@/types/project-analyzer";

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

export async function getEntryPoints(
  projectId: number,
): Promise<EntryPointDetectionResponse> {
  const res = await api.get<EntryPointDetectionResponse>(
    `/projects/${projectId}/entry-points`,
  );
  return res.data;
}

export async function getArchitecture(
  projectId: number,
): Promise<ArchitectureDetectionResponse> {
  const res = await api.get<ArchitectureDetectionResponse>(
    `/projects/${projectId}/architecture`,
  );
  return res.data;
}

export async function getModules(
  projectId: number,
): Promise<ModuleDetectionResponse> {
  const res = await api.get<ModuleDetectionResponse>(
    `/projects/${projectId}/modules`,
  );
  return res.data;
}

export async function getFrameworks(
  projectId: number,
): Promise<FrameworkIntelligenceResponse> {
  const res = await api.get<FrameworkIntelligenceResponse>(
    `/projects/${projectId}/frameworks`,
  );
  return res.data;
}

export async function getProjectInsights(
  projectId: number,
): Promise<ProjectInsightsResponse> {
  const res = await api.get<ProjectInsightsResponse>(
    `/projects/${projectId}/project-insights`,
  );
  return res.data;
}

export async function getProjectIntelligence(
  projectId: number,
): Promise<ProjectIntelligenceResponse> {
  const res = await api.get<ProjectIntelligenceResponse>(
    `/projects/${projectId}/project-intelligence`,
  );
  return res.data;
}

export async function getConfiguration(
  projectId: number,
): Promise<ConfigurationIntelligenceResponse> {
  const res = await api.get<ConfigurationIntelligenceResponse>(
    `/projects/${projectId}/configuration`,
  );
  return res.data;
}

export async function getAnalyzerValidation(
  projectId: number,
): Promise<AnalyzerValidationResponse> {
  const res = await api.get<AnalyzerValidationResponse>(
    `/projects/${projectId}/analyzer-validation`,
  );
  return res.data;
}

export async function getCodeIntelligence(
  projectId: number,
): Promise<SourceCodeIntelligenceResponse> {
  const res = await api.get<SourceCodeIntelligenceResponse>(
    `/projects/${projectId}/code-intelligence`,
  );
  return res.data;
}

export async function getFunctionClassAnalysis(
  projectId: number,
): Promise<FunctionClassResponse> {
  const res = await api.get<FunctionClassResponse>(
    `/projects/${projectId}/function-class-analysis`,
  );
  return res.data;
}

export async function getImportDependencyAnalysis(
  projectId: number,
): Promise<ImportDependencyResponse> {
  const res = await api.get<ImportDependencyResponse>(
    `/projects/${projectId}/import-dependency-analysis`,
  );
  return res.data;
}

export async function getFileAnalysis(
  projectId: number,
): Promise<FileAnalysisResponse> {
  const res = await api.get<FileAnalysisResponse>(
    `/projects/${projectId}/file-analysis`,
  );
  return res.data;
}

export async function getCodeQuality(
  projectId: number,
): Promise<CodeQualityResponse> {
  const res = await api.get<CodeQualityResponse>(
    `/projects/${projectId}/code-quality`,
  );
  return res.data;
}
