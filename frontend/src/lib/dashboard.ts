import { api } from "@/lib/api";
import type { DashboardStats } from "@/types/dashboard";

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await api.get<DashboardStats>("/dashboard/stats");
  return res.data;
}
