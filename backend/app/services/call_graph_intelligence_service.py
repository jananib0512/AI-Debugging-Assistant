from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.call_graph_intelligence_engine import CallGraphIntelligenceEngine
from app.schemas.project_analyzer import (
    CallGraphEdge,
    CallGraphIssue,
    CallGraphNode,
    CallGraphResponse,
    CallGraphStats,
    ExecutionFlow,
)


class CallGraphIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> CallGraphResponse:
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

        engine = CallGraphIntelligenceEngine()
        result = engine.analyze(workspace_path)

        nodes = [CallGraphNode(**n) for n in result["nodes"]]
        edges = [CallGraphEdge(**e) for e in result["edges"]]
        entry_points = [CallGraphNode(**n) for n in result["entry_points"]]
        stats = CallGraphStats(**result["stats"])

        execution_flows = [
            ExecutionFlow(
                id=f["id"],
                name=f["name"],
                description=f.get("description", ""),
                flow_type=f.get("flow_type", "request"),
                entry_node=f.get("entry_node", ""),
                exit_node=f.get("exit_node", ""),
                path=f.get("path", []),
                depth=f.get("depth", 0),
                is_complete=f.get("is_complete", False),
                issues=f.get("issues", []),
            )
            for f in result.get("execution_flows", [])
        ]

        issues = [
            CallGraphIssue(
                type=i["type"],
                severity=i.get("severity", "medium"),
                description=i.get("description", ""),
                nodes=i.get("nodes", []),
                detail=i.get("detail", ""),
            )
            for i in result.get("issues", [])
        ]

        return CallGraphResponse(
            nodes=nodes,
            edges=edges,
            execution_flows=execution_flows,
            entry_points=entry_points,
            stats=stats,
            issues=issues,
            ai_insights=result.get("ai_insights", []),
            analyzed_at=datetime.now(timezone.utc),
        )
