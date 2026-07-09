from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.bug_detection_workspace_engine import BugDetectionWorkspaceEngine
from app.schemas.project_analyzer import (
    BugDetectionWorkspaceResponse,
    DetectionModule,
    WorkspaceStatusCard,
)


class BugDetectionWorkspaceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def initialize(self, user_id: int, project_id: int) -> BugDetectionWorkspaceResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        workspace_path = get_workspace_path(project_id)
        engine = BugDetectionWorkspaceEngine()
        result = engine.analyze(workspace_path)

        if result["workspace_status"] == "missing":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project workspace has not been extracted. Please extract the project first.",
            )

        status_cards = [WorkspaceStatusCard(**c) for c in result.get("status_cards", [])]
        detection_modules = [DetectionModule(**m) for m in result.get("detection_modules", [])]

        language_desc = f"Language: {project.language}" if project.language else ""
        summary_parts = [f"Bug detection workspace initialized for project \"{project.project_name}\"."]
        if language_desc:
            summary_parts.append(language_desc)
        if result["total_files"] > 0:
            summary_parts.append(f"{result['total_files']} files and {result['total_folders']} folders detected.")
        if result["detection_ready"]:
            summary_parts.append("All detection modules are ready.")
        analysis_summary = " ".join(summary_parts)

        return BugDetectionWorkspaceResponse(
            session_id=result["session_id"],
            project_id=project_id,
            project_name=project.project_name or "",
            language=project.language or "",
            project_type=project.language or "",
            workspace_status=result["workspace_status"],
            project_ready=result["project_ready"],
            analysis_ready=result["analysis_ready"],
            detection_ready=result["detection_ready"],
            ai_confidence=result["ai_confidence"],
            total_files=result["total_files"],
            total_folders=result["total_folders"],
            status_cards=status_cards,
            detection_modules=detection_modules,
            analysis_summary=analysis_summary,
            initialized_at=datetime.now(timezone.utc),
        )
