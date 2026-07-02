from fastapi import APIRouter, Depends, Query

from app.middleware.auth_middleware import require_auth
from app.models.user import User
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("")
def list_workspaces(
    current_user: User = Depends(require_auth),
    service: WorkspaceService = Depends(WorkspaceService),
):
    return service.list_workspaces(user_id=current_user.id)


@router.get("/{project_id}/tree")
def get_workspace_tree(
    project_id: int,
    current_user: User = Depends(require_auth),
    service: WorkspaceService = Depends(WorkspaceService),
):
    return service.get_tree(user_id=current_user.id, project_id=project_id)


@router.get("/{project_id}/folder")
def list_workspace_folder(
    project_id: int,
    path: str = Query("", description="Relative path within workspace"),
    current_user: User = Depends(require_auth),
    service: WorkspaceService = Depends(WorkspaceService),
):
    return service.list_folder(
        user_id=current_user.id, project_id=project_id, path=path
    )


@router.get("/{project_id}/metadata")
def get_file_metadata(
    project_id: int,
    path: str = Query(..., description="Relative path to file or folder"),
    current_user: User = Depends(require_auth),
    service: WorkspaceService = Depends(WorkspaceService),
):
    return service.get_metadata(
        user_id=current_user.id, project_id=project_id, path=path
    )


@router.get("/{project_id}/search")
def search_workspace(
    project_id: int,
    q: str = Query("", description="Search query"),
    current_user: User = Depends(require_auth),
    service: WorkspaceService = Depends(WorkspaceService),
):
    return service.search(
        user_id=current_user.id, project_id=project_id, query=q
    )
