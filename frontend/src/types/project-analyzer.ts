export interface DetectedEntryPoint {
  path: string;
  file_name: string;
  type: string;
}

export interface DetectedDirectory {
  name: string;
  path: string;
  purpose: string;
}

export interface ProjectAnalysis {
  project_type: string;
  project_type_reason: string;
  architecture: string;
  architecture_reason: string;
  entry_points: DetectedEntryPoint[];
  important_directories: DetectedDirectory[];
  detected_modules: string[];
  frontend_framework: string | null;
  backend_framework: string | null;
  database_detected: string[];
  has_tests: boolean;
  has_docker: boolean;
  has_ci_cd: boolean;
  structure_summary: string;
  analyzed_at: string;
}

export interface TechnologyStack {
  languages: string[];
  frameworks: string[];
  databases: string[];
}

export interface FolderSummary {
  frontend: number;
  backend: number;
  source: number;
  config: number;
  assets: number;
  docs: number;
  tests: number;
  scripts: number;
  other: number;
}

export interface ConfigSummary {
  has_package_json: boolean;
  has_requirements_txt: boolean;
  has_dockerfile: boolean;
  has_docker_compose: boolean;
  has_readme: boolean;
  has_pyproject_toml: boolean;
  has_env_example: boolean;
  has_gitignore: boolean;
}

export interface AnalyzerResponse {
  project_name: string;
  project_type: string;
  workspace_status: string;
  technology_stack: TechnologyStack;
  total_files: number;
  total_folders: number;
  workspace_size: number;
  folder_summary: FolderSummary;
  config_summary: ConfigSummary;
  workspace_summary: string;
  analyzed_at: string;
}

export interface DetectedEntryPointInfo {
  entry_file: string;
  framework: string;
  project_type: string;
  confidence: number;
  reason: string;
}

export interface EntryPointDetectionResponse {
  primary_entry_point: DetectedEntryPointInfo | null;
  alternative_entry_points: DetectedEntryPointInfo[];
  total_entry_points: number;
  analyzed_at: string;
}

export interface ArchitectureLayerInfo {
  name: string;
  directories: string[];
}

export interface DetectedArchitectureInfo {
  architecture: string;
  confidence: number;
  reason: string;
  evidence: string[];
}

export interface ArchitectureDetectionResponse {
  primary_architecture: DetectedArchitectureInfo | null;
  alternative_architectures: DetectedArchitectureInfo[];
  detected_layers: ArchitectureLayerInfo[];
  analyzed_at: string;
}

export interface DetectedModuleInfo {
  module_name: string;
  status: string;
  detected_folder: string | null;
  confidence: number;
  reason: string;
}

export interface ModuleSummaryInfo {
  total_modules: number;
  detected_count: number;
  missing_count: number;
  core_detected: number;
  core_total: number;
  optional_detected: number;
  optional_total: number;
}

export interface ModuleDetectionResponse {
  modules: DetectedModuleInfo[];
  summary: ModuleSummaryInfo;
  analyzed_at: string;
}

export interface DetectedTechnology {
  name: string;
  version: string | null;
  confidence: number;
  reason: string;
}

export interface CategorizedTechnology {
  name: string;
  version: string | null;
  confidence: number;
  reason: string;
  category: string;
  detection_source: string;
}

export interface TechnologyStackDetail {
  languages: DetectedTechnology[];
  frameworks: DetectedTechnology[];
  runtimes: DetectedTechnology[];
  package_managers: DetectedTechnology[];
  build_tools: DetectedTechnology[];
  databases: DetectedTechnology[];
  containers: DetectedTechnology[];
  categorized: Record<string, CategorizedTechnology[]>;
}

export interface FrameworkHealthInfo {
  score: number;
  label: string;
  details: Record<string, number>;
}

export interface CompatibilityCheckInfo {
  framework: string;
  other_framework: string;
  status: string;
  note: string;
}

export interface FeatureDetectionInfo {
  name: string;
  confidence: number;
  evidence: string[];
}

export interface DependencyGraphLayer {
  layer: string;
  label: string;
  technologies: string[];
}

export interface FrameworkEvidenceInfo {
  name: string;
  source: string;
  confidence: number;
}

export interface FrameworkDetailInfo {
  name: string;
  version: string | null;
  confidence: number;
  reason: string;
  category: string;
  detection_source: string;
  health: FrameworkHealthInfo | null;
  role: string;
}

export interface FrameworkIntelligenceResponse {
  technology_stack: TechnologyStackDetail;
  primary_language: DetectedTechnology | null;
  primary_framework: DetectedTechnology | null;
  frameworks: FrameworkDetailInfo[];
  compatibility: CompatibilityCheckInfo[];
  features: FeatureDetectionInfo[];
  dependency_graph: DependencyGraphLayer[];
  evidence: FrameworkEvidenceInfo[];
  project_type: string;
  analyzed_at: string;
}

export interface ConfigFileInfo {
  file_name: string;
  status: string;
  category: string;
  purpose: string;
  confidence: number;
  detection_source: string;
  recommendation: string | null;
  path: string | null;
}

export interface ConfigWarning {
  message: string;
  severity: string;
  file_name: string | null;
}

export interface ConfigHealthInfo {
  score: number;
  label: string;
}

export interface DependencyValidationInfo {
  type: string;
  package: string;
  severity: string;
  detail: string;
}

export interface EnvironmentValidationInfo {
  type: string;
  file: string | null;
  severity: string;
  detail: string;
}

export interface DockerValidationInfo {
  has_dockerfile: boolean;
  has_docker_compose: boolean;
  multi_stage_build: boolean;
  production_ready: boolean;
  detail: string;
}

export interface CicdInfo {
  platform: string;
  configured: boolean;
  file: string | null;
}

export interface SecurityCheckInfo {
  type: string;
  severity: string;
  detail: string;
}

export interface ReadinessScores {
  configuration_health: number;
  readiness: number;
  security: number;
  maintainability: number;
}

export interface CodeMetricsInfo {
  total_lines: number;
  code_lines: number;
  blank_lines: number;
  comment_lines: number;
  comment_ratio: number;
  code_files: number;
  avg_file_size: number;
  largest_file: string;
  largest_file_size: number;
  smallest_file: string;
  smallest_file_size: number;
  avg_function_length: number;
  avg_class_size: number;
}

export interface ComplexityInfo {
  total_functions: number;
  total_classes: number;
  avg_cyclomatic_complexity: number;
  max_complexity: number;
  low_count: number;
  medium_count: number;
  high_count: number;
  critical_count: number;
}

export interface ComplexityDistributionItem {
  label: string;
  count: number;
  percentage: number;
}

export interface MaintainabilityGradeInfo {
  score: number;
  grade: string;
}

export interface CodeOrganizationIssue {
  type: string;
  detail: string;
  severity: string;
}

export interface CodeStyleIssue {
  type: string;
  detail: string;
  severity: string;
}

export interface LanguageDistribution {
  language: string;
  file_count: number;
  percentage: number;
}

export interface ProjectStats {
  python_files: number;
  javascript_files: number;
  html_files: number;
  css_files: number;
  json_files: number;
  markdown_files: number;
  images: number;
  videos: number;
  other_assets: number;
}

export interface LanguageLocItem {
  language: string;
  lines: number;
  percentage: number;
}

export interface LargestDirectoryItem {
  path: string;
  file_count: number;
  size: number;
}

export interface LargestFileItem {
  path: string;
  size: number;
  lines: number;
}

export interface MetricRecommendation {
  type: string;
  detail: string;
}

export interface ProjectIntelligenceResponse {
  code_metrics: CodeMetricsInfo;
  complexity: ComplexityInfo;
  complexity_distribution: ComplexityDistributionItem[];
  maintainability: MaintainabilityGradeInfo;
  code_organization: CodeOrganizationIssue[];
  code_style: CodeStyleIssue[];
  project_stats: ProjectStats;
  language_distribution: LanguageDistribution[];
  language_loc: LanguageLocItem[];
  largest_directories: LargestDirectoryItem[];
  largest_files: LargestFileItem[];
  recommendations: MetricRecommendation[];
  analyzed_at: string;
}

export interface HealthScoreInfo {
  score: number;
  classification: string;
}

export interface InsightStrength {
  category: string;
  detail: string;
}

export interface InsightWeakness {
  category: string;
  detail: string;
}

export interface RiskAnalysisInfo {
  level: string;
  score: number;
  explanation: string;
}

export interface ScalabilityInfo {
  level: string;
  reason: string;
}

export interface PerformanceInsight {
  type: string;
  detail: string;
}

export interface SecurityInsight {
  type: string;
  severity: string;
  detail: string;
}

export interface ProjectCodeQualityInsight {
  type: string;
  detail: string;
}

export interface RecommendedAction {
  action: string;
  priority: string;
}

export interface ReadinessDetail {
  category: string;
  score: number;
}

export interface ProjectInsightsResponse {
  health_score: HealthScoreInfo;
  ai_summary: string[];
  strengths: InsightStrength[];
  weaknesses: InsightWeakness[];
  risk_analysis: RiskAnalysisInfo;
  maintainability: MaintainabilityGradeInfo;
  maintainability_explanation: string;
  scalability: ScalabilityInfo;
  performance_insights: PerformanceInsight[];
  security_insights: SecurityInsight[];
  code_quality_insights: ProjectCodeQualityInsight[];
  recommended_actions: RecommendedAction[];
  readiness_scores: ReadinessDetail[];
  analyzed_at: string;
}

export interface CodeIntelligenceFunctionParam {
  name: string;
  type: string | null;
  default: string | null;
}

export interface CodeIntelligenceFunction {
  name: string;
  file_path: string;
  line_start: number;
  line_end: number;
  parameters: CodeIntelligenceFunctionParam[];
  return_type: string | null;
  decorators: string[];
  is_async: boolean;
  is_static: boolean;
  is_generator: boolean;
  visibility: string;
  parent_class: string | null;
}

export interface CodeIntelligenceProperty {
  name: string;
  type: string | null;
  visibility: string;
  is_static: boolean;
}

export interface CodeIntelligenceClass {
  name: string;
  file_path: string;
  line_start: number;
  line_end: number;
  base_classes: string[];
  inherited_classes: string[];
  methods: CodeIntelligenceFunction[];
  properties: CodeIntelligenceProperty[];
  decorators: string[];
  visibility: string;
  is_abstract: boolean;
}

export interface CodeIntelligenceImport {
  source: string | null;
  names: string[];
  is_external: boolean;
  is_duplicate: boolean;
  line: number;
}

export interface CodeIntelligenceVariable {
  name: string;
  file_path: string;
  line: number;
  type: string | null;
  is_constant: boolean;
}

export interface CodeIntelligenceEnum {
  name: string;
  file_path: string;
  line: number;
  values: string[];
}

export interface CodeIntelligenceInterface {
  name: string;
  file_path: string;
  line: number;
  properties: string[];
  methods: string[];
}

export interface CodeIntelligenceFileSummary {
  path: string;
  language: string;
  lines_of_code: number;
  total_lines: number;
  comment_lines: number;
  blank_lines: number;
  functions: number;
  classes: number;
  imports: number;
  exports: number;
  complexity: number;
  maintainability_score: number;
  encoding: string;
}

export interface CodeIntelligenceModule {
  name: string;
  path: string;
  files: string[];
  classes: string[];
  functions: string[];
  submodules: string[];
}

export interface CodeIntelligenceSummary {
  total_files: number;
  total_classes: number;
  total_functions: number;
  total_imports: number;
  total_external_imports: number;
  total_enums: number;
  total_interfaces: number;
  total_variables: number;
  total_constants: number;
  total_modules: number;
  total_comments: number;
  total_blank_lines: number;
  total_empty_files: number;
  total_duplicate_files: number;
  average_file_size: number;
  average_lines_of_code: number;
  average_complexity: number;
  average_maintainability: number;
  largest_file: string;
  largest_file_size: number;
  smallest_file: string;
  smallest_file_size: number;
  languages: string[];
}

export interface SourceCodeIntelligenceResponse {
  summary: CodeIntelligenceSummary;
  files: CodeIntelligenceFileSummary[];
  classes: CodeIntelligenceClass[];
  functions: CodeIntelligenceFunction[];
  imports: CodeIntelligenceImport[];
  enums: CodeIntelligenceEnum[];
  interfaces: CodeIntelligenceInterface[];
  variables: CodeIntelligenceVariable[];
  modules: CodeIntelligenceModule[];
  analyzed_at: string;
}

export interface ConsistencyCheck {
  check_name: string;
  status: string;
  detail: string;
  modules_involved: string[];
}

export interface SelfHealingAction {
  check_name: string;
  action: string;
  detail: string;
}

export interface ValidationReportItem {
  category: string;
  status: string;
  checks: ConsistencyCheck[];
}

export interface AnalyzerValidationResponse {
  consistency_score: number;
  classification: string;
  passed_checks: number;
  failed_checks: number;
  warnings: number;
  critical_errors: number;
  checks: ConsistencyCheck[];
  validation_report: ValidationReportItem[];
  self_healing: SelfHealingAction[];
  recommendations: string[];
  analyzed_at: string;
}

export interface QualityScoreInfo {
  score: number;
  label: string;
}

export interface CodeQualityIssue {
  type: string;
  severity: string;
  description: string;
  reason: string;
  suggested_fix: string;
  priority: string;
  affected_file: string;
  affected_function: string | null;
  line: number | null;
}

export interface CodeQualityCheck {
  check_name: string;
  status: string;
  severity: string;
  count: number;
  issues: CodeQualityIssue[];
}

export interface CodeQualityInsight {
  message: string;
  type: string;
  sentiment: string;
  module: string | null;
  files: string[];
  category: string;
}

export interface CodeQualityAiRecommendation {
  action: string;
  impact: string;
  effort: string;
  detail: string;
  priority: string;
  estimated_improvement: string;
  affected_file_count: number;
  affected_files: string[];
  category: string;
}

export interface CodeQualityAiSummary {
  summary: string;
  strengths: string[];
  weaknesses: string[];
  architecture: string;
  recommended_focus: string;
}

export interface CodeQualitySeverityCount {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface CodeQualityTopFile {
  path: string;
  issue_count: number;
  score: number;
}

export interface CodeQualityLanguageBreakdown {
  language: string;
  file_count: number;
  issue_count: number;
  avg_complexity: number;
}

export interface CodeQualityResponse {
  overall_score: QualityScoreInfo;
  maintainability_score: QualityScoreInfo;
  readability_score: QualityScoreInfo;
  complexity_score: QualityScoreInfo;
  documentation_score: QualityScoreInfo;
  security_score: QualityScoreInfo;
  technical_debt_score: QualityScoreInfo;
  checks: CodeQualityCheck[];
  insights: CodeQualityInsight[];
  recommendations: CodeQualityAiRecommendation[];
  severity_counts: CodeQualitySeverityCount;
  total_issues: number;
  top_problematic_files: CodeQualityTopFile[];
  top_clean_files: CodeQualityTopFile[];
  language_breakdown: CodeQualityLanguageBreakdown[];
  ai_summary: CodeQualityAiSummary | null;
  analyzed_at: string;
}

export interface ConfigurationIntelligenceResponse {
  detected_files: ConfigFileInfo[];
  missing_files: ConfigFileInfo[];
  dependency_validation: DependencyValidationInfo[];
  environment_validation: EnvironmentValidationInfo[];
  docker_validation: DockerValidationInfo;
  cicd: CicdInfo[];
  security_checks: SecurityCheckInfo[];
  scores: ReadinessScores;
  warnings: ConfigWarning[];
  recommendations: string[];
  health: ConfigHealthInfo;
  readiness_score: number;
  analyzed_at: string;
}
