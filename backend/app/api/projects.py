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
    AnalyzerResponse,
    AnalyzerValidationResponse,
    ArchitectureDetectionResponse,
    CodeQualityResponse,
    SourceCodeIntelligenceResponse,
    ComplexityAnalysisResponse,
    ConfigurationIntelligenceResponse,
    EntryPointDetectionResponse,
    FrameworkIntelligenceResponse,
    ModuleDetectionResponse,
    ProjectInsightsResponse,
    ProjectIntelligenceResponse,
)
from app.services.architecture_detection_service import ArchitectureDetectionService
from app.services.complexity_analysis_service import ComplexityAnalysisService
from app.services.configuration_intelligence_service import ConfigurationIntelligenceService
from app.services.entry_point_detection_service import EntryPointDetectionService
from app.services.framework_intelligence_service import FrameworkIntelligenceService
from app.services.module_detection_service import ModuleDetectionService
from app.services.project_insights_service import ProjectInsightsService
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.services.project_validation_service import ProjectValidationService
from app.services.code_quality_service import CodeQualityService
from app.services.source_code_intelligence_service import SourceCodeIntelligenceService
from app.services.extraction_service import ExtractionService
from app.services.metadata_service import MetadataService
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
