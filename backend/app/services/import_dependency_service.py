from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.import_dependency_engine import ImportDependencyEngine
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    CircularDependency,
    DependencyGraph,
    DependencyGraphEdge,
    DependencyGraphNode,
    DependencyMetrics,
    FileDependency,
    ImportDependencyResponse,
    ImportRecord,
)


class ImportDependencyService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> ImportDependencyResponse:
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

        engine = ImportDependencyEngine()
        result = engine.analyze(workspace_path)

        imports = [
            ImportRecord(
                module=imp["module"],
                symbol=imp.get("symbol", ""),
                alias=imp.get("alias"),
                source_file=imp["source_file"],
                target_file=imp.get("target_file"),
                import_type=imp.get("import_type", "internal"),
                language=imp["language"],
                is_relative=imp.get("is_relative", False),
                is_wildcard=imp.get("is_wildcard", False),
                is_dynamic=imp.get("is_dynamic", False),
                is_unused=imp.get("is_unused", False),
                is_duplicate=imp.get("is_duplicate", False),
                is_broken=imp.get("is_broken", False),
                line_number=imp.get("line_number"),
                resolved=imp.get("resolved", True),
                confidence=imp.get("confidence", 1.0),
            )
            for imp in result["imports"]
        ]

        dependencies = [
            FileDependency(**dep)
            for dep in result["dependencies"]
        ]

        circular_deps = [
            CircularDependency(
                chain=cd["chain"],
                files=cd["files"],
                severity=cd["severity"],
                suggested_resolution=cd.get("suggested_resolution", ""),
            )
            for cd in result["circular_dependencies"]
        ]

        graph_data = result["graph"]
        graph = DependencyGraph(
            nodes=[DependencyGraphNode(**n) for n in graph_data["nodes"]],
            edges=[DependencyGraphEdge(**e) for e in graph_data["edges"]],
        )

        metrics = DependencyMetrics(**result["metrics"])

        return ImportDependencyResponse(
            imports=imports,
            dependencies=dependencies,
            circular_dependencies=circular_deps,
            graph=graph,
            metrics=metrics,
            insights=result.get("insights", []),
            recommendations=result.get("recommendations", []),
            analyzed_at=datetime.now(timezone.utc),
        )
