export interface DetectedEntryPoint {
  path: string;
  file_name: string;
  type: string;
}

export interface DetectedDirectory {
  name: string;
  path: string;
  purpose: string;
}

export interface ProjectAnalysis {
  project_type: string;
  project_type_reason: string;
  architecture: string;
  architecture_reason: string;
  entry_points: DetectedEntryPoint[];
  important_directories: DetectedDirectory[];
  detected_modules: string[];
  frontend_framework: string | null;
  backend_framework: string | null;
  database_detected: string[];
  has_tests: boolean;
  has_docker: boolean;
  has_ci_cd: boolean;
  structure_summary: string;
  analyzed_at: string;
}

export interface TechnologyStack {
  languages: string[];
  frameworks: string[];
  databases: string[];
}

export interface FolderSummary {
  frontend: number;
  backend: number;
  source: number;
  config: number;
  assets: number;
  docs: number;
  tests: number;
  scripts: number;
  other: number;
}

export interface ConfigSummary {
  has_package_json: boolean;
  has_requirements_txt: boolean;
  has_dockerfile: boolean;
  has_docker_compose: boolean;
  has_readme: boolean;
  has_pyproject_toml: boolean;
  has_env_example: boolean;
  has_gitignore: boolean;
}

export interface AnalyzerResponse {
  project_name: string;
  project_type: string;
  workspace_status: string;
  technology_stack: TechnologyStack;
  total_files: number;
  total_folders: number;
  workspace_size: number;
  folder_summary: FolderSummary;
  config_summary: ConfigSummary;
  workspace_summary: string;
  analyzed_at: string;
}
