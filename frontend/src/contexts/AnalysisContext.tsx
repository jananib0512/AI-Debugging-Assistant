import { createContext, useContext, useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  getAnalyzerValidation,
  getArchitecture,
  getCodeIntelligence,
  getConfiguration,
  getEntryPoints,
  getFrameworks,
  getModules,
  getProjectAnalyzer,
  getProjectInsights,
  getProjectIntelligence,
} from "@/lib/project-analyzer";
import type {
  AnalyzerResponse,
  AnalyzerValidationResponse,
  ArchitectureDetectionResponse,
  ConfigurationIntelligenceResponse,
  EntryPointDetectionResponse,
  FrameworkIntelligenceResponse,
  ModuleDetectionResponse,
  ProjectInsightsResponse,
  ProjectIntelligenceResponse,
  SourceCodeIntelligenceResponse,
} from "@/types/project-analyzer";

interface AnalysisState {
  data: AnalyzerResponse | null;
  entryPoints: EntryPointDetectionResponse | null;
  architecture: ArchitectureDetectionResponse | null;
  modules: ModuleDetectionResponse | null;
  frameworks: FrameworkIntelligenceResponse | null;
  configIntel: ConfigurationIntelligenceResponse | null;
  projectIntel: ProjectIntelligenceResponse | null;
  projectInsights: ProjectInsightsResponse | null;
  validationResult: AnalyzerValidationResponse | null;
  codeIntel: SourceCodeIntelligenceResponse | null;
  loading: boolean;
  analyzing: boolean;
  error: string | null;
}

interface AnalysisContextValue extends AnalysisState {
  refresh: (isRefresh?: boolean) => void;
  projectId: string | undefined;
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

export function AnalysisProvider({ projectId, children }: { projectId: string | undefined; children: ReactNode }) {
  const [data, setData] = useState<AnalyzerResponse | null>(null);
  const [entryPoints, setEntryPoints] = useState<EntryPointDetectionResponse | null>(null);
  const [architecture, setArchitecture] = useState<ArchitectureDetectionResponse | null>(null);
  const [modules, setModules] = useState<ModuleDetectionResponse | null>(null);
  const [frameworks, setFrameworks] = useState<FrameworkIntelligenceResponse | null>(null);
  const [configIntel, setConfigIntel] = useState<ConfigurationIntelligenceResponse | null>(null);
  const [projectIntel, setProjectIntel] = useState<ProjectIntelligenceResponse | null>(null);
  const [projectInsights, setProjectInsights] = useState<ProjectInsightsResponse | null>(null);
  const [validationResult, setValidationResult] = useState<AnalyzerValidationResponse | null>(null);
  const [codeIntel, setCodeIntel] = useState<SourceCodeIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef(false);

  const fetchAnalysis = useCallback(async (isRefresh = false) => {
    if (!projectId) return;
    if (isRefresh) setAnalyzing(true);
    else if (!fetchedRef.current) setLoading(true);
    setError(null);

    try {
      const [
        result,
        epResult,
        archResult,
        modResult,
        fwResult,
        ciResult,
        piResult,
        insightsResult,
        validationResultData,
        codeIntelResult,
      ] = await Promise.all([
        getProjectAnalyzer(Number(projectId)),
        getEntryPoints(Number(projectId)),
        getArchitecture(Number(projectId)),
        getModules(Number(projectId)),
        getFrameworks(Number(projectId)),
        getConfiguration(Number(projectId)),
        getProjectIntelligence(Number(projectId)),
        getProjectInsights(Number(projectId)),
        getAnalyzerValidation(Number(projectId)),
        getCodeIntelligence(Number(projectId)),
      ]);
      setData(result);
      setEntryPoints(epResult);
      setArchitecture(archResult);
      setModules(modResult);
      setFrameworks(fwResult);
      setConfigIntel(ciResult);
      setProjectIntel(piResult);
      setProjectInsights(insightsResult);
      setValidationResult(validationResultData);
      setCodeIntel(codeIntelResult);
      fetchedRef.current = true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze project";
      setError(msg);
    } finally {
      setLoading(false);
      setAnalyzing(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) {
      fetchAnalysis();
    }
  }, [projectId, fetchAnalysis]);

  return (
    <AnalysisContext.Provider
      value={{
        data, entryPoints, architecture, modules, frameworks,
        configIntel, projectIntel, projectInsights,
        validationResult, codeIntel,
        loading, analyzing, error,
        refresh: fetchAnalysis,
        projectId,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error("useAnalysis must be used within AnalysisProvider");
  return ctx;
}
