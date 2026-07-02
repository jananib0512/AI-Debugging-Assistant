import logging
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.schemas.dashboard import (
    DashboardStats,
    RecentActivityItem,
    RecentProjectItem,
)

logger = logging.getLogger(__name__)


def _fmt(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class DashboardService:
    def __init__(self, db: Session = Depends(get_db)):
        self.project_repo = ProjectRepository(db)

    def get_stats(self, user_id: int) -> DashboardStats:
        total_projects = self.project_repo.count_by_user(user_id)
        total_uploads = self.project_repo.count_uploads_by_user(user_id)
        recent_projects_raw = self.project_repo.get_recent_by_user(user_id, limit=5)
        last_upload = self.project_repo.get_latest_upload_time(user_id)

        recent_projects = [
            RecentProjectItem(
                id=p.id,
                project_name=p.project_name,
                uploaded_at=_fmt(p.uploaded_at),
                language=p.language,
            )
            for p in recent_projects_raw
        ]

        activity = self._build_activity(recent_projects_raw, total_uploads)

        return DashboardStats(
            total_projects=total_projects,
            total_uploads=total_uploads,
            recent_projects=recent_projects,
            recent_activity=activity,
            workspace_count=total_projects,
            last_upload_time=_fmt(last_upload),
        )

    def _build_activity(
        self, recent_projects: list, total_uploads: int,
    ) -> list[RecentActivityItem]:
        items: list[RecentActivityItem] = []
        now = datetime.now(timezone.utc)

        for p in recent_projects:
            if p.uploaded_at:
                ts = _fmt(p.uploaded_at) or ""
                items.append(RecentActivityItem(
                    id=f"upload-{p.id}",
                    type="upload",
                    description=f"Project uploaded: {p.project_name}",
                    timestamp=ts,
                ))
            if p.extraction_status == "extracted" and p.extracted_at:
                ts = _fmt(p.extracted_at) or ""
                items.append(RecentActivityItem(
                    id=f"extract-{p.id}",
                    type="extraction",
                    description=f"Workspace created: {p.project_name}",
                    timestamp=ts,
                ))
            if p.uploaded_at:
                ts = _fmt(p.uploaded_at) or ""
                items.append(RecentActivityItem(
                    id=f"created-{p.id}",
                    type="creation",
                    description=f"Project created: {p.project_name}",
                    timestamp=ts,
                ))

        items.sort(key=lambda x: x.timestamp, reverse=True)

        if not items:
            items.append(RecentActivityItem(
                id="welcome",
                type="info",
                description="Platform initialized",
                timestamp=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ))

        return items[:10]
