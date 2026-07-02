import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import (
    FileMetadataResponse,
    FileTreeResponse,
    FolderResponse,
    SearchResponse,
    TreeEntry,
    WorkspaceListItem,
    WorkspaceListResponse,
)

logger = logging.getLogger(__name__)


class WorkspaceService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = ProjectRepository(db)

    def list_workspaces(self, user_id: int) -> WorkspaceListResponse:
        projects = self.repo.list_extracted_by_user(user_id)
        items: list[WorkspaceListItem] = []
        for p in projects:
            ws_path = get_workspace_path(p.id)
            items.append(WorkspaceListItem(
                id=p.id,
                project_id=p.id,
                project_name=p.project_name,
                language=p.language,
                status="active" if ws_path.exists() else "inactive",
                path=str(ws_path),
                created_at=p.created_at.isoformat() if p.created_at else None,
                extracted_at=p.extracted_at.isoformat() if p.extracted_at else None,
                total_files=p.total_files,
                total_folders=p.total_folders,
            ))
        return WorkspaceListResponse(workspaces=items, total=len(items))

    def _get_workspace_repo(self, user_id: int, project_id: int) -> WorkspaceRepository:
        project = self.repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.extraction_status != "extracted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has not been extracted yet",
            )

        workspace_path = get_workspace_path(project_id)
        if not workspace_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace directory not found on disk",
            )

        return WorkspaceRepository(workspace_path)

    def get_tree(self, user_id: int, project_id: int) -> FileTreeResponse:
        wr = self._get_workspace_repo(user_id, project_id)
        tree = wr.get_tree()
        return FileTreeResponse(tree=tree)

    def list_folder(
        self, user_id: int, project_id: int, path: str
    ) -> FolderResponse:
        wr = self._get_workspace_repo(user_id, project_id)
        try:
            entries = wr.list_folder(path)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path not found: {path}",
            )
        except NotADirectoryError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not a directory: {path}",
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        return FolderResponse(path=path, entries=entries)

    def get_metadata(
        self, user_id: int, project_id: int, path: str
    ) -> FileMetadataResponse:
        wr = self._get_workspace_repo(user_id, project_id)
        try:
            return wr.get_metadata(path)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path not found: {path}",
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    def search(
        self, user_id: int, project_id: int, query: str
    ) -> SearchResponse:
        if not query or not query.strip():
            return SearchResponse(query=query, results=[], total=0)

        wr = self._get_workspace_repo(user_id, project_id)
        results = wr.search(query.strip())
        return SearchResponse(
            query=query,
            results=results,
            total=len(results),
        )
