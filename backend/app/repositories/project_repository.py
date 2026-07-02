from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        project_name: str,
        language: str,
        description: str | None = None,
        framework: str | None = None,
        version: str | None = None,
    ) -> Project:
        project = Project(
            user_id=user_id,
            project_name=project_name,
            description=description,
            language=language,
            framework=framework,
            version=version,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: int) -> Project | None:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_by_user_id(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 12,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: str | None = None,
    ) -> tuple[list[Project], int]:
        query = self.db.query(Project).filter(Project.user_id == user_id)

        if search:
            query = query.filter(
                Project.project_name.ilike(f"%{search}%")
            )

        total = query.count()

        sort_column = getattr(Project, sort_by, Project.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(desc(sort_column))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def update(
        self,
        project: Project,
        project_name: str | None = None,
        description: str | None = None,
        language: str | None = None,
        framework: str | None = None,
        version: str | None = None,
    ) -> Project:
        if project_name is not None:
            project.project_name = project_name
        if description is not None:
            project.description = description
        if language is not None:
            project.language = language
        if framework is not None:
            project.framework = framework
        if version is not None:
            project.version = version

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()

    def count_by_user(self, user_id: int) -> int:
        return self.db.query(Project).filter(Project.user_id == user_id).count()

    def count_uploads_by_user(self, user_id: int) -> int:
        return self.db.query(Project).filter(
            Project.user_id == user_id,
            Project.upload_status.isnot(None),
        ).count()

    def get_recent_by_user(
        self, user_id: int, limit: int = 5,
    ) -> list[Project]:
        return (
            self.db.query(Project)
            .filter(Project.user_id == user_id)
            .order_by(desc(Project.uploaded_at))
            .limit(limit)
            .all()
        )

    def get_latest_upload_time(self, user_id: int) -> datetime | None:
        project = (
            self.db.query(Project)
            .filter(
                Project.user_id == user_id,
                Project.uploaded_at.isnot(None),
            )
            .order_by(desc(Project.uploaded_at))
            .first()
        )
        return project.uploaded_at if project else None

    def list_extracted_by_user(self, user_id: int) -> list[Project]:
        return (
            self.db.query(Project)
            .filter(
                Project.user_id == user_id,
                Project.extraction_status == "extracted",
            )
            .order_by(desc(Project.extracted_at))
            .all()
        )
