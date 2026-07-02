import { api } from "@/lib/api";
import type { ProjectMetadata } from "@/types/project-metadata";

export async function getProjectMetadata(
  projectId: number,
): Promise<ProjectMetadata> {
  const res = await api.get<ProjectMetadata>(
    `/projects/${projectId}/metadata`,
  );
  return res.data;
}
