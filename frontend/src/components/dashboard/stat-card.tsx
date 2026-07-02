import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  index: number;
}

export function StatCard({ title, value, icon: Icon, index }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.08 }}
      className="rounded-xl border border-border bg-card p-6 shadow-card"
    >
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            {title}
          </p>
          <p className="text-3xl font-bold tracking-tight text-foreground">
            {value}
          </p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </div>
    </motion.div>
  );
}
