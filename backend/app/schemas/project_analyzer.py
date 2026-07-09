from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DetectedEntryPoint(BaseModel):
    path: str
    file_name: str
    type: str


class DetectedDirectory(BaseModel):
    name: str
    path: str
    purpose: str


class ProjectAnalysisResponse(BaseModel):
    project_type: str
    project_type_reason: str
    architecture: str
    architecture_reason: str
    entry_points: list[DetectedEntryPoint]
    important_directories: list[DetectedDirectory]
    detected_modules: list[str]
    frontend_framework: str | None = None
    backend_framework: str | None = None
    database_detected: list[str]
    has_tests: bool
    has_docker: bool
    has_ci_cd: bool
    structure_summary: str
    analyzed_at: datetime


class FolderSummary(BaseModel):
    frontend: int = 0
    backend: int = 0
    source: int = 0
    config: int = 0
    assets: int = 0
    docs: int = 0
    tests: int = 0
    scripts: int = 0
    other: int = 0


class TechnologyStack(BaseModel):
    languages: list[str] = []
    frameworks: list[str] = []
    databases: list[str] = []
    package_managers: list[str] = []


class ConfigSummary(BaseModel):
    has_package_json: bool = False
    has_requirements_txt: bool = False
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    has_readme: bool = False
    has_pyproject_toml: bool = False
    has_env_example: bool = False
    has_gitignore: bool = False


class AnalyzerResponse(BaseModel):
    project_name: str
    project_type: str
    workspace_status: str
    technology_stack: TechnologyStack
    total_files: int
    total_folders: int
    workspace_size: int
    folder_summary: FolderSummary
    config_summary: ConfigSummary
    workspace_summary: str
    analyzed_at: datetime


class DetectedEntryPointInfo(BaseModel):
    entry_file: str
    framework: str
    project_type: str
    confidence: int
    reason: str


class EntryPointDetectionResponse(BaseModel):
    primary_entry_point: DetectedEntryPointInfo | None = None
    alternative_entry_points: list[DetectedEntryPointInfo] = []
    total_entry_points: int = 0
    analyzed_at: datetime


class ArchitectureLayerInfo(BaseModel):
    name: str
    directories: list[str]


class DetectedArchitectureInfo(BaseModel):
    architecture: str
    confidence: int
    reason: str
    evidence: list[str]


class ArchitectureHealthDetail(BaseModel):
    score: int
    label: str
    details: dict[str, int] = {}


class ArchitectureDetectionResponse(BaseModel):
    primary_architecture: DetectedArchitectureInfo | None = None
    alternative_architectures: list[DetectedArchitectureInfo] = []
    detected_layers: list[ArchitectureLayerInfo] = []
    health: ArchitectureHealthDetail = ArchitectureHealthDetail(score=0, label="Unknown")
    recommendations: list[str] = []
    visual_layers: list[str] = []
    organization_summary: str = ""
    analyzed_at: datetime


class DetectedModuleInfo(BaseModel):
    module_name: str
    status: str
    detected_folder: str | None = None
    confidence: int
    reason: str


class ModuleSummaryInfo(BaseModel):
    total_modules: int = 0
    detected_count: int = 0
    missing_count: int = 0
    core_detected: int = 0
    core_total: int = 0
    optional_detected: int = 0
    optional_total: int = 0


class ModuleDetectionResponse(BaseModel):
    modules: list[DetectedModuleInfo] = []
    summary: ModuleSummaryInfo = ModuleSummaryInfo()
    analyzed_at: datetime


class DetectedTechnology(BaseModel):
    name: str
    version: str | None = None
    confidence: int
    reason: str


class DetectedOrmInfo(BaseModel):
    name: str
    version: str | None = None
    confidence: int
    reason: str
    migration: str | None = None


class DetectedMigrationInfo(BaseModel):
    name: str
    version: str | None = None
    confidence: int
    reason: str


class DetectedDbFileInfo(BaseModel):
    path: str
    size: str


class DetectedConnectionInfo(BaseModel):
    raw_uri: str
    host: str | None = None
    port: str | None = None
    database: str | None = None
    type: str | None = None


class CategorizedTechnology(BaseModel):
    name: str
    version: str | None = None
    confidence: int
    reason: str
    category: str
    detection_source: str


class TechnologyStackDetail(BaseModel):
    languages: list[DetectedTechnology] = []
    frameworks: list[DetectedTechnology] = []
    runtimes: list[DetectedTechnology] = []
    package_managers: list[DetectedTechnology] = []
    build_tools: list[DetectedTechnology] = []
    databases: list[DetectedTechnology] = []
    containers: list[DetectedTechnology] = []
    orms: list[DetectedOrmInfo] = []
    migrations: list[DetectedMigrationInfo] = []
    database_files: list[DetectedDbFileInfo] = []
    connection_details: list[DetectedConnectionInfo] = []
    categorized: dict[str, list[CategorizedTechnology]] = {}


class FrameworkHealthInfo(BaseModel):
    score: int
    label: str
    details: dict[str, int] = {}


class CompatibilityCheckInfo(BaseModel):
    framework: str
    other_framework: str
    status: str
    note: str


class FeatureDetectionInfo(BaseModel):
    name: str
    confidence: int
    evidence: list[str] = []


class DependencyGraphLayer(BaseModel):
    layer: str
    label: str
    technologies: list[str]


class FrameworkEvidenceInfo(BaseModel):
    name: str
    source: str
    confidence: int


class FrameworkDetailInfo(BaseModel):
    name: str
    version: str | None = None
    confidence: int
    reason: str
    category: str = ""
    detection_source: str = ""
    health: FrameworkHealthInfo | None = None
    role: str = ""


class FrameworkIntelligenceResponse(BaseModel):
    technology_stack: TechnologyStackDetail
    primary_language: DetectedTechnology | None = None
    primary_framework: DetectedTechnology | None = None
    frameworks: list[FrameworkDetailInfo] = []
    compatibility: list[CompatibilityCheckInfo] = []
    features: list[FeatureDetectionInfo] = []
    dependency_graph: list[DependencyGraphLayer] = []
    evidence: list[FrameworkEvidenceInfo] = []
    project_type: str = ""
    analyzed_at: datetime


class ConfigFileInfo(BaseModel):
    file_name: str
    status: str
    category: str
    purpose: str = ""
    confidence: int = 0
    detection_source: str = ""
    recommendation: str | None = None
    path: str | None = None


class ConfigWarning(BaseModel):
    message: str
    severity: str
    file_name: str | None = None


class ConfigHealthInfo(BaseModel):
    score: int
    label: str


class DependencyValidationInfo(BaseModel):
    type: str
    package: str
    severity: str
    detail: str


class EnvironmentValidationInfo(BaseModel):
    type: str
    file: str | None = None
    severity: str
    detail: str


class DockerValidationInfo(BaseModel):
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    multi_stage_build: bool = False
    production_ready: bool = False
    detail: str = ""


class CicdInfo(BaseModel):
    platform: str
    configured: bool = False
    file: str | None = None


class SecurityCheckInfo(BaseModel):
    type: str
    severity: str
    detail: str


class ReadinessScores(BaseModel):
    configuration_health: int = 0
    readiness: int = 0
    security: int = 0
    maintainability: int = 0


class LanguageDistribution(BaseModel):
    language: str
    file_count: int
    percentage: float


class WorkspaceStatistics(BaseModel):
    total_files: int = 0
    total_folders: int = 0
    source_files: int = 0
    config_files: int = 0
    doc_files: int = 0
    image_files: int = 0
    video_files: int = 0
    archive_files: int = 0
    template_files: int = 0
    script_files: int = 0
    asset_files: int = 0
    largest_file: str = ""
    largest_file_size: int = 0
    largest_folder: str = ""
    largest_folder_count: int = 0
    average_file_size: int = 0
    average_folder_depth: float = 0.0
    max_folder_depth: int = 0
    workspace_size: int = 0


class ProjectScaleInfo(BaseModel):
    scale: str = "Unknown"
    confidence: int = 0


class ComplexityScoreInfo(BaseModel):
    score: int = 0
    level: str = "Unknown"
    factors: dict[str, int] = {}


class OrganizationInfo(BaseModel):
    level: str = "Unknown"
    score: int = 0


class MaintainabilityInfo(BaseModel):
    score: int = 0
    level: str = "Unknown"
    factors: dict[str, int] = {}


class DocumentationCoverage(BaseModel):
    coverage_percentage: float = 0.0
    has_readme: bool = False
    has_license: bool = False
    has_changelog: bool = False
    has_api_docs: bool = False


class BuildReadinessInfo(BaseModel):
    status: str = "Unknown"
    score: int = 0
    reasons: list[str] = []


class PerformanceEstimate(BaseModel):
    expected_analysis_time: str = ""
    workspace_scan_time: str = ""
    complexity_impact: str = ""


class ComplexityAnalysisResponse(BaseModel):
    project_scale: ProjectScaleInfo = ProjectScaleInfo()
    complexity_score: ComplexityScoreInfo = ComplexityScoreInfo()
    maintainability: MaintainabilityInfo = MaintainabilityInfo()
    workspace_statistics: WorkspaceStatistics = WorkspaceStatistics()
    language_distribution: list[LanguageDistribution] = []
    documentation_coverage: DocumentationCoverage = DocumentationCoverage()
    build_readiness: BuildReadinessInfo = BuildReadinessInfo()
    organization: OrganizationInfo = OrganizationInfo()
    performance: PerformanceEstimate | None = None
    analyzed_at: datetime


class ConfigurationIntelligenceResponse(BaseModel):
    detected_files: list[ConfigFileInfo] = []
    missing_files: list[ConfigFileInfo] = []
    dependency_validation: list[DependencyValidationInfo] = []
    environment_validation: list[EnvironmentValidationInfo] = []
    docker_validation: DockerValidationInfo = DockerValidationInfo()
    cicd: list[CicdInfo] = []
    security_checks: list[SecurityCheckInfo] = []
    scores: ReadinessScores = ReadinessScores()
    warnings: list[ConfigWarning] = []
    recommendations: list[str] = []
    health: ConfigHealthInfo
    readiness_score: int = 0
    analyzed_at: datetime


class CodeMetricsInfo(BaseModel):
    total_lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    comment_ratio: float = 0.0
    code_files: int = 0
    avg_file_size: float = 0.0
    largest_file: str = ""
    largest_file_size: int = 0
    smallest_file: str = ""
    smallest_file_size: int = 0
    avg_function_length: float = 0.0
    avg_class_size: float = 0.0


class ComplexityInfo(BaseModel):
    total_functions: int = 0
    total_classes: int = 0
    avg_cyclomatic_complexity: float = 0.0
    max_complexity: int = 0
    low_count: int = 0
    medium_count: int = 0
    high_count: int = 0
    critical_count: int = 0


class ComplexityDistributionItem(BaseModel):
    label: str
    count: int
    percentage: float


class MaintainabilityGradeInfo(BaseModel):
    score: int = 0
    grade: str = "F"


class CodeOrganizationIssue(BaseModel):
    type: str
    detail: str
    severity: str


class CodeStyleIssue(BaseModel):
    type: str
    detail: str
    severity: str


class ProjectStats(BaseModel):
    python_files: int = 0
    javascript_files: int = 0
    html_files: int = 0
    css_files: int = 0
    json_files: int = 0
    markdown_files: int = 0
    images: int = 0
    videos: int = 0
    other_assets: int = 0


class LanguageLocItem(BaseModel):
    language: str
    lines: int
    percentage: float


class LargestDirectoryItem(BaseModel):
    path: str
    file_count: int
    size: int


class LargestFileItem(BaseModel):
    path: str
    size: int
    lines: int


class MetricRecommendation(BaseModel):
    type: str
    detail: str


class ProjectIntelligenceResponse(BaseModel):
    code_metrics: CodeMetricsInfo = CodeMetricsInfo()
    complexity: ComplexityInfo = ComplexityInfo()
    complexity_distribution: list[ComplexityDistributionItem] = []
    maintainability: MaintainabilityGradeInfo = MaintainabilityGradeInfo()
    code_organization: list[CodeOrganizationIssue] = []
    code_style: list[CodeStyleIssue] = []
    project_stats: ProjectStats = ProjectStats()
    language_distribution: list[LanguageDistribution] = []
    language_loc: list[LanguageLocItem] = []
    largest_directories: list[LargestDirectoryItem] = []
    largest_files: list[LargestFileItem] = []
    recommendations: list[MetricRecommendation] = []
    analyzed_at: datetime


class HealthScoreInfo(BaseModel):
    score: int
    classification: str


class InsightStrength(BaseModel):
    category: str
    detail: str


class InsightWeakness(BaseModel):
    category: str
    detail: str


class RiskAnalysisInfo(BaseModel):
    level: str
    score: int
    explanation: str


class ScalabilityInfo(BaseModel):
    level: str
    reason: str


class PerformanceInsight(BaseModel):
    type: str
    detail: str


class SecurityInsight(BaseModel):
    type: str
    severity: str
    detail: str


class ProjectCodeQualityInsight(BaseModel):
    type: str
    detail: str


class RecommendedAction(BaseModel):
    action: str
    priority: str


class ReadinessDetail(BaseModel):
    category: str
    score: int


class ProjectInsightsResponse(BaseModel):
    health_score: HealthScoreInfo
    ai_summary: list[str]
    strengths: list[InsightStrength]
    weaknesses: list[InsightWeakness]
    risk_analysis: RiskAnalysisInfo
    maintainability: MaintainabilityGradeInfo
    maintainability_explanation: str
    scalability: ScalabilityInfo
    performance_insights: list[PerformanceInsight]
    security_insights: list[SecurityInsight]
    code_quality_insights: list[ProjectCodeQualityInsight]
    recommended_actions: list[RecommendedAction]
    readiness_scores: list[ReadinessDetail]
    analyzed_at: datetime


class ConsistencyCheck(BaseModel):
    check_name: str
    status: str
    detail: str
    modules_involved: list[str] = []


class SelfHealingAction(BaseModel):
    check_name: str
    action: str
    detail: str


class ValidationReportItem(BaseModel):
    category: str
    status: str
    checks: list[ConsistencyCheck]


class AnalyzerValidationResponse(BaseModel):
    consistency_score: int
    classification: str
    passed_checks: int
    failed_checks: int
    warnings: int
    critical_errors: int
    checks: list[ConsistencyCheck]
    validation_report: list[ValidationReportItem]
    self_healing: list[SelfHealingAction]
    recommendations: list[str]
    analyzed_at: datetime


class CodeIntelligenceFunctionParam(BaseModel):
    name: str
    type: str | None = None
    default: str | None = None


class CodeIntelligenceFunction(BaseModel):
    name: str
    file_path: str
    line_start: int
    line_end: int = 0
    parameters: list[CodeIntelligenceFunctionParam] = []
    return_type: str | None = None
    decorators: list[str] = []
    is_async: bool = False
    is_static: bool = False
    is_generator: bool = False
    visibility: str = "public"
    parent_class: str | None = None


class CodeIntelligenceProperty(BaseModel):
    name: str
    type: str | None = None
    visibility: str = "public"
    is_static: bool = False


class CodeIntelligenceClass(BaseModel):
    name: str
    file_path: str
    line_start: int
    line_end: int = 0
    base_classes: list[str] = []
    inherited_classes: list[str] = []
    methods: list[CodeIntelligenceFunction] = []
    properties: list[CodeIntelligenceProperty] = []
    decorators: list[str] = []
    visibility: str = "public"
    is_abstract: bool = False


class CodeIntelligenceImport(BaseModel):
    source: str | None = None
    names: list[str] = []
    is_external: bool = False
    is_duplicate: bool = False
    line: int = 0


class CodeIntelligenceVariable(BaseModel):
    name: str
    file_path: str
    line: int
    type: str | None = None
    is_constant: bool = False


class CodeIntelligenceEnum(BaseModel):
    name: str
    file_path: str
    line: int
    values: list[str] = []


class CodeIntelligenceInterface(BaseModel):
    name: str
    file_path: str
    line: int
    properties: list[str] = []
    methods: list[str] = []


class CodeIntelligenceFileSummary(BaseModel):
    path: str
    language: str
    lines_of_code: int = 0
    total_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: int = 0
    classes: int = 0
    imports: int = 0
    exports: int = 0
    complexity: int = 0
    maintainability_score: float = 0.0
    encoding: str = "utf-8"


class CodeIntelligenceModule(BaseModel):
    name: str
    path: str
    files: list[str] = []
    classes: list[str] = []
    functions: list[str] = []
    submodules: list[str] = []


class CodeIntelligenceSearchResult(BaseModel):
    type: str
    name: str
    file_path: str
    line: int
    detail: str = ""


class CodeIntelligenceSummary(BaseModel):
    total_files: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_imports: int = 0
    total_external_imports: int = 0
    total_enums: int = 0
    total_interfaces: int = 0
    total_variables: int = 0
    total_constants: int = 0
    total_modules: int = 0
    total_comments: int = 0
    total_blank_lines: int = 0
    total_empty_files: int = 0
    total_duplicate_files: int = 0
    average_file_size: float = 0.0
    average_lines_of_code: float = 0.0
    average_complexity: float = 0.0
    average_maintainability: float = 0.0
    largest_file: str = ""
    largest_file_size: int = 0
    smallest_file: str = ""
    smallest_file_size: int = 0
    languages: list[str] = []


class SourceCodeIntelligenceResponse(BaseModel):
    summary: CodeIntelligenceSummary
    files: list[CodeIntelligenceFileSummary] = []
    classes: list[CodeIntelligenceClass] = []
    functions: list[CodeIntelligenceFunction] = []
    imports: list[CodeIntelligenceImport] = []
    enums: list[CodeIntelligenceEnum] = []
    interfaces: list[CodeIntelligenceInterface] = []
    variables: list[CodeIntelligenceVariable] = []
    modules: list[CodeIntelligenceModule] = []
    analyzed_at: datetime


class QualityScoreInfo(BaseModel):
    score: float
    label: str


class CodeQualityIssue(BaseModel):
    type: str
    severity: str
    description: str
    reason: str
    suggested_fix: str
    priority: str
    affected_file: str
    affected_function: str | None = None
    line: int | None = None


class CodeQualityCheck(BaseModel):
    check_name: str
    status: str
    severity: str
    count: int = 0
    issues: list[CodeQualityIssue] = []


class CodeQualityInsight(BaseModel):
    message: str
    type: str
    sentiment: str
    module: str | None = None
    files: list[str] = []
    category: str = ""


class CodeQualityAiRecommendation(BaseModel):
    action: str
    impact: str
    effort: str
    detail: str
    priority: str = "medium"
    estimated_improvement: str = ""
    affected_file_count: int = 0
    affected_files: list[str] = []
    category: str = ""


class CodeQualityAiSummary(BaseModel):
    summary: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    architecture: str = ""
    recommended_focus: str = ""


class CodeQualitySeverityCount(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class CodeQualityTopFile(BaseModel):
    path: str
    issue_count: int
    score: float


class CodeQualityLanguageBreakdown(BaseModel):
    language: str
    file_count: int
    issue_count: int
    avg_complexity: float


class FileMetricScores(BaseModel):
    overall: float
    maintainability: float
    complexity: float
    readability: float
    documentation: float
    security: float


class FileAnalysisIssue(BaseModel):
    type: str
    severity: str
    description: str
    reason: str
    suggested_fix: str
    priority: str
    line: int | None = None


class FileAnalysisDetail(BaseModel):
    path: str
    file_name: str
    extension: str
    language: str
    size: int
    total_lines: int
    code_lines: int
    blank_lines: int
    comment_lines: int
    functions: int
    classes: int
    imports: int
    complexity: int
    scores: FileMetricScores
    health: str
    tags: list[str]
    ai_summary: str
    issues: list[FileAnalysisIssue]


class FileAnalysisResponse(BaseModel):
    files: list[FileAnalysisDetail]
    total_files: int
    language_counts: dict[str, int]
    analyzed_at: datetime


class FunctionClassIssue(BaseModel):
    type: str
    severity: str
    description: str
    reason: str
    suggested_fix: str
    line: int | None = None


class FunctionParameter(BaseModel):
    name: str
    type: str | None = None
    default_value: str | None = None
    is_optional: bool = False


class FunctionDetail(BaseModel):
    name: str
    file_path: str
    file_name: str
    language: str
    module: str = ""
    parameters: list[FunctionParameter] = []
    return_type: str | None = None
    decorators: list[str] = []
    is_async: bool = False
    is_generator: bool = False
    is_lambda: bool = False
    visibility: str = "public"
    lines_of_code: int = 0
    cyclomatic_complexity: int = 1
    maintainability_score: float = 100.0
    has_documentation: bool = False
    issue_count: int = 0
    health_status: str = "Good"
    issues: list[FunctionClassIssue] = []
    ai_insight: str = ""


class MethodDetail(BaseModel):
    name: str
    parent_class: str = ""
    parameters: list[FunctionParameter] = []
    return_type: str | None = None
    decorators: list[str] = []
    is_async: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    is_property: bool = False
    visibility: str = "public"
    lines_of_code: int = 0
    cyclomatic_complexity: int = 1
    maintainability_score: float = 100.0
    has_documentation: bool = False
    issue_count: int = 0
    health_status: str = "Good"
    issues: list[FunctionClassIssue] = []
    ai_insight: str = ""


class ClassDetail(BaseModel):
    name: str
    file_path: str
    file_name: str
    language: str
    module: str = ""
    base_classes: list[str] = []
    parent_class: str | None = None
    child_classes: list[str] = []
    methods: list[MethodDetail] = []
    properties: list[str] = []
    constructors: list[MethodDetail] = []
    decorators: list[str] = []
    interfaces: list[str] = []
    is_abstract: bool = False
    lines_of_code: int = 0
    complexity: int = 1
    maintainability_score: float = 100.0
    has_documentation: bool = False
    issue_count: int = 0
    health_status: str = "Good"
    issues: list[FunctionClassIssue] = []
    ai_insight: str = ""


class FunctionRelationship(BaseModel):
    name: str
    file_path: str
    callers: list[str] = []
    called_functions: list[str] = []
    is_recursive: bool = False
    is_unused: bool = False
    is_duplicate: bool = False
    cross_file_calls: list[str] = []


class ClassRelationship(BaseModel):
    name: str
    file_path: str
    inheritance: list[str] = []
    composition: list[str] = []
    aggregation: list[str] = []
    dependency: list[str] = []
    association: list[str] = []


class FunctionClassStats(BaseModel):
    total_functions: int = 0
    total_classes: int = 0
    total_methods: int = 0
    average_complexity: float = 0.0
    average_maintainability: float = 100.0
    total_issues: int = 0
    language_breakdown: dict[str, int] = {}
    health_counts: dict[str, int] = {}
    unused_functions: int = 0
    recursive_functions: int = 0
    undocumented_count: int = 0


class FunctionClassResponse(BaseModel):
    functions: list[FunctionDetail] = []
    classes: list[ClassDetail] = []
    relationships: list[FunctionRelationship] = []
    class_relationships: list[ClassRelationship] = []
    stats: FunctionClassStats
    ai_insights: list[str] = []
    analyzed_at: datetime


class ImportRecord(BaseModel):
    module: str
    symbol: str = ""
    alias: str | None = None
    source_file: str
    target_file: str | None = None
    import_type: str = "internal"
    language: str
    is_relative: bool = False
    is_wildcard: bool = False
    is_dynamic: bool = False
    is_unused: bool = False
    is_duplicate: bool = False
    is_broken: bool = False
    line_number: int | None = None
    resolved: bool = True
    confidence: float = 1.0


class FileDependency(BaseModel):
    source_file: str
    target_file: str | None = None
    target_module: str = ""
    dependency_type: str = "import"
    language: str
    import_count: int = 1
    is_external: bool = False
    is_circular: bool = False
    is_broken: bool = False
    is_unused: bool = False


class CircularDependency(BaseModel):
    chain: list[str]
    files: list[str]
    severity: str = "medium"
    suggested_resolution: str = ""


class DependencyGraphNode(BaseModel):
    id: str
    label: str
    type: str = "file"
    language: str = ""
    file_count: int = 1
    import_count: int = 0


class DependencyGraphEdge(BaseModel):
    source: str
    target: str
    weight: int = 1
    type: str = "import"


class DependencyGraph(BaseModel):
    nodes: list[DependencyGraphNode] = []
    edges: list[DependencyGraphEdge] = []


class DependencyMetrics(BaseModel):
    total_files: int = 0
    total_imports: int = 0
    total_dependencies: int = 0
    external_libraries: int = 0
    internal_libraries: int = 0
    broken_dependencies: int = 0
    unused_imports: int = 0
    circular_dependencies: int = 0
    average_dependency_depth: float = 0.0
    coupling_score: float = 0.0
    language_breakdown: dict[str, int] = {}
    dependency_type_counts: dict[str, int] = {}


class ImportDependencyResponse(BaseModel):
    imports: list[ImportRecord]
    dependencies: list[FileDependency]
    circular_dependencies: list[CircularDependency]
    graph: DependencyGraph
    metrics: DependencyMetrics
    insights: list[str]
    recommendations: list[str]
    analyzed_at: datetime


class CodeQualityResponse(BaseModel):
    overall_score: QualityScoreInfo
    maintainability_score: QualityScoreInfo
    readability_score: QualityScoreInfo
    complexity_score: QualityScoreInfo
    documentation_score: QualityScoreInfo
    security_score: QualityScoreInfo
    technical_debt_score: QualityScoreInfo
    checks: list[CodeQualityCheck]
    insights: list[CodeQualityInsight]
    recommendations: list[CodeQualityAiRecommendation]
    severity_counts: CodeQualitySeverityCount
    total_issues: int
    top_problematic_files: list[CodeQualityTopFile] = []
    top_clean_files: list[CodeQualityTopFile] = []
    language_breakdown: list[CodeQualityLanguageBreakdown] = []
    ai_summary: CodeQualityAiSummary | None = None
    analyzed_at: datetime


class FileIntelligenceHealth(BaseModel):
    overall: float
    maintainability: float
    complexity: float
    documentation: float
    security: float
    readability: float


class FileIntelligenceIssue(BaseModel):
    type: str
    severity: str
    description: str
    reason: str = ""
    suggested_fix: str = ""


class FileIntelligenceDetail(BaseModel):
    file_name: str
    path: str
    extension: str
    language: str
    encoding: str = "utf-8"
    size: int = 0
    last_modified: str = ""
    total_lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    functions: int = 0
    classes: int = 0
    imports: int = 0
    complexity: int = 0
    health: FileIntelligenceHealth
    classification: str
    tags: list[str] = []
    issues: list[FileIntelligenceIssue] = []
    ai_summary: str = ""


class FileIntelligenceStats(BaseModel):
    total_files: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_imports: int = 0
    total_lines: int = 0
    total_code_lines: int = 0
    total_blank_lines: int = 0
    total_comment_lines: int = 0
    language_counts: dict[str, int] = {}
    classification_counts: dict[str, int] = {}
    health_distribution: dict[str, int] = {}
    average_complexity: float = 0.0
    average_maintainability: float = 0.0
    total_issues: int = 0
    large_files: int = 0
    empty_files: int = 0
    duplicate_files: int = 0


class FileIntelligenceResponse(BaseModel):
    files: list[FileIntelligenceDetail]
    stats: FileIntelligenceStats
    analyzed_at: datetime


class FuncClassIntelligenceParam(BaseModel):
    name: str
    type: str | None = None
    default_value: str | None = None
    is_optional: bool = False


class FuncClassIntelligenceIssue(BaseModel):
    type: str
    severity: str
    description: str
    reason: str = ""
    suggested_fix: str = ""
    line: int | None = None


class FuncClassIntelligenceFunc(BaseModel):
    name: str
    file_path: str
    file_name: str
    language: str
    module: str = ""
    parameters: list[FuncClassIntelligenceParam] = []
    return_type: str | None = None
    decorators: list[str] = []
    is_async: bool = False
    is_generator: bool = False
    is_lambda: bool = False
    visibility: str = "public"
    lines_of_code: int = 0
    start_line: int = 0
    end_line: int = 0
    cyclomatic_complexity: int = 1
    maintainability_score: float = 100.0
    has_documentation: bool = False
    has_type_hints: bool = False
    deepest_nesting: int = 0
    issue_count: int = 0
    health_status: str = "Good"
    issues: list[FuncClassIntelligenceIssue] = []
    callers: list[str] = []
    called_functions: list[str] = []
    is_recursive: bool = False
    is_unused: bool = False
    cross_file_calls: list[str] = []
    ai_insight: str = ""


class FuncClassIntelligenceMethod(BaseModel):
    name: str
    parent_class: str = ""
    parameters: list[FuncClassIntelligenceParam] = []
    return_type: str | None = None
    decorators: list[str] = []
    is_async: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    is_property: bool = False
    visibility: str = "public"
    lines_of_code: int = 0
    start_line: int = 0
    end_line: int = 0
    cyclomatic_complexity: int = 1
    maintainability_score: float = 100.0
    has_documentation: bool = False
    has_type_hints: bool = False
    issue_count: int = 0
    health_status: str = "Good"
    issues: list[FuncClassIntelligenceIssue] = []
    ai_insight: str = ""


class FuncClassIntelligenceClass(BaseModel):
    name: str
    file_path: str
    file_name: str
    language: str
    module: str = ""
    base_classes: list[str] = []
    parent_class: str | None = None
    child_classes: list[str] = []
    methods: list[FuncClassIntelligenceMethod] = []
    properties: list[str] = []
    class_variables: list[str] = []
    constructors: list[FuncClassIntelligenceMethod] = []
    decorators: list[str] = []
    interfaces: list[str] = []
    is_abstract: bool = False
    has_nested_classes: bool = False
    lines_of_code: int = 0
    complexity: int = 1
    maintainability_score: float = 100.0
    has_documentation: bool = False
    issue_count: int = 0
    health_status: str = "Good"
    issues: list[FuncClassIntelligenceIssue] = []
    coupling: int = 0
    method_count: int = 0
    property_count: int = 0
    ai_insight: str = ""


class FuncClassRelationship(BaseModel):
    type: str  # "inheritance", "composition", "aggregation", "association", "dependency"
    source: str
    target: str
    source_file: str = ""
    target_file: str = ""
    strength: str = "weak"  # "weak", "medium", "strong"


class FuncClassIntelligenceStats(BaseModel):
    total_functions: int = 0
    total_classes: int = 0
    total_methods: int = 0
    average_complexity: float = 0.0
    average_maintainability: float = 100.0
    total_issues: int = 0
    language_breakdown: dict[str, int] = {}
    health_counts: dict[str, int] = {}
    unused_functions: int = 0
    recursive_functions: int = 0
    undocumented_count: int = 0
    deep_nesting_count: int = 0
    missing_type_hints_count: int = 0


class FuncClassIntelligenceResponse(BaseModel):
    functions: list[FuncClassIntelligenceFunc]
    classes: list[FuncClassIntelligenceClass]
    relationships: list[FuncClassRelationship]
    stats: FuncClassIntelligenceStats
    ai_insights: list[str] = []
    analyzed_at: datetime


class CallGraphNode(BaseModel):
    id: str
    name: str
    type: str  # "function", "method", "class", "entry_point", "route", "controller", "service", "repository", "library"
    file_path: str = ""
    module: str = ""
    language: str = ""
    line_number: int = 0
    complexity: int = 0
    maintainability: float = 100.0
    call_depth: int = 0
    is_entry_point: bool = False
    is_recursive: bool = False
    is_dead: bool = False
    is_library: bool = False
    is_framework: bool = False


class CallGraphEdge(BaseModel):
    source: str
    target: str
    call_type: str = "direct"  # "direct", "async", "callback", "event", "import"
    call_count: int = 1
    is_cross_file: bool = False
    is_cross_module: bool = False
    is_recursive: bool = False
    is_library: bool = False
    file_path: str = ""
    line_number: int = 0


class ExecutionFlow(BaseModel):
    id: str
    name: str
    description: str = ""
    flow_type: str = "request"  # "request", "api", "cli", "background", "main", "framework"
    entry_node: str = ""
    exit_node: str = ""
    path: list[str] = []
    depth: int = 0
    is_complete: bool = False
    issues: list[str] = []


class CallGraphIssue(BaseModel):
    type: str  # "dead_chain", "recursive_loop", "circular_call", "unused_function", "orphan_method", "broken_path"
    severity: str  # "high", "medium", "low"
    description: str = ""
    nodes: list[str] = []
    detail: str = ""


class CallGraphStats(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    total_entry_points: int = 0
    total_execution_flows: int = 0
    total_issues: int = 0
    average_call_depth: float = 0.0
    max_call_depth: int = 0
    total_unused: int = 0
    total_recursive: int = 0
    total_circular: int = 0
    total_dead_chains: int = 0
    total_orphans: int = 0
    total_broken_paths: int = 0
    language_breakdown: dict[str, int] = {}
    node_type_counts: dict[str, int] = {}


class CallGraphResponse(BaseModel):
    nodes: list[CallGraphNode]
    edges: list[CallGraphEdge]
    execution_flows: list[ExecutionFlow]
    entry_points: list[CallGraphNode] = []
    stats: CallGraphStats
    issues: list[CallGraphIssue] = []
    ai_insights: list[str] = []
    analyzed_at: datetime


# ── Phase 3B.11: Semantic Code Intelligence ─────────────────────────────────


class SemanticComponent(BaseModel):
    id: str
    name: str
    type: str = ""
    sub_type: str = ""
    file_path: str = ""
    module: str = ""
    language: str = ""
    line_number: int = 0
    purpose: str = ""
    responsibility: str = ""
    role: str = ""
    business_context: str = ""
    summary: str = ""
    classification_reason: str = ""
    confidence: float = 0.0
    complexity: int = 0
    is_entry_point: bool = False
    is_exported: bool = False
    is_test: bool = False
    is_abstract: bool = False
    is_deprecated: bool = False
    has_ai_summary: bool = False


class SemanticRelationship(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str = ""
    description: str = ""
    strength: float = 1.0
    is_direct: bool = True
    file_path: str = ""
    line_number: int = 0


class SemanticSymbol(BaseModel):
    name: str
    kind: str = ""
    file_path: str = ""
    module: str = ""
    line_number: int = 0
    is_definition: bool = False
    is_exported: bool = False
    is_imported: bool = False
    resolved_target: str = ""
    aliases: list[str] = []


class BusinessFlow(BaseModel):
    id: str
    name: str
    description: str = ""
    flow_type: str = ""
    confidence: str = "medium"
    entry_components: list[str] = []
    exit_components: list[str] = []
    path: list[str] = []
    components: list[str] = []
    verified: bool = False


class SemanticCodeIssue(BaseModel):
    type: str
    severity: str = "info"
    component_id: str = ""
    description: str = ""
    detail: str = ""
    suggestion: str = ""


class SemanticSimilarity(BaseModel):
    component_a_id: str
    component_b_id: str
    similarity_type: str = ""
    score: float = 0.0
    description: str = ""
    shared_patterns: list[str] = []


class SemanticStats(BaseModel):
    total_components: int = 0
    total_files: int = 0
    total_classes: int = 0
    total_functions: int = 0
    type_breakdown: dict[str, int] = {}
    language_breakdown: dict[str, int] = {}
    total_relationships: int = 0
    total_business_flows: int = 0
    total_verified_flows: int = 0
    total_symbols: int = 0
    total_issues: int = 0
    total_similarities: int = 0
    component_type_counts: dict[str, int] = {}


class UnderstandingScore(BaseModel):
    overall: float = 0.0
    architecture: float = 0.0
    business_logic: float = 0.0
    dependencies: float = 0.0
    code_organization: float = 0.0
    execution_flow: float = 0.0
    semantic_relationships: float = 0.0
    maintainability: float = 0.0
    readability: float = 0.0
    has_entry_points: bool = False
    has_controllers: bool = False
    has_services: bool = False
    has_repositories: bool = False
    has_ml_components: bool = False
    has_forecast_components: bool = False
    component_coverage: float = 0.0
    flow_capture_rate: float = 0.0
    insight_count: int = 0


class KnowledgeGraphNode(BaseModel):
    id: str
    label: str
    type: str = ""
    sub_type: str = ""
    file_path: str = ""
    module: str = ""
    importance: float = 1.0
    group: str = ""
    details: dict[str, Any] = {}


class KnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    relationship: str = ""
    weight: float = 1.0
    description: str = ""


class KnowledgeGraph(BaseModel):
    nodes: list[KnowledgeGraphNode] = []
    edges: list[KnowledgeGraphEdge] = []


class BusinessComponent(BaseModel):
    id: str
    name: str
    type: str = ""
    file_path: str = ""
    module: str = ""
    confidence: float = 0.0
    description: str = ""
    related_components: list[str] = []


class SemanticResponse(BaseModel):
    components: list[SemanticComponent]
    relationships: list[SemanticRelationship]
    symbols: list[SemanticSymbol]
    business_flows: list[BusinessFlow]
    issues: list[SemanticCodeIssue]
    similarities: list[SemanticSimilarity]
    stats: SemanticStats
    understanding_score: UnderstandingScore = None
    knowledge_graph: KnowledgeGraph = None
    business_components: list[BusinessComponent] = []
    ai_insights: list[str] = []
    analyzed_at: datetime


# ── Phase 3B.12: Unified AI Analyzer Dashboard ────────────────────────────────


class UnifiedHealthMetrics(BaseModel):
    overall_health: float = 0.0
    overall_quality: float = 0.0
    architecture_health: float = 0.0
    dependency_health: float = 0.0
    security_health: float = 0.0
    performance_health: float = 0.0
    maintainability: float = 0.0
    readiness: float = 0.0
    technical_debt: float = 0.0
    ai_confidence: float = 0.0


class UnifiedProjectScore(BaseModel):
    overall_score: float = 0.0
    architecture_score: float = 0.0
    code_quality_score: float = 0.0
    dependency_score: float = 0.0
    security_score: float = 0.0
    file_quality_score: float = 0.0
    function_quality_score: float = 0.0
    configuration_score: float = 0.0
    semantic_score: float = 0.0


class GlobalInsight(BaseModel):
    type: str
    label: str
    value: str
    severity: str = "info"
    source: str = ""
    detail: str = ""


class ExecutiveSummary(BaseModel):
    project_summary: str = ""
    architecture_summary: str = ""
    business_logic_summary: str = ""
    risk_summary: str = ""
    security_summary: str = ""
    recommendation_summary: str = ""
    future_improvements: list[str] = []


class KnowledgeHubItem(BaseModel):
    category: str
    label: str
    value: str
    link: str = ""
    count: int = 0


class HealthMapModule(BaseModel):
    name: str
    path: str = ""
    status: str = "healthy"
    issues: int = 0
    score: float = 0.0


class ProjectTimelineStage(BaseModel):
    stage: str
    label: str
    status: str = "pending"
    details: str = ""
    score: float = 0.0


class GlobalSearchResult(BaseModel):
    category: str
    items: list[dict] = []
    total: int = 0


class UnifiedIntelligenceResponse(BaseModel):
    health: UnifiedHealthMetrics
    scores: UnifiedProjectScore
    insights: list[GlobalInsight] = []
    executive_summary: ExecutiveSummary
    knowledge_hub: list[KnowledgeHubItem] = []
    health_map: list[HealthMapModule] = []
    timeline: list[ProjectTimelineStage] = []
    search_results: dict[str, GlobalSearchResult] = {}
    analyzed_at: datetime


# ── Phase 3C.1: Project Risk Intelligence ─────────────────────────────────────


class RiskScore(BaseModel):
    overall_risk: float = 0.0
    risk_level: str = "unknown"
    confidence_score: float = 0.0
    project_stability: float = 0.0
    maintainability_risk: float = 0.0
    architecture_risk: float = 0.0
    dependency_risk: float = 0.0
    security_risk: float = 0.0
    performance_risk: float = 0.0


class RiskImpact(BaseModel):
    business_impact: str = ""
    technical_impact: str = ""
    recommended_priority: str = "medium"


class RiskItem(BaseModel):
    name: str
    type: str
    severity: str = "medium"
    affected_files: list[str] = []
    affected_classes: list[str] = []
    affected_functions: list[str] = []
    impact: RiskImpact = RiskImpact()
    detail: str = ""
    recommendation: str = ""


class RiskHeatmapItem(BaseModel):
    name: str
    path: str = ""
    category: str = "file"
    risk_score: float = 0.0
    risk_level: str = "low"
    top_risks: list[str] = []


class RiskSummary(BaseModel):
    highest_risk_module: str = ""
    highest_risk_area: str = ""
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary_text: str = ""
    prioritized_recommendations: list[str] = []


class RiskIntelligenceResponse(BaseModel):
    risk_score: RiskScore
    risks: list[RiskItem] = []
    heatmap: list[RiskHeatmapItem] = []
    summary: RiskSummary = RiskSummary()
    search_results: dict[str, list[dict]] = {}
    analyzed_at: datetime


# ── Phase 3C.2: Security Intelligence ──────────────────────────────────────────


class SecurityScore(BaseModel):
    overall_security_score: float = 0.0
    security_health: float = 0.0
    security_confidence: float = 0.0
    security_readiness: float = 0.0
    risk_level: str = "unknown"


class SecurityFinding(BaseModel):
    name: str
    type: str
    severity: str = "medium"
    affected_files: list[str] = []
    affected_functions: list[str] = []
    detail: str = ""
    business_impact: str = ""
    technical_impact: str = ""
    recommended_fix: str = ""


class DependencySecurity(BaseModel):
    name: str
    severity: str = "medium"
    detail: str = ""
    recommendation: str = ""


class SecuritySummary(BaseModel):
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary_text: str = ""
    prioritized_recommendations: list[str] = []


class SecurityIntelligenceResponse(BaseModel):
    security_score: SecurityScore
    findings: list[SecurityFinding] = []
    dependency_issues: list[DependencySecurity] = []
    summary: SecuritySummary = SecuritySummary()
    analyzed_at: datetime


# ── Phase 3C.3: Performance Intelligence ───────────────────────────────────────


class PerformanceScore(BaseModel):
    overall_performance_score: float = 0.0
    performance_health: float = 0.0
    performance_readiness: float = 0.0
    optimization_potential: float = 0.0
    ai_confidence: float = 0.0
    risk_level: str = "unknown"


class PerformanceFinding(BaseModel):
    name: str
    type: str
    severity: str = "medium"
    estimated_cost: str = ""
    affected_files: list[str] = []
    affected_functions: list[str] = []
    detail: str = ""
    optimization_suggestion: str = ""
    estimated_gain: str = ""
    complexity_reduction: str = ""


class PerformanceSummary(BaseModel):
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary_text: str = ""
    prioritized_recommendations: list[str] = []


class PerformanceIntelligenceResponse(BaseModel):
    performance_score: PerformanceScore
    findings: list[PerformanceFinding] = []
    summary: PerformanceSummary = PerformanceSummary()
    analyzed_at: datetime


# ── Phase 3C.4: Maintainability Intelligence ──────────────────────────────────


class MaintainabilityScore(BaseModel):
    overall_maintainability_score: float = 0.0
    maintainability_health: float = 0.0
    technical_debt_score: float = 0.0
    refactoring_readiness: float = 0.0
    long_term_stability: float = 0.0
    readability: float = 0.0
    modularity: float = 0.0
    code_organization: float = 0.0
    ai_confidence: float = 0.0
    risk_level: str = "unknown"


class CodeSmellItem(BaseModel):
    name: str
    type: str
    severity: str = "medium"
    affected_files: list[str] = []
    affected_functions: list[str] = []
    affected_classes: list[str] = []
    description: str = ""
    refactoring_effort: str = ""
    ai_suggestion: str = ""


class TechnicalDebtEstimate(BaseModel):
    total_debt_hours: float = 0.0
    debt_level: str = "low"
    estimated_refactoring_effort: str = ""
    maintenance_cost: str = ""
    critical_file_count: int = 0
    high_file_count: int = 0
    medium_file_count: int = 0
    low_file_count: int = 0


class ModuleHealthScore(BaseModel):
    file_name: str = ""
    score: float = 0.0
    issues: list[str] = []
    complexity: float = 0.0
    cohesion: float = 0.0
    coupling: float = 0.0
    debt_estimate: str = ""


class MaintainabilitySummary(BaseModel):
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    informational_count: int = 0
    summary_text: str = ""
    prioritized_recommendations: list[str] = []


class MaintainabilityIntelligenceResponse(BaseModel):
    maintainability_score: MaintainabilityScore
    code_smells: list[CodeSmellItem] = []
    technical_debt: TechnicalDebtEstimate = TechnicalDebtEstimate()
    module_health: list[ModuleHealthScore] = []
    summary: MaintainabilitySummary = MaintainabilitySummary()
    analyzed_at: datetime


# ── Phase 3C.5: AI Refactoring Intelligence ───────────────────────────────────


class RefactoringScore(BaseModel):
    refactoring_score: float = 0.0
    project_cleanliness: float = 0.0
    code_organization: float = 0.0
    debt_reduction_potential: float = 0.0
    refactoring_readiness: float = 0.0
    ai_confidence: float = 0.0
    risk_level: str = "unknown"


class ImpactEstimate(BaseModel):
    estimated_files_changed: int = 0
    estimated_complexity_reduction: str = ""
    estimated_maintainability_improvement: str = ""
    estimated_risk: str = "low"


class RefactoringOpportunity(BaseModel):
    name: str
    type: str
    severity: str = "medium"
    affected_files: list[str] = []
    affected_classes: list[str] = []
    affected_functions: list[str] = []
    description: str = ""
    reason: str = ""
    recommendation: str = ""
    impact: ImpactEstimate = ImpactEstimate()
    expected_benefit: str = ""


class RefactoringSummary(BaseModel):
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary_text: str = ""
    roadmap: list[str] = []


class RefactoringIntelligenceResponse(BaseModel):
    refactoring_score: RefactoringScore
    opportunities: list[RefactoringOpportunity] = []
    summary: RefactoringSummary = RefactoringSummary()
    analyzed_at: datetime


# ── Phase 3C.6: Documentation Intelligence ────────────────────────────────────


class DocumentationScore(BaseModel):
    overall_documentation_score: float = 0.0
    documentation_coverage: float = 0.0
    documentation_quality: float = 0.0
    developer_readiness: float = 0.0
    ai_confidence: float = 0.0
    risk_level: str = "unknown"


class CodeDocumentationItem(BaseModel):
    type: str
    name: str
    file: str = ""
    documented: bool = False
    documentation_type: str = ""  # docstring / comment / inline
    line: int = 0
    quality: str = "missing"  # excellent / good / average / poor / missing


class ProjectDocItem(BaseModel):
    name: str
    path: str = ""
    doc_type: str = ""
    present: bool = False
    quality: str = "missing"
    size: int = 0
    completeness: str = "missing"  # comprehensive / partial / missing


class DocFinding(BaseModel):
    name: str
    type: str
    severity: str = "medium"
    affected_files: list[str] = []
    affected_functions: list[str] = []
    affected_classes: list[str] = []
    description: str = ""
    recommendation: str = ""
    estimated_improvement: str = ""


class DocumentationSummary(BaseModel):
    missing_readme: bool = False
    missing_license: bool = False
    missing_contributing: bool = False
    missing_changelog: bool = False
    missing_architecture_docs: bool = False
    coverage_percentage: float = 0.0
    documented_functions: int = 0
    undocumented_functions: int = 0
    documented_classes: int = 0
    undocumented_classes: int = 0
    files_with_comments: int = 0
    files_without_comments: int = 0
    summary_text: str = ""
    prioritized_recommendations: list[str] = []


class DocumentationIntelligenceResponse(BaseModel):
    documentation_score: DocumentationScore
    code_documentation: list[CodeDocumentationItem] = []
    project_docs: list[ProjectDocItem] = []
    findings: list[DocFinding] = []
    summary: DocumentationSummary = DocumentationSummary()
    analyzed_at: datetime


# ── Phase 3C.7: Test Intelligence ────────────────────────────────────────────


class TestScore(BaseModel):
    overall_test_score: float = 0.0
    test_coverage: float = 0.0
    testing_health: float = 0.0
    regression_readiness: float = 0.0
    ai_confidence: float = 0.0
    risk_level: str = "unknown"


class DetectedFramework(BaseModel):
    name: str
    type: str = ""  # python/js/java/e2e/etc.
    version: str = ""
    config_file: str = ""
    reliability: str = "unknown"  # high / medium / low / unknown


class TestFileInfo(BaseModel):
    path: str
    file_name: str
    framework: str = ""
    test_count: int = 0
    assertion_count: int = 0
    fixture_count: int = 0
    mock_count: int = 0
    test_types: list[str] = []  # unit / integration / api / e2e / performance / security / regression / smoke
    naming_quality: str = "unknown"
    organization_quality: str = "unknown"
    maintainability: str = "unknown"
    coverage_estimate: float = 0.0
    has_failures: bool = False
    lines_of_code: int = 0


class UntestedComponent(BaseModel):
    name: str
    type: str  # file / function / class / module
    path: str = ""
    risk: str = "medium"
    reason: str = ""
    suggested_test_type: str = ""
    priority: int = 0


class MissingTestCase(BaseModel):
    name: str
    module: str = ""
    type: str = "unit"
    severity: str = "medium"
    affected_file: str = ""
    suggestion: str = ""
    estimated_impact: str = ""


class TestQualityMetrics(BaseModel):
    naming_quality: float = 0.0
    assertion_density: float = 0.0
    coverage_depth: float = 0.0
    organization_score: float = 0.0
    maintainability_score: float = 0.0
    reliability_score: float = 0.0


class TestRecommendation(BaseModel):
    priority: int = 0
    category: str = ""
    title: str = ""
    description: str = ""
    suggested_framework: str = ""
    estimated_coverage_improvement: float = 0.0
    affected_modules: list[str] = []


class TestSummary(BaseModel):
    total_test_files: int = 0
    total_test_functions: int = 0
    total_test_classes: int = 0
    total_assertions: int = 0
    total_fixtures: int = 0
    total_mocks: int = 0
    untested_files: int = 0
    untested_functions: int = 0
    untested_classes: int = 0
    coverage_percentage: float = 0.0
    detected_frameworks: list[str] = []
    summary_text: str = ""
    prioritized_recommendations: list[str] = []


class TestIntelligenceResponse(BaseModel):
    test_score: TestScore
    detected_frameworks: list[DetectedFramework] = []
    test_files: list[TestFileInfo] = []
    untested_components: list[UntestedComponent] = []
    missing_test_cases: list[MissingTestCase] = []
    quality_metrics: TestQualityMetrics = TestQualityMetrics()
    recommendations: list[TestRecommendation] = []
    summary: TestSummary = TestSummary()
    analyzed_at: datetime


# ── Phase 3C.8: Production Readiness Intelligence ─────────────────────────────


class ProductionScore(BaseModel):
    overall_production_score: float = 0.0
    deployment_readiness: float = 0.0
    operational_readiness: float = 0.0
    maintainability_readiness: float = 0.0
    ai_confidence: float = 0.0


class ProductionFinding(BaseModel):
    name: str
    category: str = ""
    severity: str = "medium"
    affected_files: list[str] = []
    affected_components: list[str] = []
    detail: str = ""
    deployment_impact: str = ""
    business_impact: str = ""
    ai_recommendation: str = ""


class DeploymentDetection(BaseModel):
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    has_kubernetes: bool = False
    has_helm_charts: bool = False
    has_github_actions: bool = False
    has_gitlab_ci: bool = False
    has_azure_pipelines: bool = False
    has_jenkins: bool = False
    has_render_config: bool = False
    has_railway_config: bool = False
    has_vercel_config: bool = False
    has_netlify_config: bool = False
    has_deployment_scripts: bool = False
    detected_platforms: list[str] = []


class ConfigValidation(BaseModel):
    has_environment_variables: bool = False
    has_env_file: bool = False
    has_production_config: bool = False
    has_development_config: bool = False
    has_secret_management: bool = False
    has_database_config: bool = False
    has_cache_config: bool = False
    env_var_count: int = 0


class ReleaseReadiness(BaseModel):
    has_versioning: bool = False
    has_release_notes: bool = False
    has_build_scripts: bool = False
    has_startup_scripts: bool = False
    has_shutdown_handling: bool = False
    has_health_checks: bool = False


class ObservabilityDetection(BaseModel):
    has_logging: bool = False
    has_monitoring: bool = False
    has_metrics: bool = False
    has_tracing: bool = False
    has_health_endpoints: bool = False


class CategoryScore(BaseModel):
    architecture_readiness: float = 0.0
    security_readiness: float = 0.0
    performance_readiness: float = 0.0
    dependency_health: float = 0.0
    configuration_health: float = 0.0
    environment_configuration: float = 0.0
    logging_configuration: float = 0.0
    monitoring_support: float = 0.0
    error_handling: float = 0.0
    exception_handling: float = 0.0
    documentation_readiness: float = 0.0
    testing_readiness: float = 0.0
    cicd_readiness: float = 0.0


class ProductionSummary(BaseModel):
    classification: str = "Not Ready"
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary_text: str = ""
    prioritized_recommendations: list[str] = []


class ProductionReadinessResponse(BaseModel):
    production_score: ProductionScore
    category_scores: CategoryScore = CategoryScore()
    findings: list[ProductionFinding] = []
    deployment: DeploymentDetection = DeploymentDetection()
    config_validation: ConfigValidation = ConfigValidation()
    release_readiness: ReleaseReadiness = ReleaseReadiness()
    observability: ObservabilityDetection = ObservabilityDetection()
    summary: ProductionSummary = ProductionSummary()
    analyzed_at: datetime


# ── Phase 3C.9: AI Software Engineering Readiness ─────────────────────────────


class AiEngineeringScore(BaseModel):
    overall_engineering_score: float = 0.0
    engineering_readiness: float = 0.0
    ai_confidence: float = 0.0
    repair_readiness: float = 0.0
    automation_readiness: float = 0.0
    project_stability: float = 0.0


class EngineeringCapability(BaseModel):
    name: str
    score: float = 0.0
    status: str = "unknown"
    detail: str = ""
    requirements: list[str] = []


class ProjectHealthEntry(BaseModel):
    architecture_health: float = 0.0
    code_health: float = 0.0
    dependency_health: float = 0.0
    security_health: float = 0.0
    performance_health: float = 0.0
    maintainability_health: float = 0.0
    documentation_health: float = 0.0
    testing_health: float = 0.0
    production_health: float = 0.0


class RepairReadinessEstimate(BaseModel):
    files_safe_to_modify: int = 0
    high_risk_files: int = 0
    protected_files: int = 0
    configuration_files: int = 0
    core_modules: int = 0
    utility_modules: int = 0


class EngineeringRoadmapStage(BaseModel):
    step: int
    name: str
    status: str = "pending"
    readiness: float = 0.0
    detail: str = ""


class AiEngineeringFinding(BaseModel):
    name: str
    category: str = ""
    severity: str = "medium"
    detail: str = ""
    affected_modules: list[str] = []
    impact: str = ""
    recommendation: str = ""


class AiEngineeringSummary(BaseModel):
    summary_text: str = ""
    capabilities_ready: int = 0
    capabilities_total: int = 7
    critical_findings: int = 0
    high_findings: int = 0
    prioritized_recommendations: list[str] = []


class AiEngineeringReadinessResponse(BaseModel):
    engineering_score: AiEngineeringScore
    capabilities: list[EngineeringCapability] = []
    project_health: ProjectHealthEntry = ProjectHealthEntry()
    findings: list[AiEngineeringFinding] = []
    repair_readiness: RepairReadinessEstimate = RepairReadinessEstimate()
    roadmap: list[EngineeringRoadmapStage] = []
    summary: AiEngineeringSummary = AiEngineeringSummary()
    analyzed_at: datetime


# ── Phase 4.1.1: Bug Detection Workspace Initialization ────────────────────────


class DetectionModule(BaseModel):
    name: str
    ready: bool = True
    description: str = ""


class WorkspaceStatusCard(BaseModel):
    label: str
    status: str = "ready"


class BugDetectionWorkspaceResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str = ""
    language: str = ""
    project_type: str = ""
    workspace_status: str = "initialized"
    project_ready: bool = True
    analysis_ready: bool = True
    detection_ready: bool = True
    ai_confidence: float = 0.0
    total_files: int = 0
    total_folders: int = 0
    status_cards: list[WorkspaceStatusCard] = []
    detection_modules: list[DetectionModule] = []
    analysis_summary: str = ""
    initialized_at: datetime


# ── Phase 4.1.2: AI Bug Detection Pipeline Manager ─────────────────────────


class PipelineModule(BaseModel):
    name: str
    order: int
    status: str = "ready"
    description: str = ""
    purpose: str = ""
    required_inputs: list[str] = []
    expected_outputs: list[str] = []


class PipelineStatusResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str = ""
    pipeline_status: str = "initialized"
    overall_readiness: int = 0
    modules_ready: int = 0
    modules_total: int = 0
    modules_waiting: int = 0
    modules: list[PipelineModule] = []
    status_cards: list[WorkspaceStatusCard] = []
    summary: str = ""
    initialized_at: datetime


# ── Phase 4.2.1: Syntax & Compilation Bug Detection ──────────────────────


class SyntaxErrorInfo(BaseModel):
    bug_title: str
    description: str
    severity: str
    confidence: int
    language: str
    affected_file: str
    line_number: int
    column_number: int
    code_snippet: str
    ai_explanation: str
    suggested_fix: str
    error_type: str = "syntax"
    function_name: str = ""


class StaticCodeInfo(SyntaxErrorInfo):
    error_type: str = "static"
    function_name: str = ""


class SyntaxDetectionResult(BaseModel):
    file_path: str
    language: str
    errors: list[SyntaxErrorInfo] = []
    error_count: int = 0
    health_score: float = 100.0


class SyntaxDetectionResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    language: str
    status: str
    summary: str
    total_errors: int = 0
    total_files_scanned: int = 0
    files_with_errors: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    results: list[SyntaxDetectionResult] = []
    scanned_languages: list[str] = []


# ── Phase 4.2.2: Static Code Analysis ─────────────────────────────────────


class StaticCodeAnalysisResult(BaseModel):
    file_path: str
    language: str
    errors: list[StaticCodeInfo] = []
    error_count: int = 0
    health_score: float = 100.0


class StaticCodeAnalysisResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    language: str
    status: str
    summary: str
    total_errors: int = 0
    total_files_scanned: int = 0
    files_with_errors: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    results: list[StaticCodeAnalysisResult] = []
    scanned_languages: list[str] = []


# ── Phase 4.2.3: Dependency Bug Detection ─────────────────────────────────


class DependencyIssueInfo(StaticCodeInfo):
    error_type: str = "dependency"
    package_name: str = ""
    current_version: str = ""
    recommended_version: str = ""


class DependencyAnalysisResult(BaseModel):
    file_path: str
    language: str
    errors: list[DependencyIssueInfo] = []
    error_count: int = 0
    health_score: float = 100.0


class DependencyAnalysisResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    language: str
    status: str
    summary: str
    total_errors: int = 0
    total_files_scanned: int = 0
    files_with_errors: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    results: list[DependencyAnalysisResult] = []
    package_manager: str = ""
    declared_packages: list[str] = []


# ── Phase 4.2.4: Runtime Risk Detection ────────────────────────────────────


class RuntimeIssueInfo(StaticCodeInfo):
    error_type: str = "runtime"
    function_name: str = ""
    possible_impact: str = ""


class RuntimeAnalysisResult(BaseModel):
    file_path: str
    language: str
    errors: list[RuntimeIssueInfo] = []
    error_count: int = 0
    health_score: float = 100.0


class RuntimeAnalysisResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    language: str
    status: str
    summary: str
    total_errors: int = 0
    total_files_scanned: int = 0
    files_with_errors: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    results: list[RuntimeAnalysisResult] = []
    scanned_languages: list[str] = []


# ── Phase 4.2.5: Security Bug Detection ────────────────────────────────────


class SecurityIssueInfo(StaticCodeInfo):
    error_type: str = "security"
    security_category: str = ""
    security_impact: str = ""
    cwe_id: str = ""


class SecurityAnalysisResult(BaseModel):
    file_path: str
    language: str
    errors: list[SecurityIssueInfo] = []
    error_count: int = 0
    health_score: float = 100.0


class SecurityAnalysisResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    language: str
    status: str
    summary: str
    total_errors: int = 0
    total_files_scanned: int = 0
    files_with_errors: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    results: list[SecurityAnalysisResult] = []
    scanned_languages: list[str] = []
    security_score: int = 100


# ── Phase 4.2.6: Performance Bug Detection ─────────────────────────────────


class PerformanceIssueInfo(StaticCodeInfo):
    error_type: str = "performance"
    performance_category: str = ""
    estimated_cost: str = ""
    function_name: str = ""


class PerformanceAnalysisResult(BaseModel):
    file_path: str
    language: str
    errors: list[PerformanceIssueInfo] = []
    error_count: int = 0
    health_score: float = 100.0


class PerformanceAnalysisResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    language: str
    status: str
    summary: str
    total_errors: int = 0
    total_files_scanned: int = 0
    files_with_errors: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    results: list[PerformanceAnalysisResult] = []
    scanned_languages: list[str] = []


# ── Phase 4.2.7: Architecture & Logic Bug Detection ───────────────────────────


class ArchitectureIssueInfo(BaseModel):
    bug_title: str
    description: str
    severity: str
    confidence: int = 0
    language: str = ""
    affected_file: str = ""
    line_number: int = 0
    column_number: int = 0
    code_snippet: str = ""
    ai_explanation: str = ""
    suggested_fix: str = ""
    error_type: str = ""
    function_name: str = ""
    architecture_category: str = ""
    impact_scope: str = ""


class ArchitectureAnalysisResult(BaseModel):
    file_path: str
    language: str
    errors: list[ArchitectureIssueInfo] = []
    error_count: int = 0
    health_score: float = 100.0


class ArchitectureAnalysisResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    language: str
    status: str
    summary: str
    total_errors: int = 0
    total_files_scanned: int = 0
    files_with_errors: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    results: list[ArchitectureAnalysisResult] = []
    scanned_languages: list[str] = []


# ── Phase 4.3: AI Bug Prioritization ────────────────────────────────────────


class PrioritizedIssueInfo(BaseModel):
    bug_title: str
    description: str
    severity: str
    confidence: int = 0
    language: str = ""
    affected_file: str = ""
    line_number: int = 0
    column_number: int = 0
    code_snippet: str = ""
    ai_explanation: str = ""
    suggested_fix: str = ""
    error_type: str = ""
    function_name: str = ""
    source_engine: str = ""
    priority_score: float = 0.0
    cross_cutting_categories: list[str] = []
    recommended_action: str = ""


class PrioritizationFileGroup(BaseModel):
    file_path: str
    language: str
    total_issues: int = 0
    avg_priority: float = 0.0
    max_severity: str = "Low"
    issues: list[PrioritizedIssueInfo] = []


class PrioritizationResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    language: str
    status: str
    summary: str
    total_issues: int = 0
    total_files_affected: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    prioritized_issues: list[PrioritizedIssueInfo] = []
    file_groups: list[PrioritizationFileGroup] = []
    ai_recommendations: list[str] = []
    analyzed_at: datetime
