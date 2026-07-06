from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.source_code_intelligence_engine import SourceCodeIntelligenceEngine
from app.schemas.project_analyzer import (
    CodeIntelligenceClass,
    CodeIntelligenceEnum,
    CodeIntelligenceFileSummary,
    CodeIntelligenceFunction,
    CodeIntelligenceFunctionParam,
    CodeIntelligenceImport,
    CodeIntelligenceInterface,
    CodeIntelligenceModule,
    CodeIntelligenceProperty,
    CodeIntelligenceSummary,
    CodeIntelligenceVariable,
    SourceCodeIntelligenceResponse,
)


class SourceCodeIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> SourceCodeIntelligenceResponse:
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

        engine = SourceCodeIntelligenceEngine()
        result = engine.analyze(workspace_path)

        return SourceCodeIntelligenceResponse(
            summary=CodeIntelligenceSummary(**result["summary"]),
            files=[CodeIntelligenceFileSummary(**f) for f in result["files"]],
            classes=[CodeIntelligenceClass(
                name=c["name"],
                file_path=c["file_path"],
                line_start=c["line_start"],
                line_end=c.get("line_end", 0),
                base_classes=c.get("base_classes", []),
                inherited_classes=c.get("inherited_classes", []),
                methods=[CodeIntelligenceFunction(**m) for m in c.get("methods", [])],
                properties=[CodeIntelligenceProperty(**p) for p in c.get("properties", [])],
                decorators=c.get("decorators", []),
                visibility=c.get("visibility", "public"),
                is_abstract=c.get("is_abstract", False),
            ) for c in result["classes"]],
            functions=[CodeIntelligenceFunction(
                name=f["name"],
                file_path=f["file_path"],
                line_start=f["line_start"],
                line_end=f.get("line_end", 0),
                parameters=[CodeIntelligenceFunctionParam(**p) for p in f.get("parameters", [])],
                return_type=f.get("return_type"),
                decorators=f.get("decorators", []),
                is_async=f.get("is_async", False),
                is_static=f.get("is_static", False),
                is_generator=f.get("is_generator", False),
                visibility=f.get("visibility", "public"),
                parent_class=f.get("parent_class"),
            ) for f in result["functions"]],
            imports=[CodeIntelligenceImport(**i) for i in result["imports"]],
            enums=[CodeIntelligenceEnum(**e) for e in result["enums"]],
            interfaces=[CodeIntelligenceInterface(**i) for i in result["interfaces"]],
            variables=[CodeIntelligenceVariable(**v) for v in result["variables"]],
            modules=[CodeIntelligenceModule(**m) for m in result["modules"]],
            analyzed_at=datetime.now(timezone.utc),
        )
