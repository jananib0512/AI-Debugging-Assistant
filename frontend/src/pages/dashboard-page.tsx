import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  CheckCircle2,
  Clock,
  FolderKanban,
  HardDrive,
  Sparkles,
  Upload,
} from "lucide-react";

import { DashboardCards } from "@/components/dashboard/dashboard-cards";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { StatCard } from "@/components/dashboard/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getDashboardStats } from "@/lib/dashboard";
import type { DashboardStats } from "@/types/dashboard";
import { useAuth } from "@/providers/auth-provider";

export function DashboardPage() {
  const { lastLogin } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch(() => {
        /* keep null — fallback below */
      })
      .finally(() => setLoading(false));
  }, []);

  function formatDate(dateString: string | null) {
    if (!dateString) return "N/A";
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(dateString));
  }

  const statCards = [
    {
      title: "Total Projects",
      value: stats !== null ? String(stats.total_projects) : (loading ? "—" : "0"),
      icon: FolderKanban,
    },
    {
      title: "Total Uploads",
      value: stats !== null ? String(stats.total_uploads) : (loading ? "—" : "0"),
      icon: Upload,
    },
    {
      title: "Last Login",
      value: formatDate(lastLogin),
      icon: Clock,
    },
    {
      title: "Account Status",
      value: "Active",
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat, index) => (
          <StatCard key={stat.title} {...stat} index={index} />
        ))}
      </div>

      <div>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="mb-4"
        >
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Quick Access
          </h2>
        </motion.div>
        <DashboardCards />
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RecentActivity items={stats?.recent_activity ?? []} />
        </div>

        <div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-muted-foreground" />
                  <CardTitle className="text-sm font-semibold">Quick Actions</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-sm font-normal h-11"
                  asChild
                >
                  <a href="/upload">
                    <Upload className="h-4 w-4" />
                    Upload Project
                  </a>
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-sm font-normal h-11"
                  asChild
                >
                  <a href="/workspace">
                    <Activity className="h-4 w-4" />
                    Open Workspace
                  </a>
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-sm font-normal h-11"
                  asChild
                >
                  <a href="/projects">
                    <FolderKanban className="h-4 w-4" />
                    View Projects
                  </a>
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-sm font-normal h-11"
                  asChild
                >
                  <a href="/scan-history">
                    <HardDrive className="h-4 w-4" />
                    Scan History
                  </a>
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.5 }}
            className="mt-4"
          >
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
                    <Sparkles className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">AI Status</p>
                    <p className="text-xs text-muted-foreground">
                      AI features coming soon
                    </p>
                  </div>
                  <div className="h-2 w-2 rounded-full bg-yellow-400 shrink-0" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
