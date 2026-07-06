from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_validation_engine import ProjectValidationEngine
from app.schemas.project_analyzer import (
    AnalyzerValidationResponse,
    ConsistencyCheck,
    SelfHealingAction,
    ValidationReportItem,
)
from app.services.architecture_detection_service import ArchitectureDetectionService
from app.services.configuration_intelligence_service import ConfigurationIntelligenceService
from app.services.entry_point_detection_service import EntryPointDetectionService
from app.services.framework_intelligence_service import FrameworkIntelligenceService
from app.services.module_detection_service import ModuleDetectionService
from app.services.project_analyzer_service import ProjectAnalyzerCoreService
from app.services.project_insights_service import ProjectInsightsService
from app.services.project_intelligence_service import ProjectIntelligenceService


class ProjectValidationService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)
        self._analyzer_service = ProjectAnalyzerCoreService(db)
        self._ep_service = EntryPointDetectionService(db)
        self._arch_service = ArchitectureDetectionService(db)
        self._mod_service = ModuleDetectionService(db)
        self._fw_service = FrameworkIntelligenceService(db)
        self._ci_service = ConfigurationIntelligenceService(db)
        self._pi_service = ProjectIntelligenceService(db)
        self._insights_service = ProjectInsightsService(db)

    def validate(self, user_id: int, project_id: int) -> AnalyzerValidationResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if project.extraction_status != "extracted":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project workspace has not been extracted.",
            )

        try:
            analyzer_data = self._analyzer_service.analyze(user_id, project_id)
            ep_data = self._ep_service.detect(user_id, project_id)
            arch_data = self._arch_service.detect(user_id, project_id)
            mod_data = self._mod_service.detect(user_id, project_id)
            fw_data = self._fw_service.detect(user_id, project_id)
            ci_data = self._ci_service.detect(user_id, project_id)
            pi_data = self._pi_service.detect(user_id, project_id)
            insights_data = self._insights_service.detect(user_id, project_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to gather analyzer data for validation: {e}",
            )

        engine = ProjectValidationEngine()
        result = engine.validate(
            analyzer_data=analyzer_data.model_dump() if hasattr(analyzer_data, "model_dump") else {},
            ep_data=ep_data.model_dump() if hasattr(ep_data, "model_dump") else {},
            arch_data=arch_data.model_dump() if hasattr(arch_data, "model_dump") else {},
            mod_data=mod_data.model_dump() if hasattr(mod_data, "model_dump") else {},
            fw_data=fw_data.model_dump() if hasattr(fw_data, "model_dump") else {},
            ci_data=ci_data.model_dump() if hasattr(ci_data, "model_dump") else {},
            pi_data=pi_data.model_dump() if hasattr(pi_data, "model_dump") else {},
            insights_data=insights_data.model_dump() if hasattr(insights_data, "model_dump") else {},
        )

        return AnalyzerValidationResponse(
            consistency_score=result["consistency_score"],
            classification=result["classification"],
            passed_checks=result["passed_checks"],
            failed_checks=result["failed_checks"],
            warnings=result["warnings"],
            critical_errors=result["critical_errors"],
            checks=[ConsistencyCheck(**c) for c in result["checks"]],
            validation_report=[ValidationReportItem(**r) for r in result["validation_report"]],
            self_healing=[SelfHealingAction(**s) for s in result["self_healing"]],
            recommendations=result["recommendations"],
            analyzed_at=datetime.now(timezone.utc),
        )
