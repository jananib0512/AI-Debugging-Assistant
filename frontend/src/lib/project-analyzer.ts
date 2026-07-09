import { api } from "@/lib/api";
import type {
  AiEngineeringReadinessResponse,
  AnalyzerResponse,
  AnalyzerValidationResponse,
  ArchitectureDetectionResponse,
  BugDetectionWorkspaceResponse,
  PipelineStatusResponse,
  SyntaxDetectionResponse,
  StaticCodeAnalysisResponse,
  DependencyAnalysisResponse,
  RuntimeAnalysisResponse,
  SecurityAnalysisResponse,
  PerformanceAnalysisResponse,
  ArchitectureAnalysisResponse,
  PrioritizationResponse,
  CallGraphResponse,
  CodeQualityResponse,
  ConfigurationIntelligenceResponse,
  DocumentationIntelligenceResponse,
  EntryPointDetectionResponse,
  FileAnalysisResponse,
  FileIntelligenceResponse,
  FrameworkIntelligenceResponse,
  FuncClassIntelligenceResponse,
  FunctionClassResponse,
  ImportDependencyResponse,
  ModuleDetectionResponse,
  ProductionReadinessResponse,
  ProjectAnalysis,
  ProjectInsightsResponse,
  ProjectIntelligenceResponse,
  RefactoringIntelligenceResponse,
  RiskIntelligenceResponse,
  SecurityIntelligenceResponse,
  PerformanceIntelligenceResponse,
  MaintainabilityIntelligenceResponse,
  SemanticResponse,
  SourceCodeIntelligenceResponse,
  TestIntelligenceResponse,
  UnifiedIntelligenceResponse,
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

export async function getFileIntelligence(
  projectId: number,
): Promise<FileIntelligenceResponse> {
  const res = await api.get<FileIntelligenceResponse>(
    `/projects/${projectId}/file-intelligence`,
  );
  return res.data;
}

export async function getCallGraph(
  projectId: number,
): Promise<CallGraphResponse> {
  const res = await api.get<CallGraphResponse>(
    `/projects/${projectId}/call-graph`,
  );
  return res.data;
}

export async function getFunctionClassIntelligence(
  projectId: number,
): Promise<FuncClassIntelligenceResponse> {
  const res = await api.get<FuncClassIntelligenceResponse>(
    `/projects/${projectId}/function-class-intelligence`,
  );
  return res.data;
}

export async function getSemanticIntelligence(
  projectId: number,
): Promise<SemanticResponse> {
  const res = await api.get<SemanticResponse>(
    `/projects/${projectId}/semantic-intelligence`,
  );
  return res.data;
}

export async function getUnifiedIntelligence(
  projectId: number,
): Promise<UnifiedIntelligenceResponse> {
  const res = await api.get<UnifiedIntelligenceResponse>(
    `/projects/${projectId}/unified-intelligence`,
  );
  return res.data;
}

export async function getRiskIntelligence(
  projectId: number,
): Promise<RiskIntelligenceResponse> {
  const res = await api.get<RiskIntelligenceResponse>(
    `/projects/${projectId}/risk-intelligence`,
  );
  return res.data;
}

export async function getSecurityIntelligence(
  projectId: number,
): Promise<SecurityIntelligenceResponse> {
  const res = await api.get<SecurityIntelligenceResponse>(
    `/projects/${projectId}/security-intelligence`,
  );
  return res.data;
}

export async function getPerformanceIntelligence(
  projectId: number,
): Promise<PerformanceIntelligenceResponse> {
  const res = await api.get<PerformanceIntelligenceResponse>(
    `/projects/${projectId}/performance-intelligence`,
  );
  return res.data;
}

export async function getMaintainabilityIntelligence(
  projectId: number,
): Promise<MaintainabilityIntelligenceResponse> {
  const res = await api.get<MaintainabilityIntelligenceResponse>(
    `/projects/${projectId}/maintainability-intelligence`,
  );
  return res.data;
}

export async function getRefactoringIntelligence(
  projectId: number,
): Promise<RefactoringIntelligenceResponse> {
  const res = await api.get<RefactoringIntelligenceResponse>(
    `/projects/${projectId}/refactoring-intelligence`,
  );
  return res.data;
}

export async function getDocumentationIntelligence(
  projectId: number,
): Promise<DocumentationIntelligenceResponse> {
  const res = await api.get<DocumentationIntelligenceResponse>(
    `/projects/${projectId}/documentation-intelligence`,
  );
  return res.data;
}

export async function getTestIntelligence(
  projectId: number,
): Promise<TestIntelligenceResponse> {
  const res = await api.get<TestIntelligenceResponse>(
    `/projects/${projectId}/test-intelligence`,
  );
  return res.data;
}

export async function getProductionReadiness(
  projectId: number,
): Promise<ProductionReadinessResponse> {
  const res = await api.get<ProductionReadinessResponse>(
    `/projects/${projectId}/production-readiness`,
  );
  return res.data;
}

export async function getAiEngineeringReadiness(
  projectId: number,
): Promise<AiEngineeringReadinessResponse> {
  const res = await api.get<AiEngineeringReadinessResponse>(
    `/projects/${projectId}/ai-engineering-readiness`,
  );
  return res.data;
}

export async function getBugDetectionWorkspace(
  projectId: number,
): Promise<BugDetectionWorkspaceResponse> {
  const res = await api.get<BugDetectionWorkspaceResponse>(
    `/projects/${projectId}/bug-detection/workspace`,
  );
  return res.data;
}

export async function getBugDetectionPipeline(
  projectId: number,
): Promise<PipelineStatusResponse> {
  const res = await api.get<PipelineStatusResponse>(
    `/projects/${projectId}/bug-detection/pipeline`,
  );
  return res.data;
}

export async function getSyntaxDetection(
  projectId: number,
): Promise<SyntaxDetectionResponse> {
  const res = await api.get<SyntaxDetectionResponse>(
    `/projects/${projectId}/bug-detection/syntax-detection`,
  );
  return res.data;
}

export async function getStaticCodeAnalysis(
  projectId: number,
): Promise<StaticCodeAnalysisResponse> {
  const res = await api.get<StaticCodeAnalysisResponse>(
    `/projects/${projectId}/bug-detection/static-analysis`,
  );
  return res.data;
}

export async function getDependencyAnalysis(
  projectId: number,
): Promise<DependencyAnalysisResponse> {
  const res = await api.get<DependencyAnalysisResponse>(
    `/projects/${projectId}/bug-detection/dependency-analysis`,
  );
  return res.data;
}

export async function getRuntimeAnalysis(
  projectId: number,
): Promise<RuntimeAnalysisResponse> {
  const res = await api.get<RuntimeAnalysisResponse>(
    `/projects/${projectId}/bug-detection/runtime-analysis`,
  );
  return res.data;
}

export async function getSecurityAnalysis(
  projectId: number,
): Promise<SecurityAnalysisResponse> {
  const res = await api.get<SecurityAnalysisResponse>(
    `/projects/${projectId}/bug-detection/security-analysis`,
  );
  return res.data;
}

export async function getPerformanceAnalysis(
  projectId: number,
): Promise<PerformanceAnalysisResponse> {
  const res = await api.get<PerformanceAnalysisResponse>(
    `/projects/${projectId}/bug-detection/performance-analysis`,
  );
  return res.data;
}

export async function getArchitectureAnalysis(
  projectId: number,
): Promise<ArchitectureAnalysisResponse> {
  const res = await api.get<ArchitectureAnalysisResponse>(
    `/projects/${projectId}/bug-detection/architecture-analysis`,
  );
  return res.data;
}

export async function getBugPrioritization(
  projectId: number,
): Promise<PrioritizationResponse> {
  const res = await api.get<PrioritizationResponse>(
    `/projects/${projectId}/bug-detection/prioritization`,
  );
  return res.data;
}
