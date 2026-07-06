from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.code_quality_engine import CodeQualityEngine
from app.schemas.project_analyzer import (
    CodeQualityAiRecommendation,
    CodeQualityAiSummary,
    CodeQualityCheck,
    CodeQualityInsight,
    CodeQualityIssue,
    CodeQualityLanguageBreakdown,
    CodeQualityResponse,
    CodeQualitySeverityCount,
    CodeQualityTopFile,
    QualityScoreInfo,
)


class CodeQualityService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> CodeQualityResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project workspace has not been extracted.")

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace directory not found.")

        engine = CodeQualityEngine()
        result = engine.analyze(workspace_path)

        return CodeQualityResponse(
            overall_score=QualityScoreInfo(**result["overall_score"]),
            maintainability_score=QualityScoreInfo(**result["maintainability_score"]),
            readability_score=QualityScoreInfo(**result["readability_score"]),
            complexity_score=QualityScoreInfo(**result["complexity_score"]),
            documentation_score=QualityScoreInfo(**result["documentation_score"]),
            security_score=QualityScoreInfo(**result["security_score"]),
            technical_debt_score=QualityScoreInfo(**result["technical_debt_score"]),
            checks=[CodeQualityCheck(
                check_name=c["check_name"],
                status=c["status"],
                severity=c["severity"],
                count=c["count"],
                issues=[CodeQualityIssue(**i) for i in c["issues"]],
            ) for c in result["checks"]],
            insights=[CodeQualityInsight(**i) for i in result["insights"]],
            recommendations=[CodeQualityAiRecommendation(**r) for r in result["recommendations"]],
            severity_counts=CodeQualitySeverityCount(**result["severity_counts"]),
            total_issues=result["total_issues"],
            top_problematic_files=[CodeQualityTopFile(**f) for f in result["top_problematic_files"]],
            top_clean_files=[CodeQualityTopFile(**f) for f in result["top_clean_files"]],
            language_breakdown=[CodeQualityLanguageBreakdown(**l) for l in result["language_breakdown"]],
            ai_summary=CodeQualityAiSummary(**result["ai_summary"]),
            analyzed_at=datetime.now(timezone.utc),
        )
