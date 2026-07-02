import { motion } from "framer-motion";
import { Clock, Inbox, Upload, HardDrive, FolderKanban } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RecentActivityItem } from "@/types/dashboard";

function ActivityIcon({ type }: { type: string }) {
  const Icon = type === "upload"
    ? Upload
    : type === "extraction"
      ? HardDrive
      : type === "creation"
        ? FolderKanban
        : Clock;
  return <Icon className="h-4 w-4 text-primary" />;
}

function formatTimestamp(ts: string) {
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function RecentActivity({ items }: { items: RecentActivityItem[] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.3 }}
    >
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-semibold">Recent Activity</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary mb-4">
                <Inbox className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground">No activity yet</p>
              <p className="mt-1 text-xs text-muted-foreground text-center max-w-[200px]">
                Your recent actions will appear here once you start using the platform
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {items.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center gap-4 py-3"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                    <ActivityIcon type={activity.type} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate text-foreground">
                      {activity.description}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatTimestamp(activity.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
