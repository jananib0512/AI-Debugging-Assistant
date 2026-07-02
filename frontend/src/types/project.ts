export interface Project {
  id: number;
  user_id: number;
  project_name: string;
  description: string | null;
  language: string;
  framework: string | null;
  version: string | null;
  uploaded_file_name: string | null;
  uploaded_file_size: number | null;
  uploaded_file_path: string | null;
  upload_status: string | null;
  workspace_path: string | null;
  uploaded_at: string | null;
  extraction_status: string | null;
  total_files: number | null;
  total_folders: number | null;
  extraction_time_ms: number | null;
  extracted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProjectCreateInput {
  project_name: string;
  description?: string;
  language: string;
  framework?: string;
  version?: string;
}

export interface ProjectUpdateInput {
  project_name?: string;
  description?: string;
  language?: string;
  framework?: string;
  version?: string;
}
