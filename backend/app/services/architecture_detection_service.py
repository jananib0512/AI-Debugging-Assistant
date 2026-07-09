from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.project_scanner import ProjectScanner
from app.repositories.architecture_detector import ArchitectureDetectorRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    ArchitectureDetectionResponse,
    ArchitectureHealthDetail,
    ArchitectureLayerInfo,
    DetectedArchitectureInfo,
)


class ArchitectureDetectionService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def detect(self, user_id: int, project_id: int) -> ArchitectureDetectionResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        workspace_path = get_workspace_path(project_id)
        scanner = ProjectScanner(workspace_path)
        scan = scanner.scan()

        detector = ArchitectureDetectorRepository(scan)
        result = detector.detect()

        return ArchitectureDetectionResponse(
            primary_architecture=result.get("primary_architecture"),
            alternative_architectures=result.get("alternative_architectures", []),
            detected_layers=result.get("detected_layers", []),
            health=result.get("health", ArchitectureHealthDetail(score=0, label="Unknown")),
            recommendations=result.get("recommendations", []),
            visual_layers=result.get("visual_layers", []),
            organization_summary=result.get("organization_summary", ""),
            analyzed_at=datetime.now(timezone.utc),
        )
