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

export interface FileMetricScores {
  overall: number;
  maintainability: number;
  complexity: number;
  readability: number;
  documentation: number;
  security: number;
}

export interface FileAnalysisIssue {
  type: string;
  severity: string;
  description: string;
  reason: string;
  suggested_fix: string;
  priority: string;
  line: number | null;
}

export interface FileAnalysisDetail {
  path: string;
  file_name: string;
  extension: string;
  language: string;
  size: number;
  total_lines: number;
  code_lines: number;
  blank_lines: number;
  comment_lines: number;
  functions: number;
  classes: number;
  imports: number;
  complexity: number;
  scores: FileMetricScores;
  health: string;
  tags: string[];
  ai_summary: string;
  issues: FileAnalysisIssue[];
}

export interface FileAnalysisResponse {
  files: FileAnalysisDetail[];
  total_files: number;
  language_counts: Record<string, number>;
  analyzed_at: string;
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

export interface FunctionClassIssue {
  type: string;
  severity: string;
  description: string;
  reason: string;
  suggested_fix: string;
  line: number | null;
}

export interface FunctionParameter {
  name: string;
  type: string | null;
  default_value: string | null;
  is_optional: boolean;
}

export interface FunctionDetail {
  name: string;
  file_path: string;
  file_name: string;
  language: string;
  module: string;
  parameters: FunctionParameter[];
  return_type: string | null;
  decorators: string[];
  is_async: boolean;
  is_generator: boolean;
  is_lambda: boolean;
  visibility: string;
  lines_of_code: number;
  cyclomatic_complexity: number;
  maintainability_score: number;
  has_documentation: boolean;
  issue_count: number;
  health_status: string;
  issues: FunctionClassIssue[];
  ai_insight: string;
}

export interface MethodDetail {
  name: string;
  parent_class: string;
  parameters: FunctionParameter[];
  return_type: string | null;
  decorators: string[];
  is_async: boolean;
  is_static: boolean;
  is_classmethod: boolean;
  is_property: boolean;
  visibility: string;
  lines_of_code: number;
  cyclomatic_complexity: number;
  maintainability_score: number;
  has_documentation: boolean;
  issue_count: number;
  health_status: string;
  issues: FunctionClassIssue[];
  ai_insight: string;
}

export interface ClassDetail {
  name: string;
  file_path: string;
  file_name: string;
  language: string;
  module: string;
  base_classes: string[];
  parent_class: string | null;
  child_classes: string[];
  methods: MethodDetail[];
  properties: string[];
  constructors: MethodDetail[];
  decorators: string[];
  interfaces: string[];
  is_abstract: boolean;
  lines_of_code: number;
  complexity: number;
  maintainability_score: number;
  has_documentation: boolean;
  issue_count: number;
  health_status: string;
  issues: FunctionClassIssue[];
  ai_insight: string;
}

export interface FunctionRelationship {
  name: string;
  file_path: string;
  callers: string[];
  called_functions: string[];
  is_recursive: boolean;
  is_unused: boolean;
  is_duplicate: boolean;
  cross_file_calls: string[];
}

export interface ClassRelationship {
  name: string;
  file_path: string;
  inheritance: string[];
  composition: string[];
  aggregation: string[];
  dependency: string[];
  association: string[];
}

export interface FunctionClassStats {
  total_functions: number;
  total_classes: number;
  total_methods: number;
  average_complexity: number;
  average_maintainability: number;
  total_issues: number;
  language_breakdown: Record<string, number>;
  health_counts: Record<string, number>;
  unused_functions: number;
  recursive_functions: number;
  undocumented_count: number;
}

export interface FunctionClassResponse {
  functions: FunctionDetail[];
  classes: ClassDetail[];
  relationships: FunctionRelationship[];
  class_relationships: ClassRelationship[];
  stats: FunctionClassStats;
  ai_insights: string[];
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

export interface ImportRecord {
  module: string;
  symbol: string;
  alias: string | null;
  source_file: string;
  target_file: string | null;
  import_type: string;
  language: string;
  is_relative: boolean;
  is_wildcard: boolean;
  is_dynamic: boolean;
  is_unused: boolean;
  is_duplicate: boolean;
  is_broken: boolean;
  line_number: number | null;
  resolved: boolean;
  confidence: number;
}

export interface FileDependency {
  source_file: string;
  target_file: string | null;
  target_module: string;
  dependency_type: string;
  language: string;
  import_count: number;
  is_external: boolean;
  is_circular: boolean;
  is_broken: boolean;
  is_unused: boolean;
}

export interface CircularDependency {
  chain: string[];
  files: string[];
  severity: string;
  suggested_resolution: string;
}

export interface DependencyGraphNode {
  id: string;
  label: string;
  type: string;
  language: string;
  file_count: number;
  import_count: number;
}

export interface DependencyGraphEdge {
  source: string;
  target: string;
  weight: number;
  type: string;
}

export interface DependencyGraph {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
}

export interface DependencyMetrics {
  total_files: number;
  total_imports: number;
  total_dependencies: number;
  external_libraries: number;
  internal_libraries: number;
  broken_dependencies: number;
  unused_imports: number;
  circular_dependencies: number;
  average_dependency_depth: number;
  coupling_score: number;
  language_breakdown: Record<string, number>;
  dependency_type_counts: Record<string, number>;
}

export interface FileIntelligenceHealth {
  overall: number;
  maintainability: number;
  complexity: number;
  documentation: number;
  security: number;
  readability: number;
}

export interface FileIntelligenceIssue {
  type: string;
  severity: string;
  description: string;
  reason: string;
  suggested_fix: string;
}

export interface FileIntelligenceDetail {
  file_name: string;
  path: string;
  extension: string;
  language: string;
  encoding: string;
  size: number;
  last_modified: string;
  total_lines: number;
  code_lines: number;
  blank_lines: number;
  comment_lines: number;
  functions: number;
  classes: number;
  imports: number;
  complexity: number;
  health: FileIntelligenceHealth;
  classification: string;
  tags: string[];
  issues: FileIntelligenceIssue[];
  ai_summary: string;
}

export interface FileIntelligenceStats {
  total_files: number;
  total_classes: number;
  total_functions: number;
  total_imports: number;
  total_lines: number;
  total_code_lines: number;
  total_blank_lines: number;
  total_comment_lines: number;
  language_counts: Record<string, number>;
  classification_counts: Record<string, number>;
  health_distribution: Record<string, number>;
  average_complexity: number;
  average_maintainability: number;
  total_issues: number;
  large_files: number;
  empty_files: number;
  duplicate_files: number;
}

export interface FileIntelligenceResponse {
  files: FileIntelligenceDetail[];
  stats: FileIntelligenceStats;
  analyzed_at: string;
}

export interface ImportDependencyResponse {
  imports: ImportRecord[];
  dependencies: FileDependency[];
  circular_dependencies: CircularDependency[];
  graph: DependencyGraph;
  metrics: DependencyMetrics;
  insights: string[];
  recommendations: string[];
  analyzed_at: string;
}

export interface FuncClassIntelligenceParam {
  name: string;
  type: string | null;
  default_value: string | null;
  is_optional: boolean;
}

export interface FuncClassIntelligenceIssue {
  type: string;
  severity: string;
  description: string;
  reason: string;
  suggested_fix: string;
  line: number | null;
}

export interface FuncClassIntelligenceFunc {
  name: string;
  file_path: string;
  file_name: string;
  language: string;
  module: string;
  parameters: FuncClassIntelligenceParam[];
  return_type: string | null;
  decorators: string[];
  is_async: boolean;
  is_generator: boolean;
  is_lambda: boolean;
  visibility: string;
  lines_of_code: number;
  start_line: number;
  end_line: number;
  cyclomatic_complexity: number;
  maintainability_score: number;
  has_documentation: boolean;
  has_type_hints: boolean;
  deepest_nesting: number;
  issue_count: number;
  health_status: string;
  issues: FuncClassIntelligenceIssue[];
  callers: string[];
  called_functions: string[];
  is_recursive: boolean;
  is_unused: boolean;
  cross_file_calls: string[];
  ai_insight: string;
}

export interface FuncClassIntelligenceMethod {
  name: string;
  parent_class: string;
  parameters: FuncClassIntelligenceParam[];
  return_type: string | null;
  decorators: string[];
  is_async: boolean;
  is_static: boolean;
  is_classmethod: boolean;
  is_property: boolean;
  visibility: string;
  lines_of_code: number;
  start_line: number;
  end_line: number;
  cyclomatic_complexity: number;
  maintainability_score: number;
  has_documentation: boolean;
  has_type_hints: boolean;
  issue_count: number;
  health_status: string;
  issues: FuncClassIntelligenceIssue[];
  ai_insight: string;
}

export interface FuncClassIntelligenceClass {
  name: string;
  file_path: string;
  file_name: string;
  language: string;
  module: string;
  base_classes: string[];
  parent_class: string | null;
  child_classes: string[];
  methods: FuncClassIntelligenceMethod[];
  properties: string[];
  class_variables: string[];
  constructors: FuncClassIntelligenceMethod[];
  decorators: string[];
  interfaces: string[];
  is_abstract: boolean;
  has_nested_classes: boolean;
  lines_of_code: number;
  complexity: number;
  maintainability_score: number;
  has_documentation: boolean;
  issue_count: number;
  health_status: string;
  issues: FuncClassIntelligenceIssue[];
  coupling: number;
  method_count: number;
  property_count: number;
  ai_insight: string;
}

export interface FuncClassRelationship {
  type: string;
  source: string;
  target: string;
  source_file: string;
  target_file: string;
  strength: string;
}

export interface FuncClassIntelligenceStats {
  total_functions: number;
  total_classes: number;
  total_methods: number;
  average_complexity: number;
  average_maintainability: number;
  total_issues: number;
  language_breakdown: Record<string, number>;
  health_counts: Record<string, number>;
  unused_functions: number;
  recursive_functions: number;
  undocumented_count: number;
  deep_nesting_count: number;
  missing_type_hints_count: number;
}

export interface FuncClassIntelligenceResponse {
  functions: FuncClassIntelligenceFunc[];
  classes: FuncClassIntelligenceClass[];
  relationships: FuncClassRelationship[];
  stats: FuncClassIntelligenceStats;
  ai_insights: string[];
  analyzed_at: string;
}

export interface CallGraphNode {
  id: string;
  name: string;
  type: string;
  file_path: string;
  module: string;
  language: string;
  line_number: number;
  complexity: number;
  maintainability: number;
  call_depth: number;
  is_entry_point: boolean;
  is_recursive: boolean;
  is_dead: boolean;
  is_library: boolean;
  is_framework: boolean;
}

export interface CallGraphEdge {
  source: string;
  target: string;
  call_type: string;
  call_count: number;
  is_cross_file: boolean;
  is_cross_module: boolean;
  is_recursive: boolean;
  is_library: boolean;
  file_path: string;
  line_number: number;
}

export interface ExecutionFlow {
  id: string;
  name: string;
  description: string;
  flow_type: string;
  entry_node: string;
  exit_node: string;
  path: string[];
  depth: number;
  is_complete: boolean;
  issues: string[];
}

export interface CallGraphIssue {
  type: string;
  severity: string;
  description: string;
  nodes: string[];
  detail: string;
}

export interface CallGraphStats {
  total_nodes: number;
  total_edges: number;
  total_entry_points: number;
  total_execution_flows: number;
  total_issues: number;
  average_call_depth: number;
  max_call_depth: number;
  total_unused: number;
  total_recursive: number;
  total_circular: number;
  total_dead_chains: number;
  total_orphans: number;
  total_broken_paths: number;
  language_breakdown: Record<string, number>;
  node_type_counts: Record<string, number>;
}

export interface CallGraphResponse {
  nodes: CallGraphNode[];
  edges: CallGraphEdge[];
  execution_flows: ExecutionFlow[];
  entry_points: CallGraphNode[];
  stats: CallGraphStats;
  issues: CallGraphIssue[];
  ai_insights: string[];
  analyzed_at: string;
}

export interface SemanticComponent {
  id: string;
  name: string;
  type: string;
  sub_type: string;
  file_path: string;
  module: string;
  language: string;
  line_number: number;
  purpose: string;
  responsibility: string;
  role: string;
  business_context: string;
  summary: string;
  classification_reason: string;
  confidence: number;
  complexity: number;
  is_entry_point: boolean;
  is_exported: boolean;
  is_test: boolean;
  is_abstract: boolean;
  is_deprecated: boolean;
  has_ai_summary: boolean;
}

export interface SemanticRelationship {
  source_id: string;
  target_id: string;
  relationship_type: string;
  description: string;
  strength: number;
  is_direct: boolean;
  file_path: string;
  line_number: number;
}

export interface SemanticSymbol {
  name: string;
  kind: string;
  file_path: string;
  module: string;
  line_number: number;
  is_definition: boolean;
  is_exported: boolean;
  is_imported: boolean;
  resolved_target: string;
  aliases: string[];
}

export interface BusinessFlow {
  id: string;
  name: string;
  description: string;
  flow_type: string;
  confidence: string;
  entry_components: string[];
  exit_components: string[];
  path: string[];
  components: string[];
  verified: boolean;
}

export interface SemanticCodeIssue {
  type: string;
  severity: string;
  component_id: string;
  description: string;
  detail: string;
  suggestion: string;
}

export interface SemanticSimilarity {
  component_a_id: string;
  component_b_id: string;
  similarity_type: string;
  score: number;
  description: string;
  shared_patterns: string[];
}

export interface SemanticStats {
  total_components: number;
  total_files: number;
  total_classes: number;
  total_functions: number;
  type_breakdown: Record<string, number>;
  language_breakdown: Record<string, number>;
  total_relationships: number;
  total_business_flows: number;
  total_verified_flows: number;
  total_symbols: number;
  total_issues: number;
  total_similarities: number;
  component_type_counts: Record<string, number>;
}

export interface UnderstandingScore {
  overall: number;
  architecture: number;
  business_logic: number;
  dependencies: number;
  code_organization: number;
  execution_flow: number;
  semantic_relationships: number;
  maintainability: number;
  readability: number;
  has_entry_points: boolean;
  has_controllers: boolean;
  has_services: boolean;
  has_repositories: boolean;
  has_ml_components: boolean;
  has_forecast_components: boolean;
  component_coverage: number;
  flow_capture_rate: number;
  insight_count: number;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  sub_type: string;
  file_path: string;
  module: string;
  importance: number;
  group: string;
  details: Record<string, unknown>;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
  description: string;
}

export interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

export interface BusinessComponent {
  id: string;
  name: string;
  type: string;
  file_path: string;
  module: string;
  confidence: number;
  description: string;
  related_components: string[];
}

export interface SemanticResponse {
  components: SemanticComponent[];
  relationships: SemanticRelationship[];
  symbols: SemanticSymbol[];
  business_flows: BusinessFlow[];
  issues: SemanticCodeIssue[];
  similarities: SemanticSimilarity[];
  stats: SemanticStats;
  understanding_score: UnderstandingScore | null;
  knowledge_graph: KnowledgeGraph | null;
  business_components: BusinessComponent[];
  ai_insights: string[];
  analyzed_at: string;
}

export interface UnifiedHealthMetrics {
  overall_health: number;
  overall_quality: number;
  architecture_health: number;
  dependency_health: number;
  security_health: number;
  performance_health: number;
  maintainability: number;
  readiness: number;
  technical_debt: number;
  ai_confidence: number;
}

export interface UnifiedProjectScore {
  overall_score: number;
  architecture_score: number;
  code_quality_score: number;
  dependency_score: number;
  security_score: number;
  file_quality_score: number;
  function_quality_score: number;
  configuration_score: number;
  semantic_score: number;
}

export interface GlobalInsight {
  type: string;
  label: string;
  value: string;
  severity: string;
  source: string;
  detail: string;
}

export interface ExecutiveSummary {
  project_summary: string;
  architecture_summary: string;
  business_logic_summary: string;
  risk_summary: string;
  security_summary: string;
  recommendation_summary: string;
  future_improvements: string[];
}

export interface KnowledgeHubItem {
  category: string;
  label: string;
  value: string;
  link: string;
  count: number;
}

export interface HealthMapModule {
  name: string;
  path: string;
  status: string;
  issues: number;
  score: number;
}

export interface ProjectTimelineStage {
  stage: string;
  label: string;
  status: string;
  details: string;
  score: number;
}

export interface GlobalSearchResult {
  category: string;
  items: Record<string, unknown>[];
  total: number;
}

export interface UnifiedIntelligenceResponse {
  health: UnifiedHealthMetrics;
  scores: UnifiedProjectScore;
  insights: GlobalInsight[];
  executive_summary: ExecutiveSummary;
  knowledge_hub: KnowledgeHubItem[];
  health_map: HealthMapModule[];
  timeline: ProjectTimelineStage[];
  search_results: Record<string, GlobalSearchResult>;
  analyzed_at: string;
}

export interface RiskScore {
  overall_risk: number;
  risk_level: string;
  confidence_score: number;
  project_stability: number;
  maintainability_risk: number;
  architecture_risk: number;
  dependency_risk: number;
  security_risk: number;
  performance_risk: number;
}

export interface RiskImpact {
  business_impact: string;
  technical_impact: string;
  recommended_priority: string;
}

export interface RiskItem {
  name: string;
  type: string;
  severity: string;
  affected_files: string[];
  affected_classes: string[];
  affected_functions: string[];
  impact: RiskImpact;
  detail: string;
  recommendation: string;
}

export interface RiskHeatmapItem {
  name: string;
  path: string;
  category: string;
  risk_score: number;
  risk_level: string;
  top_risks: string[];
}

export interface RiskSummary {
  highest_risk_module: string;
  highest_risk_area: string;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_text: string;
  prioritized_recommendations: string[];
}

export interface RiskIntelligenceResponse {
  risk_score: RiskScore;
  risks: RiskItem[];
  heatmap: RiskHeatmapItem[];
  summary: RiskSummary;
  search_results: Record<string, unknown[]>;
  analyzed_at: string;
}

export interface SecurityScore {
  overall_security_score: number;
  security_health: number;
  security_confidence: number;
  security_readiness: number;
  risk_level: string;
}

export interface SecurityFinding {
  name: string;
  type: string;
  severity: string;
  affected_files: string[];
  affected_functions: string[];
  detail: string;
  business_impact: string;
  technical_impact: string;
  recommended_fix: string;
}

export interface DependencySecurity {
  name: string;
  severity: string;
  detail: string;
  recommendation: string;
}

export interface SecuritySummary {
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_text: string;
  prioritized_recommendations: string[];
}

export interface SecurityIntelligenceResponse {
  security_score: SecurityScore;
  findings: SecurityFinding[];
  dependency_issues: DependencySecurity[];
  summary: SecuritySummary;
  analyzed_at: string;
}


export interface PerformanceScore {
  overall_performance_score: number;
  performance_health: number;
  performance_readiness: number;
  optimization_potential: number;
  ai_confidence: number;
  risk_level: string;
}

export interface PerformanceFinding {
  name: string;
  type: string;
  severity: string;
  estimated_cost: string;
  affected_files: string[];
  affected_functions: string[];
  detail: string;
  optimization_suggestion: string;
  estimated_gain: string;
  complexity_reduction: string;
}

export interface PerformanceSummary {
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_text: string;
  prioritized_recommendations: string[];
}

export interface PerformanceIntelligenceResponse {
  performance_score: PerformanceScore;
  findings: PerformanceFinding[];
  summary: PerformanceSummary;
  analyzed_at: string;
}


export interface MaintainabilityScore {
  overall_maintainability_score: number;
  maintainability_health: number;
  technical_debt_score: number;
  refactoring_readiness: number;
  long_term_stability: number;
  readability: number;
  modularity: number;
  code_organization: number;
  ai_confidence: number;
  risk_level: string;
}

export interface CodeSmellItem {
  name: string;
  type: string;
  severity: string;
  affected_files: string[];
  affected_functions: string[];
  affected_classes: string[];
  description: string;
  refactoring_effort: string;
  ai_suggestion: string;
}

export interface TechnicalDebtEstimate {
  total_debt_hours: number;
  debt_level: string;
  estimated_refactoring_effort: string;
  maintenance_cost: string;
  critical_file_count: number;
  high_file_count: number;
  medium_file_count: number;
  low_file_count: number;
}

export interface ModuleHealthScore {
  file_name: string;
  score: number;
  issues: string[];
  complexity: number;
  cohesion: number;
  coupling: number;
  debt_estimate: string;
}

export interface MaintainabilitySummary {
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  informational_count: number;
  summary_text: string;
  prioritized_recommendations: string[];
}

export interface DocumentationScore {
  overall_documentation_score: number;
  documentation_coverage: number;
  documentation_quality: number;
  developer_readiness: number;
  ai_confidence: number;
  risk_level: string;
}

export interface CodeDocumentationItem {
  type: string;
  name: string;
  file: string;
  documented: boolean;
  documentation_type: string;
  line: number;
  quality: string;
}

export interface ProjectDocItem {
  name: string;
  path: string;
  doc_type: string;
  present: boolean;
  quality: string;
  size: number;
  completeness: string;
}

export interface DocFinding {
  name: string;
  type: string;
  severity: string;
  affected_files: string[];
  affected_functions: string[];
  affected_classes: string[];
  description: string;
  recommendation: string;
  estimated_improvement: string;
}

export interface DocumentationSummary {
  missing_readme: boolean;
  missing_license: boolean;
  missing_contributing: boolean;
  missing_changelog: boolean;
  missing_architecture_docs: boolean;
  coverage_percentage: number;
  documented_functions: number;
  undocumented_functions: number;
  documented_classes: number;
  undocumented_classes: number;
  files_with_comments: number;
  files_without_comments: number;
  summary_text: string;
  prioritized_recommendations: string[];
}

export interface DocumentationIntelligenceResponse {
  documentation_score: DocumentationScore;
  code_documentation: CodeDocumentationItem[];
  project_docs: ProjectDocItem[];
  findings: DocFinding[];
  summary: DocumentationSummary;
  analyzed_at: string;
}

export interface TestScore {
  overall_test_score: number;
  test_coverage: number;
  testing_health: number;
  regression_readiness: number;
  ai_confidence: number;
  risk_level: string;
}

export interface DetectedFramework {
  name: string;
  type: string;
  version: string;
  config_file: string;
  reliability: string;
}

export interface TestFileInfo {
  path: string;
  file_name: string;
  framework: string;
  test_count: number;
  assertion_count: number;
  fixture_count: number;
  mock_count: number;
  test_types: string[];
  naming_quality: string;
  organization_quality: string;
  maintainability: string;
  coverage_estimate: number;
  has_failures: boolean;
  lines_of_code: number;
}

export interface UntestedComponent {
  name: string;
  type: string;
  path: string;
  risk: string;
  reason: string;
  suggested_test_type: string;
  priority: number;
}

export interface MissingTestCase {
  name: string;
  module: string;
  type: string;
  severity: string;
  affected_file: string;
  suggestion: string;
  estimated_impact: string;
}

export interface TestQualityMetrics {
  naming_quality: number;
  assertion_density: number;
  coverage_depth: number;
  organization_score: number;
  maintainability_score: number;
  reliability_score: number;
}

export interface TestRecommendation {
  priority: number;
  category: string;
  title: string;
  description: string;
  suggested_framework: string;
  estimated_coverage_improvement: number;
  affected_modules: string[];
}

export interface TestSummary {
  total_test_files: number;
  total_test_functions: number;
  total_test_classes: number;
  total_assertions: number;
  total_fixtures: number;
  total_mocks: number;
  untested_files: number;
  untested_functions: number;
  untested_classes: number;
  coverage_percentage: number;
  detected_frameworks: string[];
  summary_text: string;
  prioritized_recommendations: string[];
}

export interface TestIntelligenceResponse {
  test_score: TestScore;
  detected_frameworks: DetectedFramework[];
  test_files: TestFileInfo[];
  untested_components: UntestedComponent[];
  missing_test_cases: MissingTestCase[];
  quality_metrics: TestQualityMetrics;
  recommendations: TestRecommendation[];
  summary: TestSummary;
  analyzed_at: string;
}

export interface MaintainabilityIntelligenceResponse {
  maintainability_score: MaintainabilityScore;
  code_smells: CodeSmellItem[];
  technical_debt: TechnicalDebtEstimate;
  module_health: ModuleHealthScore[];
  summary: MaintainabilitySummary;
  analyzed_at: string;
}

export interface RefactoringScore {
  refactoring_score: number;
  project_cleanliness: number;
  code_organization: number;
  debt_reduction_potential: number;
  refactoring_readiness: number;
  ai_confidence: number;
  risk_level: string;
}

export interface ImpactEstimate {
  estimated_files_changed: number;
  estimated_complexity_reduction: string;
  estimated_maintainability_improvement: string;
  estimated_risk: string;
}

export interface RefactoringOpportunity {
  name: string;
  type: string;
  severity: string;
  affected_files: string[];
  affected_classes: string[];
  affected_functions: string[];
  description: string;
  reason: string;
  recommendation: string;
  impact: ImpactEstimate;
  expected_benefit: string;
}

export interface RefactoringSummary {
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_text: string;
  roadmap: string[];
}

export interface RefactoringIntelligenceResponse {
  refactoring_score: RefactoringScore;
  opportunities: RefactoringOpportunity[];
  summary: RefactoringSummary;
  analyzed_at: string;
}

export interface ProductionScore {
  overall_production_score: number;
  deployment_readiness: number;
  operational_readiness: number;
  maintainability_readiness: number;
  ai_confidence: number;
}

export interface ProductionFinding {
  name: string;
  category: string;
  severity: string;
  affected_files: string[];
  affected_components: string[];
  detail: string;
  deployment_impact: string;
  business_impact: string;
  ai_recommendation: string;
}

export interface DeploymentDetection {
  has_dockerfile: boolean;
  has_docker_compose: boolean;
  has_kubernetes: boolean;
  has_helm_charts: boolean;
  has_github_actions: boolean;
  has_gitlab_ci: boolean;
  has_azure_pipelines: boolean;
  has_jenkins: boolean;
  has_render_config: boolean;
  has_railway_config: boolean;
  has_vercel_config: boolean;
  has_netlify_config: boolean;
  has_deployment_scripts: boolean;
  detected_platforms: string[];
}

export interface ConfigValidation {
  has_environment_variables: boolean;
  has_env_file: boolean;
  has_production_config: boolean;
  has_development_config: boolean;
  has_secret_management: boolean;
  has_database_config: boolean;
  has_cache_config: boolean;
  env_var_count: number;
}

export interface ReleaseReadiness {
  has_versioning: boolean;
  has_release_notes: boolean;
  has_build_scripts: boolean;
  has_startup_scripts: boolean;
  has_shutdown_handling: boolean;
  has_health_checks: boolean;
}

export interface ObservabilityDetection {
  has_logging: boolean;
  has_monitoring: boolean;
  has_metrics: boolean;
  has_tracing: boolean;
  has_health_endpoints: boolean;
}

export interface CategoryScore {
  architecture_readiness: number;
  security_readiness: number;
  performance_readiness: number;
  dependency_health: number;
  configuration_health: number;
  environment_configuration: number;
  logging_configuration: number;
  monitoring_support: number;
  error_handling: number;
  exception_handling: number;
  documentation_readiness: number;
  testing_readiness: number;
  cicd_readiness: number;
}

export interface ProductionSummary {
  classification: string;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_text: string;
  prioritized_recommendations: string[];
}

export interface ProductionReadinessResponse {
  production_score: ProductionScore;
  category_scores: CategoryScore;
  findings: ProductionFinding[];
  deployment: DeploymentDetection;
  config_validation: ConfigValidation;
  release_readiness: ReleaseReadiness;
  observability: ObservabilityDetection;
  summary: ProductionSummary;
  analyzed_at: string;
}

export interface AiEngineeringScore {
  overall_engineering_score: number;
  engineering_readiness: number;
  ai_confidence: number;
  repair_readiness: number;
  automation_readiness: number;
  project_stability: number;
}

export interface EngineeringCapability {
  name: string;
  score: number;
  status: string;
  detail: string;
  requirements: string[];
}

export interface ProjectHealthEntry {
  architecture_health: number;
  code_health: number;
  dependency_health: number;
  security_health: number;
  performance_health: number;
  maintainability_health: number;
  documentation_health: number;
  testing_health: number;
  production_health: number;
}

export interface RepairReadinessEstimate {
  files_safe_to_modify: number;
  high_risk_files: number;
  protected_files: number;
  configuration_files: number;
  core_modules: number;
  utility_modules: number;
}

export interface EngineeringRoadmapStage {
  step: number;
  name: string;
  status: string;
  readiness: number;
  detail: string;
}

export interface AiEngineeringFinding {
  name: string;
  category: string;
  severity: string;
  detail: string;
  affected_modules: string[];
  impact: string;
  recommendation: string;
}

export interface AiEngineeringSummary {
  summary_text: string;
  capabilities_ready: number;
  capabilities_total: number;
  critical_findings: number;
  high_findings: number;
  prioritized_recommendations: string[];
}

export interface AiEngineeringReadinessResponse {
  engineering_score: AiEngineeringScore;
  capabilities: EngineeringCapability[];
  project_health: ProjectHealthEntry;
  findings: AiEngineeringFinding[];
  repair_readiness: RepairReadinessEstimate;
  roadmap: EngineeringRoadmapStage[];
  summary: AiEngineeringSummary;
  analyzed_at: string;
}

export interface DetectionModule {
  name: string;
  description: string;
  ready: boolean;
}

export interface WorkspaceStatusCard {
  label: string;
  status: string;
}

export interface BugDetectionWorkspaceResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  project_type: string;
  workspace_status: string;
  project_ready: boolean;
  analysis_ready: boolean;
  detection_ready: boolean;
  ai_confidence: number;
  total_files: number;
  total_folders: number;
  status_cards: WorkspaceStatusCard[];
  detection_modules: DetectionModule[];
  analysis_summary: string;
  initialized_at: string;
}

export interface PipelineModule {
  name: string;
  order: number;
  status: string;
  description: string;
  purpose: string;
  required_inputs: string[];
  expected_outputs: string[];
}

export interface PipelineStatusResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  pipeline_status: string;
  overall_readiness: number;
  modules_ready: number;
  modules_total: number;
  modules_waiting: number;
  modules: PipelineModule[];
  status_cards: WorkspaceStatusCard[];
  summary: string;
  initialized_at: string;
}

export interface SyntaxErrorInfo {
  bug_title: string;
  description: string;
  severity: string;
  confidence: number;
  language: string;
  affected_file: string;
  line_number: number;
  column_number: number;
  code_snippet: string;
  ai_explanation: string;
  suggested_fix: string;
  error_type: string;
  function_name: string;
}

export interface SyntaxDetectionResult {
  file_path: string;
  language: string;
  errors: SyntaxErrorInfo[];
  error_count: number;
  health_score: number;
}

export interface SyntaxDetectionResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  summary: string;
  total_errors: number;
  total_files_scanned: number;
  files_with_errors: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  results: SyntaxDetectionResult[];
  scanned_languages: string[];
}

export interface StaticCodeAnalysisResult {
  file_path: string;
  language: string;
  errors: SyntaxErrorInfo[];
  error_count: number;
  health_score: number;
}

export interface StaticCodeAnalysisResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  summary: string;
  total_errors: number;
  total_files_scanned: number;
  files_with_errors: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  results: StaticCodeAnalysisResult[];
  scanned_languages: string[];
}

export interface DependencyIssueInfo extends SyntaxErrorInfo {
  package_name: string;
  current_version: string;
  recommended_version: string;
}

export interface DependencyAnalysisResult {
  file_path: string;
  language: string;
  errors: DependencyIssueInfo[];
  error_count: number;
  health_score: number;
}

export interface DependencyAnalysisResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  summary: string;
  total_errors: number;
  total_files_scanned: number;
  files_with_errors: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  results: DependencyAnalysisResult[];
  package_manager: string;
  declared_packages: string[];
}

export interface RuntimeIssueInfo extends SyntaxErrorInfo {
  possible_impact: string;
}

export interface RuntimeAnalysisResult {
  file_path: string;
  language: string;
  errors: RuntimeIssueInfo[];
  error_count: number;
  health_score: number;
}

export interface RuntimeAnalysisResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  summary: string;
  total_errors: number;
  total_files_scanned: number;
  files_with_errors: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  results: RuntimeAnalysisResult[];
  scanned_languages: string[];
}

export interface SecurityIssueInfo extends SyntaxErrorInfo {
  security_category: string;
  security_impact: string;
  cwe_id: string;
}

export interface SecurityAnalysisResult {
  file_path: string;
  language: string;
  errors: SecurityIssueInfo[];
  error_count: number;
  health_score: number;
}

export interface SecurityAnalysisResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  summary: string;
  total_errors: number;
  total_files_scanned: number;
  files_with_errors: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  results: SecurityAnalysisResult[];
  scanned_languages: string[];
  security_score: number;
}

export interface PerformanceIssueInfo extends SyntaxErrorInfo {
  performance_category: string;
  estimated_cost: string;
}

export interface PerformanceAnalysisResult {
  file_path: string;
  language: string;
  errors: PerformanceIssueInfo[];
  error_count: number;
  health_score: number;
}

export interface PerformanceAnalysisResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  summary: string;
  total_errors: number;
  total_files_scanned: number;
  files_with_errors: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  results: PerformanceAnalysisResult[];
  scanned_languages: string[];
}

export interface ArchitectureIssueInfo extends SyntaxErrorInfo {
  architecture_category: string;
  impact_scope: string;
  affected_module?: string;
  business_impact?: string;
  architecture_impact?: string;
}

export interface ArchitectureAnalysisResult {
  file_path: string;
  language: string;
  errors: ArchitectureIssueInfo[];
  error_count: number;
  health_score: number;
}

export interface ArchitectureAnalysisResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  summary: string;
  total_errors: number;
  total_files_scanned: number;
  files_with_errors: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  results: ArchitectureAnalysisResult[];
  scanned_languages: string[];
}

export interface PrioritizedIssueInfo extends SyntaxErrorInfo {
  source_engine: string;
  priority_score: number;
  cross_cutting_categories: string[];
  recommended_action: string;
}

export interface PrioritizationFileGroup {
  file_path: string;
  language: string;
  total_issues: number;
  avg_priority: number;
  max_severity: string;
  issues: PrioritizedIssueInfo[];
}

export interface PrioritizationResponse {
  session_id: string;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  summary: string;
  total_issues: number;
  total_files_affected: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  prioritized_issues: PrioritizedIssueInfo[];
  file_groups: PrioritizationFileGroup[];
  ai_recommendations: string[];
  analyzed_at: string;
}
