from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.dependency_detection_engine import DependencyDetectionEngine
from app.schemas.project_analyzer import (
    DependencyAnalysisResponse,
    DependencyAnalysisResult,
    DependencyIssueInfo,
)


class DependencyDetectionService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> DependencyAnalysisResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        workspace_path = get_workspace_path(project_id)
        engine = DependencyDetectionEngine()
        result = engine.analyze(workspace_path)

        results = [DependencyAnalysisResult(**r) for r in result.get("results", [])]
        language = project.language or result.get("package_manager", "")

        if result["status"] == "unavailable":
            summary = f"The project workspace for \"{project.project_name}\" is not available."
        elif result["total_errors"] == 0:
            summary = f"Dependency analysis completed. No dependency issues detected. All packages are properly configured."
        else:
            parts = [f"Dependency analysis completed. {result['total_errors']} dependency issues detected."]
            if result["critical_count"] > 0:
                parts.append(f"{result['critical_count']} Critical.")
            if result["high_count"] > 0:
                parts.append(f"{result['high_count']} High.")
            if result["medium_count"] > 0:
                parts.append(f"{result['medium_count']} Medium.")
            if result["low_count"] > 0:
                parts.append(f"{result['low_count']} Low.")
            parts.append("The project has dependency issues that should be addressed.")
            summary = " ".join(parts)

        return DependencyAnalysisResponse(
            session_id=result["session_id"],
            project_id=project_id,
            project_name=project.project_name or "",
            language=language,
            status=result["status"],
            summary=summary,
            total_errors=result["total_errors"],
            total_files_scanned=result["total_files_scanned"],
            files_with_errors=result["files_with_errors"],
            critical_count=result["critical_count"],
            high_count=result["high_count"],
            medium_count=result["medium_count"],
            low_count=result["low_count"],
            results=results,
            package_manager=result.get("package_manager", ""),
            declared_packages=result.get("declared_packages", []),
        )
