from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.call_graph_intelligence_engine import CallGraphIntelligenceEngine
from app.repositories.project_repository import ProjectRepository
from app.repositories.semantic_intelligence_engine import SemanticCodeIntelligenceEngine
from app.schemas.project_analyzer import (
    BusinessComponent,
    BusinessFlow,
    KnowledgeGraph,
    SemanticCodeIssue,
    SemanticComponent,
    SemanticRelationship,
    SemanticResponse,
    SemanticSimilarity,
    SemanticStats,
    SemanticSymbol,
    UnderstandingScore,
)


class SemanticIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> SemanticResponse:
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

        engine = SemanticCodeIntelligenceEngine()
        cg_engine = CallGraphIntelligenceEngine()

        cg_raw = cg_engine.analyze(workspace_path)
        call_graph_data = {
            "nodes": cg_raw.get("nodes", []),
            "edges": cg_raw.get("edges", []),
            "file_imports": cg_raw.get("file_imports", {}),
            "file_language_map": cg_raw.get("file_language_map", {}),
            "file_exports": cg_raw.get("file_exports", {}),
            "file_contents": cg_raw.get("file_contents", {}),
            "module_map": cg_raw.get("module_map", {}),
        }
        execution_flows = cg_raw.get("execution_flows", [])

        result = engine.analyze(workspace_path, call_graph_data=call_graph_data, execution_flows=execution_flows)

        components = [SemanticComponent(**c) for c in result["components"]]
        relationships = [SemanticRelationship(**r) for r in result["relationships"]]
        symbols = [SemanticSymbol(**s) for s in result["symbols"]]
        stats = SemanticStats(**result["stats"])

        business_flows = [
            BusinessFlow(
                id=f["id"],
                name=f["name"],
                description=f.get("description", ""),
                flow_type=f.get("flow_type", ""),
                confidence=f.get("confidence", "medium"),
                entry_components=f.get("entry_components", []),
                exit_components=f.get("exit_components", []),
                path=f.get("path", []),
                components=f.get("components", []),
                verified=f.get("verified", False),
            )
            for f in result.get("business_flows", [])
        ]

        issues = [
            SemanticCodeIssue(
                type=i["type"],
                severity=i.get("severity", "info"),
                component_id=i.get("component_id", ""),
                description=i.get("description", ""),
                detail=i.get("detail", ""),
                suggestion=i.get("suggestion", ""),
            )
            for i in result.get("issues", [])
        ]

        similarities = [
            SemanticSimilarity(
                component_a_id=s["component_a_id"],
                component_b_id=s["component_b_id"],
                similarity_type=s.get("similarity_type", ""),
                score=s.get("score", 0.0),
                description=s.get("description", ""),
                shared_patterns=s.get("shared_patterns", []),
            )
            for s in result.get("similarities", [])
        ]

        us = result.get("understanding_score", {})
        understanding_score = UnderstandingScore(
            overall=us.get("overall", 0.0),
            architecture=us.get("architecture", 0.0),
            business_logic=us.get("business_logic", 0.0),
            dependencies=us.get("dependencies", 0.0),
            code_organization=us.get("code_organization", 0.0),
            execution_flow=us.get("execution_flow", 0.0),
            semantic_relationships=us.get("semantic_relationships", 0.0),
            maintainability=us.get("maintainability", 0.0),
            readability=us.get("readability", 0.0),
            has_entry_points=us.get("has_entry_points", False),
            has_controllers=us.get("has_controllers", False),
            has_services=us.get("has_services", False),
            has_repositories=us.get("has_repositories", False),
            has_ml_components=us.get("has_ml_components", False),
            has_forecast_components=us.get("has_forecast_components", False),
            component_coverage=us.get("component_coverage", 0.0),
            flow_capture_rate=us.get("flow_capture_rate", 0.0),
            insight_count=us.get("insight_count", 0),
        )

        kg = result.get("knowledge_graph", {})
        knowledge_graph = KnowledgeGraph(
            nodes=kg.get("nodes", []),
            edges=kg.get("edges", []),
        )

        business_components = [
            BusinessComponent(
                id=bc["id"],
                name=bc["name"],
                type=bc.get("type", ""),
                file_path=bc.get("file_path", ""),
                module=bc.get("module", ""),
                confidence=bc.get("confidence", 0.0),
                description=bc.get("description", ""),
                related_components=bc.get("related_components", []),
            )
            for bc in result.get("business_components", [])
        ]

        return SemanticResponse(
            components=components,
            relationships=relationships,
            symbols=symbols,
            business_flows=business_flows,
            issues=issues,
            similarities=similarities,
            stats=stats,
            understanding_score=understanding_score,
            knowledge_graph=knowledge_graph,
            business_components=business_components,
            ai_insights=result.get("ai_insights", []),
            analyzed_at=datetime.now(timezone.utc),
        )
