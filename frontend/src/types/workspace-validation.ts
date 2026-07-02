export interface ValidationWarning {
  type: string;
  message: string;
  detail: string | null;
}

export interface ValidationError {
  type: string;
  message: string;
  detail: string | null;
}

export interface ProjectStructureInfo {
  has_frontend: boolean;
  has_backend: boolean;
  has_source_folders: boolean;
  has_config_folder: boolean;
  has_assets_folder: boolean;
  has_documentation_folder: boolean;
  has_hidden_folders: boolean;
  notes: string[];
}

export interface ConfigFilesSummary {
  has_package_json: boolean;
  has_requirements_txt: boolean;
  has_pyproject_toml: boolean;
  has_dockerfile: boolean;
  has_docker_compose: boolean;
  has_readme: boolean;
  has_env_example: boolean;
  files_found: string[];
  files_missing: string[];
}

export interface WorkspaceValidation {
  workspace_status: string;
  validation_result: string;
  warnings: ValidationWarning[];
  errors: ValidationError[];
  project_structure: ProjectStructureInfo;
  config_files_summary: ConfigFilesSummary;
  ready_for_analysis: boolean;
  summary: string;
}
