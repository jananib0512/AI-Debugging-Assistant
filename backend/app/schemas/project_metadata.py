from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectStatistics(BaseModel):
    total_files: int
    total_folders: int
    total_size_bytes: int
    source_files: int
    config_files_count: int
    documentation_files: int
    image_files: int
    video_files: int
    asset_files: int


class DevOpsInfo(BaseModel):
    docker: bool
    docker_compose: bool
    kubernetes: bool
    ci_cd: list[str]


class ProjectMetadataResponse(BaseModel):
    project_name: str
    project_type: Optional[str] = None
    primary_language: Optional[str] = None
    secondary_languages: list[str]
    languages: dict[str, int]
    frameworks: list[str]
    package_manager: Optional[str] = None
    databases: list[str]
    devops: DevOpsInfo
    config_files: list[str]
    has_readme: bool
    statistics: ProjectStatistics
    last_scanned_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
