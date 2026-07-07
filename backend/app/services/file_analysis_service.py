from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.file_analysis_engine import FileAnalysisEngine
from app.schemas.project_analyzer import (
    FileAnalysisDetail,
    FileAnalysisIssue,
    FileAnalysisResponse,
    FileMetricScores,
)


class FileAnalysisService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> FileAnalysisResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Project workspace has not been extracted.")

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Workspace directory not found.")

        engine = FileAnalysisEngine()
        result = engine.analyze(workspace_path)

        return FileAnalysisResponse(
            files=[FileAnalysisDetail(
                path=f["path"],
                file_name=f["file_name"],
                extension=f["extension"],
                language=f["language"],
                size=f["size"],
                total_lines=f["total_lines"],
                code_lines=f["code_lines"],
                blank_lines=f["blank_lines"],
                comment_lines=f["comment_lines"],
                functions=f["functions"],
                classes=f["classes"],
                imports=f["imports"],
                complexity=f["complexity"],
                scores=FileMetricScores(**f["scores"]),
                health=f["health"],
                tags=f["tags"],
                ai_summary=f["ai_summary"],
                issues=[FileAnalysisIssue(**iss) for iss in f["issues"]],
            ) for f in result["files"]],
            total_files=result["total_files"],
            language_counts=result["language_counts"],
            analyzed_at=datetime.now(timezone.utc),
        )
