import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export function AiStatusPage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-foreground">AI Status</h2>
        <p className="text-sm text-muted-foreground">
          AI-powered debugging features
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card>
          <CardContent className="p-8 sm:p-12 flex flex-col items-center text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-blue-50 mb-6">
              <Brain className="h-10 w-10 text-primary" />
            </div>
            <h3 className="text-2xl font-bold text-foreground">AI Features</h3>
            <p className="mt-2 text-sm text-muted-foreground max-w-md">
              Intelligent bug detection, automated root cause analysis, and
              smart code review powered by advanced AI are coming soon.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-6">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Sparkles className="h-4 w-4 text-primary" />
                Bug Detection
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Sparkles className="h-4 w-4 text-primary" />
                Root Cause Analysis
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Sparkles className="h-4 w-4 text-primary" />
                Smart Code Review
              </div>
            </div>
            <div className="mt-8">
              <div className="inline-flex items-center gap-2 rounded-full bg-yellow-50 px-4 py-1.5 text-xs font-medium text-yellow-600">
                <div className="h-1.5 w-1.5 rounded-full bg-yellow-400" />
                Coming Soon
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
