from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.project_scanner import ProjectScanner
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.module_detector import ModuleDetectorRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    DetectedModuleInfo,
    ModuleDetectionResponse,
    ModuleSummaryInfo,
)


class ModuleDetectionService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)
        self._metadata_repo = MetadataRepository(db)

    def detect(self, user_id: int, project_id: int) -> ModuleDetectionResponse:
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
        detector = ModuleDetectorRepository(scan_result)
        raw_modules = detector.detect_modules()

        modules: list[DetectedModuleInfo] = []
        detected_count = 0
        missing_count = 0
        core_detected = 0
        core_total = 0
        optional_detected = 0
        optional_total = 0

        for m in raw_modules:
            info = DetectedModuleInfo(
                module_name=m["module_name"],
                status=m["status"],
                detected_folder=m["detected_folder"],
                confidence=m["confidence"],
                reason=m["reason"],
            )
            modules.append(info)

            if m["core"]:
                core_total += 1
                if m["status"] == "Detected":
                    core_detected += 1
            else:
                optional_total += 1
                if m["status"] == "Detected":
                    optional_detected += 1

            if m["status"] == "Detected":
                detected_count += 1
            else:
                missing_count += 1

        return ModuleDetectionResponse(
            modules=modules,
            summary=ModuleSummaryInfo(
                total_modules=len(modules),
                detected_count=detected_count,
                missing_count=missing_count,
                core_detected=core_detected,
                core_total=core_total,
                optional_detected=optional_detected,
                optional_total=optional_total,
            ),
            analyzed_at=datetime.now(timezone.utc),
        )
