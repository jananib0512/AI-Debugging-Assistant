from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.detection.project_scanner import ProjectScanner
from app.repositories.framework_detector import FrameworkDetectorRepository
from app.repositories.framework_intelligence_engine import FrameworkIntelligenceEngine
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.technology_classifier import TechnologyClassifier
from app.schemas.project_analyzer import (
    CategorizedTechnology,
    CompatibilityCheckInfo,
    DetectedConnectionInfo,
    DetectedDbFileInfo,
    DetectedMigrationInfo,
    DetectedOrmInfo,
    DetectedTechnology,
    DependencyGraphLayer,
    FeatureDetectionInfo,
    FrameworkDetailInfo,
    FrameworkEvidenceInfo,
    FrameworkHealthInfo,
    FrameworkIntelligenceResponse,
    TechnologyStackDetail,
)


class FrameworkIntelligenceService:
    def __init__(self, db: Session = Depends(get_db)):
        self._project_repo = ProjectRepository(db)
        self._metadata_repo = MetadataRepository(db)

    def detect(self, user_id: int, project_id: int) -> FrameworkIntelligenceResponse:
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.extraction_status != "extracted":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project workspace has not been extracted.")

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace directory not found.")

        metadata = self._metadata_repo.get_by_project_id(project_id)
        if not metadata:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project metadata not available.")

        scanner = ProjectScanner()
        scan_result = scanner.scan(workspace_path)
        detector = FrameworkDetectorRepository(scan_result)
        engine = FrameworkIntelligenceEngine(scan_result)

        def to_tech(items: list[dict]) -> list[DetectedTechnology]:
            return [
                DetectedTechnology(
                    name=i["name"],
                    version=i.get("version"),
                    confidence=i["confidence"],
                    reason=i["reason"],
                )
                for i in items
            ]

        languages = to_tech(detector.detect_languages())
        framework_list = detector.detect_frameworks()
        runtimes = to_tech(detector.detect_runtimes())
        pm_list = detector.detect_package_managers()
        build_tools = to_tech(detector.detect_build_tools())
        database_list = detector.detect_databases()
        containers = to_tech(detector.detect_containers())
        orm_list = detector.detect_orms()

        categorized = TechnologyClassifier.build_response(
            framework_techs=framework_list,
            database_techs=database_list,
            orm_techs=orm_list,
            pm_techs=pm_list,
        )

        categorized_models: dict[str, list[CategorizedTechnology]] = {}
        for cat, techs in categorized.items():
            categorized_models[cat] = [
                CategorizedTechnology(
                    name=t["name"],
                    version=t.get("version"),
                    confidence=t["confidence"],
                    reason=t["reason"],
                    category=t["category"],
                    detection_source=t["detection_source"],
                )
                for t in techs
            ]

        orms = [
            DetectedOrmInfo(
                name=o["name"],
                version=o.get("version"),
                confidence=o["confidence"],
                reason=o["reason"],
                migration=o.get("migration"),
            )
            for o in orm_list
        ]
        migrations = [
            DetectedMigrationInfo(
                name=m["name"],
                version=m.get("version"),
                confidence=m["confidence"],
                reason=m["reason"],
            )
            for m in detector.detect_migrations()
        ]
        database_files = [
            DetectedDbFileInfo(path=f["path"], size=f["size"])
            for f in detector.detect_database_files()
        ]
        connection_details = [
            DetectedConnectionInfo(
                raw_uri=c["raw_uri"],
                host=c.get("host"),
                port=c.get("port"),
                database=c.get("database"),
                type=c.get("type"),
            )
            for c in detector.detect_connection_details()
        ]

        primary_language = languages[0] if languages else None
        primary_framework = (
            DetectedTechnology(
                name=categorized.get("Application Framework", [{}])[0]["name"],
                confidence=categorized["Application Framework"][0]["confidence"],
                reason=categorized["Application Framework"][0]["reason"],
            )
            if categorized.get("Application Framework")
            else None
        )

        engine_analysis = engine.analyze()

        frameworks_detail = [
            FrameworkDetailInfo(
                name=t["name"],
                version=t.get("version"),
                confidence=t["confidence"],
                reason=t["reason"],
                category=t.get("category", ""),
                detection_source=t.get("detection_source", ""),
                health=FrameworkHealthInfo(
                    score=t["health"]["score"],
                    label=t["health"]["label"],
                    details=t["health"]["details"],
                ) if t.get("health") else None,
                role=t.get("role", ""),
            )
            for t in engine_analysis["frameworks"]
        ]

        compatibility = [
            CompatibilityCheckInfo(
                framework=c["framework"],
                other_framework=c["with"],
                status=c["status"],
                note=c["note"],
            )
            for c in engine_analysis["compatibility"]
        ]

        features = [
            FeatureDetectionInfo(
                name=f["name"],
                confidence=f["confidence"],
                evidence=f["evidence"],
            )
            for f in engine_analysis["features"]
        ]

        dep_graph = [
            DependencyGraphLayer(
                layer=g["layer"],
                label=g["label"],
                technologies=g["technologies"],
            )
            for g in engine_analysis["dependency_graph"]
        ]

        evidence_list = [
            FrameworkEvidenceInfo(
                name=e["name"],
                source=e.get("source", ""),
                confidence=e["confidence"],
            )
            for e in engine_analysis["evidence"]
        ]

        return FrameworkIntelligenceResponse(
            technology_stack=TechnologyStackDetail(
                languages=languages,
                frameworks=to_tech(framework_list),
                runtimes=runtimes,
                package_managers=to_tech(pm_list),
                build_tools=build_tools,
                databases=to_tech(database_list),
                containers=containers,
                orms=orms,
                migrations=migrations,
                database_files=database_files,
                connection_details=connection_details,
                categorized=categorized_models,
            ),
            primary_language=primary_language,
            primary_framework=primary_framework,
            frameworks=frameworks_detail,
            compatibility=compatibility,
            features=features,
            dependency_graph=dep_graph,
            evidence=evidence_list,
            project_type=engine_analysis.get("project_type", ""),
            analyzed_at=datetime.now(timezone.utc),
        )
