from datetime import datetime

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
