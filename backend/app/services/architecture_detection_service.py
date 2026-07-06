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

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workspace not extracted")

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workspace directory not found")

        if not any(workspace_path.iterdir()):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workspace is empty")

        scanner = ProjectScanner()
        scan_result = scanner.scan(workspace_path)
        detector = ArchitectureDetectorRepository(scan_result)
        arch_results = detector.detect_architectures()
        layer_results = detector.detect_layers()

        primary: DetectedArchitectureInfo | None = None
        alternatives: list[DetectedArchitectureInfo] = []

        for i, arch in enumerate(arch_results):
            info = DetectedArchitectureInfo(
                architecture=arch["architecture"],
                confidence=arch["confidence"],
                reason=arch["reason"],
                evidence=arch["evidence"],
            )
            if i == 0 and arch["confidence"] >= 20:
                primary = info
            elif arch["confidence"] >= 10:
                alternatives.append(info)

        detected_layers = [
            ArchitectureLayerInfo(name=layer["name"], directories=layer["directories"])
            for layer in layer_results
        ]

        arch_name = primary.architecture if primary else "Unknown"
        health = detector.compute_health(arch_name)
        recommendations = detector.generate_recommendations()
        visual_layers = detector.compute_visual_layers()
        organization_summary = detector.compute_organization_summary()

        return ArchitectureDetectionResponse(
            primary_architecture=primary,
            alternative_architectures=alternatives,
            detected_layers=detected_layers,
            health=ArchitectureHealthDetail(
                score=health["score"],
                label=health["label"],
                details=health.get("details", {}),
            ),
            recommendations=recommendations,
            visual_layers=visual_layers,
            organization_summary=organization_summary,
            analyzed_at=datetime.now(timezone.utc),
        )
