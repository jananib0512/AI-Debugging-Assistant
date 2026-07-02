import os
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
WORKSPACES_DIR = STORAGE_DIR / "workspaces"


def ensure_directories():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)


def generate_file_id() -> str:
    return uuid.uuid4().hex


def get_upload_path(file_id: str) -> Path:
    return UPLOADS_DIR / f"{file_id}.zip"


def get_workspace_path(project_id: int) -> Path:
    return WORKSPACES_DIR / str(project_id)


def create_workspace(project_id: int) -> Path:
    path = get_workspace_path(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def remove_upload(file_path: Path):
    if file_path.exists():
        file_path.unlink()
    workspace = file_path.parent
    if workspace.exists() and workspace.name != "uploads":
        pass


def remove_workspace(project_id: int):
    path = get_workspace_path(project_id)
    if path.exists():
        import shutil
        shutil.rmtree(path)
