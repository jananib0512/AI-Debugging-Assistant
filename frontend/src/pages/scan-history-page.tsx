import { motion } from "framer-motion";
import { ScanEye } from "lucide-react";

import { Card } from "@/components/ui/card";

export function ScanHistoryPage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Scan History</h2>
        <p className="text-sm text-muted-foreground">
          View your past debugging scan results
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card>
          <div className="flex flex-col items-center justify-center py-24">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary mb-6">
              <ScanEye className="h-7 w-7 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground">No scan history</h3>
            <p className="mt-1 text-sm text-muted-foreground text-center max-w-sm">
              Upload and scan a project to see your scan history here
            </p>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
