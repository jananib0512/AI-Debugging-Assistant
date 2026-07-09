from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.bug_prioritization_engine import BugPrioritizationEngine
from app.schemas.project_analyzer import (
    PrioritizationResponse,
    PrioritizationFileGroup,
    PrioritizedIssueInfo,
)


class BugPrioritizationService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> PrioritizationResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        workspace_path = get_workspace_path(project_id)
        engine = BugPrioritizationEngine()
        result = engine.analyze(workspace_path)

        prioritized_issues = [PrioritizedIssueInfo(**i) for i in result.get("prioritized_issues", [])]
        file_groups = [PrioritizationFileGroup(**g) for g in result.get("file_groups", [])]
        language = project.language or ""

        if result["status"] == "unavailable":
            summary = f"The project workspace for \"{project.project_name}\" is not available."
        elif result["total_issues"] == 0:
            summary = f"Prioritization completed. No issues found across all detection engines."
        else:
            parts = [
                f"Prioritization completed. {result['total_issues']} issues ranked across "
                f"{result['total_files_affected']} files."
            ]
            if result["critical_count"] > 0:
                parts.append(f"{result['critical_count']} Critical.")
            if result["high_count"] > 0:
                parts.append(f"{result['high_count']} High.")
            if result["medium_count"] > 0:
                parts.append(f"{result['medium_count']} Medium.")
            if result["low_count"] > 0:
                parts.append(f"{result['low_count']} Low.")
            top = result.get("prioritized_issues", [])[:3]
            if top:
                files = list(set(i.get("affected_file", "") for i in top))
                parts.append(f"Top priority files: {', '.join(files[:3])}.")
            summary = " ".join(parts)

        return PrioritizationResponse(
            session_id=result["session_id"],
            project_id=project_id,
            project_name=project.project_name or "",
            language=language,
            status=result["status"],
            summary=summary,
            total_issues=result["total_issues"],
            total_files_affected=result["total_files_affected"],
            critical_count=result["critical_count"],
            high_count=result["high_count"],
            medium_count=result["medium_count"],
            low_count=result["low_count"],
            prioritized_issues=prioritized_issues,
            file_groups=file_groups,
            ai_recommendations=result.get("ai_recommendations", []),
            analyzed_at=datetime.now(timezone.utc),
        )
