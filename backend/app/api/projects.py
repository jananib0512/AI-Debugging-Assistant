from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.middleware.auth_middleware import require_auth
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.schemas.project_analyzer import (
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
    SourceCodeIntelligenceResponse,
    ComplexityAnalysisResponse,
    ConfigurationIntelligenceResponse,
    EntryPointDetectionResponse,
    FileAnalysisResponse,
    FileIntelligenceResponse,
    FrameworkIntelligenceResponse,
    FuncClassIntelligenceResponse,
    FunctionClassResponse,
    ImportDependencyResponse,
    ModuleDetectionResponse,
    ProductionReadinessResponse,
    ProjectInsightsResponse,
    ProjectIntelligenceResponse,
    RiskIntelligenceResponse,
    SecurityIntelligenceResponse,
    PerformanceIntelligenceResponse,
    DocumentationIntelligenceResponse,
    MaintainabilityIntelligenceResponse,
    RefactoringIntelligenceResponse,
    TestIntelligenceResponse,
    SemanticResponse,
    UnifiedIntelligenceResponse,
)
from app.services.architecture_detection_service import ArchitectureDetectionService
from app.services.call_graph_intelligence_service import CallGraphIntelligenceService
from app.services.semantic_intelligence_service import SemanticIntelligenceService
from app.services.unified_intelligence_service import UnifiedIntelligenceService
from app.services.risk_intelligence_service import RiskIntelligenceService
from app.services.security_intelligence_service import SecurityIntelligenceService
from app.services.performance_intelligence_service import PerformanceIntelligenceService
from app.services.documentation_intelligence_service import DocumentationIntelligenceService
from app.services.maintainability_intelligence_service import MaintainabilityIntelligenceService
from app.services.refactoring_intelligence_service import RefactoringIntelligenceService
from app.services.test_intelligence_service import TestIntelligenceService
from app.services.complexity_analysis_service import ComplexityAnalysisService
from app.services.configuration_intelligence_service import ConfigurationIntelligenceService
from app.services.entry_point_detection_service import EntryPointDetectionService
from app.services.framework_intelligence_service import FrameworkIntelligenceService
from app.services.module_detection_service import ModuleDetectionService
from app.services.project_insights_service import ProjectInsightsService
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.services.project_validation_service import ProjectValidationService
from app.services.code_quality_service import CodeQualityService
from app.services.file_analysis_service import FileAnalysisService
from app.services.file_intelligence_service import FileIntelligenceService
from app.services.function_class_service import FunctionClassService
from app.services.function_class_intelligence_service import FunctionClassIntelligenceService
from app.services.import_dependency_service import ImportDependencyService
from app.services.source_code_intelligence_service import SourceCodeIntelligenceService
from app.services.extraction_service import ExtractionService
from app.services.metadata_service import MetadataService
from app.services.ai_engineering_readiness_service import AiEngineeringReadinessService
from app.services.bug_detection_workspace_service import BugDetectionWorkspaceService
from app.services.bug_detection_pipeline_service import BugDetectionPipelineService
from app.services.syntax_detection_service import SyntaxDetectionService
from app.services.static_code_analysis_service import StaticCodeAnalysisService
from app.services.dependency_detection_service import DependencyDetectionService
from app.services.runtime_detection_service import RuntimeDetectionService
from app.services.security_detection_service import SecurityDetectionService
from app.services.performance_detection_service import PerformanceDetectionService
from app.services.architecture_bug_service import ArchitectureBugService
from app.services.bug_prioritization_service import BugPrioritizationService
from app.services.production_readiness_service import ProductionReadinessService
from app.services.project_analyzer_service import (
    ProjectAnalyzerCoreService,
    ProjectAnalyzerService,
)
from app.services.project_service import ProjectService
from app.services.upload_service import UploadService
from app.services.workspace_validation_service import WorkspaceValidationService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    request: ProjectCreateRequest,
    current_user: User = Depends(require_auth),
    service: ProjectService = Depends(ProjectService),
):
    return service.create(user_id=current_user.id, request=request)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    search: str | None = Query(None),
    current_user: User = Depends(require_auth),
    service: ProjectService = Depends(ProjectService),
):
    return service.list(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ProjectService = Depends(ProjectService),
):
    return service.get_by_id(user_id=current_user.id, project_id=project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    current_user: User = Depends(require_auth),
    service: ProjectService = Depends(ProjectService),
):
    return service.update(
        user_id=current_user.id, project_id=project_id, request=request
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ProjectService = Depends(ProjectService),
):
    service.delete(user_id=current_user.id, project_id=project_id)


@router.post("/{project_id}/upload", response_model=ProjectResponse)
def upload_project(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_auth),
    service: UploadService = Depends(UploadService),
):
    return service.upload(
        user_id=current_user.id, project_id=project_id, file=file
    )


@router.post("/{project_id}/extract", response_model=ProjectResponse)
def extract_project(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ExtractionService = Depends(ExtractionService),
):
    return service.extract(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/metadata")
def get_project_metadata(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: MetadataService = Depends(MetadataService),
):
    return service.get_metadata(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/workspace-validation")
def get_workspace_validation(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: WorkspaceValidationService = Depends(WorkspaceValidationService),
):
    return service.validate(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/analysis")
def get_project_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ProjectAnalyzerService = Depends(ProjectAnalyzerService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/analyzer", response_model=AnalyzerResponse)
def get_project_analyzer(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ProjectAnalyzerCoreService = Depends(ProjectAnalyzerCoreService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/entry-points", response_model=EntryPointDetectionResponse)
def get_entry_points(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: EntryPointDetectionService = Depends(EntryPointDetectionService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/architecture", response_model=ArchitectureDetectionResponse)
def get_architecture(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ArchitectureDetectionService = Depends(ArchitectureDetectionService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/modules", response_model=ModuleDetectionResponse)
def get_modules(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ModuleDetectionService = Depends(ModuleDetectionService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/frameworks", response_model=FrameworkIntelligenceResponse)
def get_frameworks(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: FrameworkIntelligenceService = Depends(FrameworkIntelligenceService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/configuration", response_model=ConfigurationIntelligenceResponse)
def get_configuration(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ConfigurationIntelligenceService = Depends(ConfigurationIntelligenceService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/complexity", response_model=ComplexityAnalysisResponse)
def get_complexity(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ComplexityAnalysisService = Depends(ComplexityAnalysisService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/project-insights", response_model=ProjectInsightsResponse)
def get_project_insights(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ProjectInsightsService = Depends(ProjectInsightsService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/project-intelligence", response_model=ProjectIntelligenceResponse)
def get_project_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ProjectIntelligenceService = Depends(ProjectIntelligenceService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/analyzer-validation", response_model=AnalyzerValidationResponse)
def get_analyzer_validation(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ProjectValidationService = Depends(ProjectValidationService),
):
    return service.validate(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/code-intelligence", response_model=SourceCodeIntelligenceResponse)
def get_code_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: SourceCodeIntelligenceService = Depends(SourceCodeIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/code-quality", response_model=CodeQualityResponse)
def get_code_quality(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: CodeQualityService = Depends(CodeQualityService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/file-analysis", response_model=FileAnalysisResponse)
def get_file_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: FileAnalysisService = Depends(FileAnalysisService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/function-class-analysis", response_model=FunctionClassResponse)
def get_function_class_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: FunctionClassService = Depends(FunctionClassService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/import-dependency-analysis", response_model=ImportDependencyResponse)
def get_import_dependency_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ImportDependencyService = Depends(ImportDependencyService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/file-intelligence", response_model=FileIntelligenceResponse)
def get_file_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: FileIntelligenceService = Depends(FileIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/function-class-intelligence", response_model=FuncClassIntelligenceResponse)
def get_function_class_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: FunctionClassIntelligenceService = Depends(FunctionClassIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/call-graph", response_model=CallGraphResponse)
def get_call_graph(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: CallGraphIntelligenceService = Depends(CallGraphIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/semantic-intelligence", response_model=SemanticResponse)
def get_semantic_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: SemanticIntelligenceService = Depends(SemanticIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/unified-intelligence", response_model=UnifiedIntelligenceResponse)
def get_unified_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: UnifiedIntelligenceService = Depends(UnifiedIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/risk-intelligence", response_model=RiskIntelligenceResponse)
def get_risk_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: RiskIntelligenceService = Depends(RiskIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/security-intelligence", response_model=SecurityIntelligenceResponse)
def get_security_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: SecurityIntelligenceService = Depends(SecurityIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/performance-intelligence", response_model=PerformanceIntelligenceResponse)
def get_performance_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: PerformanceIntelligenceService = Depends(PerformanceIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/maintainability-intelligence", response_model=MaintainabilityIntelligenceResponse)
def get_maintainability_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: MaintainabilityIntelligenceService = Depends(MaintainabilityIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/refactoring-intelligence", response_model=RefactoringIntelligenceResponse)
def get_refactoring_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: RefactoringIntelligenceService = Depends(RefactoringIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/documentation-intelligence", response_model=DocumentationIntelligenceResponse)
def get_documentation_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: DocumentationIntelligenceService = Depends(DocumentationIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/test-intelligence", response_model=TestIntelligenceResponse)
def get_test_intelligence(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: TestIntelligenceService = Depends(TestIntelligenceService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/production-readiness", response_model=ProductionReadinessResponse)
def get_production_readiness(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ProductionReadinessService = Depends(ProductionReadinessService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/ai-engineering-readiness", response_model=AiEngineeringReadinessResponse)
def get_ai_engineering_readiness(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: AiEngineeringReadinessService = Depends(AiEngineeringReadinessService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/workspace", response_model=BugDetectionWorkspaceResponse)
def get_bug_detection_workspace(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: BugDetectionWorkspaceService = Depends(BugDetectionWorkspaceService),
):
    return service.initialize(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/pipeline", response_model=PipelineStatusResponse)
def get_bug_detection_pipeline(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: BugDetectionPipelineService = Depends(BugDetectionPipelineService),
):
    return service.get_pipeline(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/syntax-detection", response_model=SyntaxDetectionResponse)
def get_syntax_detection(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: SyntaxDetectionService = Depends(SyntaxDetectionService),
):
    return service.detect(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/static-analysis", response_model=StaticCodeAnalysisResponse)
def get_static_code_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: StaticCodeAnalysisService = Depends(StaticCodeAnalysisService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/dependency-analysis", response_model=DependencyAnalysisResponse)
def get_dependency_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: DependencyDetectionService = Depends(DependencyDetectionService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/runtime-analysis", response_model=RuntimeAnalysisResponse)
def get_runtime_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: RuntimeDetectionService = Depends(RuntimeDetectionService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/security-analysis", response_model=SecurityAnalysisResponse)
def get_security_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: SecurityDetectionService = Depends(SecurityDetectionService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/performance-analysis", response_model=PerformanceAnalysisResponse)
def get_performance_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: PerformanceDetectionService = Depends(PerformanceDetectionService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/architecture-analysis", response_model=ArchitectureAnalysisResponse)
def get_architecture_analysis(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: ArchitectureBugService = Depends(ArchitectureBugService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )


@router.get("/{project_id}/bug-detection/prioritization", response_model=PrioritizationResponse)
def get_bug_prioritization(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: BugPrioritizationService = Depends(BugPrioritizationService),
):
    return service.analyze(
        user_id=current_user.id, project_id=project_id
    )
