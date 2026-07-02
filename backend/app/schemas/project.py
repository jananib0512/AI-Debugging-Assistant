from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = Field(..., min_length=1, max_length=100)
    framework: Optional[str] = None
    version: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    project_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    language: Optional[str] = Field(None, min_length=1, max_length=100)
    framework: Optional[str] = None
    version: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    project_name: str
    description: Optional[str] = None
    language: str
    framework: Optional[str] = None
    version: Optional[str] = None
    uploaded_file_name: Optional[str] = None
    uploaded_file_size: Optional[int] = None
    uploaded_file_path: Optional[str] = None
    upload_status: Optional[str] = None
    workspace_path: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    extraction_status: Optional[str] = None
    total_files: Optional[int] = None
    total_folders: Optional[int] = None
    extraction_time_ms: Optional[int] = None
    extracted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
