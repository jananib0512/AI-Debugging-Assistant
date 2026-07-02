import { api } from "@/lib/api";
import type { WorkspaceValidation } from "@/types/workspace-validation";

export async function getWorkspaceValidation(
  projectId: number,
): Promise<WorkspaceValidation> {
  const res = await api.get<WorkspaceValidation>(
    `/projects/${projectId}/workspace-validation`,
  );
  return res.data;
}
