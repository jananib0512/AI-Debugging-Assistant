from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.project_scanner import ProjectScanner
from app.repositories.complexity_analyzer import ComplexityAnalyzerRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_analyzer import (
    BuildReadinessInfo,
    ComplexityAnalysisResponse,
    ComplexityScoreInfo,
    DocumentationCoverage,
    LanguageDistribution,
    MaintainabilityInfo,
    OrganizationInfo,
    PerformanceEstimate,
    ProjectScaleInfo,
    WorkspaceStatistics,
)


class ComplexityAnalysisService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)

    def detect(self, user_id: int, project_id: int) -> ComplexityAnalysisResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workspace not extracted")

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workspace directory not found")

        if not any(workspace_path.iterdir()):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workspace is empty")

        scanner = ProjectScanner()
        scan_result = scanner.scan(workspace_path)
        analyzer = ComplexityAnalyzerRepository(scan_result)

        ws_stats = analyzer.compute_workspace_statistics()
        lang_dist = analyzer.compute_language_distribution()
        scale = analyzer.compute_project_scale()
        complexity = analyzer.compute_complexity_score()
        org = analyzer.compute_organization()
        maint = analyzer.compute_maintainability()
        docs = analyzer.compute_documentation_coverage()
        readiness = analyzer.compute_build_readiness()
        perf = analyzer.compute_performance_estimate()

        return ComplexityAnalysisResponse(
            project_scale=ProjectScaleInfo(scale=scale["scale"], confidence=scale["confidence"]),
            complexity_score=ComplexityScoreInfo(
                score=complexity["score"],
                level=complexity["level"],
                factors=complexity["factors"],
            ),
            maintainability=MaintainabilityInfo(
                score=maint["score"],
                level=maint["level"],
                factors=maint["factors"],
            ),
            workspace_statistics=WorkspaceStatistics(
                total_files=ws_stats["total_files"],
                total_folders=ws_stats["total_folders"],
                source_files=ws_stats["source_files"],
                config_files=ws_stats["config_files"],
                doc_files=ws_stats["doc_files"],
                image_files=ws_stats["image_files"],
                video_files=ws_stats["video_files"],
                archive_files=ws_stats["archive_files"],
                template_files=ws_stats["template_files"],
                script_files=ws_stats["script_files"],
                asset_files=ws_stats["asset_files"],
                largest_file=ws_stats["largest_file"],
                largest_file_size=ws_stats["largest_file_size"],
                largest_folder=ws_stats["largest_folder"],
                largest_folder_count=ws_stats["largest_folder_count"],
                average_file_size=ws_stats["average_file_size"],
                average_folder_depth=ws_stats["average_folder_depth"],
                max_folder_depth=ws_stats["max_folder_depth"],
                workspace_size=ws_stats["workspace_size"],
            ),
            language_distribution=[
                LanguageDistribution(language=d["language"], file_count=d["file_count"], percentage=d["percentage"])
                for d in lang_dist
            ],
            documentation_coverage=DocumentationCoverage(
                coverage_percentage=docs["coverage_percentage"],
                has_readme=docs["has_readme"],
                has_license=docs["has_license"],
                has_changelog=docs["has_changelog"],
                has_api_docs=docs["has_api_docs"],
            ),
            build_readiness=BuildReadinessInfo(
                status=readiness["status"],
                score=readiness["score"],
                reasons=readiness["reasons"],
            ),
            organization=OrganizationInfo(
                level=org["level"],
                score=org["score"],
            ),
            performance=PerformanceEstimate(
                expected_analysis_time=perf["expected_analysis_time"],
                workspace_scan_time=perf["workspace_scan_time"],
                complexity_impact=perf["complexity_impact"],
            ),
            analyzed_at=datetime.now(timezone.utc),
        )
