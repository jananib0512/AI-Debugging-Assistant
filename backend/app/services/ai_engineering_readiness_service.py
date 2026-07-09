from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.ai_engineering_readiness_engine import AiEngineeringReadinessEngine
from app.schemas.project_analyzer import (
    AiEngineeringFinding,
    AiEngineeringReadinessResponse,
    AiEngineeringScore,
    AiEngineeringSummary,
    EngineeringCapability,
    EngineeringRoadmapStage,
    ProjectHealthEntry,
    RepairReadinessEstimate,
)


class AiEngineeringReadinessService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> AiEngineeringReadinessResponse:
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

        data = self._aggregate_all_engines(workspace_path)
        engine = AiEngineeringReadinessEngine()
        result = engine.analyze(
            workspace_path,
            project_analysis=data.get("project_analysis"),
            code_intel=data.get("code_intel"),
            code_quality=data.get("code_quality"),
            file_analysis=data.get("file_analysis"),
            dep_analysis=data.get("dep_analysis"),
            call_graph=data.get("call_graph"),
            semantic=data.get("semantic"),
            config_intel=data.get("config_intel"),
            recommendations=data.get("recommendations"),
            security_intel=data.get("security_intel"),
            performance_intel=data.get("performance_intel"),
            maintainability_intel=data.get("maintainability_intel"),
            documentation_intel=data.get("documentation_intel"),
            test_intel=data.get("test_intel"),
            production_intel=data.get("production_intel"),
        )

        score = AiEngineeringScore(**result["engineering_score"])
        capabilities = [EngineeringCapability(**c) for c in result.get("capabilities", [])]
        health = ProjectHealthEntry(**result["project_health"])
        findings = [AiEngineeringFinding(**f) for f in result.get("findings", [])]
        repair = RepairReadinessEstimate(**result["repair_readiness"])
        roadmap = [EngineeringRoadmapStage(**s) for s in result.get("roadmap", [])]
        summary = AiEngineeringSummary(**result["summary"])

        return AiEngineeringReadinessResponse(
            engineering_score=score,
            capabilities=capabilities,
            project_health=health,
            findings=findings,
            repair_readiness=repair,
            roadmap=roadmap,
            summary=summary,
            analyzed_at=datetime.now(timezone.utc),
        )

    def _aggregate_all_engines(self, workspace_path: Path) -> dict:
        result = {}

        try:
            from app.repositories.project_intelligence_engine import ProjectIntelligenceEngine
            result["project_analysis"] = ProjectIntelligenceEngine().analyze(workspace_path)
        except Exception:
            result["project_analysis"] = None

        try:
            from app.repositories.source_code_intelligence_engine import SourceCodeIntelligenceEngine
            result["code_intel"] = SourceCodeIntelligenceEngine().analyze(workspace_path)
        except Exception:
            result["code_intel"] = None

        try:
            from app.repositories.code_quality_engine import CodeQualityEngine
            result["code_quality"] = CodeQualityEngine().analyze(workspace_path)
        except Exception:
            result["code_quality"] = None

        try:
            from app.repositories.file_intelligence_engine import FileIntelligenceEngine
            result["file_analysis"] = FileIntelligenceEngine().analyze(workspace_path)
        except Exception:
            result["file_analysis"] = None

        try:
            from app.repositories.import_dependency_engine import ImportDependencyEngine
            result["dep_analysis"] = ImportDependencyEngine().analyze(workspace_path)
        except Exception:
            result["dep_analysis"] = None

        try:
            from app.repositories.call_graph_intelligence_engine import CallGraphIntelligenceEngine
            result["call_graph"] = CallGraphIntelligenceEngine().analyze(workspace_path)
        except Exception:
            result["call_graph"] = None

        try:
            from app.repositories.semantic_intelligence_engine import SemanticCodeIntelligenceEngine
            result["semantic"] = SemanticCodeIntelligenceEngine().analyze(workspace_path)
        except Exception:
            result["semantic"] = None

        try:
            from app.repositories.configuration_intelligence_engine import ConfigurationIntelligenceEngine
            result["config_intel"] = ConfigurationIntelligenceEngine().analyze(workspace_path)
        except Exception:
            result["config_intel"] = None

        try:
            from app.repositories.project_insights_engine import ProjectInsightsEngine
            project_data = result.get("project_analysis", {})
            code_intel_data = result.get("code_intel", {})
            result["recommendations"] = ProjectInsightsEngine().analyze(
                workspace_path, project_data, code_intel_data
            )
        except Exception:
            result["recommendations"] = None

        try:
            from app.repositories.security_intelligence_engine import SecurityIntelligenceEngine
            result["security_intel"] = SecurityIntelligenceEngine().analyze(
                workspace_path,
                project_analysis=result.get("project_analysis"),
                code_intel=result.get("code_intel"),
                code_quality=result.get("code_quality"),
                dep_analysis=result.get("dep_analysis"),
                config_intel=result.get("config_intel"),
            )
        except Exception:
            result["security_intel"] = None

        try:
            from app.repositories.performance_intelligence_engine import PerformanceIntelligenceEngine
            result["performance_intel"] = PerformanceIntelligenceEngine().analyze(
                workspace_path,
                project_analysis=result.get("project_analysis"),
                code_intel=result.get("code_intel"),
                code_quality=result.get("code_quality"),
                dep_analysis=result.get("dep_analysis"),
            )
        except Exception:
            result["performance_intel"] = None

        try:
            from app.repositories.maintainability_intelligence_engine import MaintainabilityIntelligenceEngine
            result["maintainability_intel"] = MaintainabilityIntelligenceEngine().analyze(
                workspace_path,
                project_analysis=result.get("project_analysis"),
                code_intel=result.get("code_intel"),
                code_quality=result.get("code_quality"),
                dep_analysis=result.get("dep_analysis"),
            )
        except Exception:
            result["maintainability_intel"] = None

        try:
            from app.repositories.documentation_intelligence_engine import DocumentationIntelligenceEngine
            result["documentation_intel"] = DocumentationIntelligenceEngine().analyze(workspace_path)
        except Exception:
            result["documentation_intel"] = None

        try:
            from app.repositories.test_intelligence_engine import TestIntelligenceEngine
            result["test_intel"] = TestIntelligenceEngine().analyze(
                workspace_path,
                project_analysis=result.get("project_analysis"),
                code_intel=result.get("code_intel"),
            )
        except Exception:
            result["test_intel"] = None

        try:
            from app.repositories.production_readiness_engine import ProductionReadinessEngine
            result["production_intel"] = ProductionReadinessEngine().analyze(
                workspace_path,
                project_analysis=result.get("project_analysis"),
                code_intel=result.get("code_intel"),
                code_quality=result.get("code_quality"),
                dep_analysis=result.get("dep_analysis"),
                config_intel=result.get("config_intel"),
                security_intel=result.get("security_intel"),
                performance_intel=result.get("performance_intel"),
                maintainability_intel=result.get("maintainability_intel"),
                documentation_intel=result.get("documentation_intel"),
                test_intel=result.get("test_intel"),
            )
        except Exception:
            result["production_intel"] = None

        return result
