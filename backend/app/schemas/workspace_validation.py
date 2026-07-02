from pydantic import BaseModel


class ValidationWarning(BaseModel):
    type: str
    message: str
    detail: str | None = None


class ValidationError(BaseModel):
    type: str
    message: str
    detail: str | None = None


class ProjectStructureInfo(BaseModel):
    has_frontend: bool
    has_backend: bool
    has_source_folders: bool
    has_config_folder: bool
    has_assets_folder: bool
    has_documentation_folder: bool
    has_hidden_folders: bool
    notes: list[str]


class ConfigFilesSummary(BaseModel):
    has_package_json: bool
    has_requirements_txt: bool
    has_pyproject_toml: bool
    has_dockerfile: bool
    has_docker_compose: bool
    has_readme: bool
    has_env_example: bool
    files_found: list[str]
    files_missing: list[str]


class WorkspaceValidationResponse(BaseModel):
    workspace_status: str
    validation_result: str
    warnings: list[ValidationWarning]
    errors: list[ValidationError]
    project_structure: ProjectStructureInfo
    config_files_summary: ConfigFilesSummary
    ready_for_analysis: bool
    summary: str
