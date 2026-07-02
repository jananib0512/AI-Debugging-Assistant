export interface ProjectStatistics {
  total_files: number;
  total_folders: number;
  total_size_bytes: number;
  source_files: number;
  config_files_count: number;
  documentation_files: number;
  image_files: number;
  video_files: number;
  asset_files: number;
}

export interface DevOpsInfo {
  docker: boolean;
  docker_compose: boolean;
  kubernetes: boolean;
  ci_cd: string[];
}

export interface ProjectMetadata {
  project_name: string;
  project_type: string | null;
  primary_language: string | null;
  secondary_languages: string[];
  languages: Record<string, number>;
  frameworks: string[];
  package_manager: string | null;
  databases: string[];
  devops: DevOpsInfo;
  config_files: string[];
  has_readme: boolean;
  statistics: ProjectStatistics;
  last_scanned_at: string | null;
}
