from datetime import datetime

from pydantic import BaseModel


class DetectedEntryPoint(BaseModel):
    path: str
    file_name: str
    type: str


class DetectedDirectory(BaseModel):
    name: str
    path: str
    purpose: str


class ProjectAnalysisResponse(BaseModel):
    project_type: str
    project_type_reason: str
    architecture: str
    architecture_reason: str
    entry_points: list[DetectedEntryPoint]
    important_directories: list[DetectedDirectory]
    detected_modules: list[str]
    frontend_framework: str | None = None
    backend_framework: str | None = None
    database_detected: list[str]
    has_tests: bool
    has_docker: bool
    has_ci_cd: bool
    structure_summary: str
    analyzed_at: datetime


class FolderSummary(BaseModel):
    frontend: int = 0
    backend: int = 0
    source: int = 0
    config: int = 0
    assets: int = 0
    docs: int = 0
    tests: int = 0
    scripts: int = 0
    other: int = 0


class TechnologyStack(BaseModel):
    languages: list[str] = []
    frameworks: list[str] = []
    databases: list[str] = []


class ConfigSummary(BaseModel):
    has_package_json: bool = False
    has_requirements_txt: bool = False
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    has_readme: bool = False
    has_pyproject_toml: bool = False
    has_env_example: bool = False
    has_gitignore: bool = False


class AnalyzerResponse(BaseModel):
    project_name: str
    project_type: str
    workspace_status: str
    technology_stack: TechnologyStack
    total_files: int
    total_folders: int
    workspace_size: int
    folder_summary: FolderSummary
    config_summary: ConfigSummary
    workspace_summary: str
    analyzed_at: datetime
