from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.project_insights_engine import ProjectInsightsEngine
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    HealthScoreInfo,
    InsightStrength,
    InsightWeakness,
    MaintainabilityGradeInfo,
    PerformanceInsight,
    ProjectInsightsResponse,
    ReadinessDetail,
    RecommendedAction,
    RiskAnalysisInfo,
    ScalabilityInfo,
    SecurityInsight,
    ProjectCodeQualityInsight,
)
from app.services.architecture_detection_service import ArchitectureDetectionService
from app.services.configuration_intelligence_service import ConfigurationIntelligenceService
from app.services.entry_point_detection_service import EntryPointDetectionService
from app.services.framework_intelligence_service import FrameworkIntelligenceService
from app.services.module_detection_service import ModuleDetectionService
from app.services.project_analyzer_service import ProjectAnalyzerCoreService
from app.services.project_intelligence_service import ProjectIntelligenceService


class ProjectInsightsService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)
        self._analyzer_service = ProjectAnalyzerCoreService(db)
        self._ep_service = EntryPointDetectionService(db)
        self._arch_service = ArchitectureDetectionService(db)
        self._mod_service = ModuleDetectionService(db)
        self._fw_service = FrameworkIntelligenceService(db)
        self._ci_service = ConfigurationIntelligenceService(db)
        self._pi_service = ProjectIntelligenceService(db)

    def detect(self, user_id: int, project_id: int) -> ProjectInsightsResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project workspace has not been extracted.")

        try:
            analyzer_data = self._analyzer_service.analyze(user_id, project_id)
            ep_data = self._ep_service.detect(user_id, project_id)
            arch_data = self._arch_service.detect(user_id, project_id)
            mod_data = self._mod_service.detect(user_id, project_id)
            fw_data = self._fw_service.detect(user_id, project_id)
            ci_data = self._ci_service.detect(user_id, project_id)
            pi_data = self._pi_service.detect(user_id, project_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to gather analysis data: {e}",
            )

        engine = ProjectInsightsEngine()
        result = engine.analyze(
            analyzer_data=analyzer_data.model_dump() if hasattr(analyzer_data, "model_dump") else {},
            ep_data=ep_data.model_dump() if hasattr(ep_data, "model_dump") else {},
            arch_data=arch_data.model_dump() if hasattr(arch_data, "model_dump") else {},
            mod_data=mod_data.model_dump() if hasattr(mod_data, "model_dump") else {},
            fw_data=fw_data.model_dump() if hasattr(fw_data, "model_dump") else {},
            ci_data=ci_data.model_dump() if hasattr(ci_data, "model_dump") else {},
            pi_data=pi_data.model_dump() if hasattr(pi_data, "model_dump") else {},
        )

        return ProjectInsightsResponse(
            health_score=HealthScoreInfo(**result["health_score"]),
            ai_summary=result["ai_summary"],
            strengths=[InsightStrength(**s) for s in result["strengths"]],
            weaknesses=[InsightWeakness(**w) for w in result["weaknesses"]],
            risk_analysis=RiskAnalysisInfo(**result["risk_analysis"]),
            maintainability=MaintainabilityGradeInfo(**result["maintainability"]),
            maintainability_explanation=result["maintainability_explanation"],
            scalability=ScalabilityInfo(**result["scalability"]),
            performance_insights=[PerformanceInsight(**p) for p in result["performance_insights"]],
            security_insights=[SecurityInsight(**s) for s in result["security_insights"]],
            code_quality_insights=[ProjectCodeQualityInsight(**c) for c in result["code_quality_insights"]],
            recommended_actions=[RecommendedAction(**a) for a in result["recommended_actions"]],
            readiness_scores=[ReadinessDetail(**r) for r in result["readiness_scores"]],
            analyzed_at=datetime.now(timezone.utc),
        )
