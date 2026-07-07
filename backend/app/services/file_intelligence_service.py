from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.file_intelligence_engine import FileIntelligenceEngine
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    FileIntelligenceDetail,
    FileIntelligenceHealth,
    FileIntelligenceIssue,
    FileIntelligenceResponse,
    FileIntelligenceStats,
)


class FileIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> FileIntelligenceResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        if project.extraction_status != "extracted":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project workspace has not been extracted.",
            )

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace directory not found.",
            )

        engine = FileIntelligenceEngine()
        result = engine.analyze(workspace_path)

        files = [
            FileIntelligenceDetail(
                file_name=f["file_name"],
                path=f["path"],
                extension=f["extension"],
                language=f["language"],
                encoding=f["encoding"],
                size=f["size"],
                last_modified=f["last_modified"],
                total_lines=f["total_lines"],
                code_lines=f["code_lines"],
                blank_lines=f["blank_lines"],
                comment_lines=f["comment_lines"],
                functions=f["functions"],
                classes=f["classes"],
                imports=f["imports"],
                complexity=f["complexity"],
                health=FileIntelligenceHealth(**f["health"]),
                classification=f["classification"],
                tags=f["tags"],
                issues=[FileIntelligenceIssue(**i) for i in f["issues"]],
                ai_summary=f["ai_summary"],
            )
            for f in result["files"]
        ]

        return FileIntelligenceResponse(
            files=files,
            stats=FileIntelligenceStats(**result["stats"]),
            analyzed_at=datetime.now(timezone.utc),
        )
