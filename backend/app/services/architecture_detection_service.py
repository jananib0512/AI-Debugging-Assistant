from datetime import datetime, timezone
from pathlib import Path

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
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace not found")

        scanner = ProjectScanner()
        scan = scanner.scan(Path(workspace_path))

        detector = ArchitectureDetectorRepository(scan)
        architectures = detector.detect_architectures()
        layers = detector.detect_layers()

        primary = None
        alternatives: list[DetectedArchitectureInfo] = []
        for i, arch in enumerate(architectures):
            info = DetectedArchitectureInfo(
                architecture=arch.get("architecture", "Unknown"),
                confidence=arch.get("confidence", 0),
                reason=arch.get("reason", ""),
                evidence=arch.get("evidence", []),
            )
            if i == 0:
                primary = info
            else:
                alternatives.append(info)

        detected_layers = [
            ArchitectureLayerInfo(name=layer["name"], directories=layer.get("directories", []))
            for layer in layers
        ]

        return ArchitectureDetectionResponse(
            primary_architecture=primary,
            alternative_architectures=alternatives,
            detected_layers=detected_layers,
            health=ArchitectureHealthDetail(
                score=primary.confidence if primary else 0,
                label="Detected" if primary else "Unknown",
            ),
            recommendations=[],
            visual_layers=[],
            organization_summary="",
            analyzed_at=datetime.now(timezone.utc),
        )
