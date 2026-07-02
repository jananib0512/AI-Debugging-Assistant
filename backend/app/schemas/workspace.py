from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TreeEntry(BaseModel):
    name: str
    path: str
    type: str
    children: Optional[list["TreeEntry"]] = None


class FileTreeResponse(BaseModel):
    tree: TreeEntry


class FolderEntry(BaseModel):
    name: str
    path: str
    type: str
    size: Optional[int] = None
    extension: Optional[str] = None
    modified_at: Optional[datetime] = None


class FolderResponse(BaseModel):
    path: str
    entries: list[FolderEntry]


class FileMetadataResponse(BaseModel):
    name: str
    path: str
    extension: str
    size: int
    created_at: datetime
    modified_at: datetime
    is_directory: bool
    relative_path: str


class SearchResult(BaseModel):
    name: str
    path: str
    type: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class WorkspaceListItem(BaseModel):
    id: int
    project_id: int
    project_name: str
    language: str
    status: str
    path: str
    created_at: str | None = None
    extracted_at: str | None = None
    total_files: int | None = None
    total_folders: int | None = None


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceListItem]
    total: int
