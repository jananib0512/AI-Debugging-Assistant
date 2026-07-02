export interface RecentProjectItem {
  id: number;
  project_name: string;
  uploaded_at: string | null;
  language: string;
}

export interface RecentActivityItem {
  id: string;
  type: string;
  description: string;
  timestamp: string;
}

export interface DashboardStats {
  total_projects: number;
  total_uploads: number;
  recent_projects: RecentProjectItem[];
  recent_activity: RecentActivityItem[];
  workspace_count: number;
  last_upload_time: string | null;
}
