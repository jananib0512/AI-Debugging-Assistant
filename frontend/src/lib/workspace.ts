import { api } from "@/lib/api";
import type {
  FileMetadata,
  FileTreeResponse,
  FolderResponse,
  SearchResponse,
  TreeEntry,
  WorkspaceListResponse,
} from "@/types/workspace";

export async function getWorkspaceTree(
  projectId: number,
): Promise<TreeEntry> {
  const res = await api.get<FileTreeResponse>(
    `/workspaces/${projectId}/tree`,
  );
  return res.data.tree;
}

export async function listWorkspaceFolder(
  projectId: number,
  path: string,
): Promise<FolderResponse> {
  const res = await api.get<FolderResponse>(
    `/workspaces/${projectId}/folder`,
    { params: { path } },
  );
  return res.data;
}

export async function getFileMetadata(
  projectId: number,
  path: string,
): Promise<FileMetadata> {
  const res = await api.get<FileMetadata>(
    `/workspaces/${projectId}/metadata`,
    { params: { path } },
  );
  return res.data;
}

export async function searchWorkspace(
  projectId: number,
  query: string,
): Promise<SearchResponse> {
  const res = await api.get<SearchResponse>(
    `/workspaces/${projectId}/search`,
    { params: { q: query } },
  );
  return res.data;
}

export async function listWorkspaces(): Promise<WorkspaceListResponse> {
  const res = await api.get<WorkspaceListResponse>("/workspaces");
  return res.data;
}
