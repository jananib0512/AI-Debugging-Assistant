from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)


class ProjectService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = ProjectRepository(db)

    def create(self, user_id: int, request: ProjectCreateRequest) -> ProjectResponse:
        project = self.repo.create(
            user_id=user_id,
            project_name=request.project_name,
            description=request.description,
            language=request.language,
            framework=request.framework,
            version=request.version,
        )
        return ProjectResponse.model_validate(project)

    def get_by_id(self, user_id: int, project_id: int) -> ProjectResponse:
        project = self.repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return ProjectResponse.model_validate(project)

    def list(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 12,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: str | None = None,
    ) -> ProjectListResponse:
        items, total = self.repo.get_by_user_id(
            user_id=user_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )
        return ProjectListResponse(
            items=[ProjectResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(1, (total + page_size - 1) // page_size),
        )

    def update(
        self, user_id: int, project_id: int, request: ProjectUpdateRequest
    ) -> ProjectResponse:
        project = self.repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        updated = self.repo.update(
            project=project,
            project_name=request.project_name,
            description=request.description,
            language=request.language,
            framework=request.framework,
            version=request.version,
        )
        return ProjectResponse.model_validate(updated)

    def delete(self, user_id: int, project_id: int) -> None:
        project = self.repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        self.repo.delete(project)
