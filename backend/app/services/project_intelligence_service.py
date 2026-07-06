from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_intelligence_engine import ProjectIntelligenceEngine
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    CodeMetricsInfo,
    CodeOrganizationIssue,
    CodeStyleIssue,
    ComplexityDistributionItem,
    ComplexityInfo,
    LanguageDistribution,
    LanguageLocItem,
    LargestDirectoryItem,
    LargestFileItem,
    MaintainabilityGradeInfo,
    MetricRecommendation,
    ProjectIntelligenceResponse,
    ProjectStats,
)


class ProjectIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def detect(self, user_id: int, project_id: int) -> ProjectIntelligenceResponse:
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

        engine = ProjectIntelligenceEngine()
        result = engine.analyze(workspace_path)

        cm = result["code_metrics"]
        cx = result["complexity"]

        return ProjectIntelligenceResponse(
            code_metrics=CodeMetricsInfo(
                total_lines=cm["total_lines"],
                code_lines=cm["code_lines"],
                blank_lines=cm["blank_lines"],
                comment_lines=cm["comment_lines"],
                comment_ratio=cm["comment_ratio"],
                code_files=cm["code_files"],
                avg_file_size=cm["avg_file_size"],
                largest_file=cm["largest_file"],
                largest_file_size=cm["largest_file_size"],
                smallest_file=cm["smallest_file"],
                smallest_file_size=cm["smallest_file_size"],
                avg_function_length=cm["avg_function_length"],
                avg_class_size=cm["avg_class_size"],
            ),
            complexity=ComplexityInfo(
                total_functions=cx["total_functions"],
                total_classes=cx["total_classes"],
                avg_cyclomatic_complexity=cx["avg_cyclomatic_complexity"],
                max_complexity=cx["max_complexity"],
                low_count=cx["low_count"],
                medium_count=cx["medium_count"],
                high_count=cx["high_count"],
                critical_count=cx["critical_count"],
            ),
            complexity_distribution=[
                ComplexityDistributionItem(**d) for d in result["complexity_distribution"]
            ],
            maintainability=MaintainabilityGradeInfo(
                score=result["maintainability"]["score"],
                grade=result["maintainability"]["grade"],
            ),
            code_organization=[
                CodeOrganizationIssue(**o) for o in result["code_organization"]
            ],
            code_style=[
                CodeStyleIssue(**s) for s in result["code_style"]
            ],
            project_stats=ProjectStats(**result["project_stats"]),
            language_distribution=[
                LanguageDistribution(**d) for d in result["language_distribution"]
            ],
            language_loc=[
                LanguageLocItem(**l) for l in result["language_loc"]
            ],
            largest_directories=[
                LargestDirectoryItem(**d) for d in result["largest_directories"]
            ],
            largest_files=[
                LargestFileItem(**f) for f in result["largest_files"]
            ],
            recommendations=[
                MetricRecommendation(**r) for r in result["recommendations"]
            ],
            analyzed_at=datetime.now(timezone.utc),
        )
