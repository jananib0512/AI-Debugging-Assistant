import logging
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.detector import (
    collect_statistics,
    detect_databases,
    detect_devops,
    detect_frameworks,
    detect_languages,
    detect_package_manager,
)
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.config_detection import ConfigFilesDetectionResult
from app.schemas.project_metadata import DevOpsInfo, ProjectMetadataResponse, ProjectStatistics
from app.services.configuration_detection_service import ConfigurationDetectionService

logger = logging.getLogger(__name__)


class MetadataService:
    def __init__(self, db: Session = Depends(get_db)):
        self.project_repo = ProjectRepository(db)
        self.metadata_repo = MetadataRepository(db)
        self.config_detection = ConfigurationDetectionService()
        self.db = db

    def get_metadata(self, user_id: int, project_id: int) -> ProjectMetadataResponse:
        project = self.project_repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.extraction_status != "extracted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has not been extracted yet. Please extract the ZIP file first.",
            )

        cached = self.metadata_repo.get_by_project_id(project_id)
        if cached:
            return self._from_db_record(project.project_name, cached)

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace directory not found on disk",
            )

        try:
            languages = detect_languages(workspace_path)
            primary_lang = max(languages, key=languages.get) if languages else None
            secondary = sorted(
                [lang for lang in languages if lang != primary_lang],
                key=lambda l: languages[l],
                reverse=True,
            )

            frameworks = sorted(detect_frameworks(workspace_path, languages))
            package_manager = detect_package_manager(workspace_path)
            databases = detect_databases(workspace_path)
            devops_data = detect_devops(workspace_path)
            config_result: ConfigFilesDetectionResult = self.config_detection.get_config_files(
                project_id, workspace_path,
            )
            statistics = collect_statistics(workspace_path)

            now = datetime.now(timezone.utc)

            self.metadata_repo.upsert(project_id, {
                "primary_language": primary_lang,
                "secondary_languages": secondary[:5],
                "framework": frameworks[0] if frameworks else None,
                "package_manager": package_manager,
                "databases": databases,
                "docker": bool(devops_data.get("docker", False)),
                "docker_compose": bool(devops_data.get("docker_compose", False)),
                "kubernetes": bool(devops_data.get("kubernetes", False)),
                "ci_cd": list(devops_data.get("ci_cd", [])),
                "config_files": config_result.files_found,
                "has_readme": config_result.readme,
                "detected_languages": languages,
                "total_files": statistics["total_files"],
                "total_folders": statistics["total_folders"],
                "total_size_bytes": statistics["total_size_bytes"],
                "source_files": statistics["source_files"],
                "config_files_count": statistics["config_files_count"],
                "documentation_files": statistics["documentation_files"],
                "image_files": statistics["image_files"],
                "video_files": statistics["video_files"],
                "asset_files": statistics["asset_files"],
                "last_scanned_at": now,
            })

            return ProjectMetadataResponse(
                project_name=project.project_name,
                project_type=primary_lang,
                primary_language=primary_lang,
                secondary_languages=secondary[:5],
                languages=languages,
                frameworks=frameworks,
                package_manager=package_manager,
                databases=databases,
                devops=DevOpsInfo(
                    docker=bool(devops_data.get("docker", False)),
                    docker_compose=bool(devops_data.get("docker_compose", False)),
                    kubernetes=bool(devops_data.get("kubernetes", False)),
                    ci_cd=list(devops_data.get("ci_cd", [])),
                ),
                config_files=config_result.files_found,
                has_readme=config_result.readme,
                statistics=ProjectStatistics(**statistics),
                last_scanned_at=now,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Metadata detection failed for project %s", project_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze project: {str(e)}",
            )

    def _from_db_record(
        self, project_name: str, record
    ) -> ProjectMetadataResponse:
        languages = record.detected_languages or {}
        primary_lang = record.primary_language
        secondary = record.secondary_languages or []
        frameworks_list = [record.framework] if record.framework else []
        databases_list = record.databases or []
        config_files_list = record.config_files or []
        ci_cd_list = record.ci_cd or []

        return ProjectMetadataResponse(
            project_name=project_name,
            project_type=primary_lang,
            primary_language=primary_lang,
            secondary_languages=secondary,
            languages=languages,
            frameworks=frameworks_list,
            package_manager=record.package_manager,
            databases=databases_list,
            devops=DevOpsInfo(
                docker=record.docker,
                docker_compose=record.docker_compose,
                kubernetes=record.kubernetes,
                ci_cd=ci_cd_list,
            ),
            config_files=config_files_list,
            has_readme=record.has_readme,
            statistics=ProjectStatistics(
                total_files=record.total_files,
                total_folders=record.total_folders,
                total_size_bytes=record.total_size_bytes,
                source_files=record.source_files,
                config_files_count=record.config_files_count,
                documentation_files=record.documentation_files,
                image_files=record.image_files,
                video_files=record.video_files,
                asset_files=record.asset_files,
            ),
            last_scanned_at=record.last_scanned_at,
        )
