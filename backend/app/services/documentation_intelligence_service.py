from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.documentation_intelligence_engine import DocumentationIntelligenceEngine
from app.schemas.project_analyzer import (
    CodeDocumentationItem,
    DocFinding,
    DocumentationIntelligenceResponse,
    DocumentationScore,
    DocumentationSummary,
    ProjectDocItem,
)


class DocumentationIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> DocumentationIntelligenceResponse:
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
        engine = DocumentationIntelligenceEngine()
        result = engine.analyze(
            workspace_path,
            project_analysis=data.get("project_analysis"),
            code_intel=data.get("code_intel"),
            code_quality=data.get("code_quality"),
            file_analysis=data.get("file_analysis"),
            func_class=data.get("func_class"),
            dep_analysis=data.get("dep_analysis"),
            call_graph=data.get("call_graph"),
            semantic=data.get("semantic"),
            config_intel=data.get("config_intel"),
            recommendations=data.get("recommendations"),
        )

        score = DocumentationScore(**result["documentation_score"])
        code_docs = [CodeDocumentationItem(**c) for c in result.get("code_documentation", [])]
        project_docs = [ProjectDocItem(**p) for p in result.get("project_docs", [])]
        findings = [DocFinding(**f) for f in result.get("findings", [])]
        summary = DocumentationSummary(**result["summary"])

        return DocumentationIntelligenceResponse(
            documentation_score=score,
            code_documentation=code_docs,
            project_docs=project_docs,
            findings=findings,
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
            from app.repositories.function_class_intelligence_engine import FunctionClassIntelligenceEngine
            result["func_class"] = FunctionClassIntelligenceEngine().analyze(workspace_path)
        except Exception:
            result["func_class"] = None

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
            code_intel = result.get("code_intel", {})
            result["recommendations"] = ProjectInsightsEngine().analyze(workspace_path, project_data, code_intel)
        except Exception:
            result["recommendations"] = None

        return result
