from datetime import datetime

from pydantic import BaseModel


class RecentProjectItem(BaseModel):
    id: int
    project_name: str
    uploaded_at: str | None = None
    language: str


class RecentActivityItem(BaseModel):
    id: str
    type: str
    description: str
    timestamp: str


class DashboardStats(BaseModel):
    total_projects: int
    total_uploads: int
    recent_projects: list[RecentProjectItem]
    recent_activity: list[RecentActivityItem]
    workspace_count: int
    last_upload_time: str | None = None
