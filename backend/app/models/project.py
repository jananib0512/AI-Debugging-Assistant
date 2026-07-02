from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(100), nullable=False)
    framework: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    uploaded_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    upload_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )
    workspace_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extraction_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )
    total_files: Mapped[int | None] = mapped_column(BigInteger, nullable=True, default=None)
    total_folders: Mapped[int | None] = mapped_column(BigInteger, nullable=True, default=None)
    extraction_time_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True, default=None)
    extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="projects")
    project_metadata: Mapped["ProjectMetadata | None"] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
