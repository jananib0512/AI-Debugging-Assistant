import { api } from "@/lib/api";
import type {
  Project,
  ProjectCreateInput,
  ProjectListResponse,
  ProjectUpdateInput,
} from "@/types/project";

export async function listProjects(params: {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
  search?: string;
}): Promise<ProjectListResponse> {
  const res = await api.get<ProjectListResponse>("/projects", { params });
  return res.data;
}

export async function getProject(id: number): Promise<Project> {
  const res = await api.get<Project>(`/projects/${id}`);
  return res.data;
}

export async function createProject(
  input: ProjectCreateInput,
): Promise<Project> {
  const res = await api.post<Project>("/projects", input);
  return res.data;
}

export async function updateProject(
  id: number,
  input: ProjectUpdateInput,
): Promise<Project> {
  const res = await api.put<Project>(`/projects/${id}`, input);
  return res.data;
}

export async function deleteProject(id: number): Promise<void> {
  await api.delete(`/projects/${id}`);
}

export async function uploadProjectFile(
  projectId: number,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<Project> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await api.post<Project>(
    `/projects/${projectId}/upload`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress(percent);
        }
      },
    },
  );
  return res.data;
}

export async function extractProject(
  projectId: number,
): Promise<Project> {
  const res = await api.post<Project>(`/projects/${projectId}/extract`);
  return res.data;
}
