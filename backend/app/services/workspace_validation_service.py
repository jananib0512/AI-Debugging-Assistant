import logging
from pathlib import Path

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_validation_repository import WorkspaceValidationRepository
from app.schemas.config_detection import ConfigFilesDetectionResult
from app.schemas.workspace_validation import (
    ConfigFilesSummary,
    ProjectStructureInfo,
    ValidationError,
    ValidationWarning,
    WorkspaceValidationResponse,
)
from app.services.configuration_detection_service import ConfigurationDetectionService

logger = logging.getLogger(__name__)

LARGE_PROJECT_SIZE = 100 * 1024 * 1024  # 100 MB
VERY_LARGE_PROJECT_SIZE = 500 * 1024 * 1024  # 500 MB
MINIMUM_SOURCE_FILES_FOR_ANALYSIS = 1


class WorkspaceValidationService:
    def __init__(self, db: Session = Depends(get_db)):
        self.project_repo = ProjectRepository(db)
        self.config_detection = ConfigurationDetectionService()

    def validate(
        self, user_id: int, project_id: int
    ) -> WorkspaceValidationResponse:
        project = self.project_repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.extraction_status != "extracted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has not been extracted yet. Please extract before running validation.",
            )

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace directory not found on disk. Please re-extract the project.",
            )

        config_result: ConfigFilesDetectionResult = self.config_detection.get_config_files(
            project_id, workspace_path,
        )
        repo = WorkspaceValidationRepository(workspace_path)
        return self._run_validation(repo, config_result, workspace_path, project.project_name)

    def _run_validation(
        self,
        repo: WorkspaceValidationRepository,
        config_result: ConfigFilesDetectionResult,
        workspace_path: Path,
        project_name: str,
    ) -> WorkspaceValidationResponse:
        data = repo.validate_all(config_result)
        warnings: list[ValidationWarning] = []
        errors: list[ValidationError] = []

        # Workspace existence
        if not data["workspace_exists"]:
            return WorkspaceValidationResponse(
                workspace_status="not_ready",
                validation_result="failed",
                warnings=[],
                errors=[ValidationError(
                    type="workspace_missing",
                    message="Workspace directory does not exist on disk",
                    detail=f"Expected at: {workspace_path}",
                )],
                project_structure=ProjectStructureInfo(
                    has_frontend=False, has_backend=False,
                    has_source_folders=False, has_config_folder=False,
                    has_assets_folder=False, has_documentation_folder=False,
                    has_hidden_folders=False, notes=[],
                ),
                config_files_summary=ConfigFilesSummary(
                    has_package_json=config_result.package_json,
                    has_requirements_txt=config_result.requirements_txt,
                    has_pyproject_toml=config_result.pyproject_toml,
                    has_dockerfile=config_result.dockerfile,
                    has_docker_compose=config_result.docker_compose,
                    has_readme=config_result.readme,
                    has_env_example=config_result.env_example,
                    files_found=config_result.files_found,
                    files_missing=config_result.files_missing,
                ),
                ready_for_analysis=False,
                summary="Workspace missing. Upload and extract the project before validation.",
            )

        # Accessibility
        if not data["workspace_accessible"]:
            errors.append(ValidationError(
                type="workspace_inaccessible",
                message="Workspace directory is not readable",
                detail=f"Cannot access: {workspace_path}",
            ))

        # Empty workspace
        if not data["workspace_not_empty"]:
            errors.append(ValidationError(
                type="workspace_empty",
                message="Workspace directory is empty or contains only ignored files",
                detail="No project files found in workspace",
            ))

        # Source files
        source_count = data["has_source_files"]
        if source_count == 0:
            errors.append(ValidationError(
                type="no_source_files",
                message="No readable source files found in workspace",
                detail="The workspace contains no files with recognized source code extensions",
            ))
        elif source_count < 10:
            warnings.append(ValidationWarning(
                type="very_few_source_files",
                message=f"Very few source files detected ({source_count})",
                detail="Projects typically contain more than a handful of source files",
            ))

        # Total file count
        total_files = data["total_file_count"]

        # Project size
        total_size = data["total_size_bytes"]
        if total_size > VERY_LARGE_PROJECT_SIZE:
            size_mb = total_size / (1024 * 1024)
            warnings.append(ValidationWarning(
                type="very_large_project",
                message=f"Project size ({size_mb:.0f} MB) exceeds recommended limit",
                detail="Very large projects may impact analysis performance",
            ))
        elif total_size > LARGE_PROJECT_SIZE:
            size_mb = total_size / (1024 * 1024)
            warnings.append(ValidationWarning(
                type="large_project",
                message=f"Large project detected ({size_mb:.0f} MB)",
                detail="Consider this when running analysis",
            ))

        # Corrupted files
        corrupted = data["corrupted_files"]
        if corrupted:
            errors.append(ValidationError(
                type="corrupted_files",
                message=f"Found {len(corrupted)} file(s) that cannot be read",
                detail="These files may be corrupt or have permission issues",
            ))

        # Invalid paths
        invalid = data["invalid_paths"]
        if invalid:
            errors.append(ValidationError(
                type="invalid_paths",
                message=f"Found {len(invalid)} invalid path(s) in workspace",
                detail="Some files have paths outside the expected workspace boundary",
            ))

        # Project structure
        structure = data["structure"]
        structure_info = ProjectStructureInfo(
            has_frontend=structure["has_frontend"],
            has_backend=structure["has_backend"],
            has_source_folders=structure["has_source_folders"],
            has_config_folder=structure["has_config_folder"],
            has_assets_folder=structure["has_assets_folder"],
            has_documentation_folder=structure["has_documentation_folder"],
            has_hidden_folders=structure["has_hidden_folders"],
            notes=structure["notes"],
        )

        for note in structure["notes"]:
            warnings.append(ValidationWarning(
                type="structure_note",
                message=note,
                detail=None,
            ))

        # Config files (single source of truth: config_result from centralized service)
        config_files_summary = ConfigFilesSummary(
            has_package_json=config_result.package_json,
            has_requirements_txt=config_result.requirements_txt,
            has_pyproject_toml=config_result.pyproject_toml,
            has_dockerfile=config_result.dockerfile,
            has_docker_compose=config_result.docker_compose,
            has_readme=config_result.readme,
            has_env_example=config_result.env_example,
            files_found=config_result.files_found,
            files_missing=config_result.files_missing,
        )

        if not config_result.readme:
            warnings.append(ValidationWarning(
                type="missing_readme",
                message="README missing",
                detail="Adding a README helps document your project",
            ))
        if not config_result.dockerfile:
            warnings.append(ValidationWarning(
                type="no_docker",
                message="Docker not configured",
                detail="Docker containerization enables consistent environments",
            ))
        has_dep_file = (
            config_result.package_json
            or config_result.requirements_txt
            or config_result.pyproject_toml
        )
        if not has_dep_file:
            warnings.append(ValidationWarning(
                type="no_dependency_file",
                message="No dependency file found",
                detail="package.json, requirements.txt, or pyproject.toml not detected",
            ))

        # Determine status
        ready = len(errors) == 0
        if ready and len(warnings) > 0:
            workspace_status = "ready_with_warnings"
            validation_result = "passed_with_warnings"
        elif ready:
            workspace_status = "ready"
            validation_result = "passed"
        else:
            workspace_status = "not_ready"
            validation_result = "failed"

        # Summary
        summary = self._generate_summary(
            workspace_status, errors, warnings,
            source_count, total_files, total_size, project_name,
        )

        return WorkspaceValidationResponse(
            workspace_status=workspace_status,
            validation_result=validation_result,
            warnings=warnings,
            errors=errors,
            project_structure=structure_info,
            config_files_summary=config_files_summary,
            ready_for_analysis=ready,
            summary=summary,
        )

    def _generate_summary(
        self,
        status: str,
        errors: list,
        warnings: list,
        source_count: int,
        total_files: int,
        total_size: int,
        project_name: str,
    ) -> str:
        if status == "not_ready":
            return (
                f"Validation failed for '{project_name}': "
                f"{len(errors)} error(s) found. "
                f"Resolve the issues above before proceeding with analysis."
            )
        if status == "ready_with_warnings":
            size_mb = total_size / (1024 * 1024)
            return (
                f"'{project_name}' is ready with {len(warnings)} warning(s). "
                f"Project contains {source_count} source files "
                f"({total_files} total files, {size_mb:.1f} MB)."
            )
        size_mb = total_size / (1024 * 1024)
        return (
            f"'{project_name}' is fully validated and ready for analysis. "
            f"Project contains {source_count} source files "
            f"({total_files} total files, {size_mb:.1f} MB)."
        )
