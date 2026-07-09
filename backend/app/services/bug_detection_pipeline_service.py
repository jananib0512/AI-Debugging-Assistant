from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.bug_detection_pipeline_engine import BugDetectionPipelineEngine
from app.schemas.project_analyzer import (
    PipelineStatusResponse,
    PipelineModule,
    WorkspaceStatusCard,
)


class BugDetectionPipelineService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def get_pipeline(self, user_id: int, project_id: int) -> PipelineStatusResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        workspace_path = get_workspace_path(project_id)
        engine = BugDetectionPipelineEngine()
        result = engine.analyze(workspace_path)

        status_cards = [WorkspaceStatusCard(**c) for c in result.get("status_cards", [])]
        modules = [PipelineModule(**m) for m in result.get("modules", [])]

        summary_parts = [
            f"Project analysis has completed successfully for \"{project.project_name}\"."
        ]
        if result["pipeline_status"] == "initialized":
            summary_parts.append("The Bug Detection Pipeline has been initialized.")
            summary_parts.append("All detection modules are ready.")
            summary_parts.append("No bug detection has started yet.")
            summary_parts.append("The project is ready to begin AI Bug Detection.")
        elif result["pipeline_status"] == "unavailable":
            summary_parts.append("The Bug Detection Pipeline is unavailable.")
            summary_parts.append("Please ensure the project workspace has been extracted and analyzed.")
        summary = " ".join(summary_parts)

        return PipelineStatusResponse(
            session_id=result["session_id"],
            project_id=project_id,
            project_name=project.project_name or "",
            pipeline_status=result["pipeline_status"],
            overall_readiness=result["overall_readiness"],
            modules_ready=result["modules_ready"],
            modules_total=result["modules_total"],
            modules_waiting=result["modules_waiting"],
            modules=modules,
            status_cards=status_cards,
            summary=summary,
            initialized_at=datetime.now(timezone.utc),
        )
