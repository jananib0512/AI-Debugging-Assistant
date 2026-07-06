import logging
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.project_scanner import ProjectScanner
from app.repositories.entry_point_detector import EntryPointDetector
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    DetectedEntryPointInfo,
    EntryPointDetectionResponse,
)

logger = logging.getLogger(__name__)


class EntryPointDetectionService:
    def __init__(self, db: Session = Depends(get_db)):
        self.project_repo = ProjectRepository(db)
        self.metadata_repo = MetadataRepository(db)

    def detect(self, user_id: int, project_id: int) -> EntryPointDetectionResponse:
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project workspace has not been extracted.")

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace directory not found.")

        metadata = self.metadata_repo.get_by_project_id(project_id)
        if not metadata:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project metadata not available.")

        scanner = ProjectScanner()
        scan_result = scanner.scan(workspace_path)
        detector = EntryPointDetector(workspace_path, scan_result)
        candidates = detector.detect()

        entry_points = [
            DetectedEntryPointInfo(
                entry_file=c["entry_file"],
                framework=c["framework"],
                project_type=c["project_type"],
                confidence=c["confidence"],
                reason=c["reason"],
            )
            for c in candidates
        ]

        primary = entry_points[0] if entry_points else None
        alternatives = entry_points[1:] if len(entry_points) > 1 else []

        return EntryPointDetectionResponse(
            primary_entry_point=primary,
            alternative_entry_points=alternatives,
            total_entry_points=len(entry_points),
            analyzed_at=datetime.now(timezone.utc),
        )
