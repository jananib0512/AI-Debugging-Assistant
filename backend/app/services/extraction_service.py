import logging
import os
import shutil
import tarfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_upload_path, get_workspace_path
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectResponse

logger = logging.getLogger(__name__)

MAX_EXTRACTED_SIZE = 2 * 1024 * 1024 * 1024
MAX_FILE_COUNT = 100000

IGNORED_DIRS = frozenset({
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "coverage",
    ".next",
    "target",
    "vendor",
    ".idea",
    ".vscode",
    "__MACOSX",
})

IGNORED_FILES = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})


class ExtractionError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ExtractionService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = ProjectRepository(db)

    def extract(self, user_id: int, project_id: int) -> ProjectResponse:
        project = self.repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.upload_status != "uploaded":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No uploaded file to extract. Please upload a project archive first.",
            )

        if project.extraction_status == "extracting":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Extraction is already in progress",
            )

        if project.extraction_status == "extracted":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Project has already been extracted",
            )

        archive_path = Path(project.uploaded_file_path) if project.uploaded_file_path else None
        if not archive_path or not archive_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded archive file not found on disk",
            )

        workspace_path = get_workspace_path(project_id)

        if workspace_path.exists():
            shutil.rmtree(workspace_path)
        workspace_path.mkdir(parents=True, exist_ok=True)

        project.extraction_status = "extracting"
        self.repo.db.commit()

        start_time = time.monotonic()
        total_files = 0
        total_folders = 0

        try:
            ext = self._detect_archive_format(archive_path)
            if ext in (".zip",):
                total_files, total_folders = self._extract_zip(archive_path, workspace_path)
            elif ext in (".tar.gz", ".tgz"):
                total_files, total_folders = self._extract_tar(archive_path, workspace_path)
            elif ext in (".7z", ".rar"):
                total_files, total_folders = self._extract_with_patool(archive_path, workspace_path)
            else:
                raise ExtractionError(
                    f"Unsupported archive format: {ext}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except ExtractionError as e:
            project.extraction_status = "failed"
            self.repo.db.commit()
            self.repo.db.refresh(project)
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message,
            )
        except Exception:
            logger.exception("Unexpected extraction error for project %s", project_id)
            project.extraction_status = "failed"
            self.repo.db.commit()
            self.repo.db.refresh(project)
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Extraction failed due to a server error",
            )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        project.extraction_status = "extracted"
        project.total_files = total_files
        project.total_folders = total_folders
        project.extraction_time_ms = elapsed_ms
        project.extracted_at = datetime.now(timezone.utc)
        project.workspace_path = str(workspace_path)
        self.repo.db.commit()
        self.repo.db.refresh(project)

        logger.info(
            "Extraction complete for project %s: %d files, %d folders, %d ms",
            project_id, total_files, total_folders, elapsed_ms,
        )

        return ProjectResponse.model_validate(project)

    @staticmethod
    def _detect_archive_format(path: Path) -> str:
        name = path.name.lower()
        if name.endswith(".tar.gz") or name.endswith(".tgz"):
            return ".tar.gz"
        if name.endswith(".zip"):
            return ".zip"
        if name.endswith(".7z"):
            return ".7z"
        if name.endswith(".rar"):
            return ".rar"
        return path.suffix.lower()

    def _extract_zip(self, zip_path: Path, target_dir: Path) -> tuple[int, int]:
        if not zipfile.is_zipfile(zip_path):
            raise ExtractionError("Uploaded file is not a valid ZIP archive")

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                bad_file = zf.testzip()
                if bad_file is not None:
                    raise ExtractionError(
                        f"ZIP archive is corrupted (bad entry: {bad_file})"
                    )

                info_list = zf.infolist()
                if not info_list:
                    raise ExtractionError("Archive is empty")

                filtered_entries = []
                total_size = 0

                for info in info_list:
                    norm_path = info.filename.replace("\\", "/")
                    if self._is_ignored(norm_path):
                        continue
                    filtered_entries.append(info)
                    if not info.is_dir():
                        total_size += info.file_size

                if len(filtered_entries) > MAX_FILE_COUNT:
                    raise ExtractionError(
                        f"Project contains too many source files ({len(filtered_entries)}). "
                        f"Maximum allowed source files is {MAX_FILE_COUNT}."
                    )

                if total_size > MAX_EXTRACTED_SIZE:
                    raise ExtractionError(
                        f"Total project size ({total_size / (1024*1024):.1f} MB) exceeds "
                        f"the maximum allowed size of {MAX_EXTRACTED_SIZE / (1024*1024*1024):.0f} GB"
                    )

                file_count = 0

                for info in filtered_entries:
                    path = self._resolve_path(target_dir, info.filename)

                    if info.is_dir():
                        path.mkdir(parents=True, exist_ok=True)
                        continue

                    path.parent.mkdir(parents=True, exist_ok=True)
                    zf.extract(info, target_dir)
                    file_count += 1

                folder_count = self._count_folders(target_dir)

                return file_count, folder_count

        except ExtractionError:
            raise
        except zipfile.BadZipFile:
            raise ExtractionError("Archive is corrupted or invalid")
        except OSError as e:
            self._handle_os_error(e)

    def _extract_tar(self, tar_path: Path, target_dir: Path) -> tuple[int, int]:
        try:
            if not tarfile.is_tarfile(tar_path):
                raise ExtractionError("Uploaded file is not a valid tar archive")

            with tarfile.open(tar_path, "r:*") as tf:
                members = tf.getmembers()
                if not members:
                    raise ExtractionError("Archive is empty")

                filtered_members = []
                total_size = 0

                for member in members:
                    norm_path = member.name.replace("\\", "/")
                    if self._is_ignored(norm_path):
                        continue
                    filtered_members.append(member)
                    if member.isfile():
                        if member.size is not None:
                            total_size += member.size

                if len(filtered_members) > MAX_FILE_COUNT:
                    raise ExtractionError(
                        f"Project contains too many source files ({len(filtered_members)}). "
                        f"Maximum allowed source files is {MAX_FILE_COUNT}."
                    )

                if total_size > MAX_EXTRACTED_SIZE:
                    raise ExtractionError(
                        f"Total project size ({total_size / (1024*1024):.1f} MB) exceeds "
                        f"the maximum allowed size of {MAX_EXTRACTED_SIZE / (1024*1024*1024):.0f} GB"
                    )

                file_count = 0

                for member in filtered_members:
                    path = self._resolve_path(target_dir, member.name)

                    if member.isdir():
                        path.mkdir(parents=True, exist_ok=True)
                        continue

                    path.parent.mkdir(parents=True, exist_ok=True)
                    tf.extract(member, target_dir)
                    file_count += 1

                folder_count = self._count_folders(target_dir)

                return file_count, folder_count

        except ExtractionError:
            raise
        except tarfile.TarError:
            raise ExtractionError("Archive is corrupted or invalid")
        except OSError as e:
            self._handle_os_error(e)

    def _extract_with_patool(self, archive_path: Path, target_dir: Path) -> tuple[int, int]:
        try:
            import patoolib
        except ImportError:
            raise ExtractionError(
                f"Extraction of {archive_path.suffix} archives requires patool. "
                "Install it with: pip install patool",
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
            )

        try:
            patoolib.extract_archive(str(archive_path), outdir=str(target_dir))
        except patoolib.util.PatoolError as e:
            msg = str(e).lower()
            if "password" in msg or "encrypted" in msg:
                raise ExtractionError("Archive is password-protected and cannot be extracted")
            if "corrupt" in msg or "invalid" in msg:
                raise ExtractionError(f"Archive is corrupted: {e}")
            raise ExtractionError(f"Extraction failed: {e}")

        file_count = self._count_files(target_dir)
        if file_count > MAX_FILE_COUNT:
            shutil.rmtree(target_dir)
            raise ExtractionError(
                f"Project contains too many source files ({file_count}). "
                f"Maximum allowed source files is {MAX_FILE_COUNT}."
            )

        total_size = sum(
            f.stat().st_size for f in target_dir.rglob("*") if f.is_file()
        )
        if total_size > MAX_EXTRACTED_SIZE:
            shutil.rmtree(target_dir)
            raise ExtractionError(
                f"Total project size ({total_size / (1024*1024):.1f} MB) exceeds "
                f"the maximum allowed size of {MAX_EXTRACTED_SIZE / (1024*1024*1024):.0f} GB"
            )

        folder_count = self._count_folders(target_dir)
        return file_count, folder_count

    @staticmethod
    def _handle_os_error(e: OSError):
        if "No space left on device" in str(e):
            raise ExtractionError(
                "Disk full: insufficient space to extract the archive",
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            )
        if "Permission denied" in str(e):
            raise ExtractionError(
                "Permission denied while extracting files",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        raise ExtractionError(
            f"Extraction failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @staticmethod
    def _is_ignored(entry_path: str) -> bool:
        parts = entry_path.rstrip("/").split("/")
        for part in parts:
            if part in IGNORED_DIRS:
                return True
        name = parts[-1] if parts else ""
        if name in IGNORED_FILES:
            return True
        return False

    @staticmethod
    def _resolve_path(target_dir: Path, member_path: str) -> Path:
        sep = member_path.replace("\\", "/")
        cleaned = os.path.normpath(sep)

        if cleaned.startswith("..") or cleaned.startswith("/") or cleaned == ".":
            raise ExtractionError(
                f"Archive entry has an invalid or dangerous path: {member_path}"
            )

        resolved = (target_dir / cleaned).resolve()
        if not str(resolved).startswith(str(target_dir.resolve())):
            raise ExtractionError(
                f"Archive entry attempts path traversal outside workspace: {member_path}"
            )

        return resolved

    @staticmethod
    def _count_files(directory: Path) -> int:
        count = 0
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            count += len(files)
        return count

    @staticmethod
    def _count_folders(directory: Path) -> int:
        count = 0
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            count += len(dirs)
        return count
