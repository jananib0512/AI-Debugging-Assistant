import os
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import (
    create_workspace,
    ensure_directories,
    generate_file_id,
    get_upload_path,
)
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectResponse

MAX_UPLOAD_SIZE = 1024 * 1024 * 1024  # 1 GB
ALLOWED_EXTENSIONS = {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar"}
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB per chunk for streaming


class UploadService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = ProjectRepository(db)

    def upload(self, user_id: int, project_id: int, file: UploadFile) -> ProjectResponse:
        project = self.repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.upload_status == "uploaded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A file has already been uploaded for this project",
            )

        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        archive_ext = self._detect_archive_ext(filename)

        if archive_ext is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported archive format. Supported formats: .zip, .tar.gz, .tgz, .7z, .rar",
            )

        if ext == ".gz" and archive_ext not in (".tar.gz", ".tgz"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported archive format. Supported formats: .zip, .tar.gz, .tgz, .7z, .rar",
            )

        if file.size is not None and file.size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Maximum upload size is 1 GB.",
            )

        if filename.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        safe_name = os.path.basename(filename)

        ensure_directories()
        file_id = generate_file_id()
        upload_path = get_upload_path(file_id)

        try:
            project.upload_status = "uploading"
            self.repo.db.commit()

            file_size = 0
            with open(upload_path, "wb") as f:
                while True:
                    chunk = file.file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    file_size += len(chunk)
                    if file_size > MAX_UPLOAD_SIZE:
                        f.close()
                        upload_path.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Maximum upload size is 1 GB.",
                        )
                    f.write(chunk)

            if file_size == 0:
                upload_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty",
                )

            workspace_path = create_workspace(project.id)

            project.uploaded_file_name = safe_name
            project.uploaded_file_size = file_size
            project.uploaded_file_path = str(upload_path)
            project.upload_status = "uploaded"
            project.workspace_path = str(workspace_path)
            project.uploaded_at = datetime.now(timezone.utc)
            self.repo.db.commit()
            self.repo.db.refresh(project)

        except HTTPException:
            raise
        except Exception:
            project.upload_status = "failed"
            self.repo.db.commit()
            if upload_path.exists():
                upload_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Upload failed due to a server error",
            )

        return ProjectResponse.model_validate(project)

    @staticmethod
    def _detect_archive_ext(filename: str) -> str | None:
        name_lower = filename.lower()
        if name_lower.endswith(".tar.gz") or name_lower.endswith(".tgz"):
            return ".tar.gz"
        for ext in ALLOWED_EXTENSIONS:
            if name_lower.endswith(ext):
                return ext
        return None
