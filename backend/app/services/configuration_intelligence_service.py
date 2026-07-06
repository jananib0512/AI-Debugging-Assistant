from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.project_scanner import ProjectScanner
from app.repositories.configuration_intelligence_engine import ConfigurationIntelligenceEngine
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    CicdInfo,
    ConfigFileInfo,
    ConfigHealthInfo,
    ConfigWarning,
    ConfigurationIntelligenceResponse,
    DependencyValidationInfo,
    DockerValidationInfo,
    EnvironmentValidationInfo,
    ReadinessScores,
    SecurityCheckInfo,
)


class ConfigurationIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)
        self._metadata_repo = MetadataRepository(db)

    def detect(self, user_id: int, project_id: int) -> ConfigurationIntelligenceResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project workspace has not been extracted.")

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace directory not found.")

        metadata = self._metadata_repo.get_by_project_id(project_id)
        if not metadata:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project metadata not available.")

        scanner = ProjectScanner()
        scan_result = scanner.scan(workspace_path)
        engine = ConfigurationIntelligenceEngine(scan_result)
        analysis = engine.analyze()

        detected_files = [ConfigFileInfo(**d) for d in analysis["detected_files"]]
        missing_files = [ConfigFileInfo(**m) for m in analysis["missing_files"]]
        warnings = [ConfigWarning(**w) for w in analysis["warnings"]]

        health_data = analysis["health"]
        health = ConfigHealthInfo(score=health_data["score"], label=health_data["label"])

        return ConfigurationIntelligenceResponse(
            detected_files=detected_files,
            missing_files=missing_files,
            dependency_validation=[
                DependencyValidationInfo(**d) for d in analysis["dependency_validation"]
            ],
            environment_validation=[
                EnvironmentValidationInfo(**e) for e in analysis["environment_validation"]
            ],
            docker_validation=DockerValidationInfo(**analysis["docker_validation"]),
            cicd=[CicdInfo(**c) for c in analysis["cicd"]],
            security_checks=[SecurityCheckInfo(**s) for s in analysis["security_checks"]],
            scores=ReadinessScores(**analysis["scores"]),
            warnings=warnings,
            recommendations=analysis["recommendations"],
            health=health,
            readiness_score=analysis["readiness_score"],
            analyzed_at=datetime.now(timezone.utc),
        )
