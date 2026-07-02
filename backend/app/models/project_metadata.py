from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProjectMetadata(Base):
    __tablename__ = "project_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    primary_language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    secondary_languages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    framework: Mapped[str | None] = mapped_column(String(100), nullable=True)
    package_manager: Mapped[str | None] = mapped_column(String(50), nullable=True)
    databases: Mapped[list | None] = mapped_column(JSON, nullable=True)
    docker: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    docker_compose: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kubernetes: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ci_cd: Mapped[list | None] = mapped_column(JSON, nullable=True)
    config_files: Mapped[list | None] = mapped_column(JSON, nullable=True)
    has_readme: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detected_languages: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_folders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    source_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config_files_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documentation_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    video_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    asset_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="project_metadata")
