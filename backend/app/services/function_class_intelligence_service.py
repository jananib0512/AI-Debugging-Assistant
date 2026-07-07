from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.function_class_intelligence_engine import FunctionClassIntelligenceEngine
from app.schemas.project_analyzer import (
    FuncClassIntelligenceClass,
    FuncClassIntelligenceFunc,
    FuncClassIntelligenceIssue,
    FuncClassIntelligenceMethod,
    FuncClassIntelligenceParam,
    FuncClassIntelligenceResponse,
    FuncClassIntelligenceStats,
    FuncClassRelationship,
)


class FunctionClassIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def analyze(self, user_id: int, project_id: int) -> FuncClassIntelligenceResponse:
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

        engine = FunctionClassIntelligenceEngine()
        result = engine.analyze(workspace_path)

        def _to_param(p: dict) -> FuncClassIntelligenceParam:
            return FuncClassIntelligenceParam(
                name=p["name"],
                type=p.get("type"),
                default_value=p.get("default_value"),
                is_optional=p.get("is_optional", False),
            )

        def _to_issue(iss: dict) -> FuncClassIntelligenceIssue:
            return FuncClassIntelligenceIssue(
                type=iss["type"],
                severity=iss["severity"],
                description=iss["description"],
                reason=iss.get("reason", ""),
                suggested_fix=iss.get("suggested_fix", ""),
                line=iss.get("line"),
            )

        def _to_method(m: dict) -> FuncClassIntelligenceMethod:
            return FuncClassIntelligenceMethod(
                name=m["name"],
                parent_class=m.get("parent_class", ""),
                parameters=[_to_param(p) for p in m.get("parameters", [])],
                return_type=m.get("return_type"),
                decorators=m.get("decorators", []),
                is_async=m.get("is_async", False),
                is_static=m.get("is_static", False),
                is_classmethod=m.get("is_classmethod", False),
                is_property=m.get("is_property", False),
                visibility=m.get("visibility", "public"),
                lines_of_code=m.get("lines_of_code", 0),
                start_line=m.get("start_line", 0),
                end_line=m.get("end_line", 0),
                cyclomatic_complexity=m.get("cyclomatic_complexity", 1),
                maintainability_score=m.get("maintainability_score", 100.0),
                has_documentation=m.get("has_documentation", False),
                has_type_hints=m.get("has_type_hints", False),
                issue_count=m.get("issue_count", 0),
                health_status=m.get("health_status", "Good"),
                issues=[_to_issue(i) for i in m.get("issues", [])],
                ai_insight=m.get("ai_insight", ""),
            )

        functions = [
            FuncClassIntelligenceFunc(
                name=f["name"],
                file_path=f["file_path"],
                file_name=f["file_name"],
                language=f["language"],
                module=f.get("module", ""),
                parameters=[_to_param(p) for p in f.get("parameters", [])],
                return_type=f.get("return_type"),
                decorators=f.get("decorators", []),
                is_async=f.get("is_async", False),
                is_generator=f.get("is_generator", False),
                is_lambda=f.get("is_lambda", False),
                visibility=f.get("visibility", "public"),
                lines_of_code=f.get("lines_of_code", 0),
                start_line=f.get("start_line", 0),
                end_line=f.get("end_line", 0),
                cyclomatic_complexity=f.get("cyclomatic_complexity", 1),
                maintainability_score=f.get("maintainability_score", 100.0),
                has_documentation=f.get("has_documentation", False),
                has_type_hints=f.get("has_type_hints", False),
                deepest_nesting=f.get("deepest_nesting", 0),
                issue_count=f.get("issue_count", 0),
                health_status=f.get("health_status", "Good"),
                issues=[_to_issue(i) for i in f.get("issues", [])],
                callers=f.get("_callers", []),
                called_functions=list(f.get("_called_functions", [])),
                is_recursive=f.get("_is_recursive", False),
                is_unused=f.get("_is_unused", False),
                cross_file_calls=f.get("_cross_file_calls", []),
                ai_insight=f.get("ai_insight", ""),
            )
            for f in result["functions"]
        ]

        classes = [
            FuncClassIntelligenceClass(
                name=c["name"],
                file_path=c["file_path"],
                file_name=c["file_name"],
                language=c["language"],
                module=c.get("module", ""),
                base_classes=c.get("base_classes", []),
                parent_class=c.get("parent_class"),
                child_classes=c.get("child_classes", []),
                methods=[_to_method(m) for m in c.get("methods", [])],
                properties=c.get("properties", []),
                class_variables=c.get("class_variables", []),
                constructors=[_to_method(m) for m in c.get("constructors", [])],
                decorators=c.get("decorators", []),
                interfaces=c.get("interfaces", []),
                is_abstract=c.get("is_abstract", False),
                has_nested_classes=c.get("has_nested_classes", False),
                lines_of_code=c.get("lines_of_code", 0),
                complexity=c.get("complexity", 1),
                maintainability_score=c.get("maintainability_score", 100.0),
                has_documentation=c.get("has_documentation", False),
                issue_count=c.get("issue_count", 0),
                health_status=c.get("health_status", "Good"),
                issues=[_to_issue(i) for i in c.get("issues", [])],
                coupling=c.get("coupling", 0),
                method_count=c.get("method_count", 0),
                property_count=c.get("property_count", 0),
                ai_insight=c.get("ai_insight", ""),
            )
            for c in result["classes"]
        ]

        relationships = [
            FuncClassRelationship(
                type=r["type"],
                source=r["source"],
                target=r["target"],
                source_file=r.get("source_file", ""),
                target_file=r.get("target_file", ""),
                strength=r.get("strength", "weak"),
            )
            for r in result.get("relationships", [])
        ]

        stats_data = result["stats"]
        stats = FuncClassIntelligenceStats(
            total_functions=stats_data["total_functions"],
            total_classes=stats_data["total_classes"],
            total_methods=stats_data["total_methods"],
            average_complexity=stats_data["average_complexity"],
            average_maintainability=stats_data["average_maintainability"],
            total_issues=stats_data["total_issues"],
            language_breakdown=stats_data.get("language_breakdown", {}),
            health_counts=stats_data.get("health_counts", {}),
            unused_functions=stats_data.get("unused_functions", 0),
            recursive_functions=stats_data.get("recursive_functions", 0),
            undocumented_count=stats_data.get("undocumented_count", 0),
            deep_nesting_count=stats_data.get("deep_nesting_count", 0),
            missing_type_hints_count=stats_data.get("missing_type_hints_count", 0),
        )

        return FuncClassIntelligenceResponse(
            functions=functions,
            classes=classes,
            relationships=relationships,
            stats=stats,
            ai_insights=result.get("ai_insights", []),
            analyzed_at=datetime.now(timezone.utc),
        )
