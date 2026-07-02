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

MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB
ALLOWED_EXTENSIONS = {".zip"}


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

        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .zip files are supported",
            )

        if file.size is not None and file.size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File exceeds the maximum upload size of 500 MB",
            )

        if file.filename is None or file.filename.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        safe_name = os.path.basename(file.filename)

        ensure_directories()
        file_id = generate_file_id()
        upload_path = get_upload_path(file_id)

        try:
            project.upload_status = "uploading"
            self.repo.db.commit()

            content = file.file.read()
            file_size = len(content)

            if file_size == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty",
                )

            if file_size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File exceeds the maximum upload size of 500 MB",
                )

            with open(upload_path, "wb") as f:
                f.write(content)

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
