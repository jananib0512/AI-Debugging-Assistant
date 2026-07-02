export interface TreeEntry {
  name: string;
  path: string;
  type: "file" | "directory";
  children: TreeEntry[] | null;
}

export interface FileTreeResponse {
  tree: TreeEntry;
}

export interface FolderEntry {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number | null;
  extension: string | null;
  modified_at: string | null;
}

export interface FolderResponse {
  path: string;
  entries: FolderEntry[];
}

export interface FileMetadata {
  name: string;
  path: string;
  extension: string;
  size: number;
  created_at: string;
  modified_at: string;
  is_directory: boolean;
  relative_path: string;
}

export interface SearchResult {
  name: string;
  path: string;
  type: "file" | "directory";
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface WorkspaceListItem {
  id: number;
  project_id: number;
  project_name: string;
  language: string;
  status: string;
  path: string;
  created_at: string | null;
  extracted_at: string | null;
  total_files: number | null;
  total_folders: number | null;
}

export interface WorkspaceListResponse {
  workspaces: WorkspaceListItem[];
  total: number;
}
