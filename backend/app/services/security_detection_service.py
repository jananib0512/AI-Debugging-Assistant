from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.security_detection_engine import SecurityDetectionEngine
from app.schemas.project_analyzer import (
    SecurityAnalysisResponse,
    SecurityAnalysisResult,
    SecurityIssueInfo,
)


class SecurityDetectionService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> SecurityAnalysisResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        workspace_path = get_workspace_path(project_id)
        engine = SecurityDetectionEngine()
        result = engine.analyze(workspace_path)

        results = [SecurityAnalysisResult(**r) for r in result.get("results", [])]
        language = project.language or ", ".join(result.get("scanned_languages", []))

        if result["status"] == "unavailable":
            summary = f"The project workspace for \"{project.project_name}\" is not available."
        elif result["total_errors"] == 0:
            summary = f"Security analysis completed. No vulnerabilities detected. Security score: {result.get('security_score', 100)}/100."
        else:
            parts = [f"Security analysis completed. {result['total_errors']} security issues detected."]
            if result["critical_count"] > 0:
                parts.append(f"{result['critical_count']} Critical vulnerabilities.")
            if result["high_count"] > 0:
                parts.append(f"{result['high_count']} High severity issues.")
            if result["medium_count"] > 0:
                parts.append(f"{result['medium_count']} Medium severity issues.")
            if result["low_count"] > 0:
                parts.append(f"{result['low_count']} Low severity issues.")
            parts.append(f"Security score: {result.get('security_score', 0)}/100.")
            parts.append("The project has security vulnerabilities that must be addressed before deployment.")
            summary = " ".join(parts)

        return SecurityAnalysisResponse(
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
            scanned_languages=result.get("scanned_languages", []),
            security_score=result.get("security_score", 100),
        )
